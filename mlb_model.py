#!/usr/bin/env python3
"""
MLB Predictive Model - Sports Edge

Ensemble of 3 models for predicting MLB game totals:
  1. Pitcher-Adjusted Poisson: run-scoring rates adjusted for SP quality, park, weather
  2. XGBoost Regression: gradient-boosted features predicting game total runs
  3. Market Model: Pinnacle/consensus line as a Bayesian anchor

Usage:
    python3 mlb_model.py                      # Predict today's games
    python3 mlb_model.py --backtest            # Walk-forward backtest
    python3 mlb_model.py --backtest --start 2025-04-01 --end 2025-09-30
    python3 mlb_model.py --edges               # Find betting edges vs market
    python3 mlb_model.py --game LAD NYY        # Single game prediction
"""

import argparse
import json
import logging
import math
import os
import pickle
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import poisson, nbinom

try:
    import xgboost as xgb
except ImportError:
    print("[SETUP] xgboost not found -- installing...")
    import subprocess
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--break-system-packages", "xgboost", "-q"],
        stderr=subprocess.DEVNULL,
    )
    import xgboost as xgb

# Local pipeline
from mlb_data_pipeline import (
    DB_PATH,
    MLB_STADIUMS,
    STADIUM_BY_ABBREV,
    STADIUM_BY_TEAM_ID,
    TEAM_ABBREV_BY_ID,
    compute_bullpen_fatigue,
    compute_pitcher_features,
    compute_team_batting_features,
    get_db,
    get_game_features,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

XGBOOST_MODEL_PATH = os.path.join(MODEL_DIR, "mlb_xgb_total.pkl")

# League-average constants (2024 MLB season baselines)
LEAGUE_AVG_RS_PER_GAME = 4.52  # league-wide runs per team per game
LEAGUE_AVG_ERA = 4.17
LEAGUE_AVG_FIP = 4.14
LEAGUE_AVG_WHIP = 1.28
LEAGUE_AVG_K_PER_9 = 8.60
LEAGUE_AVG_BB_PER_9 = 3.20

# Ensemble weights
WEIGHT_POISSON = 0.30
WEIGHT_XGBOOST = 0.40
WEIGHT_MARKET = 0.30

# Weather constants
TEMP_BASELINE_F = 70.0
TEMP_COEFF_PER_DEGREE = 0.01  # +0.01 runs per degree F above 70
WIND_COEFF = 0.03  # +0.03 runs per mph when wind is blowing out

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MODEL] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mlb_model")


# ===========================================================================
# Helper: Negative Binomial distribution math (handles MLB overdispersion)
# ===========================================================================

# MLB run scoring has variance ~2x the mean (overdispersion).
# Poisson assumes variance = mean, making probability tails too thin.
# Negative binomial has a dispersion parameter to handle this.
MLB_OVERDISPERSION = 2.1  # variance/mean ratio (empirical: AL=2.22, NL=2.15, per-inning=2.11)


def _nb_params(mu: float, overdispersion: float = MLB_OVERDISPERSION):
    """Convert mean + overdispersion to scipy nbinom (n, p) parameters."""
    r = mu / (overdispersion - 1)
    p = r / (r + mu)
    return r, p


def poisson_game_total_probs(lambda_home: float, lambda_away: float,
                              max_runs_per_team: int = 20) -> Dict[float, float]:
    """
    Compute P(total = k) for k = 0 .. 2*max_runs_per_team
    by convolving two independent negative binomial distributions.
    Returns {total: probability}.

    Uses negative binomial instead of Poisson to account for
    MLB's overdispersed run scoring (variance >> mean).
    """
    r_h, p_h = _nb_params(lambda_home)
    r_a, p_a = _nb_params(lambda_away)

    # Pre-compute PMFs for efficiency
    pmf_home = [nbinom.pmf(k, r_h, p_h) for k in range(max_runs_per_team + 1)]
    pmf_away = [nbinom.pmf(k, r_a, p_a) for k in range(max_runs_per_team + 1)]

    probs = {}
    for total in range(0, 2 * max_runs_per_team + 1):
        p = 0.0
        for home_r in range(0, min(total, max_runs_per_team) + 1):
            away_r = total - home_r
            if away_r > max_runs_per_team:
                continue
            p += pmf_home[home_r] * pmf_away[away_r]
        probs[total] = p
    return probs


def prob_over(total_probs: Dict[float, float], line: float) -> float:
    """P(total > line).  If line is X.5, it's clean. If X.0, push = no action."""
    p_over = 0.0
    for total, prob in total_probs.items():
        if total > line:
            p_over += prob
    return p_over


def prob_over_for_lines(total_probs: Dict[float, float],
                         lines: List[float] = None) -> Dict[str, float]:
    """Return P(over X) for standard betting lines."""
    if lines is None:
        lines = [6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0]
    return {str(line): round(prob_over(total_probs, line), 4) for line in lines}


# ===========================================================================
# Wind direction utility
# ===========================================================================

# Approximate home plate -> CF bearing for each park (degrees from north).
# Most parks face NE-ish. This is a simplification; real values vary.
PARK_HP_TO_CF_BEARING = {
    "LAA": 30, "ARI": 45, "NYM": 45, "PHI": 50, "DET": 20,
    "COL": 60, "LAD": 0, "BOS": 30, "TEX": 45, "CIN": 60,
    "CWS": 45, "KC": 45, "MIA": 0, "HOU": 45, "WSH": 45,
    "OAK": 180, "SF": 225, "BAL": 30, "PIT": 45, "SD": 0,
    "CLE": 35, "TOR": 0, "SEA": 0, "MIN": 45, "TB": 0,
    "ATL": 45, "CHC": 0, "NYY": 45, "STL": 45, "MIL": 45,
}


def wind_run_adjustment(wind_speed_mph: float, wind_dir_deg: float,
                         team_abbrev: str, is_dome: bool) -> float:
    """
    Calculate wind's effect on run scoring.
    Returns adjustment in runs (positive = more runs).

    Wind blowing out to CF increases offense; blowing in reduces it.
    Cross-winds have minimal effect.
    """
    if is_dome or wind_speed_mph is None or wind_dir_deg is None:
        return 0.0

    hp_to_cf = PARK_HP_TO_CF_BEARING.get(team_abbrev, 45)

    # Angle between wind direction (where wind comes FROM) and HP->CF line
    # Wind FROM the direction behind home plate blows OUT to CF
    # Wind dir 180 degrees from HP->CF means wind is blowing OUT
    angle_diff = (wind_dir_deg - hp_to_cf + 180) % 360
    # Normalize to -180..180
    if angle_diff > 180:
        angle_diff -= 360

    # cos component: 1.0 = straight out, -1.0 = straight in, 0 = cross-wind
    directional_factor = math.cos(math.radians(angle_diff))

    # Scale: multiply by wind speed, diminishing returns above 15 mph
    effective_wind = min(wind_speed_mph, 25.0)
    adjustment = WIND_COEFF * effective_wind * directional_factor

    return round(adjustment, 2)


def temperature_run_adjustment(temp_f: float) -> float:
    """Linear temperature adjustment. +0.01 runs per degree above 70F baseline."""
    if temp_f is None:
        return 0.0
    return round(TEMP_COEFF_PER_DEGREE * (temp_f - TEMP_BASELINE_F), 2)


# ===========================================================================
# Model 1: Pitcher-Adjusted Poisson
# ===========================================================================

class PoissonPitcherModel:
    """
    Estimates each team's expected runs as an adjusted Poisson rate.

    For each team:
      base_rate = team RS/game (season or recent blend)
      pitcher_adj = league_avg_FIP / opposing_pitcher_FIP
      park_adj = park_factor
      weather_adj = wind + temperature effects

      lambda = base_rate * pitcher_adj * park_adj + weather_adj
    """

    def __init__(self):
        self.name = "poisson_pitcher"

    def predict(self, features: dict) -> dict:
        """
        Given features dict from get_game_features(), return expected total
        and probability distribution.
        """
        # Base run-scoring rates
        home_rs = self._team_run_rate(features, "home")
        away_rs = self._team_run_rate(features, "away")

        # Pitcher adjustments (opposing pitcher quality)
        away_pitcher_adj = self._pitcher_adjustment(features.get("away_pitcher"))
        home_pitcher_adj = self._pitcher_adjustment(features.get("home_pitcher"))

        # Home team faces away pitcher, away team faces home pitcher
        home_lambda = home_rs * away_pitcher_adj
        away_lambda = away_rs * home_pitcher_adj

        # Park factor
        pf = features.get("park_factor_runs", 1.0) or 1.0
        home_lambda *= pf
        away_lambda *= pf

        # Weather adjustments (additive, not multiplicative)
        wx_adj = self._weather_adjustment(features)
        home_lambda += wx_adj / 2
        away_lambda += wx_adj / 2

        # Floor: don't allow negative or unreasonably low lambdas
        home_lambda = max(home_lambda, 1.5)
        away_lambda = max(away_lambda, 1.5)

        expected_total = round(home_lambda + away_lambda, 2)

        # Full probability distribution
        total_probs = poisson_game_total_probs(home_lambda, away_lambda)
        over_probs = prob_over_for_lines(total_probs)

        return {
            "model": self.name,
            "home_lambda": round(home_lambda, 3),
            "away_lambda": round(away_lambda, 3),
            "expected_total": expected_total,
            "over_probs": over_probs,
            "total_distribution": total_probs,
        }

    def _team_run_rate(self, features: dict, side: str) -> float:
        """Blend season rate with recent 10-game rate (60/40 split)."""
        batting = features.get(f"{side}_batting", {})
        season_rate = batting.get("rs_per_game_season")
        recent_rate = batting.get("rs_per_game_last_10")

        if season_rate and recent_rate:
            return season_rate * 0.6 + recent_rate * 0.4
        if season_rate:
            return season_rate
        if recent_rate:
            return recent_rate
        return LEAGUE_AVG_RS_PER_GAME

    def _pitcher_adjustment(self, pitcher: dict) -> float:
        """
        Pitcher quality multiplier. Uses FIP (less noisy than ERA).
        Ratio: league_avg_FIP / pitcher_FIP.
        Good pitcher (low FIP) -> ratio > 1 -> opposing team scores LESS.
        Bad pitcher (high FIP) -> ratio < 1 -> opposing team scores MORE.

        We INVERT this because the adjustment applies to the BATTING team.
        Facing a bad pitcher means MORE runs, so we want:
          pitcher_FIP / league_avg_FIP  (bad pitcher = high ratio = more runs)
        """
        if not pitcher or not pitcher.get("found"):
            return 1.0  # league average assumption

        # Prefer xFIP > FIP > ERA (least noisy to most)
        xfip = pitcher.get("xfip")
        fip = pitcher.get("fip")
        era = pitcher.get("era")

        # Use best available metric
        pitcher_quality = None
        if xfip is not None and pitcher.get("innings_pitched", 0) >= 20:
            pitcher_quality = xfip
        elif fip is not None and pitcher.get("innings_pitched", 0) >= 10:
            pitcher_quality = fip
        elif era is not None:
            pitcher_quality = era

        if pitcher_quality is None or pitcher_quality <= 0:
            return 1.0

        ip = pitcher.get("innings_pitched", 0) or 0

        # Hard floor: pitchers with <10 IP are pure noise, treat as league avg
        if ip < 10:
            return 1.0

        # pitcher_FIP / league_avg means facing a 5.00 FIP pitcher
        # when league avg is 4.14 gives a 1.21x multiplier (more runs)
        ratio = pitcher_quality / LEAGUE_AVG_FIP

        # Regress toward 1.0 based on sample size
        # At 180+ IP, trust fully. Under that, heavy regression.
        # Use sqrt curve so regression is much stronger at low IP
        reliability = min((ip / 180.0) ** 0.5, 1.0)
        # At 10 IP: reliability = 0.24 -> weight = 0.12
        # At 30 IP: reliability = 0.41 -> weight = 0.20
        # At 60 IP: reliability = 0.58 -> weight = 0.29
        # At 120 IP: reliability = 0.82 -> weight = 0.41
        # At 180 IP: reliability = 1.0  -> weight = 0.50
        regressed_ratio = 1.0 + (ratio - 1.0) * (0.5 * reliability)

        # IP-dependent clamping: less trust = tighter bounds
        if ip < 30:
            max_adj = 1.15
        elif ip < 60:
            max_adj = 1.25
        elif ip < 120:
            max_adj = 1.40
        else:
            max_adj = 1.50
        min_adj = 2.0 - max_adj  # Symmetric: 1.15 max -> 0.85 min

        return max(min_adj, min(regressed_ratio, max_adj))

    def _weather_adjustment(self, features: dict) -> float:
        """Total weather run adjustment for the game."""
        is_dome = features.get("is_dome", False)
        if is_dome:
            return 0.0

        wx = features.get("weather", {})
        if not wx:
            return 0.0

        temp_f = wx.get("temperature_f")
        wind_speed = wx.get("wind_speed_mph")
        wind_dir = wx.get("wind_direction_deg")
        home_team = features.get("home_team", "")

        temp_adj = temperature_run_adjustment(temp_f)
        wind_adj = wind_run_adjustment(wind_speed, wind_dir, home_team, is_dome)

        return temp_adj + wind_adj


# ===========================================================================
# Model 2: XGBoost MLB Total Regression
# ===========================================================================

# Feature columns the XGBoost model expects
XGBOOST_FEATURE_COLS = [
    # Home pitcher
    "hp_era", "hp_fip", "hp_xfip", "hp_whip", "hp_k_per_9", "hp_bb_per_9",
    "hp_innings_pitched", "hp_quality_score",
    "hp_hard_hit_pct", "hp_barrel_pct", "hp_whiff_pct",
    # Away pitcher
    "ap_era", "ap_fip", "ap_xfip", "ap_whip", "ap_k_per_9", "ap_bb_per_9",
    "ap_innings_pitched", "ap_quality_score",
    "ap_hard_hit_pct", "ap_barrel_pct", "ap_whiff_pct",
    # Home batting
    "h_rs_season", "h_rs_last_10", "h_woba", "h_xwoba",
    "h_k_pct", "h_bb_pct", "h_exit_velo",
    # Away batting
    "a_rs_season", "a_rs_last_10", "a_woba", "a_xwoba",
    "a_k_pct", "a_bb_pct", "a_exit_velo",
    # Bullpen
    "h_bp_fatigue", "a_bp_fatigue",
    # Park & environment
    "park_factor",
    "temperature_f", "wind_speed_mph", "wind_dir_cos",
    "humidity_pct", "is_dome",
]


class XGBoostMLBModel:
    """
    XGBoost regression model predicting game total runs.
    Features derived from pitcher stats, team batting, bullpen fatigue,
    park factors, and weather.
    """

    def __init__(self):
        self.name = "xgboost_mlb"
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_cols = XGBOOST_FEATURE_COLS
        self._load_model()

    def _load_model(self):
        """Load trained model from disk if available."""
        if os.path.exists(XGBOOST_MODEL_PATH):
            try:
                with open(XGBOOST_MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                log.info("Loaded XGBoost model from %s", XGBOOST_MODEL_PATH)
            except Exception as e:
                log.warning("Failed to load XGBoost model: %s", e)
                self.model = None

    def _save_model(self):
        with open(XGBOOST_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        log.info("Saved XGBoost model to %s", XGBOOST_MODEL_PATH)

    def features_from_game(self, features: dict) -> dict:
        """
        Convert get_game_features() output to flat feature dict
        matching XGBOOST_FEATURE_COLS.
        """
        hp = features.get("home_pitcher", {})
        ap = features.get("away_pitcher", {})
        hb = features.get("home_batting", {})
        ab = features.get("away_batting", {})
        hbp = features.get("home_bullpen", {})
        abp = features.get("away_bullpen", {})
        wx = features.get("weather", {})
        is_dome = 1 if features.get("is_dome") else 0

        # Wind direction cosine (blowing out = positive)
        wind_dir_cos = 0.0
        if wx.get("wind_direction_deg") is not None and not is_dome:
            home_team = features.get("home_team", "")
            hp_to_cf = PARK_HP_TO_CF_BEARING.get(home_team, 45)
            angle_diff = (wx["wind_direction_deg"] - hp_to_cf + 180) % 360
            if angle_diff > 180:
                angle_diff -= 360
            wind_dir_cos = math.cos(math.radians(angle_diff))

        row = {
            # Home pitcher
            "hp_era": hp.get("era"),
            "hp_fip": hp.get("fip"),
            "hp_xfip": hp.get("xfip"),
            "hp_whip": hp.get("whip"),
            "hp_k_per_9": hp.get("k_per_9"),
            "hp_bb_per_9": hp.get("bb_per_9"),
            "hp_innings_pitched": hp.get("innings_pitched"),
            "hp_quality_score": hp.get("quality_score"),
            "hp_hard_hit_pct": hp.get("hard_hit_pct_against"),
            "hp_barrel_pct": hp.get("barrel_pct_against"),
            "hp_whiff_pct": hp.get("whiff_pct"),
            # Away pitcher
            "ap_era": ap.get("era"),
            "ap_fip": ap.get("fip"),
            "ap_xfip": ap.get("xfip"),
            "ap_whip": ap.get("whip"),
            "ap_k_per_9": ap.get("k_per_9"),
            "ap_bb_per_9": ap.get("bb_per_9"),
            "ap_innings_pitched": ap.get("innings_pitched"),
            "ap_quality_score": ap.get("quality_score"),
            "ap_hard_hit_pct": ap.get("hard_hit_pct_against"),
            "ap_barrel_pct": ap.get("barrel_pct_against"),
            "ap_whiff_pct": ap.get("whiff_pct"),
            # Home batting
            "h_rs_season": hb.get("rs_per_game_season"),
            "h_rs_last_10": hb.get("rs_per_game_last_10"),
            "h_woba": hb.get("team_woba"),
            "h_xwoba": hb.get("team_xwoba"),
            "h_k_pct": hb.get("team_k_pct"),
            "h_bb_pct": hb.get("team_bb_pct"),
            "h_exit_velo": hb.get("team_avg_exit_velo"),
            # Away batting
            "a_rs_season": ab.get("rs_per_game_season"),
            "a_rs_last_10": ab.get("rs_per_game_last_10"),
            "a_woba": ab.get("team_woba"),
            "a_xwoba": ab.get("team_xwoba"),
            "a_k_pct": ab.get("team_k_pct"),
            "a_bb_pct": ab.get("team_bb_pct"),
            "a_exit_velo": ab.get("team_avg_exit_velo"),
            # Bullpen
            "h_bp_fatigue": hbp.get("bullpen_fatigue_score", 0.0),
            "a_bp_fatigue": abp.get("bullpen_fatigue_score", 0.0),
            # Park & environment
            "park_factor": features.get("park_factor_runs", 1.0),
            "temperature_f": wx.get("temperature_f"),
            "wind_speed_mph": wx.get("wind_speed_mph"),
            "wind_dir_cos": wind_dir_cos,
            "humidity_pct": wx.get("humidity_pct"),
            "is_dome": is_dome,
        }
        return row

    def predict(self, features: dict) -> dict:
        """Predict game total using trained XGBoost model."""
        row = self.features_from_game(features)
        df = pd.DataFrame([row], columns=self.feature_cols)

        # Coerce all features to numeric (some come as strings from DB)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if self.model is None:
            # Fallback: simple feature-weighted estimate
            return self._fallback_predict(row)

        pred = float(self.model.predict(df)[0])
        pred = max(pred, 4.0)  # floor at 4 total runs

        return {
            "model": self.name,
            "expected_total": round(pred, 2),
            "features_used": len([v for v in row.values() if v is not None]),
            "features_total": len(self.feature_cols),
        }

    def _fallback_predict(self, row: dict) -> dict:
        """
        Simple weighted average when XGBoost model isn't trained yet.
        Uses a linear combination of the most predictive features.
        """
        h_rs = row.get("h_rs_season") or LEAGUE_AVG_RS_PER_GAME
        a_rs = row.get("a_rs_season") or LEAGUE_AVG_RS_PER_GAME
        pf = row.get("park_factor") or 1.0

        # Base: sum of team run rates * park factor
        total = (h_rs + a_rs) * pf

        # Pitcher adjustment using quality scores (lower = better pitcher = fewer runs)
        hp_qs = row.get("hp_quality_score")
        ap_qs = row.get("ap_quality_score")
        if hp_qs is not None:
            # Away team faces home pitcher. League avg quality score ~ 3.8
            total += (hp_qs - 3.8) * 0.3
        if ap_qs is not None:
            total += (ap_qs - 3.8) * 0.3

        # Weather
        temp = row.get("temperature_f")
        if temp and not row.get("is_dome"):
            total += temperature_run_adjustment(temp)

        total = max(total, 4.0)

        return {
            "model": f"{self.name}_fallback",
            "expected_total": round(total, 2),
            "features_used": len([v for v in row.values() if v is not None]),
            "features_total": len(self.feature_cols),
        }

    def train(self, training_data: pd.DataFrame):
        """
        Train XGBoost model on historical game data.

        training_data must have columns matching XGBOOST_FEATURE_COLS + 'actual_total'.
        """
        target_col = "actual_total"
        if target_col not in training_data.columns:
            raise ValueError(f"Training data must have '{target_col}' column")

        X = training_data[self.feature_cols].copy()
        y = training_data[target_col].copy()

        # Coerce all features to numeric (some come as strings from DB)
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")
        y = pd.to_numeric(y, errors="coerce")

        # Drop rows where target is missing
        valid = y.notna()
        X = X[valid]
        y = y[valid]

        if len(X) < 50:
            log.warning("Only %d training samples -- model may be unreliable", len(X))

        self.model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_alpha=0.5,
            reg_lambda=1.0,
            objective="reg:squarederror",
            random_state=42,
            enable_categorical=False,
        )

        self.model.fit(X, y, verbose=False)
        self._save_model()

        # Training metrics
        preds = self.model.predict(X)
        mae = float(np.mean(np.abs(preds - y)))
        rmse = float(np.sqrt(np.mean((preds - y) ** 2)))
        log.info("XGBoost trained: %d samples, MAE=%.2f, RMSE=%.2f", len(X), mae, rmse)

        return {"samples": len(X), "mae": mae, "rmse": rmse}


# ===========================================================================
# Model 3: Market Model
# ===========================================================================

class MarketModel:
    """
    Uses consensus/Pinnacle total line as the prediction.
    This embeds the market's best estimate. The sharpest line available
    is Pinnacle; if unavailable we use whatever is in our odds database.
    """

    def __init__(self):
        self.name = "market"

    def predict(self, home_team: str, away_team: str,
                game_date: str = None, market_total: float = None) -> dict:
        """
        Look up market total from our odds database or accept it directly.
        """
        if market_total is not None:
            return {
                "model": self.name,
                "expected_total": market_total,
                "source": "provided",
            }

        # Try to find in our odds databases
        total = self._lookup_market_total(home_team, away_team, game_date)
        if total:
            return {
                "model": self.name,
                "expected_total": total,
                "source": "database",
            }

        return {
            "model": self.name,
            "expected_total": None,
            "source": "unavailable",
        }

    def _lookup_market_total(self, home_team: str, away_team: str,
                              game_date: str = None) -> Optional[float]:
        """
        Search our odds data for the game total line.
        Checks game_line_scan.json (Level 1 scanner output) first,
        then falls back to database files.
        """
        if game_date is None:
            game_date = datetime.now().strftime("%Y-%m-%d")

        # Check game_line_scan.json (produced by Level 1 scanner)
        scan_path = os.path.join(BASE_DIR, "data", "game_line_scan.json")
        if os.path.exists(scan_path):
            try:
                with open(scan_path) as f:
                    scan_data = json.load(f)
                # Look in the games list for matching total lines
                for game_data in scan_data.get("games", []):
                    game_name = game_data.get("game", "").upper()
                    sport = game_data.get("sport", "")
                    if sport != "MLB":
                        continue
                    if home_team.upper() in game_name or away_team.upper() in game_name:
                        # Look for Pinnacle total line
                        lines = game_data.get("lines", {})
                        for book, book_lines in lines.items():
                            if "pinnacle" in book.lower():
                                total = book_lines.get("total")
                                if total:
                                    return float(total)
                        # Fall back to any book's total
                        for book, book_lines in lines.items():
                            total = book_lines.get("total")
                            if total:
                                return float(total)

                # Also check opportunities list for total lines
                for opp in scan_data.get("opportunities", []):
                    if opp.get("sport") != "MLB":
                        continue
                    game_name = opp.get("game", "").upper()
                    market = opp.get("market", "").lower()
                    if "total" not in market:
                        continue
                    if home_team.upper() in game_name or away_team.upper() in game_name:
                        line = opp.get("line")
                        if line:
                            return float(line)
            except Exception:
                pass

        # Fall back to game_lines.db (populated by game_line_scanner)
        db_path = os.path.join(BASE_DIR, "data", "game_lines.db")
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                # Query game_odds table for Pinnacle total line
                row = conn.execute("""
                    SELECT line FROM game_odds
                    WHERE sport = 'MLB'
                      AND market = 'total'
                      AND side = 'over'
                      AND book = 'pinnacle'
                      AND (game LIKE ? OR game LIKE ?)
                    ORDER BY timestamp DESC LIMIT 1
                """, (f"%{away_team}%", f"%{home_team}%")).fetchone()
                if row and row["line"]:
                    conn.close()
                    return float(row["line"])
                conn.close()
            except Exception:
                pass

        return None


# ===========================================================================
# Ensemble Model
# ===========================================================================

class MLBEnsembleModel:
    """
    Combines Poisson, XGBoost, and Market models into a weighted ensemble.
    Weights: Poisson 0.30, XGBoost 0.40, Market 0.30.
    If a model is unavailable, weights redistribute proportionally.
    """

    def __init__(self):
        self.poisson = PoissonPitcherModel()
        self.xgboost = XGBoostMLBModel()
        self.market = MarketModel()

    def predict_game(self, home_team: str, away_team: str,
                      home_pitcher_id: int = None, away_pitcher_id: int = None,
                      game_pk: int = None, market_total: float = None,
                      game_date: str = None) -> dict:
        """
        Full prediction for a single game.
        Returns ensemble prediction with breakdowns and over/under probabilities.
        """
        if game_date is None:
            game_date = datetime.now().strftime("%Y-%m-%d")

        # Fetch features from pipeline
        features = get_game_features(home_team, away_team,
                                     home_pitcher_id, away_pitcher_id, game_pk)

        if "error" in features:
            return {"error": features["error"]}

        # Run each model
        poisson_result = self.poisson.predict(features)
        xgb_result = self.xgboost.predict(features)
        market_result = self.market.predict(home_team, away_team, game_date, market_total)

        # Collect predictions and weights
        predictions = {}
        weights = {}

        if poisson_result.get("expected_total") is not None:
            predictions["poisson"] = poisson_result["expected_total"]
            weights["poisson"] = WEIGHT_POISSON

        if xgb_result.get("expected_total") is not None:
            predictions["xgboost"] = xgb_result["expected_total"]
            weights["xgboost"] = WEIGHT_XGBOOST

        if market_result.get("expected_total") is not None:
            predictions["market"] = market_result["expected_total"]
            weights["market"] = WEIGHT_MARKET

        if not predictions:
            return {"error": "No models produced predictions"}

        # Normalize weights
        total_weight = sum(weights.values())
        ensemble_total = sum(
            predictions[k] * weights[k] / total_weight
            for k in predictions
        )
        ensemble_total = round(ensemble_total, 2)

        # Probability distribution from Poisson (most principled for this)
        over_probs = poisson_result.get("over_probs", {})

        # Weather description
        wx = features.get("weather", {})
        wx_desc = self._weather_description(features)

        # Edge vs market
        mkt = market_result.get("expected_total")
        edge = round(ensemble_total - mkt, 2) if mkt else None

        # Recommendation
        recommendation = self._generate_recommendation(ensemble_total, mkt, over_probs)

        # Kelly sizing
        kelly_pct = None
        if mkt and over_probs:
            kelly_pct = self._kelly_criterion(ensemble_total, mkt, over_probs)

        # Pitcher names
        hp = features.get("home_pitcher", {})
        ap = features.get("away_pitcher", {})

        result = {
            "game": f"{away_team} @ {home_team}",
            "date": game_date,
            "home_pitcher": hp.get("pitcher_name", "Unknown"),
            "away_pitcher": ap.get("pitcher_name", "Unknown"),
            "model_total": ensemble_total,
            "market_total": mkt,
            "over_prob": over_probs,
            "park_factor": features.get("park_factor_runs"),
            "weather_impact": wx_desc,
            "edge_vs_market": edge,
            "recommendation": recommendation,
            "kelly_pct": kelly_pct,
            "poisson_total": poisson_result.get("expected_total"),
            "xgboost_total": xgb_result.get("expected_total"),
            "market_total_implied": mkt,
            # Diagnostic
            "home_lambda": poisson_result.get("home_lambda"),
            "away_lambda": poisson_result.get("away_lambda"),
            "xgb_features_used": xgb_result.get("features_used"),
            "weights_used": weights,
        }

        return result

    def _weather_description(self, features: dict) -> str:
        """Human-readable weather impact string."""
        if features.get("is_dome"):
            return "Dome (no weather effect)"

        wx = features.get("weather", {})
        if not wx:
            return "No weather data"

        parts = []
        temp = wx.get("temperature_f")
        wind = wx.get("wind_speed_mph")
        wind_dir = wx.get("wind_direction_deg")
        home = features.get("home_team", "")

        total_adj = 0.0
        if temp:
            t_adj = temperature_run_adjustment(temp)
            total_adj += t_adj
            parts.append(f"{temp:.0f}F")

        if wind and wind_dir is not None:
            w_adj = wind_run_adjustment(wind, wind_dir, home, False)
            total_adj += w_adj
            direction = "out" if w_adj > 0 else "in" if w_adj < 0 else "cross"
            parts.append(f"wind {direction} {wind:.0f}mph")

        sign = "+" if total_adj >= 0 else ""
        return f"{sign}{total_adj:.1f} runs ({', '.join(parts)})" if parts else "No weather data"

    def _generate_recommendation(self, model_total: float,
                                  market_total: Optional[float],
                                  over_probs: dict) -> str:
        """Generate betting recommendation."""
        if market_total is None:
            return "NO MARKET LINE AVAILABLE"

        edge = model_total - market_total
        # Look at the nearest half-point line
        nearest_line = round(market_total * 2) / 2

        prob_key = str(nearest_line)
        p_over = over_probs.get(prob_key, 0.5)

        if abs(edge) < 0.3:
            return "NO EDGE (model agrees with market)"

        if edge > 0.3:
            # Implied probability at standard -110 juice
            implied_no_vig = 0.5238  # -110 implied prob without vig
            if p_over > implied_no_vig + 0.03:
                return f"OVER {nearest_line} @ -110 (model: {model_total}, P(over)={p_over:.1%})"
            return f"LEAN OVER {nearest_line} (edge={edge:.1f}, P(over)={p_over:.1%})"

        if edge < -0.3:
            p_under = 1 - p_over
            implied_no_vig = 0.5238
            if p_under > implied_no_vig + 0.03:
                return f"UNDER {nearest_line} @ -110 (model: {model_total}, P(under)={p_under:.1%})"
            return f"LEAN UNDER {nearest_line} (edge={edge:.1f}, P(under)={1-p_over:.1%})"

        return "NO EDGE"

    def _kelly_criterion(self, model_total: float, market_total: float,
                          over_probs: dict) -> Optional[float]:
        """
        Half-Kelly bet sizing as percentage of bankroll.
        Uses the over/under probability vs -110 standard vig.
        """
        nearest_line = round(market_total * 2) / 2
        prob_key = str(nearest_line)
        p_over = over_probs.get(prob_key)

        if p_over is None:
            return None

        edge = model_total - market_total

        if edge > 0:
            # Betting over
            p = p_over
        else:
            # Betting under
            p = 1 - p_over

        # Standard -110 payoff: risk 110 to win 100 => decimal odds 1.909
        decimal_odds = 1.909
        b = decimal_odds - 1  # net profit per unit

        # Kelly: f = (bp - q) / b  where q = 1-p
        q = 1 - p
        kelly_full = (b * p - q) / b if b > 0 else 0

        # Half-Kelly for safety
        kelly_half = kelly_full / 2

        # Clamp to reasonable range
        kelly_half = max(0, min(kelly_half, 0.05))  # cap at 5% of bankroll

        return round(kelly_half * 100, 1)  # return as percentage

    def predict_today(self) -> List[dict]:
        """Predict all of today's scheduled games."""
        conn = get_db()
        today = datetime.now().strftime("%Y-%m-%d")

        games = conn.execute("""
            SELECT * FROM mlb_schedule
            WHERE game_date = ? AND status NOT LIKE '%Final%'
            ORDER BY game_time
        """, (today,)).fetchall()
        conn.close()

        if not games:
            log.warning("No games found for %s. Run pipeline first: python3 mlb_data_pipeline.py", today)
            return []

        results = []
        for g in games:
            gd = dict(g)
            try:
                pred = self.predict_game(
                    home_team=gd["home_team_abbrev"],
                    away_team=gd["away_team_abbrev"],
                    home_pitcher_id=gd.get("home_pitcher_id"),
                    away_pitcher_id=gd.get("away_pitcher_id"),
                    game_pk=gd.get("game_pk"),
                    game_date=today,
                )
                pred["game_pk"] = gd.get("game_pk")
                pred["game_time"] = gd.get("game_time")
                results.append(pred)
            except Exception as e:
                log.error("Failed to predict %s @ %s: %s",
                          gd.get("away_team_abbrev"), gd.get("home_team_abbrev"), e)
                results.append({
                    "game": f"{gd.get('away_team_abbrev')} @ {gd.get('home_team_abbrev')}",
                    "error": str(e),
                })

        return results

    def find_edges(self, min_edge: float = 0.10) -> List[dict]:
        """
        Find betting opportunities where model disagrees with market.
        min_edge is the minimum probability edge (not total difference).
        """
        predictions = self.predict_today()
        edges = []

        for pred in predictions:
            if "error" in pred:
                continue

            market = pred.get("market_total")
            if market is None:
                continue

            over_probs = pred.get("over_prob", {})
            nearest_line = round(market * 2) / 2
            prob_key = str(nearest_line)
            p_over = over_probs.get(prob_key)

            if p_over is None:
                continue

            # -110 breakeven is ~52.38%
            breakeven = 0.5238

            # Check over edge
            over_edge = p_over - breakeven
            under_edge = (1 - p_over) - breakeven

            if over_edge > min_edge:
                pred["edge_type"] = "OVER"
                pred["prob_edge"] = round(over_edge, 4)
                pred["ev_per_unit"] = round(p_over * 0.909 - (1 - p_over), 3)
                edges.append(pred)
            elif under_edge > min_edge:
                pred["edge_type"] = "UNDER"
                pred["prob_edge"] = round(under_edge, 4)
                pred["ev_per_unit"] = round((1 - p_over) * 0.909 - p_over, 3)
                edges.append(pred)

        # Sort by edge size
        edges.sort(key=lambda x: x.get("prob_edge", 0), reverse=True)
        return edges


# ===========================================================================
# Walk-Forward Backtest
# ===========================================================================

def build_training_row(game_row: dict, season: int) -> Optional[dict]:
    """
    Build a training feature row from a completed mlb_games record.
    Returns None if insufficient data.
    """
    home_id = game_row.get("home_team_id")
    away_id = game_row.get("away_team_id")
    home_score = game_row.get("home_score")
    away_score = game_row.get("away_score")

    if home_score is None or away_score is None:
        return None

    actual_total = home_score + away_score

    home_abbrev = game_row.get("home_team_abbrev", "")
    away_abbrev = game_row.get("away_team_abbrev", "")

    # Get features from pipeline
    features = get_game_features(
        home_abbrev, away_abbrev,
        game_row.get("home_pitcher_id"),
        game_row.get("away_pitcher_id"),
        game_row.get("game_pk"),
    )

    if "error" in features:
        return None

    # Convert to XGBoost feature row
    xgb_model = XGBoostMLBModel()
    row = xgb_model.features_from_game(features)
    row["actual_total"] = actual_total
    row["game_date"] = game_row.get("game_date")
    row["game_pk"] = game_row.get("game_pk")
    row["home_team"] = home_abbrev
    row["away_team"] = away_abbrev

    return row


def backtest(start_date: str = "2025-04-01", end_date: str = None,
             retrain_interval_days: int = 7) -> dict:
    """
    Walk-forward backtest of the ensemble model.

    1. Use all data before start_date for initial training
    2. Predict each game day-by-day
    3. Retrain XGBoost every retrain_interval_days
    4. Track accuracy, calibration, simulated ROI
    """
    if end_date is None:
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    conn = get_db()

    log.info("=== Walk-Forward Backtest: %s to %s ===", start_date, end_date)

    # Get all completed games in the backtest window
    all_games = conn.execute("""
        SELECT * FROM mlb_games
        WHERE status LIKE '%Final%' AND innings <= 9
          AND game_date >= ? AND game_date <= ?
        ORDER BY game_date
    """, (start_date, end_date)).fetchall()

    # Get training data (games before the start)
    training_games = conn.execute("""
        SELECT * FROM mlb_games
        WHERE status LIKE '%Final%' AND innings <= 9
          AND game_date < ?
        ORDER BY game_date
    """, (start_date,)).fetchall()
    conn.close()

    if not all_games:
        log.warning("No games found for backtest window")
        return {"error": "No games in window"}

    log.info("Backtest games: %d, Pre-training games: %d",
             len(all_games), len(training_games))

    # Build initial training data
    log.info("Building initial training dataset...")
    training_rows = []
    for g in training_games:
        row = build_training_row(dict(g), datetime.strptime(start_date, "%Y-%m-%d").year)
        if row:
            training_rows.append(row)

    # Train initial XGBoost model
    ensemble = MLBEnsembleModel()
    if len(training_rows) >= 50:
        train_df = pd.DataFrame(training_rows)
        ensemble.xgboost.train(train_df)
        log.info("Initial XGBoost trained on %d games", len(training_rows))
    else:
        log.warning("Insufficient training data (%d games), using fallback", len(training_rows))

    # Walk forward
    results = []
    last_retrain_date = start_date
    errors_abs = []
    correct_over_under = 0
    total_with_market = 0
    simulated_pnl = 0.0
    bets_placed = 0

    for game in all_games:
        gd = dict(game)
        actual_total = gd["home_score"] + gd["away_score"]

        # Check if we need to retrain
        if gd["game_date"] >= (
            datetime.strptime(last_retrain_date, "%Y-%m-%d") +
            timedelta(days=retrain_interval_days)
        ).strftime("%Y-%m-%d"):
            # Add all games since last retrain to training set
            for g2 in all_games:
                g2d = dict(g2)
                if last_retrain_date <= g2d["game_date"] < gd["game_date"]:
                    row = build_training_row(g2d, datetime.strptime(gd["game_date"], "%Y-%m-%d").year)
                    if row:
                        training_rows.append(row)

            if len(training_rows) >= 50:
                train_df = pd.DataFrame(training_rows)
                ensemble.xgboost.train(train_df)

            last_retrain_date = gd["game_date"]

        # Predict
        try:
            pred = ensemble.predict_game(
                home_team=gd["home_team_abbrev"],
                away_team=gd["away_team_abbrev"],
                home_pitcher_id=gd.get("home_pitcher_id"),
                away_pitcher_id=gd.get("away_pitcher_id"),
                game_pk=gd.get("game_pk"),
                game_date=gd["game_date"],
            )

            if "error" in pred:
                continue

            model_total = pred.get("model_total")
            if model_total is None:
                continue

            error = model_total - actual_total
            errors_abs.append(abs(error))

            game_result = {
                "game": pred.get("game"),
                "date": gd["game_date"],
                "model_total": model_total,
                "actual_total": actual_total,
                "error": round(error, 2),
                "poisson_total": pred.get("poisson_total"),
                "xgboost_total": pred.get("xgboost_total"),
                "market_total": pred.get("market_total"),
            }

            # Track over/under accuracy vs market
            market = pred.get("market_total")
            if market:
                total_with_market += 1
                model_side = "over" if model_total > market else "under"
                actual_side = "over" if actual_total > market else "under"
                if actual_total != market:  # exclude pushes
                    if model_side == actual_side:
                        correct_over_under += 1
                    game_result["model_side"] = model_side
                    game_result["actual_side"] = actual_side
                    game_result["correct"] = model_side == actual_side

                # Simulated betting: bet when edge > 3%
                over_probs = pred.get("over_prob", {})
                nearest_line = round(market * 2) / 2
                prob_key = str(nearest_line)
                p_over = over_probs.get(prob_key)

                if p_over is not None:
                    if p_over > 0.56:  # ~3.6% edge over breakeven
                        bets_placed += 1
                        if actual_total > nearest_line:
                            simulated_pnl += 0.909  # win at -110
                        elif actual_total < nearest_line:
                            simulated_pnl -= 1.0
                        # push = no action
                        game_result["bet"] = f"OVER {nearest_line}"
                    elif (1 - p_over) > 0.56:
                        bets_placed += 1
                        if actual_total < nearest_line:
                            simulated_pnl += 0.909
                        elif actual_total > nearest_line:
                            simulated_pnl -= 1.0
                        game_result["bet"] = f"UNDER {nearest_line}"

            results.append(game_result)

        except Exception as e:
            log.debug("Backtest error for game %s: %s", gd.get("game_pk"), e)
            continue

    # Summary statistics
    mae = np.mean(errors_abs) if errors_abs else 0
    rmse = np.sqrt(np.mean([e**2 for e in errors_abs])) if errors_abs else 0

    ou_accuracy = correct_over_under / total_with_market if total_with_market else 0
    roi = simulated_pnl / bets_placed if bets_placed else 0

    summary = {
        "period": f"{start_date} to {end_date}",
        "games_predicted": len(results),
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "over_under_accuracy": round(ou_accuracy, 4),
        "games_with_market": total_with_market,
        "bets_placed": bets_placed,
        "simulated_pnl_units": round(simulated_pnl, 2),
        "roi_pct": round(roi * 100, 2) if bets_placed else 0,
    }

    # Calibration buckets: group by P(over) and check actual over rate
    calibration = _compute_calibration(results)
    summary["calibration"] = calibration

    log.info("=== Backtest Summary ===")
    log.info("Games: %d | MAE: %.2f | RMSE: %.2f", len(results), mae, rmse)
    log.info("O/U Accuracy: %.1f%% (%d/%d)", ou_accuracy * 100,
             correct_over_under, total_with_market)
    log.info("Bets: %d | P&L: %.2f units | ROI: %.1f%%",
             bets_placed, simulated_pnl, roi * 100 if bets_placed else 0)

    # Save results
    output_path = os.path.join(BASE_DIR, "data", "mlb_backtest_results.json")
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "games": results[:50]}, f, indent=2)
    log.info("Results saved to %s", output_path)

    return summary


def _compute_calibration(results: List[dict], buckets: int = 5) -> List[dict]:
    """
    Compute calibration: for games where we predicted P(over)=X%,
    how often did the total actually go over?
    """
    # Not all results have over_prob data from backtest, so this is approximate
    calibration = []
    # Group by predicted side and confidence
    over_correct = sum(1 for r in results if r.get("correct") and r.get("model_side") == "over")
    over_total = sum(1 for r in results if r.get("model_side") == "over")
    under_correct = sum(1 for r in results if r.get("correct") and r.get("model_side") == "under")
    under_total = sum(1 for r in results if r.get("model_side") == "under")

    if over_total:
        calibration.append({
            "side": "over",
            "predictions": over_total,
            "correct": over_correct,
            "accuracy": round(over_correct / over_total, 3),
        })
    if under_total:
        calibration.append({
            "side": "under",
            "predictions": under_total,
            "correct": under_correct,
            "accuracy": round(under_correct / under_total, 3),
        })

    return calibration


# ===========================================================================
# CLI and output formatting
# ===========================================================================

def format_prediction(pred: dict) -> str:
    """Format a single game prediction for console output."""
    if "error" in pred:
        return f"  {pred.get('game', '???')}: ERROR - {pred['error']}"

    lines = []
    lines.append(f"\n  {'='*60}")
    lines.append(f"  {pred.get('game', '???')}  |  {pred.get('date', '')}")
    lines.append(f"  {'='*60}")

    hp = pred.get("home_pitcher", "TBD")
    ap = pred.get("away_pitcher", "TBD")
    lines.append(f"  Pitchers: {ap} vs {hp}")

    lines.append(f"  Park Factor: {pred.get('park_factor', 'N/A')}")
    lines.append(f"  Weather: {pred.get('weather_impact', 'N/A')}")

    lines.append(f"  ---")
    lines.append(f"  Model Total:    {pred.get('model_total', 'N/A')}")
    lines.append(f"    Poisson:      {pred.get('poisson_total', 'N/A')}")
    lines.append(f"    XGBoost:      {pred.get('xgboost_total', 'N/A')}")
    lines.append(f"    Market:       {pred.get('market_total_implied', 'N/A')}")

    edge = pred.get("edge_vs_market")
    if edge is not None:
        sign = "+" if edge >= 0 else ""
        lines.append(f"  Edge vs Market: {sign}{edge}")

    # Over probabilities
    over_probs = pred.get("over_prob", {})
    if over_probs:
        lines.append(f"  ---")
        lines.append(f"  Over Probabilities:")
        for line_val, prob in sorted(over_probs.items(), key=lambda x: float(x[0])):
            bar = "#" * int(float(prob) * 40)
            lines.append(f"    O {line_val:>4s}: {float(prob):>5.1%}  {bar}")

    rec = pred.get("recommendation")
    if rec:
        lines.append(f"  ---")
        lines.append(f"  >> {rec}")

    kelly = pred.get("kelly_pct")
    if kelly and kelly > 0:
        lines.append(f"  Kelly: {kelly}% of bankroll")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MLB Predictive Model - Sports Edge")
    parser.add_argument("--backtest", action="store_true", help="Run walk-forward backtest")
    parser.add_argument("--start", type=str, default="2025-04-01", help="Backtest start date")
    parser.add_argument("--end", type=str, default=None, help="Backtest end date")
    parser.add_argument("--edges", action="store_true", help="Find betting edges")
    parser.add_argument("--game", nargs=2, metavar=("HOME", "AWAY"), help="Predict single game")
    parser.add_argument("--market-total", type=float, default=None, help="Market total for --game")
    parser.add_argument("--train", action="store_true", help="Train XGBoost on available data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.backtest:
        result = backtest(start_date=args.start, end_date=args.end)
        if args.json:
            print(json.dumps(result, indent=2))
        return

    if args.train:
        log.info("Training XGBoost model on all available game data...")
        conn = get_db()
        games = conn.execute("""
            SELECT * FROM mlb_games
            WHERE status LIKE '%Final%' AND innings <= 9
            ORDER BY game_date
        """).fetchall()
        conn.close()

        rows = []
        for g in games:
            row = build_training_row(dict(g), datetime.now().year)
            if row:
                rows.append(row)

        if len(rows) < 50:
            log.warning("Only %d valid training rows. Need 50+ for reliable model.", len(rows))
            if len(rows) == 0:
                print("No training data. Run the data pipeline first:")
                print("  python3 mlb_data_pipeline.py")
                return

        df = pd.DataFrame(rows)
        model = XGBoostMLBModel()
        metrics = model.train(df)
        print(f"Training complete: {json.dumps(metrics, indent=2)}")
        return

    if args.game:
        home, away = args.game
        ensemble = MLBEnsembleModel()
        pred = ensemble.predict_game(home.upper(), away.upper(),
                                      market_total=args.market_total)
        if args.json:
            # Remove large distribution dict for JSON output
            pred.pop("total_distribution", None)
            print(json.dumps(pred, indent=2))
        else:
            print(format_prediction(pred))
        return

    if args.edges:
        ensemble = MLBEnsembleModel()
        edges = ensemble.find_edges(min_edge=0.03)
        if not edges:
            print("No edges found today. Model agrees with market.")
            return

        print(f"\n  MLB EDGES ({datetime.now().strftime('%Y-%m-%d')})")
        print(f"  {'='*60}")
        for pred in edges:
            print(f"\n  {pred.get('game')} | {pred.get('edge_type')} | "
                  f"Edge: {pred.get('prob_edge', 0):.1%} | "
                  f"EV: {pred.get('ev_per_unit', 0):+.3f}/unit")
            print(format_prediction(pred))
        return

    # Default: predict today's games
    ensemble = MLBEnsembleModel()
    predictions = ensemble.predict_today()

    if not predictions:
        print("No games found for today. Make sure the data pipeline is up to date:")
        print("  python3 mlb_data_pipeline.py schedule")
        return

    print(f"\n  MLB PREDICTIONS ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"  Games: {len(predictions)}")

    for pred in predictions:
        print(format_prediction(pred))

    # Summary table
    print(f"\n  {'='*60}")
    print(f"  SUMMARY")
    print(f"  {'='*60}")
    print(f"  {'Game':<20s} {'Model':>6s} {'Poiss':>6s} {'XGB':>6s} {'Mkt':>6s} {'Edge':>6s}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
    for p in predictions:
        if "error" in p:
            continue
        game = p.get("game", "???")[:20]
        model_t = p.get("model_total", 0)
        poiss_t = p.get("poisson_total", 0)
        xgb_t = p.get("xgboost_total", 0)
        mkt_t = p.get("market_total_implied") or 0
        edge = p.get("edge_vs_market") or 0
        print(f"  {game:<20s} {model_t:>6.1f} {poiss_t:>6.1f} {xgb_t:>6.1f} {mkt_t:>6.1f} {edge:>+6.1f}")

    # Save predictions
    output_path = os.path.join(BASE_DIR, "data", f"mlb_predictions_{datetime.now().strftime('%Y%m%d')}.json")
    clean_preds = []
    for p in predictions:
        p_copy = {k: v for k, v in p.items() if k != "total_distribution"}
        clean_preds.append(p_copy)
    with open(output_path, "w") as f:
        json.dump(clean_preds, f, indent=2)
    print(f"\n  Predictions saved to {output_path}")


if __name__ == "__main__":
    main()

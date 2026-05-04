#!/usr/bin/env python3
"""
NHL Historical Backtesting Engine
===================================

Walk-forward backtesting of the Dixon-Coles + XGBoost ensemble model
against multiple seasons of NHL data.

Proves (or disproves) that the model has predictive edge on totals markets.

Architecture:
  1. Download historical game results from NHL API (season schedules per team)
  2. Store in SQLite with season tagging
  3. Walk-forward: train on first N games, predict day-by-day, retrain weekly
  4. Simulate quarter-Kelly betting at -110 juice
  5. Generate comprehensive statistical report + equity curve

NO LOOKAHEAD BIAS: The model only ever sees data before each prediction date.

Usage:
  python3 nhl_backtest_engine.py                     # Full multi-season backtest
  python3 nhl_backtest_engine.py --season 2023       # Single season (2023-24)
  python3 nhl_backtest_engine.py --quick             # Quick 1-month test
  python3 nhl_backtest_engine.py --download-only     # Just download historical data
  python3 nhl_backtest_engine.py --report-only FILE  # Generate report from saved results
"""

import argparse
import json
import math
import os
import sqlite3
import sys
import time
import warnings
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

try:
    from sklearn.isotonic import IsotonicRegression
    HAS_ISOTONIC = True
except ImportError:
    HAS_ISOTONIC = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKTEST_DIR = os.path.join(DATA_DIR, "backtest_results")
BACKTEST_DB = os.path.join(DATA_DIR, "backtest_history.db")

os.makedirs(BACKTEST_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# NHL API
NHL_API_BASE = "https://api-web.nhle.com/v1"

# All 32 NHL teams (current abbreviations)
NHL_TEAMS = [
    "ANA", "ARI", "BOS", "BUF", "CAR", "CGY", "CHI", "COL",
    "CBJ", "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL",
    "NSH", "NJD", "NYI", "NYR", "OTT", "PHI", "PIT", "SJS",
    "SEA", "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH",
]

# Season definitions: start_year -> (season_code, approx_start, approx_end)
SEASONS = {
    2021: ("20212022", "2021-10-12", "2022-04-29"),
    2022: ("20222023", "2022-10-07", "2023-04-14"),
    2023: ("20232024", "2023-10-10", "2024-04-18"),
    2024: ("20242025", "2024-10-04", "2025-04-17"),
}

# Betting parameters
STANDARD_JUICE = -110          # American odds for both sides
DEFAULT_TOTAL_LINE = 6.0       # Default NHL totals line when unknown
MIN_EDGE_THRESHOLD = 0.03      # 3% minimum edge to bet
KELLY_FRACTION = 0.25          # Quarter-Kelly
MAX_BET_FRACTION = 0.03        # Cap at 3% of bankroll per bet
INITIAL_BANKROLL = 5000.0

# Dixon-Coles backtest config
DC_RETRAIN_INTERVAL_DAYS = 14   # Retrain every 14 days
DC_MIN_TRAINING_GAMES = 50     # Minimum games before first prediction
DC_HALF_LIFE = 30              # Exponential decay half-life in games

# Rate limiting
API_DELAY_SECONDS = 0.5

# Browser-like headers
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Team abbreviation normalization (NHL API can return different abbrevs)
TEAM_NORMALIZE = {
    "LAK": "LAK", "L.A": "LAK", "LA": "LAK",
    "NJD": "NJD", "N.J": "NJD", "NJ": "NJD",
    "SJS": "SJS", "S.J": "SJS", "SJ": "SJS",
    "TBL": "TBL", "T.B": "TBL", "TB": "TBL",
    "VGK": "VGK", "VEG": "VGK",
    "WSH": "WSH", "WAS": "WSH",
    "CBJ": "CBJ", "CLB": "CBJ",
    "MTL": "MTL", "MON": "MTL",
    "UTA": "UTA", "ARI": "ARI",
}


def normalize_team(abbrev: str) -> str:
    """Normalize team abbreviation."""
    if not abbrev:
        return abbrev
    clean = abbrev.strip().upper()
    return TEAM_NORMALIZE.get(clean, clean)


# ===========================================================================
# Database
# ===========================================================================

def get_backtest_db() -> sqlite3.Connection:
    """Open the backtest-specific SQLite database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(BACKTEST_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_backtest_schema(conn: sqlite3.Connection) -> None:
    """Create tables for historical game data."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS historical_games (
            game_id INTEGER PRIMARY KEY,
            season TEXT NOT NULL,
            game_date TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_score INTEGER,
            away_score INTEGER,
            total_goals INTEGER,
            game_outcome TEXT,
            game_type INTEGER DEFAULT 2,
            venue TEXT,
            UNIQUE(game_id)
        );

        CREATE INDEX IF NOT EXISTS idx_hist_date
            ON historical_games(game_date);
        CREATE INDEX IF NOT EXISTS idx_hist_season
            ON historical_games(season);
        CREATE INDEX IF NOT EXISTS idx_hist_teams
            ON historical_games(home_team, away_team);

        CREATE TABLE IF NOT EXISTS backtest_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            game_id INTEGER,
            game_date TEXT,
            season TEXT,
            home_team TEXT,
            away_team TEXT,
            actual_total INTEGER,
            market_line REAL,
            dc_predicted_total REAL,
            dc_over_prob REAL,
            ensemble_over_prob REAL,
            model_edge REAL,
            bet_side TEXT,
            bet_size REAL,
            bet_won INTEGER,
            pnl REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_bt_run
            ON backtest_predictions(run_id);

        CREATE TABLE IF NOT EXISTS backtest_runs (
            run_id TEXT PRIMARY KEY,
            seasons TEXT,
            started_at TEXT,
            completed_at TEXT,
            total_games INTEGER,
            total_bets INTEGER,
            win_rate REAL,
            roi REAL,
            total_pnl REAL,
            max_drawdown REAL,
            sharpe_ratio REAL,
            config TEXT
        );
    """)
    conn.commit()


# ===========================================================================
# Historical Data Download
# ===========================================================================

def _nhl_api_get(endpoint: str) -> Optional[dict]:
    """Fetch from NHL API with rate limiting."""
    import requests
    url = f"{NHL_API_BASE}/{endpoint}"
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            print(f"  NHL API {endpoint}: HTTP {resp.status_code}")
            return None
        return resp.json()
    except Exception as e:
        print(f"  NHL API {endpoint} failed: {e}")
        return None


def download_season_games(season_start_year: int,
                          conn: sqlite3.Connection) -> int:
    """
    Download all regular-season game results for a given season.

    Uses the NHL API club-schedule-season endpoint for each team,
    then deduplicates (each game appears for both home and away team).
    """
    if season_start_year not in SEASONS:
        print(f"Unknown season: {season_start_year}")
        return 0

    season_code, _, _ = SEASONS[season_start_year]
    season_label = str(season_start_year)

    # Check how many we already have
    existing = conn.execute(
        "SELECT COUNT(*) FROM historical_games WHERE season=?",
        (season_label,)
    ).fetchone()[0]

    if existing > 1200:
        print(f"  Season {season_start_year}-{season_start_year+1}: "
              f"already have {existing} games, skipping download")
        return existing

    print(f"\nDownloading season {season_start_year}-{season_start_year+1} "
          f"(code: {season_code})...")

    seen_game_ids = set()
    game_count = 0

    # Collect existing game IDs to avoid re-inserting
    for row in conn.execute(
        "SELECT game_id FROM historical_games WHERE season=?",
        (season_label,)
    ):
        seen_game_ids.add(row[0])

    teams_to_fetch = list(NHL_TEAMS)
    # Arizona -> Utah transition: 2024+ use UTA, before that ARI
    if season_start_year < 2024:
        if "UTA" in teams_to_fetch:
            teams_to_fetch.remove("UTA")
        if "ARI" not in teams_to_fetch:
            teams_to_fetch.append("ARI")
    else:
        if "ARI" in teams_to_fetch:
            teams_to_fetch.remove("ARI")

    # Seattle joined in 2021-22
    if season_start_year < 2021 and "SEA" in teams_to_fetch:
        teams_to_fetch.remove("SEA")

    for i, team in enumerate(teams_to_fetch):
        endpoint = f"club-schedule-season/{team}/{season_code}"
        data = _nhl_api_get(endpoint)
        time.sleep(API_DELAY_SECONDS)

        if not data or "games" not in data:
            print(f"  {team}: no data")
            continue

        team_games = 0
        for g in data["games"]:
            game_id = g.get("id")
            if not game_id or game_id in seen_game_ids:
                continue

            # Only regular season (gameType == 2)
            game_type = g.get("gameType", 0)
            if game_type != 2:
                continue

            # Only completed games
            state = g.get("gameState", "")
            if state not in ("OFF", "FINAL"):
                continue

            home_team_data = g.get("homeTeam", {})
            away_team_data = g.get("awayTeam", {})

            home_abbrev = normalize_team(
                home_team_data.get("abbrev", "")
            )
            away_abbrev = normalize_team(
                away_team_data.get("abbrev", "")
            )
            home_score = home_team_data.get("score")
            away_score = away_team_data.get("score")

            if home_score is None or away_score is None:
                continue

            total = home_score + away_score
            game_date = g.get("gameDate", "")
            if not game_date:
                start = g.get("startTimeUTC", "")
                if start:
                    game_date = start[:10]

            # Game outcome
            outcome = g.get("gameOutcome", {})
            if isinstance(outcome, dict):
                outcome_type = outcome.get("lastPeriodType", "REG")
            else:
                outcome_type = "REG"

            venue = g.get("venue", {})
            venue_name = ""
            if isinstance(venue, dict):
                venue_name = venue.get("default", "")

            try:
                conn.execute("""
                    INSERT OR IGNORE INTO historical_games
                    (game_id, season, game_date, home_team, away_team,
                     home_score, away_score, total_goals, game_outcome,
                     game_type, venue)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_id, season_label, game_date,
                    home_abbrev, away_abbrev,
                    home_score, away_score, total,
                    outcome_type, game_type, venue_name,
                ))
                seen_game_ids.add(game_id)
                game_count += 1
                team_games += 1
            except sqlite3.IntegrityError:
                pass

        if (i + 1) % 8 == 0:
            conn.commit()
            print(f"  Progress: {i+1}/{len(teams_to_fetch)} teams, "
                  f"{game_count} new games")

    conn.commit()

    total_in_db = conn.execute(
        "SELECT COUNT(*) FROM historical_games WHERE season=?",
        (season_label,)
    ).fetchone()[0]

    print(f"  Season {season_start_year}-{season_start_year+1}: "
          f"{game_count} new games downloaded, {total_in_db} total in DB")
    return total_in_db


def download_historical_games(seasons: list, conn: Optional[sqlite3.Connection] = None) -> dict:
    """
    Download game results for multiple seasons.

    Returns dict of {season: game_count}.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_backtest_db()
        init_backtest_schema(conn)

    results = {}
    for season in seasons:
        count = download_season_games(season, conn)
        results[season] = count

    if own_conn:
        conn.close()

    return results


# ===========================================================================
# Dixon-Coles Model (self-contained for backtesting)
# ===========================================================================

class BacktestDixonColes:
    """
    Stripped-down Dixon-Coles for backtesting.

    Pure Poisson + correlation adjustment, fitted via MLE with time weighting.
    No external dependencies beyond numpy/scipy.
    """

    def __init__(self, half_life: int = DC_HALF_LIFE):
        self.half_life = half_life
        self.teams = []
        self.params = {}
        self.home_adv = 0.15
        self.rho = 0.0
        self.fitted = False
        self.league_avg = 3.10
        self.n_games_fit = 0

    @staticmethod
    def _tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
        """Dixon-Coles correlation correction for low scores."""
        if x == 0 and y == 0:
            return 1.0 - lam * mu * rho
        elif x == 0 and y == 1:
            return 1.0 + lam * rho
        elif x == 1 and y == 0:
            return 1.0 + mu * rho
        elif x == 1 and y == 1:
            return 1.0 - rho
        return 1.0

    def _time_weight(self, days_ago: float) -> float:
        """Exponential decay. Half-life in games (~2 days per game)."""
        games_ago = max(days_ago, 0) / 2.0
        return math.exp(-math.log(2) * games_ago / self.half_life)

    def fit(self, games: list, reference_date: str) -> bool:
        """
        Fit on a list of game dicts.

        Each game: {home_team, away_team, home_score, away_score, game_date}
        reference_date: YYYY-MM-DD string for time weighting.
        """
        from scipy.optimize import minimize
        from scipy.stats import poisson

        if len(games) < DC_MIN_TRAINING_GAMES:
            return False

        teams = sorted(set(
            [g["home_team"] for g in games] + [g["away_team"] for g in games]
        ))
        n = len(teams)
        tidx = {t: i for i, t in enumerate(teams)}

        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")

        # Precompute arrays
        home_goals = np.array([g["home_score"] for g in games], dtype=float)
        away_goals = np.array([g["away_score"] for g in games], dtype=float)
        home_idx = np.array([tidx[g["home_team"]] for g in games])
        away_idx = np.array([tidx[g["away_team"]] for g in games])

        weights = np.array([
            self._time_weight(
                (ref_dt - datetime.strptime(g["game_date"][:10], "%Y-%m-%d")
                 ).days
            )
            for g in games
        ])

        def neg_ll(p):
            atk = p[:n]
            dfn = p[n:2*n]
            ha = p[2*n]
            rho_val = p[2*n + 1]

            ll = 0.0
            for idx in range(len(home_goals)):
                hi, ai = home_idx[idx], away_idx[idx]
                lam = max(math.exp(atk[hi] + dfn[ai] + ha), 0.01)
                mu = max(math.exp(atk[ai] + dfn[hi]), 0.01)

                hg = int(home_goals[idx])
                ag = int(away_goals[idx])

                prob = (poisson.pmf(hg, lam) *
                        poisson.pmf(ag, mu) *
                        self._tau(hg, ag, lam, mu, rho_val))

                ll += weights[idx] * (math.log(prob) if prob > 0 else -30.0)

            # Regularization
            ll -= 10.0 * (np.mean(atk) - math.log(self.league_avg)) ** 2
            ll -= 5.0 * np.mean(dfn) ** 2
            return -ll

        x0 = np.concatenate([
            np.full(n, math.log(self.league_avg)),
            np.zeros(n),
            [0.15, 0.0]
        ])

        bounds = (
            [(None, None)] * (2 * n) +
            [(-0.1, 0.5)] +    # home advantage
            [(-0.5, 0.5)]      # rho
        )

        result = minimize(neg_ll, x0, method="L-BFGS-B", bounds=bounds,
                          options={"maxiter": 100, "ftol": 1e-5})

        opt = result.x
        self.teams = teams
        self.params = {}
        for i, t in enumerate(teams):
            self.params[t] = {"attack": opt[i], "defense": opt[n + i]}
        self.home_adv = opt[2 * n]
        self.rho = opt[2 * n + 1]
        self.fitted = True
        self.n_games_fit = len(games)
        return True

    def predict_expected_total(self, home: str, away: str) -> Optional[float]:
        """Expected total goals for a matchup."""
        if not self.fitted:
            return None

        h_atk = self.params.get(home, {}).get("attack", math.log(self.league_avg))
        h_def = self.params.get(home, {}).get("defense", 0.0)
        a_atk = self.params.get(away, {}).get("attack", math.log(self.league_avg))
        a_def = self.params.get(away, {}).get("defense", 0.0)

        lam = math.exp(h_atk + a_def + self.home_adv)
        mu = math.exp(a_atk + h_def)
        return lam + mu

    def predict_over_prob(self, home: str, away: str,
                          line: float) -> Optional[float]:
        """P(total > line)."""
        from scipy.stats import poisson

        if not self.fitted:
            return None

        h_atk = self.params.get(home, {}).get("attack", math.log(self.league_avg))
        h_def = self.params.get(home, {}).get("defense", 0.0)
        a_atk = self.params.get(away, {}).get("attack", math.log(self.league_avg))
        a_def = self.params.get(away, {}).get("defense", 0.0)

        lam = math.exp(h_atk + a_def + self.home_adv)
        mu = math.exp(a_atk + h_def)

        max_g = 12
        prob_over = 0.0
        for i in range(max_g + 1):
            for j in range(max_g + 1):
                if i + j > line:
                    p = (poisson.pmf(i, lam) *
                         poisson.pmf(j, mu) *
                         self._tau(i, j, lam, mu, self.rho))
                    prob_over += p

        return min(max(prob_over, 0.001), 0.999)


# ===========================================================================
# Elo Rating System (self-contained for backtesting)
# ===========================================================================

class BacktestElo:
    """
    MOV-scaled Elo for backtesting.

    K = 20 * ((MOV+3)^0.8) / (7.5 + 0.006 * |elo_diff|)
    25% mean reversion between seasons.
    """

    INITIAL = 1500.0
    REVERSION = 0.25

    def __init__(self):
        self.ratings = {}
        self._season = None

    def get(self, team: str) -> float:
        return self.ratings.get(team, self.INITIAL)

    def season_revert(self):
        for t in self.ratings:
            self.ratings[t] = self.INITIAL * self.REVERSION + self.ratings[t] * (1.0 - self.REVERSION)

    def update(self, home: str, away: str, home_score: int, away_score: int,
               season: str = None):
        if season and season != self._season:
            if self._season is not None:
                self.season_revert()
            self._season = season

        he = self.get(home)
        ae = self.get(away)
        diff = he - ae + 65.0
        exp_h = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        actual_h = 1.0 if home_score > away_score else (0.0 if home_score < away_score else 0.5)
        mov = abs(home_score - away_score)
        k = 20.0 * ((mov + 3) ** 0.8) / (7.5 + 0.006 * abs(diff))
        delta = k * (actual_h - exp_h)
        self.ratings[home] = he + delta
        self.ratings[away] = ae - delta


# ===========================================================================
# Isotonic Calibration (self-contained for backtesting)
# ===========================================================================

class BacktestCalibrator:
    """Isotonic calibration for backtest over/under probabilities."""

    def __init__(self):
        self.iso = None
        self.fitted = False

    def fit(self, pred_probs, actuals):
        """Fit on arrays of predicted probabilities and 0/1 outcomes."""
        if not HAS_ISOTONIC or len(pred_probs) < 20:
            return
        self.iso = IsotonicRegression(y_min=0.01, y_max=0.99, out_of_bounds="clip")
        self.iso.fit(np.asarray(pred_probs), np.asarray(actuals))
        self.fitted = True

    def calibrate(self, prob: float) -> float:
        if not self.fitted or self.iso is None:
            return prob
        return float(np.clip(self.iso.predict(np.array([prob]))[0], 0.01, 0.99))


# ===========================================================================
# Goalie GSAX Cache (loads from MoneyPuck data in SQLite)
# ===========================================================================

class GoalieGSAXCache:
    """
    Loads team-level goalie quality (games-weighted GSAX per game)
    from MoneyPuck data stored in sports_edge.db.

    For each team+season, computes a games-weighted average GSAX/game
    across all goalies with 10+ games. This represents expected goalie
    quality for that team in that season.

    Used as a feature adjustment: elite goalies suppress totals,
    weak goalies inflate them.
    """

    def __init__(self):
        self.team_gsax = {}  # (team, season) -> gsax_per_game
        self._loaded = False

    def load(self):
        """Load all goalie data from sports_edge.db."""
        db_path = os.path.join(DATA_DIR, "sports_edge.db")
        if not os.path.exists(db_path):
            return
        try:
            conn = sqlite3.connect(db_path)
            rows = conn.execute("""
                SELECT team, season, name, games_played, gsax
                FROM nhl_goalies
                WHERE situation = 'all' AND games_played >= 10
                ORDER BY team, season, games_played DESC
            """).fetchall()
            conn.close()

            # Group by (team, season) and compute games-weighted average GSAX/game
            from collections import defaultdict
            team_data = defaultdict(list)
            for team, season, name, gp, gsax in rows:
                if gsax is not None and gp > 0:
                    team_data[(team, season)].append((gp, gsax / gp))

            for key, goalies in team_data.items():
                total_gp = sum(gp for gp, _ in goalies)
                if total_gp > 0:
                    weighted_gsax = sum(gp * gsax_pg for gp, gsax_pg in goalies) / total_gp
                    self.team_gsax[key] = weighted_gsax

            self._loaded = True
        except Exception:
            pass

    def get(self, team: str, season: str) -> float:
        """Get team's goalie GSAX per game. Returns 0.0 if unknown."""
        if not self._loaded:
            self.load()
        return self.team_gsax.get((team, season), 0.0)

    def get_adjustment(self, home: str, away: str, season: str) -> float:
        """
        Compute goalie-based total adjustment.

        Positive GSAX = goalie saves more than expected = fewer goals = lower total.
        Each team's goalie quality affects the OTHER team's scoring.

        Returns adjustment to predicted total (negative = lower total expected).

        Scaling is conservative (0.3x) because Dixon-Coles already partially
        captures goalie quality through team defense parameters. We're only
        adding the residual signal DC misses - the goalie-specific component
        beyond team-level defense.
        """
        h_gsax = self.get(home, season)
        a_gsax = self.get(away, season)
        # Better goalies = fewer goals allowed = lower total
        # Conservative: DC already has some goalie signal via team defense
        return -(h_gsax + a_gsax) * 0.3


# ===========================================================================
# Residual XGBoost Model
# ===========================================================================

class ResidualXGBoost:
    """
    XGBoost model that learns to correct Dixon-Coles prediction errors.

    Instead of predicting totals directly, this model predicts the RESIDUAL
    (actual_total - dc_predicted_total) from enhanced features.

    Training data: historical games where we have both DC prediction and actual result.
    Features: rest days, Elo, rolling averages, etc.
    Target: actual_total - dc_predicted_total

    Walk-forward: retrained alongside DC model, only on past data.
    """

    FEATURE_COLS = [
        "home_rest_days", "away_rest_days", "home_b2b", "away_b2b",
        "home_gf_l5", "home_ga_l5", "away_gf_l5", "away_ga_l5",
        "home_gf_l10", "home_ga_l10", "away_gf_l10", "away_ga_l10",
        "home_gf_l20", "home_ga_l20", "away_gf_l20", "away_ga_l20",
        "home_gf_season", "home_ga_season", "away_gf_season", "away_ga_season",
        "home_elo", "away_elo", "elo_diff",
        "home_home_wr_l10", "away_road_wr_l10",
        "implied_total",
    ]

    MIN_TRAINING_SAMPLES = 200  # Don't train on fewer than this

    def __init__(self):
        self.model = None
        self.fitted = False

    def fit(self, training_data: list, dc_model, elo: 'BacktestElo',
            current_date: str):
        """
        Train on residuals from past games.

        Args:
            training_data: list of game dicts (with actual results)
            dc_model: fitted BacktestDixonColes model
            elo: BacktestElo instance
            current_date: only use games before this date
        """
        if not HAS_XGB:
            return

        rows = []
        for game in training_data:
            gd = game["game_date"]
            if gd >= current_date:
                continue

            home = game["home_team"]
            away = game["away_team"]
            actual = game["total_goals"]

            # Get DC prediction for this game
            dc_pred = dc_model.predict_expected_total(home, away)
            if dc_pred is None:
                continue

            # Get features (point-in-time)
            feats = compute_backtest_features(home, away, gd, training_data, elo)

            # Build feature vector
            fv = [feats.get(col, 0.0) for col in self.FEATURE_COLS]
            residual = actual - dc_pred
            rows.append((fv, residual))

        if len(rows) < self.MIN_TRAINING_SAMPLES:
            return

        X = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])

        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.7,
            min_child_weight=10,
            reg_alpha=1.0,
            reg_lambda=5.0,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X, y)
        self.fitted = True

    def predict_residual(self, feats: dict) -> float:
        """Predict the residual (correction to DC total) from features."""
        if not self.fitted or self.model is None:
            return 0.0

        fv = np.array([[feats.get(col, 0.0) for col in self.FEATURE_COLS]])
        pred = float(self.model.predict(fv)[0])
        # Clamp to reasonable range: DC is usually within ~2 goals
        return max(-1.5, min(1.5, pred))


# ===========================================================================
# Enhanced Features for Backtesting (point-in-time)
# ===========================================================================

def compute_backtest_features(home: str, away: str, game_date: str,
                               past_games: list, elo: BacktestElo) -> dict:
    """
    Compute enhanced features from historical game list.
    All point-in-time: only uses games before game_date.

    Returns dict of feature_name -> value.
    """
    features = {}
    before = [g for g in past_games if g["game_date"] < game_date]

    def tg(team):
        return [g for g in before
                if g["home_team"] == team or g["away_team"] == team]

    def gf(team, g):
        return g["home_score"] if g["home_team"] == team else g["away_score"]

    def ga(team, g):
        return g["away_score"] if g["home_team"] == team else g["home_score"]

    from datetime import datetime as _dt
    try:
        gdt = _dt.strptime(game_date[:10], "%Y-%m-%d")
    except ValueError:
        gdt = _dt.now()

    for pfx, team in [("home", home), ("away", away)]:
        team_hist = tg(team)
        team_hist.sort(key=lambda g: g["game_date"], reverse=True)

        # Multi-window rolling goals
        for w in [5, 10, 20]:
            wg = team_hist[:w]
            n = len(wg)
            if n > 0:
                features[f"{pfx}_gf_l{w}"] = sum(gf(team, g) for g in wg) / n
                features[f"{pfx}_ga_l{w}"] = sum(ga(team, g) for g in wg) / n
            else:
                features[f"{pfx}_gf_l{w}"] = 3.0
                features[f"{pfx}_ga_l{w}"] = 3.0

        # Season-level
        n_all = len(team_hist)
        if n_all > 0:
            features[f"{pfx}_gf_season"] = sum(gf(team, g) for g in team_hist) / n_all
            features[f"{pfx}_ga_season"] = sum(ga(team, g) for g in team_hist) / n_all
        else:
            features[f"{pfx}_gf_season"] = 3.0
            features[f"{pfx}_ga_season"] = 3.0

        # Home/away record L10
        hg = [g for g in team_hist if g["home_team"] == team][:10]
        ag = [g for g in team_hist if g["away_team"] == team][:10]
        features[f"{pfx}_home_wr_l10"] = (
            sum(1 for g in hg if gf(team, g) > ga(team, g)) / max(len(hg), 1)
        )
        features[f"{pfx}_road_wr_l10"] = (
            sum(1 for g in ag if gf(team, g) > ga(team, g)) / max(len(ag), 1)
        )

        # Rest days
        if team_hist:
            try:
                last_dt = _dt.strptime(team_hist[0]["game_date"][:10], "%Y-%m-%d")
                rest = (gdt - last_dt).days
            except ValueError:
                rest = 2
        else:
            rest = 3
        features[f"{pfx}_rest_days"] = min(rest, 7)
        features[f"{pfx}_b2b"] = 1 if rest <= 1 else 0

    # Elo
    features["home_elo"] = elo.get(home)
    features["away_elo"] = elo.get(away)
    features["elo_diff"] = features["home_elo"] - features["away_elo"]

    # Implied total from rolling averages
    features["implied_total"] = (
        (features["home_gf_l10"] + features["away_ga_l10"]) / 2 +
        (features["away_gf_l10"] + features["home_ga_l10"]) / 2
    )

    return features


# ===========================================================================
# Betting Math
# ===========================================================================

def american_to_implied(american: float) -> float:
    """Convert American odds to implied probability (including vig)."""
    if american < 0:
        return abs(american) / (abs(american) + 100.0)
    else:
        return 100.0 / (american + 100.0)


def implied_to_decimal(implied: float) -> float:
    """Convert implied probability to decimal odds."""
    if implied <= 0:
        return 99.0
    return 1.0 / implied


def breakeven_prob(american: float) -> float:
    """Breakeven probability at given American odds."""
    return american_to_implied(american)


def kelly_bet_size(edge: float, odds_decimal: float,
                   fraction: float = KELLY_FRACTION,
                   max_fraction: float = MAX_BET_FRACTION) -> float:
    """
    Quarter-Kelly bet sizing.

    edge: model_prob - breakeven_prob
    odds_decimal: decimal odds (e.g. 1.909 for -110)
    Returns fraction of bankroll to bet.
    """
    if edge <= 0:
        return 0.0

    b = odds_decimal - 1.0  # net payout per unit
    p = breakeven_prob(STANDARD_JUICE) + edge  # model probability

    q = 1.0 - p
    if b <= 0:
        return 0.0

    full_kelly = (b * p - q) / b
    fractional = full_kelly * fraction

    return min(max(fractional, 0.0), max_fraction)


# ===========================================================================
# Walk-Forward Backtest
# ===========================================================================

def get_games_as_list(conn: sqlite3.Connection, season: str,
                      before_date: Optional[str] = None,
                      after_date: Optional[str] = None) -> list:
    """Get games from DB as list of dicts, optionally filtered by date."""
    query = "SELECT * FROM historical_games WHERE season=?"
    params = [season]

    if before_date:
        query += " AND game_date < ?"
        params.append(before_date)
    if after_date:
        query += " AND game_date >= ?"
        params.append(after_date)

    query += " ORDER BY game_date"

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def walk_forward_backtest(
    conn: sqlite3.Connection,
    target_season: int,
    prior_seasons: list = None,
    train_months: int = 2,
    retrain_days: int = DC_RETRAIN_INTERVAL_DAYS,
    run_id: Optional[str] = None,
    variable_line: bool = False,
    use_calibration: bool = False,
    use_enhanced: bool = False,
    use_xgboost: bool = False,
) -> dict:
    """
    Walk-forward backtest for one season.

    1. Collect all games from prior seasons + first train_months of target
    2. Fit Dixon-Coles
    3. For each subsequent day with games:
       a. Predict each game (over/under probability)
       b. Compare to market line (default 6.0 or infer from data)
       c. If edge > threshold, place simulated bet
       d. Record result
    4. Retrain every retrain_days with new data included

    Returns results dict with all predictions and P&L.
    """
    if run_id is None:
        run_id = f"wf_{target_season}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    season_label = str(target_season)
    _, season_start, season_end = SEASONS[target_season]

    # Determine training cutoff: first train_months of the season
    start_dt = datetime.strptime(season_start, "%Y-%m-%d")
    train_cutoff_dt = start_dt + timedelta(days=train_months * 30)
    train_cutoff = train_cutoff_dt.strftime("%Y-%m-%d")

    # Seasons to include for training
    training_seasons = [season_label]
    if prior_seasons:
        training_seasons = [str(s) for s in prior_seasons] + [season_label]

    print(f"\n{'='*60}")
    print(f"WALK-FORWARD BACKTEST: {target_season}-{target_season+1}")
    print(f"{'='*60}")
    print(f"Training seasons: {training_seasons}")
    print(f"Training cutoff: {train_cutoff}")
    print(f"Retrain interval: every {retrain_days} days")

    # Get all games for this season
    all_season_games = get_games_as_list(conn, season_label)
    if not all_season_games:
        print(f"  No games found for season {season_label}")
        return {"season": target_season, "season_label": f"{target_season}-{target_season+1}",
                "predictions": [], "total_bets": 0, "wins": 0, "losses": 0,
                "pushes": 0, "win_rate": 0, "total_wagered": 0, "total_pnl": 0,
                "roi": 0, "max_drawdown": 0, "sharpe_ratio": 0,
                "games_predicted": 0, "final_bankroll": INITIAL_BANKROLL,
                "daily_returns": [], "bankroll_history": [INITIAL_BANKROLL],
                "model_games_fit": 0, "run_id": run_id, "error": "no_data"}

    # Split into training and prediction sets
    train_games_only = [g for g in all_season_games
                        if g["game_date"] < train_cutoff]
    predict_games = [g for g in all_season_games
                     if g["game_date"] >= train_cutoff]

    # Also get prior season games for training
    prior_games = []
    if prior_seasons:
        for ps in prior_seasons:
            prior_games.extend(
                get_games_as_list(conn, str(ps))
            )

    print(f"  Prior season training games: {len(prior_games)}")
    print(f"  Current season training games: {len(train_games_only)}")
    print(f"  Games to predict: {len(predict_games)}")

    if len(predict_games) == 0:
        print("  No games to predict after training period")
        return {"season": target_season, "season_label": f"{target_season}-{target_season+1}",
                "predictions": [], "total_bets": 0, "wins": 0, "losses": 0,
                "pushes": 0, "win_rate": 0, "total_wagered": 0, "total_pnl": 0,
                "roi": 0, "max_drawdown": 0, "sharpe_ratio": 0,
                "games_predicted": 0, "final_bankroll": INITIAL_BANKROLL,
                "daily_returns": [], "bankroll_history": [INITIAL_BANKROLL],
                "model_games_fit": 0, "run_id": run_id, "error": "no_predict"}

    # Group prediction games by date
    games_by_date = defaultdict(list)
    for g in predict_games:
        games_by_date[g["game_date"]].append(g)

    prediction_dates = sorted(games_by_date.keys())
    print(f"  Prediction dates: {prediction_dates[0]} to {prediction_dates[-1]}")
    print(f"  ({len(prediction_dates)} unique dates)")

    # Initialize model
    model = BacktestDixonColes(half_life=DC_HALF_LIFE)

    # Initialize Elo system (always built, features optional)
    elo = BacktestElo()
    # Build Elo from all prior + training games in chronological order
    all_for_elo = sorted(
        prior_games + train_games_only,
        key=lambda g: g["game_date"]
    )
    for g in all_for_elo:
        elo.update(g["home_team"], g["away_team"],
                   g["home_score"], g["away_score"],
                   season=g.get("season"))

    # Initialize calibrator
    calibrator = BacktestCalibrator()

    # Initialize goalie GSAX cache
    goalie_cache = GoalieGSAXCache()
    if use_enhanced:
        goalie_cache.load()
        if goalie_cache._loaded:
            h_sample = goalie_cache.get(predict_games[0]["home_team"] if predict_games else "TOR", season_label)
            print(f"  Goalie GSAX cache loaded ({len(goalie_cache.team_gsax)} team-seasons)")

    # Initialize residual XGBoost
    residual_xgb = ResidualXGBoost() if use_xgboost and HAS_XGB else None
    if use_xgboost and not HAS_XGB:
        print("  WARNING: XGBoost not available, --xgboost flag ignored")

    # Initial training data: prior seasons + early current season
    current_training = prior_games + train_games_only

    # Fit initial model
    print(f"\n  Fitting initial model on {len(current_training)} games...")
    fit_ok = model.fit(current_training, train_cutoff)
    if not fit_ok:
        print(f"  WARNING: Initial fit failed ({len(current_training)} games). "
              f"Need at least {DC_MIN_TRAINING_GAMES}.")
    last_retrain_date = train_cutoff

    # Fit initial calibration on training data holdout
    if use_calibration and model.fitted:
        n_train = len(current_training)
        cal_split = int(n_train * 0.7)
        if cal_split >= DC_MIN_TRAINING_GAMES and n_train - cal_split >= 20:
            cal_train = current_training[:cal_split]
            cal_holdout = current_training[cal_split:]
            cal_model = BacktestDixonColes(half_life=DC_HALF_LIFE)
            if cal_model.fit(cal_train, cal_holdout[0]["game_date"]):
                cal_preds = []
                cal_actuals = []
                for g in cal_holdout:
                    p = cal_model.predict_over_prob(
                        g["home_team"], g["away_team"], DEFAULT_TOTAL_LINE
                    )
                    if p is not None:
                        cal_preds.append(p)
                        cal_actuals.append(1 if g["total_goals"] > DEFAULT_TOTAL_LINE else 0)
                calibrator.fit(cal_preds, cal_actuals)
                if calibrator.fitted:
                    print(f"  Calibration: fitted on {len(cal_preds)} holdout games")

    if variable_line:
        print(f"  Variable line mode: using DC predicted total rounded to 0.5")
    if use_calibration:
        print(f"  Calibration: {'active' if calibrator.fitted else 'not fitted'}")
    if use_enhanced:
        print(f"  Enhanced features: Elo + rolling windows + rest days")

    # Tracking
    predictions = []
    bankroll = INITIAL_BANKROLL
    peak_bankroll = INITIAL_BANKROLL
    max_drawdown = 0.0
    daily_returns = []
    prev_bankroll = INITIAL_BANKROLL

    total_bets = 0
    wins = 0
    losses = 0
    pushes = 0

    games_processed = 0
    retrain_count = 0

    for date_idx, date_str in enumerate(prediction_dates):
        date_games = games_by_date[date_str]

        # Check if we need to retrain
        days_since = (
            datetime.strptime(date_str, "%Y-%m-%d") -
            datetime.strptime(last_retrain_date, "%Y-%m-%d")
        ).days

        if days_since >= retrain_days:
            # Add all games up to (but not including) today -- NO LOOKAHEAD
            games_before_today = [
                g for g in all_season_games if g["game_date"] < date_str
            ]
            current_training = prior_games + games_before_today
            fit_ok = model.fit(current_training, date_str)
            if fit_ok:
                retrain_count += 1

                # Re-fit calibration on retrain
                if use_calibration:
                    n_ct = len(current_training)
                    cs = int(n_ct * 0.7)
                    if cs >= DC_MIN_TRAINING_GAMES and n_ct - cs >= 20:
                        cm = BacktestDixonColes(half_life=DC_HALF_LIFE)
                        if cm.fit(current_training[:cs], current_training[cs]["game_date"]):
                            cp, ca = [], []
                            for g in current_training[cs:]:
                                p = cm.predict_over_prob(
                                    g["home_team"], g["away_team"], DEFAULT_TOTAL_LINE
                                )
                                if p is not None:
                                    cp.append(p)
                                    ca.append(1 if g["total_goals"] > DEFAULT_TOTAL_LINE else 0)
                            calibrator.fit(cp, ca)

            last_retrain_date = date_str

            # Retrain residual XGBoost alongside DC
            if residual_xgb is not None and model.fitted:
                residual_xgb.fit(current_training, model, elo, date_str)
                if residual_xgb.fitted:
                    pass  # Silently fitted

        # Predict each game
        daily_pnl = 0.0

        for game in date_games:
            home = game["home_team"]
            away = game["away_team"]
            actual_total = game["total_goals"]
            game_id = game["game_id"]

            if not model.fitted:
                continue

            # Dixon-Coles prediction
            dc_total = model.predict_expected_total(home, away)
            if dc_total is None:
                continue

            # Enhanced feature adjustment to DC total
            adjusted_total = dc_total
            if use_enhanced:
                try:
                    feats = compute_backtest_features(
                        home, away, date_str, current_training, elo
                    )

                    if residual_xgb is not None and residual_xgb.fitted:
                        # XGBoost learned correction: replaces hand-tuned adjustments
                        residual = residual_xgb.predict_residual(feats)
                        adjusted_total += residual
                    else:
                        # Hand-tuned adjustments (fallback before XGB has enough data)
                        # 1. Rest advantage
                        h_rest = feats.get("home_rest_days", 1)
                        a_rest = feats.get("away_rest_days", 1)
                        if h_rest == 0:
                            adjusted_total -= 0.15
                        if a_rest == 0:
                            adjusted_total -= 0.15
                        if h_rest >= 3:
                            adjusted_total += 0.1
                        if a_rest >= 3:
                            adjusted_total += 0.1

                        # 2. Elo-based adjustment
                        elo_diff = feats.get("elo_diff", 0)
                        if abs(elo_diff) > 100:
                            adjusted_total += 0.1
                except Exception:
                    pass  # Fall back to raw DC total

            # Market line: variable or fixed
            if variable_line:
                # Use adjusted total rounded to nearest 0.5 as market line proxy
                market_line = round(adjusted_total * 2) / 2.0
                # Clamp to realistic NHL range
                market_line = max(5.0, min(market_line, 7.5))
            else:
                market_line = DEFAULT_TOTAL_LINE

            # Predict over probability using adjusted total
            dc_over_prob = model.predict_over_prob(home, away, market_line)
            if dc_over_prob is None:
                continue

            # If enhanced, blend DC prob with feature-based adjustment
            if use_enhanced and adjusted_total != dc_total:
                # Shift the probability based on how our adjusted total
                # differs from DC total relative to the line
                shift = (adjusted_total - dc_total) * 0.08  # ~8% prob per goal
                ensemble_over_prob = max(0.01, min(0.99, dc_over_prob + shift))
            elif use_calibration and calibrator.fitted:
                ensemble_over_prob = calibrator.calibrate(dc_over_prob)
            else:
                ensemble_over_prob = dc_over_prob

            # Determine edge
            be_prob = breakeven_prob(STANDARD_JUICE)  # ~0.5238

            over_edge = ensemble_over_prob - be_prob
            under_edge = (1.0 - ensemble_over_prob) - be_prob

            pred = {
                "run_id": run_id,
                "game_id": game_id,
                "game_date": date_str,
                "season": season_label,
                "home_team": home,
                "away_team": away,
                "actual_total": actual_total,
                "market_line": market_line,
                "dc_predicted_total": round(dc_total, 3),
                "dc_over_prob": round(dc_over_prob, 4),
                "ensemble_over_prob": round(ensemble_over_prob, 4),
                "model_edge": None,
                "bet_side": None,
                "bet_size": 0.0,
                "bet_won": None,
                "pnl": 0.0,
            }

            # Bet if edge exceeds threshold
            if over_edge >= MIN_EDGE_THRESHOLD:
                decimal_odds = implied_to_decimal(be_prob)
                bet_frac = kelly_bet_size(over_edge, decimal_odds)
                bet_amount = bankroll * bet_frac

                if bet_amount > 0:
                    won = actual_total > market_line
                    is_push = (actual_total == market_line and
                               market_line == int(market_line))

                    if is_push:
                        pnl = 0.0
                        pushes += 1
                    elif won:
                        pnl = bet_amount * (decimal_odds - 1.0)
                        wins += 1
                    else:
                        pnl = -bet_amount
                        losses += 1

                    pred["model_edge"] = round(over_edge, 4)
                    pred["bet_side"] = "over"
                    pred["bet_size"] = round(bet_amount, 2)
                    pred["bet_won"] = 1 if won else (None if is_push else 0)
                    pred["pnl"] = round(pnl, 2)

                    bankroll += pnl
                    daily_pnl += pnl
                    total_bets += 1

            elif under_edge >= MIN_EDGE_THRESHOLD:
                decimal_odds = implied_to_decimal(be_prob)
                bet_frac = kelly_bet_size(under_edge, decimal_odds)
                bet_amount = bankroll * bet_frac

                if bet_amount > 0:
                    won = actual_total < market_line
                    is_push = (actual_total == market_line and
                               market_line == int(market_line))

                    if is_push:
                        pnl = 0.0
                        pushes += 1
                    elif won:
                        pnl = bet_amount * (decimal_odds - 1.0)
                        wins += 1
                    else:
                        pnl = -bet_amount
                        losses += 1

                    pred["model_edge"] = round(under_edge, 4)
                    pred["bet_side"] = "under"
                    pred["bet_size"] = round(bet_amount, 2)
                    pred["bet_won"] = 1 if won else (None if is_push else 0)
                    pred["pnl"] = round(pnl, 2)

                    bankroll += pnl
                    daily_pnl += pnl
                    total_bets += 1

            predictions.append(pred)
            games_processed += 1

        # Update Elo with today's results (after prediction, no lookahead)
        for game in date_games:
            elo.update(game["home_team"], game["away_team"],
                       game["home_score"], game["away_score"],
                       season=game.get("season", season_label))

        # Track daily return
        if prev_bankroll > 0:
            daily_ret = (bankroll - prev_bankroll) / prev_bankroll
        else:
            daily_ret = 0.0
        daily_returns.append(daily_ret)
        prev_bankroll = bankroll

        # Drawdown tracking
        if bankroll > peak_bankroll:
            peak_bankroll = bankroll
        dd = peak_bankroll - bankroll
        if dd > max_drawdown:
            max_drawdown = dd

        # Progress output every 20 dates
        if (date_idx + 1) % 20 == 0:
            print(f"  Processed {date_idx+1}/{len(prediction_dates)} dates, "
                  f"{total_bets} bets, bankroll: ${bankroll:.2f}")

    # Calculate Sharpe ratio (annualized, ~180 betting days per season)
    if daily_returns and len(daily_returns) > 1:
        mean_ret = np.mean(daily_returns)
        std_ret = np.std(daily_returns, ddof=1)
        if std_ret > 0:
            sharpe = (mean_ret / std_ret) * math.sqrt(180)
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0

    total_wagered = sum(
        abs(p["bet_size"]) for p in predictions if p["bet_side"]
    )
    total_pnl = bankroll - INITIAL_BANKROLL
    roi = (total_pnl / total_wagered * 100) if total_wagered > 0 else 0.0
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

    results = {
        "run_id": run_id,
        "season": target_season,
        "season_label": f"{target_season}-{target_season+1}",
        "games_predicted": games_processed,
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": round(win_rate, 2),
        "total_wagered": round(total_wagered, 2),
        "total_pnl": round(total_pnl, 2),
        "roi": round(roi, 2),
        "final_bankroll": round(bankroll, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 3),
        "predictions": predictions,
        "daily_returns": daily_returns,
        "bankroll_history": [],
        "model_games_fit": model.n_games_fit,
        "retrain_count": retrain_count,
    }

    # Reconstruct bankroll history for equity curve
    bh = [INITIAL_BANKROLL]
    b = INITIAL_BANKROLL
    for p in predictions:
        b += p["pnl"]
        bh.append(round(b, 2))
    results["bankroll_history"] = bh

    print(f"\n  --- Season {target_season}-{target_season+1} Results ---")
    print(f"  Games predicted: {games_processed}")
    print(f"  Model retrains: {retrain_count}")
    print(f"  Bets placed: {total_bets}")
    print(f"  Win rate: {win_rate:.1f}%")
    print(f"  ROI: {roi:+.2f}%")
    print(f"  P&L: ${total_pnl:+.2f}")
    print(f"  Max drawdown: ${max_drawdown:.2f}")
    print(f"  Sharpe ratio: {sharpe:.3f}")
    print(f"  Final bankroll: ${bankroll:.2f}")

    return results


# ===========================================================================
# Multi-Season Backtest
# ===========================================================================

def multi_season_backtest(
    seasons: list = None,
    conn: Optional[sqlite3.Connection] = None,
    use_prior_seasons: bool = True,
    variable_line: bool = False,
    use_calibration: bool = False,
    use_enhanced: bool = False,
    use_xgboost: bool = False,
) -> dict:
    """
    Run walk-forward backtests across multiple seasons.

    Each season uses prior seasons for additional training data.
    """
    if seasons is None:
        seasons = [2022, 2023, 2024]

    own_conn = conn is None
    if own_conn:
        conn = get_backtest_db()
        init_backtest_schema(conn)

    run_id = f"multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("\n" + "=" * 60)
    print("MULTI-SEASON BACKTEST")
    print("=" * 60)
    print(f"Seasons: {[f'{s}-{s+1}' for s in seasons]}")
    print(f"Run ID: {run_id}")

    all_results = []
    all_predictions = []
    all_bankroll = [INITIAL_BANKROLL]

    cumulative_bankroll = INITIAL_BANKROLL
    cumulative_peak = INITIAL_BANKROLL
    cumulative_max_dd = 0.0

    for i, season in enumerate(seasons):
        # Prior seasons for training context
        prior = []
        if use_prior_seasons:
            prior = [s for s in seasons if s < season]
            # Also add the season before our first test season if available
            if season - 1 not in prior and (season - 1) in SEASONS:
                prior.insert(0, season - 1)

        result = walk_forward_backtest(
            conn=conn,
            target_season=season,
            prior_seasons=prior if prior else None,
            run_id=f"{run_id}_s{season}",
            variable_line=variable_line,
            use_calibration=use_calibration,
            use_enhanced=use_enhanced,
            use_xgboost=use_xgboost,
        )

        all_results.append(result)
        all_predictions.extend(result.get("predictions", []))

        # Track cumulative bankroll
        for p in result.get("predictions", []):
            cumulative_bankroll += p["pnl"]
            if cumulative_bankroll > cumulative_peak:
                cumulative_peak = cumulative_bankroll
            dd = cumulative_peak - cumulative_bankroll
            if dd > cumulative_max_dd:
                cumulative_max_dd = dd
            all_bankroll.append(round(cumulative_bankroll, 2))

    # Aggregate stats
    total_games = sum(r.get("games_predicted", 0) for r in all_results)
    total_bets = sum(r.get("total_bets", 0) for r in all_results)
    total_wins = sum(r.get("wins", 0) for r in all_results)
    total_losses = sum(r.get("losses", 0) for r in all_results)
    total_pushes = sum(r.get("pushes", 0) for r in all_results)
    total_wagered = sum(r.get("total_wagered", 0) for r in all_results)
    total_pnl = cumulative_bankroll - INITIAL_BANKROLL

    agg_win_rate = (
        total_wins / (total_wins + total_losses) * 100
        if (total_wins + total_losses) > 0 else 0.0
    )
    agg_roi = (total_pnl / total_wagered * 100) if total_wagered > 0 else 0.0

    # Aggregate daily returns for Sharpe
    all_daily = []
    for r in all_results:
        all_daily.extend(r.get("daily_returns", []))

    if all_daily and len(all_daily) > 1:
        std = np.std(all_daily, ddof=1)
        sharpe = (np.mean(all_daily) / std) * math.sqrt(180) if std > 0 else 0.0
    else:
        sharpe = 0.0

    # Edge bucket analysis
    edge_buckets = {
        "3-5%": {"bets": 0, "wins": 0, "pnl": 0.0, "wagered": 0.0},
        "5-8%": {"bets": 0, "wins": 0, "pnl": 0.0, "wagered": 0.0},
        "8%+":  {"bets": 0, "wins": 0, "pnl": 0.0, "wagered": 0.0},
    }

    for p in all_predictions:
        if p["bet_side"] is None or p["model_edge"] is None:
            continue
        edge = p["model_edge"]
        if edge < 0.05:
            bucket = "3-5%"
        elif edge < 0.08:
            bucket = "5-8%"
        else:
            bucket = "8%+"

        edge_buckets[bucket]["bets"] += 1
        edge_buckets[bucket]["wagered"] += abs(p["bet_size"])
        edge_buckets[bucket]["pnl"] += p["pnl"]
        if p["bet_won"] == 1:
            edge_buckets[bucket]["wins"] += 1

    # Calibration analysis
    calibration = compute_calibration(all_predictions)

    # Side analysis
    over_bets = [p for p in all_predictions if p["bet_side"] == "over"]
    under_bets = [p for p in all_predictions if p["bet_side"] == "under"]

    over_wins = sum(1 for p in over_bets if p["bet_won"] == 1)
    under_wins = sum(1 for p in under_bets if p["bet_won"] == 1)
    over_pnl = sum(p["pnl"] for p in over_bets)
    under_pnl = sum(p["pnl"] for p in under_bets)

    summary = {
        "run_id": run_id,
        "seasons": [f"{s}-{s+1}" for s in seasons],
        "total_games_predicted": total_games,
        "total_bets": total_bets,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_pushes": total_pushes,
        "win_rate": round(agg_win_rate, 2),
        "roi": round(agg_roi, 2),
        "total_wagered": round(total_wagered, 2),
        "total_pnl": round(total_pnl, 2),
        "final_bankroll": round(cumulative_bankroll, 2),
        "max_drawdown": round(cumulative_max_dd, 2),
        "sharpe_ratio": round(sharpe, 3),
        "edge_buckets": edge_buckets,
        "calibration": calibration,
        "by_season": [
            {
                "season": r["season_label"],
                "bets": r["total_bets"],
                "win_rate": r["win_rate"],
                "roi": r["roi"],
                "pnl": r["total_pnl"],
            }
            for r in all_results
        ],
        "by_side": {
            "over": {
                "bets": len(over_bets),
                "wins": over_wins,
                "win_rate": round(
                    over_wins / len(over_bets) * 100, 1
                ) if over_bets else 0,
                "pnl": round(over_pnl, 2),
            },
            "under": {
                "bets": len(under_bets),
                "wins": under_wins,
                "win_rate": round(
                    under_wins / len(under_bets) * 100, 1
                ) if under_bets else 0,
                "pnl": round(under_pnl, 2),
            },
        },
        "season_results": all_results,
        "predictions": all_predictions,
        "bankroll_history": all_bankroll,
        "config": {
            "variable_line": variable_line,
            "use_calibration": use_calibration,
            "use_enhanced": use_enhanced,
            "min_edge": MIN_EDGE_THRESHOLD,
            "kelly_fraction": KELLY_FRACTION,
            "default_line": DEFAULT_TOTAL_LINE,
        },
    }

    if own_conn:
        conn.close()

    return summary


# ===========================================================================
# Calibration Analysis
# ===========================================================================

def compute_calibration(predictions: list, n_bins: int = 10) -> list:
    """
    Compute model calibration: group predictions by confidence,
    compare predicted probability to actual hit rate.
    """
    calls = [p for p in predictions if p["dc_over_prob"] is not None]
    if not calls:
        return []

    calls.sort(key=lambda x: x["dc_over_prob"])

    bins = []
    bin_size = max(1, len(calls) // n_bins)

    for i in range(0, len(calls), bin_size):
        chunk = calls[i:i + bin_size]
        if not chunk:
            continue

        avg_predicted = np.mean([c["dc_over_prob"] for c in chunk])
        actual_overs = sum(
            1 for c in chunk
            if c["actual_total"] is not None and
            c["actual_total"] > c["market_line"]
        )
        actual_rate = actual_overs / len(chunk) if chunk else 0

        bins.append({
            "predicted_prob": round(float(avg_predicted), 3),
            "actual_rate": round(float(actual_rate), 3),
            "count": len(chunk),
            "deviation": round(float(actual_rate - avg_predicted), 3),
        })

    return bins


# ===========================================================================
# Report Generation
# ===========================================================================

def generate_report(summary: dict) -> str:
    """Generate comprehensive text report from backtest results."""
    lines = []
    lines.append("")
    lines.append("=" * 65)
    lines.append("  NHL TOTALS MODEL BACKTEST REPORT")
    lines.append("  Dixon-Coles Walk-Forward Analysis")
    lines.append("=" * 65)
    lines.append("")

    seasons_str = ", ".join(summary.get("seasons", []))
    lines.append(f"Seasons tested:        {seasons_str}")
    lines.append(f"Total games predicted:  {summary['total_games_predicted']}")
    lines.append(f"Total bets placed:      {summary['total_bets']}")
    lines.append(f"  (edge > {MIN_EDGE_THRESHOLD*100:.0f}%, quarter-Kelly, "
                 f"max {MAX_BET_FRACTION*100:.0f}% per bet)")
    config = summary.get("config", {})
    line_mode = "Variable (DC rounded)" if config.get("variable_line") else f"Fixed {DEFAULT_TOTAL_LINE}"
    lines.append(f"Market line mode:       {line_mode}")
    lines.append(f"Standard juice:         {STANDARD_JUICE}")
    lines.append(f"Initial bankroll:       ${INITIAL_BANKROLL:,.0f}")
    lines.append("")

    lines.append("-" * 65)
    lines.append("  OVERALL RESULTS")
    lines.append("-" * 65)
    lines.append(f"  Win rate:       {summary['win_rate']:.1f}% "
                 f"({summary['total_wins']}W / {summary['total_losses']}L / "
                 f"{summary['total_pushes']}P)")
    lines.append(f"  ROI:            {summary['roi']:+.2f}%")
    lines.append(f"  Total P&L:      ${summary['total_pnl']:+,.2f}")
    lines.append(f"  Total wagered:  ${summary['total_wagered']:,.2f}")
    lines.append(f"  Final bankroll: ${summary['final_bankroll']:,.2f}")
    lines.append(f"  Max drawdown:   ${summary['max_drawdown']:,.2f}")
    lines.append(f"  Sharpe ratio:   {summary['sharpe_ratio']:.3f}")
    lines.append("")

    # By season
    lines.append("-" * 65)
    lines.append("  BY SEASON")
    lines.append("-" * 65)
    lines.append(f"  {'Season':<14} {'Bets':>6} {'WR%':>8} {'ROI%':>8} {'P&L':>10}")
    lines.append(f"  {'-'*14} {'-'*6} {'-'*8} {'-'*8} {'-'*10}")

    for s in summary.get("by_season", []):
        lines.append(
            f"  {s['season']:<14} {s['bets']:>6} "
            f"{s['win_rate']:>7.1f}% {s['roi']:>+7.2f}% "
            f"${s['pnl']:>+9.2f}"
        )
    lines.append("")

    # By edge bucket
    lines.append("-" * 65)
    lines.append("  BY EDGE BUCKET")
    lines.append("-" * 65)
    lines.append(f"  {'Bucket':<10} {'Bets':>6} {'WR%':>8} {'ROI%':>8} {'P&L':>10}")
    lines.append(f"  {'-'*10} {'-'*6} {'-'*8} {'-'*8} {'-'*10}")

    for bucket_name, b in summary.get("edge_buckets", {}).items():
        bets = b["bets"]
        if bets == 0:
            continue
        wr = b["wins"] / bets * 100 if bets > 0 else 0
        roi = b["pnl"] / b["wagered"] * 100 if b["wagered"] > 0 else 0
        lines.append(
            f"  {bucket_name:<10} {bets:>6} "
            f"{wr:>7.1f}% {roi:>+7.2f}% "
            f"${b['pnl']:>+9.2f}"
        )
    lines.append("")

    # By side
    lines.append("-" * 65)
    lines.append("  BY SIDE")
    lines.append("-" * 65)
    for side_name, s in summary.get("by_side", {}).items():
        lines.append(
            f"  {side_name.upper():<10} "
            f"{s['bets']:>4} bets, "
            f"{s['win_rate']:.1f}% WR, "
            f"${s['pnl']:+,.2f} P&L"
        )
    lines.append("")

    # Calibration
    cal = summary.get("calibration", [])
    if cal:
        lines.append("-" * 65)
        lines.append("  CALIBRATION (Model predicted vs actual over rate)")
        lines.append("-" * 65)
        lines.append(f"  {'Predicted':>10} {'Actual':>10} {'N':>6} {'Deviation':>10}")
        lines.append(f"  {'-'*10} {'-'*10} {'-'*6} {'-'*10}")
        for c in cal:
            lines.append(
                f"  {c['predicted_prob']:>9.1%} "
                f"{c['actual_rate']:>9.1%} "
                f"{c['count']:>6} "
                f"{c['deviation']:>+9.1%}"
            )
    lines.append("")

    # Baseline comparisons
    baselines = summary.get("baselines", {})
    if baselines:
        lines.append("-" * 65)
        lines.append("  BASELINE COMPARISONS (flat $100 bets)")
        lines.append("-" * 65)
        lines.append(f"  {'Strategy':<20} {'Bets':>6} {'WR%':>8} {'ROI%':>8} {'P&L':>10}")
        lines.append(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*10}")
        for name, b in baselines.items():
            lines.append(
                f"  {name:<20} {b['bets']:>6} "
                f"{b['win_rate']:>7.1f}% {b['roi']:>+7.2f}% "
                f"${b['pnl']:>+9.2f}"
            )
    lines.append("")

    # Model statistics
    lines.append("-" * 65)
    lines.append("  MODEL STATISTICS")
    lines.append("-" * 65)
    preds = summary.get("predictions", [])
    if preds:
        matched = [
            (p["dc_predicted_total"], p["actual_total"])
            for p in preds
            if p["dc_predicted_total"] is not None and
            p["actual_total"] is not None
        ]
        if matched:
            pt = np.array([m[0] for m in matched])
            at = np.array([m[1] for m in matched])

            mae = float(np.mean(np.abs(pt - at)))
            rmse = float(np.sqrt(np.mean((pt - at)**2)))
            bias = float(np.mean(pt - at))
            correlation = float(np.corrcoef(pt, at)[0, 1]) if len(pt) > 2 else 0

            lines.append(f"  Predicted total mean:  {np.mean(pt):.2f}")
            lines.append(f"  Actual total mean:     {np.mean(at):.2f}")
            lines.append(f"  MAE:                   {mae:.3f}")
            lines.append(f"  RMSE:                  {rmse:.3f}")
            lines.append(f"  Bias:                  {bias:+.3f}")
            lines.append(f"  Correlation:           {correlation:.4f}")
    lines.append("")

    # Key insight
    lines.append("-" * 65)
    lines.append("  KEY NOTES")
    lines.append("-" * 65)
    if config.get("variable_line"):
        lines.append("  - Variable line mode: DC predicted total rounded to 0.5")
    else:
        lines.append("  - Backtest uses fixed 6.0 line (actual lines vary 5.5-7.0)")
    if config.get("use_calibration"):
        lines.append("  - Isotonic calibration applied to model probabilities")
    if config.get("use_enhanced"):
        lines.append("  - Enhanced features: Elo + rolling windows + rest days")
    lines.append("  - No market model in backtest (no historical odds data)")
    lines.append("  - Dixon-Coles core: team strength parameters find edge")
    lines.append("  - Quarter-Kelly sizing caps risk at 3% per bet")
    lines.append("  - Break-even at -110 requires 52.38% win rate")
    lines.append("")

    lines.append("=" * 65)
    lines.append("  END OF REPORT")
    lines.append("=" * 65)

    return "\n".join(lines)


# ===========================================================================
# Equity Curve Plot
# ===========================================================================

def plot_equity_curve(summary: dict,
                      output_path: Optional[str] = None) -> str:
    """Generate equity curve chart and save as PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        print("matplotlib not installed, skipping equity curve plot")
        return ""

    if output_path is None:
        output_path = os.path.join(
            BACKTEST_DIR,
            f"equity_curve_{summary.get('run_id', 'unknown')}.png"
        )

    bh = summary.get("bankroll_history", [])
    if len(bh) < 2:
        print("Not enough data points for equity curve")
        return ""

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
    fig.suptitle(
        "NHL Totals Model - Walk-Forward Backtest",
        fontsize=14, fontweight="bold"
    )

    # Top: Equity curve
    ax1 = axes[0]
    x = range(len(bh))
    ax1.plot(x, bh, color="#2196F3", linewidth=1.2, label="Model Bankroll")
    ax1.axhline(y=INITIAL_BANKROLL, color="gray", linestyle="--",
                alpha=0.5, label=f"Starting (${INITIAL_BANKROLL:,.0f})")
    ax1.fill_between(
        x,
        [min(INITIAL_BANKROLL, min(bh))] * len(bh),
        bh,
        alpha=0.1, color="#2196F3"
    )
    ax1.set_ylabel("Bankroll ($)")
    ax1.set_title(
        f"Seasons: {', '.join(summary.get('seasons', []))} | "
        f"ROI: {summary.get('roi', 0):+.2f}% | "
        f"Sharpe: {summary.get('sharpe_ratio', 0):.3f}"
    )
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda val, p: f"${val:,.0f}"
    ))

    # Bottom: Drawdown
    ax2 = axes[1]
    peak = pd.Series(bh).cummax()
    drawdown = (pd.Series(bh) - peak)
    ax2.fill_between(range(len(drawdown)), 0, drawdown,
                     color="#F44336", alpha=0.4)
    ax2.plot(range(len(drawdown)), drawdown, color="#F44336",
             linewidth=0.8)
    ax2.set_ylabel("Drawdown ($)")
    ax2.set_xlabel("Prediction #")
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda val, p: f"${val:,.0f}"
    ))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"\nEquity curve saved to: {output_path}")
    return output_path


# ===========================================================================
# Comparative Baselines
# ===========================================================================

def run_baselines(predictions: list) -> dict:
    """
    Run baseline strategies on the same games for comparison.

    Baselines:
      - always_over: bet over every game at -110
      - always_under: bet under every game at -110
      - random: random side each game at -110
    """
    preds_with_total = [
        p for p in predictions
        if p["actual_total"] is not None
    ]

    flat_bet = 100.0
    decimal_110 = 1.0 + 100.0 / 110.0  # ~1.909

    results = {}

    # Count non-push games
    non_push = [
        p for p in preds_with_total
        if not (p["actual_total"] == p["market_line"] and
                p["market_line"] == int(p["market_line"]))
    ]
    n_decided = len(non_push)

    # Always over
    over_pnl = 0.0
    over_wins = 0
    for p in non_push:
        won = p["actual_total"] > p["market_line"]
        if won:
            over_pnl += flat_bet * (decimal_110 - 1.0)
            over_wins += 1
        else:
            over_pnl -= flat_bet

    results["always_over"] = {
        "bets": n_decided,
        "wins": over_wins,
        "win_rate": round(over_wins / n_decided * 100, 1) if n_decided else 0,
        "pnl": round(over_pnl, 2),
        "roi": round(over_pnl / (n_decided * flat_bet) * 100, 2) if n_decided else 0,
    }

    # Always under
    under_pnl = 0.0
    under_wins = 0
    for p in non_push:
        won = p["actual_total"] < p["market_line"]
        if won:
            under_pnl += flat_bet * (decimal_110 - 1.0)
            under_wins += 1
        else:
            under_pnl -= flat_bet

    results["always_under"] = {
        "bets": n_decided,
        "wins": under_wins,
        "win_rate": round(under_wins / n_decided * 100, 1) if n_decided else 0,
        "pnl": round(under_pnl, 2),
        "roi": round(under_pnl / (n_decided * flat_bet) * 100, 2) if n_decided else 0,
    }

    # Random betting (seeded for reproducibility)
    np.random.seed(42)
    random_pnl = 0.0
    random_wins = 0
    for p in non_push:
        bet_over = np.random.random() > 0.5
        if bet_over:
            won = p["actual_total"] > p["market_line"]
        else:
            won = p["actual_total"] < p["market_line"]
        if won:
            random_pnl += flat_bet * (decimal_110 - 1.0)
            random_wins += 1
        else:
            random_pnl -= flat_bet

    results["random"] = {
        "bets": n_decided,
        "wins": random_wins,
        "win_rate": round(random_wins / n_decided * 100, 1) if n_decided else 0,
        "pnl": round(random_pnl, 2),
        "roi": round(random_pnl / (n_decided * flat_bet) * 100, 2) if n_decided else 0,
    }

    return results


# ===========================================================================
# Save / Load Results
# ===========================================================================

def save_results(summary: dict, filename: Optional[str] = None) -> str:
    """Save backtest results to JSON."""
    if filename is None:
        filename = f"backtest_{summary.get('run_id', 'unknown')}.json"

    path = os.path.join(BACKTEST_DIR, filename)

    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    clean = json.loads(json.dumps(summary, default=convert))

    with open(path, "w") as f:
        json.dump(clean, f, indent=2)

    print(f"\nResults saved to: {path}")
    return path


def load_results(path: str) -> dict:
    """Load backtest results from JSON."""
    with open(path) as f:
        return json.load(f)


# ===========================================================================
# Store predictions to DB
# ===========================================================================

def store_predictions_db(conn: sqlite3.Connection, predictions: list,
                         summary: dict) -> None:
    """Store predictions and run metadata in the backtest DB."""
    conn.execute("""
        INSERT OR REPLACE INTO backtest_runs
        (run_id, seasons, started_at, completed_at, total_games,
         total_bets, win_rate, roi, total_pnl, max_drawdown,
         sharpe_ratio, config)
        VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        summary["run_id"],
        json.dumps(summary.get("seasons", [])),
        summary.get("started_at", datetime.now().isoformat()),
        summary["total_games_predicted"],
        summary["total_bets"],
        summary["win_rate"],
        summary["roi"],
        summary["total_pnl"],
        summary["max_drawdown"],
        summary["sharpe_ratio"],
        json.dumps({
            "min_edge": MIN_EDGE_THRESHOLD,
            "kelly_fraction": KELLY_FRACTION,
            "juice": STANDARD_JUICE,
            "default_line": DEFAULT_TOTAL_LINE,
            "retrain_days": DC_RETRAIN_INTERVAL_DAYS,
            "half_life": DC_HALF_LIFE,
        }),
    ))

    for p in predictions:
        conn.execute("""
            INSERT INTO backtest_predictions
            (run_id, game_id, game_date, season, home_team, away_team,
             actual_total, market_line, dc_predicted_total, dc_over_prob,
             ensemble_over_prob, model_edge, bet_side, bet_size, bet_won, pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["run_id"], p.get("game_id"), p["game_date"], p["season"],
            p["home_team"], p["away_team"],
            p["actual_total"], p["market_line"],
            p["dc_predicted_total"], p["dc_over_prob"],
            p["ensemble_over_prob"], p["model_edge"],
            p["bet_side"], p["bet_size"], p["bet_won"], p["pnl"],
        ))

    conn.commit()
    print(f"Stored {len(predictions)} predictions in backtest DB")


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NHL Historical Backtesting Engine"
    )
    parser.add_argument(
        "--season", type=int, default=None,
        help="Backtest a single season (start year, e.g. 2023 for 2023-24)"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick test: one season (2023), reduced training"
    )
    parser.add_argument(
        "--download-only", action="store_true",
        help="Only download historical data, skip backtesting"
    )
    parser.add_argument(
        "--report-only", type=str, default=None,
        help="Generate report from saved results JSON file"
    )
    parser.add_argument(
        "--no-plot", action="store_true",
        help="Skip equity curve plot generation"
    )
    parser.add_argument(
        "--seasons", type=str, default=None,
        help="Comma-separated list of seasons (e.g. '2022,2023,2024')"
    )
    parser.add_argument(
        "--edge", type=float, default=None,
        help="Minimum edge threshold (default 0.03 = 3%%)"
    )
    parser.add_argument(
        "--line", type=float, default=None,
        help="Market total line to use (default 6.0)"
    )
    parser.add_argument(
        "--variable-line", action="store_true",
        help="Use variable market lines estimated from model predictions "
             "instead of fixed 6.0 (more realistic backtest)"
    )
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Apply isotonic calibration to model probabilities"
    )
    parser.add_argument(
        "--enhanced", action="store_true",
        help="Use enhanced features (Elo, rolling windows, rest days)"
    )
    parser.add_argument(
        "--xgboost", action="store_true",
        help="Use residual XGBoost to correct DC predictions (requires --enhanced)"
    )

    args = parser.parse_args()

    # Override globals if specified
    global MIN_EDGE_THRESHOLD, DEFAULT_TOTAL_LINE
    if args.edge is not None:
        MIN_EDGE_THRESHOLD = args.edge
    if args.line is not None:
        DEFAULT_TOTAL_LINE = args.line

    # Report only mode
    if args.report_only:
        print(f"Loading results from: {args.report_only}")
        summary = load_results(args.report_only)
        report = generate_report(summary)
        print(report)

        report_path = os.path.join(BACKTEST_DIR, "latest_report.txt")
        with open(report_path, "w") as f:
            f.write(report)
        print(f"Report saved to: {report_path}")

        if not args.no_plot:
            plot_equity_curve(summary)
        return

    # Determine seasons
    if args.seasons:
        seasons = [int(s.strip()) for s in args.seasons.split(",")]
    elif args.season:
        seasons = [args.season]
    elif args.quick:
        seasons = [2023]
    else:
        seasons = [2022, 2023, 2024]

    # Validate seasons
    for s in seasons:
        if s not in SEASONS:
            print(f"ERROR: Unknown season {s}. "
                  f"Available: {list(SEASONS.keys())}")
            sys.exit(1)

    # Download historical data
    conn = get_backtest_db()
    init_backtest_schema(conn)

    print("\n" + "=" * 60)
    print("  STEP 1: DOWNLOAD HISTORICAL DATA")
    print("=" * 60)

    # Download all required seasons (including one prior for training)
    download_seasons = set(seasons)
    for s in seasons:
        if s - 1 in SEASONS:
            download_seasons.add(s - 1)

    download_seasons = sorted(download_seasons)
    dl_results = download_historical_games(download_seasons, conn)

    for s, count in dl_results.items():
        print(f"  Season {s}-{s+1}: {count} games")

    if args.download_only:
        print("\nDownload complete. Exiting (--download-only).")
        conn.close()
        return

    # Run backtest
    print("\n" + "=" * 60)
    print("  STEP 2: WALK-FORWARD BACKTESTING")
    print("=" * 60)

    summary = multi_season_backtest(
        seasons=seasons,
        conn=conn,
        use_prior_seasons=True,
        variable_line=args.variable_line,
        use_calibration=args.calibrate,
        use_enhanced=args.enhanced,
        use_xgboost=args.xgboost,
    )

    # Run baselines
    print("\n" + "=" * 60)
    print("  STEP 3: BASELINE COMPARISONS")
    print("=" * 60)

    baselines = run_baselines(summary["predictions"])
    summary["baselines"] = baselines

    for name, b in baselines.items():
        print(f"  {name:<20} {b['bets']} bets, "
              f"{b['win_rate']:.1f}% WR, "
              f"ROI: {b['roi']:+.2f}%, "
              f"P&L: ${b['pnl']:+,.2f}")

    # Generate report
    print("\n" + "=" * 60)
    print("  STEP 4: GENERATE REPORT")
    print("=" * 60)

    report = generate_report(summary)
    print(report)

    # Save everything
    results_path = save_results(summary)
    report_path = os.path.join(BACKTEST_DIR, "latest_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved to: {report_path}")

    # Store in DB
    store_predictions_db(conn, summary["predictions"], summary)

    # Equity curve
    if not args.no_plot:
        plot_equity_curve(summary)

    conn.close()

    print("\n" + "=" * 60)
    print("  BACKTEST COMPLETE")
    print("=" * 60)
    print(f"  Results:  {results_path}")
    print(f"  Report:   {report_path}")
    print(f"  Database: {BACKTEST_DB}")
    print(f"  Total P&L: ${summary['total_pnl']:+,.2f}")
    print(f"  ROI: {summary['roi']:+.2f}%")
    print(f"  Win Rate: {summary['win_rate']:.1f}%")


if __name__ == "__main__":
    main()

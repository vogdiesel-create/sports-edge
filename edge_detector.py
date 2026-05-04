#!/usr/bin/env python3
"""
Sports Edge - Level 2 Predictive Model Engine
==============================================

The predictive model is the PRIMARY decision engine.
Level 1 (Pinnacle devig) is a CONFIRMATION signal only.

Pipeline:
  1. Run NHL predictive model → predictions for ALL games
  2. Run MLB predictive model → predictions for ALL games
  3. Model finds edges: model_prob vs market_implied_prob
  4. Run Level 1 scanner → used ONLY to confirm/boost model picks
  5. Tier assignment based on model edge + L1 confirmation
  6. Kelly sizing adjusted by confidence tier
  7. Deduplicate: 1 bet per game at best available odds
  8. Feed picks into paper trading ledger

Confidence Tiers (MODEL-DRIVEN):
  S - Model edge 5%+ AND Level 1 confirms same direction
  A - Model edge 5%+ standalone (strong model conviction)
  B - Model edge 3-5% AND Level 1 confirms same direction
  [No C tier - L1 alone does NOT generate picks]

Usage:
  python3 edge_detector.py              # Run full pipeline, print picks
  python3 edge_detector.py --json       # Output JSON only
  python3 edge_detector.py --dry-run    # Skip paper trading
"""

import json
import os
import sqlite3
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PICKS_DIR = os.path.join(DATA_DIR, "unified_picks")
LEDGER_PATH = os.path.join(DATA_DIR, "paper_ledger.json")
os.makedirs(PICKS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_BANKROLL = 5000
MAX_KELLY_PCT = 3.0            # max 3% of bankroll per bet
MAX_TOTAL_EXPOSURE_PCT = 15.0  # max 15% total exposure
MIN_EDGE_MODEL = 0.03          # 3% global minimum (fallback)
MIN_EDGE_STRONG = 0.10         # 10% for strong standalone picks
MAX_EDGE = 0.12                # 12% max edge - paper trading: 5-12% = 7W-2L +63% ROI, 12%+ = 1W-3L -$351

# Sport/market-specific minimum edges from backtest optimization
# Higher thresholds where backtest shows best ROI at higher edges
MIN_EDGE_BY_SPORT = {
    ("NHL", "totals"):    0.07,  # NHL UNDER 7%: +3.4% ROI (940 bets); 10%: +11.1% (581 bets)
    ("NHL", "moneyline"): 0.05,  # NHL ML AWAY 5%: +4.3% ROI (1332 bets)
    ("MLB", "totals"):    0.08,  # Raised from 5% -> 8%. Paper trading: 5% edges = negative CLV. Only 10%+ showed profit.
    ("MLB", "moneyline"): 0.08,  # Raised from 5% -> 8%. ML AWAY was 0-4 live. Tighter filter.
}
KELLY_BASE_FRACTION = 0.25     # quarter-Kelly

TIER_KELLY_MULT = {
    "S": 1.00,   # Model 15%+ AND L1 confirms
    "A": 0.75,   # Model 15%+ standalone
    "B": 0.50,   # Model 10-15% AND L1 confirms
}

# Sport-specific side restrictions from EXPANDED backtest (Apr 2026):
# NHL Feature Model: UNDER +11.1% ROI at 10% threshold, OVER unprofitable
# NHL Moneyline: AWAY +4.3% ROI at 5% threshold, HOME degrades above 3%
# MLB Poisson Model: UNDER +5.1% ROI at 5% threshold, OVER unprofitable
# MLB Moneyline: AWAY +4.1% ROI at 5% threshold
# Non-preferred sides are CUT ENTIRELY.
PREFERRED_SIDE = {
    "NHL": "UNDER",  # NHL UNDER 10%: 581 bets, 55.2% WR, +11.1% ROI (feature model)
    "MLB": "OVER",   # EXP-006: UNDERs disabled Apr 26. 10W-12L-1P -$170, CLV -0.49%. OVERs: 5W-0L +$642, CLV +0.44%.
}

# Moneyline side restrictions (separate from totals)
# Set to True to completely disable moneyline picks
MONEYLINE_DISABLED = True  # ML AWAY 0-6 live despite backtest edge. Re-enable at 50+ graded totals bets.
# v3 backtest (142 features, pitcher+park+weather): MLB AWAY 3% = +4.5% ROI (2051 bets)

PREFERRED_ML_SIDE = {
    # Re-enable after totals reach 50+ graded bets with positive CLV
    # "NHL": "AWAY",
    # "MLB": "AWAY",
}

# Line filters based on backtest analysis.
# NHL UNDER 5.5: -4.8% ROI at 7%+ edge (trap line, market prices it efficiently)
# NHL UNDER 6.0+: +2.1% to +41.9% ROI (real edges exist here)
SKIP_LINES = {
    ("NHL", "UNDER"): {5.5},  # Skip UNDER 5.5 - backtest unprofitable
}
LINE_FILTERS = {
    "NHL": {"UNDER": None},  # NHL OVER blocked: 0W-2L -$300 in paper trading
    "MLB": {"UNDER": None, "OVER": None},
}


# ---------------------------------------------------------------------------
# Odds / Probability Utilities
# ---------------------------------------------------------------------------

def american_to_implied(odds: float) -> float:
    """Convert American odds to implied probability (no-vig)."""
    if odds == 0:
        return 0.5
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal odds."""
    if odds == 0:
        return 2.0
    if odds < 0:
        return 1 + 100 / abs(odds)
    return 1 + odds / 100


def compute_kelly(edge: float, odds: float, tier: str) -> float:
    """
    Compute Kelly-sized wager as percentage of bankroll.

    Uses quarter-Kelly base, multiplied by tier factor, capped at MAX_KELLY_PCT.

    Parameters:
        edge: our probability - market implied probability (e.g. 0.05 = 5%)
        odds: American odds (e.g. -110, +150)
        tier: confidence tier (S, A, B)

    Returns:
        Wager as percentage of bankroll.
    """
    implied = american_to_implied(odds)
    our_prob = implied + edge
    our_prob = max(0.01, min(0.99, our_prob))

    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1  # net profit per unit wagered

    if b <= 0:
        return 0.0

    q = 1 - our_prob
    kelly_full = (b * our_prob - q) / b

    if kelly_full <= 0:
        return 0.0

    # Quarter-Kelly, scaled by tier
    tier_mult = TIER_KELLY_MULT.get(tier, 0.25)
    kelly_adj = kelly_full * KELLY_BASE_FRACTION * tier_mult

    # Cap at MAX_KELLY_PCT
    return min(round(kelly_adj * 100, 2), MAX_KELLY_PCT)


# ---------------------------------------------------------------------------
# Bankroll
# ---------------------------------------------------------------------------

def get_bankroll() -> float:
    """Read current bankroll from paper_ledger.json or return default."""
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH) as f:
                ledger = json.load(f)
            return ledger.get("bankroll", DEFAULT_BANKROLL)
        except (json.JSONDecodeError, KeyError):
            pass
    return DEFAULT_BANKROLL


# ---------------------------------------------------------------------------
# Model Runners
# ---------------------------------------------------------------------------

def run_nhl_model() -> List[dict]:
    """
    Run the NHL feature-rich XGBoost model on ALL today's games.
    Returns predictions for both totals AND moneyline with edge calculations.

    Feature model backtest results:
      - UNDER totals at 10%: 581 bets, 55.2% WR, +11.1% ROI
      - Moneyline at 2%: 3498 bets, 51.3% WR, +2.91% ROI
      - AWAY ML at 5%: 1332 bets, +4.3% ROI
    """
    try:
        from nhl_feature_model import NHLFeaturePredictor

        predictor = NHLFeaturePredictor()
        predictor.fit()

        if not predictor.fitted:
            print("  [NHL MODEL] Feature model failed to train")
            return []

        all_predictions = predictor.predict_today()

        picks = []
        for pred in all_predictions:
            edge = pred.get("edge", 0)
            market_type = pred.get("market_type", "totals")
            side = pred.get("side", "")

            # Sport/market-specific minimum edge threshold
            min_edge = MIN_EDGE_BY_SPORT.get(("NHL", market_type), MIN_EDGE_MODEL)
            if edge < min_edge:
                continue
            if edge > MAX_EDGE:
                continue

            # Apply side restrictions from backtest
            if market_type == "totals":
                preferred = PREFERRED_SIDE.get("NHL")
                if preferred and side != preferred:
                    continue
                # Skip trap lines
                market_line = pred.get("market_line")
                skip_set = SKIP_LINES.get(("NHL", side), set())
                if market_line in skip_set:
                    continue
            elif market_type == "moneyline":
                if MONEYLINE_DISABLED:
                    continue
                preferred_ml = PREFERRED_ML_SIDE.get("NHL")
                if preferred_ml and side != preferred_ml:
                    continue

            picks.append({
                "source": "nhl_feature",
                "sport": "NHL",
                "game": pred.get("game", ""),
                "home_team": pred.get("home_team", ""),
                "away_team": pred.get("away_team", ""),
                "side": side,
                "market_type": market_type,
                "market_line": pred.get("market_line"),
                "odds": pred.get("odds", -110),
                "our_prob": pred.get("our_prob", 0.5),
                "edge": pred.get("edge", 0),
                "model_confidence": pred.get("model_confidence", 0.5),
            })

        return picks

    except Exception as e:
        print(f"  [NHL MODEL] Error: {e}")
        traceback.print_exc()
        return []


def _get_mlb_market_totals() -> Dict[str, float]:
    """
    Extract MLB game total lines from the Level 1 scan data.
    Returns {normalized_game_key: total_line}.
    """
    scan_path = os.path.join(DATA_DIR, "game_line_scan.json")
    totals = {}
    if not os.path.exists(scan_path):
        return totals
    try:
        with open(scan_path) as f:
            data = json.load(f)
        for opp in data.get("opportunities", []):
            if opp.get("sport") != "MLB":
                continue
            market = opp.get("market", "").lower()
            if "total" not in market:
                continue
            game = opp.get("game", "").upper()
            line = opp.get("line")
            if game and line:
                totals[game] = float(line)
    except Exception:
        pass
    return totals


def _mlb_home_win_prob(home_lambda: float, away_lambda: float) -> float:
    """
    Compute P(home wins) from Poisson lambdas using negative binomial.
    MLB has no draws - extra innings modeled as 52/48 home advantage.
    """
    from scipy.stats import nbinom
    import math

    OVERDISPERSION = 1.15
    home_lambda = max(0.5, min(home_lambda, 15.0))
    away_lambda = max(0.5, min(away_lambda, 15.0))

    def nb_params(mu):
        r = mu / (OVERDISPERSION - 1)
        p = r / (r + mu)
        return r, p

    r_h, p_h = nb_params(home_lambda)
    r_a, p_a = nb_params(away_lambda)

    max_runs = 20
    p_home_win = 0.0
    p_draw = 0.0
    for hr in range(max_runs + 1):
        ph = nbinom.pmf(hr, r_h, p_h)
        for ar in range(max_runs + 1):
            pa = nbinom.pmf(ar, r_a, p_a)
            if hr > ar:
                p_home_win += ph * pa
            elif hr == ar:
                p_draw += ph * pa

    p_home_win += p_draw * 0.52
    return p_home_win


def run_mlb_feature_model() -> List[dict]:
    """
    Run the MLB feature-rich XGBoost model (market correction approach).
    Same architecture that took NHL from -8% to +11% ROI.
    """
    try:
        from mlb_feature_model import MLBFeaturePredictor

        predictor = MLBFeaturePredictor()
        predictor.fit()

        if not predictor.fitted:
            print("  [MLB FEATURE] Feature model failed to train")
            return []

        all_predictions = predictor.predict_today()

        picks = []
        for pred in all_predictions:
            edge = pred.get("edge", 0)
            market_type = pred.get("market_type", "totals")
            side = pred.get("side", "")

            # Sport/market-specific minimum edge threshold
            min_edge = MIN_EDGE_BY_SPORT.get(("MLB", market_type), MIN_EDGE_MODEL)
            if edge < min_edge:
                continue
            if edge > MAX_EDGE:
                continue

            # Apply side restrictions from backtest
            if market_type == "totals":
                preferred = PREFERRED_SIDE.get("MLB")
                if preferred and side != preferred:
                    continue
            elif market_type == "moneyline":
                if MONEYLINE_DISABLED:
                    continue
                preferred_ml = PREFERRED_ML_SIDE.get("MLB")
                if preferred_ml and side != preferred_ml:
                    continue

            picks.append({
                "source": "mlb_feature",
                "sport": "MLB",
                "game": pred.get("game", ""),
                "home_team": pred.get("home_team", ""),
                "away_team": pred.get("away_team", ""),
                "side": side,
                "market_type": market_type,
                "market_line": pred.get("market_line"),
                "odds": pred.get("odds", -110),
                "our_prob": pred.get("our_prob", 0.5),
                "edge": pred.get("edge", 0),
                "model_confidence": pred.get("model_confidence", 0.5),
            })

        return picks

    except Exception as e:
        print(f"  [MLB FEATURE] Error: {e}")
        traceback.print_exc()
        return []


def run_mlb_model() -> List[dict]:
    """
    Run the MLB ensemble model and return edge picks for totals AND moneyline.

    Backtest results:
      - UNDER totals at 5%: 1900 bets, 54.1% WR, +5.11% ROI
      - AWAY moneyline at 5%: 1638 bets, 47.0% WR, +4.1% ROI
    """
    try:
        from mlb_model import MLBEnsembleModel
        model = MLBEnsembleModel()

        predictions = model.predict_today()
        picks = []

        for pred in predictions:
            if "error" in pred:
                continue

            # --- TOTALS ---
            market_total = pred.get("market_total")
            if market_total is not None:
                over_probs = pred.get("over_prob", {})
                nearest_line = round(market_total * 2) / 2
                prob_key = str(nearest_line)
                p_over = over_probs.get(prob_key)

                if p_over is not None:
                    # Get actual Pinnacle totals odds for this game and devig
                    totals_odds = _get_mlb_totals_odds(pred.get("game", ""))
                    if totals_odds:
                        # Devig: convert both sides' American odds to implied,
                        # then normalize to remove vig
                        impl_over = american_to_implied(totals_odds["over"]["odds"])
                        impl_under = american_to_implied(totals_odds["under"]["odds"])
                        total_impl = impl_over + impl_under
                        devig_over = impl_over / total_impl
                        devig_under = impl_under / total_impl
                        over_edge = p_over - devig_over
                        under_edge = (1 - p_over) - devig_under
                        # Use actual book odds (not assumed -110)
                        over_odds = totals_odds["over"]["odds"]
                        under_odds = totals_odds["under"]["odds"]
                        # Use the line from the book (may differ from market_total)
                        book_line = totals_odds["over"]["line"]
                        if book_line != nearest_line:
                            # Re-check probability at the book's line
                            alt_key = str(book_line)
                            if alt_key in over_probs:
                                p_over = over_probs[alt_key]
                                over_edge = p_over - devig_over
                                under_edge = (1 - p_over) - devig_under
                                nearest_line = book_line
                    else:
                        # Fallback: no market odds found, use -110 breakeven
                        breakeven = 0.5238  # -110 breakeven
                        over_edge = p_over - breakeven
                        under_edge = (1 - p_over) - breakeven
                        over_odds = -110
                        under_odds = -110

                    mlb_totals_min = MIN_EDGE_BY_SPORT.get(("MLB", "totals"), MIN_EDGE_MODEL)
                    if over_edge > mlb_totals_min or under_edge > mlb_totals_min:
                        if over_edge >= under_edge and over_edge > mlb_totals_min:
                            side, prob_edge, our_prob = "OVER", over_edge, p_over
                            bet_odds = over_odds if totals_odds else -110
                        elif under_edge > mlb_totals_min:
                            side, prob_edge, our_prob = "UNDER", under_edge, 1 - p_over
                            bet_odds = under_odds if totals_odds else -110
                        else:
                            side, prob_edge, our_prob = None, 0, 0
                            bet_odds = -110

                        if side and prob_edge <= MAX_EDGE:
                            # Apply side restriction
                            preferred = PREFERRED_SIDE.get("MLB")
                            if not preferred or side == preferred:
                                picks.append({
                                    "source": "mlb_model",
                                    "sport": "MLB",
                                    "market_type": "totals",
                                    "game": pred.get("game", ""),
                                    "side": side,
                                    "market_line": nearest_line,
                                    "odds": bet_odds,
                                    "model_total": pred.get("model_total"),
                                    "our_prob": round(our_prob, 4),
                                    "edge": round(prob_edge, 4),
                                    "poisson_total": pred.get("poisson_total"),
                                    "xgboost_total": pred.get("xgboost_total"),
                                    "market_total_implied": pred.get("market_total_implied"),
                                    "weather_impact": pred.get("weather_impact", ""),
                                    "home_pitcher": pred.get("home_pitcher", ""),
                                    "away_pitcher": pred.get("away_pitcher", ""),
                                    "model_confidence": round(max(p_over, 1 - p_over), 4),
                                })

            # --- MONEYLINE ---
            if MONEYLINE_DISABLED:
                pass  # Skip ML entirely when disabled
            elif (home_lambda := pred.get("home_lambda")) and (away_lambda := pred.get("away_lambda")) and home_lambda > 0 and away_lambda > 0:
                p_home = _mlb_home_win_prob(home_lambda, away_lambda)
                p_away = 1 - p_home

                # Get moneyline odds from market data
                ml_odds = _get_mlb_moneyline_odds(pred.get("game", ""))
                if ml_odds:
                    ml_impl_home = american_to_implied(ml_odds["home"])
                    ml_impl_away = american_to_implied(ml_odds["away"])
                    # Devig
                    total_impl = ml_impl_home + ml_impl_away
                    devig_home = ml_impl_home / total_impl
                    devig_away = ml_impl_away / total_impl

                    edge_home = p_home - devig_home
                    edge_away = p_away - devig_away

                    mlb_ml_min = MIN_EDGE_BY_SPORT.get(("MLB", "moneyline"), MIN_EDGE_MODEL)
                    if edge_home > mlb_ml_min or edge_away > mlb_ml_min:
                        if edge_home >= edge_away and edge_home > mlb_ml_min:
                            ml_side = "HOME"
                            ml_edge = edge_home
                            ml_prob = p_home
                            ml_odds_val = ml_odds["home"]
                        elif edge_away > mlb_ml_min:
                            ml_side = "AWAY"
                            ml_edge = edge_away
                            ml_prob = p_away
                            ml_odds_val = ml_odds["away"]
                        else:
                            ml_side = None

                        # Apply ML side restriction
                        preferred_ml = PREFERRED_ML_SIDE.get("MLB")
                        if preferred_ml and ml_side and ml_side != preferred_ml:
                            ml_side = None

                        if ml_side and ml_edge <= MAX_EDGE:
                            picks.append({
                                "source": "mlb_model",
                                "sport": "MLB",
                                "market_type": "moneyline",
                                "game": pred.get("game", ""),
                                "side": ml_side,
                                "market_line": None,
                                "odds": ml_odds_val,
                                "our_prob": round(ml_prob, 4),
                                "edge": round(ml_edge, 4),
                                "home_pitcher": pred.get("home_pitcher", ""),
                                "away_pitcher": pred.get("away_pitcher", ""),
                                "model_confidence": round(max(p_home, p_away), 4),
                            })

        return picks

    except Exception as e:
        print(f"  [MLB MODEL] Error: {e}")
        traceback.print_exc()
        return []


def _get_mlb_totals_odds(game_str: str) -> Optional[Dict[str, dict]]:
    """
    Get MLB totals over/under odds from game_line_snapshots for a game.
    Returns {"over": {"odds": -110, "line": 8.5}, "under": {"odds": -107, "line": 8.5}}
    or None if not found.

    Prefers Pinnacle, falls back to consensus/heritage/betonline.
    """
    se_db = os.path.join(DATA_DIR, "sports_edge.db")
    if not os.path.exists(se_db):
        return None

    try:
        from mlb_feature_model import MLB_FULL_TO_ABBREV as MLB_FTA
    except ImportError:
        try:
            from backtest_mlb_pinnacle import MLB_FULL_TO_ABBREV as MLB_FTA
        except ImportError:
            MLB_FTA = {}

    try:
        conn = sqlite3.connect(se_db)
        conn.row_factory = sqlite3.Row
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Parse teams from "AWAY @ HOME"
        parts = game_str.split(" @ ")
        if len(parts) != 2:
            conn.close()
            return None

        away_abbr, home_abbr = parts[0].strip(), parts[1].strip()

        books = ["pinnacle", "consensus", "heritage", "betonline"]
        result = {}
        for book in books:
            rows = conn.execute("""
                SELECT home_team, away_team, side, line, odds
                FROM game_line_snapshots
                WHERE sport='MLB' AND game_date=? AND market='total'
                AND book=?
                ORDER BY collected_at DESC
            """, (today, book)).fetchall()

            for r in rows:
                h = r["home_team"]
                a = r["away_team"]
                # Convert stored full names to abbreviations for matching
                h_abbr = MLB_FTA.get(h, h)
                a_abbr = MLB_FTA.get(a, a)
                if h_abbr == h:
                    for full_name, abbr in MLB_FTA.items():
                        if full_name.startswith(h + " ") or full_name == h:
                            h_abbr = abbr
                            break
                if a_abbr == a:
                    for full_name, abbr in MLB_FTA.items():
                        if full_name.startswith(a + " ") or full_name == a:
                            a_abbr = abbr
                            break
                h_match = (h_abbr == home_abbr)
                a_match = (a_abbr == away_abbr)

                if h_match and a_match:
                    side = r["side"]
                    if side == "over" and "over" not in result:
                        result["over"] = {"odds": r["odds"], "line": r["line"]}
                    elif side == "under" and "under" not in result:
                        result["under"] = {"odds": r["odds"], "line": r["line"]}

            if "over" in result and "under" in result:
                break

        conn.close()
        return result if "over" in result and "under" in result else None

    except Exception:
        return None


def _get_mlb_moneyline_odds(game_str: str) -> Optional[Dict[str, int]]:
    """Get MLB moneyline odds from game_line_snapshots for a game."""
    se_db = os.path.join(DATA_DIR, "sports_edge.db")
    if not os.path.exists(se_db):
        return None

    try:
        from mlb_feature_model import MLB_FULL_TO_ABBREV as MLB_FTA
    except ImportError:
        try:
            from backtest_mlb_pinnacle import MLB_FULL_TO_ABBREV as MLB_FTA
        except ImportError:
            MLB_FTA = {}

    try:
        conn = sqlite3.connect(se_db)
        conn.row_factory = sqlite3.Row
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Parse teams from "AWAY @ HOME"
        parts = game_str.split(" @ ")
        if len(parts) != 2:
            conn.close()
            return None

        away_abbr, home_abbr = parts[0].strip(), parts[1].strip()

        books = ["pinnacle", "consensus", "heritage", "betonline"]
        result = {}
        for book in books:
            rows = conn.execute("""
                SELECT home_team, away_team, side, odds
                FROM game_line_snapshots
                WHERE sport='MLB' AND game_date=? AND market='moneyline'
                AND book=?
                ORDER BY collected_at DESC
            """, (today, book)).fetchall()

            for r in rows:
                h = r["home_team"]
                a = r["away_team"]
                # Convert stored names to abbreviations for matching
                h_abbr = MLB_FTA.get(h, h)
                a_abbr = MLB_FTA.get(a, a)
                # Also try city-only name lookup (e.g., "Baltimore" -> "BAL")
                if h_abbr == h:
                    for full_name, abbr in MLB_FTA.items():
                        if full_name.startswith(h + " "):
                            h_abbr = abbr
                            break
                if a_abbr == a:
                    for full_name, abbr in MLB_FTA.items():
                        if full_name.startswith(a + " "):
                            a_abbr = abbr
                            break
                h_match = (h_abbr == home_abbr)
                a_match = (a_abbr == away_abbr)

                if h_match and a_match:
                    side = r["side"]
                    if side == "home" and "home" not in result:
                        result["home"] = r["odds"]
                    elif side == "away" and "away" not in result:
                        result["away"] = r["odds"]

            if "home" in result and "away" in result:
                break

        conn.close()
        return result if "home" in result and "away" in result else None

    except Exception:
        return None


def run_level1() -> List[dict]:
    """
    Run the Level 1 price-comparison scanner (Pinnacle devig).
    Returns normalized pick dicts.
    """
    try:
        from smart_scanner import scan_game_lines
        result = scan_game_lines()
        raw_picks = result.get("picks", [])

        picks = []
        for opp in raw_picks:
            sport = opp.get("sport", "")
            if sport not in ("NHL", "MLB"):
                # Still include other sports at C tier
                pass

            edge = opp.get("edge", 0)
            if edge < MIN_EDGE_MODEL or edge > MAX_EDGE:
                continue

            picks.append({
                "source": "level1",
                "sport": sport,
                "game": opp.get("game", ""),
                "market": opp.get("market", ""),
                "side": opp.get("side", ""),
                "line": opp.get("line", ""),
                "book": opp.get("book", ""),
                "odds": opp.get("odds", -110),
                "edge": round(edge, 4),
                "ev": opp.get("ev", 0),
                "fair_prob": opp.get("fair_prob", 0),
                "pinnacle_odds": opp.get("pinnacle_odds", ""),
                "kelly_pct_raw": opp.get("kelly_pct", 0),
            })

        return picks

    except Exception as e:
        print(f"  [LEVEL 1] Error: {e}")
        traceback.print_exc()
        return []


# ---------------------------------------------------------------------------
# Cross-Reference & Tier Assignment
# ---------------------------------------------------------------------------

def _normalize_game_key(game: str) -> str:
    """Normalize a game string for fuzzy matching."""
    return game.strip().upper().replace("  ", " ")


def _match_picks(model_pick: dict, l1_pick: dict) -> bool:
    """
    Check if a model pick and a Level 1 pick refer to the same bet.
    Matching logic: same sport, overlapping game string, compatible side.
    """
    if model_pick.get("sport") != l1_pick.get("sport"):
        return False

    # Game matching (fuzzy: check if teams overlap)
    mg = _normalize_game_key(model_pick.get("game", ""))
    lg = _normalize_game_key(l1_pick.get("game", ""))

    if not mg or not lg:
        return False

    # Extract team abbreviations from "AWAY @ HOME" format
    mg_parts = [p.strip() for p in mg.split("@")]
    lg_parts = [p.strip() for p in lg.split("@")]

    game_match = False
    if len(mg_parts) == 2 and len(lg_parts) == 2:
        # Both teams must appear
        game_match = (mg_parts[0] in lg or mg_parts[1] in lg or
                      lg_parts[0] in mg or lg_parts[1] in mg)
    else:
        game_match = mg in lg or lg in mg

    if not game_match:
        return False

    # Side matching: model "OVER"/"UNDER" should align with Level 1
    model_side = model_pick.get("side", "").upper()
    l1_side = l1_pick.get("side", "").upper()
    l1_market = l1_pick.get("market", "").upper()

    if model_side and l1_side:
        # Direct side match
        if model_side in l1_side or l1_side in model_side:
            return True
    if model_side and l1_market:
        # Market contains "OVER" or "UNDER"
        if model_side in l1_market:
            return True

    # If game matches but sides are ambiguous, still count as same game
    return game_match


def cross_reference(model_picks: List[dict], level1_picks: List[dict]) -> List[dict]:
    """
    LEVEL 2: Model picks are PRIMARY. Level 1 only confirms/boosts.

    Tier assignment:
      S - Model edge 5%+ AND Level 1 confirms same direction
      A - Model edge 5%+ standalone
      B - Model edge 3-5% AND Level 1 confirms same direction

    NO C tier. L1 alone does NOT generate picks.
    3-5% model edge WITHOUT L1 confirmation = no bet (too noisy alone).
    """
    unified = []

    for mp in model_picks:
        edge = mp.get("edge", 0)

        # Find matching Level 1 pick (same game, same direction)
        l1_match = None
        for lp in level1_picks:
            if _match_picks(mp, lp):
                l1_match = lp
                break

        # Tier assignment - MODEL DRIVEN
        # Pinnacle backtest: 10%+ edge is profitable standalone (no L1 needed)
        if edge >= MIN_EDGE_STRONG and l1_match:
            tier = "S"   # Strong model edge + L1 confirms = highest confidence
        elif edge >= MIN_EDGE_STRONG:
            tier = "A"   # Strong model edge standalone
        elif edge >= MIN_EDGE_MODEL and l1_match:
            tier = "B"   # Moderate model edge + L1 confirms = boosted confidence
        elif edge >= MIN_EDGE_MODEL:
            tier = "B"   # Moderate model edge standalone (backtest-validated)
        else:
            continue

        pick = {
            **mp,
            "tier": tier,
            "level1_confirms": l1_match is not None,
            "level1_detail": l1_match,
        }
        unified.append(pick)

    # NOTE: Unmatched L1 picks are intentionally EXCLUDED.
    # Level 2 = model is primary. L1 without model support = no bet.

    # Sort: S first, then A, B; within tier by edge descending
    tier_order = {"S": 0, "A": 1, "B": 2}
    unified.sort(key=lambda x: (tier_order.get(x["tier"], 9), -x.get("edge", 0)))

    return unified


# ---------------------------------------------------------------------------
# Sizing & Exposure
# ---------------------------------------------------------------------------

def size_picks(picks: List[dict], bankroll: float) -> List[dict]:
    """
    Apply Kelly sizing to each pick, respecting per-bet and total exposure caps.
    """
    total_exposure = 0.0

    for pick in picks:
        edge = pick.get("edge", 0)
        odds = pick.get("odds", -110)
        tier = pick.get("tier", "B")

        kelly_pct = compute_kelly(edge, odds, tier)

        # Enforce sport-specific side restrictions
        sport = pick.get("sport", "")
        side = pick.get("side", "")
        mkt_type = pick.get("market_type", "totals")
        if mkt_type == "totals":
            preferred = PREFERRED_SIDE.get(sport)
            if preferred and side and side != preferred:
                continue  # Skip non-preferred totals side
        elif mkt_type == "moneyline":
            if MONEYLINE_DISABLED:
                continue  # ML completely disabled
            preferred_ml = PREFERRED_ML_SIDE.get(sport)
            if preferred_ml and side and side != preferred_ml:
                continue  # Skip non-preferred moneyline side
        pick["side_penalty"] = False

        wager = round(bankroll * kelly_pct / 100, 2)

        # Check total exposure cap
        if total_exposure + wager > bankroll * MAX_TOTAL_EXPOSURE_PCT / 100:
            remaining = max(0, bankroll * MAX_TOTAL_EXPOSURE_PCT / 100 - total_exposure)
            wager = round(remaining, 2)
            kelly_pct = round(wager / bankroll * 100, 2) if bankroll > 0 else 0

        pick["kelly_pct"] = kelly_pct
        pick["wager"] = wager
        total_exposure += wager

    return picks


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def output_picks(picks: List[dict], bankroll: float) -> str:
    """Format picks for console output. Returns the formatted string."""
    now = datetime.now(timezone.utc)
    lines = []

    lines.append("")
    lines.append("=" * 60)
    lines.append("  LEVEL 2 - MODEL-DRIVEN PICKS")
    lines.append(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 60)

    if not picks:
        lines.append("")
        lines.append("  No actionable picks at this time.")
        lines.append("=" * 60)
        return "\n".join(lines)

    for pick in picks:
        tier = pick.get("tier", "?")
        sport = pick.get("sport", "")
        game = pick.get("game", "")
        side = pick.get("side", "")
        market_type = pick.get("market_type", "totals")
        market_line = pick.get("market_line", pick.get("line", ""))
        odds = pick.get("odds", -110)
        odds_str = f"{odds:+d}" if isinstance(odds, (int, float)) else str(odds)

        lines.append("")
        if market_type == "moneyline":
            lines.append(f"  [{tier}] {sport}: {game} - ML {side} @ {odds_str}")
        else:
            lines.append(f"  [{tier}] {sport}: {game} - {side} {market_line} @ {odds_str}")

        # Model details
        model_total = pick.get("model_total")
        our_prob = pick.get("our_prob")
        edge = pick.get("edge", 0)
        kelly = pick.get("kelly_pct", 0)
        wager = pick.get("wager", 0)

        if market_type == "moneyline":
            prob_str = f"{our_prob:.0%}" if our_prob else "N/A"
            lines.append(f"      Model: {prob_str} {side.lower()} win")
        elif model_total is not None:
            prob_str = f"{our_prob:.0%}" if our_prob else "N/A"
            lines.append(
                f"      Model: {model_total} total ({prob_str} {side.lower()}) "
                f"| Market: {market_line}"
            )

        lines.append(
            f"      Edge: +{edge:.1%} | Kelly: {kelly:.1f}% | Wager: ${wager:.0f}"
        )

        # Sport-specific sub-model details
        if sport == "NHL":
            dc = pick.get("dixon_coles_total")
            xgb = pick.get("xgboost_total")
            mkt_impl = pick.get("market_total_implied")
            parts = []
            if dc is not None:
                parts.append(f"Dixon-Coles: {dc}")
            if xgb is not None:
                parts.append(f"XGBoost: {xgb}")
            if mkt_impl is not None:
                parts.append(f"Pinnacle devig: {mkt_impl}")
            if parts:
                lines.append(f"      {' | '.join(parts)}")

        elif sport == "MLB":
            poi = pick.get("poisson_total")
            xgb = pick.get("xgboost_total")
            mkt = pick.get("market_total_implied")
            parts = []
            if poi is not None:
                parts.append(f"Poisson: {poi}")
            if xgb is not None:
                parts.append(f"XGBoost: {xgb}")
            if mkt is not None:
                parts.append(f"Market: {mkt}")
            if parts:
                lines.append(f"      {' | '.join(parts)}")

            wx = pick.get("weather_impact")
            if wx and "no weather" not in wx.lower() and "dome" not in wx.lower():
                lines.append(f"      Weather: {wx}")

        # Level 1 confirmation
        l1 = pick.get("level1_confirms", False)
        l1_detail = pick.get("level1_detail")
        if l1 and l1_detail:
            book = l1_detail.get("book", "")
            l1_edge = l1_detail.get("edge", 0)
            lines.append(
                f"      Level 1 confirms: YES ({book} +{l1_edge:.1%} edge)"
            )
        elif pick.get("source") != "level1":
            lines.append("      Level 1 confirms: NO")

    # Summary
    tier_counts = {"S": 0, "A": 0, "B": 0}
    total_wager = 0.0
    for p in picks:
        t = p.get("tier", "B")
        tier_counts[t] = tier_counts.get(t, 0) + 1
        total_wager += p.get("wager", 0)

    tier_str = ", ".join(f"{v}{k}" for k, v in tier_counts.items() if v > 0)
    exposure_pct = total_wager / bankroll * 100 if bankroll > 0 else 0

    lines.append("")
    lines.append(
        f"  SUMMARY: {len(picks)} picks ({tier_str}) | "
        f"Total exposure: ${total_wager:.0f} ({exposure_pct:.0f}% of bankroll)"
    )
    lines.append("=" * 60)

    output = "\n".join(lines)
    print(output)
    return output


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_picks(picks: List[dict], bankroll: float) -> str:
    """Save unified picks to JSON. Returns file path."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M")

    # Clean picks for JSON serialization
    clean_picks = []
    for p in picks:
        cp = {}
        for k, v in p.items():
            if isinstance(v, float) and (v != v):  # NaN check
                cp[k] = None
            else:
                cp[k] = v
        clean_picks.append(cp)

    payload = {
        "timestamp": now.isoformat(),
        "bankroll": bankroll,
        "total_picks": len(clean_picks),
        "tier_counts": {
            t: sum(1 for p in clean_picks if p.get("tier") == t)
            for t in ("S", "A", "B")
        },
        "total_exposure": sum(p.get("wager", 0) for p in clean_picks),
        "picks": clean_picks,
    }

    # Save timestamped version
    path = os.path.join(PICKS_DIR, f"picks_{ts}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    # Also save as "latest"
    latest_path = os.path.join(PICKS_DIR, "latest.json")
    with open(latest_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    return path


def deduplicate_picks(picks: List[dict]) -> List[dict]:
    """
    Deduplicate picks: 1 bet per game at best available odds.
    If multiple books have the same game+side, keep the one with best odds.
    """
    best_by_game = {}  # key: (sport, market_type, game_normalized, side) -> best pick

    for pick in picks:
        sport = pick.get("sport", "")
        mkt_type = pick.get("market_type", "totals")
        game = _normalize_game_key(pick.get("game", ""))
        side = pick.get("side", "").upper()
        key = (sport, mkt_type, game, side)

        if key not in best_by_game:
            best_by_game[key] = pick
        else:
            # Keep the one with better odds (higher = better for the bettor)
            existing_odds = best_by_game[key].get("odds", -110)
            new_odds = pick.get("odds", -110)
            if new_odds > existing_odds:
                best_by_game[key] = pick
            # If same odds, keep higher tier
            elif new_odds == existing_odds:
                tier_order = {"S": 0, "A": 1, "B": 2}
                if tier_order.get(pick.get("tier"), 9) < tier_order.get(best_by_game[key].get("tier"), 9):
                    best_by_game[key] = pick

    return list(best_by_game.values())


def feed_paper_trader(picks: List[dict]) -> None:
    """
    Feed unified picks into the paper trading ledger.
    Picks are already deduplicated (1 per game) by this point.
    """
    try:
        from paper_trader import load_ledger, save_ledger
    except ImportError:
        print("  [PAPER TRADER] paper_trader module not available, skipping.")
        return

    ledger = load_ledger()
    existing_ids = {b["pick_id"] for b in ledger.get("bets", [])}
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    new_count = 0

    for pick in picks:
        wager = pick.get("wager", 0)
        if wager <= 0:
            continue

        # Unique ID: 1 per game per side per market_type per day
        sport = pick.get("sport", "")
        game = pick.get("game", "")
        side = pick.get("side", "")
        market_type = pick.get("market_type", "totals")
        line = pick.get("market_line", pick.get("line", ""))
        pick_id = f"L2|{today}|{sport}|{market_type}|{game}|{side}|{line}"

        # Also check game-level dedup (ignore line) to prevent duplicate bets
        # when the line moves between scan runs
        game_key = f"L2|{today}|{sport}|{market_type}|{game}|{side}"
        game_level_exists = any(
            eid.startswith(game_key) for eid in existing_ids
        )
        if pick_id in existing_ids or game_level_exists:
            continue

        odds = pick.get("odds", -110)
        if isinstance(odds, (int, float)):
            if odds > 0:
                profit_if_win = wager * odds / 100
            else:
                profit_if_win = wager * 100 / abs(odds) if odds != 0 else wager
        else:
            profit_if_win = wager

        # Compute hours to game for CLV timing analysis
        game_time = pick.get("game_time")
        hours_to_game = None
        if game_time:
            try:
                from datetime import datetime as _dt
                gt = _dt.fromisoformat(game_time.replace("Z", "+00:00")) if isinstance(game_time, str) else game_time
                hours_to_game = round((gt - now).total_seconds() / 3600, 1)
            except Exception:
                pass

        bet = {
            "pick_id": pick_id,
            "logged_at": now.isoformat(),
            "bet_placement_utc": now.strftime("%H:%M"),
            "hours_to_game": hours_to_game,
            "sport": sport,
            "game": game,
            "market": f"moneyline {side.lower()}" if market_type == "moneyline" else f"total {side.lower()}",
            "side": side,
            "line": line,
            "book": pick.get("book", "model"),
            "odds": odds,
            "edge": pick.get("edge", 0),
            "ev": pick.get("ev", 0),
            "fair_prob": pick.get("our_prob", 0),
            "tier": pick.get("tier", "B"),
            "kelly_pct": pick.get("kelly_pct", 0),
            "wager": wager,
            "profit_if_win": round(profit_if_win, 2),
            "result": None,
            "actual_total": None,
            "closing_odds": None,
            "clv": None,
            "graded_at": None,
            "source": "level2_model",
        }

        ledger["bets"].append(bet)
        ledger["summary"]["total_bets"] += 1
        ledger["summary"]["total_wagered"] += wager
        existing_ids.add(pick_id)
        new_count += 1

    save_ledger(ledger)
    if new_count:
        print(f"  [PAPER TRADER] Logged {new_count} new picks (1 per game, deduped)")
    else:
        print(f"  [PAPER TRADER] No new picks to log (all duplicates)")


# ---------------------------------------------------------------------------
# Master Pipeline
# ---------------------------------------------------------------------------

def generate_picks() -> Tuple[List[dict], float]:
    """
    LEVEL 2 Pipeline: Model-driven edge detection.

    1. Predictive models evaluate ALL games
    2. Model finds edges vs market (3%+ threshold)
    3. Level 1 scanner confirms/boosts model picks
    4. Deduplicate to 1 bet per game
    5. Kelly sizing by tier

    Returns:
        (picks, bankroll) tuple
    """
    bankroll = get_bankroll()
    now = datetime.now(timezone.utc)

    print(f"\n{'='*60}")
    print(f"  LEVEL 2 ENGINE - Model-Driven Edge Detection")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Bankroll: ${bankroll:,.2f}")
    print(f"{'='*60}")

    # Step 1: Run Level 1 scanner FIRST (populates market data for models)
    print(f"\n  [1/5] Running Level 1 scanner (market data + confirmation signal)...")
    l1_picks = run_level1()
    print(f"    Level 1 found {len(l1_picks)} opportunities (used for tier boost only)")

    # Step 2: Run predictive models (PRIMARY - evaluates every game)
    print(f"\n  [2/5] Running NHL feature model (totals + moneyline)...")
    nhl_picks = run_nhl_model()
    nhl_totals = sum(1 for p in nhl_picks if p.get("market_type") == "totals")
    nhl_ml = sum(1 for p in nhl_picks if p.get("market_type") == "moneyline")
    print(f"    Found {len(nhl_picks)} NHL edges ({nhl_totals} totals, {nhl_ml} moneyline)")

    # MLB model: only runs if backtest validation exists
    mlb_backtest_path = os.path.join(DATA_DIR, "mlb_backtest_results.json")
    if os.path.exists(mlb_backtest_path):
        import json as _json
        with open(mlb_backtest_path) as _f:
            mlb_bt = _json.load(_f)
        mlb_bt_summary = mlb_bt.get("summary", {})
        mlb_bt_games = mlb_bt_summary.get("games_predicted", 0)
        mlb_bt_roi = mlb_bt_summary.get("roi_pct", -999)
        if mlb_bt_games >= 200 and mlb_bt_roi > 0:
            print(f"\n  [3/5] Running MLB predictive model (backtest: {mlb_bt_games} games, {mlb_bt_roi:+.1f}% ROI)...")
            mlb_picks = run_mlb_model()
            print(f"    Model found {len(mlb_picks)} MLB games with 3%+ edge")
        else:
            mlb_picks = []
            print(f"\n  [3/5] MLB model BLOCKED (backtest: {mlb_bt_games} games, {mlb_bt_roi:+.1f}% ROI - need 200+ games with positive ROI)")
    else:
        mlb_picks = []
        print(f"\n  [3/5] MLB model BLOCKED (no backtest found - run: python3 mlb_model.py backtest)")

    # Step 3b: Run MLB feature model (market correction approach)
    print(f"\n  [3b/5] Running MLB feature model (market correction)...")
    mlb_feature_picks = run_mlb_feature_model()
    mlb_feat_totals = sum(1 for p in mlb_feature_picks if p.get("market_type") == "totals")
    mlb_feat_ml = sum(1 for p in mlb_feature_picks if p.get("market_type") == "moneyline")
    print(f"    Found {len(mlb_feature_picks)} MLB feature edges ({mlb_feat_totals} totals, {mlb_feat_ml} moneyline)")

    # Combine: prefer feature model picks over ensemble for same game
    mlb_feature_games = {p.get("game") + "_" + p.get("market_type", "") for p in mlb_feature_picks}
    mlb_ensemble_unique = [p for p in mlb_picks
                           if (p.get("game") + "_" + p.get("market_type", "")) not in mlb_feature_games]
    if mlb_ensemble_unique:
        print(f"    + {len(mlb_ensemble_unique)} additional from ensemble model")

    # Step 3c: Run MLB pitcher K prop model
    prop_picks = []
    try:
        from mlb_prop_model import generate_today_picks as gen_k_picks
        k_picks = gen_k_picks()
        for kp in k_picks:
            if kp.get("side") and kp.get("edge", 0) > 0.05:  # 5%+ edge only
                prop_picks.append({
                    "sport": "MLB",
                    "game": f"{kp['team']} vs {kp['opponent']}",
                    "market_type": "prop",
                    "side": f"{kp['side']} {kp.get('fd_line', '')} Ks",
                    "player": kp["pitcher"],
                    "odds": kp.get("odds"),
                    "edge": kp["edge"],
                    "model_prob": kp.get("p_over" if kp["side"] == "OVER" else "p_under", 0),
                    "projected_k": kp["projected_k"],
                    "source": "k_prop_model",
                })
        if prop_picks:
            print(f"\n  [3c/5] MLB K prop model: {len(prop_picks)} picks (5%+ edge)")
    except Exception as e:
        print(f"\n  [3c/5] MLB K prop model error: {e}")

    # Step 3d: Run MLB batter prop model
    batter_prop_picks = []
    try:
        from mlb_batter_prop_model import generate_today_picks as gen_batter_picks
        batter_picks = gen_batter_picks()
        for bp in batter_picks:
            if bp.get("edge", 0) > 0.05:  # 5%+ edge (restored: NegBin fixed calibration)
                batter_prop_picks.append({
                    "sport": "MLB",
                    "game": bp.get("game", ""),
                    "market_type": "prop",
                    "side": f"{bp['player']} {bp['market']}",
                    "player": bp["player"],
                    "odds": bp.get("odds"),
                    "edge": bp["edge"],
                    "model_prob": bp.get("model_prob", 0),
                    "source": "batter_prop_model",
                })
        if batter_prop_picks:
            print(f"\n  [3d/5] MLB batter prop model: {len(batter_prop_picks)} picks (5%+ edge)")
    except Exception as e:
        print(f"\n  [3d/5] MLB batter prop model error: {e}")

    prop_picks.extend(batter_prop_picks)

    model_picks = nhl_picks + mlb_feature_picks + mlb_ensemble_unique

    # Step 4: Tier assignment (model primary, L1 confirms)
    print(f"\n  [4/5] Assigning tiers (model-driven)...")
    unified = cross_reference(model_picks, l1_picks)

    # Step 5: Deduplicate (1 bet per game at best odds)
    before_dedup = len(unified)
    unified = deduplicate_picks(unified)
    if before_dedup != len(unified):
        print(f"    Deduped: {before_dedup} -> {len(unified)} picks (1 per game)")
    else:
        print(f"    {len(unified)} picks (no duplicates)")

    # Step 6: Kelly sizing
    unified = size_picks(unified, bankroll)

    # Filter out zero-wager picks
    unified = [p for p in unified if p.get("wager", 0) > 0]

    return unified, bankroll, prop_picks


def run(dry_run: bool = False, json_output: bool = False) -> dict:
    """
    Run the complete edge detection pipeline.

    Args:
        dry_run: if True, skip paper trading
        json_output: if True, suppress console output

    Returns:
        Result dict with picks and metadata.
    """
    # Run data pipeline (goalie starts, pitcher stats, line snapshots)
    try:
        from data_pipeline import run_pipeline
        run_pipeline()
    except Exception as e:
        print(f"  [DATA] Pipeline warning: {e}")

    # Check kill criteria before generating picks
    try:
        latest_reports = sorted(
            [f for f in os.listdir(os.path.join(DATA_DIR, "daily_reports"))
             if f.startswith("report_")], reverse=True)
        if latest_reports:
            with open(os.path.join(DATA_DIR, "daily_reports", latest_reports[0])) as _f:
                latest_report = json.load(_f)
            if latest_report.get("kill_triggered"):
                reason = latest_report.get("kill_reason", "unknown")
                print(f"\n  *** KILL CRITERIA ACTIVE ***")
                print(f"  Reason: {reason}")
                print(f"  No new picks until model is reviewed and kill criteria cleared.")
                return {"timestamp": datetime.now(timezone.utc).isoformat(),
                        "picks": [], "kill_triggered": True, "kill_reason": reason}
    except Exception:
        pass  # Don't block picks if report check fails

    picks, bankroll, prop_picks = generate_picks()

    # Output
    if not json_output:
        output_picks(picks, bankroll)

    # Print prop picks if any
    if prop_picks and not json_output:
        k_props = [pp for pp in prop_picks if pp.get("source") == "k_prop_model"]
        batter_props = [pp for pp in prop_picks if pp.get("source") == "batter_prop_model"]
        if k_props:
            print(f"\n  --- PITCHER K PROP PICKS ({len(k_props)}) ---")
            for pp in k_props:
                print(f"  {pp['side']:>20} - {pp['player']} ({pp['game']})")
                print(f"        Projected: {pp.get('projected_k', 0):.1f}K | Edge: {pp['edge']*100:+.1f}% | Odds: {pp.get('odds', '-')}")
        if batter_props:
            print(f"\n  --- BATTER PROP PICKS ({len(batter_props)}) ---")
            for pp in batter_props:
                print(f"  {pp['side']}")
                print(f"        Game: {pp['game']} | Edge: {pp['edge']*100:+.1f}% | Model: {pp['model_prob']*100:.0f}% | Odds: {pp.get('odds', '-')}")

    # Save JSON
    path = save_picks(picks, bankroll)
    if not json_output:
        print(f"\n  Saved to {path}")

    # Paper trading
    if not dry_run:
        feed_paper_trader(picks)

    # Log prop picks for tracking
    if prop_picks and not dry_run:
        try:
            from prop_pick_tracker import load_log, save_log
            log = load_log()
            today = datetime.now().strftime("%Y-%m-%d")
            existing = {(p.get("player", ""), p.get("market", ""),
                         p.get("game_date", "")) for p in log["picks"]}
            new_count = 0
            for pp in prop_picks:
                key = (pp.get("player", ""), pp.get("side", ""), today)
                if key in existing:
                    continue
                existing.add(key)
                log["picks"].append({
                    "game_date": today, "source": pp.get("source", ""),
                    "sport": "MLB", "player": pp.get("player", ""),
                    "market": pp.get("side", ""), "game": pp.get("game", ""),
                    "odds": pp.get("odds"), "edge": pp.get("edge", 0),
                    "model_prob": pp.get("model_prob", 0),
                    "graded": False, "won": None, "actual": None,
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                })
                new_count += 1
            save_log(log)
            if new_count > 0:
                print(f"\n  [PROP TRACKER] Logged {new_count} new prop picks")
        except Exception as e:
            print(f"  [PROP TRACKER] Warning: {e}")

    # CLV tracking: check closing lines for all logged bets
    try:
        from clv_tracker import check_clv
        print(f"\n  [CLV] Checking closing line values...")
        check_clv()
    except Exception as e:
        print(f"  [CLV] Warning: {e}")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bankroll": bankroll,
        "picks": picks,
        "prop_picks": prop_picks,
        "total_picks": len(picks),
        "saved_to": path,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sports Edge - Unified Edge Detector")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--dry-run", action="store_true", help="Skip paper trading")
    args = parser.parse_args()

    result = run(dry_run=args.dry_run, json_output=args.json)

    if args.json:
        # Clean output for piping
        clean = {
            "timestamp": result["timestamp"],
            "bankroll": result["bankroll"],
            "total_picks": result["total_picks"],
            "picks": [
                {
                    "tier": p.get("tier"),
                    "sport": p.get("sport"),
                    "game": p.get("game"),
                    "side": p.get("side"),
                    "line": p.get("market_line", p.get("line")),
                    "odds": p.get("odds"),
                    "edge": p.get("edge"),
                    "kelly_pct": p.get("kelly_pct"),
                    "wager": p.get("wager"),
                    "level1_confirms": p.get("level1_confirms", False),
                }
                for p in result["picks"]
            ],
        }
        print(json.dumps(clean, indent=2))

#!/usr/bin/env python3
"""
MLB Batter Prop Model
=====================

Projects batter outcomes using:
- Batter rolling stats (AVG, HR/PA, TB/PA over L5, L10, L20, season)
- Opposing pitcher handedness and quality (ERA, WHIP, HR/9)
- Park factors (HR-friendly vs pitcher-friendly)
- Weather (temperature affects HR distance)

Supported markets:
- To Hit A Home Run (Poisson: P(HR >= 1))
- To Record A Hit (Binomial: P(H >= 1) given AVG and expected ABs)
- To Record 2+ Hits (Binomial: P(H >= 2))
- To Record 2+ Total Bases (P(TB >= 2))

Compares projections to FanDuel posted odds to find edges.

Usage:
    python3 mlb_batter_prop_model.py              # Generate today's picks
    python3 mlb_batter_prop_model.py backtest      # Backtest accuracy
"""

import math
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np
from scipy.stats import nbinom

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GL_DB = os.path.join(DATA_DIR, "game_lines.db")
SE_DB = os.path.join(DATA_DIR, "sports_edge.db")

# Park factors for HOME RUNS (Coors is extreme, SF suppresses)
PARK_HR_FACTOR = {
    "COL": 1.28, "CIN": 1.12, "NYY": 1.10, "PHI": 1.08, "CHC": 1.06,
    "BAL": 1.05, "BOS": 1.04, "TEX": 1.03, "ARI": 1.02, "ATL": 1.02,
    "CWS": 1.01, "TOR": 1.01, "MIN": 1.00, "MIL": 1.00, "HOU": 1.00,
    "LAD": 0.99, "WSH": 0.99, "KC": 0.98, "LAA": 0.98, "CLE": 0.97,
    "STL": 0.97, "DET": 0.96, "PIT": 0.96, "NYM": 0.95, "OAK": 0.95,
    "SD": 0.94, "SEA": 0.93, "TB": 0.93, "MIA": 0.92, "SF": 0.90,
}

# Park factors for HITS (less extreme variance than HR)
PARK_HIT_FACTOR = {
    "COL": 1.10, "BOS": 1.04, "CIN": 1.03, "PHI": 1.02, "TEX": 1.02,
    "ARI": 1.01, "ATL": 1.01, "CHC": 1.01, "NYY": 1.00, "BAL": 1.00,
    "CWS": 1.00, "HOU": 1.00, "TOR": 1.00, "MIN": 1.00, "MIL": 1.00,
    "CLE": 1.00, "DET": 1.00, "KC": 0.99, "LAD": 0.99, "WSH": 0.99,
    "STL": 0.99, "LAA": 0.99, "PIT": 0.99, "NYM": 0.98, "OAK": 0.98,
    "TB": 0.98, "SD": 0.97, "SEA": 0.97, "MIA": 0.97, "SF": 0.96,
}

IS_DOME = {"ARI", "HOU", "TEX", "TOR", "MIL", "SEA", "MIA", "TB"}

MLB_FULL_TO_ABBREV = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL", "Detroit Tigers": "DET",
    "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH",
    "Cleveland Indians": "CLE", "Athletics": "OAK",
}


def load_batter_logs():
    """Load all batter game logs from game_lines.db."""
    conn = sqlite3.connect(GL_DB, timeout=15)
    rows = conn.execute("""
        SELECT batter_id, batter_name, game_date, team,
               at_bats, plate_appearances, hits, doubles, triples,
               home_runs, rbi, runs, walks, strikeouts, stolen_bases,
               total_bases
        FROM mlb_batter_game_logs
        WHERE at_bats > 0
        ORDER BY batter_id, game_date
    """).fetchall()
    conn.close()

    logs = defaultdict(list)
    for r in rows:
        logs[r[0]].append({
            "name": r[1], "date": r[2], "team": r[3],
            "ab": r[4], "pa": r[5], "h": r[6], "doubles": r[7],
            "triples": r[8], "hr": r[9], "rbi": r[10], "runs": r[11],
            "bb": r[12], "k": r[13], "sb": r[14], "tb": r[15],
        })
    return logs


def load_pitcher_quality():
    """Load pitcher quality stats for opposing pitcher adjustments."""
    conn = sqlite3.connect(GL_DB, timeout=15)
    rows = conn.execute("""
        SELECT pitcher_id, pitcher_name, game_date,
               innings_pitched, hits_allowed, earned_runs,
               walks, home_runs_allowed
        FROM mlb_pitcher_game_logs
        WHERE game_started = 1 AND innings_pitched > 0
        ORDER BY pitcher_id, game_date
    """).fetchall()
    conn.close()

    logs = defaultdict(list)
    for r in rows:
        logs[r[0]].append({
            "name": r[1], "date": r[2], "ip": r[3],
            "h": r[4], "er": r[5], "bb": r[6], "hr": r[7],
        })
    return logs


def get_pitcher_adjustment(pitcher_logs, game_date, n_recent=5):
    """
    Compute how much easier/harder a pitcher is to hit vs league average.

    Returns multipliers for hits and HRs:
    - >1.0 means pitcher gives up more than average (boost batter projection)
    - <1.0 means pitcher is better than average (reduce batter projection)
    """
    prior = [l for l in pitcher_logs if l["date"] < game_date]
    if len(prior) < 3:
        return 1.0, 1.0  # Default: league average

    recent = prior[-n_recent:]
    total_ip = sum(l["ip"] for l in recent)
    if total_ip == 0:
        return 1.0, 1.0

    # Hits allowed per 9 IP (league avg ~8.5)
    h_per_9 = (sum(l["h"] for l in recent) / total_ip) * 9
    hit_adj = h_per_9 / 8.5

    # HR allowed per 9 IP (league avg ~1.2)
    hr_per_9 = (sum(l["hr"] for l in recent) / total_ip) * 9
    hr_adj = hr_per_9 / 1.2

    # Cap adjustments to avoid extreme values
    hit_adj = max(0.75, min(1.35, hit_adj))
    hr_adj = max(0.60, min(1.60, hr_adj))

    return hit_adj, hr_adj


def compute_batter_projection(batter_logs, game_date, park_team,
                              opp_pitcher_adj=None, n_recent=10):
    """
    Project batter stats for a game.

    Returns rates per plate appearance for HR, H, TB, plus expected ABs.
    opp_pitcher_adj: tuple (hit_adj, hr_adj) from get_pitcher_adjustment()
    """
    prior = [l for l in batter_logs if l["date"] < game_date]
    if len(prior) < 5:
        return None

    # Recent stats (last 10 games)
    recent = prior[-n_recent:]
    r_ab = sum(l["ab"] for l in recent)
    r_pa = sum(l["pa"] for l in recent)
    r_h = sum(l["h"] for l in recent)
    r_hr = sum(l["hr"] for l in recent)
    r_tb = sum(l["tb"] for l in recent)

    if r_ab == 0:
        return None

    # Season stats
    s_ab = sum(l["ab"] for l in prior)
    s_pa = sum(l["pa"] for l in prior)
    s_h = sum(l["h"] for l in prior)
    s_hr = sum(l["hr"] for l in prior)
    s_tb = sum(l["tb"] for l in prior)

    if s_ab == 0:
        return None

    # Per-PA rates (recent) with outlier resistance
    r_avg = r_h / r_ab
    r_hr_rate = r_hr / r_pa if r_pa > 0 else 0
    r_tb_rate = r_tb / r_pa if r_pa > 0 else 0

    # Winsorize recent TB rate: cap per-game TB at 90th percentile (4 TB)
    # This prevents one 9-TB explosion from dominating the projection
    capped_tb = sum(min(l["tb"], 4) for l in recent)
    r_tb_rate_capped = capped_tb / r_pa if r_pa > 0 else 0

    # Per-PA rates (season)
    s_avg = s_h / s_ab
    s_hr_rate = s_hr / s_pa if s_pa > 0 else 0
    s_tb_rate = s_tb / s_pa if s_pa > 0 else 0

    # Blend: 55% recent, 45% season (batters are streaky, recent form matters)
    avg = 0.55 * r_avg + 0.45 * s_avg
    hr_rate = 0.55 * r_hr_rate + 0.45 * s_hr_rate
    tb_rate = 0.55 * r_tb_rate_capped + 0.45 * s_tb_rate

    # Expected plate appearances (use recent average)
    avg_pa = r_pa / len(recent)

    # Park adjustments
    hr_park = PARK_HR_FACTOR.get(park_team, 1.0)
    hit_park = PARK_HIT_FACTOR.get(park_team, 1.0)

    # Opposing pitcher adjustments
    hit_pitcher_adj = 1.0
    hr_pitcher_adj = 1.0
    if opp_pitcher_adj:
        hit_pitcher_adj, hr_pitcher_adj = opp_pitcher_adj

    # Projected per-game stats
    proj_hr = hr_rate * avg_pa * hr_park * hr_pitcher_adj
    proj_tb = tb_rate * avg_pa * ((hr_park + hit_park) / 2) * ((hit_pitcher_adj + hr_pitcher_adj) / 2)

    # Calibration: cap extreme projections (regression to mean)
    # Backtest shows model over-projects at extremes by ~30%
    # Cap HR projection at 95th percentile (0.20 HR/game = ~32 HR season pace)
    proj_hr = min(proj_hr, 0.20)
    # Cap TB projection at 95th percentile
    proj_tb = min(proj_tb, 2.5)

    # More accurate: expected ABs (PA minus walks ratio)
    bb_rate = sum(l["bb"] for l in recent) / r_pa if r_pa > 0 else 0.08
    expected_ab = avg_pa * (1 - bb_rate)
    proj_h = avg * expected_ab * hit_park * hit_pitcher_adj

    # RBI and runs projections (with outlier capping)
    r_rbi = sum(min(l["rbi"], 3) for l in recent)  # Cap per-game RBI at 3
    r_runs = sum(min(l["runs"], 3) for l in recent)  # Cap per-game runs at 3
    s_rbi = sum(l["rbi"] for l in prior)
    s_runs = sum(l["runs"] for l in prior)

    r_rbi_rate = r_rbi / r_pa if r_pa > 0 else 0
    s_rbi_rate = s_rbi / s_pa if s_pa > 0 else 0
    rbi_rate = 0.55 * r_rbi_rate + 0.45 * s_rbi_rate

    r_runs_rate = r_runs / r_pa if r_pa > 0 else 0
    s_runs_rate = s_runs / s_pa if s_pa > 0 else 0
    runs_rate = 0.55 * r_runs_rate + 0.45 * s_runs_rate

    proj_rbi = rbi_rate * avg_pa * hr_pitcher_adj  # RBI correlates with pitcher HR-giving tendency
    proj_runs = runs_rate * avg_pa

    # Stolen base projection
    r_sb = sum(l["sb"] for l in recent)
    s_sb = sum(l["sb"] for l in prior)
    r_sb_rate = r_sb / len(recent) if recent else 0
    s_sb_rate = s_sb / len(prior) if prior else 0
    sb_rate = 0.60 * r_sb_rate + 0.40 * s_sb_rate  # Heavier recency for SB (streaky skill)
    proj_sb = sb_rate  # Per-game rate, no park/pitcher adjustment

    return {
        "proj_hr_per_game": proj_hr,
        "proj_h_per_game": proj_h,
        "proj_tb_per_game": proj_tb,
        "proj_rbi_per_game": proj_rbi,
        "proj_runs_per_game": proj_runs,
        "proj_sb_per_game": proj_sb,
        "avg_recent": r_avg,
        "avg_season": s_avg,
        "avg_blended": avg,
        "hr_rate_recent": r_hr_rate,
        "hr_rate_season": s_hr_rate,
        "expected_ab": expected_ab,
        "expected_pa": avg_pa,
        "park_hr": hr_park,
        "park_hit": hit_park,
        "n_games": len(prior),
    }


# Empirical overdispersion ratios (variance/mean from 221K batter game logs)
BATTER_OVERDISPERSION = {
    "tb": 2.122,    # Total bases: heavily overdispersed
    "rbi": 1.558,   # RBI: moderately overdispersed
    "hr": 1.007,    # Home runs: negligible (Poisson-equivalent)
    "runs": 0.978,  # Runs: slightly underdispersed (use Poisson)
    "sb": 1.2,      # Stolen bases: estimated (small counts)
    "hit": 1.0,     # Hits: underdispersed (0.863), use binomial instead
}

# Zero-inflation rates: backtest shows NegBin alone handles dispersion well.
# ZI=0 gives best calibration for TB (pred 0.320 vs actual 0.346 = -2.6% err).
# Any ZI > 0 overcorrects (tested 0.03-0.10, all worse).
BATTER_ZERO_INFLATION = {
    "tb": 0.0,
    "rbi": 0.0,
    "hr": 0.0,
    "runs": 0.0,
    "sb": 0.0,
    "hit": 0.0,
}


def _nb_params_batter(mu, market_type):
    """Convert mean + market-specific overdispersion to scipy nbinom params."""
    od = BATTER_OVERDISPERSION.get(market_type, 1.0)
    if od <= 1.0 or mu <= 0:
        # Poisson-equivalent
        return 1e6, 1e6 / (1e6 + mu)
    r = mu / (od - 1)
    p = r / (r + mu)
    return r, p


def negbin_at_least(lam, n, market_type="tb"):
    """
    P(X >= n) using Negative Binomial with market-specific overdispersion.
    For zero-inflated markets (TB), mixes in extra zero probability.
    """
    if lam <= 0:
        return 0.0
    r, p = _nb_params_batter(lam, market_type)
    zi = BATTER_ZERO_INFLATION.get(market_type, 0.0)
    if zi > 0 and n > 0:
        # Zero-inflated NegBin: P(X >= n) = (1 - zi) * P(NB >= n)
        return (1 - zi) * (1 - nbinom.cdf(n - 1, r, p))
    return 1 - nbinom.cdf(n - 1, r, p)


def poisson_at_least(lam, n):
    """Legacy Poisson function -- kept for backtest comparison only."""
    prob_less = 0
    for k in range(n):
        prob_less += (lam ** k * math.exp(-lam)) / math.factorial(k)
    return 1 - prob_less


def binomial_at_least(n_trials, p_success, n_min):
    """P(X >= n_min) where X ~ Binomial(n_trials, p_success)."""
    # Use complement: 1 - P(X < n_min)
    n_trials = int(round(n_trials))
    if n_trials <= 0:
        return 0
    prob_less = 0
    for k in range(min(n_min, n_trials + 1)):
        coeff = math.comb(n_trials, k)
        prob_less += coeff * (p_success ** k) * ((1 - p_success) ** (n_trials - k))
    return 1 - prob_less


def calibrate_prob(raw_prob, market_type, threshold):
    """
    Apply calibration corrections.

    NegBin replaced Poisson (Apr 20), fixing the primary overestimation cause.
    Backtest calibration (200 batters, 2024+):
    - TB: NegBin pred 0.320 vs actual 0.346 (-2.6% err) -- near-perfect, no multiplier needed
    - RBI: NegBin pred 0.296 vs actual 0.289 (+3% err) -- near-perfect
    - HR/SB/Runs: still disabled (structural model issues, not distributional)
    - Hits: uses binomial (not affected by NegBin change)

    Previous Poisson-era multipliers REMOVED -- NegBin handles the overdispersion directly.
    """
    # DISABLED markets: structural model issues beyond distribution choice
    if market_type in ("hr", "sb", "runs"):
        return 0.001  # Effectively disabled

    if market_type == "hit":
        # Hits use binomial (unaffected by NegBin change). Keep slight correction.
        # Live ratio was 0.67, but that was 1 day of data. Apply conservative 0.85x.
        raw_prob *= 0.85

    # TB and RBI: NegBin now handles calibration directly. No multiplier.

    return max(0.001, min(0.999, raw_prob))


def american_to_prob(odds):
    """Convert American odds to implied probability."""
    if odds is None:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def prob_to_american(prob):
    """Convert probability to American odds."""
    if prob <= 0:
        return 999
    if prob >= 1:
        return -9999
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)


def generate_today_picks():
    """Generate batter prop picks for today's games."""
    print("Loading batter data...")
    batter_logs = load_batter_logs()
    if not batter_logs:
        print("No batter game logs found. Run fetch_batter_history.py first.")
        return []

    print("Loading pitcher quality data...")
    pitcher_logs = load_pitcher_quality()

    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's FanDuel batter props
    conn = sqlite3.connect(SE_DB)

    # Markets we can model
    markets_to_model = {
        "To Hit A Home Run": {"type": "hr", "threshold": 1},
        "To Record A Hit": {"type": "hit", "threshold": 1},
        "To Record 2+ Hits": {"type": "hit", "threshold": 2},
        "To Record 2+ Total Bases": {"type": "tb", "threshold": 2},
        "To Record 3+ Total Bases": {"type": "tb", "threshold": 3},
        "To Record 4+ Total Bases": {"type": "tb", "threshold": 4},
        "To Record An RBI": {"type": "rbi", "threshold": 1},
        "To Record 2+ RBIs": {"type": "rbi", "threshold": 2},
        "To Record A Run": {"type": "runs", "threshold": 1},
        "To Record 2+ Runs": {"type": "runs", "threshold": 2},
        "To Record A Stolen Base": {"type": "sb", "threshold": 1},
    }

    # Get today's prop odds
    props = []
    for market_name, market_info in markets_to_model.items():
        rows = conn.execute("""
            SELECT player, market, over_odds, game
            FROM fd_prop_snapshots
            WHERE sport='MLB' AND market=? AND collected_at LIKE ?
            AND over_odds IS NOT NULL
            ORDER BY collected_at DESC
        """, (market_name, today + "%")).fetchall()

        # Deduplicate by player (keep latest)
        seen = set()
        for r in rows:
            player_name = r[0]
            if player_name in seen:
                continue
            seen.add(player_name)
            props.append({
                "player": player_name,
                "market": market_name,
                "market_type": market_info["type"],
                "threshold": market_info["threshold"],
                "odds": r[2],
                "game": r[3],
            })

    conn.close()

    if not props:
        print("No FanDuel batter props found for today.")
        return []

    print(f"Found {len(props)} batter props across {len(markets_to_model)} markets")

    # Match players to batter IDs by name
    # Build name->id lookup
    name_to_id = {}
    for bid, logs in batter_logs.items():
        if logs:
            name = logs[0]["name"]
            if name:
                name_to_id[name.lower()] = bid

    # Determine park and opposing pitcher for each game
    game_parks = {}
    game_away_team = {}
    for p in props:
        game = p["game"]
        if game and "@" in game:
            parts = game.split(" @ ")
            if len(parts) == 2:
                away_full = parts[0].strip()
                home_full = parts[1].strip()
                home_abbr = MLB_FULL_TO_ABBREV.get(home_full)
                away_abbr = MLB_FULL_TO_ABBREV.get(away_full)
                if home_abbr:
                    game_parks[game] = home_abbr
                if away_abbr:
                    game_away_team[game] = away_abbr

    # Get today's starters to find opposing pitchers
    gl_conn = sqlite3.connect(GL_DB, timeout=15)
    game_pitchers = {}  # game_string -> {home_pitcher_id, away_pitcher_id}
    try:
        starters = gl_conn.execute("""
            SELECT home_team, away_team, home_pitcher_id, away_pitcher_id
            FROM mlb_game_starters WHERE game_date = ?
        """, (today,)).fetchall()
        for s in starters:
            game_pitchers[s[0]] = {"home_pid": s[2], "away_pid": s[3]}
            game_pitchers[s[1]] = {"home_pid": s[2], "away_pid": s[3]}
    except Exception:
        pass

    # Also check mlb_pitchers table
    if not game_pitchers:
        try:
            rows = gl_conn.execute("""
                SELECT team, pitcher_id FROM mlb_pitchers WHERE game_date = ?
            """, (today,)).fetchall()
            for r in rows:
                team_abbr = MLB_FULL_TO_ABBREV.get(r[0], r[0])
                game_pitchers[team_abbr] = {"pitcher_id": r[1]}
        except Exception:
            pass
    gl_conn.close()

    # Build batter team lookup from most recent game
    batter_team = {}
    for bid, logs in batter_logs.items():
        if logs:
            batter_team[bid] = logs[-1]["team"]

    picks = []
    matched = 0
    unmatched = 0

    for p in props:
        player_lower = p["player"].lower()
        bid = name_to_id.get(player_lower)

        if not bid or bid not in batter_logs:
            unmatched += 1
            continue
        matched += 1

        park_team = game_parks.get(p["game"], "NYY")  # Default to neutral

        # Get opposing pitcher adjustment
        opp_pitcher_adj = None
        batter_tm = batter_team.get(bid)
        if batter_tm:
            # Batter's team -> find opposing pitcher
            opp_info = game_pitchers.get(batter_tm, {})
            opp_pid = None
            if "home_pid" in opp_info:
                # If batter is on away team, opposing pitcher is home pitcher
                if batter_tm == game_away_team.get(p["game"]):
                    opp_pid = opp_info.get("home_pid")
                else:
                    opp_pid = opp_info.get("away_pid")
            elif "pitcher_id" in opp_info:
                opp_pid = opp_info.get("pitcher_id")

            if opp_pid and opp_pid in pitcher_logs:
                opp_pitcher_adj = get_pitcher_adjustment(pitcher_logs[opp_pid], today)

        proj = compute_batter_projection(batter_logs[bid], today, park_team,
                                         opp_pitcher_adj=opp_pitcher_adj)
        if proj is None:
            continue

        # Calculate model probability based on market type (NegBin for count data)
        if p["market_type"] == "hr":
            raw_prob = negbin_at_least(proj["proj_hr_per_game"], p["threshold"], "hr")
        elif p["market_type"] == "hit":
            raw_prob = binomial_at_least(
                proj["expected_ab"], proj["avg_blended"] * proj["park_hit"],
                p["threshold"]
            )
        elif p["market_type"] == "tb":
            raw_prob = negbin_at_least(proj["proj_tb_per_game"], p["threshold"], "tb")
        elif p["market_type"] == "rbi":
            raw_prob = negbin_at_least(proj["proj_rbi_per_game"], p["threshold"], "rbi")
        elif p["market_type"] == "runs":
            raw_prob = negbin_at_least(proj["proj_runs_per_game"], p["threshold"], "runs")
        elif p["market_type"] == "sb":
            raw_prob = negbin_at_least(proj["proj_sb_per_game"], p["threshold"], "sb")
        else:
            continue

        model_prob = calibrate_prob(raw_prob, p["market_type"], p["threshold"])

        # Compare to FanDuel implied probability
        fd_prob = american_to_prob(p["odds"])
        if fd_prob is None or fd_prob <= 0:
            continue

        # Filter out likely non-starters: if FanDuel implies < 33% for a hit
        # market, the player is probably not in the starting lineup
        if p["market_type"] == "hit" and p["threshold"] == 1 and p["odds"] > 200:
            continue
        # Same for "To Record A Run" - starters are typically -money or close
        if p["market_type"] == "runs" and p["threshold"] == 1 and p["odds"] > 250:
            continue

        edge = model_prob - fd_prob

        if edge > 0.05:  # 5%+ edge (restored: NegBin fixed calibration)
            picks.append({
                "player": p["player"],
                "market": p["market"],
                "game": p["game"],
                "side": "YES",
                "model_prob": model_prob,
                "fd_prob": fd_prob,
                "edge": edge,
                "odds": p["odds"],
                "fair_odds": prob_to_american(model_prob),
                "proj": proj,
            })

    print(f"Matched {matched}/{matched + unmatched} players to historical data")
    print(f"Found {len(picks)} batter prop edges (5%+ threshold)")

    # Sort by edge descending
    picks.sort(key=lambda x: -x["edge"])
    return picks


def backtest():
    """Walk-forward backtest of all batter prop markets on 2024-2025 data."""
    print("Loading batter data...")
    batter_logs = load_batter_logs()
    if not batter_logs:
        print("No batter game logs found.")
        return

    print("Loading pitcher quality data...")
    pitcher_logs = load_pitcher_quality()

    print("\n=== Batter Prop Model Walk-Forward Backtest (2024-2025) ===")

    # Collect results per market type
    results = {
        "hr_1": {"actual": [], "prob": [], "label": "HR >= 1"},
        "hit_1": {"actual": [], "prob": [], "label": "Hit >= 1"},
        "hit_2": {"actual": [], "prob": [], "label": "2+ Hits"},
        "tb_2": {"actual": [], "prob": [], "label": "2+ TB"},
        "tb_3": {"actual": [], "prob": [], "label": "3+ TB"},
        "tb_4": {"actual": [], "prob": [], "label": "4+ TB"},
        "rbi_1": {"actual": [], "prob": [], "label": "RBI >= 1"},
        "runs_1": {"actual": [], "prob": [], "label": "Run >= 1"},
        "sb_1": {"actual": [], "prob": [], "label": "SB >= 1"},
    }

    total_tested = 0
    batters_tested = 0

    for bid, logs in batter_logs.items():
        if len(logs) < 50:
            continue

        # Walk-forward: test each game from 2024-2025 using prior data only
        tested_any = False
        for i in range(len(logs)):
            game = logs[i]
            if game["date"] < "2024-01-01":
                continue

            park_team = game["team"]  # Use actual game team for park factors
            prior_logs = logs[:i]

            proj = compute_batter_projection(prior_logs, game["date"], park_team,
                                             n_recent=10)
            if proj is None:
                continue

            tested_any = True
            total_tested += 1

            # HR market
            hr_prob = calibrate_prob(
                negbin_at_least(proj["proj_hr_per_game"], 1, "hr"), "hr", 1)
            results["hr_1"]["actual"].append(1 if game["hr"] >= 1 else 0)
            results["hr_1"]["prob"].append(hr_prob)

            # Hit markets
            hit_prob_1 = calibrate_prob(
                binomial_at_least(proj["expected_ab"],
                                  proj["avg_blended"] * proj["park_hit"], 1),
                "hit", 1)
            results["hit_1"]["actual"].append(1 if game["h"] >= 1 else 0)
            results["hit_1"]["prob"].append(hit_prob_1)

            hit_prob_2 = calibrate_prob(
                binomial_at_least(proj["expected_ab"],
                                  proj["avg_blended"] * proj["park_hit"], 2),
                "hit", 2)
            results["hit_2"]["actual"].append(1 if game["h"] >= 2 else 0)
            results["hit_2"]["prob"].append(hit_prob_2)

            # TB markets
            for thresh in [2, 3, 4]:
                tb_prob = calibrate_prob(
                    negbin_at_least(proj["proj_tb_per_game"], thresh, "tb"),
                    "tb", thresh)
                results[f"tb_{thresh}"]["actual"].append(
                    1 if game["tb"] >= thresh else 0)
                results[f"tb_{thresh}"]["prob"].append(tb_prob)

            # RBI market
            rbi_prob = calibrate_prob(
                negbin_at_least(proj["proj_rbi_per_game"], 1, "rbi"), "rbi", 1)
            results["rbi_1"]["actual"].append(1 if game["rbi"] >= 1 else 0)
            results["rbi_1"]["prob"].append(rbi_prob)

            # Runs market
            runs_prob = calibrate_prob(
                negbin_at_least(proj["proj_runs_per_game"], 1, "runs"), "runs", 1)
            results["runs_1"]["actual"].append(1 if game["runs"] >= 1 else 0)
            results["runs_1"]["prob"].append(runs_prob)

            # SB market
            sb_prob = calibrate_prob(
                negbin_at_least(proj["proj_sb_per_game"], 1, "sb"), "sb", 1)
            results["sb_1"]["actual"].append(1 if game["sb"] >= 1 else 0)
            results["sb_1"]["prob"].append(sb_prob)

        if tested_any:
            batters_tested += 1

    print(f"Total: {total_tested} game-projections across {batters_tested} batters\n")

    # Analyze each market
    print(f"{'Market':<14} {'Games':>7} {'Actual':>8} {'Pred':>8} {'Bias':>8} "
          f"{'MAE':>7} {'Top10%':>10} {'TopActual':>10}")
    print("-" * 82)

    for key, data in results.items():
        if not data["actual"]:
            continue
        actual = np.array(data["actual"])
        prob = np.array(data["prob"])

        act_rate = actual.mean()
        pred_rate = prob.mean()
        bias = pred_rate - act_rate
        mae = np.mean(np.abs(actual - prob))

        # Edge detection: when model says probability is highest (top 10%),
        # does the actual rate exceed the average?
        thresh_90 = np.percentile(prob, 90)
        top_mask = prob >= thresh_90
        top_actual = actual[top_mask].mean() if top_mask.sum() > 0 else 0
        top_pred = prob[top_mask].mean() if top_mask.sum() > 0 else 0

        print(f"{data['label']:<14} {len(actual):>7,} {act_rate:>7.1%} {pred_rate:>7.1%} "
              f"{bias:>+7.1%} {mae:>7.4f} {top_pred:>9.1%} {top_actual:>9.1%}")

    # Calibration: bin predictions and check actual rate
    print(f"\n--- Calibration (HR >= 1) ---")
    hr_actual = np.array(results["hr_1"]["actual"])
    hr_prob = np.array(results["hr_1"]["prob"])
    bins = [0, 0.05, 0.10, 0.15, 0.20, 0.30, 1.0]
    print(f"{'Bin':<12} {'Count':>7} {'Predicted':>10} {'Actual':>10} {'Diff':>10}")
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (hr_prob >= lo) & (hr_prob < hi)
        if mask.sum() < 10:
            continue
        avg_pred = hr_prob[mask].mean()
        avg_act = hr_actual[mask].mean()
        print(f"{lo:.0%}-{hi:.0%}    {mask.sum():>7,} {avg_pred:>9.1%} {avg_act:>9.1%} "
              f"{avg_act - avg_pred:>+9.1%}")

    print(f"\n--- Calibration (Hit >= 1) ---")
    hit_actual = np.array(results["hit_1"]["actual"])
    hit_prob = np.array(results["hit_1"]["prob"])
    bins = [0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    print(f"{'Bin':<12} {'Count':>7} {'Predicted':>10} {'Actual':>10} {'Diff':>10}")
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (hit_prob >= lo) & (hit_prob < hi)
        if mask.sum() < 10:
            continue
        avg_pred = hit_prob[mask].mean()
        avg_act = hit_actual[mask].mean()
        print(f"{lo:.0%}-{hi:.0%}    {mask.sum():>7,} {avg_pred:>9.1%} {avg_act:>9.1%} "
              f"{avg_act - avg_pred:>+9.1%}")

    # Discrimination test: can the model sort batters above/below population mean?
    # NOTE: This is NOT ROI. "Market price" = population avg rate (no vig, no individual pricing).
    # A positive number means the model identifies above-mean batters, not that it beats sportsbooks.
    # Real ROI requires real historical lines, which this project doesn't have for props.
    print(f"\n--- Discrimination Test (model vs population mean, NOT ROI) ---")
    for key in ["hr_1", "hit_1", "tb_2", "rbi_1", "runs_1"]:
        data = results[key]
        if not data["actual"]:
            continue
        actual = np.array(data["actual"])
        prob = np.array(data["prob"])
        avg_rate = actual.mean()

        edges = prob - avg_rate
        for edge_thresh in [0.03, 0.05, 0.10]:
            mask = edges >= edge_thresh
            if mask.sum() < 20:
                continue
            bet_actual = actual[mask].mean()
            bet_prob = prob[mask].mean()
            # Discrimination = (actual win rate * fair payout - 1) where fair payout = 1/avg_rate
            # Positive = model picks above-mean batters. NOT profitability against real lines.
            payout = 1.0 / avg_rate if avg_rate > 0 else 0
            disc = (bet_actual * payout - 1) * 100
            print(f"  {data['label']:<12} edge>={edge_thresh:.0%}: "
                  f"{mask.sum():>5} bets, actual={bet_actual:.1%}, disc={disc:+.1f}% (n={mask.sum()})")

    print(f"\nBacktest complete.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        backtest()
    else:
        picks = generate_today_picks()
        if picks:
            print(f"\n{'='*60}")
            print(f"  BATTER PROP PICKS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print(f"{'='*60}")
            for p in picks[:15]:  # Top 15
                edge_pct = p["edge"] * 100
                print(f"\n  {p['player']} - {p['market']}")
                print(f"    Game: {p['game']}")
                print(f"    FanDuel: {p['odds']:+d} ({p['fd_prob']*100:.1f}%)")
                print(f"    Model: {p['fair_odds']:+d} ({p['model_prob']*100:.1f}%)")
                print(f"    Edge: +{edge_pct:.1f}%")
                pr = p["proj"]
                if "hr" in p["market"].lower():
                    print(f"    HR/game: {pr['proj_hr_per_game']:.3f} | Park: {pr['park_hr']:.2f}")
                elif "hit" in p["market"].lower():
                    print(f"    AVG: {pr['avg_blended']:.3f} (L10: {pr['avg_recent']:.3f}) | AB: {pr['expected_ab']:.1f}")
                else:
                    print(f"    TB/game: {pr['proj_tb_per_game']:.2f} | Park HR: {pr['park_hr']:.2f}")
            print(f"\n{'='*60}")
        else:
            print("No batter prop edges found.")

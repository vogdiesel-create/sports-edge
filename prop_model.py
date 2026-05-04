#!/usr/bin/env python3
"""
Pitcher Strikeout Prop Model - Sports Edge

Predicts expected pitcher strikeouts per game using:
  - Pitcher K/9 rate (regressed to league avg based on IP)
  - IP projection (pitcher's historical average)
  - Matchup adjustment (opponent team K-rate vs league avg)
  - Poisson distribution for probability of K >= N

Compares model probabilities to FanDuel alt-line implied probabilities
to find edges.

Usage:
    python3 prop_model.py                # Today's predictions
    python3 prop_model.py --refresh      # Refresh pitcher game logs first
    python3 prop_model.py --pitcher 663460  # Single pitcher by ID
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from scipy.stats import poisson

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SPORTS_EDGE_DB = os.path.join(DATA_DIR, "sports_edge.db")
GAME_LINES_DB = os.path.join(DATA_DIR, "game_lines.db")

MLB_API = "https://statsapi.mlb.com/api/v1"

# League averages (2025-2026 baseline)
LEAGUE_AVG_K_PER_9 = 8.50
LEAGUE_AVG_IP_PER_START = 5.50
LEAGUE_AVG_K_RATE_BATTING = 0.230  # ~23% of PAs end in K, league-wide

# Regression: how much to regress toward league avg based on sample size
# At REGRESSION_IP innings, pitcher's rate is weighted 50/50 with league avg
REGRESSION_IP = 60.0
REGRESSION_STARTS_IP = 15  # At 15 starts, pitcher's avg IP is weighted 50/50 with league avg

# Minimum edge to flag as a pick
# Backtest: UNDER +30% ROI vs OVER +8% ROI — lower threshold for UNDER
MIN_EDGE_PCT = 5.0        # default (used for OVER)
MIN_EDGE_UNDER = 3.0      # lower bar for UNDER (proven 3x more profitable)
MAX_EDGE_OVER = 15.0      # cap OVER edges (game model lesson: huge edges = model errors)
MAX_EDGE_UNDER = 15.0     # cap UNDER edges: 15-20% is 13W-10L (57%, +$110 all-time), 10-15% is 24W-14L (63%, +$657). Apr 29.
DISABLE_OVER_BETS = False  # Re-enabled Apr 26: 16W-11L +$196 (59%WR). Bias correction 0.91->0.86 should improve accuracy.
DISABLE_UNDER_BETS = True   # DISABLED Apr 30: UNDERs 31W-29L (51.7%, -$330 all-time). Not profitable after vig. OVERs 20W-12L (62.5%, +$486).

# Pitcher blacklist: these arms cause 47% of all K-prop losses (W17 analysis, Apr 26).
# Model can't price their K variance correctly.
PITCHER_BLACKLIST = {
    "Cole Ragans",        # Extreme K variance, model consistently wrong (0W-1L)
    "Tarik Skubal",       # High-K elite arm, model underestimates ceiling (0W-1L)
    "Roki Sasaki",        # Dodgers rookie, model overestimates (0W-2L)
    "Jacob Misiorowski",  # Low sample, volatile K output (0W-2L)
    "Jack Leiter",        # Model misprices consistently (0W-2L)
    "Luis Severino",      # Model misprices consistently (0W-2L)
    "Shane Baz",          # Model underestimates Ks: exp ~4, actual 6 both times (0W-2L, -$185)
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [K-MODEL] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("prop_model")


# ===========================================================================
# Data Collection: Pitcher Game Logs from MLB Stats API
# ===========================================================================

def fetch_pitcher_game_log(pitcher_id: int, season: int = 2026) -> List[dict]:
    """Fetch pitcher game log from MLB Stats API."""
    url = f"{MLB_API}/people/{pitcher_id}/stats"
    params = {"stats": "gameLog", "season": season, "group": "pitching"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("stats") and data["stats"][0].get("splits"):
            return data["stats"][0]["splits"]
    except Exception as e:
        log.warning(f"Failed to fetch game log for pitcher {pitcher_id}: {e}")
    return []


def parse_innings_pitched(ip_str: str) -> float:
    """Convert innings pitched string (e.g., '6.1') to decimal innings.
    MLB format: 6.1 means 6 and 1/3 innings, 6.2 = 6 and 2/3."""
    try:
        ip = float(ip_str)
        whole = int(ip)
        fraction = ip - whole
        # .1 = 1/3, .2 = 2/3 in MLB notation
        if abs(fraction - 0.1) < 0.05:
            return whole + 1 / 3
        elif abs(fraction - 0.2) < 0.05:
            return whole + 2 / 3
        else:
            return ip  # already decimal
    except (ValueError, TypeError):
        return 0.0


def store_pitcher_game_logs(pitcher_id: int, pitcher_name: str, season: int = 2026):
    """Fetch and store pitcher game logs in SQLite."""
    splits = fetch_pitcher_game_log(pitcher_id, season)
    if not splits:
        return 0

    conn = sqlite3.connect(SPORTS_EDGE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pitcher_game_logs (
            pitcher_id INTEGER,
            pitcher_name TEXT,
            game_date TEXT,
            opponent TEXT,
            strikeouts INTEGER,
            innings_pitched REAL,
            hits_allowed INTEGER,
            walks INTEGER,
            earned_runs INTEGER,
            games_started INTEGER,
            k_per_9 REAL,
            season INTEGER,
            PRIMARY KEY (pitcher_id, game_date)
        )
    """)

    count = 0
    for split in splits:
        stat = split.get("stat", {})
        opponent = split.get("opponent", {}).get("name", "Unknown")
        game_date = split.get("date", "")
        ip = parse_innings_pitched(stat.get("inningsPitched", "0"))
        ks = int(stat.get("strikeOuts", 0))
        k9 = (ks / ip * 9) if ip > 0 else 0.0

        try:
            conn.execute("""
                INSERT OR REPLACE INTO pitcher_game_logs
                (pitcher_id, pitcher_name, game_date, opponent, strikeouts,
                 innings_pitched, hits_allowed, walks, earned_runs, games_started, k_per_9, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pitcher_id, pitcher_name, game_date, opponent, ks,
                round(ip, 2),
                int(stat.get("hits", 0)),
                int(stat.get("baseOnBalls", 0)),
                int(stat.get("earnedRuns", 0)),
                int(stat.get("gamesStarted", 0)),
                round(k9, 2),
                season,
            ))
            count += 1
        except Exception as e:
            log.warning(f"Error storing game log: {e}")

    conn.commit()
    conn.close()
    return count


# ===========================================================================
# Team Batting K-Rate: Aggregated from mlb_batters table
# ===========================================================================

def get_team_batting_k_rates() -> Dict[str, float]:
    """
    Compute team batting K% from individual batter stats in sports_edge.db.
    Returns {team_abbrev: k_rate} where k_rate is fraction (e.g., 0.25 = 25%).
    """
    conn = sqlite3.connect(SPORTS_EDGE_DB)
    rows = conn.execute("""
        SELECT team_abbrev,
               SUM(plate_appearances) as total_pa,
               SUM(CAST(plate_appearances * k_pct / 100.0 AS REAL)) as total_k
        FROM mlb_batters
        WHERE season = 2026 AND plate_appearances > 0
        GROUP BY team_abbrev
    """).fetchall()
    conn.close()

    rates = {}
    for team, pa, k_est in rows:
        if pa and pa > 0:
            rates[team] = k_est / pa
    return rates


def get_team_name_to_abbrev() -> Dict[str, str]:
    """Map full team names to abbreviations using mlb_teams table."""
    conn = sqlite3.connect(SPORTS_EDGE_DB)
    rows = conn.execute("""
        SELECT team_name, team_abbrev FROM mlb_teams WHERE season = 2026
    """).fetchall()
    conn.close()

    mapping = {}
    for name, abbrev in rows:
        mapping[name] = abbrev
        # Also map common variations
        # "New York Yankees" -> "NYY", "Los Angeles Angels" -> "LAA"
    return mapping


def get_team_id_to_abbrev() -> Dict[int, str]:
    """Map team IDs to abbreviations."""
    conn = sqlite3.connect(SPORTS_EDGE_DB)
    rows = conn.execute("""
        SELECT team_id, team_abbrev FROM mlb_teams WHERE season = 2026
    """).fetchall()
    conn.close()
    return {tid: abbrev for tid, abbrev in rows}


# ===========================================================================
# Prediction Model
# ===========================================================================

class PitcherStrikeoutModel:
    """Predicts expected strikeouts for a pitcher in a given matchup."""

    def __init__(self):
        self.team_k_rates = get_team_batting_k_rates()
        self.team_name_to_abbrev = get_team_name_to_abbrev()
        self.team_id_to_abbrev = get_team_id_to_abbrev()
        self.league_avg_k_rate = LEAGUE_AVG_K_RATE_BATTING

        # Compute league-average batting K-rate from actual data if available
        if self.team_k_rates:
            self.league_avg_k_rate = sum(self.team_k_rates.values()) / len(self.team_k_rates)
            log.info(f"League avg batting K-rate from data: {self.league_avg_k_rate:.3f}")

    def get_pitcher_stats(self, pitcher_id: int) -> Optional[dict]:
        """Get pitcher's season stats from game logs.
        Excludes today's date since games may be in progress with partial stats."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(SPORTS_EDGE_DB)
        rows = conn.execute("""
            SELECT strikeouts, innings_pitched, games_started
            FROM pitcher_game_logs
            WHERE pitcher_id = ? AND season = 2026 AND game_date < ?
            ORDER BY game_date
        """, (pitcher_id, today)).fetchall()
        conn.close()

        if not rows:
            return None

        total_k = sum(r[0] for r in rows)
        total_ip = sum(r[1] for r in rows)
        total_gs = sum(r[2] for r in rows)
        games = len(rows)

        k_per_9 = (total_k / total_ip * 9) if total_ip > 0 else LEAGUE_AVG_K_PER_9
        avg_ip = total_ip / games if games > 0 else LEAGUE_AVG_IP_PER_START
        avg_k = total_k / games if games > 0 else 0

        return {
            "games": games,
            "total_k": total_k,
            "total_ip": round(total_ip, 1),
            "k_per_9": round(k_per_9, 2),
            "avg_ip": round(avg_ip, 2),
            "avg_k": round(avg_k, 2),
        }

    def get_prior_season_k9(self, pitcher_id: int) -> Optional[float]:
        """Get pitcher's prior season (2025) K/9 from MLB API.
        Returns None if no prior data available."""
        if not hasattr(self, '_prior_k9_cache'):
            self._prior_k9_cache = {}
        if pitcher_id in self._prior_k9_cache:
            return self._prior_k9_cache[pitcher_id]

        try:
            import requests
            r = requests.get(
                f"{MLB_API}/people/{pitcher_id}/stats?stats=season&season=2025&group=pitching",
                timeout=5
            )
            data = r.json()
            if data.get("stats") and data["stats"][0].get("splits"):
                stat = data["stats"][0]["splits"][0]["stat"]
                ip = float(stat.get("inningsPitched", "0"))
                if ip >= 30:  # need meaningful sample
                    k9 = float(stat.get("strikeoutsPer9Inn", "0"))
                    if k9 > 0:
                        self._prior_k9_cache[pitcher_id] = k9
                        return k9
        except Exception:
            pass
        self._prior_k9_cache[pitcher_id] = None
        return None

    def regressed_k_per_9(self, raw_k9: float, innings_pitched: float,
                          pitcher_id: int = None) -> float:
        """
        Regress pitcher K/9 toward a prior based on sample size.
        Prior = pitcher's 2025 K/9 if available, else league average.
        More innings = more weight on actual rate.
        At REGRESSION_IP innings, it's 50/50 actual vs prior.
        """
        # Use pitcher-specific prior if available (fixes elite pitcher underestimation)
        prior_k9 = LEAGUE_AVG_K_PER_9
        if pitcher_id:
            prior = self.get_prior_season_k9(pitcher_id)
            if prior:
                prior_k9 = prior

        weight = innings_pitched / (innings_pitched + REGRESSION_IP)
        return weight * raw_k9 + (1 - weight) * prior_k9

    def predict_ks(
        self,
        pitcher_id: int,
        pitcher_name: str,
        pitcher_k9: float,
        pitcher_ip: float,
        opponent_abbrev: str,
    ) -> dict:
        """
        Predict expected strikeouts for a pitcher vs an opponent.

        Returns dict with expected_ks, probabilities for each K threshold,
        and component details.
        """
        # Step 1: Get pitcher game log stats (if available)
        stats = self.get_pitcher_stats(pitcher_id)

        if stats and stats["total_ip"] > 0:
            raw_k9 = stats["k_per_9"]
            total_ip = stats["total_ip"]
            avg_ip_per_start = stats["avg_ip"]
        else:
            # Fall back to season stats from mlb_pitchers table
            raw_k9 = pitcher_k9 if pitcher_k9 and pitcher_k9 > 0 else LEAGUE_AVG_K_PER_9
            total_ip = pitcher_ip if pitcher_ip and pitcher_ip > 0 else 0
            avg_ip_per_start = min(total_ip / max(1, round(total_ip / 5.5)), 7.0) if total_ip > 0 else LEAGUE_AVG_IP_PER_START
            if avg_ip_per_start < 3.0:
                avg_ip_per_start = LEAGUE_AVG_IP_PER_START

        # Step 2: Regress K/9 toward prior (pitcher's 2025 K/9 or league avg)
        regressed_k9 = self.regressed_k_per_9(raw_k9, total_ip, pitcher_id=pitcher_id)

        # Step 3: IP projection - regress toward league avg for small samples
        games = stats["games"] if stats else 1
        ip_weight = games / (games + REGRESSION_STARTS_IP)
        regressed_ip = ip_weight * avg_ip_per_start + (1 - ip_weight) * LEAGUE_AVG_IP_PER_START
        ip_projection = max(4.0, min(regressed_ip, 7.5))

        # Step 4: Matchup adjustment based on opponent K-rate
        opp_k_rate = self.team_k_rates.get(opponent_abbrev, self.league_avg_k_rate)
        matchup_adj = opp_k_rate / self.league_avg_k_rate if self.league_avg_k_rate > 0 else 1.0

        # Step 5: Calculate expected Ks
        # expected_Ks = (regressed_K/9) * (IP_projection / 9) * matchup_adjustment
        expected_ks = regressed_k9 * (ip_projection / 9.0) * matchup_adj

        # Step 5b: Bias correction — model overestimates by +0.9 Ks on average (N=54, Apr 26 W17)
        # UNDER bias: -0.84, OVER bias: -0.96. Avg ~0.9. Previous 0.91 was too weak.
        expected_ks = expected_ks * 0.86  # ~0.9 reduction at avg of 6.4 expected Ks

        # Step 6: Poisson probabilities for each threshold
        probs = {}
        for n in range(1, 16):
            # P(K >= n) = 1 - P(K <= n-1) = 1 - poisson.cdf(n-1, expected_ks)
            probs[n] = 1.0 - poisson.cdf(n - 1, expected_ks)

        return {
            "pitcher_name": pitcher_name,
            "pitcher_id": pitcher_id,
            "opponent": opponent_abbrev,
            "raw_k9": round(raw_k9, 2),
            "regressed_k9": round(regressed_k9, 2),
            "ip_projection": round(ip_projection, 2),
            "matchup_adj": round(matchup_adj, 3),
            "opp_k_rate": round(opp_k_rate, 3),
            "expected_ks": round(expected_ks, 2),
            "total_ip_sample": round(total_ip, 1),
            "probs": probs,
            "game_log_games": stats["games"] if stats else 0,
        }

    def get_fd_strikeout_props(self, pitcher_name: str) -> Dict[int, float]:
        """
        Get FanDuel alt strikeout lines for a pitcher.
        Returns {threshold: american_odds} for alt lines,
        plus the main over/under line.
        """
        conn = sqlite3.connect(SPORTS_EDGE_DB)

        # Get the latest snapshot for this pitcher's alt K lines
        # Use the most recent collected_at
        rows = conn.execute("""
            SELECT player, over_odds, collected_at
            FROM fd_prop_snapshots
            WHERE market LIKE ? AND market LIKE '%Alt Strikeout%'
            AND collected_at >= date('now', '-1 day')
            ORDER BY collected_at DESC
        """, (f"{pitcher_name}%",)).fetchall()

        alt_lines = {}
        seen = set()
        for player, odds, ts in rows:
            # Parse "Player Name N+ Strikeouts" -> N
            match = re.match(r'.+ (\d+)\+ Strikeouts?', player)
            if match:
                threshold = int(match.group(1))
                if threshold not in seen:
                    alt_lines[threshold] = odds
                    seen.add(threshold)

        # Also get the main over/under line
        main_row = conn.execute("""
            SELECT line, over_odds, under_odds, collected_at
            FROM fd_prop_snapshots
            WHERE market LIKE ? AND market NOT LIKE '%Alt%' AND market NOT LIKE '%Combined%'
            AND collected_at >= date('now', '-1 day')
            ORDER BY collected_at DESC LIMIT 1
        """, (f"{pitcher_name}%Strikeout%",)).fetchone()

        main_line = None
        if main_row:
            main_line = {
                "line": main_row[0],
                "over_odds": main_row[1],
                "under_odds": main_row[2],
            }

        conn.close()

        return {
            "alt_lines": alt_lines,
            "main_line": main_line,
        }

    def american_to_implied_prob(self, odds: int) -> float:
        """Convert American odds to implied probability."""
        if odds is None:
            return 0.0
        if odds > 0:
            return 100.0 / (odds + 100.0)
        else:
            return abs(odds) / (abs(odds) + 100.0)

    def find_edges(self, prediction: dict, fd_props: dict) -> List[dict]:
        """Compare model probabilities to FanDuel implied probabilities.
        Checks both OVER (K >= threshold) and UNDER (K < threshold) on main line.
        Backtest: UNDER is significantly more profitable (+26-30% ROI vs +2-8% for OVER).
        """
        edges = []

        alt_lines = fd_props.get("alt_lines", {})
        for threshold, odds in sorted(alt_lines.items()):
            implied_prob = self.american_to_implied_prob(odds)
            model_prob = prediction["probs"].get(threshold, 0.0)
            edge = (model_prob - implied_prob) * 100  # percentage points

            edges.append({
                "threshold": threshold,
                "label": f"{threshold}+ Ks",
                "side": "over",
                "fd_odds": odds,
                "fd_implied": round(implied_prob * 100, 1),
                "model_prob": round(model_prob * 100, 1),
                "edge": round(edge, 1),
            })

        # Check main over/under line
        main = fd_props.get("main_line")
        if main and main["line"]:
            line = main["line"]
            threshold = int(line) + 1  # over 4.5 means 5+

            # OVER check
            over_implied = self.american_to_implied_prob(main["over_odds"])
            model_over = prediction["probs"].get(threshold, 0.0)
            over_edge = (model_over - over_implied) * 100

            existing = next((e for e in edges if e["threshold"] == threshold), None)
            if existing:
                if over_edge > existing["edge"]:
                    existing["label"] = f"Over {line} (main)"
                    existing["fd_odds"] = main["over_odds"]
                    existing["fd_implied"] = round(over_implied * 100, 1)
                    existing["edge"] = round(over_edge, 1)
            else:
                edges.append({
                    "threshold": threshold,
                    "label": f"Over {line} (main)",
                    "side": "over",
                    "fd_odds": main["over_odds"],
                    "fd_implied": round(over_implied * 100, 1),
                    "model_prob": round(model_over * 100, 1),
                    "edge": round(over_edge, 1),
                })

            # UNDER check - backtest shows this is the real edge
            if main.get("under_odds"):
                under_implied = self.american_to_implied_prob(main["under_odds"])
                model_under = 1.0 - model_over  # P(K < threshold) = 1 - P(K >= threshold)
                under_edge = (model_under - under_implied) * 100

                edges.append({
                    "threshold": threshold,
                    "label": f"Under {line} (main)",
                    "side": "under",
                    "fd_odds": main["under_odds"],
                    "fd_implied": round(under_implied * 100, 1),
                    "model_prob": round(model_under * 100, 1),
                    "edge": round(under_edge, 1),
                })

        return edges

    def predict_today(self, refresh: bool = True) -> List[dict]:
        """
        Full pipeline: get today's pitchers, fetch game logs, predict Ks,
        compare to FanDuel lines, return picks with edges.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log.info(f"=== Pitcher Strikeout Model - {today} ===")

        # Step 1: Get today's starters from mlb_pitchers table (game_lines.db)
        conn_gl = sqlite3.connect(GAME_LINES_DB)
        pitchers = conn_gl.execute("""
            SELECT DISTINCT pitcher_name, pitcher_id, team, k_per_9, innings_pitched, game_id
            FROM mlb_pitchers
            WHERE game_date = ?
            ORDER BY team
        """, (today,)).fetchall()
        conn_gl.close()

        if not pitchers:
            log.warning("No pitchers found for today. Run mlb_data_pipeline.py first.")
            return []

        log.info(f"Found {len(pitchers)} starters for today")

        # Step 2: Get today's schedule for opponent mapping
        conn_se = sqlite3.connect(SPORTS_EDGE_DB)
        schedule = conn_se.execute("""
            SELECT game_pk, home_team_id, home_team_abbrev,
                   away_team_id, away_team_abbrev,
                   home_pitcher_id, away_pitcher_id
            FROM mlb_schedule
            WHERE game_date = ?
        """, (today,)).fetchall()
        conn_se.close()

        # Build pitcher_id -> opponent_abbrev mapping
        pitcher_opponent = {}
        for gp, ht_id, ht_ab, at_id, at_ab, hp_id, ap_id in schedule:
            pitcher_opponent[hp_id] = at_ab  # home pitcher faces away team
            pitcher_opponent[ap_id] = ht_ab  # away pitcher faces home team

        # Step 3: Fetch game logs for each pitcher
        if refresh:
            log.info("Fetching pitcher game logs from MLB API...")
            for name, pid, team, k9, ip, gid in pitchers:
                n = store_pitcher_game_logs(pid, name, 2026)
                if n > 0:
                    log.info(f"  {name}: {n} game logs stored")
                else:
                    log.warning(f"  {name}: no game logs found")
                time.sleep(0.3)  # rate limit

        # Step 4: Predict for each pitcher (deduplicate by pitcher_id)
        results = []
        seen_pids = set()
        for name, pid, team, k9, ip, gid in pitchers:
            if pid in seen_pids:
                continue
            seen_pids.add(pid)
            opponent = pitcher_opponent.get(pid)
            if not opponent:
                log.warning(f"  {name}: no opponent mapping found, skipping")
                continue

            # Predict
            pred = self.predict_ks(pid, name, k9, ip, opponent)

            # Get FD props
            fd = self.get_fd_strikeout_props(name)

            # Find edges
            edges = self.find_edges(pred, fd)

            results.append({
                "prediction": pred,
                "fd_props": fd,
                "edges": edges,
                "team": team,
            })

        # Step 5: Sort by best edge
        results.sort(
            key=lambda x: max((e["edge"] for e in x["edges"]), default=0),
            reverse=True,
        )

        return results


# ===========================================================================
# Display
# ===========================================================================

def format_results(results: List[dict], min_edge: float = MIN_EDGE_PCT) -> str:
    """Format results for display."""
    lines = []
    lines.append("=" * 80)
    lines.append("PITCHER STRIKEOUT PROP MODEL - EDGE DETECTION")
    lines.append("=" * 80)
    lines.append("")

    picks = []

    for r in results:
        pred = r["prediction"]
        edges = r["edges"]
        team = r["team"]

        # Skip blacklisted pitchers
        if pred["pitcher_name"] in PITCHER_BLACKLIST:
            lines.append(f"--- {pred['pitcher_name']} ({team}) vs {pred['opponent']} --- BLACKLISTED (skip)")
            lines.append("")
            continue

        lines.append(f"--- {pred['pitcher_name']} ({team}) vs {pred['opponent']} ---")
        lines.append(
            f"  K/9: {pred['raw_k9']} raw -> {pred['regressed_k9']} regressed "
            f"(sample: {pred['total_ip_sample']} IP, {pred['game_log_games']} games)"
        )
        lines.append(
            f"  IP proj: {pred['ip_projection']} | "
            f"Matchup adj: {pred['matchup_adj']:.3f} "
            f"(opp K-rate: {pred['opp_k_rate']:.3f})"
        )
        lines.append(f"  EXPECTED Ks: {pred['expected_ks']}")
        lines.append("")

        if edges:
            lines.append(f"  {'Line':<16} {'FD Odds':>8} {'FD Impl%':>9} {'Model%':>8} {'Edge':>8}")
            lines.append(f"  {'-'*52}")
            for e in sorted(edges, key=lambda x: x["threshold"]):
                side = e.get("side", "over")
                # Skip OVER bets entirely -- data shows they lose money
                if DISABLE_OVER_BETS and side == "over":
                    continue
                if DISABLE_UNDER_BETS and side == "under":
                    continue
                edge_threshold = MIN_EDGE_UNDER if side == "under" else min_edge
                # Cap: skip overconfident edges (same pattern as game model 12%+ issue)
                if side == "over" and e["edge"] > MAX_EDGE_OVER:
                    continue
                if side == "under" and e["edge"] > MAX_EDGE_UNDER:
                    continue
                marker = " ***" if e["edge"] >= edge_threshold else ""
                lines.append(
                    f"  {e['label']:<16} {e['fd_odds']:>+8} {e['fd_implied']:>8.1f}% "
                    f"{e['model_prob']:>7.1f}% {e['edge']:>+7.1f}%{marker}"
                )
                if e["edge"] >= edge_threshold:
                    picks.append({
                        "pitcher": pred["pitcher_name"],
                        "team": team,
                        "opponent": pred["opponent"],
                        "pick": e["label"],
                        "side": e.get("side", "over"),
                        "odds": e["fd_odds"],
                        "model_prob": e["model_prob"],
                        "fd_implied": e["fd_implied"],
                        "edge": e["edge"],
                        "expected_ks": pred["expected_ks"],
                    })
        else:
            lines.append("  No FanDuel props available for this pitcher")

        lines.append("")

    # Summary of picks
    if picks:
        lines.append("=" * 80)
        lines.append(f"TOP PICKS (edge >= {min_edge}%)")
        lines.append("=" * 80)
        picks.sort(key=lambda x: x["edge"], reverse=True)
        for p in picks:
            lines.append(
                f"  {p['pitcher']:<20} {p['pick']:<16} "
                f"odds: {p['odds']:>+5} | model: {p['model_prob']:.1f}% "
                f"vs FD: {p['fd_implied']:.1f}% | EDGE: {p['edge']:>+.1f}%"
            )
    else:
        lines.append("No picks found above minimum edge threshold.")

    return "\n".join(lines)


# ===========================================================================
# Save & Paper Trading
# ===========================================================================

PROPS_DIR = os.path.join(DATA_DIR, "k_props")
K_LEDGER_PATH = os.path.join(DATA_DIR, "k_prop_ledger.json")
BANKROLL = 3000.0
KELLY_FRACTION = 0.25  # Quarter-Kelly


def save_predictions(results: List[dict], picks: List[dict], min_edge: float) -> str:
    """Save predictions + picks to timestamped JSON. Returns file path."""
    os.makedirs(PROPS_DIR, exist_ok=True)
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M")

    payload = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "min_edge": min_edge,
        "total_pitchers": len(results),
        "total_picks": len(picks),
        "predictions": [],
        "picks": picks,
    }

    for r in results:
        pred = r["prediction"]
        payload["predictions"].append({
            "pitcher": pred["pitcher_name"],
            "pitcher_id": pred.get("pitcher_id"),
            "team": r["team"],
            "opponent": pred["opponent"],
            "expected_ks": pred["expected_ks"],
            "raw_k9": pred["raw_k9"],
            "regressed_k9": pred["regressed_k9"],
            "ip_projection": pred["ip_projection"],
            "matchup_adj": round(pred["matchup_adj"], 4),
            "total_ip_sample": pred["total_ip_sample"],
            "game_log_games": pred["game_log_games"],
            "edges": r["edges"],
        })

    path = os.path.join(PROPS_DIR, f"k_props_{ts}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    latest = os.path.join(PROPS_DIR, "latest.json")
    with open(latest, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    log.info(f"Saved {len(picks)} picks to {path}")
    return path


def load_k_ledger() -> dict:
    """Load or initialize the K-prop paper trading ledger."""
    if os.path.exists(K_LEDGER_PATH):
        with open(K_LEDGER_PATH) as f:
            return json.load(f)
    return {
        "bankroll": BANKROLL,
        "started": datetime.now().isoformat(),
        "bets": [],
        "summary": {
            "total_bets": 0, "graded": 0, "wins": 0, "losses": 0,
            "pushes": 0, "total_wagered": 0.0, "total_pnl": 0.0,
        },
    }


def save_k_ledger(ledger: dict):
    with open(K_LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)


MAX_BETS_PER_PITCHER = 1  # Cap at 1: double exposure cost -$91 over 3 instances (H008)
MAX_DAILY_EXPOSURE = 0.25  # Max 25% of bankroll wagered per day


def log_k_prop_picks(picks: List[dict]):
    """Add qualifying K-prop picks to the paper trading ledger.
    Limits to top MAX_BETS_PER_PITCHER edges per pitcher to control correlation.
    Never bets both sides of the same pitcher. Caps daily exposure."""
    if not picks:
        return

    # Sort by edge descending, then limit per pitcher
    # Also prevent betting OVER and UNDER on same pitcher (guaranteed vig loss)
    sorted_picks = sorted(picks, key=lambda x: x["edge"], reverse=True)
    pitcher_counts = {}
    pitcher_sides = {}  # track which side we've bet for each pitcher
    filtered_picks = []
    for p in sorted_picks:
        name = p["pitcher"]
        side = p.get("side", "over")

        # Don't bet both sides of same pitcher
        if name in pitcher_sides and pitcher_sides[name] != side:
            continue

        pitcher_counts[name] = pitcher_counts.get(name, 0) + 1
        if pitcher_counts[name] <= MAX_BETS_PER_PITCHER:
            filtered_picks.append(p)
            pitcher_sides[name] = side

    ledger = load_k_ledger()
    existing_ids = {b["pick_id"] for b in ledger["bets"]}
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    new_count = 0
    bankroll = ledger["bankroll"]

    # Track daily exposure to cap total risk
    today_wagered = sum(b["wager"] for b in ledger["bets"] if b.get("date") == today)
    max_daily = bankroll * MAX_DAILY_EXPOSURE

    for p in filtered_picks:
        pick_id = f"K|{today}|{p['pitcher']}|{p['pick']}"
        if pick_id in existing_ids:
            continue

        # Check daily exposure cap
        if today_wagered >= max_daily:
            log.info(f"Daily exposure cap reached (${today_wagered:.0f} / ${max_daily:.0f}). Skipping remaining picks.")
            break

        edge_decimal = p["edge"] / 100.0
        model_prob = p["model_prob"] / 100.0
        fd_implied = p["fd_implied"] / 100.0

        # Quarter-Kelly sizing
        odds = p["odds"]
        if odds > 0:
            b = odds / 100.0
        else:
            b = 100.0 / abs(odds)

        kelly = (model_prob * b - (1 - model_prob)) / b
        kelly = max(kelly, 0)
        wager_pct = kelly * KELLY_FRACTION
        wager = round(bankroll * min(wager_pct, 0.03), 2)  # cap at 3% bankroll
        if wager < 5:
            wager = 5.0  # minimum bet

        # Don't exceed daily cap
        if today_wagered + wager > max_daily:
            wager = round(max_daily - today_wagered, 2)
            if wager < 5:
                break

        if odds > 0:
            profit_if_win = round(wager * odds / 100, 2)
        else:
            profit_if_win = round(wager * 100 / abs(odds), 2)

        # Parse threshold from pick label
        pick_label = p["pick"]
        side = p.get("side", "over")
        if "+" in pick_label:
            threshold = int(pick_label.split("+")[0])
        elif "Over" in pick_label or "Under" in pick_label:
            # "Over 4.5 (main)" or "Under 4.5 (main)" -> threshold = 5
            import re as _re
            m = _re.search(r'(\d+\.?\d*)', pick_label)
            threshold = int(float(m.group(1))) + 1 if m else None
        else:
            threshold = None

        bet = {
            "pick_id": pick_id,
            "logged_at": now.isoformat(),
            "date": today,
            "sport": "MLB",
            "market": "pitcher_strikeouts",
            "pitcher": p["pitcher"],
            "team": p["team"],
            "opponent": p["opponent"],
            "pick": pick_label,
            "side": side,
            "threshold": threshold,
            "odds": odds,
            "model_prob": round(model_prob, 4),
            "fd_implied": round(fd_implied, 4),
            "edge": round(edge_decimal, 4),
            "expected_ks": p["expected_ks"],
            "kelly_pct": round(wager_pct * 100, 2),
            "wager": wager,
            "profit_if_win": profit_if_win,
            "result": None,
            "actual_ks": None,
            "graded_at": None,
        }

        ledger["bets"].append(bet)
        ledger["summary"]["total_bets"] += 1
        ledger["summary"]["total_wagered"] += wager
        today_wagered += wager
        existing_ids.add(pick_id)
        new_count += 1

    save_k_ledger(ledger)
    log.info(f"Logged {new_count} K-prop picks ({ledger['summary']['total_bets']} total in ledger)")
    return new_count


def grade_k_props():
    """Grade K-prop bets using actual pitcher strikeout data from MLB API."""
    ledger = load_k_ledger()
    ungraded = [b for b in ledger["bets"] if b["result"] is None]
    if not ungraded:
        log.info("No ungraded K-prop bets.")
        return

    log.info(f"Grading {len(ungraded)} K-prop bets...")
    graded = 0

    for bet in ungraded:
        date = bet.get("date")
        pitcher = bet.get("pitcher")
        threshold = bet.get("threshold")
        if not date or not pitcher or threshold is None:
            continue

        # Step 1: Get game PKs for that date
        sched_url = f"{MLB_API}/schedule?date={date}&sportId=1"
        try:
            sched_resp = requests.get(sched_url, timeout=15)
            sched_data = sched_resp.json()
        except Exception as e:
            log.warning(f"  Failed to fetch schedule for {date}: {e}")
            continue

        actual_ks = None
        for d in sched_data.get("dates", []):
            for g in d.get("games", []):
                state = g.get("status", {}).get("abstractGameState", "")
                if state != "Final":
                    continue
                gpk = g.get("gamePk")
                if not gpk:
                    continue

                # Step 2: Fetch live feed for boxscore
                try:
                    live_url = f"{MLB_API.replace('/v1', '/v1.1')}/game/{gpk}/feed/live"
                    live_resp = requests.get(live_url, timeout=15)
                    live_data = live_resp.json()
                except Exception:
                    continue

                box = live_data.get("liveData", {}).get("boxscore", {})
                if not box:
                    continue
                for side in ("away", "home"):
                    players = box.get("teams", {}).get(side, {}).get("players", {})
                    for pid, pdata in players.items():
                        pname = pdata.get("person", {}).get("fullName", "")
                        if pname.lower() == pitcher.lower():
                            stats = pdata.get("stats", {}).get("pitching", {})
                            ks = stats.get("strikeOuts", 0)
                            actual_ks = ks
                            break
                    if actual_ks is not None:
                        break
                if actual_ks is not None:
                    break
            if actual_ks is not None:
                break

        if actual_ks is not None:
            bet["actual_ks"] = actual_ks
            bet_side = bet.get("side", "over")

            if bet_side == "under":
                # UNDER wins when actual < threshold
                won = actual_ks < threshold
            else:
                # OVER wins when actual >= threshold
                won = actual_ks >= threshold

            if won:
                bet["result"] = "win"
                bet["pnl"] = bet["profit_if_win"]
                ledger["summary"]["wins"] += 1
            else:
                bet["result"] = "loss"
                bet["pnl"] = -bet["wager"]
                ledger["summary"]["losses"] += 1

            ledger["summary"]["graded"] += 1
            ledger["summary"]["total_pnl"] = round(
                ledger["summary"].get("total_pnl", 0) + bet.get("pnl", 0), 2
            )
            bet["graded_at"] = datetime.now().isoformat()
            graded += 1
            log.info(f"  {pitcher}: {actual_ks} Ks vs {threshold}+ -> {bet['result']} (${bet['pnl']:+.2f})")

    # Recompute bankroll from actual bet PnL (prevents drift)
    all_graded = [b for b in ledger["bets"] if b.get("result") in ("win", "loss")]
    computed_pnl = sum(b.get("pnl", 0) for b in all_graded)
    ledger["bankroll"] = round(BANKROLL + computed_pnl, 2)

    save_k_ledger(ledger)
    s = ledger["summary"]
    log.info(f"Graded {graded} bets. Record: {s['wins']}W-{s['losses']}L, PnL: ${s['total_pnl']:+.2f}")


# ===========================================================================
# Backtest
# ===========================================================================

def run_k_backtest(min_starts: int = 3):
    """
    Walk-forward backtest of the K-prop Poisson model using 2025 data.
    For each game start, use only prior games to predict Ks, then compare to actual.
    """
    conn = sqlite3.connect(SPORTS_EDGE_DB)

    # Get all 2025 game starts ordered by date
    rows = conn.execute("""
        SELECT pitcher_id, pitcher_name, game_date, opponent, strikeouts, innings_pitched
        FROM pitcher_game_logs_2025
        WHERE game_started = 1
        ORDER BY game_date
    """).fetchall()
    conn.close()

    if not rows:
        print("No 2025 game log data. Run the data fetch first.")
        return

    print(f"Backtesting {len(rows)} game starts from 2025...")

    # Build pitcher history incrementally
    pitcher_history = {}  # pid -> [(date, ks, ip), ...]
    results = []

    for pid, name, date, opp, actual_ks, ip in rows:
        # Get prior history for this pitcher
        history = pitcher_history.get(pid, [])

        if len(history) >= min_starts:
            # Enough data to make a prediction
            total_k = sum(h[1] for h in history)
            total_ip = sum(h[2] for h in history)
            games = len(history)

            if total_ip > 0:
                raw_k9 = total_k / total_ip * 9
                avg_ip = total_ip / games

                # Regress toward league avg
                weight = total_ip / (total_ip + REGRESSION_IP)
                regressed_k9 = weight * raw_k9 + (1 - weight) * LEAGUE_AVG_K_PER_9

                # IP projection
                ip_proj = max(4.0, min(avg_ip, 7.5))

                # Expected Ks (no matchup adj in backtest - we don't have team K rates for 2025)
                expected_ks = regressed_k9 * (ip_proj / 9.0)

                results.append({
                    "pitcher": name,
                    "date": date,
                    "expected": round(expected_ks, 2),
                    "actual": actual_ks,
                    "error": actual_ks - expected_ks,
                    "abs_error": abs(actual_ks - expected_ks),
                    "prior_games": games,
                    "prior_ip": round(total_ip, 1),
                })

        # Add this game to history
        if pid not in pitcher_history:
            pitcher_history[pid] = []
        pitcher_history[pid].append((date, actual_ks, ip))

    if not results:
        print("Not enough pitcher history for backtesting.")
        return

    # Calculate metrics
    n = len(results)
    mae = sum(r["abs_error"] for r in results) / n
    bias = sum(r["error"] for r in results) / n
    rmse = (sum(r["error"] ** 2 for r in results) / n) ** 0.5

    # Correlation
    exp_vals = [r["expected"] for r in results]
    act_vals = [r["actual"] for r in results]
    exp_mean = sum(exp_vals) / n
    act_mean = sum(act_vals) / n
    cov = sum((e - exp_mean) * (a - act_mean) for e, a in zip(exp_vals, act_vals)) / n
    std_e = (sum((e - exp_mean) ** 2 for e in exp_vals) / n) ** 0.5
    std_a = (sum((a - act_mean) ** 2 for a in act_vals) / n) ** 0.5
    corr = cov / (std_e * std_a) if std_e > 0 and std_a > 0 else 0

    print(f"\n{'='*60}")
    print(f"K-PROP MODEL BACKTEST (2025 season, {n} predictions)")
    print(f"{'='*60}")
    print(f"MAE:         {mae:.2f} Ks")
    print(f"RMSE:        {rmse:.2f} Ks")
    print(f"Bias:        {bias:+.2f} Ks ({'over' if bias > 0 else 'under'}-predicting)")
    print(f"Correlation: {corr:.3f}")
    print(f"Avg Expected: {exp_mean:.2f}")
    print(f"Avg Actual:   {act_mean:.2f}")

    # Simulate betting: would we profit betting OVER at various thresholds?
    print(f"\nSimulated K-prop betting (OVER only, -110 odds):")
    for edge_min in [0.03, 0.05, 0.07, 0.10]:
        wins = losses = 0
        for r in results:
            expected = r["expected"]
            actual = r["actual"]
            # For each common K threshold
            for threshold in [4, 5, 6, 7, 8]:
                model_prob = 1.0 - poisson.cdf(threshold - 1, expected)
                # Assume market is 50% (fair line) for simplicity
                # In reality we'd need actual prop odds
                assumed_fair = 0.50
                edge = model_prob - assumed_fair
                if edge >= edge_min and model_prob > 0.50:
                    if actual >= threshold:
                        wins += 1
                    else:
                        losses += 1

        total = wins + losses
        if total:
            wr = wins / total * 100
            pnl_per = wins * (100 / 110) - losses
            roi = pnl_per / total * 100
            print(f"  Edge>={edge_min:.0%}: {wins}W-{losses}L ({wr:.1f}% WR) ROI~{roi:+.1f}%")
        else:
            print(f"  Edge>={edge_min:.0%}: no bets")

    # Save results
    out_path = os.path.join(PROPS_DIR, "k_backtest_2025.json")
    os.makedirs(PROPS_DIR, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "n": n, "mae": mae, "rmse": rmse, "bias": bias, "correlation": corr,
            "results": results[:100],  # Save first 100 for inspection
        }, f, indent=2)
    print(f"\nSaved to {out_path}")


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Pitcher Strikeout Prop Model")
    parser.add_argument("--refresh", action="store_true", help="Refresh pitcher game logs")
    parser.add_argument("--no-refresh", action="store_true", help="Skip game log refresh")
    parser.add_argument("--pitcher", type=int, help="Single pitcher ID")
    parser.add_argument("--min-edge", type=float, default=MIN_EDGE_PCT, help="Minimum edge %%")
    parser.add_argument("--grade", action="store_true", help="Grade past K-prop bets")
    parser.add_argument("--status", action="store_true", help="Show K-prop ledger status")
    parser.add_argument("--no-save", action="store_true", help="Don't save predictions or log picks")
    parser.add_argument("--backtest", action="store_true", help="Run 2025 walk-forward backtest")
    args = parser.parse_args()

    if args.backtest:
        run_k_backtest()
        return

    if args.grade:
        grade_k_props()
        return

    if args.status:
        ledger = load_k_ledger()
        s = ledger["summary"]
        total = s["total_bets"]
        print(f"K-Prop Ledger: {total} bets, {s['graded']} graded")
        if s["graded"]:
            print(f"  Record: {s['wins']}W-{s['losses']}L")
            print(f"  PnL: ${s['total_pnl']:+.2f}")
            wagered = s["total_wagered"]
            if wagered:
                print(f"  ROI: {s['total_pnl']/wagered*100:+.1f}%")
        print(f"  Ungraded: {total - s['graded']}")
        return

    model = PitcherStrikeoutModel()

    refresh = not args.no_refresh
    results = model.predict_today(refresh=refresh)

    if results:
        output = format_results(results, min_edge=args.min_edge)
        print(output)

        # Extract picks - UNDER gets lower threshold (backtest: 3x more profitable)
        # OVER gets capped (game model lesson: extreme edges = model errors)
        picks = []
        for r in results:
            pred = r["prediction"]
            if pred["pitcher_name"] in PITCHER_BLACKLIST:
                continue
            for e in r["edges"]:
                side = e.get("side", "over")
                if DISABLE_OVER_BETS and side == "over":
                    continue
                if DISABLE_UNDER_BETS and side == "under":
                    continue
                min_thresh = MIN_EDGE_UNDER if side == "under" else args.min_edge
                if side == "over" and e["edge"] > MAX_EDGE_OVER:
                    continue  # skip overconfident OVER bets
                if side == "under" and e["edge"] > MAX_EDGE_UNDER:
                    continue  # skip overconfident UNDER bets (20%+ is 6W-8L, Apr 28)
                if e["edge"] >= min_thresh:
                    picks.append({
                        "pitcher": pred["pitcher_name"],
                        "team": r["team"],
                        "opponent": pred["opponent"],
                        "pick": e["label"],
                        "side": side,
                        "odds": e["fd_odds"],
                        "model_prob": e["model_prob"],
                        "fd_implied": e["fd_implied"],
                        "edge": e["edge"],
                        "expected_ks": pred["expected_ks"],
                    })

        if not args.no_save:
            save_predictions(results, picks, args.min_edge)
            log_k_prop_picks(picks)
    else:
        print("No results. Ensure today's pitchers are loaded (run mlb_data_pipeline.py).")


if __name__ == "__main__":
    main()

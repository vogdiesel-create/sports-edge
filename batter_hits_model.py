#!/usr/bin/env python3
"""
Batter Hits Prop Model - Sports Edge

Predicts expected hits per game for MLB batters using:
  - Batter's rolling batting average (regressed to league avg)
  - Expected plate appearances (~4 for most lineup spots)
  - Matchup adjustment (opposing pitcher's hits allowed rate)
  - Poisson distribution for P(hits >= N)

Compares model probabilities to FanDuel prop lines to find edges.

Backtest validation: run --backtest to test on 2025 data.

Usage:
    python3 batter_hits_model.py              # Today's predictions
    python3 batter_hits_model.py --backtest   # 2025 walk-forward backtest
    python3 batter_hits_model.py --grade      # Grade past bets
    python3 batter_hits_model.py --status     # Ledger status
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from scipy.stats import poisson

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SPORTS_EDGE_DB = os.path.join(DATA_DIR, "sports_edge.db")
GAME_LINES_DB = os.path.join(DATA_DIR, "game_lines.db")
PROPS_DIR = os.path.join(DATA_DIR, "hit_props")
LEDGER_PATH = os.path.join(DATA_DIR, "hit_prop_ledger.json")

MLB_API = "https://statsapi.mlb.com/api/v1"

# League averages
LEAGUE_AVG_BA = 0.245          # ~.245 batting average league-wide
LEAGUE_AVG_PA_PER_GAME = 4.0   # ~4 PA per game for typical starter
LEAGUE_AVG_HITS_PER_GAME = 0.98  # ~1 hit per game

# Regression: at REGRESSION_AB at-bats, weight is 50/50 actual vs league avg
REGRESSION_AB = 150

# Minimum edge to flag
MIN_EDGE_PCT = 5.0

# Betting
BANKROLL = 3000.0
KELLY_FRACTION = 0.25
MAX_BETS_PER_BATTER = 1  # Hits is binary-ish, 1 bet per batter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HIT-MODEL] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("batter_hits")


# ===========================================================================
# Prediction Model
# ===========================================================================

class BatterHitsModel:
    """Predicts expected hits for a batter in a given game."""

    def __init__(self):
        self.league_avg_ba = LEAGUE_AVG_BA

    def get_batter_stats(self, batter_id: int, before_date: str = None,
                         table: str = "batter_game_logs_2025") -> Optional[dict]:
        """Get batter's rolling stats from game logs."""
        if before_date is None:
            before_date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(SPORTS_EDGE_DB)
        rows = conn.execute(f"""
            SELECT hits, at_bats, plate_appearances, home_runs, total_bases
            FROM {table}
            WHERE batter_id = ? AND game_date < ?
            ORDER BY game_date
        """, (batter_id, before_date)).fetchall()
        conn.close()

        if not rows:
            return None

        total_h = sum(r[0] for r in rows)
        total_ab = sum(r[1] for r in rows)
        total_pa = sum(r[2] for r in rows)
        total_hr = sum(r[3] for r in rows)
        total_tb = sum(r[4] for r in rows)
        games = len(rows)

        ba = total_h / total_ab if total_ab > 0 else LEAGUE_AVG_BA
        avg_pa = total_pa / games if games > 0 else LEAGUE_AVG_PA_PER_GAME
        avg_hits = total_h / games if games > 0 else LEAGUE_AVG_HITS_PER_GAME

        return {
            "games": games,
            "total_hits": total_h,
            "total_ab": total_ab,
            "total_pa": total_pa,
            "batting_avg": round(ba, 3),
            "avg_pa": round(avg_pa, 2),
            "avg_hits": round(avg_hits, 2),
            "slg": round(total_tb / total_ab, 3) if total_ab > 0 else 0.400,
        }

    def regressed_ba(self, raw_ba: float, at_bats: int) -> float:
        """Regress batting average toward league average based on sample size."""
        weight = at_bats / (at_bats + REGRESSION_AB)
        return weight * raw_ba + (1 - weight) * LEAGUE_AVG_BA

    def predict_hits(self, batter_stats: dict, pa_estimate: float = None) -> dict:
        """
        Predict expected hits for a batter.

        Uses Poisson distribution with lambda = regressed_BA * expected_PA.
        """
        if batter_stats is None:
            return None

        raw_ba = batter_stats["batting_avg"]
        total_ab = batter_stats["total_ab"]
        avg_pa = batter_stats["avg_pa"]

        # Regress BA toward league avg
        reg_ba = self.regressed_ba(raw_ba, total_ab)

        # PA estimate (default to their average)
        if pa_estimate is None:
            pa_estimate = max(3.0, min(avg_pa, 5.5))

        # Expected hits = regressed BA * PA
        # Using AB not PA for hits calculation (hits/AB = BA)
        # Approximate: AB ~ PA * 0.88 (subtract walks, HBP, sac)
        expected_ab = pa_estimate * 0.88
        expected_hits = reg_ba * expected_ab

        # Poisson probabilities
        probs = {}
        for n in range(0, 6):
            # P(hits >= n) = 1 - P(hits <= n-1)
            if n == 0:
                probs[n] = 1.0
            else:
                probs[n] = 1.0 - poisson.cdf(n - 1, expected_hits)

        return {
            "raw_ba": round(raw_ba, 3),
            "regressed_ba": round(reg_ba, 3),
            "total_ab": total_ab,
            "games": batter_stats["games"],
            "pa_estimate": round(pa_estimate, 2),
            "expected_hits": round(expected_hits, 3),
            "probs": probs,
        }

    def get_fd_hit_props(self, batter_name: str) -> dict:
        """Get FanDuel hit prop lines for a batter."""
        conn = sqlite3.connect(SPORTS_EDGE_DB)

        # Look for "To Record A Hit", "To Record 2+ Hits", "To Record 3+ Hits"
        props = {}
        for threshold, market_pattern in [
            (1, "%To Record A Hit%"),
            (2, "%To Record 2+ Hits%"),
            (3, "%To Record 3+ Hits%"),
        ]:
            row = conn.execute("""
                SELECT over_odds, under_odds, collected_at
                FROM fd_prop_snapshots
                WHERE player LIKE ? AND market LIKE ?
                AND collected_at >= date('now', '-1 day')
                ORDER BY collected_at DESC LIMIT 1
            """, (f"%{batter_name}%", market_pattern)).fetchone()

            if row and row[0] is not None:
                props[threshold] = {
                    "over_odds": row[0],
                    "under_odds": row[1],
                }

        conn.close()
        return props

    @staticmethod
    def american_to_implied(odds: int) -> float:
        if odds is None:
            return 0.0
        if odds > 0:
            return 100.0 / (odds + 100.0)
        else:
            return abs(odds) / (abs(odds) + 100.0)

    def find_edges(self, prediction: dict, fd_props: dict) -> List[dict]:
        """Find edges between model and FanDuel lines."""
        edges = []
        if prediction is None:
            return edges

        for threshold, line_data in fd_props.items():
            model_over = prediction["probs"].get(threshold, 0.0)
            model_under = 1.0 - model_over

            # Check OVER
            over_odds = line_data.get("over_odds")
            if over_odds is not None:
                over_implied = self.american_to_implied(over_odds)
                over_edge = (model_over - over_implied) * 100
                edges.append({
                    "threshold": threshold,
                    "label": f"{threshold}+ Hits",
                    "side": "over",
                    "fd_odds": over_odds,
                    "fd_implied": round(over_implied * 100, 1),
                    "model_prob": round(model_over * 100, 1),
                    "edge": round(over_edge, 1),
                })

            # Check UNDER
            under_odds = line_data.get("under_odds")
            if under_odds is not None:
                under_implied = self.american_to_implied(under_odds)
                under_edge = (model_under - under_implied) * 100
                edges.append({
                    "threshold": threshold,
                    "label": f"Under {threshold} Hits",
                    "side": "under",
                    "fd_odds": under_odds,
                    "fd_implied": round(under_implied * 100, 1),
                    "model_prob": round(model_under * 100, 1),
                    "edge": round(under_edge, 1),
                })

        return edges


# ===========================================================================
# Backtest
# ===========================================================================

def run_hits_backtest(min_games: int = 10):
    """Walk-forward backtest of hits model on 2025 data."""
    conn = sqlite3.connect(SPORTS_EDGE_DB)

    rows = conn.execute("""
        SELECT batter_id, batter_name, game_date, opponent, hits, at_bats, plate_appearances
        FROM batter_game_logs_2025
        ORDER BY game_date
    """).fetchall()
    conn.close()

    if not rows:
        print("No 2025 batter data. Run the data fetch first.")
        return

    print(f"Backtesting {len(rows)} batter games from 2025...")

    batter_history = {}  # bid -> [(date, hits, ab, pa), ...]
    results = []

    for bid, name, date, opp, actual_hits, ab, pa in rows:
        history = batter_history.get(bid, [])

        if len(history) >= min_games:
            total_h = sum(h[1] for h in history)
            total_ab = sum(h[2] for h in history)
            total_pa = sum(h[3] for h in history)
            games = len(history)

            if total_ab > 0:
                raw_ba = total_h / total_ab
                weight = total_ab / (total_ab + REGRESSION_AB)
                reg_ba = weight * raw_ba + (1 - weight) * LEAGUE_AVG_BA

                avg_pa = total_pa / games
                pa_est = max(3.0, min(avg_pa, 5.5))
                expected_ab = pa_est * 0.88
                expected_hits = reg_ba * expected_ab

                results.append({
                    "expected": expected_hits,
                    "actual": actual_hits,
                    "games": games,
                    "total_ab": total_ab,
                })

        if bid not in batter_history:
            batter_history[bid] = []
        batter_history[bid].append((date, actual_hits, ab, pa))

    if not results:
        print("Not enough history for backtesting.")
        return

    n = len(results)
    mae = sum(abs(r["actual"] - r["expected"]) for r in results) / n
    bias = sum(r["actual"] - r["expected"] for r in results) / n

    exp_vals = [r["expected"] for r in results]
    act_vals = [r["actual"] for r in results]
    exp_mean = sum(exp_vals) / n
    act_mean = sum(act_vals) / n
    cov = sum((e - exp_mean) * (a - act_mean) for e, a in zip(exp_vals, act_vals)) / n
    std_e = (sum((e - exp_mean) ** 2 for e in exp_vals) / n) ** 0.5
    std_a = (sum((a - act_mean) ** 2 for a in act_vals) / n) ** 0.5
    corr = cov / (std_e * std_a) if std_e > 0 and std_a > 0 else 0

    print(f"\n{'='*60}")
    print(f"BATTER HITS MODEL BACKTEST (2025, {n} predictions)")
    print(f"{'='*60}")
    print(f"MAE:         {mae:.3f} hits")
    print(f"Bias:        {bias:+.3f} hits")
    print(f"Correlation: {corr:.3f}")
    print(f"Avg Expected: {exp_mean:.3f}")
    print(f"Avg Actual:   {act_mean:.3f}")

    # Simulate betting
    print(f"\nSimulated hit-prop betting (model vs base-rate 'market'):")

    # Compute running base rate
    all_prior = []
    batter_hist2 = {}
    for bid, name, date, opp, actual_hits, ab, pa in rows if rows else []:
        pass  # Already processed above

    # Use overall league avg as market proxy
    for side_label, side_name in [("OVER", "over"), ("UNDER", "under")]:
        print(f"\n  {side_label}:")
        for edge_min in [0.03, 0.05, 0.07, 0.10]:
            wins = losses = 0
            for r in results:
                expected = r["expected"]
                actual = r["actual"]

                for threshold in [1, 2, 3]:
                    model_over = 1.0 - poisson.cdf(threshold - 1, expected)
                    market_over = 1.0 - poisson.cdf(threshold - 1, LEAGUE_AVG_HITS_PER_GAME)

                    if side_name == "over":
                        edge = model_over - market_over
                        won = actual >= threshold
                    else:
                        edge = (1 - model_over) - (1 - market_over)
                        won = actual < threshold

                    if edge >= edge_min:
                        if won:
                            wins += 1
                        else:
                            losses += 1

            total = wins + losses
            if total:
                wr = wins / total * 100
                pnl_per = wins * (100 / 115) - losses
                roi = pnl_per / total * 100
                print(f"    Edge>={edge_min:.0%}: {wins}W-{losses}L ({wr:.1f}%) ROI~{roi:+.1f}% (@-115)")

    # Calibration check
    print(f"\nCalibration (P(1+ hit)):")
    buckets = {}
    for r in results:
        model_p = 1.0 - poisson.cdf(0, r["expected"])
        bucket = round(model_p * 10) / 10
        if bucket not in buckets:
            buckets[bucket] = {"n": 0, "hits": 0}
        buckets[bucket]["n"] += 1
        if r["actual"] >= 1:
            buckets[bucket]["hits"] += 1

    for b in sorted(buckets.keys()):
        v = buckets[b]
        actual = v["hits"] / v["n"] if v["n"] else 0
        print(f"  Pred {b:.1f}: Actual {actual:.3f} (n={v['n']})")

    # Save
    os.makedirs(PROPS_DIR, exist_ok=True)
    out_path = os.path.join(PROPS_DIR, "hits_backtest_2025.json")
    with open(out_path, "w") as f:
        json.dump({"n": n, "mae": mae, "bias": bias, "correlation": corr}, f, indent=2)
    print(f"\nSaved to {out_path}")


# ===========================================================================
# Today's Predictions
# ===========================================================================

def predict_today(min_edge: float = MIN_EDGE_PCT) -> tuple:
    """Run predictions for today's batters. Returns (results, picks)."""
    model = BatterHitsModel()
    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's lineups from FD prop snapshots (batters with props = in lineup)
    conn = sqlite3.connect(SPORTS_EDGE_DB)
    batter_rows = conn.execute("""
        SELECT DISTINCT player
        FROM fd_prop_snapshots
        WHERE market LIKE '%To Record A Hit%'
        AND collected_at >= date('now', '-1 day')
    """).fetchall()
    conn.close()

    if not batter_rows:
        print("No batter props found. Data may not be collected yet.")
        return [], []

    batter_names = [r[0] for r in batter_rows]
    log.info(f"Found {len(batter_names)} batters with FD hit props")

    results = []
    picks = []

    for name in batter_names:
        # Look up batter ID from 2026 game logs or FD data
        conn = sqlite3.connect(SPORTS_EDGE_DB)
        bid_row = conn.execute("""
            SELECT batter_id FROM batter_game_logs_2025
            WHERE batter_name = ? LIMIT 1
        """, (name,)).fetchone()
        conn.close()

        if not bid_row:
            continue

        bid = bid_row[0]
        stats = model.get_batter_stats(bid, before_date=today)
        if not stats or stats["games"] < 5:
            continue

        pred = model.predict_hits(stats)
        if pred is None:
            continue

        fd_props = model.get_fd_hit_props(name)
        edges = model.find_edges(pred, fd_props)

        qualifying = [e for e in edges if e["edge"] >= min_edge]
        if qualifying:
            results.append({
                "batter": name,
                "prediction": pred,
                "fd_props": fd_props,
                "edges": edges,
            })
            for e in qualifying:
                picks.append({
                    "batter": name,
                    "pick": e["label"],
                    "side": e["side"],
                    "odds": e["fd_odds"],
                    "model_prob": e["model_prob"],
                    "fd_implied": e["fd_implied"],
                    "edge": e["edge"],
                    "expected_hits": pred["expected_hits"],
                    "threshold": e["threshold"],
                })

    # Sort by edge
    picks.sort(key=lambda x: x["edge"], reverse=True)
    return results, picks


# ===========================================================================
# Ledger
# ===========================================================================

def load_ledger() -> dict:
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH) as f:
            return json.load(f)
    return {
        "bankroll": BANKROLL, "started": datetime.now().isoformat(),
        "bets": [],
        "summary": {"total_bets": 0, "graded": 0, "wins": 0, "losses": 0,
                     "pushes": 0, "total_wagered": 0.0, "total_pnl": 0.0},
    }


def save_ledger(ledger: dict):
    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)


def log_hit_picks(picks: List[dict]):
    """Log qualifying hit prop picks to ledger."""
    if not picks:
        return 0

    # Limit per batter
    sorted_picks = sorted(picks, key=lambda x: x["edge"], reverse=True)
    batter_counts = {}
    filtered = []
    for p in sorted_picks:
        name = p["batter"]
        batter_counts[name] = batter_counts.get(name, 0) + 1
        if batter_counts[name] <= MAX_BETS_PER_BATTER:
            filtered.append(p)

    ledger = load_ledger()
    existing = {b["pick_id"] for b in ledger["bets"]}
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    new_count = 0
    bankroll = ledger["bankroll"]

    for p in filtered:
        pick_id = f"HIT|{today}|{p['batter']}|{p['pick']}"
        if pick_id in existing:
            continue

        model_prob = p["model_prob"] / 100.0
        odds = p["odds"]
        b = odds / 100.0 if odds > 0 else 100.0 / abs(odds)

        kelly = (model_prob * b - (1 - model_prob)) / b
        kelly = max(kelly, 0)
        wager_pct = kelly * KELLY_FRACTION
        wager = round(bankroll * min(wager_pct, 0.03), 2)
        if wager < 5:
            wager = 5.0

        profit = round(wager * odds / 100, 2) if odds > 0 else round(wager * 100 / abs(odds), 2)

        bet = {
            "pick_id": pick_id,
            "logged_at": now.isoformat(),
            "date": today,
            "sport": "MLB",
            "market": "batter_hits",
            "batter": p["batter"],
            "pick": p["pick"],
            "side": p["side"],
            "threshold": p["threshold"],
            "odds": odds,
            "model_prob": round(model_prob, 4),
            "fd_implied": round(p["fd_implied"] / 100.0, 4),
            "edge": round(p["edge"] / 100.0, 4),
            "expected_hits": p["expected_hits"],
            "wager": wager,
            "profit_if_win": profit,
            "result": None,
            "actual_hits": None,
            "graded_at": None,
        }

        ledger["bets"].append(bet)
        ledger["summary"]["total_bets"] += 1
        ledger["summary"]["total_wagered"] += wager
        existing.add(pick_id)
        new_count += 1

    save_ledger(ledger)
    log.info(f"Logged {new_count} hit-prop picks ({ledger['summary']['total_bets']} total)")
    return new_count


def grade_hit_props():
    """Grade hit prop bets using MLB box scores."""
    ledger = load_ledger()
    ungraded = [b for b in ledger["bets"] if b["result"] is None]
    if not ungraded:
        log.info("No ungraded hit-prop bets.")
        return

    log.info(f"Grading {len(ungraded)} hit-prop bets...")
    graded = 0

    for bet in ungraded:
        date = bet.get("date")
        batter = bet.get("batter")
        threshold = bet.get("threshold")
        side = bet.get("side", "over")
        if not date or not batter or threshold is None:
            continue

        url = f"{MLB_API}/schedule?date={date}&sportId=1&hydrate=boxscore"
        try:
            resp = requests.get(url, timeout=15)
            data = resp.json()
        except Exception as e:
            log.warning(f"  Failed to fetch scores for {date}: {e}")
            continue

        actual_hits = None
        for d in data.get("dates", []):
            for g in d.get("games", []):
                state = g.get("status", {}).get("abstractGameState", "")
                if state != "Final":
                    continue
                box = g.get("boxscore", {})
                if not box:
                    continue
                for team_side in ("away", "home"):
                    players = box.get("teams", {}).get(team_side, {}).get("players", {})
                    for pid, pdata in players.items():
                        pname = pdata.get("person", {}).get("fullName", "")
                        if pname.lower() == batter.lower():
                            stats = pdata.get("stats", {}).get("batting", {})
                            actual_hits = stats.get("hits", 0)
                            break
                    if actual_hits is not None:
                        break
                if actual_hits is not None:
                    break
            if actual_hits is not None:
                break

        if actual_hits is not None:
            bet["actual_hits"] = actual_hits
            if side == "under":
                won = actual_hits < threshold
            else:
                won = actual_hits >= threshold

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
            log.info(f"  {batter}: {actual_hits} hits vs {threshold} ({side}) -> {bet['result']}")

    save_ledger(ledger)
    s = ledger["summary"]
    log.info(f"Graded {graded}. Record: {s['wins']}W-{s['losses']}L, PnL: ${s['total_pnl']:+.2f}")


# ===========================================================================
# Display
# ===========================================================================

def format_results(results: List[dict], picks: List[dict], min_edge: float) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("BATTER HITS PROP MODEL - EDGE DETECTION")
    lines.append("=" * 70)

    for r in results:
        pred = r["prediction"]
        name = r["batter"]
        lines.append(f"\n--- {name} ---")
        lines.append(f"  BA: {pred['raw_ba']:.3f} raw -> {pred['regressed_ba']:.3f} regressed "
                      f"({pred['total_ab']} AB, {pred['games']} games)")
        lines.append(f"  Expected hits: {pred['expected_hits']:.3f} | PA est: {pred['pa_estimate']}")
        lines.append(f"  P(1+ hit): {pred['probs'].get(1, 0)*100:.1f}% | "
                      f"P(2+ hits): {pred['probs'].get(2, 0)*100:.1f}% | "
                      f"P(3+ hits): {pred['probs'].get(3, 0)*100:.1f}%")

        qualifying = [e for e in r["edges"] if e["edge"] >= min_edge]
        for e in qualifying:
            lines.append(f"  >> {e['label']}: model {e['model_prob']:.1f}% vs FD {e['fd_implied']:.1f}% "
                          f"| EDGE: {e['edge']:+.1f}% | odds: {e['fd_odds']:+d}")

    if picks:
        lines.append(f"\n{'='*70}")
        lines.append(f"TOP PICKS (edge >= {min_edge}%)")
        lines.append("=" * 70)
        for p in picks[:20]:
            lines.append(f"  {p['batter']:<25} {p['pick']:<15} "
                          f"odds:{p['odds']:>+5} | edge:{p['edge']:>+.1f}%")
    else:
        lines.append("\nNo picks above minimum edge threshold.")

    return "\n".join(lines)


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Batter Hits Prop Model")
    parser.add_argument("--backtest", action="store_true", help="Run 2025 backtest")
    parser.add_argument("--grade", action="store_true", help="Grade past bets")
    parser.add_argument("--status", action="store_true", help="Ledger status")
    parser.add_argument("--min-edge", type=float, default=MIN_EDGE_PCT, help="Min edge %%")
    parser.add_argument("--no-save", action="store_true", help="Don't save/log picks")
    args = parser.parse_args()

    if args.backtest:
        run_hits_backtest()
        return

    if args.grade:
        grade_hit_props()
        return

    if args.status:
        ledger = load_ledger()
        s = ledger["summary"]
        print(f"Hit-Prop Ledger: {s['total_bets']} bets, {s['graded']} graded")
        if s["graded"]:
            print(f"  Record: {s['wins']}W-{s['losses']}L")
            print(f"  PnL: ${s['total_pnl']:+.2f}")
            if s["total_wagered"]:
                print(f"  ROI: {s['total_pnl']/s['total_wagered']*100:+.1f}%")
        print(f"  Ungraded: {s['total_bets'] - s['graded']}")
        return

    results, picks = predict_today(min_edge=args.min_edge)

    if results:
        output = format_results(results, picks, args.min_edge)
        print(output)

        if not args.no_save and picks:
            # Save predictions
            os.makedirs(PROPS_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            path = os.path.join(PROPS_DIR, f"hit_props_{ts}.json")
            with open(path, "w") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "picks": picks}, f, indent=2, default=str)
            with open(os.path.join(PROPS_DIR, "latest.json"), "w") as f:
                json.dump({"timestamp": datetime.now().isoformat(), "picks": picks}, f, indent=2, default=str)
            log.info(f"Saved {len(picks)} picks to {path}")

            log_hit_picks(picks)
    else:
        print("No results. Ensure FD prop data is collected (run data_collector.py).")


if __name__ == "__main__":
    main()

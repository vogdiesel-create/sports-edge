#!/usr/bin/env python3
"""
Track and grade our batter + K prop model picks.

Logs picks with timestamps, then grades against actual MLB box scores.
Tracks win rate, ROI, and calibration per market type.

Usage:
    python3 prop_pick_tracker.py log       # Log today's prop picks
    python3 prop_pick_tracker.py grade     # Grade completed picks
    python3 prop_pick_tracker.py summary   # Show P&L summary
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PROP_PICKS_LOG = os.path.join(DATA_DIR, "model_prop_picks.json")


def load_log():
    if os.path.exists(PROP_PICKS_LOG):
        with open(PROP_PICKS_LOG) as f:
            return json.load(f)
    return {"picks": [], "summary": {}}


def save_log(data):
    with open(PROP_PICKS_LOG, "w") as f:
        json.dump(data, f, indent=2, default=str)


def american_to_decimal(odds):
    if odds > 0:
        return 1 + odds / 100
    else:
        return 1 + 100 / abs(odds)


def log_picks():
    """Log today's batter and K prop picks."""
    from edge_detector import generate_picks
    _, _, prop_picks = generate_picks()

    if not prop_picks:
        print("No prop picks to log.")
        return

    log = load_log()
    today = datetime.now().strftime("%Y-%m-%d")

    # Deduplicate against existing picks
    existing = set()
    for p in log["picks"]:
        existing.add((p.get("player", ""), p.get("market", ""),
                      p.get("game_date", "")))

    new_count = 0
    for pp in prop_picks:
        key = (pp.get("player", ""), pp.get("side", ""), today)
        if key in existing:
            continue
        existing.add(key)

        log["picks"].append({
            "game_date": today,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "source": pp.get("source", "unknown"),
            "sport": pp.get("sport", "MLB"),
            "player": pp.get("player", ""),
            "market": pp.get("side", ""),  # e.g., "Aaron Judge To Record An RBI"
            "game": pp.get("game", ""),
            "odds": pp.get("odds"),
            "edge": pp.get("edge", 0),
            "model_prob": pp.get("model_prob", 0),
            "graded": False,
            "won": None,
            "actual": None,
        })
        new_count += 1

    save_log(log)
    print(f"Logged {new_count} new prop picks ({len(log['picks'])} total)")


def get_mlb_player_stats(date_str):
    """Get MLB player box scores for a date."""
    url = f"https://statsapi.mlb.com/api/v1/schedule?date={date_str}&sportId=1"
    resp = requests.get(url, timeout=10)
    dates = resp.json().get("dates", [])
    games = dates[0].get("games", []) if dates else []

    player_stats = {}
    for game in games:
        status = game.get("status", {}).get("detailedState", "")
        if status not in ("Final", "Game Over", "Completed Early"):
            continue

        game_pk = game.get("gamePk")
        try:
            box_resp = requests.get(
                f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore",
                timeout=10)
            box = box_resp.json()
        except Exception:
            continue

        for side in ["away", "home"]:
            players = box.get("teams", {}).get(side, {}).get("players", {})
            for _, p_data in players.items():
                name = p_data.get("person", {}).get("fullName", "")
                if not name:
                    continue

                batting = p_data.get("stats", {}).get("batting", {})
                pitching = p_data.get("stats", {}).get("pitching", {})

                player_stats[name.lower()] = {
                    "name": name,
                    "hits": batting.get("hits", 0),
                    "home_runs": batting.get("homeRuns", 0),
                    "rbi": batting.get("rbi", 0),
                    "runs": batting.get("runs", 0),
                    "total_bases": batting.get("totalBases", 0),
                    "stolen_bases": batting.get("stolenBases", 0),
                    "at_bats": batting.get("atBats", 0),
                    "strikeouts_pitched": pitching.get("strikeOuts", 0),
                    "innings_pitched": pitching.get("inningsPitched", "0"),
                    "hits_allowed": pitching.get("hits", 0),
                    "earned_runs": pitching.get("earnedRuns", 0),
                }

    return player_stats


def grade_pick(pick, player_stats):
    """Grade a single pick. Returns (won, actual) or None if can't grade."""
    player = pick.get("player", "")
    market = pick.get("market", "")

    # Find player stats
    stats = player_stats.get(player.lower())
    if not stats:
        # Try fuzzy matching by last name
        last = player.split()[-1].lower() if player else ""
        for key, val in player_stats.items():
            if last and last in key:
                stats = val
                break
    if not stats:
        return None

    # Parse market string to determine what to check
    market_lower = market.lower()

    # Batter prop markets
    if "home run" in market_lower:
        actual = stats["home_runs"]
        if "2+" in market_lower:
            return actual >= 2, actual
        return actual >= 1, actual

    if "hit" in market_lower and "record" in market_lower:
        actual = stats["hits"]
        if "3+" in market_lower:
            return actual >= 3, actual
        if "2+" in market_lower:
            return actual >= 2, actual
        return actual >= 1, actual

    if "total bases" in market_lower or "total base" in market_lower:
        actual = stats["total_bases"]
        m = re.search(r"(\d+)\+", market_lower)
        if m:
            return actual >= int(m.group(1)), actual
        return actual >= 2, actual

    if "rbi" in market_lower:
        actual = stats["rbi"]
        if "2+" in market_lower:
            return actual >= 2, actual
        return actual >= 1, actual

    if "run" in market_lower and "record" in market_lower:
        actual = stats["runs"]
        if "2+" in market_lower:
            return actual >= 2, actual
        return actual >= 1, actual

    if "stolen base" in market_lower:
        actual = stats["stolen_bases"]
        if "2+" in market_lower:
            return actual >= 2, actual
        return actual >= 1, actual

    # K prop picks (pitcher strikeouts)
    if "strikeout" in market_lower or " k " in market_lower or " ks" in market_lower:
        actual = stats["strikeouts_pitched"]
        # Parse line from market string like "UNDER 5.5 Ks"
        m = re.search(r"(over|under)\s+(\d+\.?\d*)", market_lower)
        if m:
            direction = m.group(1)
            line = float(m.group(2))
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual

    return None


def grade_picks(date_str=None):
    """Grade ungraded picks."""
    log = load_log()
    if not log["picks"]:
        print("No picks to grade.")
        return

    # Find dates with ungraded picks
    dates_needed = set()
    for p in log["picks"]:
        if not p.get("graded"):
            dates_needed.add(p["game_date"])

    if not dates_needed:
        print("All picks already graded.")
        return

    if date_str:
        dates_needed = {date_str}

    graded = 0
    wins = 0
    total_pnl = 0

    for d in sorted(dates_needed):
        print(f"Fetching box scores for {d}...")
        try:
            stats = get_mlb_player_stats(d)
        except Exception as e:
            print(f"  Error: {e}")
            continue

        if not stats:
            print(f"  No completed games found for {d}")
            continue

        print(f"  {len(stats)} players found")

        for pick in log["picks"]:
            if pick.get("graded") or pick["game_date"] != d:
                continue

            result = grade_pick(pick, stats)
            if result is None:
                continue

            won, actual = result
            odds = pick.get("odds", 100)
            dec = american_to_decimal(odds) if odds else 2.0
            stake = 20  # $20 unit
            pnl = stake * (dec - 1) if won else -stake

            pick["graded"] = True
            pick["won"] = won
            pick["actual"] = actual
            pick["pnl"] = round(pnl, 2)

            graded += 1
            if won:
                wins += 1
            total_pnl += pnl

    save_log(log)

    if graded > 0:
        print(f"\nGraded {graded} picks: {wins}W-{graded-wins}L")
        print(f"P&L: ${total_pnl:+.2f} | ROI: {total_pnl/(graded*20)*100:+.1f}%")
    else:
        print("No picks could be graded (games not yet complete).")


def show_summary():
    """Show prop pick tracking summary."""
    log = load_log()
    graded = [p for p in log["picks"] if p.get("graded")]

    if not graded:
        print("No graded prop picks yet.")
        ungraded = [p for p in log["picks"] if not p.get("graded")]
        if ungraded:
            print(f"({len(ungraded)} picks pending)")
        return

    total = len(graded)
    wins = sum(1 for p in graded if p.get("won"))
    total_pnl = sum(p.get("pnl", 0) for p in graded)

    print(f"\n{'='*60}")
    print(f"  MODEL PROP PICKS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total: {total} | W: {wins} L: {total-wins} "
          f"({wins/total*100:.1f}% WR)")
    print(f"  P&L: ${total_pnl:+.2f} | ROI: {total_pnl/(total*20)*100:+.1f}%")

    # By source
    by_source = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0})
    for p in graded:
        src = p.get("source", "unknown")
        if p["won"]:
            by_source[src]["w"] += 1
        else:
            by_source[src]["l"] += 1
        by_source[src]["pnl"] += p.get("pnl", 0)

    print(f"\n  By Source:")
    for src, s in by_source.items():
        t = s["w"] + s["l"]
        wr = s["w"] / t * 100 if t > 0 else 0
        print(f"    {src:<20} {t:>3} bets  {wr:.0f}% WR  ${s['pnl']:+.2f}")

    # By market type
    by_market = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0})
    for p in graded:
        market = p.get("market", "unknown")
        # Simplify market name
        m = market.lower()
        if "home run" in m:
            mtype = "HR"
        elif "hit" in m:
            mtype = "Hits"
        elif "total base" in m:
            mtype = "TB"
        elif "rbi" in m:
            mtype = "RBI"
        elif "run" in m and "record" in m:
            mtype = "Runs"
        elif "stolen" in m:
            mtype = "SB"
        elif "strikeout" in m or "k " in m.lower():
            mtype = "K"
        else:
            mtype = "Other"

        if p["won"]:
            by_market[mtype]["w"] += 1
        else:
            by_market[mtype]["l"] += 1
        by_market[mtype]["pnl"] += p.get("pnl", 0)

    print(f"\n  By Market:")
    for mtype, s in sorted(by_market.items()):
        t = s["w"] + s["l"]
        wr = s["w"] / t * 100 if t > 0 else 0
        print(f"    {mtype:<10} {t:>3} bets  {wr:.0f}% WR  ${s['pnl']:+.2f}")

    # Calibration: model_prob vs actual win rate
    print(f"\n  Calibration:")
    bins = [(0.05, 0.15), (0.15, 0.25), (0.25, 0.40), (0.40, 0.60), (0.60, 1.0)]
    for lo, hi in bins:
        in_bin = [p for p in graded if lo <= p.get("model_prob", 0) < hi]
        if len(in_bin) < 5:
            continue
        avg_prob = sum(p.get("model_prob", 0) for p in in_bin) / len(in_bin)
        win_rate = sum(1 for p in in_bin if p["won"]) / len(in_bin)
        print(f"    Pred {lo:.0%}-{hi:.0%}: {len(in_bin):>3} picks, "
              f"avg pred={avg_prob:.1%}, actual={win_rate:.1%}, "
              f"diff={win_rate-avg_prob:+.1%}")

    # Recent results
    recent = graded[-15:]
    if recent:
        print(f"\n  Recent Results:")
        for p in recent:
            status = "W" if p["won"] else "L"
            print(f"    [{status}] {p['player']:<20} {p.get('market',''):<35} "
                  f"actual={p.get('actual','-')} edge={p.get('edge',0)*100:+.1f}% "
                  f"${p.get('pnl',0):+.2f}")

    ungraded = [p for p in log["picks"] if not p.get("graded")]
    if ungraded:
        print(f"\n  Pending: {len(ungraded)} ungraded picks")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        date = sys.argv[2] if len(sys.argv) > 2 else None
        if cmd == "log":
            log_picks()
        elif cmd == "grade":
            grade_picks(date)
        elif cmd == "summary":
            show_summary()
    else:
        log_picks()
        grade_picks()
        show_summary()

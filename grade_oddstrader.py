#!/usr/bin/env python3
"""
Grade OddsTrader simulation ledger picks against MLB box scores.

Usage:
    python3 grade_oddstrader.py              # Grade all ungraded
    python3 grade_oddstrader.py summary      # Show P&L summary
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SIM_LEDGER = os.path.join(DATA_DIR, "oddstrader_sim_ledger.json")
OLD_LEDGER = os.path.join(DATA_DIR, "prop_ledger.json")

# Reuse the MLB stats fetcher
from prop_pick_tracker import get_mlb_player_stats


def american_to_decimal(odds_str):
    """Convert American odds string to decimal."""
    try:
        odds = int(odds_str.replace("+", ""))
    except (ValueError, AttributeError):
        return 2.0
    if odds > 0:
        return 1 + odds / 100
    else:
        return 1 + 100 / abs(odds)


def parse_line(line_str):
    """Parse OddsTrader line format like 'u4½', 'o5½', 'u1½'."""
    if not line_str:
        return None, None
    line_str = str(line_str).strip().lower()
    direction = None
    if line_str.startswith("u"):
        direction = "under"
        line_str = line_str[1:]
    elif line_str.startswith("o"):
        direction = "over"
        line_str = line_str[1:]
    # Handle ½ character
    line_str = line_str.replace("½", ".5")
    try:
        return direction, float(line_str)
    except ValueError:
        return direction, None


def grade_bet(bet, player_stats):
    """Grade a single OddsTrader bet. Returns (won, actual) or None."""
    player = bet.get("player", "")
    market = bet.get("market", "")
    side = bet.get("side", "")
    line_str = bet.get("line", "")

    # Find player (normalize accents for matching)
    def normalize(s):
        return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

    player_norm = normalize(player)
    stats = player_stats.get(player.lower()) or player_stats.get(player_norm)
    if not stats:
        last = player.split()[-1].lower() if player else ""
        last_norm = normalize(last)
        for key, val in player_stats.items():
            key_norm = normalize(key)
            if (last and last in key) or (last_norm and last_norm in key_norm):
                stats = val
                break
    if not stats:
        return None

    market_lower = market.lower()
    direction, line = parse_line(line_str)

    # Total Strikeouts (pitcher)
    if "strikeout" in market_lower:
        actual = stats["strikeouts_pitched"]
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        return None

    # Total Pitching Hits Allowed
    if "hits allowed" in market_lower or "pitching hits" in market_lower:
        actual = stats.get("hits_allowed", 0)
        if actual == 0 and stats.get("innings_pitched", "0") == "0":
            return None  # Player didn't pitch
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        return None

    # Total Bases (batter)
    if "total bases" in market_lower or "total base" in market_lower:
        if stats.get("at_bats", 0) == 0:
            return None  # Player didn't bat (DNP/bench) - can't grade
        actual = stats["total_bases"]
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        m = re.search(r"(\d+)\+", market_lower)
        if m:
            return actual >= int(m.group(1)), actual
        return actual >= 2, actual

    # Player to hit a RBI
    if "rbi" in market_lower:
        actual = stats["rbi"]
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        return actual >= 1, actual

    # Total Hits (batter)
    if "total hits" in market_lower or ("hit" in market_lower and "rbi" not in market_lower):
        actual = stats["hits"]
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        return actual >= 1, actual

    # Total Earned Runs (pitcher)
    if "earned run" in market_lower:
        actual = stats.get("earned_runs", 0)
        if actual == 0 and stats.get("innings_pitched", "0") == "0":
            return None  # Player didn't pitch
        if direction and line is not None:
            if direction == "under":
                return actual < line, actual
            else:
                return actual > line, actual
        return None

    return None


def grade_all():
    """Grade ungraded picks in the sim ledger."""
    if not os.path.exists(SIM_LEDGER):
        print("No simulation ledger found. Run oddstrader_scraper.py first.")
        return

    with open(SIM_LEDGER) as f:
        ledger = json.load(f)

    ungraded = [b for b in ledger["bets"] if not b.get("graded")]
    if not ungraded:
        print("All picks already graded.")
        return

    dates_needed = set()
    for b in ungraded:
        d = b.get("date", "")[:10]
        if d:
            dates_needed.add(d)

    graded_count = 0
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
            print(f"  No completed games for {d}")
            continue

        for bet in ledger["bets"]:
            if bet.get("graded") or bet.get("date", "")[:10] != d:
                continue

            result = grade_bet(bet, stats)
            if result is None:
                continue

            won, actual = result
            dec = american_to_decimal(bet.get("odds", "100"))
            wager = bet.get("wager", 20)
            pnl = wager * (dec - 1) if won else -wager

            bet["graded"] = True
            bet["won"] = won
            bet["actual"] = actual
            bet["pnl"] = round(pnl, 2)

            graded_count += 1
            if won:
                wins += 1
            total_pnl += pnl

    # Recalculate bankroll from all graded bets (prevents drift from manual corrections)
    all_pnl = sum(b.get("pnl", 0) for b in ledger["bets"] if b.get("graded"))
    ledger["bankroll"] = 5000 + all_pnl

    with open(SIM_LEDGER, "w") as f:
        json.dump(ledger, f, indent=2)

    if graded_count:
        print(f"\nGraded {graded_count}: {wins}W-{graded_count-wins}L")
        print(f"P&L: ${total_pnl:+.2f}")
        print(f"Bankroll: ${ledger['bankroll']:.2f}")
    else:
        print("No picks could be graded yet.")


def show_summary():
    """Show P&L summary by market."""
    if not os.path.exists(SIM_LEDGER):
        print("No simulation ledger found.")
        return

    with open(SIM_LEDGER) as f:
        ledger = json.load(f)

    bets = ledger["bets"]
    graded = [b for b in bets if b.get("graded")]
    ungraded = [b for b in bets if not b.get("graded")]

    print(f"\n{'='*65}")
    print(f"  ODDSTRADER SIMULATION LEDGER")
    print(f"{'='*65}")
    print(f"  Bankroll: ${ledger['bankroll']:.2f}")
    print(f"  Total bets: {len(bets)} ({len(graded)} graded, {len(ungraded)} pending)")

    if not graded:
        return

    total_wagered = sum(b.get("wager", 20) for b in graded)
    total_pnl = sum(b.get("pnl", 0) for b in graded)
    total_won = sum(1 for b in graded if b.get("won"))

    print(f"  Record: {total_won}W-{len(graded)-total_won}L ({total_won/len(graded)*100:.1f}% WR)")
    print(f"  P&L: ${total_pnl:+.2f} | Wagered: ${total_wagered:.2f} | ROI: {total_pnl/total_wagered*100:+.1f}%")

    # By market
    by_market = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0, "wagered": 0})
    for b in graded:
        m = b.get("market", "unknown")
        by_market[m]["wagered"] += b.get("wager", 20)
        by_market[m]["pnl"] += b.get("pnl", 0)
        if b.get("won"):
            by_market[m]["w"] += 1
        else:
            by_market[m]["l"] += 1

    print(f"\n  {'Market':<35} {'W':>4} {'L':>4} {'WR':>6} {'P&L':>9} {'ROI':>7}")
    print(f"  {'-'*65}")
    for m, d in sorted(by_market.items(), key=lambda x: -x[1]["pnl"]):
        total = d["w"] + d["l"]
        wr = d["w"] / total * 100 if total > 0 else 0
        roi = d["pnl"] / d["wagered"] * 100 if d["wagered"] > 0 else 0
        print(f"  {m:<35} {d['w']:>4} {d['l']:>4} {wr:>5.1f}% ${d['pnl']:>+8.2f} {roi:>+6.1f}%")

    # By tier
    print(f"\n  By Tier:")
    by_tier = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0, "wagered": 0})
    for b in graded:
        t = b.get("tier", "?")
        by_tier[t]["wagered"] += b.get("wager", 20)
        by_tier[t]["pnl"] += b.get("pnl", 0)
        if b.get("won"):
            by_tier[t]["w"] += 1
        else:
            by_tier[t]["l"] += 1

    for t in sorted(by_tier):
        d = by_tier[t]
        total = d["w"] + d["l"]
        wr = d["w"] / total * 100 if total > 0 else 0
        roi = d["pnl"] / d["wagered"] * 100 if d["wagered"] > 0 else 0
        print(f"    Tier {t}: {d['w']}W-{d['l']}L ({wr:.1f}%) P&L: ${d['pnl']:+.2f} ROI: {roi:+.1f}%")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_summary()
    else:
        grade_all()
        print()
        show_summary()

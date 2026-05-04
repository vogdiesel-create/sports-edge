#!/usr/bin/env python3
"""
Sports Edge - Daily Report Generator

Produces a clean summary of today's opportunities and yesterday's results.
Designed for quick mobile reading.
"""

import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def generate_report():
    now = datetime.now(timezone.utc)

    # Load latest scan
    scan_path = os.path.join(DATA_DIR, "unified_scan.json")
    if not os.path.exists(scan_path):
        return "No scan data available. Run smart_scanner.py first."

    with open(scan_path) as f:
        scan = json.load(f)

    lines = []
    lines.append(f"SPORTS EDGE DAILY REPORT")
    lines.append(f"{now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 50)

    # Backtest results
    bt = scan.get("backtest")
    if bt:
        lines.append("")
        lines.append("YESTERDAY'S RESULTS")
        lines.append(f"  Bets: {bt['bets']} | WR: {bt['win_rate']}% | P&L: ${bt['pnl']:+.2f} | ROI: {bt['roi']:+.1f}%")

    # Game line opportunities
    gl = scan.get("game_lines", {})
    lines.append("")
    lines.append(f"GAME LINE OPPORTUNITIES ({gl.get('filtered', 0)} after filters)")
    if gl.get("rejected"):
        lines.append(f"  Rejected: {gl['rejected']}")

    # Top picks
    picks = scan.get("picks", [])
    if picks:
        lines.append("")
        lines.append("TOP PICKS")
        for i, p in enumerate(picks, 1):
            tier = f"[{p.get('tier', '?')}]" if 'tier' in p else ""
            conf = p.get("confidence", "")
            lines.append(f"")
            lines.append(f"  {i}. {tier}[{conf}] {p.get('sport', '')} - {p.get('game', '')}")
            if "player" in p:
                lines.append(f"     Player: {p['player']}")
            lines.append(f"     {p['bet']}")
            if "odds" in p:
                lines.append(f"     Odds: {p['odds']} | Edge: {p['edge']} | EV: {p.get('ev', 'N/A')}")
            else:
                lines.append(f"     Edge: {p['edge']}")
    else:
        lines.append("")
        lines.append("No actionable picks right now.")

    # FD props
    pp = scan.get("player_props")
    if pp:
        lines.append("")
        lines.append(f"FANDUEL PROPS: {pp.get('props_count', 0)} tracked | {pp.get('correlation_alerts', 0)} arb alerts")

    # Strategy notes
    lines.append("")
    lines.append("STRATEGY RULES (from backtest)")
    lines.append("  Game Lines: 3-6% edge, exclude bodog, prefer unibet/sportsbetting")
    lines.append("  Props: Rebounds market strongest (+42.7% ROI)")
    lines.append("  Props: 8+ confirming books = 69% WR, +47.6% ROI")
    lines.append("  Sizing: Quarter Kelly, max 2% bankroll")

    report = "\n".join(lines)
    print(report)

    # Save
    report_path = os.path.join(DATA_DIR, f"report_{now.strftime('%Y%m%d')}.txt")
    with open(report_path, "w") as f:
        f.write(report)

    return report


if __name__ == "__main__":
    generate_report()

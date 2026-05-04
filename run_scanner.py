#!/usr/bin/env python3
"""
Sports Edge - Unified Scanner Runner

Runs all scanning strategies and outputs a combined report.
Designed to be run periodically (every 15-30 minutes) or as a one-shot.

Usage:
  python3 run_scanner.py              # Single scan
  python3 run_scanner.py continuous   # Every 30 min
  python3 run_scanner.py report       # Just show latest results
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def run_single_scan():
    """Run all scanners and combine results."""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*70}")
    print(f"  SPORTS EDGE - UNIFIED SCAN")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*70}")

    results = {
        "timestamp": now.isoformat(),
        "game_lines": None,
        "player_props": None,
        "picks": [],
    }

    # 1. Game Line Scanner (sbrscrape - multi-book, free)
    print(f"\n{'='*70}")
    print(f"  PHASE 1: GAME LINES (10+ books via SBR)")
    print(f"{'='*70}")
    try:
        from game_line_scanner import GameLineScanner
        gls = GameLineScanner()
        gl_opps = gls.scan_all(["NBA", "MLB", "NHL"])
        results["game_lines"] = {
            "opportunities": len(gl_opps),
            "top_picks": gl_opps[:10],
        }
        for opp in gl_opps[:5]:
            results["picks"].append({
                "source": "game_line_crossbook",
                "sport": opp["sport"],
                "game": opp["game"],
                "bet": f"{opp['market']} {opp['side']} {opp['line']} @ {opp['book']}",
                "odds": f"{opp['odds']:+d}",
                "edge": f"{opp['edge']:.1%}",
                "ev": f"{opp['ev']:.1%}",
                "kelly": f"{opp['kelly_pct']:.1f}%",
                "confidence": "HIGH" if opp["edge"] > 0.04 else "MEDIUM",
            })
    except Exception as e:
        print(f"  Game line scanner error: {e}")

    # 2. FanDuel Player Props (unlimited, free)
    print(f"\n{'='*70}")
    print(f"  PHASE 2: FANDUEL PLAYER PROPS")
    print(f"{'='*70}")
    try:
        from fd_line_tracker import LineTracker
        lt = LineTracker()
        lt_results = lt.run_full_analysis()
        if lt_results:
            results["player_props"] = {
                "props_count": lt_results.get("props_count", 0),
                "line_moves": len(lt_results.get("line_moves", [])),
                "correlation_alerts": len(lt_results.get("correlation_alerts", [])),
            }
            for alert in lt_results.get("correlation_alerts", [])[:3]:
                if abs(alert.get("discrepancy", 0)) >= 2.0:
                    results["picks"].append({
                        "source": "fd_correlation",
                        "sport": "NBA",
                        "game": alert.get("game", ""),
                        "bet": f"{alert['signal']} {alert.get('combo_line', '')}",
                        "player": alert.get("player", ""),
                        "edge": f"{abs(alert.get('discrepancy', 0)):.1f} pts discrepancy",
                        "confidence": "MEDIUM",
                    })
    except Exception as e:
        print(f"  FD tracker error: {e}")

    # 3. Game Line Backtest (today's completed games)
    print(f"\n{'='*70}")
    print(f"  PHASE 3: BACKTEST (Today's Results)")
    print(f"{'='*70}")
    try:
        from game_line_backtester import backtest_sport
        combined_bets = []
        for sport in ["NBA", "MLB", "NHL"]:
            result = backtest_sport(sport)
            if result and result["bets"]:
                combined_bets.extend(result["bets"])

        if combined_bets:
            wins = sum(1 for b in combined_bets if b["won"])
            total_pnl = sum(b["pnl"] for b in combined_bets)
            total_staked = sum(b["stake"] for b in combined_bets)
            roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

            print(f"\n  Today's backtest: {len(combined_bets)} bets, "
                  f"{wins/len(combined_bets)*100:.0f}% WR, "
                  f"${total_pnl:+.2f} ({roi:+.1f}% ROI)")
            results["backtest"] = {
                "bets": len(combined_bets),
                "win_rate": round(wins / len(combined_bets) * 100, 1),
                "pnl": round(total_pnl, 2),
                "roi": round(roi, 1),
            }
    except Exception as e:
        print(f"  Backtest error: {e}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  ACTIONABLE PICKS")
    print(f"{'='*70}")

    if results["picks"]:
        for i, pick in enumerate(results["picks"], 1):
            conf = pick.get("confidence", "LOW")
            print(f"\n  {i}. [{conf}] {pick.get('sport', '')} - {pick.get('game', '')}")
            if "player" in pick:
                print(f"     Player: {pick['player']}")
            print(f"     Bet: {pick['bet']}")
            if "odds" in pick:
                print(f"     Odds: {pick['odds']} | Edge: {pick['edge']} | EV: {pick.get('ev', 'N/A')}")
            else:
                print(f"     Edge: {pick['edge']}")
    else:
        print("  No actionable picks at this time")

    # Save combined results
    outpath = os.path.join(DATA_DIR, "unified_scan.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Combined results saved to {outpath}")

    return results


def show_report():
    """Display latest scan results."""
    outpath = os.path.join(DATA_DIR, "unified_scan.json")
    if not os.path.exists(outpath):
        print("No scan results found. Run: python3 run_scanner.py")
        return

    with open(outpath) as f:
        results = json.load(f)

    print(f"\n  Last scan: {results.get('timestamp', 'unknown')}")

    gl = results.get("game_lines", {})
    if gl:
        print(f"  Game line opportunities: {gl.get('opportunities', 0)}")

    pp = results.get("player_props", {})
    if pp:
        print(f"  FD player props: {pp.get('props_count', 0)}")
        print(f"  Line moves: {pp.get('line_moves', 0)}")
        print(f"  Correlation alerts: {pp.get('correlation_alerts', 0)}")

    bt = results.get("backtest", {})
    if bt:
        print(f"  Today's backtest: {bt.get('bets', 0)} bets, "
              f"{bt.get('win_rate', 0):.0f}% WR, "
              f"${bt.get('pnl', 0):+.2f} ({bt.get('roi', 0):+.1f}% ROI)")

    picks = results.get("picks", [])
    if picks:
        print(f"\n  Picks ({len(picks)}):")
        for pick in picks:
            print(f"    [{pick.get('confidence', '?')}] {pick.get('sport', '')} "
                  f"{pick.get('game', '')} - {pick.get('bet', '')}")


def continuous(interval_minutes=30, max_cycles=16):
    """Run scans continuously."""
    print(f"  Continuous mode: every {interval_minutes} minutes")
    for cycle in range(1, max_cycles + 1):
        print(f"\n  === Cycle {cycle}/{max_cycles} ({datetime.now(timezone.utc).strftime('%H:%M UTC')}) ===")
        run_single_scan()
        if cycle < max_cycles:
            print(f"\n  Sleeping {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            continuous(interval)
        elif sys.argv[1] == "report":
            show_report()
        else:
            run_single_scan()
    else:
        run_single_scan()

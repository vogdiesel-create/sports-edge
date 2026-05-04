#!/usr/bin/env python3
"""
Sports Edge - Smart Scanner V2

Applies backtested learnings to produce higher-quality picks:

GAME LINES (SBR data):
- Pinnacle benchmark devig strategy
- Edge cap: 3-6% (below 3% = noise, above 6% = stale line)
- Exclude bodog (high volume but net negative in backtest)
- Track which books are consistently profitable

PLAYER PROPS (FanDuel):
- Correlation arbitrage (combo vs individual mismatch)
- Vig outlier detection
- Line movement tracking

OUTPUT: JSON file consumed by dashboard + daily email digest
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def scan_game_lines():
    """Scan game lines with refined filters."""
    try:
        from game_line_scanner import GameLineScanner
    except ImportError:
        return {"error": "game_line_scanner not available", "picks": []}

    gls = GameLineScanner()
    raw_opps = gls.scan_all(["NBA", "MLB", "NHL"])

    # Apply refined filters
    filtered = []
    rejected_reasons = defaultdict(int)

    for opp in raw_opps:
        edge = opp.get("edge", 0)
        book = opp.get("book", "")

        # Filter 1: Edge range (3-6%)
        if edge < 0.03:
            rejected_reasons["edge_too_low"] += 1
            continue
        if edge > 0.06:
            rejected_reasons["edge_too_high_stale"] += 1
            continue

        # Filter 2: Exclude consistently unprofitable books
        if book in ("bodog",):
            rejected_reasons["unprofitable_book"] += 1
            continue

        # Tier the pick by confidence
        if book in ("unibet", "sportsbetting"):
            opp["tier"] = "A"  # Historically most profitable
            opp["confidence"] = "HIGH"
        elif book in ("bet365", "heritage", "gtbets", "intertops"):
            opp["tier"] = "B"
            opp["confidence"] = "HIGH" if edge > 0.04 else "MEDIUM"
        else:
            opp["tier"] = "C"
            opp["confidence"] = "MEDIUM"

        filtered.append(opp)

    # Sort: Tier A first, then by edge
    filtered.sort(key=lambda x: ({"A": 0, "B": 1, "C": 2}[x["tier"]], -x["edge"]))

    return {
        "raw_count": len(raw_opps),
        "filtered_count": len(filtered),
        "rejected": dict(rejected_reasons),
        "picks": filtered[:15],  # Top 15
    }


def scan_fd_props():
    """Scan FanDuel player props."""
    try:
        from fd_line_tracker import LineTracker
    except ImportError:
        return {"error": "fd_line_tracker not available"}

    lt = LineTracker()
    result = lt.run_full_analysis()
    if not result:
        return {"error": "no FD data"}

    # Extract correlation alerts with significant discrepancy
    alerts = []
    for alert in result.get("correlation_alerts", []):
        disc = abs(alert.get("discrepancy", 0))
        if disc >= 2.0:
            alerts.append({
                "player": alert.get("player", ""),
                "game": alert.get("game", ""),
                "combo_type": alert.get("combo_type", ""),
                "combo_line": alert.get("combo_line"),
                "sum_line": alert.get("sum_line"),
                "discrepancy": round(disc, 1),
                "signal": alert.get("signal", ""),
                "confidence": "HIGH" if disc >= 3.0 else "MEDIUM",
            })

    return {
        "props_count": result.get("props_count", 0),
        "line_moves": len(result.get("line_moves", [])),
        "correlation_alerts": len(alerts),
        "top_alerts": alerts[:10],
    }


def run_daily_backtest():
    """Backtest today's completed games."""
    try:
        from game_line_backtester import backtest_sport
    except ImportError:
        return None

    combined_bets = []
    for sport in ["NBA", "MLB", "NHL"]:
        try:
            result = backtest_sport(sport)
            if result and result["bets"]:
                combined_bets.extend(result["bets"])
        except:
            continue

    if not combined_bets:
        return None

    wins = sum(1 for b in combined_bets if b["won"])
    total_pnl = sum(b["pnl"] for b in combined_bets)
    total_staked = sum(b["stake"] for b in combined_bets)
    roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

    return {
        "bets": len(combined_bets),
        "wins": wins,
        "win_rate": round(wins / len(combined_bets) * 100, 1),
        "pnl": round(total_pnl, 2),
        "roi": round(roi, 1),
        "details": combined_bets[:20],
    }


def collect_data_snapshot():
    """Save raw data snapshot for future backtesting."""
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "game_lines": {},
    }

    try:
        from sbrscrape import Scoreboard
        for sport in ["NBA", "MLB", "NHL"]:
            try:
                sb = Scoreboard(sport)
                games = []
                for g in sb.games:
                    games.append({
                        "date": g.get("date", ""),
                        "status": g.get("status", ""),
                        "home_team": g.get("home_team", ""),
                        "away_team": g.get("away_team", ""),
                        "home_score": g.get("home_score"),
                        "away_score": g.get("away_score"),
                        "home_ml": g.get("home_ml", {}),
                        "away_ml": g.get("away_ml", {}),
                        "total": g.get("total", {}),
                        "over_odds": g.get("over_odds", {}),
                        "under_odds": g.get("under_odds", {}),
                        "home_spread": g.get("home_spread", {}),
                        "home_spread_odds": g.get("home_spread_odds", {}),
                        "away_spread": g.get("away_spread", {}),
                        "away_spread_odds": g.get("away_spread_odds", {}),
                    })
                snapshot["game_lines"][sport] = games
                time.sleep(0.3)
            except:
                continue
    except ImportError:
        pass

    # Save with timestamp
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    path = os.path.join(DATA_DIR, f"snapshot_{ts}.json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    return path


def run_smart_scan():
    """Run the full smart scanner."""
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  SPORTS EDGE - SMART SCANNER V2")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    results = {
        "timestamp": now.isoformat(),
        "version": "2.0",
        "picks": [],
        "game_lines": None,
        "player_props": None,
        "backtest": None,
    }

    # 1. Game Lines (refined)
    print(f"\n  [1/4] Game Lines (Pinnacle benchmark, 3-6% edge filter)...")
    gl = scan_game_lines()
    results["game_lines"] = {
        "raw": gl.get("raw_count", 0),
        "filtered": gl.get("filtered_count", 0),
        "rejected": gl.get("rejected", {}),
        "opportunities": gl.get("filtered_count", 0),
        "top_picks": gl.get("picks", [])[:10],
    }

    for opp in gl.get("picks", [])[:5]:
        results["picks"].append({
            "source": "game_line_v2",
            "sport": opp.get("sport", ""),
            "game": opp.get("game", ""),
            "bet": f"{opp['market']} {opp['side']} {opp.get('line','')} @ {opp['book']}",
            "odds": f"{opp['odds']:+d}" if isinstance(opp.get('odds'), (int, float)) else str(opp.get('odds', '')),
            "edge": f"{opp['edge']:.1%}",
            "ev": f"{opp.get('ev', 0):.1%}",
            "kelly": f"{opp.get('kelly_pct', 0):.1f}%",
            "confidence": opp.get("confidence", "MEDIUM"),
            "tier": opp.get("tier", "C"),
        })

    print(f"    Raw: {gl.get('raw_count', 0)} | After filter: {gl.get('filtered_count', 0)}")
    if gl.get("rejected"):
        print(f"    Rejected: {gl['rejected']}")

    # 2. OddsTrader +EV Props (Pinnacle-benchmarked)
    print(f"\n  [2/5] OddsTrader +EV Props (Pinnacle benchmark)...")
    try:
        from oddstrader_scraper import run_scrape as ot_scrape
        ot = ot_scrape()
        ot_props = ot.get("props", [])
        results["oddstrader_props"] = {
            "total_scraped": ot.get("total_scraped", 0),
            "actionable": ot.get("actionable", 0),
        }

        # Add top OddsTrader picks to unified picks list
        for prop in ot_props[:10]:
            results["picks"].append({
                "source": "oddstrader_ev",
                "sport": prop.get("sport", ""),
                "game": prop.get("game", ""),
                "player": prop.get("player", ""),
                "bet": f"{prop['market']} {prop.get('best_odds', '')}",
                "ev": f"+{prop['ev_pct']:.1f}%",
                "edge": f"+{prop['ev_pct']:.1f}%",
                "fair_prob": f"{prop['fair_prob']:.0%}",
                "kelly": f"{prop.get('kelly_pct', 0):.2f}%",
                "confidence": prop.get("confidence", "MEDIUM"),
                "tier": prop.get("tier", "C"),
            })
        print(f"    Scraped: {ot.get('total_scraped', 0)} | Actionable: {ot.get('actionable', 0)}")
    except Exception as e:
        print(f"    OddsTrader error: {e}")
        results["oddstrader_props"] = {"error": str(e)}

    # 3. FanDuel Props
    print(f"\n  [3/5] FanDuel Player Props...")
    pp = scan_fd_props()
    if "error" not in pp:
        results["player_props"] = {
            "props_count": pp.get("props_count", 0),
            "line_moves": pp.get("line_moves", 0),
            "correlation_alerts": pp.get("correlation_alerts", 0),
        }
        for alert in pp.get("top_alerts", [])[:3]:
            results["picks"].append({
                "source": "fd_correlation",
                "sport": "NBA",
                "game": alert.get("game", ""),
                "player": alert.get("player", ""),
                "bet": f"{alert['signal']} {alert.get('combo_line', '')}",
                "edge": f"{alert['discrepancy']:.1f} pts discrepancy",
                "confidence": alert.get("confidence", "MEDIUM"),
            })
        print(f"    Props: {pp.get('props_count', 0)} | Moves: {pp.get('line_moves', 0)} | Correlation alerts: {pp.get('correlation_alerts', 0)}")
    else:
        print(f"    Error: {pp['error']}")

    # 4. Backtest
    print(f"\n  [4/5] Today's Backtest...")
    bt = run_daily_backtest()
    if bt:
        results["backtest"] = {
            "bets": bt["bets"],
            "win_rate": bt["win_rate"],
            "pnl": bt["pnl"],
            "roi": bt["roi"],
        }
        print(f"    {bt['bets']} bets, {bt['win_rate']:.0f}% WR, ${bt['pnl']:+.2f} ({bt['roi']:+.1f}% ROI)")
    else:
        print(f"    No completed games to backtest")

    # 5. Data Collection
    print(f"\n  [5/5] Collecting data snapshot...")
    snap_path = collect_data_snapshot()
    print(f"    Saved to {snap_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  ACTIONABLE PICKS ({len(results['picks'])})")
    print(f"{'='*60}")

    if results["picks"]:
        for i, pick in enumerate(results["picks"], 1):
            tier = f"[{pick.get('tier', '?')}]" if 'tier' in pick else ""
            conf = pick.get("confidence", "")
            print(f"\n  {i}. {tier}[{conf}] {pick.get('sport', '')} - {pick.get('game', '')}")
            if "player" in pick:
                print(f"     Player: {pick['player']}")
            print(f"     Bet: {pick['bet']}")
            if "odds" in pick:
                print(f"     Odds: {pick['odds']} | Edge: {pick['edge']} | EV: {pick.get('ev', 'N/A')}")
            else:
                print(f"     Edge: {pick['edge']}")
    else:
        print("  No actionable picks at this time")

    # Save
    outpath = os.path.join(DATA_DIR, "unified_scan.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")

    # 6. Multi-Book Cross-Validation
    print(f"\n  [6/9] Multi-Book Devig Cross-Validation...")
    try:
        from multi_book_devig import run_multi_book_devig
        mbd = run_multi_book_devig()
        xv = mbd.get("cross_validation", {})
        confirmed = xv.get("confirmed", [])
        results["cross_validation"] = {
            "confirmed_count": len(confirmed),
            "disagreed_count": len(xv.get("disagreed", [])),
            "unmatched_count": len(xv.get("unmatched", [])),
            "confirmed_picks": confirmed[:10],
        }
        # Add confirmed cross-validated picks to top of picks list
        for c in confirmed[:5]:
            results["picks"].insert(0, {
                "source": "cross_validated",
                "sport": c.get("sport", ""),
                "game": c.get("game", ""),
                "player": c.get("player", ""),
                "bet": f"{c['market']} {c.get('line','')} {c['ot_best_odds']}",
                "edge": f"OT:+{c['ot_ev_pct']:.1f}% Bov:+{c['edge_vs_bovada_devig']:.1f}%",
                "confidence": c.get("confidence", "HIGH"),
                "tier": "S",  # Cross-validated = highest tier
            })
        print(f"    Confirmed: {len(confirmed)} | Disagreed: {len(xv.get('disagreed',[]))} | Unmatched: {len(xv.get('unmatched',[]))}")
    except Exception as e:
        print(f"    Multi-book devig error: {e}")

    # 7. Prop Grading
    print(f"\n  [7/9] Prop Grading...")
    try:
        from prop_grader import log_props, grade_props
        log_props()
        grade_props()
    except Exception as e:
        print(f"    Prop grading error: {e}")

    # 8. Archive picks for historical tracking
    try:
        import shutil
        archive_dir = os.path.join(DATA_DIR, "archives")
        os.makedirs(archive_dir, exist_ok=True)
        ts = now.strftime("%Y%m%d_%H%M")
        shutil.copy2(outpath, os.path.join(archive_dir, f"unified_{ts}.json"))
    except:
        pass

    # 9. Paper Trading
    print(f"\n  [9/10] Paper Trading...")
    try:
        from paper_trader import run_paper_cycle
        run_paper_cycle()
    except Exception as e:
        print(f"    Paper trading error: {e}")

    # 10. CLV Tracking (log picks and check previous picks)
    print(f"\n  [10/10] CLV Tracking...")
    try:
        from clv_tracker import check_clv
        check_clv()
    except Exception as e:
        print(f"    CLV error: {e}")

    return results


def continuous(interval=30, cycles=16):
    """Run continuously."""
    print(f"  Continuous mode: every {interval} min, {cycles} cycles")
    for i in range(1, cycles + 1):
        print(f"\n  === Cycle {i}/{cycles} ===")
        try:
            run_smart_scan()
        except Exception as e:
            print(f"  Error in cycle {i}: {e}")
        if i < cycles:
            print(f"\n  Sleeping {interval} minutes...")
            time.sleep(interval * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        continuous(interval)
    else:
        run_smart_scan()

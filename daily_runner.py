#!/usr/bin/env python3
"""
Sports Edge Daily Runner
========================

Automated daily pipeline that runs all models and captures edges.

Schedule (all times ET):
  10:00 AM - Data refresh + grade yesterday's picks
  12:00 PM - First model run + OddsTrader scan (lines posted by ~11 AM)
   3:00 PM - Second model run (line movements, updated rosters)
   6:00 PM - Pre-game final scan (last chance for early games)

Usage:
    python3 daily_runner.py              # Run full pipeline once
    python3 daily_runner.py --grade      # Grade only
    python3 daily_runner.py --scan       # OddsTrader scan only
    python3 daily_runner.py --summary    # Print today's summary
"""

import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "daily_logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def grade_picks():
    """Grade yesterday's ungraded picks."""
    log("Grading outstanding picks...")
    try:
        from prop_pick_tracker import grade_all_picks
        results = grade_all_picks()
        log(f"  Grading complete: {results}")
        return results
    except ImportError:
        # Try running as script
        os.system(f"cd {BASE_DIR} && python3 prop_pick_tracker.py grade")
        return "ran via subprocess"


def refresh_data():
    """Refresh MLB data (schedules, lines, pitcher stats)."""
    log("Refreshing data pipeline...")
    try:
        from data_pipeline import run_pipeline
        run_pipeline()
        log("  Data refresh complete")
    except Exception as e:
        log(f"  Data refresh warning: {e}")

    # Also refresh MLB-specific data
    try:
        from mlb_data_pipeline import main as mlb_refresh
        mlb_refresh()
        log("  MLB data refresh complete")
    except Exception as e:
        log(f"  MLB data refresh warning: {e}")


def run_models():
    """Run edge detector (all models)."""
    log("Running edge detector (all models)...")
    try:
        from edge_detector import run
        result = run(dry_run=False)
        picks = result.get("picks", [])
        log(f"  Edge detector: {len(picks)} model picks")
        return result
    except Exception as e:
        log(f"  Edge detector error: {e}")
        return {"picks": [], "error": str(e)}


def run_oddstrader():
    """Run OddsTrader EV scanner."""
    log("Running OddsTrader scanner...")
    try:
        from oddstrader_scraper import scrape_and_save
        picks = scrape_and_save()
        log(f"  OddsTrader: {len(picks)} actionable picks")
        return picks
    except Exception as e:
        log(f"  OddsTrader error: {e}")
        return []


def daily_summary():
    """Print today's P&L and pick summary."""
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"=== DAILY SUMMARY ({today}) ===")

    # Paper ledger
    ledger_path = os.path.join(DATA_DIR, "paper_ledger.json")
    if os.path.exists(ledger_path):
        with open(ledger_path) as f:
            ledger = json.load(f)
        bets = ledger.get("bets", [])
        today_bets = [b for b in bets if b.get("date", "").startswith(today)]
        total_pnl = sum(b.get("pnl", 0) for b in bets if b.get("graded"))
        log(f"  Paper ledger: {len(bets)} total bets, {len(today_bets)} today, P&L: ${total_pnl:.2f}")

    # Prop picks
    prop_path = os.path.join(DATA_DIR, "model_prop_picks.json")
    if os.path.exists(prop_path):
        with open(prop_path) as f:
            props = json.load(f)
        picks = props.get("picks", [])
        graded = [p for p in picks if p.get("graded")]
        won = [p for p in graded if p.get("won")]
        pnl = sum(p.get("pnl", 0) for p in graded)
        log(f"  Model props: {len(picks)} total, {len(graded)} graded, {len(won)}W-{len(graded)-len(won)}L, P&L: ${pnl:.2f}")

    # OddsTrader
    ot_path = os.path.join(DATA_DIR, "prop_ledger.json")
    if os.path.exists(ot_path):
        with open(ot_path) as f:
            ot = json.load(f)
        ot_bets = ot.get("bets", [])
        ot_graded = [b for b in ot_bets if b.get("graded")]
        ot_won = [b for b in ot_graded if b.get("won")]
        ot_pnl = sum(b.get("pnl", 0) for b in ot_graded)
        log(f"  OddsTrader: {len(ot_bets)} total, {len(ot_graded)} graded, {len(ot_won)}W-{len(ot_graded)-len(ot_won)}L, P&L: ${ot_pnl:.2f}")


def run_full_pipeline():
    """Run the complete daily pipeline."""
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"=== SPORTS EDGE DAILY PIPELINE ({today}) ===\n")

    # Step 1: Grade yesterday
    grade_picks()
    print()

    # Step 2: Refresh data
    refresh_data()
    print()

    # Step 3: Run models
    model_result = run_models()
    print()

    # Step 4: OddsTrader scan
    ot_picks = run_oddstrader()
    print()

    # Step 5: Summary
    daily_summary()

    # Save run log
    run_log = {
        "timestamp": datetime.now().isoformat(),
        "model_picks": len(model_result.get("picks", [])),
        "oddstrader_picks": len(ot_picks),
    }
    log_path = os.path.join(LOG_DIR, f"run_{today}_{datetime.now().strftime('%H%M')}.json")
    with open(log_path, "w") as f:
        json.dump(run_log, f, indent=2)
    log(f"\nRun log saved to {log_path}")


if __name__ == "__main__":
    if "--grade" in sys.argv:
        grade_picks()
    elif "--scan" in sys.argv:
        run_oddstrader()
    elif "--summary" in sys.argv:
        daily_summary()
    else:
        run_full_pipeline()

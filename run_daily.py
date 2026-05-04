#!/usr/bin/env python3
"""
Sports Edge - Daily Pipeline Runner
====================================

Runs the complete daily pipeline in order:
  1. Update data pipelines (NHL + MLB)
  2. Run the unified edge detector
  3. Run paper trading cycle (grade past bets, generate report)
  4. Save results summary

Suitable for cron:
  # Run at 10:00 AM and 5:00 PM UTC daily
  0 10,17 * * * cd /home/aiciv/sports-edge && python3 run_daily.py >> data/daily_run.log 2>&1

Usage:
  python3 run_daily.py                  # Full pipeline
  python3 run_daily.py --skip-pipeline  # Skip data updates (use cached data)
  python3 run_daily.py --dry-run        # Skip paper trading
  python3 run_daily.py --quiet          # Minimal output
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "daily_runs")
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg: str, quiet: bool = False):
    """Print with timestamp."""
    if not quiet:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"  [{ts}] {msg}")


def run_step(name: str, func, quiet: bool = False) -> dict:
    """Run a pipeline step with timing and error handling."""
    log(f"Starting: {name}", quiet)
    start = time.time()
    result = {"step": name, "status": "ok", "error": None, "elapsed_sec": 0}

    try:
        output = func()
        result["output"] = output
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        if not quiet:
            traceback.print_exc()

    result["elapsed_sec"] = round(time.time() - start, 1)
    status = "OK" if result["status"] == "ok" else f"ERROR: {result['error']}"
    log(f"  {name}: {status} ({result['elapsed_sec']}s)", quiet)
    return result


def update_nhl_pipeline():
    """Update NHL data from APIs."""
    from nhl_data_pipeline import update_all
    return update_all()


def update_mlb_pipeline():
    """Update MLB data from APIs."""
    from mlb_data_pipeline import download_mlb_schedule, download_mlb_standings, fetch_weather_for_games
    download_mlb_schedule()
    download_mlb_standings()
    fetch_weather_for_games()
    return {"status": "ok"}


def run_data_collector():
    """Collect game line snapshots from SBR (needed for MLB feature model)."""
    from data_collector import run_collection
    return run_collection()


def run_edge_detector(dry_run: bool = False):
    """Run the unified edge detector."""
    from edge_detector import run
    return run(dry_run=dry_run)


def run_paper_trading():
    """Run paper trading cycle (grade bets, generate report)."""
    from paper_trader import run_paper_cycle
    return run_paper_cycle()


def run_smart_scanner():
    """Run the existing smart scanner for additional picks."""
    from smart_scanner import run_smart_scan
    return run_smart_scan()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sports Edge - Daily Pipeline")
    parser.add_argument("--skip-pipeline", action="store_true",
                        help="Skip data pipeline updates")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip paper trading")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")
    parser.add_argument("--skip-scanner", action="store_true",
                        help="Skip Level 1 smart scanner (edge detector runs its own)")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    quiet = args.quiet

    if not quiet:
        print(f"\n{'='*60}")
        print(f"  SPORTS EDGE - DAILY PIPELINE")
        print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"{'='*60}")

    results = {
        "timestamp": now.isoformat(),
        "steps": [],
    }

    # -----------------------------------------------------------------------
    # Step 1: Update data pipelines
    # -----------------------------------------------------------------------
    if not args.skip_pipeline:
        if not quiet:
            print(f"\n  === STEP 1: DATA PIPELINES ===")

        r = run_step("NHL Data Pipeline", update_nhl_pipeline, quiet)
        results["steps"].append(r)

        r = run_step("MLB Data Pipeline", update_mlb_pipeline, quiet)
        results["steps"].append(r)

        r = run_step("Game Line Collection", run_data_collector, quiet)
        results["steps"].append(r)
    else:
        log("Skipping data pipelines (--skip-pipeline)", quiet)

    # -----------------------------------------------------------------------
    # Step 2: Run unified edge detector
    # -----------------------------------------------------------------------
    if not quiet:
        print(f"\n  === STEP 2: EDGE DETECTION ===")

    r = run_step(
        "Edge Detector",
        lambda: run_edge_detector(dry_run=args.dry_run),
        quiet
    )
    results["steps"].append(r)

    edge_output = r.get("output", {})
    total_picks = 0
    if isinstance(edge_output, dict):
        total_picks = edge_output.get("total_picks", 0)

    # -----------------------------------------------------------------------
    # Step 3: Run smart scanner (optional, for additional Level 1 picks)
    # -----------------------------------------------------------------------
    if not args.skip_scanner:
        if not quiet:
            print(f"\n  === STEP 3: SMART SCANNER ===")

        r = run_step("Smart Scanner", run_smart_scanner, quiet)
        results["steps"].append(r)
    else:
        log("Skipping smart scanner (--skip-scanner)", quiet)

    # -----------------------------------------------------------------------
    # Step 4: Paper trading cycle
    # -----------------------------------------------------------------------
    if not args.dry_run:
        if not quiet:
            print(f"\n  === STEP 4: PAPER TRADING ===")

        r = run_step("Paper Trading", run_paper_trading, quiet)
        results["steps"].append(r)
    else:
        log("Skipping paper trading (--dry-run)", quiet)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    elapsed_total = sum(s.get("elapsed_sec", 0) for s in results["steps"])
    errors = [s for s in results["steps"] if s["status"] == "error"]

    results["total_elapsed_sec"] = round(elapsed_total, 1)
    results["total_steps"] = len(results["steps"])
    results["errors"] = len(errors)
    results["total_picks"] = total_picks

    if not quiet:
        print(f"\n{'='*60}")
        print(f"  DAILY PIPELINE COMPLETE")
        print(f"  Steps: {results['total_steps']} | "
              f"Errors: {results['errors']} | "
              f"Picks: {total_picks} | "
              f"Time: {elapsed_total:.0f}s")
        if errors:
            print(f"\n  ERRORS:")
            for e in errors:
                print(f"    - {e['step']}: {e['error']}")
        print(f"{'='*60}")

    # Save run log
    ts = now.strftime("%Y%m%d_%H%M")
    log_path = os.path.join(LOG_DIR, f"run_{ts}.json")

    # Clean for JSON serialization (remove non-serializable output objects)
    save_results = {
        "timestamp": results["timestamp"],
        "total_elapsed_sec": results["total_elapsed_sec"],
        "total_steps": results["total_steps"],
        "errors": results["errors"],
        "total_picks": results["total_picks"],
        "steps": [
            {
                "step": s["step"],
                "status": s["status"],
                "error": s["error"],
                "elapsed_sec": s["elapsed_sec"],
            }
            for s in results["steps"]
        ],
    }

    with open(log_path, "w") as f:
        json.dump(save_results, f, indent=2, default=str)

    if not quiet:
        print(f"  Log saved to {log_path}")

    # Exit with error code if any steps failed
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

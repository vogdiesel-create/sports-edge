#!/usr/bin/env python3
"""
Backfill Pinnacle closing line gaps in game_lines.db.

Identified gaps (2026-04-16):
1. NHL 2019-20: 0 games (entire season missing)
2. MLB 2022: 266 of ~2430 games (May-Oct missing)
3. MLB 2025: 0 games (season just started)

Uses fetch_pinnacle_history.py infrastructure (BettingIsCool API).
Estimated ~3573 API calls total (fits in one daily quota of 4800).

Usage:
    python3 backfill_pinnacle_gaps.py          # Backfill all gaps
    python3 backfill_pinnacle_gaps.py MLB       # MLB gaps only
    python3 backfill_pinnacle_gaps.py NHL       # NHL gaps only
    python3 backfill_pinnacle_gaps.py --status  # Show current gaps
"""

import sys
import os
import sqlite3
import time
from datetime import datetime

# Reuse the fetch_pinnacle_history infrastructure
sys.path.insert(0, os.path.dirname(__file__))
from fetch_pinnacle_history import (
    get_scraper, fetch, init_db, is_real_game,
    generate_monthly_windows, download_all_fixtures,
    download_closing_odds, DB_PATH, DAILY_LIMIT
)

# Only the gaps - seasons/ranges where data is missing or partial
GAPS = [
    # NHL 2019-20 season: entirely missing
    ("NHL", 1456, [("2019-10-01", "2020-10-01")]),
    # MLB 2022: only have Apr, need May-Oct
    ("MLB", 246, [("2022-05-01", "2022-11-01")]),
    # MLB 2025: season just started
    ("MLB", 246, [("2025-04-01", "2025-11-01")]),
]


def show_status():
    """Show current data status and gaps."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("=" * 60)
    print("  Pinnacle Closing Line Data Status")
    print("=" * 60)

    nhl_seasons = [
        ("2019-20", "2019-10-01", "2020-10-01", 1300),
        ("2020-21", "2021-01-01", "2021-07-31", 950),
        ("2021-22", "2021-10-01", "2022-07-01", 1400),
        ("2022-23", "2022-10-01", "2023-07-01", 1400),
        ("2023-24", "2023-10-01", "2024-07-01", 1400),
        ("2024-25", "2024-10-01", "2025-07-01", 1400),
    ]

    print("\n  NHL:")
    for name, start, end, expected in nhl_seasons:
        c.execute(
            "SELECT COUNT(DISTINCT event_id) FROM pinnacle_closing "
            "WHERE sport='NHL' AND game_date >= ? AND game_date < ?",
            (start, end)
        )
        count = c.fetchone()[0]
        pct = count / expected * 100 if expected else 0
        marker = "OK" if pct > 90 else "GAP" if pct < 50 else "PARTIAL"
        print(f"    {name}: {count:>5} games ({pct:>5.1f}% of ~{expected})  [{marker}]")

    mlb_seasons = [
        ("2021", "2021-04-01", "2021-11-01", 1400),
        ("2022", "2022-04-01", "2022-11-01", 1400),
        ("2023", "2023-04-01", "2023-11-01", 1400),
        ("2024", "2024-04-01", "2024-11-01", 1400),
        ("2025", "2025-04-01", "2025-11-01", 100),
    ]

    print("\n  MLB:")
    for name, start, end, expected in mlb_seasons:
        c.execute(
            "SELECT COUNT(DISTINCT event_id) FROM pinnacle_closing "
            "WHERE sport='MLB' AND game_date >= ? AND game_date < ?",
            (start, end)
        )
        count = c.fetchone()[0]
        pct = count / expected * 100 if expected else 0
        marker = "OK" if pct > 90 else "GAP" if pct < 50 else "PARTIAL"
        print(f"    {name}: {count:>5} games ({pct:>5.1f}% of ~{expected})  [{marker}]")

    c.execute("SELECT COUNT(DISTINCT event_id), COUNT(*) FROM pinnacle_closing")
    total_games, total_records = c.fetchone()
    print(f"\n  TOTAL: {total_games} unique games, {total_records} records")
    conn.close()
    print("=" * 60)


def main():
    sport_filter = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            show_status()
            return
        sport_filter = sys.argv[1].upper()

    print("=" * 60)
    print("  Pinnacle Gap Backfill")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if sport_filter:
        print(f"  Filter: {sport_filter} only")
    print("=" * 60)

    scraper = get_scraper()

    # Test connection
    sports = fetch(scraper, "sports")
    if not sports:
        print("ERROR: Cannot connect to API (quota may be exhausted).")
        print("Quota resets at midnight UTC daily.")
        return
    print("  API connection OK")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    total_stored = 0
    total_calls = 0

    for sport_name, league_id, seasons in GAPS:
        if sport_filter and sport_name != sport_filter:
            continue

        print(f"\n{'=' * 40}")
        print(f"  BACKFILL: {sport_name}")
        print(f"  Ranges: {', '.join(f'{s}->{e}' for s,e in seasons)}")
        print(f"{'=' * 40}")

        games = download_all_fixtures(scraper, league_id, sport_name, seasons)
        if games:
            n_stored, n_calls = download_closing_odds(scraper, conn, games, sport_name)
            total_stored += n_stored
            total_calls += n_calls

            if total_calls >= DAILY_LIMIT:
                print(f"\n  Daily limit hit. Run again tomorrow for remaining data.")
                break

    # Summary
    print(f"\n{'=' * 60}")
    for sport in ["NHL", "MLB"]:
        count = conn.execute(
            "SELECT COUNT(DISTINCT event_id) FROM pinnacle_closing WHERE sport=?",
            (sport,)
        ).fetchone()[0]
        print(f"  {sport}: {count} unique games total")

    conn.close()
    print(f"\n  {total_stored} new records stored ({total_calls} API calls)")
    print(f"  Data in {DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()

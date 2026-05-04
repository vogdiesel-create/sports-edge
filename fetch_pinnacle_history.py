#!/usr/bin/env python3
"""
Download historical Pinnacle closing odds for NHL and MLB from BettingIsCool API.
Uses cloudscraper to bypass Cloudflare.

Strategy:
- Fetch fixtures in 1-month windows (keeps each request small)
- Filter locally: parent_id=null, live_status=2, no prop/aggregate names
- Download closing odds per game (period=0 only)
- Resumable: skips event_ids already in DB
- Respects rate limit: 1.3s between calls, stops at daily limit

Rate limit: 50 req/min, 5000 req/day on Starter tier
"""

import cloudscraper
import time
import sqlite3
import os
import sys
from datetime import datetime, timedelta

API_KEY = os.environ.get("BETTINGISCOOL_API_KEY",
    "pk_da1eb76a9e24b77c360874fc0d1e57b677bf85fcbeea5e33")
HEADERS = {"X-API-Key": API_KEY}
BASE = "https://api.bettingiscool.com/api"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

# NHL: Oct-Jun each season. MLB: Apr-Oct each season.
LEAGUES = [
    ("NHL", 1456, [
        ("2019-10-01", "2020-07-01"),
        ("2020-10-01", "2021-07-01"),
        ("2021-10-01", "2022-07-01"),
        ("2022-10-01", "2023-07-01"),
        ("2023-10-01", "2024-07-01"),
        ("2024-10-01", "2025-07-01"),
    ]),
    ("MLB", 246, [
        ("2021-04-01", "2021-11-01"),
        ("2022-04-01", "2022-11-01"),
        ("2023-04-01", "2023-11-01"),
        ("2024-04-01", "2024-11-01"),
        ("2025-04-01", "2025-11-01"),
    ]),
]

DAILY_LIMIT = 4800  # Stay under 5000
RATE_DELAY = 1.3    # seconds between calls


def get_scraper():
    return cloudscraper.create_scraper()


def fetch(scraper, endpoint, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = scraper.get(f"{BASE}/{endpoint}", headers=HEADERS,
                            params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 15))
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    HTTP {r.status_code} on attempt {attempt+1}")
                time.sleep(3)
        except Exception as e:
            print(f"    Request failed: {e}")
            time.sleep(3)
    return None


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pinnacle_closing (
            event_id INTEGER,
            sport TEXT,
            league TEXT,
            game_date TEXT,
            home_team TEXT,
            away_team TEXT,
            market TEXT,
            period INTEGER,
            line REAL,
            odds_over REAL,
            odds_under REAL,
            todds_over REAL,
            todds_under REAL,
            score_home INTEGER,
            score_away INTEGER,
            total_goals INTEGER,
            result_status INTEGER,
            PRIMARY KEY (event_id, market, period, line)
        );
    """)
    conn.commit()


def is_real_game(fix):
    """Filter out props, aggregates, and incomplete games."""
    if fix.get("parent_id") is not None:
        return False
    if fix.get("live_status") != 2:
        return False
    home = fix.get("runner_home") or ""
    # Filter aggregate/prop markets
    if "Goals" in home or "(" in home or "Game" in home:
        return False
    return True


def generate_monthly_windows(start, end):
    """Generate (from, to) date pairs in ~1 month increments."""
    windows = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while current < end_dt:
        next_month = current.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        if next_month > end_dt:
            next_month = end_dt
        windows.append((current.strftime("%Y-%m-%d"), next_month.strftime("%Y-%m-%d")))
        current = next_month
    return windows


def download_all_fixtures(scraper, league_id, sport_name, seasons):
    """Download fixtures using monthly windows, filter to real completed games."""
    all_games = []
    total_raw = 0

    for season_start, season_end in seasons:
        windows = generate_monthly_windows(season_start, season_end)
        for win_from, win_to in windows:
            # API ignores offset param - just fetch once per window
            # Monthly windows keep results under 500
            data = fetch(scraper, "fixtures", {
                "league_id": league_id, "limit": 500,
                "starts_from": win_from, "starts_to": win_to
            })
            window_fixtures = data if data else []

            real = [f for f in window_fixtures if is_real_game(f)]
            total_raw += len(window_fixtures)
            all_games.extend(real)

            if real:
                print(f"    {win_from} -> {win_to}: {len(window_fixtures)} raw, {len(real)} real games")
            time.sleep(RATE_DELAY)

    print(f"  {sport_name}: {total_raw} raw fixtures -> {len(all_games)} real completed games")
    return all_games


def download_closing_odds(scraper, conn, games, sport_name):
    """Download closing odds per game, store period=0 data. Resumable."""
    print(f"\n  Downloading closing odds for {len(games)} {sport_name} games...")

    # Load existing event_ids to skip
    existing_ids = set()
    rows = conn.execute("SELECT DISTINCT event_id FROM pinnacle_closing WHERE sport=?",
                        (sport_name,)).fetchall()
    for r in rows:
        existing_ids.add(r[0])
    print(f"  {len(existing_ids)} games already in DB, will skip")

    stored = 0
    skipped = 0
    api_calls = 0

    for i, fix in enumerate(games):
        event_id = fix["event_id"]

        if event_id in existing_ids:
            skipped += 1
            continue

        closing = fetch(scraper, "closing", {"event_id": event_id})
        api_calls += 1

        if not closing:
            time.sleep(RATE_DELAY)
            continue

        home = fix["runner_home"]
        away = fix["runner_away"]
        game_date = fix["starts"][:10]

        for rec in closing:
            if rec.get("period") != 0:
                continue

            market = rec.get("market")
            line = rec.get("line")
            score_h = rec.get("score_home")
            score_a = rec.get("score_away")
            total = (score_h or 0) + (score_a or 0)

            try:
                conn.execute("""
                    INSERT OR REPLACE INTO pinnacle_closing
                    (event_id, sport, league, game_date, home_team, away_team,
                     market, period, line, odds_over, odds_under,
                     todds_over, todds_under, score_home, score_away,
                     total_goals, result_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id, sport_name, fix.get("league_name", ""),
                    game_date, home, away,
                    market, rec.get("period"), line,
                    rec.get("odds1"), rec.get("odds2"),
                    rec.get("todds1"), rec.get("todds2"),
                    score_h, score_a, total,
                    rec.get("result_status")
                ))
                stored += 1
            except Exception:
                pass

        conn.commit()
        time.sleep(RATE_DELAY)

        if (i + 1) % 100 == 0:
            done_pct = (i + 1) / len(games) * 100
            print(f"    {i+1}/{len(games)} ({done_pct:.0f}%) - "
                  f"{stored} stored, {skipped} skipped, {api_calls} API calls")

        if api_calls >= DAILY_LIMIT:
            print(f"\n  Daily limit reached ({api_calls} calls). Stopping.")
            print(f"  Run again to continue from where we left off.")
            break

    conn.commit()
    print(f"  Done: {stored} records stored, {skipped} skipped, {api_calls} API calls used")
    return stored, api_calls


def main():
    sport_filter = sys.argv[1].upper() if len(sys.argv) > 1 else None

    print("=" * 60)
    print("  Pinnacle Historical Odds Downloader")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if sport_filter:
        print(f"  Filter: {sport_filter} only")
    print("=" * 60)

    scraper = get_scraper()

    # Test connection
    sports = fetch(scraper, "sports")
    if not sports:
        print("ERROR: Cannot connect to API.")
        return
    print("  API connection OK")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    total_stored = 0
    total_calls = 0

    for sport_name, league_id, seasons in LEAGUES:
        if sport_filter and sport_name != sport_filter:
            continue

        print(f"\n{'='*40}")
        print(f"  {sport_name}")
        print(f"{'='*40}")

        games = download_all_fixtures(scraper, league_id, sport_name, seasons)
        if games:
            n_stored, n_calls = download_closing_odds(scraper, conn, games, sport_name)
            total_stored += n_stored
            total_calls += n_calls

            if total_calls >= DAILY_LIMIT:
                print(f"\n  Daily limit hit. Run again tomorrow for remaining data.")
                break

    # Summary
    print(f"\n{'='*60}")
    for sport in ["NHL", "MLB"]:
        count = conn.execute(
            "SELECT COUNT(DISTINCT event_id) FROM pinnacle_closing WHERE sport=?",
            (sport,)
        ).fetchone()[0]
        totals = conn.execute(
            "SELECT COUNT(*) FROM pinnacle_closing WHERE sport=? AND market='totals'",
            (sport,)
        ).fetchone()[0]
        print(f"  {sport}: {count} games, {totals} total line records")

    conn.close()
    print(f"\n  {total_stored} new records stored ({total_calls} API calls)")
    print(f"  Data in {DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run on YOUR Windows machine. Downloads all NHL + MLB historical
closing odds from BettingIsCool Pinnacle API.

Usage:
    pip install requests
    python download_historical_odds.py

Output: nhl_closing.json + mlb_closing.json
Upload both files to the portal when done.
"""

import requests
import json
import time
import sys
from datetime import datetime

API_KEY = "pk_da1eb76a9e24b77c360874fc0d1e57b677bf85fcbeea5e33"
HEADERS = {"X-API-Key": API_KEY}
BASE = "https://api.bettingiscool.com/api"

LEAGUES = {"NHL": 1456, "MLB": 246}


def fetch(endpoint, params=None):
    """Fetch with retry + rate limit handling."""
    for attempt in range(3):
        try:
            r = requests.get(f"{BASE}/{endpoint}", headers=HEADERS,
                             params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 15))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Error {r.status_code}: {r.text[:200]}")
                time.sleep(2)
        except Exception as e:
            print(f"  Request failed: {e}")
            time.sleep(2)
    return None


def download_league(name, league_id):
    """Download all fixtures then closing odds for a league."""
    print(f"\n{'='*60}")
    print(f"  {name} (league {league_id})")
    print(f"{'='*60}")

    # Step 1: Get all fixtures
    print(f"  Fetching fixtures...")
    all_fixtures = []
    offset = 0
    while True:
        data = fetch("fixtures", {"league_id": league_id, "limit": 500, "offset": offset})
        if not data or len(data) == 0:
            break
        all_fixtures.extend(data)
        print(f"    {len(all_fixtures)} fixtures so far...")
        offset += len(data)
        time.sleep(1.5)  # 50/min limit = 1 per 1.2s, be safe

    print(f"  Total fixtures: {len(all_fixtures)}")
    if not all_fixtures:
        return None

    # Step 2: Get closing odds for each fixture using /api/closing
    print(f"  Fetching closing odds...")
    all_closing = []
    for i, fix in enumerate(all_fixtures):
        event_id = fix.get("event_id") or fix.get("id")
        if not event_id:
            continue

        closing = fetch("closing", {"event_id": event_id})
        if closing:
            all_closing.append({
                "event_id": event_id,
                "fixture": fix,
                "closing": closing
            })

        # Rate limit: 50/min = 1.2s between requests
        time.sleep(1.3)

        if (i + 1) % 50 == 0:
            pct = (i + 1) / len(all_fixtures) * 100
            print(f"    {i+1}/{len(all_fixtures)} ({pct:.0f}%) - {len(all_closing)} with odds")
            # Save progress
            with open(f"{name.lower()}_closing_partial.json", "w") as f:
                json.dump(all_closing, f)

    print(f"  Done! {len(all_closing)} fixtures with closing odds.")
    return all_closing


def main():
    print("BettingIsCool Historical Odds Downloader")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Rate limit: 50 req/min (Starter tier)")

    # Test connection
    sports = fetch("sports")
    if not sports:
        print("ERROR: Cannot connect. Check API key.")
        sys.exit(1)
    print("API connection OK.\n")

    for name, league_id in LEAGUES.items():
        data = download_league(name, league_id)
        if data:
            outfile = f"{name.lower()}_closing.json"
            with open(outfile, "w") as f:
                json.dump(data, f)
            size_mb = len(json.dumps(data)) / 1024 / 1024
            print(f"  Saved to {outfile} ({size_mb:.1f} MB)")

    print(f"\n{'='*60}")
    print("DONE! Upload these files to the portal:")
    print("  - nhl_closing.json")
    print("  - mlb_closing.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

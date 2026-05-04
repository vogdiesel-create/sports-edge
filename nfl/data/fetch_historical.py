#!/usr/bin/env python3
"""
Fetch historical NFL player data from nflverse GitHub releases.

This script downloads player weekly stats, roster data, and schedule data
for the 2023, 2024, and 2025 NFL seasons directly from nflverse parquet files.

nfl_data_py is just a wrapper around these same URLs, so we skip the
dependency headache and fetch directly.

Usage:
    python3 /home/aiciv/sports-edge/nfl/data/fetch_historical.py
"""

import os
import sys
import time
import pandas as pd

OUTPUT_DIR = "/home/aiciv/sports-edge/nfl/data/historical"
SEASONS = [2023, 2024, 2025]

# nflverse data URLs (parquet format -- pandas reads these directly)
NFLVERSE_BASE = "https://github.com/nflverse/nflverse-data/releases/download"

DATA_SOURCES = {
    "player_stats": f"{NFLVERSE_BASE}/player_stats/player_stats.parquet",
    "rosters": {
        year: f"{NFLVERSE_BASE}/rosters/roster_weekly_{year}.parquet"
        for year in SEASONS
    },
    "schedules": f"{NFLVERSE_BASE}/schedules/schedules.parquet",
    "pbp_participation": {
        year: f"{NFLVERSE_BASE}/pbp_participation/pbp_participation_{year}.parquet"
        for year in SEASONS
    },
}


def fetch_player_stats():
    """Download weekly player stats and filter to target seasons."""
    print("\n[1/4] Fetching weekly player stats...")
    url = DATA_SOURCES["player_stats"]
    print(f"  URL: {url}")

    try:
        df = pd.read_parquet(url)
        print(f"  Raw rows: {len(df)}")

        # Filter to target seasons and regular season + postseason
        df = df[df["season"].isin(SEASONS)]
        print(f"  After filtering to {SEASONS}: {len(df)} rows")

        # Save full dataset
        out_path = os.path.join(OUTPUT_DIR, "player_stats_weekly.csv")
        df.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")

        # Print summary
        print(f"\n  Summary:")
        print(f"    Seasons: {sorted(df['season'].unique())}")
        print(f"    Weeks: {sorted(df['week'].unique())}")
        if "position" in df.columns:
            print(f"    Positions: {sorted(df['position'].dropna().unique())}")
        print(f"    Unique players: {df['player_id'].nunique()}")

        # Also save position-specific subsets for convenience
        for pos in ["QB", "RB", "WR", "TE"]:
            if "position" in df.columns:
                pos_df = df[df["position"] == pos]
            elif "position_group" in df.columns:
                pos_df = df[df["position_group"] == pos]
            else:
                print(f"  Warning: no position column found, skipping {pos} subset")
                break

            pos_path = os.path.join(OUTPUT_DIR, f"player_stats_{pos.lower()}.csv")
            pos_df.to_csv(pos_path, index=False)
            print(f"  Saved {pos}: {len(pos_df)} rows -> {pos_path}")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def fetch_rosters():
    """Download roster data for each season."""
    print("\n[2/4] Fetching roster data...")
    all_rosters = []

    for year in SEASONS:
        url = DATA_SOURCES["rosters"][year]
        print(f"  {year}: {url}")
        try:
            df = pd.read_parquet(url)
            all_rosters.append(df)
            print(f"    {len(df)} rows")
            time.sleep(1)  # Be polite
        except Exception as e:
            print(f"    ERROR for {year}: {e}")
            # Try the annual roster file as fallback
            fallback_url = f"{NFLVERSE_BASE}/rosters/roster_{year}.parquet"
            print(f"    Trying fallback: {fallback_url}")
            try:
                df = pd.read_parquet(fallback_url)
                all_rosters.append(df)
                print(f"    Fallback success: {len(df)} rows")
            except Exception as e2:
                print(f"    Fallback also failed: {e2}")

    if all_rosters:
        combined = pd.concat(all_rosters, ignore_index=True)
        out_path = os.path.join(OUTPUT_DIR, "rosters.csv")
        combined.to_csv(out_path, index=False)
        print(f"  Saved combined rosters: {len(combined)} rows -> {out_path}")
        return True
    return False


def fetch_schedules():
    """Download schedule data and filter to target seasons."""
    print("\n[3/4] Fetching schedule data...")
    url = DATA_SOURCES["schedules"]
    print(f"  URL: {url}")

    try:
        df = pd.read_parquet(url)
        print(f"  Raw rows: {len(df)}")

        df = df[df["season"].isin(SEASONS)]
        print(f"  After filtering to {SEASONS}: {len(df)} rows")

        out_path = os.path.join(OUTPUT_DIR, "schedules.csv")
        df.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")

        # Print summary
        for year in SEASONS:
            year_df = df[df["season"] == year]
            print(f"    {year}: {len(year_df)} games")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def fetch_snap_counts():
    """
    Try to fetch snap count / participation data.
    This is useful for target share analysis.
    Falls back gracefully if not available.
    """
    print("\n[4/4] Fetching participation/snap count data...")

    for year in SEASONS:
        url = DATA_SOURCES["pbp_participation"][year]
        print(f"  {year}: {url}")
        try:
            df = pd.read_parquet(url)
            out_path = os.path.join(OUTPUT_DIR, f"participation_{year}.csv")
            df.to_csv(out_path, index=False)
            print(f"    {len(df)} rows -> {out_path}")
            time.sleep(1)
        except Exception as e:
            print(f"    Skipped (not critical): {e}")

    return True


def print_data_summary():
    """Print a summary of all downloaded data."""
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    total_size = 0
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            total_size += size_mb
            print(f"  {fname:45s} {size_mb:8.2f} MB")

    print(f"  {'TOTAL':45s} {total_size:8.2f} MB")
    print("=" * 60)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("NFL Historical Data Fetch")
    print(f"Seasons: {SEASONS}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    results = {}
    results["player_stats"] = fetch_player_stats()
    results["rosters"] = fetch_rosters()
    results["schedules"] = fetch_schedules()
    results["participation"] = fetch_snap_counts()

    print_data_summary()

    # Summary
    success = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nCompleted: {success}/{total} data sources fetched successfully")

    if success < total:
        failed = [k for k, v in results.items() if not v]
        print(f"Failed: {failed}")
        print("Non-critical failures can be retried later.")

    return 0 if success >= 2 else 1  # At minimum need player_stats + schedules


if __name__ == "__main__":
    sys.exit(main())

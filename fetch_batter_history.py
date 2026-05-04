#!/usr/bin/env python3
"""
Fetch historical batter game logs for MLB prop model enrichment.

Collects batting game logs (H, HR, RBI, R, AB, BB, K, SB, 2B, 3B, TB) for
all batters from 2021-2025 seasons. Uses MLB Stats API gameLog endpoint.

Stores in game_lines.db:
- mlb_batter_game_logs: per-game batting stats for rolling feature computation
"""

import os
import sqlite3
import sys
import time
from collections import defaultdict

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

MLB_TEAM_ID_TO_ABBREV = {
    108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
    118: "KC",  119: "LAD", 120: "WSH", 121: "NYM", 133: "OAK",
    134: "PIT", 135: "SD",  136: "SEA", 137: "SF",  138: "STL",
    139: "TB",  140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
    144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mlb_batter_game_logs (
            batter_id INTEGER NOT NULL,
            batter_name TEXT,
            game_date TEXT NOT NULL,
            season INTEGER,
            team TEXT,
            at_bats INTEGER,
            plate_appearances INTEGER,
            hits INTEGER,
            doubles INTEGER,
            triples INTEGER,
            home_runs INTEGER,
            rbi INTEGER,
            runs INTEGER,
            walks INTEGER,
            strikeouts INTEGER,
            stolen_bases INTEGER,
            total_bases INTEGER,
            UNIQUE(batter_id, game_date)
        );

        CREATE INDEX IF NOT EXISTS idx_batter_logs
            ON mlb_batter_game_logs(batter_id, game_date);
        CREATE INDEX IF NOT EXISTS idx_batter_date
            ON mlb_batter_game_logs(game_date);
    """)
    conn.commit()


def get_roster_player_ids(team_id, season):
    """Get all position player IDs from a team's roster for a season."""
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    params = {"rosterType": "fullSeason", "season": season}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        player_ids = []
        for entry in data.get("roster", []):
            pos = entry.get("position", {}).get("abbreviation", "")
            if pos != "P":  # Skip pitchers
                player_ids.append(entry["person"]["id"])
        return player_ids
    except Exception:
        return []


def fetch_batter_game_log(batter_id, season):
    """Fetch a batter's game log for a season."""
    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats"
    params = {"stats": "gameLog", "season": season, "group": "hitting"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    logs = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        stat = split.get("stat", {})
        team = split.get("team", {})
        team_id = team.get("id")
        team_abbr = MLB_TEAM_ID_TO_ABBREV.get(team_id, "?")

        ab = stat.get("atBats", 0)
        if ab == 0:
            continue  # Skip games with no at-bats (pinch-runner only, etc.)

        h = stat.get("hits", 0)
        doubles = stat.get("doubles", 0)
        triples = stat.get("triples", 0)
        hr = stat.get("homeRuns", 0)
        singles = h - doubles - triples - hr
        tb = singles + 2 * doubles + 3 * triples + 4 * hr

        logs.append({
            "batter_id": batter_id,
            "batter_name": split.get("player", {}).get("fullName"),
            "game_date": split.get("date"),
            "season": season,
            "team": team_abbr,
            "at_bats": ab,
            "plate_appearances": stat.get("plateAppearances", ab),
            "hits": h,
            "doubles": doubles,
            "triples": triples,
            "home_runs": hr,
            "rbi": stat.get("rbi", 0),
            "runs": stat.get("runs", 0),
            "walks": stat.get("baseOnBalls", 0),
            "strikeouts": stat.get("strikeOuts", 0),
            "stolen_bases": stat.get("stolenBases", 0),
            "total_bases": tb,
        })

    return logs


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    existing_logs = conn.execute(
        "SELECT COUNT(*) FROM mlb_batter_game_logs"
    ).fetchone()[0]
    print(f"Existing batter game log entries: {existing_logs}")

    # Get all MLB team IDs
    team_ids = list(MLB_TEAM_ID_TO_ABBREV.keys())
    seasons = [2021, 2022, 2023, 2024, 2025]

    # Check which batter-seasons we already have
    existing_batter_seasons = set()
    if existing_logs > 0:
        rows = conn.execute(
            "SELECT DISTINCT batter_id, season FROM mlb_batter_game_logs"
        ).fetchall()
        existing_batter_seasons = {(r[0], r[1]) for r in rows}
        print(f"Already have {len(existing_batter_seasons)} batter-seasons")

    # Phase 1: Collect all player IDs from rosters
    print("\n=== Phase 1: Collecting player IDs from rosters ===")
    batter_seasons = {}  # batter_id -> set of seasons
    total_players = 0

    for season in seasons:
        season_players = set()
        for team_id in team_ids:
            players = get_roster_player_ids(team_id, season)
            for pid in players:
                season_players.add(pid)
                batter_seasons.setdefault(pid, set()).add(season)
            time.sleep(0.1)

        total_players += len(season_players)
        print(f"  {season}: {len(season_players)} position players")

    all_batters = set(batter_seasons.keys())
    print(f"\nTotal unique batters: {len(all_batters)}")

    # Phase 2: Fetch game logs
    print("\n=== Phase 2: Fetching batter game logs ===")
    to_fetch = []
    for bid in all_batters:
        for season in batter_seasons.get(bid, []):
            if (bid, season) not in existing_batter_seasons:
                to_fetch.append((bid, season))

    print(f"Batter-seasons to fetch: {len(to_fetch)}")

    fetched = 0
    errors = 0
    total_logs = 0

    for bid, season in to_fetch:
        try:
            logs = fetch_batter_game_log(bid, season)
            for log in logs:
                conn.execute("""
                    INSERT OR IGNORE INTO mlb_batter_game_logs
                    (batter_id, batter_name, game_date, season, team,
                     at_bats, plate_appearances, hits, doubles, triples,
                     home_runs, rbi, runs, walks, strikeouts, stolen_bases,
                     total_bases)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (log["batter_id"], log["batter_name"], log["game_date"],
                      log["season"], log["team"], log["at_bats"],
                      log["plate_appearances"], log["hits"], log["doubles"],
                      log["triples"], log["home_runs"], log["rbi"],
                      log["runs"], log["walks"], log["strikeouts"],
                      log["stolen_bases"], log["total_bases"]))

            total_logs += len(logs)
            fetched += 1

            if fetched % 100 == 0:
                conn.commit()
                print(f"    Fetched {fetched}/{len(to_fetch)} batter-seasons "
                      f"({total_logs} logs, {errors} errors)")

            time.sleep(0.15)  # Rate limit

        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"    Error fetching batter {bid} season {season}: {e}")
            time.sleep(0.5)

    conn.commit()

    final_count = conn.execute(
        "SELECT COUNT(*) FROM mlb_batter_game_logs"
    ).fetchone()[0]
    unique_batters = conn.execute(
        "SELECT COUNT(DISTINCT batter_id) FROM mlb_batter_game_logs"
    ).fetchone()[0]

    print(f"\n=== Summary ===")
    print(f"Total batter game log entries: {final_count}")
    print(f"Unique batters: {unique_batters}")
    print(f"Fetched: {fetched}, Errors: {errors}")

    for season in seasons:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM mlb_batter_game_logs WHERE season=?",
            (season,)
        ).fetchone()[0]
        players = conn.execute(
            "SELECT COUNT(DISTINCT batter_id) FROM mlb_batter_game_logs WHERE season=?",
            (season,)
        ).fetchone()[0]
        print(f"  {season}: {cnt} logs, {players} batters")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()

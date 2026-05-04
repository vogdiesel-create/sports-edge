#!/usr/bin/env python3
"""
Fetch historical starting pitcher data for MLB backtest enrichment.

Collects:
1. Starting pitcher for every MLB game (2021-2025) via schedule API
2. Game logs for each pitcher to compute rolling stats

Stores in game_lines.db:
- mlb_game_starters: maps each game (date + home + away) to starting pitchers
- mlb_pitcher_game_logs: per-start stats for rolling feature computation
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta

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

# Full names used in Pinnacle data
MLB_FULL_TO_ABBREV = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL", "Detroit Tigers": "DET",
    "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH",
    "Cleveland Indians": "CLE",
}


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mlb_game_starters (
            game_date TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_pitcher_id INTEGER,
            home_pitcher_name TEXT,
            away_pitcher_id INTEGER,
            away_pitcher_name TEXT,
            game_pk INTEGER,
            UNIQUE(game_date, home_team, away_team)
        );

        CREATE TABLE IF NOT EXISTS mlb_pitcher_game_logs (
            pitcher_id INTEGER NOT NULL,
            pitcher_name TEXT,
            game_date TEXT NOT NULL,
            season INTEGER,
            team TEXT,
            innings_pitched REAL,
            hits_allowed INTEGER,
            earned_runs INTEGER,
            walks INTEGER,
            strikeouts INTEGER,
            home_runs_allowed INTEGER,
            pitches_thrown INTEGER,
            game_started INTEGER DEFAULT 1,
            UNIQUE(pitcher_id, game_date)
        );

        CREATE INDEX IF NOT EXISTS idx_starters_date ON mlb_game_starters(game_date);
        CREATE INDEX IF NOT EXISTS idx_starters_teams ON mlb_game_starters(home_team, away_team);
        CREATE INDEX IF NOT EXISTS idx_pitcher_logs ON mlb_pitcher_game_logs(pitcher_id, game_date);
    """)
    conn.commit()


def fetch_starters_for_range(start_date, end_date):
    """Fetch starting pitchers for a date range from MLB schedule API."""
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "sportId": 1,
        "hydrate": "probablePitcher",
        "gameType": "R",  # Regular season only
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            if game.get("status", {}).get("abstractGameState") != "Final":
                continue

            home_team = game["teams"]["home"]["team"]
            away_team = game["teams"]["away"]["team"]

            home_abbr = MLB_TEAM_ID_TO_ABBREV.get(home_team["id"])
            away_abbr = MLB_TEAM_ID_TO_ABBREV.get(away_team["id"])
            if not home_abbr or not away_abbr:
                continue

            hp = game["teams"]["home"].get("probablePitcher", {})
            ap = game["teams"]["away"].get("probablePitcher", {})

            results.append({
                "game_date": game["officialDate"],
                "home_team": home_abbr,
                "away_team": away_abbr,
                "home_pitcher_id": hp.get("id"),
                "home_pitcher_name": hp.get("fullName"),
                "away_pitcher_id": ap.get("id"),
                "away_pitcher_name": ap.get("fullName"),
                "game_pk": game["gamePk"],
            })

    return results


def fetch_pitcher_game_log(pitcher_id, season):
    """Fetch a pitcher's game log for a season."""
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {"stats": "gameLog", "season": season, "group": "pitching"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    logs = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        stat = split.get("stat", {})
        team = split.get("team", {})
        team_id = team.get("id")
        team_abbr = MLB_TEAM_ID_TO_ABBREV.get(team_id, "?")

        # Parse innings pitched (e.g., "6.2" means 6 and 2/3)
        ip_str = stat.get("inningsPitched", "0")
        try:
            parts = str(ip_str).split(".")
            ip = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            ip = 0

        logs.append({
            "pitcher_id": pitcher_id,
            "pitcher_name": split.get("player", {}).get("fullName"),
            "game_date": split.get("date"),
            "season": season,
            "team": team_abbr,
            "innings_pitched": round(ip, 2),
            "hits_allowed": stat.get("hits", 0),
            "earned_runs": stat.get("earnedRuns", 0),
            "walks": stat.get("baseOnBalls", 0),
            "strikeouts": stat.get("strikeOuts", 0),
            "home_runs_allowed": stat.get("homeRuns", 0),
            "pitches_thrown": stat.get("numberOfPitches", 0),
            "game_started": 1 if stat.get("gamesStarted", 0) > 0 else 0,
        })

    return logs


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Check what we already have
    existing = conn.execute("SELECT COUNT(*) FROM mlb_game_starters").fetchone()[0]
    print(f"Existing starter records: {existing}")

    # Seasons to fetch
    seasons = [
        (2021, "2021-04-01", "2021-10-03"),
        (2022, "2022-04-07", "2022-10-05"),
        (2023, "2023-03-30", "2023-10-01"),
        (2024, "2024-03-20", "2024-09-29"),
        (2025, "2025-03-27", "2025-09-28"),
    ]

    # Phase 1: Fetch all game starters
    print("\n=== Phase 1: Fetching game starters ===")
    all_pitcher_ids = set()
    pitcher_seasons = {}  # pitcher_id -> set of seasons they pitched in

    for season, start, end in seasons:
        # Check if we already have this season
        count = conn.execute(
            "SELECT COUNT(*) FROM mlb_game_starters WHERE game_date BETWEEN ? AND ?",
            (start, end)
        ).fetchone()[0]
        if count > 500:
            print(f"  {season}: already have {count} games, loading pitcher IDs...")
            rows = conn.execute(
                "SELECT DISTINCT home_pitcher_id, away_pitcher_id FROM mlb_game_starters WHERE game_date BETWEEN ? AND ?",
                (start, end)
            ).fetchall()
            for r in rows:
                if r[0]:
                    all_pitcher_ids.add(r[0])
                    pitcher_seasons.setdefault(r[0], set()).add(season)
                if r[1]:
                    all_pitcher_ids.add(r[1])
                    pitcher_seasons.setdefault(r[1], set()).add(season)
            continue

        print(f"  {season}: fetching starters...")
        # Fetch in 2-week chunks to avoid API limits
        current = datetime.strptime(start, "%Y-%m-%d")
        season_end = datetime.strptime(end, "%Y-%m-%d")
        season_total = 0

        while current <= season_end:
            chunk_end = min(current + timedelta(days=13), season_end)
            try:
                games = fetch_starters_for_range(
                    current.strftime("%Y-%m-%d"),
                    chunk_end.strftime("%Y-%m-%d")
                )
                for g in games:
                    conn.execute("""
                        INSERT OR IGNORE INTO mlb_game_starters
                        (game_date, home_team, away_team, home_pitcher_id, home_pitcher_name,
                         away_pitcher_id, away_pitcher_name, game_pk)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (g["game_date"], g["home_team"], g["away_team"],
                          g["home_pitcher_id"], g["home_pitcher_name"],
                          g["away_pitcher_id"], g["away_pitcher_name"],
                          g["game_pk"]))

                    if g["home_pitcher_id"]:
                        all_pitcher_ids.add(g["home_pitcher_id"])
                        pitcher_seasons.setdefault(g["home_pitcher_id"], set()).add(season)
                    if g["away_pitcher_id"]:
                        all_pitcher_ids.add(g["away_pitcher_id"])
                        pitcher_seasons.setdefault(g["away_pitcher_id"], set()).add(season)

                season_total += len(games)
            except Exception as e:
                print(f"    Error fetching {current.strftime('%Y-%m-%d')}: {e}")

            current = chunk_end + timedelta(days=1)
            time.sleep(0.3)  # Rate limiting

        conn.commit()
        print(f"    Saved {season_total} games for {season}")

    total_starters = conn.execute("SELECT COUNT(*) FROM mlb_game_starters").fetchone()[0]
    print(f"\nTotal game starter records: {total_starters}")
    print(f"Unique pitchers: {len(all_pitcher_ids)}")

    # Phase 2: Fetch game logs for all pitchers
    print("\n=== Phase 2: Fetching pitcher game logs ===")
    existing_logs = conn.execute("SELECT COUNT(*) FROM mlb_pitcher_game_logs").fetchone()[0]
    print(f"Existing game log entries: {existing_logs}")

    # Check which pitcher-seasons we already have
    existing_pitcher_seasons = set()
    if existing_logs > 0:
        rows = conn.execute(
            "SELECT DISTINCT pitcher_id, season FROM mlb_pitcher_game_logs"
        ).fetchall()
        existing_pitcher_seasons = {(r[0], r[1]) for r in rows}

    pitchers_to_fetch = []
    for pid in all_pitcher_ids:
        for season in pitcher_seasons.get(pid, []):
            if (pid, season) not in existing_pitcher_seasons:
                pitchers_to_fetch.append((pid, season))

    print(f"Pitcher-seasons to fetch: {len(pitchers_to_fetch)}")

    fetched = 0
    errors = 0
    for pid, season in pitchers_to_fetch:
        try:
            logs = fetch_pitcher_game_log(pid, season)
            for log in logs:
                conn.execute("""
                    INSERT OR IGNORE INTO mlb_pitcher_game_logs
                    (pitcher_id, pitcher_name, game_date, season, team,
                     innings_pitched, hits_allowed, earned_runs, walks,
                     strikeouts, home_runs_allowed, pitches_thrown, game_started)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (log["pitcher_id"], log["pitcher_name"], log["game_date"],
                      log["season"], log["team"], log["innings_pitched"],
                      log["hits_allowed"], log["earned_runs"], log["walks"],
                      log["strikeouts"], log["home_runs_allowed"],
                      log["pitches_thrown"], log["game_started"]))

            fetched += 1
            if fetched % 50 == 0:
                conn.commit()
                print(f"    Fetched {fetched}/{len(pitchers_to_fetch)} pitcher-seasons ({errors} errors)")
                time.sleep(0.5)
            time.sleep(0.15)  # Rate limit

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    Error fetching pitcher {pid} season {season}: {e}")

    conn.commit()

    total_logs = conn.execute("SELECT COUNT(*) FROM mlb_pitcher_game_logs").fetchone()[0]
    print(f"\nTotal game log entries: {total_logs}")
    print(f"Fetched: {fetched}, Errors: {errors}")

    # Summary
    print("\n=== Summary ===")
    for season, start, end in seasons:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM mlb_game_starters WHERE game_date BETWEEN ? AND ?",
            (start, end)
        ).fetchone()[0]
        with_both = conn.execute(
            "SELECT COUNT(*) FROM mlb_game_starters WHERE game_date BETWEEN ? AND ? AND home_pitcher_id IS NOT NULL AND away_pitcher_id IS NOT NULL",
            (start, end)
        ).fetchone()[0]
        print(f"  {season}: {cnt} games, {with_both} with both starters ({100*with_both/max(cnt,1):.1f}%)")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()

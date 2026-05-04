#!/usr/bin/env python3
"""
Daily refresh of 2026 MLB batter and pitcher game logs.

Lightweight incremental script - only fetches data newer than what's in the DB.
Uses active rosters (not fullSeason) since the 2026 season is in progress.

Run daily before edge_detector.py to ensure prop models have fresh data.
"""

import os
import sqlite3
import time

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")
SEASON = 2026

MLB_TEAM_ID_TO_ABBREV = {
    108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
    118: "KC",  119: "LAD", 120: "WSH", 121: "NYM", 133: "OAK",
    134: "PIT", 135: "SD",  136: "SEA", 137: "SF",  138: "STL",
    139: "TB",  140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
    144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}

TEAM_IDS = list(MLB_TEAM_ID_TO_ABBREV.keys())


def get_active_roster(team_id):
    """Get active roster player IDs split into batters and pitchers."""
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    params = {"rosterType": "active", "season": SEASON}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        batters = []
        pitchers = []
        for entry in data.get("roster", []):
            pid = entry["person"]["id"]
            pos = entry.get("position", {}).get("abbreviation", "")
            if pos == "P":
                pitchers.append(pid)
            else:
                batters.append(pid)
        return batters, pitchers
    except Exception:
        return [], []


def fetch_batter_game_log(batter_id):
    """Fetch a batter's 2026 game log."""
    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats"
    params = {"stats": "gameLog", "season": SEASON, "group": "hitting"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    logs = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        stat = split.get("stat", {})
        team = split.get("team", {})
        team_abbr = MLB_TEAM_ID_TO_ABBREV.get(team.get("id"), "?")

        ab = stat.get("atBats", 0)
        if ab == 0:
            continue

        h = stat.get("hits", 0)
        doubles = stat.get("doubles", 0)
        triples = stat.get("triples", 0)
        hr = stat.get("homeRuns", 0)
        singles = h - doubles - triples - hr
        tb = singles + 2 * doubles + 3 * triples + 4 * hr

        logs.append((
            batter_id, split.get("player", {}).get("fullName"),
            split.get("date"), SEASON, team_abbr,
            ab, stat.get("plateAppearances", ab), h, doubles, triples,
            hr, stat.get("rbi", 0), stat.get("runs", 0),
            stat.get("baseOnBalls", 0), stat.get("strikeOuts", 0),
            stat.get("stolenBases", 0), tb,
        ))
    return logs


def fetch_pitcher_game_log(pitcher_id):
    """Fetch a pitcher's 2026 game log."""
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {"stats": "gameLog", "season": SEASON, "group": "pitching"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    logs = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        stat = split.get("stat", {})
        team = split.get("team", {})
        team_abbr = MLB_TEAM_ID_TO_ABBREV.get(team.get("id"), "?")

        ip_str = stat.get("inningsPitched", "0")
        try:
            parts = str(ip_str).split(".")
            ip = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            ip = 0

        logs.append((
            pitcher_id, split.get("player", {}).get("fullName"),
            split.get("date"), SEASON, team_abbr,
            round(ip, 2), stat.get("hits", 0), stat.get("earnedRuns", 0),
            stat.get("baseOnBalls", 0), stat.get("strikeOuts", 0),
            stat.get("homeRuns", 0), stat.get("numberOfPitches", 0),
            1 if stat.get("gamesStarted", 0) > 0 else 0,
        ))
    return logs


def main():
    conn = sqlite3.connect(DB_PATH, timeout=15)

    # Ensure tables exist
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mlb_batter_game_logs (
            batter_id INTEGER NOT NULL, batter_name TEXT,
            game_date TEXT NOT NULL, season INTEGER, team TEXT,
            at_bats INTEGER, plate_appearances INTEGER, hits INTEGER,
            doubles INTEGER, triples INTEGER, home_runs INTEGER,
            rbi INTEGER, runs INTEGER, walks INTEGER, strikeouts INTEGER,
            stolen_bases INTEGER, total_bases INTEGER,
            UNIQUE(batter_id, game_date)
        );
        CREATE TABLE IF NOT EXISTS mlb_pitcher_game_logs (
            pitcher_id INTEGER NOT NULL, pitcher_name TEXT,
            game_date TEXT NOT NULL, season INTEGER, team TEXT,
            innings_pitched REAL, hits_allowed INTEGER, earned_runs INTEGER,
            walks INTEGER, strikeouts INTEGER, home_runs_allowed INTEGER,
            pitches_thrown INTEGER, game_started INTEGER,
            UNIQUE(pitcher_id, game_date)
        );
    """)

    # Current counts
    batter_before = conn.execute(
        "SELECT COUNT(*) FROM mlb_batter_game_logs WHERE season=?", (SEASON,)
    ).fetchone()[0]
    pitcher_before = conn.execute(
        "SELECT COUNT(*) FROM mlb_pitcher_game_logs WHERE season=?", (SEASON,)
    ).fetchone()[0]

    print(f"Before: {batter_before} batter logs, {pitcher_before} pitcher logs (2026)")

    # Phase 1: Collect active roster player IDs
    all_batters = set()
    all_pitchers = set()
    for team_id in TEAM_IDS:
        batters, pitchers = get_active_roster(team_id)
        all_batters.update(batters)
        all_pitchers.update(pitchers)
        time.sleep(0.05)

    print(f"Active rosters: {len(all_batters)} batters, {len(all_pitchers)} pitchers")

    # Phase 2: Fetch batter game logs
    batter_new = 0
    batter_errors = 0
    for i, bid in enumerate(all_batters):
        try:
            logs = fetch_batter_game_log(bid)
            for log in logs:
                conn.execute("""
                    INSERT OR IGNORE INTO mlb_batter_game_logs
                    (batter_id, batter_name, game_date, season, team,
                     at_bats, plate_appearances, hits, doubles, triples,
                     home_runs, rbi, runs, walks, strikeouts, stolen_bases,
                     total_bases) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, log)
            batter_new += len(logs)
            if (i + 1) % 100 == 0:
                conn.commit()
                print(f"  Batters: {i+1}/{len(all_batters)}")
            time.sleep(0.1)
        except Exception as e:
            batter_errors += 1
            if batter_errors <= 5:
                print(f"  Batter error {bid}: {e}")
            time.sleep(0.3)

    conn.commit()

    # Phase 3: Fetch pitcher game logs
    pitcher_new = 0
    pitcher_errors = 0
    for i, pid in enumerate(all_pitchers):
        try:
            logs = fetch_pitcher_game_log(pid)
            for log in logs:
                conn.execute("""
                    INSERT OR IGNORE INTO mlb_pitcher_game_logs
                    (pitcher_id, pitcher_name, game_date, season, team,
                     innings_pitched, hits_allowed, earned_runs, walks,
                     strikeouts, home_runs_allowed, pitches_thrown,
                     game_started) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, log)
            pitcher_new += len(logs)
            if (i + 1) % 100 == 0:
                conn.commit()
                print(f"  Pitchers: {i+1}/{len(all_pitchers)}")
            time.sleep(0.1)
        except Exception as e:
            pitcher_errors += 1
            if pitcher_errors <= 5:
                print(f"  Pitcher error {pid}: {e}")
            time.sleep(0.3)

    conn.commit()

    # Summary
    batter_after = conn.execute(
        "SELECT COUNT(*) FROM mlb_batter_game_logs WHERE season=?", (SEASON,)
    ).fetchone()[0]
    pitcher_after = conn.execute(
        "SELECT COUNT(*) FROM mlb_pitcher_game_logs WHERE season=?", (SEASON,)
    ).fetchone()[0]

    print(f"\nAfter: {batter_after} batter logs (+{batter_after - batter_before}), "
          f"{pitcher_after} pitcher logs (+{pitcher_after - pitcher_before})")
    print(f"Errors: {batter_errors} batter, {pitcher_errors} pitcher")

    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()

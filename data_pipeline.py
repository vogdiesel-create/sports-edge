#!/usr/bin/env python3
"""
Sports Edge - Daily Data Pipeline

Collects data the model needs but doesn't currently have:
1. NHL goalie starts (confirmed vs probable)
2. MLB starting pitchers + season stats
3. MLB weather data
4. Opening/closing line snapshots

Run daily BEFORE edge_detector.py to enrich predictions.
Run AFTER games complete to store confirmed starters for historical data.
"""

import json
import os
import sqlite3
import requests
from datetime import datetime, timezone, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables(conn):
    """Create tables for supplementary data if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nhl_goalies (
            game_id TEXT,
            game_date TEXT,
            team TEXT,
            goalie_name TEXT,
            goalie_id INTEGER,
            status TEXT,  -- 'probable', 'confirmed', 'started'
            fetched_at TEXT,
            PRIMARY KEY (game_id, team, fetched_at)
        );

        CREATE TABLE IF NOT EXISTS mlb_pitchers (
            game_id INTEGER,
            game_date TEXT,
            team TEXT,
            pitcher_name TEXT,
            pitcher_id INTEGER,
            era REAL,
            whip REAL,
            innings_pitched REAL,
            k_per_9 REAL,
            bb_per_9 REAL,
            status TEXT,  -- 'probable', 'confirmed'
            fetched_at TEXT,
            PRIMARY KEY (game_id, team, fetched_at)
        );

        CREATE TABLE IF NOT EXISTS line_snapshots (
            game_id TEXT,
            sport TEXT,
            game_date TEXT,
            snapshot_time TEXT,
            source TEXT,
            total_line REAL,
            over_odds INTEGER,
            under_odds INTEGER,
            PRIMARY KEY (game_id, snapshot_time, source)
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# NHL GOALIE STARTS
# ---------------------------------------------------------------------------

def fetch_nhl_goalies(date_str: str = None) -> list:
    """Fetch probable/confirmed goalie starts from NHL API."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    results = []
    now = datetime.now(timezone.utc).isoformat()

    try:
        r = requests.get(
            f"https://api-web.nhle.com/v1/schedule/{date_str}",
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [GOALIES] NHL schedule fetch failed: {e}")
        return results

    for day in data.get("gameWeek", []):
        if day["date"] != date_str:
            continue
        for game in day.get("games", []):
            game_id = str(game["id"])
            try:
                r2 = requests.get(
                    f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing",
                    timeout=15
                )
                r2.raise_for_status()
                gd = r2.json()
            except Exception:
                continue

            for side in ["homeTeam", "awayTeam"]:
                team = gd.get(side, {})
                abbrev = team.get("abbrev", "UNK")

                # Try multiple fields for goalie info
                goalie_name = None
                goalie_id = None
                status = "unknown"

                # Check for starting goalie (confirmed)
                sg = team.get("startingGoalie") or team.get("probableGoalie")
                if sg:
                    goalie_name = f"{sg.get('firstName', {}).get('default', '')} {sg.get('lastName', {}).get('default', '')}".strip()
                    goalie_id = sg.get("id")
                    status = "confirmed" if "startingGoalie" in team else "probable"

                if goalie_name:
                    results.append({
                        "game_id": game_id,
                        "game_date": date_str,
                        "team": abbrev,
                        "goalie_name": goalie_name,
                        "goalie_id": goalie_id,
                        "status": status,
                        "fetched_at": now,
                    })

    return results


def store_nhl_goalies(conn, goalies: list):
    """Store goalie data in DB."""
    for g in goalies:
        conn.execute("""
            INSERT OR REPLACE INTO nhl_goalies
            (game_id, game_date, team, goalie_name, goalie_id, status, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (g["game_id"], g["game_date"], g["team"],
              g["goalie_name"], g["goalie_id"], g["status"], g["fetched_at"]))
    conn.commit()


# ---------------------------------------------------------------------------
# MLB STARTING PITCHERS
# ---------------------------------------------------------------------------

def fetch_mlb_pitchers(date_str: str = None) -> list:
    """Fetch probable starting pitchers from MLB Stats API."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    results = []
    now = datetime.now(timezone.utc).isoformat()

    try:
        r = requests.get(
            f"https://statsapi.mlb.com/api/v1/schedule",
            params={
                "sportId": 1,
                "date": date_str,
                "hydrate": "probablePitcher(note)"
            },
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [PITCHERS] MLB schedule fetch failed: {e}")
        return results

    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            game_id = game["gamePk"]
            game_date = date_entry["date"]

            for side in ["away", "home"]:
                team_data = game["teams"][side]
                team_name = team_data["team"]["name"]
                pitcher = team_data.get("probablePitcher", {})

                if pitcher:
                    # Fetch pitcher season stats
                    pid = pitcher.get("id")
                    era, whip, ip, k9, bb9 = None, None, None, None, None

                    if pid:
                        try:
                            sr = requests.get(
                                f"https://statsapi.mlb.com/api/v1/people/{pid}",
                                params={"hydrate": "currentTeam,stats(type=season)"},
                                timeout=10
                            )
                            sr.raise_for_status()
                            pdata = sr.json()
                            for person in pdata.get("people", []):
                                for stat_group in person.get("stats", []):
                                    for split in stat_group.get("splits", []):
                                        s = split.get("stat", {})
                                        era = _safe_float(s.get("era"))
                                        whip = _safe_float(s.get("whip"))
                                        ip = _safe_float(s.get("inningsPitched"))
                                        k9 = _safe_float(s.get("strikeoutsPer9Inn"))
                                        bb9 = _safe_float(s.get("walksPer9Inn"))
                        except Exception:
                            pass

                    results.append({
                        "game_id": game_id,
                        "game_date": game_date,
                        "team": team_name,
                        "pitcher_name": pitcher.get("fullName", "TBD"),
                        "pitcher_id": pid,
                        "era": era,
                        "whip": whip,
                        "innings_pitched": ip,
                        "k_per_9": k9,
                        "bb_per_9": bb9,
                        "status": "probable",
                        "fetched_at": now,
                    })

    return results


def store_mlb_pitchers(conn, pitchers: list):
    """Store pitcher data in DB."""
    for p in pitchers:
        conn.execute("""
            INSERT OR REPLACE INTO mlb_pitchers
            (game_id, game_date, team, pitcher_name, pitcher_id,
             era, whip, innings_pitched, k_per_9, bb_per_9, status, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p["game_id"], p["game_date"], p["team"], p["pitcher_name"],
              p["pitcher_id"], p["era"], p["whip"], p["innings_pitched"],
              p["k_per_9"], p["bb_per_9"], p["status"], p["fetched_at"]))
    conn.commit()


def _safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# LINE SNAPSHOTS (opening/closing tracking)
# ---------------------------------------------------------------------------

def snapshot_current_lines(conn):
    """Take a snapshot of current Pinnacle lines for today's games.
    Run multiple times per day to track movement."""
    now = datetime.now(timezone.utc)
    now_str = now.isoformat()
    today = now.strftime("%Y-%m-%d")

    # Read totals from game_odds, group by game to get over+under for each book
    rows = conn.execute("""
        SELECT game, sport, market, book, line, odds, side
        FROM game_odds
        WHERE market = 'total' AND timestamp >= ?
        ORDER BY game, book
    """, (today,)).fetchall()

    # Group into game+book pairs
    games = {}
    for row in rows:
        key = (row["game"], row["book"])
        if key not in games:
            games[key] = {"game": row["game"], "sport": row["sport"],
                          "book": row["book"], "line": row["line"]}
        if row["side"] == "over":
            games[key]["over_odds"] = row["odds"]
        elif row["side"] == "under":
            games[key]["under_odds"] = row["odds"]

    stored = 0
    for key, g in games.items():
        if "over_odds" in g and "under_odds" in g:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO line_snapshots
                    (game_id, sport, game_date, snapshot_time, source,
                     total_line, over_odds, under_odds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (g["game"], g["sport"], today, now_str, g["book"],
                      g["line"], g["over_odds"], g["under_odds"]))
                stored += 1
            except Exception:
                pass
    conn.commit()
    return stored


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def run_pipeline(date_str: str = None):
    """Run the full daily data pipeline."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"\n  Data Pipeline - {date_str}")
    print("=" * 50)

    conn = get_db()
    init_tables(conn)

    # 1. NHL Goalies
    goalies = fetch_nhl_goalies(date_str)
    if goalies:
        store_nhl_goalies(conn, goalies)
        print(f"  [GOALIES] Stored {len(goalies)} goalie records")
        for g in goalies:
            print(f"    {g['team']}: {g['goalie_name']} ({g['status']})")
    else:
        print(f"  [GOALIES] No goalie data found for {date_str}")

    # 2. MLB Pitchers
    pitchers = fetch_mlb_pitchers(date_str)
    if pitchers:
        store_mlb_pitchers(conn, pitchers)
        print(f"  [PITCHERS] Stored {len(pitchers)} pitcher records")
        for p in pitchers:
            era_str = f"ERA {p['era']:.2f}" if p['era'] else "no stats"
            print(f"    {p['team']}: {p['pitcher_name']} ({era_str})")
    else:
        print(f"  [PITCHERS] No pitcher data found for {date_str}")

    # 3. Line snapshots
    n_snaps = snapshot_current_lines(conn)
    print(f"  [LINES] Stored {n_snaps} line snapshots")

    conn.close()
    print(f"\n  Pipeline complete.")


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_pipeline(date_arg)

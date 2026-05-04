#!/usr/bin/env python3
"""
MLB Data Pipeline for Sports Edge Predictive Modeling

Ingests MLB data from free public sources into SQLite for predictive modeling.
Sources: MLB Stats API, pybaseball (Statcast), Open-Meteo weather API.

Usage:
    python3 mlb_data_pipeline.py                # Full pipeline update
    python3 mlb_data_pipeline.py schedule        # Schedule only
    python3 mlb_data_pipeline.py standings       # Standings only
    python3 mlb_data_pipeline.py pitchers        # Pitcher stats only
    python3 mlb_data_pipeline.py batters         # Batter stats only
    python3 mlb_data_pipeline.py weather         # Weather for upcoming games
    python3 mlb_data_pipeline.py features        # Compute all features
    python3 mlb_data_pipeline.py game LAD NYY    # Features for specific matchup
"""

import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# pybaseball lazy import -- install automatically if missing
# Statcast features are optional; core pipeline works without pybaseball.
# ---------------------------------------------------------------------------
pb = None
try:
    import pybaseball as pb
    pb.cache.enable()
except ImportError:
    try:
        print("[SETUP] pybaseball not found -- installing now...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--break-system-packages", "pybaseball", "-q"],
            stderr=subprocess.DEVNULL,
        )
        import pybaseball as pb
        pb.cache.enable()
    except Exception:
        print("[WARN] pybaseball not available -- Statcast enrichment will be skipped.")
        print("[WARN] Install manually: pip install pybaseball --break-system-packages")

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sports_edge.db")
os.makedirs(DATA_DIR, exist_ok=True)

MLB_API = "https://statsapi.mlb.com/api/v1"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"

CURRENT_SEASON = datetime.now().year

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MLB] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mlb_pipeline")

# ---------------------------------------------------------------------------
# MLB Stadium Data (all 30 parks)
# Fields: (name, team_abbrev, mlb_team_id, lat, lon, is_dome, park_factor_runs)
# Park factors are approximate run factors (1.00 = neutral).
# ---------------------------------------------------------------------------
MLB_STADIUMS = [
    ("Angel Stadium",            "LAA", 108, 33.8003, -117.8827, False, 0.97),
    ("Chase Field",              "ARI", 109, 33.4455, -112.0667, True,  1.06),
    ("Citi Field",               "NYM", 121, 40.7571, -73.8458,  False, 0.93),
    ("Citizens Bank Park",       "PHI", 143, 39.9061, -75.1665,  False, 1.05),
    ("Comerica Park",            "DET", 116, 42.3390, -83.0485,  False, 0.95),
    ("Coors Field",              "COL", 115, 39.7559, -104.9942, False, 1.28),
    ("Dodger Stadium",           "LAD", 119, 34.0739, -118.2400, False, 0.98),
    ("Fenway Park",              "BOS", 111, 42.3467, -71.0972,  False, 1.08),
    ("Globe Life Field",         "TEX", 140, 32.7473, -97.0845,  True,  1.02),
    ("Great American Ball Park", "CIN", 113, 39.0974, -84.5082,  False, 1.10),
    ("Guaranteed Rate Field",    "CWS", 145, 41.8299, -87.6338,  False, 1.04),
    ("Kauffman Stadium",         "KC",  118, 39.0517, -94.4803,  False, 0.98),
    ("LoanDepot Park",           "MIA", 146, 25.7781, -80.2196,  True,  0.92),
    ("Minute Maid Park",         "HOU", 117, 29.7573, -95.3555,  True,  1.03),
    ("Nationals Park",           "WSH", 120, 38.8730, -77.0074,  False, 1.00),
    ("Oakland Coliseum",         "OAK", 133, 37.7516, -122.2005, False, 0.93),
    ("Oracle Park",              "SF",  137, 37.7786, -122.3893, False, 0.90),
    ("Oriole Park at Camden Yards", "BAL", 110, 39.2838, -76.6218, False, 1.05),
    ("PNC Park",                 "PIT", 134, 40.4469, -80.0057,  False, 0.94),
    ("Petco Park",               "SD",  135, 32.7076, -117.1570, False, 0.93),
    ("Progressive Field",        "CLE", 114, 41.4962, -81.6852,  False, 0.96),
    ("Rogers Centre",            "TOR", 141, 43.6414, -79.3894,  True,  1.02),
    ("T-Mobile Park",            "SEA", 136, 47.5914, -122.3325, True,  0.93),
    ("Target Field",             "MIN", 142, 44.9818, -93.2775,  False, 1.01),
    ("Tropicana Field",          "TB",  139, 27.7682, -82.6534,  True,  0.91),
    ("Truist Park",              "ATL", 144, 33.8907, -84.4677,  False, 1.01),
    ("Wrigley Field",            "CHC", 112, 41.9484, -87.6553,  False, 1.05),
    ("Yankee Stadium",           "NYY", 147, 40.8296, -73.9262,  False, 1.09),
    ("Busch Stadium",            "STL", 138, 38.6226, -90.1928,  False, 0.96),
    ("American Family Field",    "MIL", 158, 43.0280, -87.9712,  True,  1.02),
]

# Build lookup dicts
STADIUM_BY_TEAM_ID = {s[2]: s for s in MLB_STADIUMS}
STADIUM_BY_ABBREV = {s[1]: s for s in MLB_STADIUMS}

# MLB team abbreviation by team id
TEAM_ABBREV_BY_ID = {s[2]: s[1] for s in MLB_STADIUMS}

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a connection to the shared sports_edge.db with MLB tables created."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS mlb_stadiums (
        team_abbrev TEXT PRIMARY KEY,
        stadium_name TEXT,
        mlb_team_id INTEGER,
        latitude REAL,
        longitude REAL,
        is_dome INTEGER,
        park_factor_runs REAL
    );

    CREATE TABLE IF NOT EXISTS mlb_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER,
        team_id INTEGER,
        team_abbrev TEXT,
        team_name TEXT,
        division TEXT,
        wins INTEGER,
        losses INTEGER,
        pct REAL,
        runs_scored INTEGER,
        runs_allowed INTEGER,
        run_diff INTEGER,
        streak TEXT,
        last_10_w INTEGER,
        last_10_l INTEGER,
        updated_at TEXT,
        UNIQUE(season, team_id)
    );

    CREATE TABLE IF NOT EXISTS mlb_pitchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER,
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbrev TEXT,
        games INTEGER DEFAULT 0,
        games_started INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        era REAL,
        fip REAL,
        xfip REAL,
        whip REAL,
        innings_pitched REAL DEFAULT 0,
        strikeouts INTEGER DEFAULT 0,
        walks INTEGER DEFAULT 0,
        hits_allowed INTEGER DEFAULT 0,
        home_runs_allowed INTEGER DEFAULT 0,
        k_per_9 REAL,
        bb_per_9 REAL,
        hr_per_9 REAL,
        batting_avg_against REAL,
        -- Statcast metrics (nullable until populated)
        avg_fastball_velo REAL,
        avg_spin_rate REAL,
        whiff_pct REAL,
        hard_hit_pct_against REAL,
        barrel_pct_against REAL,
        xera REAL,
        updated_at TEXT,
        UNIQUE(season, player_id)
    );

    CREATE TABLE IF NOT EXISTS mlb_batters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER,
        player_id INTEGER,
        player_name TEXT,
        team_id INTEGER,
        team_abbrev TEXT,
        games INTEGER DEFAULT 0,
        plate_appearances INTEGER DEFAULT 0,
        at_bats INTEGER DEFAULT 0,
        hits INTEGER DEFAULT 0,
        doubles INTEGER DEFAULT 0,
        triples INTEGER DEFAULT 0,
        home_runs INTEGER DEFAULT 0,
        rbi INTEGER DEFAULT 0,
        stolen_bases INTEGER DEFAULT 0,
        batting_avg REAL,
        obp REAL,
        slg REAL,
        ops REAL,
        k_pct REAL,
        bb_pct REAL,
        -- Statcast metrics (nullable until populated)
        woba REAL,
        xwoba REAL,
        exit_velo REAL,
        launch_angle REAL,
        hard_hit_pct REAL,
        barrel_pct REAL,
        sprint_speed REAL,
        -- Splits (nullable, populated separately)
        avg_vs_lhp REAL,
        obp_vs_lhp REAL,
        slg_vs_lhp REAL,
        avg_vs_rhp REAL,
        obp_vs_rhp REAL,
        slg_vs_rhp REAL,
        updated_at TEXT,
        UNIQUE(season, player_id)
    );

    CREATE TABLE IF NOT EXISTS mlb_games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_pk INTEGER UNIQUE,
        game_date TEXT,
        status TEXT,
        home_team_id INTEGER,
        home_team_abbrev TEXT,
        away_team_id INTEGER,
        away_team_abbrev TEXT,
        home_score INTEGER,
        away_score INTEGER,
        home_pitcher_id INTEGER,
        home_pitcher_name TEXT,
        away_pitcher_id INTEGER,
        away_pitcher_name TEXT,
        innings INTEGER,
        venue_name TEXT,
        temperature REAL,
        wind_speed REAL,
        wind_direction TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS mlb_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_pk INTEGER UNIQUE,
        game_date TEXT,
        game_time TEXT,
        home_team_id INTEGER,
        home_team_abbrev TEXT,
        away_team_id INTEGER,
        away_team_abbrev TEXT,
        home_pitcher_id INTEGER,
        home_pitcher_name TEXT,
        away_pitcher_id INTEGER,
        away_pitcher_name TEXT,
        venue_name TEXT,
        status TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS mlb_weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_pk INTEGER,
        game_date TEXT,
        game_time TEXT,
        stadium_name TEXT,
        team_abbrev TEXT,
        latitude REAL,
        longitude REAL,
        temperature_f REAL,
        wind_speed_mph REAL,
        wind_direction_deg REAL,
        precipitation_mm REAL,
        humidity_pct REAL,
        weather_impact_score REAL,
        updated_at TEXT,
        UNIQUE(game_pk, game_date)
    );

    CREATE INDEX IF NOT EXISTS idx_mlb_games_date ON mlb_games(game_date);
    CREATE INDEX IF NOT EXISTS idx_mlb_games_teams ON mlb_games(home_team_id, away_team_id);
    CREATE INDEX IF NOT EXISTS idx_mlb_schedule_date ON mlb_schedule(game_date);
    CREATE INDEX IF NOT EXISTS idx_mlb_pitchers_team ON mlb_pitchers(team_id, season);
    CREATE INDEX IF NOT EXISTS idx_mlb_batters_team ON mlb_batters(team_id, season);
    """)
    conn.commit()


def _seed_stadiums(conn: sqlite3.Connection):
    """Insert or update stadium data."""
    for name, abbrev, tid, lat, lon, dome, pf in MLB_STADIUMS:
        conn.execute("""
            INSERT INTO mlb_stadiums (team_abbrev, stadium_name, mlb_team_id, latitude, longitude, is_dome, park_factor_runs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(team_abbrev) DO UPDATE SET
                stadium_name=excluded.stadium_name,
                mlb_team_id=excluded.mlb_team_id,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                is_dome=excluded.is_dome,
                park_factor_runs=excluded.park_factor_runs
        """, (abbrev, name, tid, lat, lon, int(dome), pf))
    conn.commit()
    log.info("Seeded %d MLB stadiums", len(MLB_STADIUMS))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _mlb_get(path: str, params: dict = None) -> dict:
    """GET from MLB Stats API with retry."""
    url = f"{MLB_API}{path}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt == 2:
                log.error("MLB API failed after 3 attempts: %s -- %s", url, e)
                return {}
            time.sleep(2 ** attempt)
    return {}


def _weather_get(lat: float, lon: float, date: str, hour: int = 19) -> dict:
    """Fetch hourly weather from Open-Meteo for a specific date and hour."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation,relative_humidity_2m",
        "start_date": date,
        "end_date": date,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "America/New_York",
    }
    for attempt in range(3):
        try:
            resp = requests.get(OPEN_METEO_API, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            # Find closest hour to game time
            idx = min(hour, len(times) - 1) if times else 0
            return {
                "temperature_f": hourly.get("temperature_2m", [None])[idx],
                "wind_speed_mph": hourly.get("wind_speed_10m", [None])[idx],
                "wind_direction_deg": hourly.get("wind_direction_10m", [None])[idx],
                "precipitation_mm": hourly.get("precipitation", [None])[idx],
                "humidity_pct": hourly.get("relative_humidity_2m", [None])[idx],
            }
        except requests.RequestException as e:
            if attempt == 2:
                log.warning("Weather API failed for (%s, %s): %s", lat, lon, e)
                return {}
            time.sleep(1)
    return {}


# ---------------------------------------------------------------------------
# Data download functions
# ---------------------------------------------------------------------------

def download_mlb_schedule(date: str = None, days_ahead: int = 7) -> list:
    """
    Download MLB schedule. If date is None, fetches today + days_ahead.
    Stores in mlb_schedule table and returns list of game dicts.
    """
    conn = get_db()
    now = datetime.now()
    if date:
        start = date
        end = date
    else:
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    data = _mlb_get("/schedule", {
        "sportId": 1,
        "startDate": start,
        "endDate": end,
        "hydrate": "probablePitcher,team",
    })

    games = []
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            game_pk = g.get("gamePk")
            game_date = g.get("officialDate", date_entry.get("date", ""))
            game_time = g.get("gameDate", "")  # ISO datetime

            home = g.get("teams", {}).get("home", {})
            away = g.get("teams", {}).get("away", {})
            home_team = home.get("team", {})
            away_team = away.get("team", {})

            home_pitcher = home.get("probablePitcher", {})
            away_pitcher = away.get("probablePitcher", {})

            status = g.get("status", {}).get("detailedState", "")
            venue = g.get("venue", {}).get("name", "")

            home_tid = home_team.get("id")
            away_tid = away_team.get("id")

            rec = {
                "game_pk": game_pk,
                "game_date": game_date,
                "game_time": game_time,
                "home_team_id": home_tid,
                "home_team_abbrev": TEAM_ABBREV_BY_ID.get(home_tid, home_team.get("abbreviation", "")),
                "away_team_id": away_tid,
                "away_team_abbrev": TEAM_ABBREV_BY_ID.get(away_tid, away_team.get("abbreviation", "")),
                "home_pitcher_id": home_pitcher.get("id"),
                "home_pitcher_name": home_pitcher.get("fullName"),
                "away_pitcher_id": away_pitcher.get("id"),
                "away_pitcher_name": away_pitcher.get("fullName"),
                "venue_name": venue,
                "status": status,
            }
            games.append(rec)

            # Upsert into schedule
            conn.execute("""
                INSERT INTO mlb_schedule
                    (game_pk, game_date, game_time, home_team_id, home_team_abbrev,
                     away_team_id, away_team_abbrev, home_pitcher_id, home_pitcher_name,
                     away_pitcher_id, away_pitcher_name, venue_name, status, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(game_pk) DO UPDATE SET
                    game_date=excluded.game_date, game_time=excluded.game_time,
                    home_team_id=excluded.home_team_id, home_team_abbrev=excluded.home_team_abbrev,
                    away_team_id=excluded.away_team_id, away_team_abbrev=excluded.away_team_abbrev,
                    home_pitcher_id=excluded.home_pitcher_id, home_pitcher_name=excluded.home_pitcher_name,
                    away_pitcher_id=excluded.away_pitcher_id, away_pitcher_name=excluded.away_pitcher_name,
                    venue_name=excluded.venue_name, status=excluded.status,
                    updated_at=excluded.updated_at
            """, (
                rec["game_pk"], rec["game_date"], rec["game_time"],
                rec["home_team_id"], rec["home_team_abbrev"],
                rec["away_team_id"], rec["away_team_abbrev"],
                rec["home_pitcher_id"], rec["home_pitcher_name"],
                rec["away_pitcher_id"], rec["away_pitcher_name"],
                rec["venue_name"], rec["status"],
                datetime.now().isoformat(),
            ))

            # If game is Final, also store in mlb_games
            if "Final" in status:
                home_score = home.get("score", 0)
                away_score = away.get("score", 0)
                conn.execute("""
                    INSERT INTO mlb_games
                        (game_pk, game_date, status, home_team_id, home_team_abbrev,
                         away_team_id, away_team_abbrev, home_score, away_score,
                         home_pitcher_id, home_pitcher_name, away_pitcher_id, away_pitcher_name,
                         venue_name, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(game_pk) DO UPDATE SET
                        status=excluded.status, home_score=excluded.home_score,
                        away_score=excluded.away_score, updated_at=excluded.updated_at
                """, (
                    game_pk, game_date, status,
                    rec["home_team_id"], rec["home_team_abbrev"],
                    rec["away_team_id"], rec["away_team_abbrev"],
                    home_score, away_score,
                    rec["home_pitcher_id"], rec["home_pitcher_name"],
                    rec["away_pitcher_id"], rec["away_pitcher_name"],
                    rec["venue_name"],
                    datetime.now().isoformat(),
                ))

    conn.commit()
    conn.close()
    log.info("Schedule: fetched %d games for %s to %s", len(games), start, end)
    return games


def download_mlb_game_results(start_date: str, end_date: str = None):
    """Download completed game results for a date range and store in mlb_games."""
    if end_date is None:
        end_date = start_date

    conn = get_db()
    data = _mlb_get("/schedule", {
        "sportId": 1,
        "startDate": start_date,
        "endDate": end_date,
        "hydrate": "probablePitcher,linescore,weather,team",
    })

    count = 0
    for date_entry in data.get("dates", []):
        for g in date_entry.get("games", []):
            status = g.get("status", {}).get("detailedState", "")
            if "Final" not in status:
                continue

            game_pk = g.get("gamePk")
            game_date = g.get("officialDate", date_entry.get("date", ""))
            home = g.get("teams", {}).get("home", {})
            away = g.get("teams", {}).get("away", {})
            home_team = home.get("team", {})
            away_team = away.get("team", {})
            home_pitcher = home.get("probablePitcher", {})
            away_pitcher = away.get("probablePitcher", {})
            venue = g.get("venue", {}).get("name", "")

            linescore = g.get("linescore", {})
            innings = linescore.get("currentInning", 9)

            weather = g.get("weather", {})
            temp = None
            wind_spd = None
            wind_dir = None
            if weather:
                try:
                    temp = float(weather.get("temp", "0"))
                except (ValueError, TypeError):
                    temp = None
                wind_spd_str = weather.get("wind", "")
                # Parse "5 mph, Out To CF" style
                if wind_spd_str:
                    parts = wind_spd_str.split(" ")
                    try:
                        wind_spd = float(parts[0])
                    except (ValueError, IndexError):
                        wind_spd = None
                    wind_dir = " ".join(parts[2:]) if len(parts) > 2 else None

            home_tid = home_team.get("id")
            away_tid = away_team.get("id")

            conn.execute("""
                INSERT INTO mlb_games
                    (game_pk, game_date, status, home_team_id, home_team_abbrev,
                     away_team_id, away_team_abbrev, home_score, away_score,
                     home_pitcher_id, home_pitcher_name, away_pitcher_id, away_pitcher_name,
                     innings, venue_name, temperature, wind_speed, wind_direction, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(game_pk) DO UPDATE SET
                    status=excluded.status, home_score=excluded.home_score,
                    away_score=excluded.away_score, innings=excluded.innings,
                    temperature=excluded.temperature, wind_speed=excluded.wind_speed,
                    wind_direction=excluded.wind_direction, updated_at=excluded.updated_at
            """, (
                game_pk, game_date, status,
                home_tid, TEAM_ABBREV_BY_ID.get(home_tid, ""),
                away_tid, TEAM_ABBREV_BY_ID.get(away_tid, ""),
                home.get("score", 0), away.get("score", 0),
                home_pitcher.get("id"), home_pitcher.get("fullName"),
                away_pitcher.get("id"), away_pitcher.get("fullName"),
                innings, venue,
                temp, wind_spd, wind_dir,
                datetime.now().isoformat(),
            ))
            count += 1

    conn.commit()
    conn.close()
    log.info("Game results: stored %d completed games from %s to %s", count, start_date, end_date)


def download_mlb_standings(season: int = None):
    """Download current standings and store in mlb_teams."""
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()
    data = _mlb_get("/standings", {
        "leagueId": "103,104",
        "season": season,
        "hydrate": "team",
    })

    count = 0
    for record in data.get("records", []):
        division = record.get("division", {}).get("name", "")
        for tr in record.get("teamRecords", []):
            team = tr.get("team", {})
            team_id = team.get("id")
            team_name = team.get("name", "")
            abbrev = TEAM_ABBREV_BY_ID.get(team_id, "")

            wins = tr.get("wins", 0)
            losses = tr.get("losses", 0)
            pct = float(tr.get("winningPercentage", "0"))

            rs = tr.get("runsScored", 0)
            ra = tr.get("runsAllowed", 0)
            rd = tr.get("runDifferential", 0)

            streak = tr.get("streak", {}).get("streakCode", "")

            records = tr.get("records", {})
            last10 = {}
            for split in records.get("splitRecords", []):
                if split.get("type") == "lastTen":
                    last10 = split
                    break

            conn.execute("""
                INSERT INTO mlb_teams
                    (season, team_id, team_abbrev, team_name, division,
                     wins, losses, pct, runs_scored, runs_allowed, run_diff,
                     streak, last_10_w, last_10_l, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(season, team_id) DO UPDATE SET
                    team_abbrev=excluded.team_abbrev, team_name=excluded.team_name,
                    division=excluded.division, wins=excluded.wins, losses=excluded.losses,
                    pct=excluded.pct, runs_scored=excluded.runs_scored,
                    runs_allowed=excluded.runs_allowed, run_diff=excluded.run_diff,
                    streak=excluded.streak, last_10_w=excluded.last_10_w,
                    last_10_l=excluded.last_10_l, updated_at=excluded.updated_at
            """, (
                season, team_id, abbrev, team_name, division,
                wins, losses, pct, rs, ra, rd,
                streak,
                last10.get("wins", 0), last10.get("losses", 0),
                datetime.now().isoformat(),
            ))
            count += 1

    conn.commit()
    conn.close()
    log.info("Standings: stored %d teams for %d season", count, season)


def download_mlb_pitcher_stats(season: int = None):
    """
    Download pitcher stats for every active pitcher across all 30 teams.
    Uses MLB Stats API roster + individual stats endpoints.
    """
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()
    count = 0

    for stadium in MLB_STADIUMS:
        team_abbrev = stadium[1]
        team_id = stadium[2]

        # Get active roster
        roster_data = _mlb_get(f"/teams/{team_id}/roster", {"rosterType": "active"})
        roster = roster_data.get("roster", [])

        pitchers = [p for p in roster if p.get("position", {}).get("abbreviation") == "P"
                     or p.get("position", {}).get("type") == "Pitcher"]

        for p in pitchers:
            player_id = p.get("person", {}).get("id")
            player_name = p.get("person", {}).get("fullName", "")
            if not player_id:
                continue

            # Fetch pitching stats
            stats_data = _mlb_get(f"/people/{player_id}/stats", {
                "stats": "season",
                "season": season,
                "group": "pitching",
            })

            stats_list = stats_data.get("stats", [])
            if not stats_list:
                continue
            splits = stats_list[0].get("splits", [])
            if not splits:
                continue

            s = splits[0].get("stat", {})
            ip_str = s.get("inningsPitched", "0")
            try:
                ip = float(ip_str)
            except ValueError:
                ip = 0.0

            era = _safe_float(s.get("era"))
            whip = _safe_float(s.get("whip"))
            so = int(s.get("strikeOuts", 0))
            bb = int(s.get("baseOnBalls", 0))
            ha = int(s.get("hits", 0))
            hr = int(s.get("homeRuns", 0))
            gs = int(s.get("gamesStarted", 0))
            gp = int(s.get("gamesPitched", 0) or s.get("gamesPlayed", 0))
            w = int(s.get("wins", 0))
            l = int(s.get("losses", 0))
            baa = _safe_float(s.get("avg"))

            # Compute rate stats
            k9 = (so / ip * 9) if ip > 0 else None
            bb9 = (bb / ip * 9) if ip > 0 else None
            hr9 = (hr / ip * 9) if ip > 0 else None

            # Compute FIP: (13*HR + 3*BB - 2*K) / IP + constant(~3.10)
            fip = ((13 * hr + 3 * bb - 2 * so) / ip + 3.10) if ip > 0 else None

            # xFIP: replace HR with league-avg HR/FB rate (~10.5%)
            # Approximate: use league avg HR/FB * estimated FB
            # Simplified: (13 * (fly_balls * 0.105) + 3*BB - 2*K) / IP + 3.10
            # Without fly ball data, estimate xFIP = FIP - (HR/9 - 1.0) * 1.2
            xfip = None
            if fip is not None and hr9 is not None:
                xfip = fip - (hr9 - 1.0) * 0.4  # rough approximation

            conn.execute("""
                INSERT INTO mlb_pitchers
                    (season, player_id, player_name, team_id, team_abbrev,
                     games, games_started, wins, losses, era, fip, xfip, whip,
                     innings_pitched, strikeouts, walks, hits_allowed, home_runs_allowed,
                     k_per_9, bb_per_9, hr_per_9, batting_avg_against, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(season, player_id) DO UPDATE SET
                    player_name=excluded.player_name, team_id=excluded.team_id,
                    team_abbrev=excluded.team_abbrev, games=excluded.games,
                    games_started=excluded.games_started, wins=excluded.wins,
                    losses=excluded.losses, era=excluded.era, fip=excluded.fip,
                    xfip=excluded.xfip, whip=excluded.whip,
                    innings_pitched=excluded.innings_pitched, strikeouts=excluded.strikeouts,
                    walks=excluded.walks, hits_allowed=excluded.hits_allowed,
                    home_runs_allowed=excluded.home_runs_allowed,
                    k_per_9=excluded.k_per_9, bb_per_9=excluded.bb_per_9,
                    hr_per_9=excluded.hr_per_9, batting_avg_against=excluded.batting_avg_against,
                    updated_at=excluded.updated_at
            """, (
                season, player_id, player_name, team_id, team_abbrev,
                gp, gs, w, l, era, fip, xfip, whip,
                ip, so, bb, ha, hr,
                k9, bb9, hr9, baa,
                datetime.now().isoformat(),
            ))
            count += 1

        log.info("  %s: %d pitchers processed", team_abbrev, len(pitchers))
        time.sleep(0.3)  # rate limiting between teams

    conn.commit()
    conn.close()
    log.info("Pitcher stats: stored %d pitchers for %d season", count, season)


def download_mlb_batter_stats(season: int = None):
    """
    Download batter stats for all active position players across all 30 teams.
    Uses MLB Stats API roster + individual stats endpoints.
    """
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()
    count = 0

    for stadium in MLB_STADIUMS:
        team_abbrev = stadium[1]
        team_id = stadium[2]

        roster_data = _mlb_get(f"/teams/{team_id}/roster", {"rosterType": "active"})
        roster = roster_data.get("roster", [])

        batters = [p for p in roster if p.get("position", {}).get("abbreviation") != "P"
                   and p.get("position", {}).get("type") != "Pitcher"]

        for b in batters:
            player_id = b.get("person", {}).get("id")
            player_name = b.get("person", {}).get("fullName", "")
            if not player_id:
                continue

            # Fetch hitting stats
            stats_data = _mlb_get(f"/people/{player_id}/stats", {
                "stats": "season",
                "season": season,
                "group": "hitting",
            })

            stats_list = stats_data.get("stats", [])
            if not stats_list:
                continue
            splits = stats_list[0].get("splits", [])
            if not splits:
                continue

            s = splits[0].get("stat", {})
            pa = int(s.get("plateAppearances", 0))
            ab = int(s.get("atBats", 0))
            h = int(s.get("hits", 0))
            d = int(s.get("doubles", 0))
            t = int(s.get("triples", 0))
            hr = int(s.get("homeRuns", 0))
            rbi = int(s.get("rbi", 0))
            sb = int(s.get("stolenBases", 0))
            gp = int(s.get("gamesPlayed", 0))
            so = int(s.get("strikeOuts", 0))
            bb = int(s.get("baseOnBalls", 0))

            avg = _safe_float(s.get("avg"))
            obp = _safe_float(s.get("obp"))
            slg = _safe_float(s.get("slg"))
            ops = _safe_float(s.get("ops"))

            k_pct = (so / pa * 100) if pa > 0 else None
            bb_pct = (bb / pa * 100) if pa > 0 else None

            # wOBA approximation: (0.69*BB + 0.72*HBP + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR) / PA
            hbp = int(s.get("hitByPitch", 0))
            singles = h - d - t - hr
            woba = None
            if pa > 0:
                woba = round((0.69 * bb + 0.72 * hbp + 0.89 * singles +
                              1.27 * d + 1.62 * t + 2.10 * hr) / pa, 3)

            conn.execute("""
                INSERT INTO mlb_batters
                    (season, player_id, player_name, team_id, team_abbrev,
                     games, plate_appearances, at_bats, hits, doubles, triples,
                     home_runs, rbi, stolen_bases, batting_avg, obp, slg, ops,
                     k_pct, bb_pct, woba, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(season, player_id) DO UPDATE SET
                    player_name=excluded.player_name, team_id=excluded.team_id,
                    team_abbrev=excluded.team_abbrev, games=excluded.games,
                    plate_appearances=excluded.plate_appearances, at_bats=excluded.at_bats,
                    hits=excluded.hits, doubles=excluded.doubles, triples=excluded.triples,
                    home_runs=excluded.home_runs, rbi=excluded.rbi,
                    stolen_bases=excluded.stolen_bases, batting_avg=excluded.batting_avg,
                    obp=excluded.obp, slg=excluded.slg, ops=excluded.ops,
                    k_pct=excluded.k_pct, bb_pct=excluded.bb_pct,
                    woba=excluded.woba, updated_at=excluded.updated_at
            """, (
                season, player_id, player_name, team_id, team_abbrev,
                gp, pa, ab, h, d, t, hr, rbi, sb,
                avg, obp, slg, ops, k_pct, bb_pct, woba,
                datetime.now().isoformat(),
            ))
            count += 1

        log.info("  %s: %d batters processed", team_abbrev, len(batters))
        time.sleep(0.3)

    conn.commit()
    conn.close()
    log.info("Batter stats: stored %d batters for %d season", count, season)


def download_statcast_pitcher_extras(player_id: int, season: int = None):
    """
    Enrich a pitcher record with Statcast data from pybaseball.
    Fetches season-level averages for velo, spin, whiff%, xERA, etc.
    """
    if pb is None:
        log.warning("pybaseball not installed -- skipping Statcast pitcher enrichment")
        return

    if season is None:
        season = CURRENT_SEASON

    start = f"{season}-03-20"
    end = f"{season}-11-01"
    today = datetime.now().strftime("%Y-%m-%d")
    if end > today:
        end = today

    try:
        df = pb.statcast_pitcher(start, end, player_id)
        if df is None or df.empty:
            return
    except Exception as e:
        log.warning("Statcast pitcher %d failed: %s", player_id, e)
        return

    conn = get_db()

    # Average fastball velocity (FF = four-seam, SI = sinker)
    fb_mask = df["pitch_type"].isin(["FF", "SI", "FC"])
    avg_velo = df.loc[fb_mask, "release_speed"].mean() if fb_mask.any() else None

    avg_spin = df["release_spin_rate"].mean() if "release_spin_rate" in df.columns else None

    # Whiff %: swinging strikes / total swings
    swings = df["description"].isin([
        "swinging_strike", "swinging_strike_blocked", "foul", "foul_tip",
        "hit_into_play", "hit_into_play_no_out", "hit_into_play_score"
    ])
    whiffs = df["description"].isin(["swinging_strike", "swinging_strike_blocked"])
    whiff_pct = (whiffs.sum() / swings.sum() * 100) if swings.sum() > 0 else None

    # Hard hit % against (exit velo >= 95 mph)
    batted = df[df["launch_speed"].notna()]
    hard_hit_pct = (batted["launch_speed"] >= 95).mean() * 100 if len(batted) > 0 else None

    # Barrel % against
    barrel_pct = None
    if "barrel" in df.columns and len(batted) > 0:
        barrel_pct = df["barrel"].mean() * 100 if df["barrel"].notna().any() else None

    # xERA from estimated_ba_using_speedangle (proxy)
    xera = None
    if "estimated_woba_using_speedangle" in df.columns:
        xwoba_against = df["estimated_woba_using_speedangle"].mean()
        if xwoba_against and xwoba_against > 0:
            # Convert xwOBA to xERA approximation: xERA ~ (xwOBA / 0.320) * 4.00
            xera = round((xwoba_against / 0.320) * 4.00, 2)

    conn.execute("""
        UPDATE mlb_pitchers SET
            avg_fastball_velo=?, avg_spin_rate=?, whiff_pct=?,
            hard_hit_pct_against=?, barrel_pct_against=?, xera=?,
            updated_at=?
        WHERE season=? AND player_id=?
    """, (
        _round(avg_velo, 1), _round(avg_spin, 0), _round(whiff_pct, 1),
        _round(hard_hit_pct, 1), _round(barrel_pct, 1), xera,
        datetime.now().isoformat(),
        season, player_id,
    ))
    conn.commit()
    conn.close()


def download_statcast_batter_extras(player_id: int, season: int = None):
    """Enrich a batter record with Statcast data from pybaseball."""
    if pb is None:
        log.warning("pybaseball not installed -- skipping Statcast batter enrichment")
        return

    if season is None:
        season = CURRENT_SEASON

    start = f"{season}-03-20"
    end = f"{season}-11-01"
    today = datetime.now().strftime("%Y-%m-%d")
    if end > today:
        end = today

    try:
        df = pb.statcast_batter(start, end, player_id)
        if df is None or df.empty:
            return
    except Exception as e:
        log.warning("Statcast batter %d failed: %s", player_id, e)
        return

    conn = get_db()

    batted = df[df["launch_speed"].notna()]
    exit_velo = batted["launch_speed"].mean() if len(batted) > 0 else None
    la = batted["launch_angle"].mean() if len(batted) > 0 and "launch_angle" in batted.columns else None
    hard_hit = (batted["launch_speed"] >= 95).mean() * 100 if len(batted) > 0 else None

    barrel_pct = None
    if "barrel" in df.columns and len(batted) > 0:
        barrel_pct = df["barrel"].mean() * 100 if df["barrel"].notna().any() else None

    xwoba = None
    if "estimated_woba_using_speedangle" in df.columns:
        xwoba = df["estimated_woba_using_speedangle"].mean()

    sprint_speed = None
    if "sprint_speed" in df.columns:
        sprint_speed = df["sprint_speed"].mean()

    conn.execute("""
        UPDATE mlb_batters SET
            exit_velo=?, launch_angle=?, hard_hit_pct=?,
            barrel_pct=?, xwoba=?, sprint_speed=?,
            updated_at=?
        WHERE season=? AND player_id=?
    """, (
        _round(exit_velo, 1), _round(la, 1), _round(hard_hit, 1),
        _round(barrel_pct, 1), _round(xwoba, 3), _round(sprint_speed, 1),
        datetime.now().isoformat(),
        season, player_id,
    ))
    conn.commit()
    conn.close()


def download_batter_splits(player_id: int, season: int = None):
    """Fetch batter vs LHP/RHP splits from MLB API."""
    if season is None:
        season = CURRENT_SEASON

    stats_data = _mlb_get(f"/people/{player_id}/stats", {
        "stats": "vsPitchType",  # not ideal -- use statSplits
        "season": season,
        "group": "hitting",
    })

    # Try the statSplits endpoint for platoon data
    split_data = _mlb_get(f"/people/{player_id}/stats", {
        "stats": "statSplits",
        "season": season,
        "group": "hitting",
    })

    conn = get_db()
    updates = {}

    for stat_group in split_data.get("stats", []):
        for split in stat_group.get("splits", []):
            split_name = split.get("split", {}).get("description", "")
            s = split.get("stat", {})
            if "Left" in split_name:
                updates["avg_vs_lhp"] = _safe_float(s.get("avg"))
                updates["obp_vs_lhp"] = _safe_float(s.get("obp"))
                updates["slg_vs_lhp"] = _safe_float(s.get("slg"))
            elif "Right" in split_name:
                updates["avg_vs_rhp"] = _safe_float(s.get("avg"))
                updates["obp_vs_rhp"] = _safe_float(s.get("obp"))
                updates["slg_vs_rhp"] = _safe_float(s.get("slg"))

    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [datetime.now().isoformat(), season, player_id]
        conn.execute(
            f"UPDATE mlb_batters SET {set_clause}, updated_at=? WHERE season=? AND player_id=?",
            vals
        )
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def fetch_weather_for_games(games: list = None):
    """
    Fetch weather forecasts for upcoming outdoor games.
    If games not provided, reads from mlb_schedule for next 3 days.
    """
    conn = get_db()

    if games is None:
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT game_pk, game_date, game_time, home_team_abbrev, venue_name
            FROM mlb_schedule
            WHERE game_date >= ? AND game_date <= ?
              AND status NOT LIKE '%Final%'
        """, (today, future)).fetchall()
        games = [dict(r) for r in rows]

    count = 0
    for g in games:
        team_abbrev = g.get("home_team_abbrev", "")
        stadium = STADIUM_BY_ABBREV.get(team_abbrev)
        if not stadium:
            continue

        # Skip domed stadiums
        if stadium[5]:  # is_dome
            continue

        lat, lon = stadium[3], stadium[4]
        game_date = g.get("game_date", "")
        game_time = g.get("game_time", "")

        # Parse hour from game_time (ISO format)
        hour = 19  # default 7pm ET
        if game_time:
            try:
                dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                hour = dt.hour
            except (ValueError, AttributeError):
                pass

        wx = _weather_get(lat, lon, game_date, hour)
        if not wx:
            continue

        # Compute weather impact score
        # Higher score = more impact on scoring
        # Wind > 10mph adds/subtracts based on direction relative to park orientation
        wind_spd = wx.get("wind_speed_mph", 0) or 0
        wind_dir = wx.get("wind_direction_deg", 0) or 0
        temp = wx.get("temperature_f", 72) or 72
        precip = wx.get("precipitation_mm", 0) or 0

        # Temperature impact: cold reduces offense, hot increases it
        temp_factor = (temp - 72) * 0.005  # ~0.5% per degree from 72F

        # Wind impact: high wind amplifies. Direction factor is park-specific
        # Simplified: wind blowing out (roughly 180-270 deg) helps hitters
        wind_factor = 0
        if wind_spd > 8:
            if 135 <= wind_dir <= 315:  # blowing out broadly
                wind_factor = (wind_spd - 8) * 0.02
            else:  # blowing in
                wind_factor = -(wind_spd - 8) * 0.015

        # Precipitation dampens offense
        precip_factor = -precip * 0.1 if precip > 0 else 0

        impact = round(temp_factor + wind_factor + precip_factor, 3)

        game_pk = g.get("game_pk")
        conn.execute("""
            INSERT INTO mlb_weather
                (game_pk, game_date, game_time, stadium_name, team_abbrev,
                 latitude, longitude, temperature_f, wind_speed_mph,
                 wind_direction_deg, precipitation_mm, humidity_pct,
                 weather_impact_score, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(game_pk, game_date) DO UPDATE SET
                temperature_f=excluded.temperature_f, wind_speed_mph=excluded.wind_speed_mph,
                wind_direction_deg=excluded.wind_direction_deg,
                precipitation_mm=excluded.precipitation_mm,
                humidity_pct=excluded.humidity_pct,
                weather_impact_score=excluded.weather_impact_score,
                updated_at=excluded.updated_at
        """, (
            game_pk, game_date, game_time, stadium[0], team_abbrev,
            lat, lon,
            wx.get("temperature_f"), wx.get("wind_speed_mph"),
            wx.get("wind_direction_deg"), wx.get("precipitation_mm"),
            wx.get("humidity_pct"), impact,
            datetime.now().isoformat(),
        ))
        count += 1
        time.sleep(0.2)  # rate limit

    conn.commit()
    conn.close()
    log.info("Weather: fetched forecasts for %d outdoor games", count)


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_pitcher_features(pitcher_id: int, season: int = None) -> dict:
    """
    Compute pitcher quality features for model consumption.
    Returns a dict of features keyed by metric name.
    """
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()
    row = conn.execute("""
        SELECT * FROM mlb_pitchers WHERE player_id=? AND season=?
    """, (pitcher_id, season)).fetchone()
    conn.close()

    if not row:
        return {"pitcher_id": pitcher_id, "found": False}

    r = dict(row)
    ip = r.get("innings_pitched", 0) or 0

    features = {
        "pitcher_id": pitcher_id,
        "pitcher_name": r.get("player_name"),
        "found": True,
        "team_abbrev": r.get("team_abbrev"),
        "games_started": r.get("games_started", 0),
        "innings_pitched": ip,
        # Traditional
        "era": r.get("era"),
        "fip": r.get("fip"),
        "xfip": r.get("xfip"),
        "whip": r.get("whip"),
        "k_per_9": r.get("k_per_9"),
        "bb_per_9": r.get("bb_per_9"),
        "hr_per_9": r.get("hr_per_9"),
        "batting_avg_against": r.get("batting_avg_against"),
        # Statcast
        "avg_fastball_velo": r.get("avg_fastball_velo"),
        "avg_spin_rate": r.get("avg_spin_rate"),
        "whiff_pct": r.get("whiff_pct"),
        "hard_hit_pct_against": r.get("hard_hit_pct_against"),
        "barrel_pct_against": r.get("barrel_pct_against"),
        "xera": r.get("xera"),
        # Quality composite: lower = better
        # Weighted: 30% FIP, 25% xFIP, 20% K-BB%, 15% WHIP, 10% Hard Hit
        "quality_score": None,
    }

    # Compute quality score (lower = better pitcher)
    fip = r.get("fip")
    xfip = r.get("xfip")
    whip = r.get("whip")
    k9 = r.get("k_per_9")
    bb9 = r.get("bb_per_9")
    hh = r.get("hard_hit_pct_against")

    if fip is not None and ip >= 10:
        score = fip * 0.30
        if xfip is not None:
            score += xfip * 0.25
        else:
            score += fip * 0.25
        if k9 is not None and bb9 is not None:
            k_bb_rate = (k9 - bb9)
            # Normalize: league avg K-BB ~ 4.0, map to ERA-like scale
            score += (9.0 - k_bb_rate) * 0.20  # higher K-BB = lower score
        if whip is not None:
            score += whip * 2.0 * 0.15  # scale WHIP to ERA-like
        if hh is not None:
            score += (hh / 100 * 9) * 0.10
        features["quality_score"] = round(score, 2)

    return features


def compute_team_batting_features(team_id: int, season: int = None) -> dict:
    """
    Compute team offensive features aggregated from individual batters
    and team game results.
    """
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()

    # Team-level from standings
    team_row = conn.execute("""
        SELECT * FROM mlb_teams WHERE team_id=? AND season=?
    """, (team_id, season)).fetchone()

    # Aggregate batter stats
    batters = conn.execute("""
        SELECT * FROM mlb_batters WHERE team_id=? AND season=? AND plate_appearances >= 30
        ORDER BY plate_appearances DESC
    """, (team_id, season)).fetchall()

    # Recent game performance
    abbrev = TEAM_ABBREV_BY_ID.get(team_id, "")
    recent_games = conn.execute("""
        SELECT * FROM mlb_games
        WHERE (home_team_id=? OR away_team_id=?) AND status LIKE '%Final%'
        ORDER BY game_date DESC LIMIT 20
    """, (team_id, team_id)).fetchall()
    conn.close()

    features = {
        "team_id": team_id,
        "team_abbrev": abbrev,
    }

    if team_row:
        tr = dict(team_row)
        gp = tr.get("wins", 0) + tr.get("losses", 0)
        features.update({
            "wins": tr.get("wins", 0),
            "losses": tr.get("losses", 0),
            "win_pct": tr.get("pct"),
            "runs_scored_season": tr.get("runs_scored", 0),
            "runs_allowed_season": tr.get("runs_allowed", 0),
            "run_diff": tr.get("run_diff", 0),
            "rs_per_game_season": round(tr.get("runs_scored", 0) / gp, 2) if gp > 0 else None,
            "ra_per_game_season": round(tr.get("runs_allowed", 0) / gp, 2) if gp > 0 else None,
            "last_10_w": tr.get("last_10_w", 0),
            "last_10_l": tr.get("last_10_l", 0),
        })

    # Aggregate batter splits
    total_pa = 0
    weighted_woba = 0
    weighted_xwoba = 0
    weighted_k_pct = 0
    weighted_bb_pct = 0
    avg_vs_lhp_total = []
    avg_vs_rhp_total = []
    obp_vs_lhp_total = []
    obp_vs_rhp_total = []
    slg_vs_lhp_total = []
    slg_vs_rhp_total = []
    total_exit_velo = []

    for b in batters:
        bd = dict(b)
        pa = bd.get("plate_appearances", 0) or 0
        total_pa += pa

        if bd.get("woba") is not None:
            weighted_woba += bd["woba"] * pa
        if bd.get("xwoba") is not None:
            weighted_xwoba += bd["xwoba"] * pa
        if bd.get("k_pct") is not None:
            weighted_k_pct += bd["k_pct"] * pa
        if bd.get("bb_pct") is not None:
            weighted_bb_pct += bd["bb_pct"] * pa
        if bd.get("exit_velo") is not None:
            total_exit_velo.append(bd["exit_velo"])

        if bd.get("avg_vs_lhp") is not None:
            avg_vs_lhp_total.append(bd["avg_vs_lhp"])
        if bd.get("avg_vs_rhp") is not None:
            avg_vs_rhp_total.append(bd["avg_vs_rhp"])
        if bd.get("obp_vs_lhp") is not None:
            obp_vs_lhp_total.append(bd["obp_vs_lhp"])
        if bd.get("obp_vs_rhp") is not None:
            obp_vs_rhp_total.append(bd["obp_vs_rhp"])
        if bd.get("slg_vs_lhp") is not None:
            slg_vs_lhp_total.append(bd["slg_vs_lhp"])
        if bd.get("slg_vs_rhp") is not None:
            slg_vs_rhp_total.append(bd["slg_vs_rhp"])

    features.update({
        "team_woba": round(weighted_woba / total_pa, 3) if total_pa > 0 else None,
        "team_xwoba": round(weighted_xwoba / total_pa, 3) if total_pa > 0 else None,
        "team_k_pct": round(weighted_k_pct / total_pa, 1) if total_pa > 0 else None,
        "team_bb_pct": round(weighted_bb_pct / total_pa, 1) if total_pa > 0 else None,
        "team_avg_exit_velo": round(sum(total_exit_velo) / len(total_exit_velo), 1) if total_exit_velo else None,
        "team_avg_vs_lhp": round(sum(avg_vs_lhp_total) / len(avg_vs_lhp_total), 3) if avg_vs_lhp_total else None,
        "team_avg_vs_rhp": round(sum(avg_vs_rhp_total) / len(avg_vs_rhp_total), 3) if avg_vs_rhp_total else None,
        "team_obp_vs_lhp": round(sum(obp_vs_lhp_total) / len(obp_vs_lhp_total), 3) if obp_vs_lhp_total else None,
        "team_obp_vs_rhp": round(sum(obp_vs_rhp_total) / len(obp_vs_rhp_total), 3) if obp_vs_rhp_total else None,
        "team_slg_vs_lhp": round(sum(slg_vs_lhp_total) / len(slg_vs_lhp_total), 3) if slg_vs_lhp_total else None,
        "team_slg_vs_rhp": round(sum(slg_vs_rhp_total) / len(slg_vs_rhp_total), 3) if slg_vs_rhp_total else None,
    })

    # Recent game-based features
    if recent_games:
        runs_scored_last_10 = []
        runs_scored_last_20 = []
        runs_allowed_last_10 = []
        runs_allowed_last_20 = []

        for i, g in enumerate(recent_games):
            gd = dict(g)
            if gd["home_team_id"] == team_id:
                rs = gd.get("home_score", 0) or 0
                ra = gd.get("away_score", 0) or 0
            else:
                rs = gd.get("away_score", 0) or 0
                ra = gd.get("home_score", 0) or 0

            if i < 10:
                runs_scored_last_10.append(rs)
                runs_allowed_last_10.append(ra)
            runs_scored_last_20.append(rs)
            runs_allowed_last_20.append(ra)

        features.update({
            "rs_per_game_last_10": round(sum(runs_scored_last_10) / len(runs_scored_last_10), 2) if runs_scored_last_10 else None,
            "ra_per_game_last_10": round(sum(runs_allowed_last_10) / len(runs_allowed_last_10), 2) if runs_allowed_last_10 else None,
            "rs_per_game_last_20": round(sum(runs_scored_last_20) / len(runs_scored_last_20), 2) if runs_scored_last_20 else None,
            "ra_per_game_last_20": round(sum(runs_allowed_last_20) / len(runs_allowed_last_20), 2) if runs_allowed_last_20 else None,
        })

    return features


def compute_bullpen_fatigue(team_id: int, lookback_days: int = 3) -> dict:
    """
    Estimate bullpen fatigue based on recent game patterns.
    Games with 5+ relief innings in the last N days indicate a taxed bullpen.
    """
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    recent = conn.execute("""
        SELECT * FROM mlb_games
        WHERE (home_team_id=? OR away_team_id=?) AND status LIKE '%Final%'
          AND game_date >= ?
        ORDER BY game_date DESC
    """, (team_id, team_id, cutoff)).fetchall()
    conn.close()

    # Heuristic: if the starter averaged < 5 IP in recent games, bullpen is working hard
    # We don't have exact relief IP from the schedule API without game feeds,
    # so we approximate: extra innings games, blowouts (lots of pitchers used)
    games_played = len(recent)
    extra_inning_games = sum(1 for g in recent if (dict(g).get("innings") or 9) > 9)

    # If a game had > 9 innings or if there were many games, bullpen is likely taxed
    fatigue_score = 0.0
    if games_played >= 3:
        fatigue_score += 0.3  # played every day
    if games_played >= 4:
        fatigue_score += 0.2
    fatigue_score += extra_inning_games * 0.25

    return {
        "team_id": team_id,
        "games_last_3_days": games_played,
        "extra_inning_games": extra_inning_games,
        "bullpen_fatigue_score": round(min(fatigue_score, 1.0), 2),  # 0-1 scale
    }


def get_game_features(
    home_team: str,
    away_team: str,
    home_pitcher_id: int = None,
    away_pitcher_id: int = None,
    game_pk: int = None,
) -> dict:
    """
    Build complete feature set for a matchup.
    Combines pitcher quality, team batting, park factors, weather, bullpen fatigue.
    """
    conn = get_db()

    # Resolve team IDs from abbreviation
    home_stadium = STADIUM_BY_ABBREV.get(home_team)
    away_stadium = STADIUM_BY_ABBREV.get(away_team)

    if not home_stadium:
        return {"error": f"Unknown home team: {home_team}"}

    home_id = home_stadium[2]
    away_id = away_stadium[2] if away_stadium else None

    features = {
        "home_team": home_team,
        "away_team": away_team,
        "venue": home_stadium[0],
        "is_dome": bool(home_stadium[5]),
        "park_factor_runs": home_stadium[6],
    }

    # Pitcher features
    if home_pitcher_id:
        features["home_pitcher"] = compute_pitcher_features(home_pitcher_id)
    if away_pitcher_id:
        features["away_pitcher"] = compute_pitcher_features(away_pitcher_id)

    # Try to look up starting pitchers from schedule if not provided
    if not home_pitcher_id or not away_pitcher_id:
        today = datetime.now().strftime("%Y-%m-%d")
        sched = conn.execute("""
            SELECT * FROM mlb_schedule
            WHERE home_team_abbrev=? AND away_team_abbrev=? AND game_date=?
            LIMIT 1
        """, (home_team, away_team, today)).fetchone()
        if sched:
            sd = dict(sched)
            if not home_pitcher_id and sd.get("home_pitcher_id"):
                features["home_pitcher"] = compute_pitcher_features(sd["home_pitcher_id"])
            if not away_pitcher_id and sd.get("away_pitcher_id"):
                features["away_pitcher"] = compute_pitcher_features(sd["away_pitcher_id"])

    # Team batting features
    features["home_batting"] = compute_team_batting_features(home_id)
    if away_id:
        features["away_batting"] = compute_team_batting_features(away_id)

    # Bullpen fatigue
    features["home_bullpen"] = compute_bullpen_fatigue(home_id)
    if away_id:
        features["away_bullpen"] = compute_bullpen_fatigue(away_id)

    # Weather
    if game_pk:
        wx = conn.execute("""
            SELECT * FROM mlb_weather WHERE game_pk=? ORDER BY updated_at DESC LIMIT 1
        """, (game_pk,)).fetchone()
        if wx:
            features["weather"] = dict(wx)
    elif not home_stadium[5]:  # not a dome, try today's weather
        today = datetime.now().strftime("%Y-%m-%d")
        wx_data = _weather_get(home_stadium[3], home_stadium[4], today, 19)
        if wx_data:
            features["weather"] = wx_data

    # Park-factor adjusted expected runs
    pf = home_stadium[6]
    home_rs = features.get("home_batting", {}).get("rs_per_game_season")
    away_rs = features.get("away_batting", {}).get("rs_per_game_season")
    if home_rs and away_rs:
        # Adjust for park factor
        features["expected_total_runs_raw"] = round(home_rs + away_rs, 2)
        features["expected_total_runs_park_adj"] = round((home_rs + away_rs) * pf, 2)

        # Further adjust for weather if available
        wx_impact = features.get("weather", {}).get("weather_impact_score", 0) or 0
        features["expected_total_runs_full_adj"] = round(
            (home_rs + away_rs) * pf * (1 + wx_impact), 2
        )

    conn.close()
    return features


# ---------------------------------------------------------------------------
# Statcast bulk enrichment
# ---------------------------------------------------------------------------

def enrich_statcast(season: int = None, max_pitchers: int = 50, max_batters: int = 80):
    """
    Enrich top pitchers and batters with Statcast data.
    Rate-limited; intended for daily batch runs.
    max_pitchers/max_batters limits per run to avoid rate limits.
    """
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()

    # Top pitchers by innings pitched that haven't been enriched recently
    pitchers = conn.execute("""
        SELECT player_id, player_name FROM mlb_pitchers
        WHERE season=? AND innings_pitched >= 10
          AND (avg_fastball_velo IS NULL
               OR updated_at < datetime('now', '-1 day'))
        ORDER BY innings_pitched DESC
        LIMIT ?
    """, (season, max_pitchers)).fetchall()

    batters = conn.execute("""
        SELECT player_id, player_name FROM mlb_batters
        WHERE season=? AND plate_appearances >= 50
          AND (exit_velo IS NULL
               OR updated_at < datetime('now', '-1 day'))
        ORDER BY plate_appearances DESC
        LIMIT ?
    """, (season, max_batters)).fetchall()
    conn.close()

    log.info("Statcast enrichment: %d pitchers, %d batters to process", len(pitchers), len(batters))

    for i, p in enumerate(pitchers):
        pid = p["player_id"]
        log.info("  Statcast pitcher %d/%d: %s (%d)", i + 1, len(pitchers), p["player_name"], pid)
        try:
            download_statcast_pitcher_extras(pid, season)
        except Exception as e:
            log.warning("  Failed: %s", e)
        time.sleep(2)  # pybaseball rate limiting

    for i, b in enumerate(batters):
        bid = b["player_id"]
        log.info("  Statcast batter %d/%d: %s (%d)", i + 1, len(batters), b["player_name"], bid)
        try:
            download_statcast_batter_extras(bid, season)
        except Exception as e:
            log.warning("  Failed: %s", e)
        time.sleep(2)


def enrich_batter_splits(season: int = None, max_batters: int = 100):
    """Fetch platoon splits for batters missing split data."""
    if season is None:
        season = CURRENT_SEASON

    conn = get_db()
    batters = conn.execute("""
        SELECT player_id, player_name FROM mlb_batters
        WHERE season=? AND plate_appearances >= 30
          AND avg_vs_lhp IS NULL
        ORDER BY plate_appearances DESC
        LIMIT ?
    """, (season, max_batters)).fetchall()
    conn.close()

    log.info("Batter splits: %d batters to process", len(batters))
    for i, b in enumerate(batters):
        bid = b["player_id"]
        log.info("  Splits %d/%d: %s (%d)", i + 1, len(batters), b["player_name"], bid)
        try:
            download_batter_splits(bid, season)
        except Exception as e:
            log.warning("  Failed: %s", e)
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def update_all(season: int = None, skip_statcast: bool = False):
    """
    Run the full MLB data pipeline update.

    Steps:
    1. Seed stadium data
    2. Download schedule (today + 7 days)
    3. Download recent game results (last 7 days)
    4. Download standings
    5. Download pitcher stats for all teams
    6. Download batter stats for all teams
    7. Fetch weather for upcoming outdoor games
    8. Enrich with Statcast data (optional, slow)
    9. Enrich batter splits (optional, slow)
    """
    if season is None:
        season = CURRENT_SEASON

    start_time = time.time()
    log.info("=" * 60)
    log.info("MLB Data Pipeline - Full Update (season %d)", season)
    log.info("=" * 60)

    # 1. Seed stadiums
    conn = get_db()
    _seed_stadiums(conn)
    conn.close()

    # 2. Schedule
    log.info("-" * 40)
    log.info("Step 2: Downloading schedule...")
    download_mlb_schedule(days_ahead=7)

    # 3. Recent game results (last 14 days for good recent-form data)
    log.info("-" * 40)
    log.info("Step 3: Downloading recent game results...")
    start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    download_mlb_game_results(start, end)

    # 4. Standings
    log.info("-" * 40)
    log.info("Step 4: Downloading standings...")
    download_mlb_standings(season)

    # 5. Pitcher stats
    log.info("-" * 40)
    log.info("Step 5: Downloading pitcher stats...")
    download_mlb_pitcher_stats(season)

    # 6. Batter stats
    log.info("-" * 40)
    log.info("Step 6: Downloading batter stats...")
    download_mlb_batter_stats(season)

    # 7. Weather
    log.info("-" * 40)
    log.info("Step 7: Fetching weather forecasts...")
    fetch_weather_for_games()

    # 8. Statcast enrichment (slow -- optional)
    if not skip_statcast:
        log.info("-" * 40)
        log.info("Step 8: Enriching with Statcast data (this takes a while)...")
        try:
            enrich_statcast(season, max_pitchers=30, max_batters=50)
        except Exception as e:
            log.warning("Statcast enrichment failed (non-fatal): %s", e)

        # 9. Batter splits
        log.info("-" * 40)
        log.info("Step 9: Enriching batter splits...")
        try:
            enrich_batter_splits(season, max_batters=60)
        except Exception as e:
            log.warning("Batter splits enrichment failed (non-fatal): %s", e)
    else:
        log.info("Skipping Statcast enrichment (--skip-statcast)")

    elapsed = time.time() - start_time
    log.info("=" * 60)
    log.info("MLB Pipeline complete in %.1f seconds", elapsed)
    log.info("Database: %s", DB_PATH)
    _print_summary()


def _print_summary():
    """Print row counts for all MLB tables."""
    conn = get_db()
    tables = ["mlb_stadiums", "mlb_teams", "mlb_pitchers", "mlb_batters",
              "mlb_games", "mlb_schedule", "mlb_weather"]
    log.info("-" * 40)
    log.info("Table Summary:")
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            log.info("  %-20s %d rows", t, count)
        except Exception:
            log.info("  %-20s (not created)", t)
    conn.close()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        v = float(val)
        return v if v == v else None  # NaN check
    except (ValueError, TypeError):
        return None


def _round(val, decimals: int = 2):
    if val is None:
        return None
    try:
        return round(float(val), decimals)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args or args[0] == "all":
        skip_sc = "--skip-statcast" in args
        update_all(skip_statcast=skip_sc)

    elif args[0] == "schedule":
        date = args[1] if len(args) > 1 else None
        download_mlb_schedule(date=date)

    elif args[0] == "standings":
        download_mlb_standings()

    elif args[0] == "pitchers":
        download_mlb_pitcher_stats()

    elif args[0] == "batters":
        download_mlb_batter_stats()

    elif args[0] == "weather":
        fetch_weather_for_games()

    elif args[0] == "results":
        start = args[1] if len(args) > 1 else (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end = args[2] if len(args) > 2 else datetime.now().strftime("%Y-%m-%d")
        download_mlb_game_results(start, end)

    elif args[0] == "statcast":
        enrich_statcast()

    elif args[0] == "splits":
        enrich_batter_splits()

    elif args[0] == "features":
        # Print features for all upcoming games
        conn = get_db()
        today = datetime.now().strftime("%Y-%m-%d")
        games = conn.execute("""
            SELECT * FROM mlb_schedule
            WHERE game_date >= ? AND status NOT LIKE '%Final%'
            ORDER BY game_date, game_time
        """, (today,)).fetchall()
        conn.close()

        for g in games:
            gd = dict(g)
            log.info("\n%s @ %s (%s)", gd["away_team_abbrev"], gd["home_team_abbrev"], gd["game_date"])
            feats = get_game_features(
                gd["home_team_abbrev"], gd["away_team_abbrev"],
                gd.get("home_pitcher_id"), gd.get("away_pitcher_id"),
                gd.get("game_pk"),
            )
            # Print key features
            for k in ["venue", "park_factor_runs", "is_dome",
                       "expected_total_runs_raw", "expected_total_runs_park_adj",
                       "expected_total_runs_full_adj"]:
                if k in feats:
                    log.info("  %-35s %s", k, feats[k])

            hp = feats.get("home_pitcher", {})
            if hp.get("found"):
                log.info("  Home SP: %-25s ERA=%-6s FIP=%-6s K/9=%-5s QS=%-5s",
                         hp.get("pitcher_name", "?"), hp.get("era"), hp.get("fip"),
                         hp.get("k_per_9"), hp.get("quality_score"))
            ap = feats.get("away_pitcher", {})
            if ap.get("found"):
                log.info("  Away SP: %-25s ERA=%-6s FIP=%-6s K/9=%-5s QS=%-5s",
                         ap.get("pitcher_name", "?"), ap.get("era"), ap.get("fip"),
                         ap.get("k_per_9"), ap.get("quality_score"))

    elif args[0] == "game":
        if len(args) < 3:
            print("Usage: python mlb_data_pipeline.py game HOME AWAY [home_pid] [away_pid]")
            sys.exit(1)
        home = args[1].upper()
        away = args[2].upper()
        hp = int(args[3]) if len(args) > 3 else None
        ap = int(args[4]) if len(args) > 4 else None
        feats = get_game_features(home, away, hp, ap)
        print(json.dumps(feats, indent=2, default=str))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

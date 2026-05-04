#!/usr/bin/env python3
"""
Fetch historical weather data for MLB game venues using Open-Meteo API.

Fetches hourly weather for each stadium on game days, stores in game_lines.db.
Uses Open-Meteo archive API (free, no API key needed).
"""

import os
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

# Stadium coordinates
STADIUM_COORDS = {
    "LAA": (33.80, -117.88), "ARI": (33.45, -112.07), "NYM": (40.76, -73.85),
    "PHI": (39.91, -75.17), "DET": (42.34, -83.05), "COL": (39.76, -104.99),
    "BAL": (39.28, -76.62), "CLE": (41.50, -81.69), "BOS": (42.35, -71.10),
    "CHC": (41.95, -87.66), "CWS": (41.83, -87.63), "CIN": (39.10, -84.51),
    "HOU": (29.76, -95.36), "KC": (39.05, -94.48), "LAD": (34.07, -118.24),
    "MIA": (25.78, -80.22), "MIL": (43.03, -87.97), "MIN": (44.98, -93.28),
    "NYY": (40.83, -73.93), "OAK": (37.75, -122.20), "PIT": (40.45, -80.01),
    "SD": (32.71, -117.16), "SEA": (47.59, -122.33), "SF": (37.78, -122.39),
    "STL": (38.62, -90.19), "TB": (27.77, -82.65), "TEX": (32.75, -97.08),
    "TOR": (43.64, -79.39), "WSH": (38.87, -77.01), "ATL": (33.89, -84.47),
}

IS_DOME = {"ARI", "HOU", "TEX", "TOR", "MIL", "SEA", "MIA", "TB"}


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mlb_weather_history (
            game_date TEXT NOT NULL,
            home_team TEXT NOT NULL,
            temperature_f REAL,
            wind_speed_mph REAL,
            humidity_pct REAL,
            precipitation_mm REAL,
            UNIQUE(game_date, home_team)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_hist ON mlb_weather_history(game_date, home_team)")
    conn.commit()


def fetch_weather_bulk(lat, lon, start_date, end_date):
    """Fetch weather for a location over a date range (max ~1 year per call)."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,windspeed_10m,relativehumidity_2m,precipitation",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "timezone": "America/New_York",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    hourly = data.get("hourly", {})

    # Group by date, take evening hours (18-21 local = typical game time)
    daily = {}
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    winds = hourly.get("windspeed_10m", [])
    humids = hourly.get("relativehumidity_2m", [])
    precips = hourly.get("precipitation", [])

    for i, t in enumerate(times):
        date = t[:10]
        hour = int(t[11:13])
        if 18 <= hour <= 21:  # Evening game hours
            if date not in daily:
                daily[date] = {"temps": [], "winds": [], "humids": [], "precips": []}
            if i < len(temps) and temps[i] is not None:
                daily[date]["temps"].append(temps[i])
            if i < len(winds) and winds[i] is not None:
                daily[date]["winds"].append(winds[i])
            if i < len(humids) and humids[i] is not None:
                daily[date]["humids"].append(humids[i])
            if i < len(precips) and precips[i] is not None:
                daily[date]["precips"].append(precips[i])

    result = {}
    for date, vals in daily.items():
        if vals["temps"]:
            result[date] = {
                "temp": sum(vals["temps"]) / len(vals["temps"]),
                "wind": sum(vals["winds"]) / len(vals["winds"]) if vals["winds"] else 5,
                "humidity": sum(vals["humids"]) / len(vals["humids"]) if vals["humids"] else 50,
                "precip": sum(vals["precips"]),
            }
    return result


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Get all unique game dates + home teams from starters table
    games = conn.execute("""
        SELECT DISTINCT game_date, home_team FROM mlb_game_starters
        ORDER BY game_date
    """).fetchall()
    print(f"Total games needing weather: {len(games)}")

    # Check existing
    existing = set()
    rows = conn.execute("SELECT game_date, home_team FROM mlb_weather_history").fetchall()
    for r in rows:
        existing.add((r[0], r[1]))
    print(f"Already have weather for: {len(existing)} game-dates")

    # Group games by home team for bulk fetching
    team_dates = defaultdict(set)
    for gd, ht in games:
        if (gd, ht) not in existing and ht not in IS_DOME:
            team_dates[ht].add(gd)

    # Also add dome teams with neutral weather
    dome_games = [(gd, ht) for gd, ht in games if ht in IS_DOME and (gd, ht) not in existing]
    if dome_games:
        print(f"Inserting neutral weather for {len(dome_games)} dome games...")
        for gd, ht in dome_games:
            conn.execute("""
                INSERT OR IGNORE INTO mlb_weather_history
                (game_date, home_team, temperature_f, wind_speed_mph, humidity_pct, precipitation_mm)
                VALUES (?, ?, 72, 0, 50, 0)
            """, (gd, ht))
        conn.commit()

    teams_to_fetch = [t for t in team_dates if team_dates[t]]
    print(f"Teams needing weather fetch: {len(teams_to_fetch)}")
    total_dates = sum(len(d) for d in team_dates.values())
    print(f"Total outdoor game-dates to fetch: {total_dates}")

    fetched = 0
    errors = 0
    for team in sorted(teams_to_fetch):
        coords = STADIUM_COORDS.get(team)
        if not coords:
            continue

        dates = sorted(team_dates[team])
        if not dates:
            continue

        # Fetch in season chunks (Open-Meteo handles up to ~1 year)
        # Group by year
        by_year = defaultdict(list)
        for d in dates:
            by_year[d[:4]].append(d)

        for year, year_dates in sorted(by_year.items()):
            start = year_dates[0]
            end = year_dates[-1]

            try:
                weather = fetch_weather_bulk(coords[0], coords[1], start, end)
                inserted = 0
                for gd in year_dates:
                    w = weather.get(gd)
                    if w:
                        conn.execute("""
                            INSERT OR IGNORE INTO mlb_weather_history
                            (game_date, home_team, temperature_f, wind_speed_mph, humidity_pct, precipitation_mm)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (gd, team, w["temp"], w["wind"], w["humidity"], w["precip"]))
                        inserted += 1
                conn.commit()
                fetched += inserted
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  Error fetching {team} {year}: {e}")
                time.sleep(1)

        print(f"  {team}: fetched weather for {len(dates)} dates")

    total = conn.execute("SELECT COUNT(*) FROM mlb_weather_history").fetchone()[0]
    print(f"\nTotal weather records: {total}")
    print(f"Fetched: {fetched}, Errors: {errors}")
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()

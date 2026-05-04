#!/usr/bin/env python3
"""
Game-Time Weather Fetcher for MLB

Fetches weather conditions at game time for outdoor MLB stadiums.
Uses Open-Meteo API (free, no key required, unlimited calls).

Weather affects MLB totals significantly:
- Wind speed/direction: 5+ mph out = more HRs
- Temperature: hot = ball carries, cold = dead
- Humidity: some effect on ball flight
- Rain: game delays, different ball grip
"""

import json
import sqlite3
import sys
from datetime import datetime, timedelta

import httpx

DB_PATH = "/home/aiciv/sports-edge/data/sports_edge.db"

# Stadium coordinates (lat, lon)
STADIUM_COORDS = {
    "ARI": (33.4455, -112.0667),   # Chase Field (retractable roof)
    "ATL": (33.8907, -84.4677),
    "BAL": (39.2838, -76.6216),
    "BOS": (42.3467, -71.0972),
    "CHC": (41.9484, -87.6553),
    "CWS": (41.8299, -87.6338),
    "CIN": (39.0975, -84.5086),
    "CLE": (41.4962, -81.6852),
    "COL": (39.7561, -104.9942),
    "DET": (42.3390, -83.0485),
    "HOU": (29.7573, -95.3555),    # Minute Maid (retractable roof)
    "KC":  (39.0517, -94.4803),
    "LAA": (33.8003, -117.8827),
    "LAD": (34.0739, -118.2400),
    "MIA": (25.7781, -80.2196),    # LoanDepot (retractable roof)
    "MIL": (43.0280, -87.9712),    # AmFam (retractable roof)
    "MIN": (44.9817, -93.2776),
    "NYM": (40.7571, -73.8458),
    "NYY": (40.8296, -73.9262),
    "OAK": (37.7516, -122.2005),
    "PHI": (39.9061, -75.1665),
    "PIT": (40.4469, -80.0058),
    "SD":  (32.7076, -117.1570),
    "SF":  (37.7786, -122.3893),
    "SEA": (47.5914, -122.3325),   # T-Mobile (retractable roof)
    "STL": (38.6226, -90.1928),
    "TB":  (27.7682, -82.6534),    # Tropicana (dome - skip weather)
    "TEX": (32.7512, -97.0832),    # Globe Life (retractable roof)
    "TOR": (43.6414, -79.3894),    # Rogers Centre (retractable roof)
    "WSH": (38.8730, -77.0074),
}

# Domed/roofed stadiums where weather doesn't affect play as much
INDOOR_STADIUMS = {"TB"}  # Tropicana is always closed
RETRACTABLE = {"ARI", "HOU", "MIA", "MIL", "SEA", "TEX", "TOR"}


def fetch_weather(lat: float, lon: float, date: str, hour: int = 19) -> dict:
    """Fetch weather for a location and date using Open-Meteo (free API).

    Args:
        lat, lon: Stadium coordinates
        date: Game date (YYYY-MM-DD)
        hour: Local game start hour (default 7pm)

    Returns:
        Dict with temperature_f, wind_speed_mph, wind_direction, humidity, precipitation
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
        "start_date": date,
        "end_date": date,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "America/New_York"
    }

    resp = httpx.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get("hourly", {})
    # Get the hour closest to game time
    idx = min(hour, len(hourly.get("temperature_2m", [])) - 1)

    return {
        "temperature_f": hourly.get("temperature_2m", [None])[idx],
        "humidity": hourly.get("relative_humidity_2m", [None])[idx],
        "wind_speed_mph": hourly.get("wind_speed_10m", [None])[idx],
        "wind_direction": hourly.get("wind_direction_10m", [None])[idx],
        "precipitation_mm": hourly.get("precipitation", [None])[idx],
    }


def fetch_today_weather() -> list[dict]:
    """Fetch weather for all outdoor MLB games today."""
    today = datetime.now().strftime("%Y-%m-%d")
    results = []

    conn = sqlite3.connect(DB_PATH)
    # Get today's scheduled games
    games = conn.execute("""
        SELECT game_pk, home_team_abbrev, away_team_abbrev
        FROM mlb_schedule
        WHERE game_date = ?
    """, (today,)).fetchall()
    conn.close()

    if not games:
        print(f"No MLB games scheduled for {today}")
        return results

    for game_id, home, away in games:
        if home in INDOOR_STADIUMS:
            results.append({
                "game_id": game_id,
                "home": home,
                "away": away,
                "indoor": True,
                "weather": None
            })
            continue

        coords = STADIUM_COORDS.get(home)
        if not coords:
            continue

        try:
            weather = fetch_weather(coords[0], coords[1], today)
            weather["is_retractable"] = home in RETRACTABLE
            results.append({
                "game_id": game_id,
                "home": home,
                "away": away,
                "indoor": False,
                "weather": weather
            })
            print(f"  {away} @ {home}: {weather['temperature_f']}F, "
                  f"wind {weather['wind_speed_mph']}mph, "
                  f"humidity {weather['humidity']}%"
                  f"{' (retractable roof)' if home in RETRACTABLE else ''}")
        except Exception as e:
            print(f"  {away} @ {home}: Weather fetch failed: {e}")

    return results


def store_weather(results: list[dict]):
    """Store weather data in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mlb_game_weather (
            game_id TEXT PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            temperature_f REAL,
            humidity REAL,
            wind_speed_mph REAL,
            wind_direction REAL,
            precipitation_mm REAL,
            is_indoor INTEGER,
            is_retractable INTEGER,
            fetched_at TEXT
        )
    """)

    for r in results:
        w = r.get("weather") or {}
        try:
            conn.execute("""
                INSERT OR REPLACE INTO mlb_game_weather
                (game_id, home_team, away_team, temperature_f, humidity,
                 wind_speed_mph, wind_direction, precipitation_mm,
                 is_indoor, is_retractable, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["game_id"], r["home"], r["away"],
                w.get("temperature_f"), w.get("humidity"),
                w.get("wind_speed_mph"), w.get("wind_direction"),
                w.get("precipitation_mm"),
                1 if r["indoor"] else 0,
                1 if w.get("is_retractable") else 0,
                datetime.now().isoformat()
            ))
        except Exception as e:
            print(f"  Store error for {r['game_id']}: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("MLB Game Weather Fetcher")
    print("=" * 50)
    results = fetch_today_weather()
    if results:
        store_weather(results)
        print(f"\nStored weather for {len(results)} games")

        # Summary
        outdoor = [r for r in results if not r["indoor"] and r["weather"]]
        if outdoor:
            temps = [r["weather"]["temperature_f"] for r in outdoor if r["weather"]["temperature_f"]]
            winds = [r["weather"]["wind_speed_mph"] for r in outdoor if r["weather"]["wind_speed_mph"]]
            if temps:
                print(f"Temperature range: {min(temps):.0f}F - {max(temps):.0f}F")
            if winds:
                print(f"Wind range: {min(winds):.0f} - {max(winds):.0f} mph")

"""
Sports Edge - Real Data Backtesting Engine
Pulls historical odds from the-odds-api and real game results from NBA CDN.
Outputs JSON for the frontend to consume.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta

API_KEY = "077a2076a8f81c71bd1178368809cf8b"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# NBA team mapping
TEAM_MAP = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}


def fetch_json(url, headers=None):
    """Fetch JSON from URL with error handling."""
    hdrs = {"User-Agent": "Mozilla/5.0"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR fetching {url[:80]}: {e}", file=sys.stderr)
        return None


def get_game_ids_for_date(date_str):
    """Get NBA game IDs for a specific date from the schedule."""
    # date_str format: "2025-03-01"
    cache_file = os.path.join(DATA_DIR, f"schedule_{date_str[:4]}.json")

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            schedule = json.load(f)
    else:
        # Determine season
        year = int(date_str[:4])
        month = int(date_str[5:7])
        season_year = year if month >= 10 else year - 1
        url = f"https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
        schedule = fetch_json(url)
        if schedule:
            with open(cache_file, "w") as f:
                json.dump(schedule, f)

    if not schedule:
        return []

    game_ids = []
    target = datetime.strptime(date_str, "%Y-%m-%d")
    for gd in schedule.get("leagueSchedule", {}).get("gameDates", []):
        gd_str = gd.get("gameDate", "")[:10]
        try:
            gd_date = datetime.strptime(gd_str, "%m/%d/%Y")
        except:
            continue
        if gd_date.date() == target.date():
            for game in gd.get("games", []):
                if game.get("gameStatus") == 3:  # Final
                    game_ids.append({
                        "gameId": game["gameId"],
                        "home": game.get("homeTeam", {}).get("teamTricode", ""),
                        "away": game.get("awayTeam", {}).get("teamTricode", ""),
                    })
            break
    return game_ids


def get_box_score(game_id):
    """Fetch box score for a specific game."""
    cache_file = os.path.join(DATA_DIR, f"box_{game_id}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)

    url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
    data = fetch_json(url)
    if data:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    return data


def get_historical_props(date_str):
    """Fetch historical player props from the-odds-api for a date."""
    cache_file = os.path.join(DATA_DIR, f"props_{date_str}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)

    # Get events for the date
    ts = f"{date_str}T12:00:00Z"
    events_url = f"https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events?apiKey={API_KEY}&date={ts}"
    events_data = fetch_json(events_url)

    if not events_data or "data" not in events_data:
        return None

    events = events_data["data"]
    print(f"  {date_str}: Found {len(events)} events")

    all_props = []
    for event in events:
        eid = event["id"]
        props_url = (
            f"https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events/{eid}/odds"
            f"?apiKey={API_KEY}&regions=us"
            f"&markets=player_points,player_rebounds,player_assists,player_threes"
            f"&date={ts}&oddsFormat=american"
        )
        props_data = fetch_json(props_url)
        if props_data and "data" in props_data:
            props_data["data"]["_home"] = event.get("home_team", "")
            props_data["data"]["_away"] = event.get("away_team", "")
            all_props.append(props_data["data"])
        time.sleep(0.2)  # Rate limit

    result = {"date": date_str, "events": all_props}
    with open(cache_file, "w") as f:
        json.dump(result, f)
    return result


def extract_player_stats(box_data):
    """Extract player stats from box score data."""
    if not box_data:
        return []

    game = box_data.get("game", {})
    stats = []

    for team_key in ["homeTeam", "awayTeam"]:
        team = game.get(team_key, {})
        team_tri = team.get("teamTricode", "")
        is_home = team_key == "homeTeam"

        for player in team.get("players", []):
            s = player.get("statistics", {})
            if s.get("minutes", "PT00M") == "PT00M":
                continue  # DNP

            # Parse minutes from ISO duration "PT32M15.00S"
            min_str = s.get("minutes", "PT0M")
            mins = 0
            if "M" in min_str:
                try:
                    mins = int(min_str.split("T")[1].split("M")[0])
                except:
                    pass

            stats.append({
                "name": player.get("name", ""),
                "team": team_tri,
                "home": is_home,
                "min": mins,
                "pts": s.get("points", 0),
                "reb": s.get("reboundsTotal", 0),
                "ast": s.get("assists", 0),
                "fg3m": s.get("threePointersMade", 0),
            })

    return stats


def extract_prop_lines(props_data):
    """Extract player prop lines from odds API data."""
    if not props_data:
        return []

    lines = []
    for event in props_data.get("events", []):
        home_full = event.get("_home", "")
        away_full = event.get("_away", "")
        home_tri = TEAM_MAP.get(home_full, "")
        away_tri = TEAM_MAP.get(away_full, "")

        for bookmaker in event.get("bookmakers", []):
            book = bookmaker.get("title", "")
            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")
                stat_map = {
                    "player_points": "pts",
                    "player_rebounds": "reb",
                    "player_assists": "ast",
                    "player_threes": "fg3m",
                }
                stat = stat_map.get(market_key)
                if not stat:
                    continue

                outcomes = market.get("outcomes", [])
                # Group by player
                player_lines = {}
                for o in outcomes:
                    pname = o.get("description", "")
                    if pname not in player_lines:
                        player_lines[pname] = {}
                    player_lines[pname][o["name"].lower()] = {
                        "price": o.get("price"),
                        "point": o.get("point"),
                    }

                for pname, sides in player_lines.items():
                    over = sides.get("over", {})
                    under = sides.get("under", {})
                    if over.get("point") is not None:
                        lines.append({
                            "player": pname,
                            "stat": stat,
                            "line": over["point"],
                            "over_odds": over.get("price", -110),
                            "under_odds": under.get("price", -110),
                            "book": book,
                            "home_team": home_tri,
                            "away_team": away_tri,
                        })

    return lines


def run_backtest(dates, output_file="backtest_results.json"):
    """Run backtest across multiple dates."""
    print(f"Starting backtest for {len(dates)} dates...")

    all_results = []
    requests_used = 0

    for date_str in dates:
        print(f"\n=== {date_str} ===")

        # 1. Get historical prop lines (uses API requests)
        props = get_historical_props(date_str)
        if not props:
            print(f"  Skipping {date_str}: no props data")
            continue
        requests_used += 1 + len(props.get("events", []))

        prop_lines = extract_prop_lines(props)
        print(f"  {len(prop_lines)} prop lines found")

        # 2. Get actual game results
        game_ids = get_game_ids_for_date(date_str)
        print(f"  {len(game_ids)} games found")

        actual_stats = []
        for ginfo in game_ids:
            box = get_box_score(ginfo["gameId"])
            pstats = extract_player_stats(box)
            actual_stats.extend(pstats)

        print(f"  {len(actual_stats)} player stats loaded")

        # 3. Match props to results
        for prop in prop_lines:
            # Find matching player in actual stats
            actual = None
            for s in actual_stats:
                # Fuzzy name match
                if prop["player"].lower() in s["name"].lower() or s["name"].lower() in prop["player"].lower():
                    actual = s
                    break
                # Try last name match
                prop_last = prop["player"].split()[-1].lower() if prop["player"] else ""
                stat_last = s["name"].split()[-1].lower() if s["name"] else ""
                if prop_last and stat_last and prop_last == stat_last:
                    # Verify team context
                    actual = s
                    break

            if actual is None:
                continue

            actual_val = actual.get(prop["stat"], 0)
            line = prop["line"]

            # Determine result
            over_won = actual_val > line
            under_won = actual_val < line
            push = actual_val == line

            all_results.append({
                "date": date_str,
                "player": prop["player"],
                "stat": prop["stat"],
                "line": line,
                "actual": actual_val,
                "over_odds": prop["over_odds"],
                "under_odds": prop["under_odds"],
                "over_won": over_won,
                "under_won": under_won,
                "push": push,
                "book": prop["book"],
                "player_team": actual.get("team", ""),
                "minutes": actual.get("min", 0),
            })

    output_path = os.path.join(DATA_DIR, output_file)
    with open(output_path, "w") as f:
        json.dump({
            "total_props": len(all_results),
            "dates_covered": len(dates),
            "requests_used": requests_used,
            "results": all_results,
        }, f, indent=2)

    print(f"\n=== DONE ===")
    print(f"Total matched props: {len(all_results)}")
    print(f"API requests used: ~{requests_used}")
    print(f"Results saved to: {output_path}")
    return all_results


if __name__ == "__main__":
    # Pull data for a sample of dates across the 2024-25 season
    # Start with 5 dates to test, then expand
    sample_dates = []

    # Generate dates: every Saturday from Jan-Mar 2025 (busy NBA schedule)
    start = datetime(2025, 1, 4)
    end = datetime(2025, 3, 29)
    d = start
    while d <= end:
        sample_dates.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=7)  # Weekly samples

    # Limit initial run to save API requests
    max_dates = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    dates_to_run = sample_dates[:max_dates]

    print(f"Will fetch data for {len(dates_to_run)} dates")
    print(f"Estimated API requests: ~{len(dates_to_run) * 8} (events + props per event)")
    print(f"Free tier limit: 500/month")
    print()

    results = run_backtest(dates_to_run)

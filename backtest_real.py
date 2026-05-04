"""
Sports Edge - REAL DATA Backtester
Uses:
- the-odds-api.com for historical sportsbook prop lines
- NBA CDN for actual game results (box scores)
- 2025-26 season (current, with completed games)
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


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        print(f"  FETCH ERROR: {e}", file=sys.stderr)
        return None


def load_schedule():
    """Load the 2025-26 schedule and index games by date."""
    cache = os.path.join(DATA_DIR, "schedule_2025.json")
    if os.path.exists(cache):
        with open(cache) as f:
            return json.load(f)
    data = fetch_json("https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json")
    if data:
        with open(cache, "w") as f:
            json.dump(data, f)
    return data


def get_game_ids_for_date(schedule, date_str):
    """Get completed game IDs for a date. date_str = 'YYYY-MM-DD'"""
    target = datetime.strptime(date_str, "%Y-%m-%d")
    for gd in schedule.get("leagueSchedule", {}).get("gameDates", []):
        gd_str = gd.get("gameDate", "")[:10]
        try:
            gd_date = datetime.strptime(gd_str, "%m/%d/%Y")
        except:
            continue
        if gd_date.date() == target.date():
            results = []
            for g in gd.get("games", []):
                if g.get("gameStatus") == 3:
                    results.append({
                        "gameId": g["gameId"],
                        "home": g.get("homeTeam", {}).get("teamTricode", ""),
                        "away": g.get("awayTeam", {}).get("teamTricode", ""),
                    })
            return results
    return []


def get_box_score(game_id):
    cache = os.path.join(DATA_DIR, f"box_{game_id}.json")
    if os.path.exists(cache):
        with open(cache) as f:
            return json.load(f)
    url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
    data = fetch_json(url)
    if data:
        with open(cache, "w") as f:
            json.dump(data, f)
    return data


def get_historical_props(date_str):
    """Fetch player props from odds API for a historical date."""
    cache = os.path.join(DATA_DIR, f"props_{date_str}.json")
    if os.path.exists(cache):
        with open(cache) as f:
            return json.load(f)

    ts = f"{date_str}T18:00:00Z"  # Evening snapshot

    # Get events
    eurl = f"https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events?apiKey={API_KEY}&date={ts}"
    edata = fetch_json(eurl)
    if not edata or "data" not in edata:
        print(f"  No events for {date_str}")
        return None

    events = edata["data"]
    print(f"  {len(events)} events on {date_str}")

    all_props = []
    for ev in events:
        purl = (
            f"https://api.the-odds-api.com/v4/historical/sports/basketball_nba/events/{ev['id']}/odds"
            f"?apiKey={API_KEY}&regions=us"
            f"&markets=player_points,player_rebounds,player_assists,player_threes"
            f"&date={ts}&oddsFormat=american"
        )
        pdata = fetch_json(purl)
        if pdata and "data" in pdata:
            pdata["data"]["_home"] = ev.get("home_team", "")
            pdata["data"]["_away"] = ev.get("away_team", "")
            all_props.append(pdata["data"])
        time.sleep(0.15)

    result = {"date": date_str, "events": all_props}
    with open(cache, "w") as f:
        json.dump(result, f)
    return result


def extract_stats(box_data):
    """Pull player stats from a box score."""
    if not box_data:
        return []
    game = box_data.get("game", {})
    stats = []
    for tk in ["homeTeam", "awayTeam"]:
        team = game.get(tk, {})
        tri = team.get("teamTricode", "")
        for p in team.get("players", []):
            s = p.get("statistics", {})
            mins_str = s.get("minutes", "PT00M")
            mins = 0
            try:
                mins = int(mins_str.split("T")[1].split("M")[0])
            except:
                pass
            if mins == 0:
                continue
            stats.append({
                "name": p.get("name", ""),
                "team": tri,
                "pts": s.get("points", 0),
                "reb": s.get("reboundsTotal", 0),
                "ast": s.get("assists", 0),
                "fg3m": s.get("threePointersMade", 0),
                "min": mins,
            })
    return stats


def match_name(prop_name, stat_name):
    """Fuzzy match player names between odds API and NBA box score."""
    pn = prop_name.lower().strip()
    sn = stat_name.lower().strip()
    if pn == sn:
        return True
    # Last name match
    p_last = pn.split()[-1] if pn else ""
    s_last = sn.split()[-1] if sn else ""
    p_first = pn.split()[0] if pn else ""
    s_first = sn.split()[0] if sn else ""
    if p_last == s_last and p_first[0] == s_first[0]:
        return True
    # Handle Jr/Sr/III suffixes
    if p_last in ("jr", "sr", "ii", "iii", "iv"):
        p_last = pn.split()[-2] if len(pn.split()) > 2 else p_last
    if s_last in ("jr", "sr", "ii", "iii", "iv"):
        s_last = sn.split()[-2] if len(sn.split()) > 2 else s_last
    if p_last == s_last and len(p_first) > 0 and len(s_first) > 0 and p_first[0] == s_first[0]:
        return True
    return False


def run(num_dates=5):
    print("=" * 60)
    print("SPORTS EDGE - REAL DATA BACKTEST")
    print("=" * 60)

    schedule = load_schedule()
    if not schedule:
        print("ERROR: Could not load schedule")
        return

    # Find dates with completed games in Feb-Apr 2026
    available_dates = []
    for gd in schedule.get("leagueSchedule", {}).get("gameDates", []):
        gd_str = gd.get("gameDate", "")[:10]
        try:
            gd_date = datetime.strptime(gd_str, "%m/%d/%Y")
        except:
            continue
        final_count = sum(1 for g in gd.get("games", []) if g.get("gameStatus") == 3)
        if final_count >= 5 and gd_date >= datetime(2026, 1, 1) and gd_date <= datetime(2026, 4, 11):
            available_dates.append(gd_date.strftime("%Y-%m-%d"))

    print(f"\nFound {len(available_dates)} dates with 5+ completed games")

    # Sample evenly across the range
    step = max(1, len(available_dates) // num_dates)
    selected = available_dates[::step][:num_dates]
    print(f"Selected {len(selected)} dates for backtest: {selected}")

    api_requests = 0
    all_matched = []

    for date_str in selected:
        print(f"\n--- {date_str} ---")

        # 1. Get prop lines
        props = get_historical_props(date_str)
        if not props:
            continue
        api_requests += 1 + len(props.get("events", []))

        # Extract all prop lines
        prop_lines = []
        for event in props.get("events", []):
            for bk in event.get("bookmakers", []):
                for mkt in bk.get("markets", []):
                    stat_map = {"player_points": "pts", "player_rebounds": "reb",
                                "player_assists": "ast", "player_threes": "fg3m"}
                    stat = stat_map.get(mkt.get("key"))
                    if not stat:
                        continue
                    by_player = {}
                    for o in mkt.get("outcomes", []):
                        pn = o.get("description", "")
                        if pn not in by_player:
                            by_player[pn] = {}
                        by_player[pn][o["name"].lower()] = {"price": o.get("price"), "point": o.get("point")}
                    for pn, sides in by_player.items():
                        ov = sides.get("over", {})
                        un = sides.get("under", {})
                        if ov.get("point") is not None:
                            prop_lines.append({
                                "player": pn, "stat": stat,
                                "line": ov["point"],
                                "over_odds": ov.get("price", -110),
                                "under_odds": un.get("price", -110),
                                "book": bk.get("title", ""),
                            })

        print(f"  {len(prop_lines)} prop lines from sportsbooks")

        # 2. Get actual results
        game_ids = get_game_ids_for_date(schedule, date_str)
        print(f"  {len(game_ids)} completed games")

        all_stats = []
        for gi in game_ids:
            box = get_box_score(gi["gameId"])
            all_stats.extend(extract_stats(box))
        print(f"  {len(all_stats)} player stat lines")

        # 3. Match props to actuals
        matched = 0
        for prop in prop_lines:
            for s in all_stats:
                if match_name(prop["player"], s["name"]):
                    actual_val = s.get(prop["stat"], 0)
                    line = prop["line"]
                    all_matched.append({
                        "date": date_str,
                        "player": s["name"],
                        "prop_name": prop["player"],
                        "stat": prop["stat"],
                        "line": line,
                        "actual": actual_val,
                        "over_won": actual_val > line,
                        "under_won": actual_val < line,
                        "push": actual_val == line,
                        "over_odds": prop["over_odds"],
                        "under_odds": prop["under_odds"],
                        "book": prop["book"],
                        "minutes": s.get("min", 0),
                    })
                    matched += 1
                    break

        print(f"  {matched} props matched to results")

    # 4. Analyze results
    print(f"\n{'=' * 60}")
    print(f"BACKTEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Dates: {len(selected)}")
    print(f"Total matched props: {len(all_matched)}")
    print(f"API requests used: ~{api_requests}")

    if all_matched:
        # Basic over/under accuracy
        overs_won = sum(1 for m in all_matched if m["over_won"])
        unders_won = sum(1 for m in all_matched if m["under_won"])
        pushes = sum(1 for m in all_matched if m["push"])
        total = len(all_matched)

        print(f"\nOverall line accuracy:")
        print(f"  Overs hit:  {overs_won}/{total} ({overs_won/total*100:.1f}%)")
        print(f"  Unders hit: {unders_won}/{total} ({unders_won/total*100:.1f}%)")
        print(f"  Pushes:     {pushes}/{total} ({pushes/total*100:.1f}%)")

        # By stat type
        for stat in ["pts", "reb", "ast", "fg3m"]:
            subset = [m for m in all_matched if m["stat"] == stat]
            if not subset:
                continue
            ow = sum(1 for m in subset if m["over_won"])
            uw = sum(1 for m in subset if m["under_won"])
            n = len(subset)
            print(f"\n  {stat.upper()}: {n} props")
            print(f"    Overs:  {ow}/{n} ({ow/n*100:.1f}%)")
            print(f"    Unders: {uw}/{n} ({uw/n*100:.1f}%)")

            # Average deviation from line
            devs = [m["actual"] - m["line"] for m in subset]
            avg_dev = sum(devs) / len(devs)
            print(f"    Avg deviation from line: {avg_dev:+.2f}")

        # Simulate flat betting on overs vs unders
        print(f"\n{'=' * 60}")
        print(f"SIMPLE STRATEGY TEST: Flat $100 bets")
        print(f"{'=' * 60}")

        for side_name, side_check in [("ALL OVERS", "over_won"), ("ALL UNDERS", "under_won")]:
            wins = sum(1 for m in all_matched if m[side_check])
            losses = sum(1 for m in all_matched if not m[side_check] and not m["push"])
            psh = sum(1 for m in all_matched if m["push"])
            # Assume -110 average odds
            profit = wins * 90.91 - losses * 100
            roi = profit / (total * 100) * 100
            print(f"\n  {side_name}:")
            print(f"    W/L/P: {wins}/{losses}/{psh}")
            print(f"    Win rate: {wins/(wins+losses)*100:.1f}%")
            print(f"    Profit: ${profit:+,.0f}")
            print(f"    ROI: {roi:+.2f}%")

    # Save results
    output = os.path.join(DATA_DIR, "real_backtest.json")
    with open(output, "w") as f:
        json.dump({
            "dates": selected,
            "total_props": len(all_matched),
            "api_requests": api_requests,
            "results": all_matched,
        }, f, indent=2)
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run(n)

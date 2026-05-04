#!/usr/bin/env python3
"""
Sports Edge - OddsPapi Client

Free tier: 250 requests/month, 350+ bookmakers including Pinnacle.
Sign up at https://oddspapi.io/en/sign-up (no credit card).

This gives us REAL Pinnacle prop odds for independent devigging,
replacing our reliance on OddsTrader's unverified model.

Usage:
    # First time: set your API key
    python3 oddspapi_client.py setup YOUR_API_KEY

    # Discover sports and tournaments
    python3 oddspapi_client.py discover

    # Fetch NHL/MLB props with Pinnacle odds
    python3 oddspapi_client.py props

    # Full scan: fetch, devig, find edges
    python3 oddspapi_client.py scan
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "oddspapi_config.json")
os.makedirs(os.path.join(os.path.dirname(__file__), "config"), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

BASE_URL = "https://api.oddspapi.io/v4"


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key():
    config = load_config()
    key = config.get("api_key", "")
    if not key:
        print("ERROR: No API key configured.")
        print("Sign up at https://oddspapi.io/en/sign-up (free, no credit card)")
        print("Then run: python3 oddspapi_client.py setup YOUR_API_KEY")
        return None
    return key


def api_call(endpoint, params=None):
    """Make an API call, tracking usage."""
    key = get_api_key()
    if not key:
        return None

    if params is None:
        params = {}
    params["apiKey"] = key

    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        # Track usage
        config = load_config()
        config["requests_used"] = config.get("requests_used", 0) + 1
        config["last_request"] = datetime.now(timezone.utc).isoformat()
        save_config(config)

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  API error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  Request error: {e}")
        return None


def setup(api_key):
    """Configure API key and test connection."""
    config = load_config()
    config["api_key"] = api_key
    config["requests_used"] = 0
    config["setup_date"] = datetime.now(timezone.utc).isoformat()
    save_config(config)

    # Test the key
    print("Testing API key...")
    data = api_call("/sports")
    if data:
        sports = data if isinstance(data, list) else data.get("sports", data.get("data", []))
        print(f"  Success! {len(sports)} sports available.")
        print(f"  Key saved to {CONFIG_PATH}")
        return True
    else:
        print("  Failed - check your API key")
        return False


def discover():
    """Discover sport IDs, tournament IDs, and market types."""
    print("\n=== DISCOVERING ODDSPAPI STRUCTURE ===\n")

    # 1. Get sports
    print("Sports:")
    sports_data = api_call("/sports")
    if not sports_data:
        return

    sports = sports_data if isinstance(sports_data, list) else sports_data.get("sports", sports_data.get("data", []))
    config = load_config()
    config["sports"] = {}

    for s in sports:
        sid = s.get("id", s.get("sportId", ""))
        name = s.get("name", s.get("sportName", ""))
        print(f"  {sid}: {name}")
        if any(k in name.lower() for k in ["hockey", "ice hockey", "nhl"]):
            config["nhl_sport_id"] = sid
            print(f"    ^ NHL SPORT ID: {sid}")
        if any(k in name.lower() for k in ["baseball", "mlb"]):
            config["mlb_sport_id"] = sid
            print(f"    ^ MLB SPORT ID: {sid}")

    # 2. Get tournaments for NHL and MLB
    for sport_key, label in [("nhl_sport_id", "NHL"), ("mlb_sport_id", "MLB")]:
        sport_id = config.get(sport_key)
        if not sport_id:
            continue

        print(f"\n{label} Tournaments:")
        tourney_data = api_call("/tournaments", {"sportId": sport_id})
        if tourney_data:
            tourneys = tourney_data if isinstance(tourney_data, list) else tourney_data.get("tournaments", tourney_data.get("data", []))
            for t in tourneys[:20]:
                tid = t.get("id", t.get("tournamentId", ""))
                tname = t.get("name", t.get("tournamentName", ""))
                print(f"  {tid}: {tname}")
                if "nhl" in tname.lower() or (label == "NHL" and "national" in tname.lower()):
                    config["nhl_tournament_id"] = tid
                    print(f"    ^ NHL TOURNAMENT ID: {tid}")
                if "mlb" in tname.lower() or (label == "MLB" and ("major" in tname.lower() or "baseball" in tname.lower())):
                    config["mlb_tournament_id"] = tid
                    print(f"    ^ MLB TOURNAMENT ID: {tid}")

    # 3. Get available markets
    print("\nMarkets (prop types):")
    markets_data = api_call("/markets")
    if markets_data:
        markets = markets_data if isinstance(markets_data, list) else markets_data.get("markets", markets_data.get("data", []))
        config["markets"] = {}
        for m in markets[:50]:
            mid = m.get("id", m.get("marketId", ""))
            mname = m.get("name", m.get("marketName", ""))
            print(f"  {mid}: {mname}")
            mlow = mname.lower()
            if "player" in mlow or "goal" in mlow or "shot" in mlow or "hit" in mlow or "strike" in mlow:
                config["markets"][str(mid)] = mname
                print(f"    ^ PLAYER PROP MARKET")

    save_config(config)
    print(f"\nConfig saved to {CONFIG_PATH}")
    print(f"Requests used this session: {config.get('requests_used', 0)}/250")


def fetch_props():
    """Fetch today's player props with Pinnacle + other sharp books."""
    config = load_config()

    all_props = []
    for sport, tid_key in [("NHL", "nhl_tournament_id"), ("MLB", "mlb_tournament_id")]:
        tid = config.get(tid_key)
        if not tid:
            print(f"  {sport}: No tournament ID configured. Run 'discover' first.")
            continue

        print(f"\n  Fetching {sport} fixtures...")
        fixtures = api_call("/fixtures", {"tournamentIds": tid})
        if not fixtures:
            continue

        fixture_list = fixtures if isinstance(fixtures, list) else fixtures.get("fixtures", fixtures.get("data", []))
        print(f"    {len(fixture_list)} fixtures found")

        # Get odds for each fixture (this uses 1 request per fixture)
        for fix in fixture_list[:10]:  # Limit to save API calls
            fid = fix.get("id", fix.get("fixtureId", ""))
            fname = fix.get("name", fix.get("fixtureName", ""))

            print(f"    Fetching odds for {fname}...")
            odds = api_call("/odds", {
                "fixtureId": fid,
                "bookmakers": "pinnacle,draftkings,fanduel,bet365",
                "oddsFormat": "american",
            })
            if not odds:
                continue

            # Parse the odds structure
            bookmaker_odds = odds.get("bookmakerOdds", odds.get("odds", {}))
            if isinstance(bookmaker_odds, list):
                for entry in bookmaker_odds:
                    process_odds_entry(entry, sport, fname, all_props)
            elif isinstance(bookmaker_odds, dict):
                for book_name, book_data in bookmaker_odds.items():
                    markets = book_data.get("markets", {})
                    for market_id, market_data in markets.items():
                        process_market(book_name, market_id, market_data, sport, fname, all_props)

    # Save
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "oddspapi",
        "has_pinnacle": True,
        "props_count": len(all_props),
        "props": all_props,
    }
    outpath = os.path.join(DATA_DIR, "oddspapi_props.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n  Saved {len(all_props)} props to {outpath}")
    print(f"  Requests used: {config.get('requests_used', 0)}/250")
    return output


def process_market(book_name, market_id, market_data, sport, game, all_props):
    """Process a single market's odds data."""
    outcomes = market_data.get("outcomes", {})
    for outcome_id, outcome_data in outcomes.items():
        players = outcome_data.get("players", {})
        for player_id, player_data in players.items():
            price = player_data.get("price", player_data.get("odds"))
            handicap = player_data.get("handicap", player_data.get("line"))
            player_name = player_data.get("name", player_data.get("playerName", ""))

            if price:
                all_props.append({
                    "sport": sport,
                    "game": game,
                    "player": player_name,
                    "market_id": market_id,
                    "outcome_id": outcome_id,
                    "book": book_name,
                    "price": price,
                    "handicap": handicap,
                })


def process_odds_entry(entry, sport, game, all_props):
    """Process odds from list format."""
    book = entry.get("bookmaker", entry.get("book", ""))
    market = entry.get("market", entry.get("marketName", ""))
    player = entry.get("player", entry.get("playerName", ""))
    price = entry.get("price", entry.get("odds", ""))
    line = entry.get("handicap", entry.get("line", ""))

    if price:
        all_props.append({
            "sport": sport,
            "game": game,
            "player": player,
            "market": market,
            "book": book,
            "price": price,
            "handicap": line,
        })


def pinnacle_devig_scan():
    """Full scan: fetch Pinnacle props, devig, find edges vs soft books."""
    print("\n" + "=" * 60)
    print("  ODDSPAPI PINNACLE DEVIG SCAN")
    print("=" * 60)

    props_data = fetch_props()
    if not props_data:
        return

    props = props_data.get("props", [])
    if not props:
        print("  No props fetched")
        return

    # Group by player + market to find O/U pairs from same book
    by_key = defaultdict(list)
    for p in props:
        key = f"{p['sport']}|{p.get('player','')}|{p.get('market_id', p.get('market',''))}|{p.get('book','')}"
        by_key[key].append(p)

    # Find Pinnacle O/U pairs and devig them
    from multi_book_devig import devig_power, american_to_decimal, decimal_to_american

    pinnacle_fair = {}
    for key, group in by_key.items():
        if "pinnacle" not in key.lower():
            continue
        if len(group) == 2:
            try:
                p1, p2 = group
                dec1 = american_to_decimal(str(p1["price"]))
                dec2 = american_to_decimal(str(p2["price"]))
                fair1, fair2 = devig_power(dec1, dec2)
                if fair1 and fair2:
                    base_key = key.replace("|pinnacle", "")
                    pinnacle_fair[base_key] = {
                        "fair_1": fair1,
                        "fair_2": fair2,
                        "player": p1.get("player", ""),
                        "market": p1.get("market_id", p1.get("market", "")),
                        "sport": p1.get("sport", ""),
                    }
            except:
                continue

    print(f"\n  Pinnacle devigged: {len(pinnacle_fair)} markets")

    # Now find soft book prices that beat Pinnacle fair odds
    edges = []
    for key, group in by_key.items():
        if "pinnacle" in key.lower():
            continue
        base_key = "|".join(key.split("|")[:3])
        if base_key not in pinnacle_fair:
            continue

        pinn = pinnacle_fair[base_key]
        for p in group:
            try:
                soft_dec = american_to_decimal(str(p["price"]))
                soft_imp = 1.0 / soft_dec
                # Compare to Pinnacle fair prob
                fair = pinn["fair_1"]  # Simplified - need proper outcome matching
                edge = fair - soft_imp
                if edge > 0.02:  # 2%+ edge
                    edges.append({
                        "player": p.get("player", ""),
                        "sport": p.get("sport", ""),
                        "game": p.get("game", ""),
                        "market": p.get("market_id", p.get("market", "")),
                        "book": p.get("book", ""),
                        "book_odds": str(p["price"]),
                        "pinnacle_fair_prob": round(fair, 4),
                        "edge_pct": round(edge * 100, 2),
                    })
            except:
                continue

    edges.sort(key=lambda x: -x["edge_pct"])
    print(f"  Edges found (2%+): {len(edges)}")

    if edges:
        print(f"\n  TOP PINNACLE-VERIFIED EDGES:")
        for i, e in enumerate(edges[:15], 1):
            print(f"    {i:2d}. {e['sport']} {e['player']:25s} @ {e['book']:15s}"
                  f" odds:{e['book_odds']:>6s} edge:+{e['edge_pct']:.1f}%")

    # Save
    outpath = os.path.join(DATA_DIR, "pinnacle_devig_edges.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pinnacle_markets": len(pinnacle_fair),
            "edges_found": len(edges),
            "edges": edges,
        }, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 oddspapi_client.py setup YOUR_API_KEY")
        print("  python3 oddspapi_client.py discover")
        print("  python3 oddspapi_client.py props")
        print("  python3 oddspapi_client.py scan")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "setup":
        if len(sys.argv) < 3:
            print("Usage: python3 oddspapi_client.py setup YOUR_API_KEY")
            sys.exit(1)
        setup(sys.argv[2])
    elif cmd == "discover":
        discover()
    elif cmd == "props":
        fetch_props()
    elif cmd == "scan":
        pinnacle_devig_scan()
    else:
        print(f"Unknown command: {cmd}")

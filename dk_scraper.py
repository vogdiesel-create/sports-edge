"""
Sports Edge - FanDuel Props Scraper (works from our server)
+ DraftKings props via browser tool (user runs locally)

FanDuel's API is accessible from our server. We can poll it freely.
DraftKings blocks our IP but works from residential IPs (user's browser).

This script:
1. Scrapes FanDuel player props for all tonight's NBA games
2. Stores them in the odds_engine SQLite database
3. Detects +EV opportunities by comparing FanDuel lines to each other
   (within-book mispricing based on devigged fair probabilities)

When DraftKings data is available (via browser tool), cross-book
comparison becomes possible — that's the real money maker.
"""

import json
import os
import sqlite3
import sys
import time
import requests
from collections import defaultdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "odds_engine.db")

FD_BASE = "https://sbapi.mi.sportsbook.fanduel.com/api"
FD_AK = "FhMFpcPWXMeyZxOx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# FanDuel tab IDs for player props
FD_PROP_TABS = {
    168: "player_points",
    169: "player_assists",
    170: "player_rebounds",
    171: "player_combos",
    172: "player_threes",
}


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def devig(imp_a, imp_b):
    total = imp_a + imp_b
    if total <= 0:
        return 0.5, 0.5
    return imp_a / total, imp_b / total


def init_db():
    """Ensure the odds_engine database exists."""
    from odds_engine import init_db as _init
    return _init(DB_PATH)


class FanDuelScraper:
    """Scrape NBA player props from FanDuel's public API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_nba_events(self):
        """Get all NBA game events for today."""
        resp = self.session.get(
            f"{FD_BASE}/content-managed-page",
            params={
                "page": "CUSTOM",
                "customPageId": "nba",
                "pbHorizontal": "true",
                "_ak": FD_AK,
            }
        )
        if resp.status_code != 200:
            print(f"Error fetching events: {resp.status_code}")
            return []

        data = resp.json()
        events = data.get("attachments", {}).get("events", {})

        games = []
        for eid, ev in events.items():
            name = ev.get("name", "")
            if "v" in name.lower() or "@" in name.lower():
                games.append({
                    "id": eid,
                    "name": name,
                    "start": ev.get("openDate", ""),
                })
        return games

    def get_event_props(self, event_id):
        """Get all player prop markets for a specific game event."""
        all_props = []

        for tab_id, market_name in FD_PROP_TABS.items():
            # Map tab_id to URL tab name
            tab_url_map = {
                168: "player-points",
                169: "player-assists",
                170: "player-rebounds",
                171: "player-combos",
                172: "player-threes",
            }
            tab_url = tab_url_map.get(tab_id, "")

            resp = self.session.get(
                f"{FD_BASE}/event-page",
                params={
                    "eventId": event_id,
                    "tab": tab_url,
                    "_ak": FD_AK,
                }
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            markets = data.get("attachments", {}).get("markets", {})

            for mid, mkt in markets.items():
                mkt_name = mkt.get("marketName", "")
                mkt_type = mkt.get("marketType", "")
                runners = mkt.get("runners", [])

                # Look for milestone props (To Score X+, To Record X+)
                # These have implied over/under structure
                for runner in runners:
                    player_name = runner.get("runnerName", "")
                    handicap = runner.get("handicap", 0)
                    odds_data = runner.get("winRunnerOdds", {})
                    american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")

                    if not player_name or american is None:
                        continue

                    try:
                        american = int(american)
                    except (ValueError, TypeError):
                        continue

                    all_props.append({
                        "player": player_name,
                        "market": market_name,
                        "market_name": mkt_name,
                        "market_type": mkt_type,
                        "line": handicap,
                        "odds_american": american,
                        "odds_decimal": round(american_to_decimal(american), 4),
                    })

            time.sleep(0.3)

        return all_props

    def scrape_all_games(self):
        """Scrape props for all tonight's NBA games."""
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"\n{'='*65}")
        print(f"  FANDUEL NBA PLAYER PROPS SCRAPE")
        print(f"  {now}")
        print(f"{'='*65}")

        games = self.get_nba_events()
        print(f"\n  Found {len(games)} NBA games tonight")

        all_data = []
        for game in games:
            print(f"\n  {game['name']}...")
            props = self.get_event_props(game["id"])
            print(f"    {len(props)} prop lines found")

            for p in props:
                p["game"] = game["name"]
                p["event_id"] = game["id"]
                p["fetched_at"] = now

            all_data.extend(props)
            time.sleep(0.5)

        # Summary
        print(f"\n{'='*65}")
        print(f"  TOTAL: {len(all_data)} prop lines across {len(games)} games")

        if all_data:
            # Group by market type
            by_market = defaultdict(int)
            by_player = defaultdict(int)
            for p in all_data:
                by_market[p["market"]] += 1
                by_player[p["player"]] += 1

            print(f"\n  BY MARKET:")
            for m, c in sorted(by_market.items(), key=lambda x: -x[1]):
                print(f"    {m}: {c} lines")

            print(f"\n  TOP PLAYERS:")
            for p, c in sorted(by_player.items(), key=lambda x: -x[1])[:10]:
                print(f"    {p}: {c} lines")

        # Store in DB
        conn = init_db()
        stored = 0
        for p in all_data:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO odds_snapshots
                    (event_id, event_name, commence_time, book, market, player, line,
                     over_odds, under_odds, over_decimal, under_decimal, fetched_at)
                    VALUES (?, ?, ?, 'fanduel', ?, ?, ?,
                            ?, NULL, ?, NULL, ?)
                """, (p["event_id"], p["game"], "", p["market"],
                      p["player"], p["line"],
                      p["odds_american"], p["odds_decimal"], p["fetched_at"]))
                stored += 1
            except sqlite3.Error:
                pass
        conn.commit()
        print(f"\n  Stored {stored} snapshots in odds_engine.db")

        # Save raw JSON too
        outpath = os.path.join(DATA_DIR, "fanduel_props_latest.json")
        with open(outpath, "w") as f:
            json.dump({
                "scraped_at": now,
                "games": len(games),
                "total_props": len(all_data),
                "props": all_data,
            }, f, indent=2)
        print(f"  Saved to {outpath}")

        return all_data


def analyze_fanduel_props():
    """Analyze FanDuel props for potential value."""
    filepath = os.path.join(DATA_DIR, "fanduel_props_latest.json")
    if not os.path.exists(filepath):
        print("No FanDuel data yet. Run: python3 dk_scraper.py scrape")
        return

    with open(filepath) as f:
        data = json.load(f)

    props = data["props"]
    print(f"\n{'='*65}")
    print(f"  FANDUEL PROP ANALYSIS")
    print(f"  {data['scraped_at']}")
    print(f"{'='*65}")

    # Find props with the best implied value
    # For milestone props (To Score 30+), the implied probability tells us
    # what FanDuel thinks the chance is
    print(f"\n  BEST ODDS (highest implied probability of hitting):")
    sorted_props = sorted(props, key=lambda x: -x["odds_decimal"])

    # Show most likely to hit (lowest implied probability = worst for us to bet)
    # Show best value (highest decimal odds = lowest implied probability from book)
    for p in sorted_props[:20]:
        imp = decimal_to_implied(p["odds_decimal"])
        print(f"    {p['player']:25s} {p['market_name']:30s} @ {p['odds_american']:+5d} ({imp:.1%} implied)")

    # Cross-reference: when FanDuel offers very different odds on related props
    # for the same player, there might be internal inconsistency
    print(f"\n  LOOKING FOR INTERNAL INCONSISTENCIES...")
    by_player_market = defaultdict(list)
    for p in props:
        key = (p["player"], p["market"])
        by_player_market[key].append(p)

    for (player, market), player_props in by_player_market.items():
        if len(player_props) < 2:
            continue
        # Sort by line
        player_props.sort(key=lambda x: x.get("line", 0))
        for i in range(len(player_props) - 1):
            p1 = player_props[i]
            p2 = player_props[i + 1]
            imp1 = decimal_to_implied(p1["odds_decimal"])
            imp2 = decimal_to_implied(p2["odds_decimal"])
            # Higher line should have lower probability
            if imp2 > imp1 and p2.get("line", 0) > p1.get("line", 0):
                print(f"    ANOMALY: {player} {market}")
                print(f"      Line {p1.get('line',0)}: {imp1:.1%} vs Line {p2.get('line',0)}: {imp2:.1%}")
                print(f"      Higher line has HIGHER probability — mispricing!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "scrape":
            scraper = FanDuelScraper()
            scraper.scrape_all_games()
        elif cmd == "analyze":
            analyze_fanduel_props()
    else:
        # Default: scrape then analyze
        scraper = FanDuelScraper()
        props = scraper.scrape_all_games()
        if props:
            analyze_fanduel_props()

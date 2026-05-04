"""
Sports Edge - Multi-Book Odds Scraper
Scrapes odds from every accessible sportsbook and compares them.

Working sources (from our server):
1. FanDuel - Full player props (milestone format: To Score X+)
2. Bovada - Game lines + some player props (double-double, triple-double)

Blocked sources (need browser/proxy):
3. DraftKings - Blocked by Akamai WAF
4. BetMGM - Needs testing
5. Pinnacle - Needs API key

Strategy: Scrape what we can directly, use Netlify proxy or browser tool for the rest.
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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# FanDuel config
FD_BASE = "https://sbapi.mi.sportsbook.fanduel.com/api"
FD_AK = "FhMFpcPWXMeyZxOx"
FD_PROP_TABS = {
    "player-points": "player_points",
    "player-assists": "player_assists",
    "player-rebounds": "player_rebounds",
    "player-combos": "player_combos",
    "player-threes": "player_threes",
}

# Bovada config
BOV_BASE = "https://www.bovada.lv/services/sports/event/coupon/events/A/description"


def american_to_decimal(american):
    if isinstance(american, str):
        if american == "EVEN":
            return 2.0
        american = int(american.replace("+", ""))
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


class MultiBookScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.props = []  # All collected props across books

    def scrape_fanduel(self):
        """Scrape all FanDuel NBA player props."""
        print("\n  [FanDuel] Fetching NBA events...")
        resp = self.session.get(f"{FD_BASE}/content-managed-page",
            params={"page": "CUSTOM", "customPageId": "nba",
                    "pbHorizontal": "true", "_ak": FD_AK})
        if resp.status_code != 200:
            print(f"  [FanDuel] Error: {resp.status_code}")
            return

        data = resp.json()
        events = data.get("attachments", {}).get("events", {})
        games = []
        for eid, ev in events.items():
            name = ev.get("name", "")
            if "v" in name.lower() or "@" in name.lower():
                games.append({"id": eid, "name": name})

        print(f"  [FanDuel] {len(games)} games found")
        fd_count = 0

        for game in games:
            for tab_url, market_name in FD_PROP_TABS.items():
                resp = self.session.get(f"{FD_BASE}/event-page",
                    params={"eventId": game["id"], "tab": tab_url, "_ak": FD_AK})
                if resp.status_code != 200:
                    continue

                markets = resp.json().get("attachments", {}).get("markets", {})
                for mid, mkt in markets.items():
                    for runner in mkt.get("runners", []):
                        player = runner.get("runnerName", "")
                        handicap = runner.get("handicap", 0)
                        odds_data = runner.get("winRunnerOdds", {})
                        american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")
                        if not player or american is None:
                            continue
                        try:
                            american = int(american)
                        except (ValueError, TypeError):
                            continue

                        # Skip non-player entries (team names, Over/Under labels)
                        if player in ("Over", "Under", "Yes", "No", "Odd", "Even"):
                            continue

                        self.props.append({
                            "book": "fanduel",
                            "game": game["name"],
                            "player": player,
                            "market": market_name,
                            "market_name": mkt.get("marketName", ""),
                            "line": handicap,
                            "side": "over",  # FD milestone props are "To Score X+"
                            "odds_american": american,
                            "odds_decimal": round(american_to_decimal(american), 4),
                        })
                        fd_count += 1
                time.sleep(0.2)

        print(f"  [FanDuel] {fd_count} prop lines collected")

    def scrape_bovada(self):
        """Scrape Bovada NBA game lines and available player props."""
        print("\n  [Bovada] Fetching NBA events...")
        resp = self.session.get(f"{BOV_BASE}/basketball/nba")
        if resp.status_code != 200:
            print(f"  [Bovada] Error: {resp.status_code}")
            return

        data = resp.json()
        if not data or not isinstance(data, list):
            print(f"  [Bovada] Unexpected response format")
            return
        events = data[0].get("events", [])
        print(f"  [Bovada] {len(events)} games found")
        bov_count = 0

        for ev in events:
            desc = ev.get("description", "")
            for group in ev.get("displayGroups", []):
                for mkt in group.get("markets", []):
                    mdesc = mkt.get("description", "")
                    for outcome in mkt.get("outcomes", []):
                        odesc = outcome.get("description", "")
                        price = outcome.get("price", {})
                        american = price.get("american", "")
                        handicap = price.get("handicap", "")

                        if not american or american == "":
                            continue

                        try:
                            dec = american_to_decimal(american)
                        except (ValueError, TypeError):
                            continue

                        # Determine side
                        side = "over" if "over" in odesc.lower() else "under" if "under" in odesc.lower() else "pick"

                        # Map to standardized market names
                        market = self._map_bovada_market(mdesc, group.get("description", ""))

                        self.props.append({
                            "book": "bovada",
                            "game": desc,
                            "player": odesc,
                            "market": market,
                            "market_name": mdesc,
                            "line": float(handicap) if handicap else 0,
                            "side": side,
                            "odds_american": american,
                            "odds_decimal": round(dec, 4),
                        })
                        bov_count += 1

        print(f"  [Bovada] {bov_count} lines collected")

    def _map_bovada_market(self, market_desc, group_desc):
        md = market_desc.lower()
        if "moneyline" in md:
            return "moneyline"
        if "spread" in md or "point spread" in md:
            return "spread"
        if "total" in md:
            return "total"
        if "double" in md:
            return "player_combos"
        if "triple" in md:
            return "player_combos"
        return group_desc.lower().replace(" ", "_")

    def import_external(self, filepath):
        """Import odds from JSON file (e.g., DraftKings data from browser scraper)."""
        print(f"\n  [Import] Loading {filepath}...")
        with open(filepath) as f:
            data = json.load(f)

        imported = 0
        # Support multiple formats
        if "props" in data:
            for p in data["props"]:
                self.props.append(p)
                imported += 1
        elif "opportunities" in data:
            for p in data["opportunities"]:
                self.props.append(p)
                imported += 1
        elif isinstance(data, list):
            for p in data:
                self.props.append(p)
                imported += 1

        print(f"  [Import] {imported} lines imported")

    def compare_books(self):
        """
        Compare odds across books for the same props.
        This is where the money is.
        """
        print(f"\n{'='*70}")
        print(f"  MULTI-BOOK ODDS COMPARISON")
        print(f"{'='*70}")

        # Group by standardized key
        by_book = defaultdict(int)
        for p in self.props:
            by_book[p["book"]] += 1

        print(f"\n  Data sources:")
        for book, count in sorted(by_book.items()):
            print(f"    {book}: {count} lines")

        if len(by_book) < 2:
            print(f"\n  Need at least 2 books for comparison.")
            print(f"  Currently have: {list(by_book.keys())}")
            print(f"\n  To add more books:")
            print(f"    1. Deploy odds-scraper.html to Netlify (browser-based DK scraper)")
            print(f"    2. Deploy odds-proxy to Netlify (serverless proxy)")
            print(f"    3. Wait for the-odds-api quota reset")
            print(f"    4. Import DK data: python3 multi_book_scraper.py import dk_data.json")
            return

        # Find matching props across books
        # Normalize player names and match on (player, market, line)
        matches = defaultdict(lambda: defaultdict(list))
        for p in self.props:
            # Create normalized key
            player_norm = p["player"].lower().strip()
            key = (player_norm, p["market"], p.get("line", 0))
            matches[key][p["book"]].append(p)

        # Find cross-book matches
        cross_matches = {k: v for k, v in matches.items() if len(v) >= 2}
        print(f"\n  Cross-book matches: {len(cross_matches)}")

        if not cross_matches:
            print("  No matching props found across books.")
            print("  (Different books may use different player name formats)")
            return

        # Find +EV opportunities
        opportunities = []
        for (player, market, line), book_data in cross_matches.items():
            # Get implied probabilities from each book
            all_implied = []
            for book, props_list in book_data.items():
                for p in props_list:
                    imp = decimal_to_implied(p["odds_decimal"])
                    all_implied.append((book, p, imp))

            if len(all_implied) < 2:
                continue

            # Consensus fair probability (average of all books, devigged)
            avg_implied = sum(imp for _, _, imp in all_implied) / len(all_implied)

            # Check each book against consensus
            for book, prop, imp in all_implied:
                edge = avg_implied - imp  # Positive = book is offering better odds than fair
                ev = avg_implied * (prop["odds_decimal"] - 1) - (1 - avg_implied)

                if edge > 0.03 and ev > 0.02:
                    opportunities.append({
                        "player": player,
                        "market": market,
                        "line": line,
                        "book": book,
                        "odds": prop["odds_american"],
                        "decimal": prop["odds_decimal"],
                        "implied": round(imp, 4),
                        "fair": round(avg_implied, 4),
                        "edge": round(edge, 4),
                        "ev": round(ev, 4),
                        "game": prop.get("game", ""),
                    })

        if opportunities:
            opportunities.sort(key=lambda x: -x["ev"])
            print(f"\n  +EV OPPORTUNITIES: {len(opportunities)}")
            for i, opp in enumerate(opportunities[:20], 1):
                print(f"\n  {i}. {opp['player']} — {opp['market']} {opp['line']}")
                print(f"     Book: {opp['book']} @ {opp['odds']}")
                print(f"     Fair: {opp['fair']:.1%} | Implied: {opp['implied']:.1%} | Edge: {opp['edge']:.1%} | EV: {opp['ev']:.1%}")
                print(f"     Game: {opp['game']}")

            # Save
            outpath = os.path.join(DATA_DIR, "multi_book_opportunities.json")
            with open(outpath, "w") as f:
                json.dump({"scan_time": datetime.utcnow().isoformat(),
                          "opportunities": opportunities}, f, indent=2)
            print(f"\n  Saved to {outpath}")
        else:
            print(f"\n  No +EV opportunities found in cross-book comparison.")

    def run(self):
        """Full scrape cycle."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        print(f"{'='*70}")
        print(f"  MULTI-BOOK NBA ODDS SCRAPER")
        print(f"  {now}")
        print(f"{'='*70}")

        self.scrape_fanduel()
        self.scrape_bovada()

        # Check for imported data
        dk_path = os.path.join(DATA_DIR, "dk_import.json")
        if os.path.exists(dk_path):
            self.import_external(dk_path)

        # Summary
        print(f"\n  TOTAL: {len(self.props)} lines from {len(set(p['book'] for p in self.props))} books")

        # Save all data
        outpath = os.path.join(DATA_DIR, "multi_book_latest.json")
        with open(outpath, "w") as f:
            json.dump({"scraped_at": now, "total": len(self.props), "props": self.props}, f, indent=2)

        # Compare
        self.compare_books()


if __name__ == "__main__":
    scraper = MultiBookScraper()
    if len(sys.argv) > 1 and sys.argv[1] == "import":
        filepath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATA_DIR, "dk_import.json")
        scraper.scrape_fanduel()
        scraper.scrape_bovada()
        scraper.import_external(filepath)
        scraper.compare_books()
    else:
        scraper.run()

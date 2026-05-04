"""
Sports Edge - Live Scanner
Automated +EV detection pipeline.

Data flow:
1. FanDuel: Auto-polled via Netlify proxy (1,400+ props, free)
2. Bovada: Auto-polled direct (game lines, free)
3. DraftKings: Imported from browser scraper (user runs manually)
4. the-odds-api: All books when quota available

Cross-compares all sources, devigs, flags +EV opportunities.
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
PROXY_URL = "https://sports-edge-proxy.netlify.app"
ODDS_API_KEY = "077a2076a8f81c71bd1178368809cf8b"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def american_to_decimal(odds):
    if isinstance(odds, str):
        if odds.upper() == "EVEN":
            return 2.0
        odds = int(odds.replace("+", ""))
    if odds > 0:
        return 1 + odds / 100
    return 1 + 100 / abs(odds)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def devig(imp_a, imp_b):
    total = imp_a + imp_b
    if total <= 0:
        return 0.5, 0.5
    return imp_a / total, imp_b / total


def kelly(prob, dec_odds, fraction=0.25):
    b = dec_odds - 1
    if b <= 0:
        return 0
    f = (b * prob - (1 - prob)) / b
    return max(0, f * fraction)


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS live_odds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book TEXT, player TEXT, stat TEXT, line REAL,
            side TEXT, odds_american INTEGER, odds_decimal REAL,
            game TEXT, fetched_at TEXT,
            UNIQUE(book, player, stat, line, side, fetched_at)
        );
        CREATE TABLE IF NOT EXISTS ev_alerts_live (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT, stat TEXT, line REAL, side TEXT,
            book TEXT, odds_american INTEGER, odds_decimal REAL,
            fair_prob REAL, edge REAL, ev REAL, kelly_pct REAL,
            n_books INTEGER, game TEXT, detected_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_live_odds_player ON live_odds(player, stat, line);
        CREATE INDEX IF NOT EXISTS idx_live_alerts_time ON ev_alerts_live(detected_at);
    """)
    conn.commit()
    return conn


class LiveScanner:
    def __init__(self):
        self.conn = init_db()
        self.props = []

    def fetch_fanduel_proxy(self):
        """Pull FanDuel props via Netlify proxy."""
        print("  [FanDuel] Fetching via proxy...")
        try:
            resp = requests.get(f"{PROXY_URL}/api/multi-book", timeout=30)
            data = resp.json()
            fd_status = data.get("bookStatus", {}).get("FanDuel", {})
            if fd_status.get("status") != "ok":
                print(f"  [FanDuel] Error: {fd_status.get('error', 'unknown')}")
                return

            # Extract FanDuel props from consolidated groups
            count = 0
            all_groups = data.get("allGroups", data.get("consolidatedGroups", {}))
            if isinstance(all_groups, dict):
                for key, group in all_groups.items():
                    books = group.get("books", {})
                    fd = books.get("FanDuel")
                    if fd:
                        self.props.append({
                            "book": "fanduel",
                            "player": group.get("player", ""),
                            "stat": group.get("stat", ""),
                            "line": group.get("line", 0),
                            "side": fd.get("over_under", "over"),
                            "odds_american": fd.get("odds", 0),
                            "odds_decimal": fd.get("oddsDecimal", 0),
                            "game": "",
                        })
                        count += 1
            elif isinstance(all_groups, list):
                for group in all_groups:
                    if group.get("book") == "FanDuel" and not group.get("error"):
                        self.props.append({
                            "book": "fanduel",
                            "player": group.get("player", ""),
                            "stat": group.get("stat", ""),
                            "line": group.get("line", 0),
                            "side": group.get("over_under", "over"),
                            "odds_american": group.get("odds", 0),
                            "odds_decimal": group.get("oddsDecimal", 0),
                            "game": "",
                        })
                        count += 1

            # Fallback: if allGroups didn't work, try raw props
            if count == 0:
                # Re-fetch just FanDuel directly
                resp2 = requests.get(
                    "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page",
                    params={"page": "CUSTOM", "customPageId": "nba",
                            "pbHorizontal": "true", "_ak": "FhMFpcPWXMeyZxOx"},
                    headers=HEADERS, timeout=15
                )
                if resp2.status_code == 200:
                    landing = resp2.json()
                    events = landing.get("attachments", {}).get("events", {})
                    games = [(eid, ev.get("name", "")) for eid, ev in events.items()
                             if "v" in ev.get("name", "").lower() or "@" in ev.get("name", "").lower()]

                    for eid, gname in games[:15]:
                        for tab in ["player-points", "player-rebounds", "player-assists", "player-threes"]:
                            try:
                                tr = requests.get(
                                    "https://sbapi.mi.sportsbook.fanduel.com/api/event-page",
                                    params={"eventId": eid, "tab": tab, "_ak": "FhMFpcPWXMeyZxOx"},
                                    headers=HEADERS, timeout=10
                                )
                                if tr.status_code != 200:
                                    continue
                                markets = tr.json().get("attachments", {}).get("markets", {})
                                for mid, mkt in markets.items():
                                    for runner in mkt.get("runners", []):
                                        name = (runner.get("runnerName") or "").strip()
                                        if not name or name in ("Over", "Under", "Yes", "No"):
                                            continue
                                        odds_data = runner.get("winRunnerOdds", {})
                                        am = (odds_data.get("americanDisplayOdds") or {}).get("americanOdds")
                                        if am is None:
                                            continue
                                        am = int(am)
                                        self.props.append({
                                            "book": "fanduel",
                                            "player": name,
                                            "stat": tab.replace("player-", ""),
                                            "line": runner.get("handicap", 0),
                                            "side": "over",
                                            "odds_american": am,
                                            "odds_decimal": round(american_to_decimal(am), 4),
                                            "game": gname,
                                        })
                                        count += 1
                            except Exception:
                                pass
                            time.sleep(0.2)

            print(f"  [FanDuel] {count} props loaded")
        except Exception as e:
            print(f"  [FanDuel] Error: {e}")

    def fetch_bovada_direct(self):
        """Pull Bovada game lines directly."""
        print("  [Bovada] Fetching direct...")
        try:
            resp = requests.get(
                "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba",
                headers=HEADERS, timeout=15
            )
            if resp.status_code != 200:
                print(f"  [Bovada] HTTP {resp.status_code}")
                return

            data = resp.json()
            if not data:
                return
            events = data[0].get("events", [])
            count = 0
            for ev in events:
                game = ev.get("description", "")
                for group in ev.get("displayGroups", []):
                    for mkt in group.get("markets", []):
                        mdesc = mkt.get("description", "")
                        for outcome in mkt.get("outcomes", []):
                            price = outcome.get("price", {})
                            am = price.get("american", "")
                            if not am:
                                continue
                            try:
                                dec = american_to_decimal(am)
                            except (ValueError, TypeError):
                                continue
                            h = price.get("handicap", "")
                            side = "over" if "over" in outcome.get("description", "").lower() else "under"
                            self.props.append({
                                "book": "bovada",
                                "player": outcome.get("description", ""),
                                "stat": mdesc,
                                "line": float(h) if h else 0,
                                "side": side,
                                "odds_american": am,
                                "odds_decimal": round(dec, 4),
                                "game": game,
                            })
                            count += 1
            print(f"  [Bovada] {count} lines loaded")
        except Exception as e:
            print(f"  [Bovada] Error: {e}")

    def fetch_odds_api(self):
        """Pull from the-odds-api if quota available."""
        print("  [OddsAPI] Checking quota...")
        try:
            resp = requests.get(
                "https://api.the-odds-api.com/v4/sports/basketball_nba/odds",
                params={
                    "apiKey": ODDS_API_KEY,
                    "regions": "us",
                    "markets": "player_points,player_rebounds,player_assists,player_threes",
                    "oddsFormat": "american",
                },
                timeout=15
            )
            remaining = resp.headers.get("x-requests-remaining", "0")
            print(f"  [OddsAPI] Quota remaining: {remaining}")
            if resp.status_code != 200:
                print(f"  [OddsAPI] HTTP {resp.status_code}")
                return

            events = resp.json()
            count = 0
            for event in events:
                game = f"{event.get('away_team', '?')} @ {event.get('home_team', '?')}"
                for bm in event.get("bookmakers", []):
                    book = bm["key"]
                    for market in bm.get("markets", []):
                        stat = market["key"].replace("player_", "")
                        for outcome in market.get("outcomes", []):
                            self.props.append({
                                "book": book,
                                "player": outcome.get("description", ""),
                                "stat": stat,
                                "line": outcome.get("point", 0),
                                "side": outcome.get("name", "").lower(),
                                "odds_american": outcome.get("price", 0),
                                "odds_decimal": round(american_to_decimal(outcome["price"]), 4),
                                "game": game,
                            })
                            count += 1
            print(f"  [OddsAPI] {count} props from {len(events)} events")
        except Exception as e:
            print(f"  [OddsAPI] Error: {e}")

    def import_dk_json(self, filepath=None):
        """Import DraftKings data from browser scraper export."""
        if filepath is None:
            filepath = os.path.join(DATA_DIR, "dk_import.json")
        if not os.path.exists(filepath):
            return
        print(f"  [DK Import] Loading {filepath}...")
        with open(filepath) as f:
            data = json.load(f)

        count = 0
        items = data if isinstance(data, list) else data.get("props", data.get("odds", []))
        for p in items:
            self.props.append({
                "book": p.get("book", "draftkings").lower(),
                "player": p.get("player", ""),
                "stat": p.get("stat", p.get("market", "")),
                "line": p.get("line", p.get("point", 0)),
                "side": p.get("side", p.get("over_under", "over")),
                "odds_american": p.get("odds", p.get("odds_american", 0)),
                "odds_decimal": p.get("oddsDecimal", p.get("odds_decimal", 0)),
                "game": p.get("game", ""),
            })
            count += 1
        print(f"  [DK Import] {count} props imported")

    def store_odds(self):
        """Store all collected odds in database."""
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        stored = 0
        for p in self.props:
            try:
                self.conn.execute("""
                    INSERT OR IGNORE INTO live_odds
                    (book, player, stat, line, side, odds_american, odds_decimal, game, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p["book"], p["player"], p["stat"], p["line"],
                      p["side"], p["odds_american"], p["odds_decimal"],
                      p["game"], now))
                stored += 1
            except sqlite3.Error:
                pass
        self.conn.commit()
        return stored

    def detect_ev(self, min_edge=0.03, min_ev=0.02):
        """
        Cross-book +EV detection.
        Groups props by (player, stat, line, side), devigs, finds outliers.
        """
        # Normalize and group
        groups = defaultdict(list)
        for p in self.props:
            player = p["player"].lower().strip()
            stat = p["stat"].lower().strip()
            # Normalize stat names
            stat_map = {"points": "pts", "rebounds": "reb", "assists": "ast",
                        "threes": "fg3m", "three": "fg3m", "3-pointers": "fg3m"}
            stat = stat_map.get(stat, stat)
            key = (player, stat, p.get("line", 0), p.get("side", "over"))
            groups[key].append(p)

        # Find cross-book matches
        alerts = []
        for (player, stat, line, side), book_props in groups.items():
            books = set(p["book"] for p in book_props)
            if len(books) < 2:
                continue

            # Calculate consensus fair probability
            implied_probs = []
            for p in book_props:
                dec = p.get("odds_decimal", 0)
                if dec > 1:
                    implied_probs.append((p["book"], p, decimal_to_implied(dec)))

            if len(implied_probs) < 2:
                continue

            avg_implied = sum(ip for _, _, ip in implied_probs) / len(implied_probs)

            # Check each book against consensus
            for book, prop, imp in implied_probs:
                edge = avg_implied - imp
                dec = prop["odds_decimal"]
                ev = avg_implied * (dec - 1) - (1 - avg_implied)

                if edge >= min_edge and ev >= min_ev:
                    k = kelly(avg_implied, dec, 0.25)
                    alerts.append({
                        "player": player,
                        "stat": stat,
                        "line": line,
                        "side": side,
                        "book": book,
                        "odds_american": prop["odds_american"],
                        "odds_decimal": dec,
                        "fair_prob": round(avg_implied, 4),
                        "implied": round(imp, 4),
                        "edge": round(edge, 4),
                        "ev": round(ev, 4),
                        "kelly_pct": round(k * 100, 2),
                        "n_books": len(books),
                        "game": prop.get("game", ""),
                    })

        alerts.sort(key=lambda x: -x["ev"])
        return alerts

    def store_alerts(self, alerts):
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        for a in alerts:
            self.conn.execute("""
                INSERT INTO ev_alerts_live
                (player, stat, line, side, book, odds_american, odds_decimal,
                 fair_prob, edge, ev, kelly_pct, n_books, game, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (a["player"], a["stat"], a["line"], a["side"],
                  a["book"], a["odds_american"], a["odds_decimal"],
                  a["fair_prob"], a["edge"], a["ev"], a["kelly_pct"],
                  a["n_books"], a["game"], now))
        self.conn.commit()

    def scan(self, include_odds_api=False):
        """Run one full scan cycle."""
        now = datetime.utcnow().strftime("%H:%M:%S UTC")
        print(f"\n{'='*65}")
        print(f"  LIVE SCAN — {now}")
        print(f"{'='*65}")

        self.props = []
        self.fetch_fanduel_proxy()
        self.fetch_bovada_direct()
        self.import_dk_json()
        if include_odds_api:
            self.fetch_odds_api()

        books = set(p["book"] for p in self.props)
        print(f"\n  Total: {len(self.props)} props from {len(books)} sources: {', '.join(sorted(books))}")

        stored = self.store_odds()
        print(f"  Stored {stored} new snapshots")

        alerts = self.detect_ev()
        if alerts:
            self.store_alerts(alerts)
            print(f"\n  +EV OPPORTUNITIES: {len(alerts)}")
            for i, a in enumerate(alerts[:15], 1):
                print(f"\n  {i}. {a['player'].title()} {a['side'].upper()} {a['line']} {a['stat'].upper()}")
                print(f"     Book: {a['book']} @ {a['odds_american']}")
                print(f"     Fair: {a['fair_prob']:.1%} | Edge: {a['edge']:.1%} | EV: {a['ev']:.1%} | Kelly: {a['kelly_pct']:.1f}%")
                print(f"     Compared across {a['n_books']} books")
        else:
            print(f"\n  No cross-book +EV opportunities found.")
            if len(books) < 2:
                print(f"  Need data from at least 2 books with matching player props.")
                print(f"  Export DK data from browser scraper -> save as data/dk_import.json")

        # Save latest results
        output = {
            "scan_time": now,
            "total_props": len(self.props),
            "books": list(books),
            "alerts": alerts[:50],
        }
        with open(os.path.join(DATA_DIR, "live_scan_latest.json"), "w") as f:
            json.dump(output, f, indent=2)

        return alerts

    def continuous(self, interval_min=5, include_odds_api=False):
        """Run continuous scanning loop."""
        print(f"Starting continuous scan (every {interval_min} min)")
        print(f"Ctrl+C to stop\n")
        while True:
            try:
                self.scan(include_odds_api=include_odds_api)
                print(f"\n  Next scan in {interval_min} min...")
                time.sleep(interval_min * 60)
            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except Exception as e:
                print(f"\n  Error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    scanner = LiveScanner()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "continuous":
            scanner.continuous(interval_min=5)
        elif cmd == "odds-api":
            scanner.scan(include_odds_api=True)
    else:
        scanner.scan()

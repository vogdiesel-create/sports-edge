"""
Sports Edge - Real-Time Odds Comparison Engine
The core infrastructure: poll odds across books, store everything,
detect mispricing in real-time.

This is what the 9.82% ROI guy built. Not a prediction model —
a data engineering system that finds where books disagree.

Architecture:
1. Poll the-odds-api every 5 min for all NBA player props
2. Store every odds snapshot in SQLite (timestamps matter)
3. For each prop, devig the sharpest line to get "fair" probability
4. Flag any book offering odds better than fair
5. Track CLV by comparing bet placement odds to closing line
"""

import json
import os
import sqlite3
import sys
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict

API_KEY = "077a2076a8f81c71bd1178368809cf8b"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "odds_engine.db")
BASE_URL = "https://api.the-odds-api.com/v4"

# Book tiers — this matters for devigging strategy
TIER_SHARP = {"pinnacle", "betfair_ex_eu", "matchbook"}
TIER_MARKET = {"draftkings", "fanduel", "betmgm", "caesars", "bet365"}
TIER_SOFT = {"bovada", "betonlineag", "mybookieag", "pointsbet",
             "betrivers", "espnbet", "fliff", "hardrockbet", "unibet_us",
             "williamhill_us", "superbook", "wynnbet"}

PROP_MARKETS = [
    "player_points", "player_rebounds", "player_assists",
    "player_threes", "player_blocks", "player_steals",
    "player_points_rebounds_assists",
]


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def devig(imp_a, imp_b, method="power"):
    """Remove vig to get fair probabilities.
    Power method (multiplicative) is standard.
    Shin method adjusts for information asymmetry."""
    total = imp_a + imp_b
    if total <= 0:
        return 0.5, 0.5
    if method == "power":
        return imp_a / total, imp_b / total
    elif method == "shin":
        if total <= 1.0:
            return imp_a, imp_b
        z = total - 1.0
        fair_a = (((z**2 + 4*(1-z)*imp_a**2/total)**0.5) - z) / (2*(1-z))
        return fair_a, 1.0 - fair_a
    return imp_a / total, imp_b / total


def init_db(db_path=DB_PATH):
    """Initialize SQLite database for odds storage."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS odds_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            event_name TEXT,
            commence_time TEXT,
            book TEXT NOT NULL,
            market TEXT NOT NULL,
            player TEXT NOT NULL,
            line REAL NOT NULL,
            over_odds INTEGER,
            under_odds INTEGER,
            over_decimal REAL,
            under_decimal REAL,
            fetched_at TEXT NOT NULL,
            UNIQUE(event_id, book, market, player, line, fetched_at)
        );

        CREATE INDEX IF NOT EXISTS idx_odds_event ON odds_snapshots(event_id);
        CREATE INDEX IF NOT EXISTS idx_odds_player ON odds_snapshots(player);
        CREATE INDEX IF NOT EXISTS idx_odds_time ON odds_snapshots(fetched_at);
        CREATE INDEX IF NOT EXISTS idx_odds_lookup
            ON odds_snapshots(event_id, market, player, line, fetched_at);

        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            event_name TEXT,
            player TEXT NOT NULL,
            market TEXT NOT NULL,
            line REAL NOT NULL,
            side TEXT NOT NULL,
            book TEXT NOT NULL,
            odds_american INTEGER NOT NULL,
            odds_decimal REAL NOT NULL,
            fair_prob REAL NOT NULL,
            edge REAL NOT NULL,
            ev REAL NOT NULL,
            kelly_pct REAL NOT NULL,
            stake REAL NOT NULL,
            placed_at TEXT NOT NULL,
            -- Filled after game
            result TEXT,
            pnl REAL,
            closing_odds_american INTEGER,
            closing_odds_decimal REAL,
            clv REAL,
            graded_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_bets_event ON bets(event_id);
        CREATE INDEX IF NOT EXISTS idx_bets_placed ON bets(placed_at);

        CREATE TABLE IF NOT EXISTS ev_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            event_name TEXT,
            player TEXT NOT NULL,
            market TEXT NOT NULL,
            line REAL NOT NULL,
            side TEXT NOT NULL,
            book TEXT NOT NULL,
            odds_american INTEGER NOT NULL,
            fair_prob REAL NOT NULL,
            edge REAL NOT NULL,
            ev REAL NOT NULL,
            n_books INTEGER NOT NULL,
            sharp_source TEXT,
            detected_at TEXT NOT NULL,
            expired INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_alerts_time ON ev_alerts(detected_at);
    """)
    conn.commit()
    return conn


class OddsEngine:
    """
    Core odds comparison and +EV detection engine.

    Usage:
        engine = OddsEngine()
        engine.poll()           # Fetch current odds, store, detect +EV
        engine.show_alerts()    # Display current opportunities
        engine.clv_report()     # Show CLV for placed bets
    """

    def __init__(self, api_key=API_KEY, db_path=DB_PATH,
                 min_edge=0.03, min_ev=0.02, min_books=3):
        self.api_key = api_key
        self.db_path = db_path
        self.min_edge = min_edge
        self.min_ev = min_ev
        self.min_books = min_books
        self.conn = init_db(db_path)
        self.remaining_requests = None

    def poll(self, sport="basketball_nba", markets=None, max_events=None):
        """
        One polling cycle:
        1. Fetch all events
        2. For each event, fetch prop odds from all books (batch markets to save quota)
        3. Store snapshots
        4. Run +EV detection
        5. Return alerts

        Quota cost: 1 (events) + N_events * ceil(N_markets / batch_size)
        With batching: ~1 + 15*2 = 31 requests for full scan (vs 105 without)
        """
        now = datetime.now(tz=None).strftime("%Y-%m-%dT%H:%M:%SZ")
        if markets is None:
            markets = PROP_MARKETS
        print(f"\n[{now}] Polling NBA player props...")

        # Check quota before burning it
        resp = requests.get(f"{BASE_URL}/sports/{sport}/events",
                           params={"apiKey": self.api_key})
        if resp.status_code != 200:
            print(f"  Error fetching events: {resp.status_code}")
            return []

        events = resp.json()
        self.remaining_requests = resp.headers.get("x-requests-remaining", "?")
        print(f"  {len(events)} upcoming events (API quota remaining: {self.remaining_requests})")

        try:
            remaining = int(self.remaining_requests)
            if remaining < 5:
                print(f"  WARNING: Only {remaining} API requests left. Aborting to conserve quota.")
                return []
        except (ValueError, TypeError):
            pass

        if max_events:
            events = events[:max_events]

        all_alerts = []
        for event in events:
            eid = event["id"]
            ename = f"{event.get('away_team','?')} @ {event.get('home_team','?')}"
            commence = event.get("commence_time", "")

            # Batch markets into comma-separated requests (API supports this)
            # Max ~4 markets per request to stay within response size limits
            batch_size = 4
            for i in range(0, len(markets), batch_size):
                batch = markets[i:i+batch_size]
                market_str = ",".join(batch)
                resp = requests.get(
                    f"{BASE_URL}/sports/{sport}/events/{eid}/odds",
                    params={
                        "apiKey": self.api_key,
                        "regions": "us,eu",
                        "markets": market_str,
                        "oddsFormat": "american",
                    }
                )
                self.remaining_requests = resp.headers.get("x-requests-remaining", "?")
                if resp.status_code != 200:
                    continue

                data = resp.json()
                bookmakers = data.get("bookmakers", [])
                if not bookmakers:
                    continue

                # Parse each market in the batch
                for market in batch:
                    snapshots = self._parse_bookmakers(eid, ename, commence, market, bookmakers, now)
                    self._store_snapshots(snapshots)
                alerts = self._detect_ev(eid, ename, commence, market, snapshots, now)
                all_alerts.extend(alerts)

                time.sleep(0.25)

        if all_alerts:
            self._store_alerts(all_alerts)
            print(f"\n  {len(all_alerts)} +EV opportunities detected!")
        else:
            print(f"\n  No +EV opportunities this cycle.")

        return all_alerts

    def _parse_bookmakers(self, event_id, event_name, commence, market, bookmakers, fetched_at):
        """Parse API response into flat snapshot rows."""
        snapshots = []
        for bm in bookmakers:
            book = bm["key"]
            for mkt in bm.get("markets", []):
                # Group outcomes by player+line
                player_lines = defaultdict(dict)
                for outcome in mkt.get("outcomes", []):
                    player = outcome.get("description", "")
                    point = outcome.get("point")
                    side = outcome.get("name", "").lower()
                    price = outcome.get("price")
                    if not player or point is None or price is None:
                        continue
                    key = (player, point)
                    player_lines[key][side] = price

                for (player, line), sides in player_lines.items():
                    over = sides.get("over")
                    under = sides.get("under")
                    if over is None and under is None:
                        continue
                    snapshots.append({
                        "event_id": event_id,
                        "event_name": event_name,
                        "commence_time": commence,
                        "book": book,
                        "market": market,
                        "player": player,
                        "line": line,
                        "over_odds": over,
                        "under_odds": under,
                        "over_decimal": american_to_decimal(over) if over else None,
                        "under_decimal": american_to_decimal(under) if under else None,
                        "fetched_at": fetched_at,
                    })
        return snapshots

    def _store_snapshots(self, snapshots):
        """Store odds snapshots in SQLite."""
        for s in snapshots:
            try:
                self.conn.execute("""
                    INSERT OR IGNORE INTO odds_snapshots
                    (event_id, event_name, commence_time, book, market, player, line,
                     over_odds, under_odds, over_decimal, under_decimal, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s["event_id"], s["event_name"], s["commence_time"],
                      s["book"], s["market"], s["player"], s["line"],
                      s["over_odds"], s["under_odds"],
                      s["over_decimal"], s["under_decimal"], s["fetched_at"]))
            except sqlite3.Error:
                pass
        self.conn.commit()

    def _detect_ev(self, event_id, event_name, commence, market, snapshots, now):
        """
        For each (player, line), find fair probability from sharp books,
        then flag any soft book offering better-than-fair odds.
        """
        # Group by (player, line)
        props = defaultdict(dict)
        for s in snapshots:
            key = (s["player"], s["line"])
            props[key][s["book"]] = s

        alerts = []
        for (player, line), book_data in props.items():
            # Get fair line
            sharp_overs = []
            sharp_unders = []
            all_overs = []
            all_unders = []

            for book, s in book_data.items():
                if s["over_decimal"] and s["under_decimal"]:
                    imp_o = decimal_to_implied(s["over_decimal"])
                    imp_u = decimal_to_implied(s["under_decimal"])
                    all_overs.append(imp_o)
                    all_unders.append(imp_u)
                    if book in TIER_SHARP:
                        sharp_overs.append(imp_o)
                        sharp_unders.append(imp_u)

            if len(all_overs) < self.min_books:
                continue

            # Use sharp if available, else market consensus
            if sharp_overs:
                avg_o = sum(sharp_overs) / len(sharp_overs)
                avg_u = sum(sharp_unders) / len(sharp_unders)
                source = "sharp"
            else:
                avg_o = sum(all_overs) / len(all_overs)
                avg_u = sum(all_unders) / len(all_unders)
                source = "consensus"

            fair_over, fair_under = devig(avg_o, avg_u)

            # Check each non-sharp book for +EV
            for book, s in book_data.items():
                if book in TIER_SHARP:
                    continue

                for side, fair_prob in [("over", fair_over), ("under", fair_under)]:
                    dec_key = f"{side}_decimal"
                    odds_key = f"{side}_odds"
                    dec = s.get(dec_key)
                    amer = s.get(odds_key)
                    if not dec or not amer:
                        continue

                    implied = decimal_to_implied(dec)
                    edge = fair_prob - implied
                    ev = fair_prob * (dec - 1) - (1 - fair_prob)

                    if edge >= self.min_edge and ev >= self.min_ev:
                        alerts.append({
                            "event_id": event_id,
                            "event_name": event_name,
                            "player": player,
                            "market": market.replace("player_", ""),
                            "line": line,
                            "side": side.upper(),
                            "book": book,
                            "odds_american": amer,
                            "fair_prob": round(fair_prob, 4),
                            "edge": round(edge, 4),
                            "ev": round(ev, 4),
                            "n_books": len(all_overs),
                            "sharp_source": source,
                            "detected_at": now,
                        })

        return alerts

    def _store_alerts(self, alerts):
        for a in alerts:
            self.conn.execute("""
                INSERT INTO ev_alerts
                (event_id, event_name, player, market, line, side, book,
                 odds_american, fair_prob, edge, ev, n_books, sharp_source, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (a["event_id"], a["event_name"], a["player"], a["market"],
                  a["line"], a["side"], a["book"], a["odds_american"],
                  a["fair_prob"], a["edge"], a["ev"], a["n_books"],
                  a["sharp_source"], a["detected_at"]))
        self.conn.commit()

    def show_alerts(self, limit=20):
        """Display most recent +EV alerts."""
        rows = self.conn.execute("""
            SELECT player, market, line, side, book, odds_american,
                   fair_prob, edge, ev, n_books, sharp_source, detected_at, event_name
            FROM ev_alerts
            WHERE expired = 0
            ORDER BY detected_at DESC, ev DESC
            LIMIT ?
        """, (limit,)).fetchall()

        if not rows:
            print("No active alerts.")
            return

        print(f"\n{'='*70}")
        print(f"  +EV ALERTS ({len(rows)} most recent)")
        print(f"{'='*70}")
        for i, row in enumerate(rows, 1):
            player, market, line, side, book, odds, fair, edge, ev, nb, src, dt, game = row
            print(f"\n  {i}. {player} {side} {line} {market}")
            print(f"     Game: {game}")
            print(f"     Book: {book} @ {odds:+d}")
            print(f"     Fair: {fair:.1%} | Edge: {edge:.1%} | EV: {ev:.1%}")
            print(f"     Books: {nb} | Source: {src} | Time: {dt}")

    def record_bet(self, alert_id, stake, bankroll=None):
        """Record a bet based on an alert."""
        alert = self.conn.execute(
            "SELECT * FROM ev_alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if not alert:
            print(f"Alert {alert_id} not found.")
            return

        # Calculate Kelly
        fair_prob = alert[8]  # fair_prob column
        odds_american = alert[7]
        dec = american_to_decimal(odds_american)
        b = dec - 1
        q = 1 - fair_prob
        kelly = max(0, (b * fair_prob - q) / b * 0.25)

        if bankroll and stake == 0:
            stake = round(bankroll * kelly, 2)

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute("""
            INSERT INTO bets
            (event_id, event_name, player, market, line, side, book,
             odds_american, odds_decimal, fair_prob, edge, ev, kelly_pct, stake, placed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alert[1], alert[2], alert[3], alert[4], alert[5], alert[6], alert[7],
              odds_american, dec, fair_prob, alert[9], alert[10], kelly*100, stake, now))
        self.conn.commit()
        print(f"  Bet recorded: ${stake} on {alert[3]} {alert[6]} {alert[5]} {alert[4]} @ {odds_american:+d}")

    def clv_report(self):
        """Show CLV for all graded bets."""
        rows = self.conn.execute("""
            SELECT player, market, line, side, book,
                   odds_decimal, closing_odds_decimal, clv, pnl, stake
            FROM bets
            WHERE clv IS NOT NULL
            ORDER BY placed_at DESC
        """).fetchall()

        if not rows:
            print("No graded bets with CLV data yet.")
            return

        total_clv = sum(r[7] for r in rows)
        avg_clv = total_clv / len(rows)
        total_pnl = sum(r[8] for r in rows if r[8])
        total_staked = sum(r[9] for r in rows if r[9])

        print(f"\n{'='*65}")
        print(f"  CLV REPORT ({len(rows)} graded bets)")
        print(f"{'='*65}")
        print(f"  Average CLV: {avg_clv:.2%}")
        print(f"  Total P/L: ${total_pnl:+,.0f}")
        print(f"  ROI: {total_pnl/total_staked*100:+.1f}%" if total_staked else "")
        print(f"\n  CLV > 0 means we beat the closing line = we have edge")
        print(f"  Need 500+ bets to be statistically confident")

    def stats(self):
        """Show engine statistics."""
        snaps = self.conn.execute("SELECT COUNT(*) FROM odds_snapshots").fetchone()[0]
        alerts = self.conn.execute("SELECT COUNT(*) FROM ev_alerts").fetchone()[0]
        bets = self.conn.execute("SELECT COUNT(*) FROM bets").fetchone()[0]
        books = self.conn.execute("SELECT COUNT(DISTINCT book) FROM odds_snapshots").fetchone()[0]
        players = self.conn.execute("SELECT COUNT(DISTINCT player) FROM odds_snapshots").fetchone()[0]

        latest = self.conn.execute(
            "SELECT MAX(fetched_at) FROM odds_snapshots"
        ).fetchone()[0]

        print(f"\n  Engine Stats:")
        print(f"    Snapshots: {snaps:,}")
        print(f"    Unique books: {books}")
        print(f"    Unique players: {players}")
        print(f"    +EV alerts: {alerts}")
        print(f"    Bets tracked: {bets}")
        print(f"    Latest poll: {latest or 'never'}")
        print(f"    API remaining: {self.remaining_requests or '?'}")

    def continuous_poll(self, interval_min=5, max_polls=None):
        """Run continuous polling loop."""
        print(f"Starting continuous polling (every {interval_min} min)")
        print(f"Press Ctrl+C to stop\n")
        polls = 0
        while True:
            try:
                alerts = self.poll()
                if alerts:
                    self.show_alerts(limit=10)
                polls += 1
                if max_polls and polls >= max_polls:
                    break
                print(f"\n  Next poll in {interval_min} min... (API remaining: {self.remaining_requests})")
                time.sleep(interval_min * 60)
            except KeyboardInterrupt:
                print("\nStopping.")
                break
            except Exception as e:
                print(f"\nError: {e}")
                time.sleep(60)


def demo_historical():
    """
    Demo: Show what the engine finds using our existing historical data.
    Simulates what would happen if we'd been running this all season.
    """
    from triple_poisson_model import load_enhanced_box_scores

    print("=" * 65)
    print("  ODDS ENGINE - Historical Demo")
    print("=" * 65)

    filepath = os.path.join(DATA_DIR, "real_backtest_full_season.json")
    with open(filepath) as f:
        data = json.load(f)
    results = data["results"]

    # Our historical data has single-book odds per prop
    # In production, we'd have multi-book. Let's analyze what we can:
    # Show the vig distribution and what devigging reveals

    vigs = []
    edges_over = []
    edges_under = []

    for r in results:
        over_dec = american_to_decimal(r["over_odds"])
        under_dec = american_to_decimal(r["under_odds"])
        imp_o = decimal_to_implied(over_dec)
        imp_u = decimal_to_implied(under_dec)
        vig = (imp_o + imp_u - 1.0) * 100
        vigs.append(vig)

        fair_o, fair_u = devig(imp_o, imp_u)
        # The "edge" available from devigging alone
        edges_over.append(fair_o - imp_o)
        edges_under.append(fair_u - imp_u)

    avg_vig = sum(vigs) / len(vigs)
    max_vig = max(vigs)
    min_vig = min(vigs)

    print(f"\n  Analyzed {len(results)} props from historical data")
    print(f"\n  VIG ANALYSIS:")
    print(f"    Average vig: {avg_vig:.2f}%")
    print(f"    Range: {min_vig:.2f}% to {max_vig:.2f}%")
    print(f"    This is the 'tax' you pay on every bet")
    print(f"\n  DEVIGGING REVEALS:")
    print(f"    Average edge recovered by devigging: {sum(edges_over)/len(edges_over)*100:.3f}%")
    print(f"    With multi-book data, outlier books offer 2-5x this edge")
    print(f"\n  WHY MULTI-BOOK MATTERS:")
    print(f"    Our data: 1 book per prop -> can only beat vig by predicting better")
    print(f"    Real system: 10+ books per prop -> find the one book that's wrong")
    print(f"    The 9.82% ROI guy: 25,000 odds/sec across all books")

    # Show what a single live poll would cost in API quota
    print(f"\n  API COST ESTIMATE:")
    print(f"    Events per night: ~8-15 NBA games")
    print(f"    Markets per event: {len(PROP_MARKETS)}")
    print(f"    Quota per request: ~10 units")
    print(f"    Per poll: ~{15 * len(PROP_MARKETS) * 10} units")
    print(f"    Free tier: 500 requests/month")
    print(f"    $20/month tier: enough for ~4 polls/night")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "poll":
            engine = OddsEngine()
            engine.poll()
            engine.show_alerts()
        elif cmd == "continuous":
            engine = OddsEngine()
            engine.continuous_poll(interval_min=5)
        elif cmd == "alerts":
            engine = OddsEngine()
            engine.show_alerts()
        elif cmd == "stats":
            engine = OddsEngine()
            engine.stats()
        elif cmd == "clv":
            engine = OddsEngine()
            engine.clv_report()
    else:
        demo_historical()

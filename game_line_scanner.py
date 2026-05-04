"""
Sports Edge - Game Line Cross-Book Scanner

Uses sbrscrape (free, no API key) to get multi-book game lines:
- Spreads + odds from 10+ books
- Totals + odds from 10+ books
- Moneylines from 10+ books
- Includes PINNACLE (sharp benchmark)

Strategy:
- Pinnacle is the sharpest book. Their lines define "true" probability.
- Devig Pinnacle lines to get fair probability.
- Find other books offering better odds than Pinnacle's fair line.
- Those are +EV bets.

Backtest showed: cross-book +EV at 8%+ edge = +16.1% ROI.
Game lines have tighter markets but higher volume opportunity.
"""

import json
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone

try:
    from sbrscrape import Scoreboard
except ImportError:
    print("Install: pip3 install --break-system-packages sbrscrape")
    raise

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

# Books ranked by sharpness (used for fair line estimation)
SHARP_BOOKS = ["pinnacle", "lowvig"]
MARKET_BOOKS = ["betonline", "bovada", "bodog", "heritage", "sportsbetting"]
SOFT_BOOKS = ["unibet", "intertops", "gtbets"]

ALL_SPORTS = ["NBA", "MLB", "NHL", "NCAAB", "NFL", "NCAAF", "Soccer"]


def american_to_decimal(american):
    if isinstance(american, str):
        if american in ("EVEN", "even"):
            return 2.0
        american = int(american.replace("+", ""))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def devig_pinnacle(over_odds, under_odds):
    """Devig Pinnacle odds to get fair probabilities."""
    if not over_odds or not under_odds:
        return None, None
    over_imp = decimal_to_implied(american_to_decimal(over_odds))
    under_imp = decimal_to_implied(american_to_decimal(under_odds))
    total = over_imp + under_imp
    if total <= 0:
        return None, None
    return over_imp / total, under_imp / total


def kelly_fraction(prob, decimal_odds, fraction=0.25):
    b = decimal_odds - 1
    q = 1 - prob
    if b <= 0:
        return 0
    f = (b * prob - q) / b
    return max(0, f * fraction)


class GameLineScanner:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS game_odds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, sport TEXT, game TEXT,
            home TEXT, away TEXT,
            market TEXT, book TEXT,
            line REAL, odds INTEGER,
            side TEXT, status TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS ev_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, sport TEXT, game TEXT,
            market TEXT, side TEXT, book TEXT,
            odds INTEGER, line REAL,
            fair_prob REAL, implied_prob REAL,
            edge REAL, ev REAL,
            pinnacle_odds INTEGER,
            kelly_pct REAL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_game_ts ON game_odds(timestamp)")
        conn.commit()
        conn.close()

    def fetch_sport(self, sport):
        """Fetch game lines for a sport via SBR scrape."""
        try:
            sb = Scoreboard(sport)
            games = sb.games
            return games
        except Exception as e:
            print(f"  [{sport}] Error: {e}")
            return []

    def scan_sport(self, sport, games):
        """Analyze games for +EV opportunities using Pinnacle as benchmark."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        opportunities = []
        total_lines = 0

        for game in games:
            home = game.get("home_team", "")
            away = game.get("away_team", "")
            status = game.get("status", "")
            game_name = f"{away} @ {home}"

            if status == "complete":
                continue  # Skip completed games

            # Analyze each market type
            for market_type, data_keys in [
                ("spread", [
                    ("home_spread", "home_spread_odds", "away_spread", "away_spread_odds"),
                ]),
                ("total", [
                    ("total", "over_odds", "total", "under_odds"),
                ]),
                ("moneyline", [
                    (None, "home_ml", None, "away_ml"),
                ]),
            ]:
                for line_key_home, odds_key_home, line_key_away, odds_key_away in data_keys:
                    home_odds_by_book = game.get(odds_key_home, {})
                    away_odds_by_book = game.get(odds_key_away, {})

                    if not isinstance(home_odds_by_book, dict):
                        continue

                    # Get Pinnacle odds for fair line
                    pin_home = home_odds_by_book.get("pinnacle")
                    pin_away = away_odds_by_book.get("pinnacle")

                    if pin_home is None or pin_away is None:
                        # Try lowvig as backup
                        pin_home = home_odds_by_book.get("lowvig", pin_home)
                        pin_away = away_odds_by_book.get("lowvig", pin_away)

                    if pin_home is None or pin_away is None:
                        continue

                    # Devig Pinnacle to get fair probabilities
                    fair_home, fair_away = devig_pinnacle(pin_home, pin_away)
                    if fair_home is None:
                        continue

                    # Get lines
                    home_lines = game.get(line_key_home, {}) if line_key_home else {}
                    away_lines = game.get(line_key_away, {}) if line_key_away else {}

                    # Store all lines
                    for book, odds in home_odds_by_book.items():
                        if book == "consensus" or odds is None:
                            continue
                        line = home_lines.get(book, 0) if isinstance(home_lines, dict) else 0
                        side = "home" if market_type != "total" else "over"
                        c.execute("""INSERT INTO game_odds
                            (timestamp, sport, game, home, away, market, book,
                             line, odds, side, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (now, sport, game_name, home, away, market_type,
                             book, line, odds, side, status))
                        total_lines += 1

                    for book, odds in away_odds_by_book.items():
                        if book == "consensus" or odds is None:
                            continue
                        line = away_lines.get(book, 0) if isinstance(away_lines, dict) else 0
                        side = "away" if market_type != "total" else "under"
                        c.execute("""INSERT INTO game_odds
                            (timestamp, sport, game, home, away, market, book,
                             line, odds, side, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (now, sport, game_name, home, away, market_type,
                             book, line, odds, side, status))
                        total_lines += 1

                    # Get Pinnacle's line for comparison
                    pin_line = None
                    if isinstance(home_lines, dict):
                        pin_line = home_lines.get("pinnacle")
                    elif isinstance(home_lines, (int, float)):
                        pin_line = home_lines

                    # Check each book against Pinnacle fair line
                    # HOME/OVER side
                    for book, odds in home_odds_by_book.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue

                        # For spreads: only compare books on the SAME line as Pinnacle
                        if market_type == "spread" and isinstance(home_lines, dict):
                            book_line = home_lines.get(book)
                            if book_line is None or (pin_line is not None and book_line != pin_line):
                                continue  # Different line = different market, skip

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_home - imp
                        ev = fair_home * (dec - 1) - (1 - fair_home)

                        if edge >= 0.02 and ev >= 0.01:
                            side_label = "home" if market_type != "total" else "over"
                            line_val = 0
                            if isinstance(home_lines, dict):
                                line_val = home_lines.get(book, 0)
                            elif isinstance(home_lines, (int, float)):
                                line_val = home_lines

                            kf = kelly_fraction(fair_home, dec)

                            opp = {
                                "sport": sport,
                                "game": game_name,
                                "market": market_type,
                                "side": side_label,
                                "book": book,
                                "odds": odds,
                                "line": line_val,
                                "fair_prob": round(fair_home, 4),
                                "implied_prob": round(imp, 4),
                                "edge": round(edge, 4),
                                "ev": round(ev, 4),
                                "pinnacle_odds": pin_home,
                                "kelly_pct": round(kf * 100, 2),
                            }
                            opportunities.append(opp)

                            c.execute("""INSERT INTO ev_alerts
                                (timestamp, sport, game, market, side, book,
                                 odds, line, fair_prob, implied_prob, edge, ev,
                                 pinnacle_odds, kelly_pct)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (now, sport, game_name, market_type, side_label, book,
                                 odds, line_val, fair_home, imp, edge, ev, pin_home, kf * 100))

                    # AWAY/UNDER side
                    for book, odds in away_odds_by_book.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue

                        # For spreads: only compare books on the SAME line as Pinnacle
                        if market_type == "spread" and isinstance(away_lines, dict):
                            book_line = away_lines.get(book)
                            pin_away_line = away_lines.get("pinnacle")
                            if book_line is None or (pin_away_line is not None and book_line != pin_away_line):
                                continue

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_away - imp
                        ev = fair_away * (dec - 1) - (1 - fair_away)

                        if edge >= 0.02 and ev >= 0.01:
                            side_label = "away" if market_type != "total" else "under"
                            line_val = 0
                            if isinstance(away_lines, dict):
                                line_val = away_lines.get(book, 0)
                            elif isinstance(away_lines, (int, float)):
                                line_val = away_lines

                            kf = kelly_fraction(fair_away, dec)

                            opp = {
                                "sport": sport,
                                "game": game_name,
                                "market": market_type,
                                "side": side_label,
                                "book": book,
                                "odds": odds,
                                "line": line_val,
                                "fair_prob": round(fair_away, 4),
                                "implied_prob": round(imp, 4),
                                "edge": round(edge, 4),
                                "ev": round(ev, 4),
                                "pinnacle_odds": pin_away,
                                "kelly_pct": round(kf * 100, 2),
                            }
                            opportunities.append(opp)

                            c.execute("""INSERT INTO ev_alerts
                                (timestamp, sport, game, market, side, book,
                                 odds, line, fair_prob, implied_prob, edge, ev,
                                 pinnacle_odds, kelly_pct)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (now, sport, game_name, market_type, side_label, book,
                                 odds, line_val, fair_away, imp, edge, ev, pin_away, kf * 100))

        conn.commit()
        conn.close()

        return opportunities, total_lines

    def scan_all(self, sports=None):
        """Scan all sports for +EV game line opportunities."""
        if sports is None:
            sports = ["NBA", "MLB", "NHL"]

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"\n{'='*70}")
        print(f"  GAME LINE CROSS-BOOK SCANNER (Pinnacle Benchmark)")
        print(f"  {now}")
        print(f"{'='*70}")

        all_opps = []
        total_lines = 0

        for sport in sports:
            print(f"\n  [{sport}] Fetching...")
            games = self.fetch_sport(sport)
            if not games:
                print(f"  [{sport}] No games found")
                continue

            upcoming = [g for g in games if g.get("status") != "complete"]
            print(f"  [{sport}] {len(games)} games ({len(upcoming)} upcoming)")

            opps, lines = self.scan_sport(sport, upcoming)
            all_opps.extend(opps)
            total_lines += lines
            print(f"  [{sport}] {lines} lines tracked, {len(opps)} +EV opportunities")
            time.sleep(0.5)

        # Sort by EV
        all_opps.sort(key=lambda x: -x["ev"])

        print(f"\n{'='*70}")
        print(f"  RESULTS")
        print(f"{'='*70}")
        print(f"  Total lines tracked: {total_lines}")
        print(f"  +EV opportunities: {len(all_opps)}")

        if all_opps:
            print(f"\n  TOP +EV PLAYS:")
            for i, opp in enumerate(all_opps[:20], 1):
                print(f"\n  {i}. [{opp['sport']}] {opp['game']}")
                print(f"     {opp['market'].upper()} {opp['side']} {opp['line']} @ {opp['book']}")
                print(f"     Odds: {opp['odds']:+d} | Fair: {opp['fair_prob']:.1%} | "
                      f"Edge: {opp['edge']:.1%} | EV: {opp['ev']:.1%} | "
                      f"Kelly: {opp['kelly_pct']:.1f}%")
                print(f"     Pinnacle: {opp['pinnacle_odds']:+d}")

            # Summary by sport
            print(f"\n  BY SPORT:")
            by_sport = defaultdict(list)
            for o in all_opps:
                by_sport[o["sport"]].append(o)
            for sport, opps in sorted(by_sport.items()):
                avg_ev = sum(o["ev"] for o in opps) / len(opps)
                avg_edge = sum(o["edge"] for o in opps) / len(opps)
                print(f"    {sport}: {len(opps)} opps, avg edge={avg_edge:.1%}, avg EV={avg_ev:.1%}")

            # Summary by book
            print(f"\n  BY BOOK (most beatable):")
            by_book = defaultdict(list)
            for o in all_opps:
                by_book[o["book"]].append(o)
            for book, opps in sorted(by_book.items(), key=lambda x: -len(x[1])):
                avg_ev = sum(o["ev"] for o in opps) / len(opps)
                print(f"    {book}: {len(opps)} opps, avg EV={avg_ev:.1%}")

            # Summary by market
            print(f"\n  BY MARKET:")
            by_mkt = defaultdict(list)
            for o in all_opps:
                by_mkt[o["market"]].append(o)
            for mkt, opps in sorted(by_mkt.items(), key=lambda x: -len(x[1])):
                avg_ev = sum(o["ev"] for o in opps) / len(opps)
                print(f"    {mkt}: {len(opps)} opps, avg EV={avg_ev:.1%}")

        # Save
        results = {
            "timestamp": now,
            "sports": sports,
            "total_lines": total_lines,
            "opportunities": all_opps[:50],
            "summary": {
                "total_opps": len(all_opps),
                "by_sport": {s: len(os) for s, os in defaultdict(list, {o["sport"]: [] for o in all_opps}).items()},
            },
        }
        outpath = os.path.join(DATA_DIR, "game_line_scan.json")
        with open(outpath, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to {outpath}")

        return all_opps

    def continuous(self, sports=None, interval_minutes=15, max_cycles=32):
        """Continuous scanning."""
        if sports is None:
            sports = ["NBA", "MLB", "NHL"]
        print(f"\n  Continuous mode: every {interval_minutes}min")
        for cycle in range(1, max_cycles + 1):
            print(f"\n  === Cycle {cycle}/{max_cycles} ===")
            self.scan_all(sports)
            if cycle < max_cycles:
                time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import sys

    scanner = GameLineScanner()

    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            sports = sys.argv[2].split(",") if len(sys.argv) > 2 else None
            scanner.continuous(sports)
        else:
            scanner.scan_all(sys.argv[1:])
    else:
        scanner.scan_all()

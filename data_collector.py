#!/usr/bin/env python3
"""
Sports Edge - Data Collection Pipeline

Accumulates game line and prop snapshots over time into SQLite.
This builds the historical database we need for robust backtesting.

Tables:
- game_line_snapshots: SBR game line odds by book (every scan)
- fd_prop_snapshots: FanDuel prop lines (every scan)
- game_results: Final scores (graded after completion)
- collection_log: Metadata about each collection run

Run: python3 data_collector.py          # Single collection
     python3 data_collector.py continuous # Every 15 min
"""

import json
import os
import sqlite3
import time
from datetime import datetime, timezone

try:
    from sbrscrape import Scoreboard
except ImportError:
    Scoreboard = None

import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "sports_edge.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS game_line_snapshots (
        id INTEGER PRIMARY KEY,
        collected_at TEXT,
        sport TEXT,
        game_date TEXT,
        home_team TEXT,
        away_team TEXT,
        status TEXT,
        home_score INTEGER,
        away_score INTEGER,
        market TEXT,
        book TEXT,
        side TEXT,
        line REAL,
        odds INTEGER,
        UNIQUE(collected_at, sport, home_team, away_team, market, book, side)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS fd_prop_snapshots (
        id INTEGER PRIMARY KEY,
        collected_at TEXT,
        sport TEXT,
        game TEXT,
        player TEXT,
        market TEXT,
        line REAL,
        over_odds INTEGER,
        under_odds INTEGER,
        UNIQUE(collected_at, game, player, market)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS game_results (
        id INTEGER PRIMARY KEY,
        sport TEXT,
        game_date TEXT,
        home_team TEXT,
        away_team TEXT,
        home_score INTEGER,
        away_score INTEGER,
        graded_at TEXT,
        UNIQUE(sport, home_team, away_team, game_date)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS collection_log (
        id INTEGER PRIMARY KEY,
        collected_at TEXT,
        game_lines_count INTEGER,
        fd_props_count INTEGER,
        games_graded INTEGER,
        duration_sec REAL
    )""")
    conn.commit()
    return conn


def collect_game_lines(conn, now_str):
    """Collect SBR game line data."""
    if Scoreboard is None:
        return 0

    total = 0
    for sport in ["NBA", "MLB", "NHL"]:
        try:
            sb = Scoreboard(sport)
            for g in sb.games:
                home = g.get("home_team", "")
                away = g.get("away_team", "")
                game_date = g.get("date", "")[:10]
                status = g.get("status", "")
                hs = g.get("home_score")
                asc = g.get("away_score")

                # Moneylines
                for side_name, ml_dict in [("home", g.get("home_ml", {})),
                                            ("away", g.get("away_ml", {}))]:
                    if not isinstance(ml_dict, dict):
                        continue
                    for book, odds in ml_dict.items():
                        if odds is None:
                            continue
                        try:
                            conn.execute(
                                "INSERT OR IGNORE INTO game_line_snapshots "
                                "(collected_at,sport,game_date,home_team,away_team,status,"
                                "home_score,away_score,market,book,side,line,odds) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (now_str, sport, game_date, home, away, status,
                                 hs, asc, "moneyline", book, side_name, None, odds)
                            )
                            total += 1
                        except:
                            pass

                # Totals
                totals = g.get("total", {})
                for side_name, odds_dict in [("over", g.get("over_odds", {})),
                                              ("under", g.get("under_odds", {}))]:
                    if not isinstance(odds_dict, dict):
                        continue
                    for book, odds in odds_dict.items():
                        if odds is None:
                            continue
                        line = totals.get(book) if isinstance(totals, dict) else totals
                        try:
                            conn.execute(
                                "INSERT OR IGNORE INTO game_line_snapshots "
                                "(collected_at,sport,game_date,home_team,away_team,status,"
                                "home_score,away_score,market,book,side,line,odds) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (now_str, sport, game_date, home, away, status,
                                 hs, asc, "total", book, side_name, line, odds)
                            )
                            total += 1
                        except:
                            pass

                # Spreads
                hs_dict = g.get("home_spread", {})
                for side_name, odds_dict, spread_dict in [
                    ("home", g.get("home_spread_odds", {}), g.get("home_spread", {})),
                    ("away", g.get("away_spread_odds", {}), g.get("away_spread", {})),
                ]:
                    if not isinstance(odds_dict, dict):
                        continue
                    for book, odds in odds_dict.items():
                        if odds is None:
                            continue
                        line = spread_dict.get(book) if isinstance(spread_dict, dict) else None
                        try:
                            conn.execute(
                                "INSERT OR IGNORE INTO game_line_snapshots "
                                "(collected_at,sport,game_date,home_team,away_team,status,"
                                "home_score,away_score,market,book,side,line,odds) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (now_str, sport, game_date, home, away, status,
                                 hs, asc, "spread", book, side_name, line, odds)
                            )
                            total += 1
                        except:
                            pass

                # Grade completed games
                if status == "complete" and hs is not None and asc is not None:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO game_results "
                            "(sport,game_date,home_team,away_team,home_score,away_score,graded_at) "
                            "VALUES (?,?,?,?,?,?,?)",
                            (sport, game_date, home, away, int(hs), int(asc), now_str)
                        )
                    except:
                        pass

            time.sleep(0.3)
        except Exception as e:
            print(f"  [{sport}] Error: {e}")

    conn.commit()
    return total


def collect_fd_props(conn, now_str):
    """Collect FanDuel prop data for MLB (and NBA when in season)."""
    total = 0
    try:
        from fd_line_tracker import LineTracker, SPORT_PROP_CONFIG
        lt = LineTracker()

        from collections import defaultdict

        for sport in SPORT_PROP_CONFIG:
            props = lt.fetch_fanduel_props(sport=sport)
            if not props:
                continue

            from collections import defaultdict

            # Group O/U props by market_name+line (Over/Under share same market_name)
            ou_grouped = defaultdict(list)
            milestone_props = []

            for p in props:
                rname = p.get("runner_name", "")
                if rname.endswith(" Over") or rname.endswith(" Under"):
                    # O/U prop - group by game+market_name+line to pair Over/Under
                    key = (p["game"], p.get("market_name", ""), p.get("line", 0))
                    ou_grouped[key].append(p)
                else:
                    # Milestone prop (individual player as runner)
                    milestone_props.append(p)

            sport_count = 0

            # Store O/U props as paired rows
            for (game, market_name, line), entries in ou_grouped.items():
                over_odds = None
                under_odds = None
                player = ""
                for e in entries:
                    rname = e.get("runner_name", "")
                    if rname.endswith(" Over"):
                        over_odds = e.get("odds_american")
                        player = rname[:-5]  # Strip " Over"
                    elif rname.endswith(" Under"):
                        under_odds = e.get("odds_american")
                        if not player:
                            player = rname[:-6]  # Strip " Under"

                if over_odds is not None or under_odds is not None:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO fd_prop_snapshots "
                            "(collected_at,sport,game,player,market,line,over_odds,under_odds) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (now_str, sport, game, player, market_name,
                             float(line) if line else 0, over_odds, under_odds)
                        )
                        sport_count += 1
                    except:
                        pass

            # Store milestone props (To Hit HR, 3+ Strikeouts, etc.)
            for e in milestone_props:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO fd_prop_snapshots "
                        "(collected_at,sport,game,player,market,line,over_odds,under_odds) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (now_str, sport, e["game"], e["player"],
                         e.get("market_name", e["market"]),
                         float(e.get("line", 0)) if e.get("line") else 0,
                         e["odds_american"], None)
                    )
                    sport_count += 1
                except:
                    pass

            print(f"    [FD-{sport}] {sport_count} props stored")
            total += sport_count

        conn.commit()
    except Exception as e:
        print(f"  [FD] Error: {e}")

    return total


def run_collection():
    """Run a single data collection cycle."""
    start = time.time()
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M")

    print(f"\n  [{now.strftime('%H:%M UTC')}] Collecting data...")

    conn = get_db()

    gl_count = collect_game_lines(conn, now_str)
    print(f"    Game lines: {gl_count} records")

    fd_count = collect_fd_props(conn, now_str)
    print(f"    FD props: {fd_count} records")

    # Count graded games
    graded = conn.execute(
        "SELECT COUNT(DISTINCT home_team||away_team||game_date) FROM game_results"
    ).fetchone()[0]

    duration = time.time() - start

    conn.execute(
        "INSERT INTO collection_log (collected_at,game_lines_count,fd_props_count,games_graded,duration_sec) "
        "VALUES (?,?,?,?,?)",
        (now_str, gl_count, fd_count, graded, round(duration, 1))
    )
    conn.commit()

    # Stats
    total_gl = conn.execute("SELECT COUNT(*) FROM game_line_snapshots").fetchone()[0]
    total_fd = conn.execute("SELECT COUNT(*) FROM fd_prop_snapshots").fetchone()[0]
    total_gr = conn.execute("SELECT COUNT(*) FROM game_results").fetchone()[0]
    collections = conn.execute("SELECT COUNT(*) FROM collection_log").fetchone()[0]

    print(f"    Duration: {duration:.1f}s")
    print(f"    DB totals: {total_gl} GL records, {total_fd} FD records, {total_gr} game results, {collections} collections")

    conn.close()


def show_stats():
    """Show database statistics."""
    conn = get_db()
    print(f"\n  DATABASE STATISTICS")
    print(f"  DB: {DB_PATH}")
    print(f"  Size: {os.path.getsize(DB_PATH)/1024/1024:.1f} MB")

    for table in ["game_line_snapshots", "fd_prop_snapshots", "game_results", "collection_log"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")

    # Unique dates
    dates = conn.execute(
        "SELECT DISTINCT collected_at FROM collection_log ORDER BY collected_at"
    ).fetchall()
    if dates:
        print(f"  Collection dates: {dates[0][0]} to {dates[-1][0]} ({len(dates)} collections)")

    # Game results by sport
    for sport in ["NBA", "MLB", "NHL"]:
        count = conn.execute(
            "SELECT COUNT(*) FROM game_results WHERE sport=?", (sport,)
        ).fetchone()[0]
        print(f"  {sport} results: {count}")

    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_stats()
    elif len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        print(f"  Data collection: every {interval} min")
        while True:
            try:
                run_collection()
            except Exception as e:
                print(f"  Error: {e}")
            time.sleep(interval * 60)
    else:
        run_collection()

"""
Sports Edge - FanDuel Line Movement Tracker
Strategy: Track how FanDuel odds change over time.
When lines move sharply, the OTHER side often becomes +EV.

Key insight: Line movement IS information. Sportsbooks move lines because
sharp money hit one side. If we detect this early, we can bet the other side
before the full correction happens.

Also: Correlation analysis between related markets (P+R+A vs PRA combo).
"""

import json
import os
import sqlite3
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "line_tracker.db")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# FanDuel config
FD_BASE = "https://sbapi.mi.sportsbook.fanduel.com/api"
FD_AK = "FhMFpcPWXMeyZxOx"
FD_PROP_TABS = {
    "player-points": "Points",
    "player-assists": "Assists",
    "player-rebounds": "Rebounds",
    "player-threes": "Threes",
    "player-combos": "Combos",
}

# Multi-sport prop configurations
# Each sport: customPageId for event listing, tabs to fetch, and market parsing rules
SPORT_PROP_CONFIG = {
    "NBA": {
        "page_id": "nba",
        "tabs": {
            "player-points": "Points",
            "player-assists": "Assists",
            "player-rebounds": "Rebounds",
            "player-threes": "Threes",
            "player-combos": "Combos",
        },
    },
    "MLB": {
        "page_id": "mlb",
        "tabs": {
            "batter-props": "Batter Props",
            "pitcher-props": "Pitcher Props",
        },
    },
    # NHL player props not available through this API endpoint as of Apr 2026.
    # Games only return 4 game-level markets regardless of tab name.
    # Will re-check periodically or find alternative data source.
}


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


def implied_to_american(imp):
    if imp <= 0 or imp >= 1:
        return 0
    if imp > 0.5:
        return int(-100 * imp / (1 - imp))
    else:
        return int(100 * (1 - imp) / imp)


class LineTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._init_db()

    def _init_db(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            game TEXT,
            player TEXT NOT NULL,
            market TEXT NOT NULL,
            market_name TEXT,
            line REAL,
            odds_american INTEGER,
            odds_decimal REAL,
            runner_name TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS line_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT NOT NULL,
            player TEXT NOT NULL,
            market TEXT NOT NULL,
            line REAL,
            old_odds INTEGER,
            new_odds INTEGER,
            odds_change INTEGER,
            implied_change REAL,
            direction TEXT,
            game TEXT,
            signal TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS correlation_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT NOT NULL,
            player TEXT NOT NULL,
            game TEXT,
            individual_sum REAL,
            combo_line REAL,
            discrepancy REAL,
            signal TEXT,
            details TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snap_player ON snapshots(player, market)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_snap_time ON snapshots(timestamp)")
        conn.commit()
        conn.close()

    def fetch_fanduel_props(self, sport="NBA"):
        """Fetch FanDuel player props for a given sport. Returns list of prop dicts."""
        props = []
        config = SPORT_PROP_CONFIG.get(sport)
        if not config:
            print(f"  [FD] No prop config for {sport}")
            return props

        try:
            resp = self.session.get(f"{FD_BASE}/content-managed-page",
                params={"page": "CUSTOM", "customPageId": config["page_id"],
                        "pbHorizontal": "true", "_ak": FD_AK}, timeout=15)
            if resp.status_code != 200:
                print(f"  [FD-{sport}] Event list error: {resp.status_code}")
                return props

            data = resp.json()
            events = data.get("attachments", {}).get("events", {})
            games = []
            for eid, ev in events.items():
                name = ev.get("name", "")
                if "v" in name.lower() or "@" in name.lower():
                    games.append({"id": eid, "name": name})

            print(f"  [FD-{sport}] {len(games)} games found")

            for game in games:
                for tab_url, market_label in config["tabs"].items():
                    try:
                        resp = self.session.get(f"{FD_BASE}/event-page",
                            params={"eventId": game["id"], "tab": tab_url, "_ak": FD_AK},
                            timeout=15)
                        if resp.status_code != 200:
                            continue

                        markets = resp.json().get("attachments", {}).get("markets", {})
                        for mid, mkt in markets.items():
                            mkt_name = mkt.get("marketName", "")
                            mkt_type = mkt.get("marketType", "")

                            # Skip game-level markets mixed into prop tabs
                            if mkt_type in ("MONEY_LINE", "MATCH_HANDICAP_(2-WAY)",
                                            "TOTAL_POINTS_(OVER/UNDER)"):
                                continue

                            for runner in mkt.get("runners", []):
                                player = runner.get("runnerName", "")
                                handicap = runner.get("handicap", 0)
                                odds_data = runner.get("winRunnerOdds", {})
                                american = odds_data.get("americanDisplayOdds", {}).get("americanOdds")
                                if not player or american is None:
                                    continue
                                if player in ("Over", "Under", "Yes", "No", "Odd", "Even"):
                                    continue
                                try:
                                    american = int(american)
                                except (ValueError, TypeError):
                                    continue

                                props.append({
                                    "sport": sport,
                                    "game": game["name"],
                                    "player": player,
                                    "market": market_label,
                                    "market_name": mkt_name,
                                    "market_type": mkt_type,
                                    "line": handicap,
                                    "odds_american": american,
                                    "odds_decimal": round(american_to_decimal(american), 4),
                                    "runner_name": runner.get("runnerName", ""),
                                })
                        time.sleep(0.15)
                    except Exception as e:
                        print(f"  [FD-{sport}] Error on {tab_url}: {e}")
                        continue

        except Exception as e:
            print(f"  [FD-{sport}] Fatal error: {e}")

        print(f"  [FD-{sport}] {len(props)} prop lines fetched")
        return props

    def snapshot(self):
        """Take a snapshot of current FanDuel odds and store in DB."""
        now = datetime.utcnow().isoformat()
        props = self.fetch_fanduel_props()
        if not props:
            print("  No props to snapshot")
            return 0

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for p in props:
            c.execute("""INSERT INTO snapshots
                (timestamp, game, player, market, market_name, line, odds_american, odds_decimal, runner_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (now, p["game"], p["player"], p["market"], p["market_name"],
                 p["line"], p["odds_american"], p["odds_decimal"], p["runner_name"]))
        conn.commit()
        conn.close()
        print(f"  [Snapshot] {len(props)} lines stored at {now}")
        return len(props)

    def detect_line_moves(self, min_odds_change=15, min_implied_change=0.03):
        """
        Compare latest snapshot against previous snapshots.
        Detect significant line movements.

        A line move of 15+ American odds points or 3%+ implied probability
        is a signal that sharp money moved the line.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get the two most recent distinct timestamps
        c.execute("SELECT DISTINCT timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 2")
        times = [r[0] for r in c.fetchall()]
        if len(times) < 2:
            print("  Need at least 2 snapshots to detect moves")
            conn.close()
            return []

        latest_time, prev_time = times[0], times[1]
        print(f"  Comparing {prev_time} -> {latest_time}")

        # Get latest snapshot
        c.execute("SELECT player, market, line, odds_american, game FROM snapshots WHERE timestamp=?",
                  (latest_time,))
        latest = {}
        for r in c.fetchall():
            key = (r[0], r[1], r[2])
            latest[key] = {"odds": r[3], "game": r[4]}

        # Get previous snapshot
        c.execute("SELECT player, market, line, odds_american, game FROM snapshots WHERE timestamp=?",
                  (prev_time,))
        previous = {}
        for r in c.fetchall():
            key = (r[0], r[1], r[2])
            previous[key] = {"odds": r[3], "game": r[4]}

        moves = []
        for key, curr in latest.items():
            if key not in previous:
                continue
            prev = previous[key]
            odds_change = curr["odds"] - prev["odds"]
            if abs(odds_change) < min_odds_change:
                continue

            curr_imp = decimal_to_implied(american_to_decimal(curr["odds"]))
            prev_imp = decimal_to_implied(american_to_decimal(prev["odds"]))
            imp_change = curr_imp - prev_imp

            if abs(imp_change) < min_implied_change:
                continue

            direction = "shortened" if odds_change < 0 else "lengthened"
            # Signal: if odds lengthened (got worse/higher), the OTHER side may be +EV
            # If odds shortened (got better), this side is getting steamed
            signal = "STEAM" if direction == "shortened" else "VALUE_OTHER_SIDE"

            move = {
                "player": key[0],
                "market": key[1],
                "line": key[2],
                "old_odds": prev["odds"],
                "new_odds": curr["odds"],
                "odds_change": odds_change,
                "implied_change": round(imp_change, 4),
                "direction": direction,
                "game": curr["game"],
                "signal": signal,
            }
            moves.append(move)

            c.execute("""INSERT INTO line_moves
                (detected_at, player, market, line, old_odds, new_odds, odds_change,
                 implied_change, direction, game, signal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (latest_time, key[0], key[1], key[2], prev["odds"], curr["odds"],
                 odds_change, imp_change, direction, curr["game"], signal))

        conn.commit()
        conn.close()

        moves.sort(key=lambda x: abs(x["implied_change"]), reverse=True)
        return moves

    def detect_correlation_arb(self):
        """
        Find correlation arbitrage within FanDuel markets.

        Key insight: FanDuel offers individual props (Points, Rebounds, Assists)
        AND combo props (PRA, P+R, P+A, R+A). The combo line should roughly
        equal the sum of individual lines. When they don't match, there's edge.

        Example: If PTS line is 25.5, REB line is 8.5, AST line is 6.5,
        then PRA should be around 40.5. If FD has PRA at 38.5, the under on
        individuals or over on PRA is mispriced.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get latest snapshot
        c.execute("SELECT DISTINCT timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return []
        latest_time = row[0]

        # Get all props from latest snapshot
        c.execute("""SELECT player, market, market_name, line, odds_american, game
                     FROM snapshots WHERE timestamp=?""", (latest_time,))
        rows = c.fetchall()

        # Group by player
        by_player = defaultdict(list)
        for r in rows:
            by_player[r[0]].append({
                "market": r[1], "market_name": r[2], "line": r[3],
                "odds": r[4], "game": r[5]
            })

        alerts = []
        for player, props_list in by_player.items():
            # Find individual lines
            pts_line = None
            reb_line = None
            ast_line = None
            threes_line = None

            # Find combo lines
            pra_line = None
            pr_line = None
            pa_line = None
            ra_line = None

            for p in props_list:
                mn = (p["market_name"] or "").lower()
                m = p["market"].lower()

                if m == "points" or "points" in mn and "combo" not in mn and "rebound" not in mn and "assist" not in mn:
                    if "over" not in mn and "under" not in mn:
                        pts_line = p["line"]
                elif m == "rebounds" or ("rebounds" in mn and "combo" not in mn and "point" not in mn and "assist" not in mn):
                    reb_line = p["line"]
                elif m == "assists" or ("assists" in mn and "combo" not in mn and "point" not in mn and "rebound" not in mn):
                    ast_line = p["line"]
                elif m == "threes" or "three" in mn or "3-pointer" in mn:
                    threes_line = p["line"]

                # Combo detection
                if "pts + reb + ast" in mn or "pra" in mn.replace(" ", ""):
                    pra_line = p["line"]
                elif "pts + reb" in mn and "ast" not in mn:
                    pr_line = p["line"]
                elif "pts + ast" in mn and "reb" not in mn:
                    pa_line = p["line"]
                elif "reb + ast" in mn and "pts" not in mn:
                    ra_line = p["line"]

            game = props_list[0]["game"] if props_list else ""

            # Check PRA vs sum of individuals
            if pts_line and reb_line and ast_line and pra_line:
                individual_sum = pts_line + reb_line + ast_line
                discrepancy = individual_sum - pra_line
                if abs(discrepancy) >= 1.5:
                    signal = "OVER_PRA" if discrepancy > 0 else "UNDER_PRA"
                    alert = {
                        "player": player,
                        "game": game,
                        "individual_sum": individual_sum,
                        "combo_line": pra_line,
                        "discrepancy": round(discrepancy, 1),
                        "signal": signal,
                        "details": f"PTS={pts_line} + REB={reb_line} + AST={ast_line} = {individual_sum} vs PRA={pra_line}",
                    }
                    alerts.append(alert)

                    c.execute("""INSERT INTO correlation_alerts
                        (detected_at, player, game, individual_sum, combo_line, discrepancy, signal, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (latest_time, player, game, individual_sum, pra_line,
                         discrepancy, signal, alert["details"]))

            # Check P+R vs individual sum
            if pts_line and reb_line and pr_line:
                ind_sum = pts_line + reb_line
                disc = ind_sum - pr_line
                if abs(disc) >= 1.0:
                    signal = "OVER_PR" if disc > 0 else "UNDER_PR"
                    alert = {
                        "player": player, "game": game,
                        "individual_sum": ind_sum, "combo_line": pr_line,
                        "discrepancy": round(disc, 1), "signal": signal,
                        "details": f"PTS={pts_line} + REB={reb_line} = {ind_sum} vs P+R={pr_line}",
                    }
                    alerts.append(alert)

            # Check P+A vs individual sum
            if pts_line and ast_line and pa_line:
                ind_sum = pts_line + ast_line
                disc = ind_sum - pa_line
                if abs(disc) >= 1.0:
                    signal = "OVER_PA" if disc > 0 else "UNDER_PA"
                    alert = {
                        "player": player, "game": game,
                        "individual_sum": ind_sum, "combo_line": pa_line,
                        "discrepancy": round(disc, 1), "signal": signal,
                        "details": f"PTS={pts_line} + AST={ast_line} = {ind_sum} vs P+A={pa_line}",
                    }
                    alerts.append(alert)

        conn.commit()
        conn.close()

        alerts.sort(key=lambda x: abs(x["discrepancy"]), reverse=True)
        return alerts

    def analyze_vig_outliers(self):
        """
        Find FanDuel props where the vig is unusually high or low.

        Normal FD vig: ~4-5% (implied probs sum to 1.04-1.05).
        If a market has 8%+ vig, FD is uncertain and pricing wide.
        If a market has 2% or less vig, it's priced tight — likely sharp.

        Wide-vig markets have more room for mispricing = more opportunity.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT DISTINCT timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return []
        latest_time = row[0]

        c.execute("""SELECT player, market, market_name, line, odds_american, game
                     FROM snapshots WHERE timestamp=?""", (latest_time,))
        rows = c.fetchall()

        # Group by (player, market_name) to find over/under pairs
        pairs = defaultdict(list)
        for r in rows:
            # Key: player + market description (to pair over/under)
            key = (r[0], r[2], r[3])  # player, market_name, line
            pairs[key].append({"odds": r[4], "game": r[5], "market": r[1]})

        outliers = []
        for key, odds_list in pairs.items():
            if len(odds_list) < 2:
                continue

            # Calculate total implied probability (should be >1 due to vig)
            total_imp = sum(decimal_to_implied(american_to_decimal(o["odds"])) for o in odds_list)
            vig = total_imp - 1.0

            if vig > 0.07:  # High vig (>7%)
                outliers.append({
                    "player": key[0],
                    "market_name": key[1],
                    "line": key[2],
                    "vig_pct": round(vig * 100, 1),
                    "total_implied": round(total_imp, 4),
                    "type": "HIGH_VIG",
                    "odds": [o["odds"] for o in odds_list],
                    "game": odds_list[0]["game"],
                })
            elif vig < 0.02:  # Low vig (<2%)
                outliers.append({
                    "player": key[0],
                    "market_name": key[1],
                    "line": key[2],
                    "vig_pct": round(vig * 100, 1),
                    "total_implied": round(total_imp, 4),
                    "type": "LOW_VIG",
                    "odds": [o["odds"] for o in odds_list],
                    "game": odds_list[0]["game"],
                })

        outliers.sort(key=lambda x: x["vig_pct"], reverse=True)
        return outliers

    def run_full_analysis(self):
        """Run complete analysis: snapshot + all detection methods."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        print(f"\n{'='*70}")
        print(f"  FANDUEL LINE TRACKER - Full Analysis")
        print(f"  {now}")
        print(f"{'='*70}")

        # Take snapshot
        count = self.snapshot()
        if count == 0:
            print("  No data to analyze")
            return

        # Detect line moves
        print(f"\n--- LINE MOVEMENTS ---")
        moves = self.detect_line_moves()
        if moves:
            for m in moves[:10]:
                arrow = "v" if m["direction"] == "shortened" else "^"
                print(f"  {arrow} {m['player']} {m['market']} {m['line']}: "
                      f"{m['old_odds']:+d} -> {m['new_odds']:+d} "
                      f"({m['implied_change']:+.1%}) [{m['signal']}]")
        else:
            print("  No significant line moves detected")

        # Correlation arbitrage
        print(f"\n--- CORRELATION ARBITRAGE ---")
        corr_alerts = self.detect_correlation_arb()
        if corr_alerts:
            for a in corr_alerts[:10]:
                print(f"  ** {a['player']}: {a['details']}")
                print(f"     Discrepancy: {a['discrepancy']:+.1f} pts -> {a['signal']}")
        else:
            print("  No correlation discrepancies found")

        # Vig outliers
        print(f"\n--- VIG OUTLIERS ---")
        outliers = self.analyze_vig_outliers()
        high_vig = [o for o in outliers if o["type"] == "HIGH_VIG"]
        low_vig = [o for o in outliers if o["type"] == "LOW_VIG"]
        print(f"  High vig (>7%): {len(high_vig)} markets")
        print(f"  Low vig (<2%): {len(low_vig)} markets")
        for o in high_vig[:5]:
            print(f"    {o['player']} {o['market_name']} line={o['line']}: "
                  f"vig={o['vig_pct']}% odds={o['odds']}")

        # Summary
        print(f"\n{'='*70}")
        print(f"  SUMMARY")
        print(f"  Props tracked: {count}")
        print(f"  Line moves: {len(moves)}")
        print(f"  Correlation alerts: {len(corr_alerts)}")
        print(f"  Vig outliers: {len(outliers)}")
        print(f"{'='*70}")

        # Save results
        results = {
            "timestamp": now,
            "props_count": count,
            "line_moves": moves[:20],
            "correlation_alerts": corr_alerts[:20],
            "vig_outliers": outliers[:20],
        }
        outpath = os.path.join(DATA_DIR, "line_tracker_latest.json")
        with open(outpath, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  Results saved to {outpath}")

        return results

    def continuous(self, interval_minutes=30, max_cycles=16):
        """Run continuous tracking with snapshots every N minutes."""
        print(f"\n  Starting continuous tracking (every {interval_minutes} min, {max_cycles} cycles)")
        for cycle in range(1, max_cycles + 1):
            print(f"\n  === Cycle {cycle}/{max_cycles} ===")
            self.run_full_analysis()
            if cycle < max_cycles:
                print(f"\n  Sleeping {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)


class HistoricalBacktester:
    """
    Backtest FD-only strategies against our historical prop data.
    We have months of props files in data/ directory.
    """
    def __init__(self):
        self.data_dir = DATA_DIR

    def load_historical_props(self):
        """Load all historical props files."""
        all_props = []
        props_files = sorted([f for f in os.listdir(self.data_dir)
                             if f.startswith("props_") and f.endswith(".json")])
        print(f"  Found {len(props_files)} historical props files")

        for fname in props_files:
            filepath = os.path.join(self.data_dir, fname)
            date = fname.replace("props_", "").replace(".json", "")
            try:
                with open(filepath) as f:
                    data = json.load(f)
                # Handle different formats
                if isinstance(data, list):
                    for p in data:
                        p["date"] = date
                    all_props.extend(data)
                elif isinstance(data, dict):
                    props = data.get("props", data.get("odds", []))
                    if isinstance(props, list):
                        for p in props:
                            p["date"] = date
                        all_props.extend(props)
            except Exception as e:
                print(f"  Error loading {fname}: {e}")
                continue

        print(f"  Loaded {len(all_props)} total historical props")
        return all_props

    def backtest_vig_strategy(self, props):
        """
        Strategy: Bet on props where FanDuel's vig is unusually low (<3%).
        Theory: Low vig = FD is confident in the line = closer to true probability.
        High vig = FD is uncertain = more room for edge.

        Actually test the inverse too: does HIGH vig predict which markets
        are easier to beat?
        """
        # Group into over/under pairs
        by_key = defaultdict(list)
        for p in props:
            player = p.get("player", p.get("runnerName", ""))
            market = p.get("market", p.get("stat", ""))
            line = p.get("line", p.get("handicap", 0))
            key = (p.get("date", ""), player, market, line)
            by_key[key].append(p)

        vig_buckets = {"low": [], "mid": [], "high": []}
        for key, pair in by_key.items():
            if len(pair) < 2:
                continue
            total_imp = 0
            for p in pair:
                odds = p.get("odds_american", p.get("american", 0))
                if not odds:
                    continue
                try:
                    odds = int(odds)
                except (ValueError, TypeError):
                    continue
                total_imp += decimal_to_implied(american_to_decimal(odds))

            if total_imp <= 0:
                continue
            vig = total_imp - 1.0

            if vig < 0.03:
                vig_buckets["low"].extend(pair)
            elif vig < 0.06:
                vig_buckets["mid"].extend(pair)
            else:
                vig_buckets["high"].extend(pair)

        print(f"\n  Vig bucket sizes: low={len(vig_buckets['low'])}, "
              f"mid={len(vig_buckets['mid'])}, high={len(vig_buckets['high'])}")
        return vig_buckets

    def backtest_line_value(self, props):
        """
        Strategy: Compare FanDuel lines to NBA averages.
        If FD sets a line significantly above/below a player's season average,
        there might be mispricing.

        This uses our box score data to check actual performance vs lines.
        """
        # Load box scores for actual results
        box_files = [f for f in os.listdir(self.data_dir) if f.startswith("box_")]
        if not box_files:
            print("  No box score data for backtest")
            return None

        # Build player stats
        player_stats = defaultdict(list)
        for bfile in box_files:
            try:
                with open(os.path.join(self.data_dir, bfile)) as f:
                    box = json.load(f)
                # Handle different box score formats
                game_data = box.get("game", box)
                for team_key in ["homeTeam", "awayTeam"]:
                    team = game_data.get(team_key, {})
                    players = team.get("players", [])
                    for player_data in players:
                        stats = player_data.get("statistics", {})
                        name = player_data.get("nameI", player_data.get("name", ""))
                        if not name or not stats:
                            continue
                        player_stats[name.lower()].append({
                            "pts": stats.get("points", 0),
                            "reb": stats.get("reboundsTotal", 0),
                            "ast": stats.get("assists", 0),
                            "fg3m": stats.get("threePointersMade", 0),
                            "min": stats.get("minutes", "0").replace("PT", "").replace("M", ""),
                        })
            except Exception:
                continue

        print(f"  Player stats from box scores: {len(player_stats)} players")

        # Check props against actuals
        results = {"correct": 0, "wrong": 0, "profit": 0.0, "bets": []}
        for p in props:
            player = (p.get("player", "")).lower()
            market = (p.get("market", p.get("stat", ""))).lower()
            line = p.get("line", 0)
            odds = p.get("odds_american", 0)
            if not player or not line or not odds:
                continue

            # Map market to stat
            stat_key = None
            if "point" in market:
                stat_key = "pts"
            elif "rebound" in market:
                stat_key = "reb"
            elif "assist" in market:
                stat_key = "ast"
            elif "three" in market or "3" in market:
                stat_key = "fg3m"

            if not stat_key:
                continue

            # Find player's recent averages
            if player not in player_stats:
                # Try partial match
                matches = [k for k in player_stats if player.split()[-1] in k]
                if matches:
                    player = matches[0]
                else:
                    continue

            games = player_stats[player]
            if len(games) < 5:
                continue

            avg = sum(g[stat_key] for g in games) / len(games)
            # If line is significantly different from average, bet accordingly
            if avg > line + 2:
                # Player averages significantly more -> bet over
                side = "over"
            elif avg < line - 2:
                side = "under"
            else:
                continue

            results["bets"].append({
                "player": player,
                "market": market,
                "line": line,
                "avg": round(avg, 1),
                "side": side,
                "odds": odds,
            })

        print(f"  Line value bets identified: {len(results['bets'])}")
        return results


if __name__ == "__main__":
    import sys

    tracker = LineTracker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            tracker.continuous(interval_minutes=interval)
        elif sys.argv[1] == "backtest":
            bt = HistoricalBacktester()
            props = bt.load_historical_props()
            bt.backtest_vig_strategy(props)
            bt.backtest_line_value(props)
        elif sys.argv[1] == "snapshot":
            tracker.snapshot()
        elif sys.argv[1] == "moves":
            moves = tracker.detect_line_moves()
            for m in moves:
                print(f"  {m['player']} {m['market']}: {m['old_odds']:+d} -> {m['new_odds']:+d}")
        elif sys.argv[1] == "corr":
            alerts = tracker.detect_correlation_arb()
            for a in alerts:
                print(f"  {a['player']}: {a['details']} -> {a['signal']}")
    else:
        tracker.run_full_analysis()

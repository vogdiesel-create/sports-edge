"""
Sports Edge - Cross-Book Historical Backtester

Uses our 69 historical props files (the-odds-api format with multi-book data)
and 518 box score files to measure actual profitability of various strategies.

Strategies tested:
1. Cross-book +EV (bet where one book offers better odds than devigged consensus)
2. Steam chasing (bet on props where one book moved significantly from the pack)
3. Correlation exploitation (combo lines vs individual sums)
4. Vig outlier betting (bet into high-vig markets)
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


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


def kelly_fraction(prob, decimal_odds, fraction=0.25):
    """Quarter Kelly sizing."""
    b = decimal_odds - 1
    q = 1 - prob
    f = (b * prob - q) / b
    return max(0, f * fraction)


class CrossBookBacktester:
    def __init__(self):
        self.props_data = []
        self.box_scores = {}  # game_date -> {player_name: {pts, reb, ast, fg3m}}
        self.results = {}

    def load_data(self):
        """Load all historical props and box scores."""
        # Load props files
        props_files = sorted([f for f in os.listdir(DATA_DIR)
                             if f.startswith("props_") and f.endswith(".json")])
        print(f"Loading {len(props_files)} props files...")

        total_props = 0
        for fname in props_files:
            date = fname.replace("props_", "").replace(".json", "")
            try:
                with open(os.path.join(DATA_DIR, fname)) as f:
                    data = json.load(f)

                events = data.get("events", [])
                if not events and isinstance(data, list):
                    events = data

                for ev in events:
                    bookmakers = ev.get("bookmakers", [])
                    home = ev.get("home_team", ev.get("_home", ""))
                    away = ev.get("away_team", ev.get("_away", ""))
                    game_name = f"{away} @ {home}"

                    for book in bookmakers:
                        book_key = book.get("key", "")
                        for market in book.get("markets", []):
                            market_key = market.get("key", "")
                            for outcome in market.get("outcomes", []):
                                player = outcome.get("description", "")
                                side = outcome.get("name", "").lower()
                                price = outcome.get("price", 0)
                                point = outcome.get("point", 0)

                                if not player or not price:
                                    continue

                                self.props_data.append({
                                    "date": date,
                                    "game": game_name,
                                    "book": book_key,
                                    "market": market_key,
                                    "player": player,
                                    "side": side,
                                    "odds_american": price,
                                    "odds_decimal": american_to_decimal(price),
                                    "line": point or 0,
                                })
                                total_props += 1
            except Exception as e:
                continue

        print(f"  Loaded {total_props} prop lines across {len(props_files)} dates")

        # Load box scores
        box_files = [f for f in os.listdir(DATA_DIR) if f.startswith("box_")]
        print(f"Loading {len(box_files)} box scores...")

        for bfile in box_files:
            try:
                with open(os.path.join(DATA_DIR, bfile)) as f:
                    box = json.load(f)

                game = box.get("game", {})
                game_date = game.get("gameTimeUTC", "")[:10]  # YYYY-MM-DD
                if not game_date:
                    # Try to extract from game data
                    game_date = game.get("gameCode", "")[:8] if game.get("gameCode") else ""
                    if game_date and len(game_date) == 8:
                        game_date = f"{game_date[:4]}-{game_date[4:6]}-{game_date[6:8]}"

                if not game_date:
                    continue

                if game_date not in self.box_scores:
                    self.box_scores[game_date] = {}

                for team_key in ["homeTeam", "awayTeam"]:
                    team = game.get(team_key, {})
                    for player in team.get("players", []):
                        stats = player.get("statistics", {})
                        name = player.get("nameI", "")
                        if not name or not stats:
                            continue

                        # Parse minutes
                        mins_str = stats.get("minutes", "PT0M")
                        try:
                            mins = float(mins_str.replace("PT", "").replace("M", "").split("S")[0])
                        except (ValueError, AttributeError):
                            mins = 0

                        self.box_scores[game_date][name.lower()] = {
                            "pts": stats.get("points", 0),
                            "reb": stats.get("reboundsTotal", 0),
                            "ast": stats.get("assists", 0),
                            "fg3m": stats.get("threePointersMade", 0),
                            "stl": stats.get("steals", 0),
                            "blk": stats.get("blocks", 0),
                            "min": mins,
                            "pra": stats.get("points", 0) + stats.get("reboundsTotal", 0) + stats.get("assists", 0),
                        }
            except Exception:
                continue

        print(f"  Loaded stats for {sum(len(v) for v in self.box_scores.values())} player-games")
        print(f"  Date range: {min(self.box_scores.keys()) if self.box_scores else 'none'} to "
              f"{max(self.box_scores.keys()) if self.box_scores else 'none'}")

    def _resolve_outcome(self, player, market, line, side, date):
        """Check if a prop bet won or lost using box score data."""
        if date not in self.box_scores:
            return None

        # Normalize player name for matching
        player_lower = player.lower().strip()

        # Try exact match
        actuals = self.box_scores[date].get(player_lower)

        if not actuals:
            # Try last name match
            last_name = player_lower.split()[-1] if player_lower else ""
            matches = [(k, v) for k, v in self.box_scores[date].items()
                      if last_name and last_name in k]
            if len(matches) == 1:
                actuals = matches[0][1]
            elif len(matches) > 1:
                # Try first initial + last name
                first_initial = player_lower[0] if player_lower else ""
                refined = [(k, v) for k, v in matches
                          if k.startswith(first_initial)]
                if len(refined) == 1:
                    actuals = refined[0][1]

        if not actuals:
            return None

        # Map market to stat
        stat_map = {
            "player_points": "pts",
            "player_rebounds": "reb",
            "player_assists": "ast",
            "player_threes": "fg3m",
            "player_points_rebounds_assists": "pra",
            "player_steals": "stl",
            "player_blocks": "blk",
        }

        stat_key = stat_map.get(market)
        if not stat_key:
            # Try partial matching
            for mk, sk in stat_map.items():
                if mk in market or market in mk:
                    stat_key = sk
                    break

        if not stat_key:
            return None

        actual = actuals.get(stat_key, 0)
        if actual == line:
            return None  # Push

        if side == "over":
            return actual > line
        else:
            return actual < line

    def backtest_cross_book_ev(self, min_edge=0.03, min_ev=0.02):
        """
        Strategy 1: Cross-book +EV detection.
        For each prop, devig across all books offering it.
        Bet when one book's odds exceed the devigged fair line.
        """
        print(f"\n{'='*60}")
        print(f"  STRATEGY 1: Cross-Book +EV")
        print(f"  min_edge={min_edge}, min_ev={min_ev}")
        print(f"{'='*60}")

        # Group props by (date, player, market, line, side)
        groups = defaultdict(list)
        for p in self.props_data:
            key = (p["date"], p["player"].lower(), p["market"], p["line"], p["side"])
            groups[key].append(p)

        # Find cross-book opportunities
        bets = []
        bankroll = 1000.0
        for key, book_props in groups.items():
            if len(set(p["book"] for p in book_props)) < 2:
                continue

            # Calculate devigged fair probability
            implieds = [(p["book"], p["odds_decimal"],
                        decimal_to_implied(p["odds_decimal"])) for p in book_props]
            avg_implied = sum(imp for _, _, imp in implieds) / len(implieds)

            for book, dec, imp in implieds:
                edge = avg_implied - imp
                ev = avg_implied * (dec - 1) - (1 - avg_implied)

                if edge >= min_edge and ev >= min_ev:
                    date, player, market, line, side = key
                    outcome = self._resolve_outcome(player, market, line, side, date)
                    if outcome is None:
                        continue

                    kf = kelly_fraction(avg_implied, dec)
                    stake = min(bankroll * kf, bankroll * 0.02)  # Cap at 2%
                    if stake < 5:
                        continue

                    pnl = stake * (dec - 1) if outcome else -stake
                    bankroll += pnl

                    bets.append({
                        "date": date,
                        "player": player,
                        "market": market,
                        "line": line,
                        "side": side,
                        "book": book,
                        "odds": dec,
                        "edge": round(edge, 4),
                        "ev": round(ev, 4),
                        "fair_prob": round(avg_implied, 4),
                        "n_books": len(set(p["book"] for p in book_props)),
                        "won": outcome,
                        "stake": round(stake, 2),
                        "pnl": round(pnl, 2),
                        "bankroll": round(bankroll, 2),
                    })

        if bets:
            wins = sum(1 for b in bets if b["won"])
            total_staked = sum(b["stake"] for b in bets)
            total_pnl = bankroll - 1000
            roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0

            print(f"\n  Results:")
            print(f"  Bets: {len(bets)}")
            print(f"  Win rate: {wins}/{len(bets)} ({wins/len(bets)*100:.1f}%)")
            print(f"  Total staked: ${total_staked:.2f}")
            print(f"  P&L: ${total_pnl:+.2f}")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Final bankroll: ${bankroll:.2f} (started $1000)")

            # By book
            by_book = defaultdict(lambda: {"bets": 0, "wins": 0, "pnl": 0})
            for b in bets:
                by_book[b["book"]]["bets"] += 1
                by_book[b["book"]]["wins"] += 1 if b["won"] else 0
                by_book[b["book"]]["pnl"] += b["pnl"]

            print(f"\n  By book:")
            for book, stats in sorted(by_book.items(), key=lambda x: -x[1]["pnl"]):
                wr = stats["wins"]/stats["bets"]*100 if stats["bets"] else 0
                print(f"    {book}: {stats['bets']} bets, {wr:.0f}% WR, ${stats['pnl']:+.2f}")

            # By market
            by_market = defaultdict(lambda: {"bets": 0, "wins": 0, "pnl": 0})
            for b in bets:
                by_market[b["market"]]["bets"] += 1
                by_market[b["market"]]["wins"] += 1 if b["won"] else 0
                by_market[b["market"]]["pnl"] += b["pnl"]

            print(f"\n  By market:")
            for mkt, stats in sorted(by_market.items(), key=lambda x: -x[1]["pnl"]):
                wr = stats["wins"]/stats["bets"]*100 if stats["bets"] else 0
                print(f"    {mkt}: {stats['bets']} bets, {wr:.0f}% WR, ${stats['pnl']:+.2f}")

            # By edge bucket
            print(f"\n  By edge bucket:")
            for edge_min, edge_max, label in [(0.03, 0.05, "3-5%"), (0.05, 0.08, "5-8%"),
                                               (0.08, 0.12, "8-12%"), (0.12, 1.0, "12%+")]:
                bucket = [b for b in bets if edge_min <= b["edge"] < edge_max]
                if bucket:
                    bw = sum(1 for b in bucket if b["won"])
                    bp = sum(b["pnl"] for b in bucket)
                    print(f"    {label}: {len(bucket)} bets, {bw/len(bucket)*100:.0f}% WR, ${bp:+.2f}")
        else:
            print("  No bets placed (insufficient cross-book data or no resolvable outcomes)")

        self.results["cross_book_ev"] = {
            "bets": len(bets),
            "final_bankroll": round(bankroll, 2),
            "roi": round((bankroll - 1000) / max(1, sum(b["stake"] for b in bets)) * 100, 2) if bets else 0,
        }
        return bets

    def backtest_steam_chasing(self, min_deviation=0.05):
        """
        Strategy 2: Steam chasing.
        When one book's odds significantly deviate from the pack,
        bet at that book (they haven't moved yet, or they've moved wrong).
        """
        print(f"\n{'='*60}")
        print(f"  STRATEGY 2: Steam Chasing")
        print(f"  min_deviation={min_deviation}")
        print(f"{'='*60}")

        groups = defaultdict(list)
        for p in self.props_data:
            key = (p["date"], p["player"].lower(), p["market"], p["line"], p["side"])
            groups[key].append(p)

        bets = []
        bankroll = 1000.0

        for key, book_props in groups.items():
            books = set(p["book"] for p in book_props)
            if len(books) < 3:  # Need 3+ books for steam detection
                continue

            # Calculate median implied probability
            implieds = sorted([decimal_to_implied(p["odds_decimal"]) for p in book_props])
            median_imp = implieds[len(implieds) // 2]

            # Find outlier books (odds significantly better than median)
            for p in book_props:
                imp = decimal_to_implied(p["odds_decimal"])
                deviation = median_imp - imp  # Positive = this book offers better odds

                if deviation >= min_deviation:
                    date, player, market, line, side = key
                    outcome = self._resolve_outcome(player, market, line, side, date)
                    if outcome is None:
                        continue

                    stake = min(bankroll * 0.01, bankroll * 0.02)  # 1% Kelly
                    if stake < 5:
                        continue

                    pnl = stake * (p["odds_decimal"] - 1) if outcome else -stake
                    bankroll += pnl

                    bets.append({
                        "date": date, "player": player, "market": market,
                        "line": line, "side": side, "book": p["book"],
                        "odds": p["odds_decimal"],
                        "deviation": round(deviation, 4),
                        "median_imp": round(median_imp, 4),
                        "n_books": len(books),
                        "won": outcome, "stake": round(stake, 2),
                        "pnl": round(pnl, 2), "bankroll": round(bankroll, 2),
                    })

        if bets:
            wins = sum(1 for b in bets if b["won"])
            total_staked = sum(b["stake"] for b in bets)
            total_pnl = bankroll - 1000
            roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0

            print(f"\n  Results:")
            print(f"  Bets: {len(bets)}")
            print(f"  Win rate: {wins}/{len(bets)} ({wins/len(bets)*100:.1f}%)")
            print(f"  P&L: ${total_pnl:+.2f}")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Final bankroll: ${bankroll:.2f}")
        else:
            print("  No bets placed")

        self.results["steam_chasing"] = {
            "bets": len(bets),
            "final_bankroll": round(bankroll, 2),
        }
        return bets

    def backtest_fanduel_value(self):
        """
        Strategy 3: FanDuel-only value detection.
        When FanDuel is the outlier (best odds) among all books,
        bet at FanDuel. This is our actionable strategy since FD is
        the book we can consistently scrape.
        """
        print(f"\n{'='*60}")
        print(f"  STRATEGY 3: FanDuel Best-Price Detection")
        print(f"{'='*60}")

        groups = defaultdict(list)
        for p in self.props_data:
            key = (p["date"], p["player"].lower(), p["market"], p["line"], p["side"])
            groups[key].append(p)

        bets = []
        bankroll = 1000.0

        for key, book_props in groups.items():
            books = set(p["book"] for p in book_props)
            if len(books) < 2 or "fanduel" not in books:
                continue

            # Get FanDuel's odds
            fd_props = [p for p in book_props if p["book"] == "fanduel"]
            other_props = [p for p in book_props if p["book"] != "fanduel"]

            if not fd_props or not other_props:
                continue

            fd_imp = decimal_to_implied(fd_props[0]["odds_decimal"])
            other_imps = [decimal_to_implied(p["odds_decimal"]) for p in other_props]
            avg_other_imp = sum(other_imps) / len(other_imps)

            # FD is offering better odds (lower implied prob) than other books
            edge = avg_other_imp - fd_imp
            if edge < 0.02:  # Need at least 2% edge
                continue

            # Devig to get fair probability
            all_imps = [fd_imp] + other_imps
            fair_prob = sum(all_imps) / len(all_imps)

            ev = fair_prob * (fd_props[0]["odds_decimal"] - 1) - (1 - fair_prob)
            if ev < 0.01:
                continue

            date, player, market, line, side = key
            outcome = self._resolve_outcome(player, market, line, side, date)
            if outcome is None:
                continue

            kf = kelly_fraction(fair_prob, fd_props[0]["odds_decimal"])
            stake = min(bankroll * kf, bankroll * 0.02)
            if stake < 5:
                continue

            pnl = stake * (fd_props[0]["odds_decimal"] - 1) if outcome else -stake
            bankroll += pnl

            bets.append({
                "date": date, "player": player, "market": market,
                "line": line, "side": side,
                "fd_odds": fd_props[0]["odds_decimal"],
                "fd_american": fd_props[0]["odds_american"],
                "edge": round(edge, 4),
                "ev": round(ev, 4),
                "fair_prob": round(fair_prob, 4),
                "n_books": len(books),
                "won": outcome, "stake": round(stake, 2),
                "pnl": round(pnl, 2), "bankroll": round(bankroll, 2),
            })

        if bets:
            wins = sum(1 for b in bets if b["won"])
            total_staked = sum(b["stake"] for b in bets)
            total_pnl = bankroll - 1000
            roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0

            print(f"\n  Results:")
            print(f"  Bets: {len(bets)}")
            print(f"  Win rate: {wins}/{len(bets)} ({wins/len(bets)*100:.1f}%)")
            print(f"  Total staked: ${total_staked:.2f}")
            print(f"  P&L: ${total_pnl:+.2f}")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Final bankroll: ${bankroll:.2f}")

            # By market
            by_market = defaultdict(lambda: {"bets": 0, "wins": 0, "pnl": 0, "staked": 0})
            for b in bets:
                by_market[b["market"]]["bets"] += 1
                by_market[b["market"]]["wins"] += 1 if b["won"] else 0
                by_market[b["market"]]["pnl"] += b["pnl"]
                by_market[b["market"]]["staked"] += b["stake"]

            print(f"\n  By market:")
            for mkt, stats in sorted(by_market.items(), key=lambda x: -x[1]["pnl"]):
                wr = stats["wins"]/stats["bets"]*100 if stats["bets"] else 0
                mroi = stats["pnl"]/stats["staked"]*100 if stats["staked"] else 0
                print(f"    {mkt}: {stats['bets']} bets, {wr:.0f}% WR, ${stats['pnl']:+.2f} ({mroi:+.1f}% ROI)")

            # By edge bucket
            print(f"\n  By edge bucket:")
            for lo, hi, label in [(0.02, 0.04, "2-4%"), (0.04, 0.06, "4-6%"),
                                   (0.06, 0.10, "6-10%"), (0.10, 1.0, "10%+")]:
                bucket = [b for b in bets if lo <= b["edge"] < hi]
                if bucket:
                    bw = sum(1 for b in bucket if b["won"])
                    bp = sum(b["pnl"] for b in bucket)
                    bs = sum(b["stake"] for b in bucket)
                    broi = bp/bs*100 if bs else 0
                    print(f"    {label}: {len(bucket)} bets, {bw/len(bucket)*100:.0f}% WR, "
                          f"${bp:+.2f} ({broi:+.1f}% ROI)")

            # Best bets
            print(f"\n  Top 10 profitable bets:")
            for b in sorted(bets, key=lambda x: -x["pnl"])[:10]:
                w = "W" if b["won"] else "L"
                print(f"    [{w}] {b['date']} {b['player']} {b['market']} {b['side']} "
                      f"{b['line']} @ {b['fd_american']:+d} | edge={b['edge']:.1%} | "
                      f"${b['pnl']:+.2f}")
        else:
            print("  No bets placed")

        self.results["fanduel_value"] = {
            "bets": len(bets),
            "final_bankroll": round(bankroll, 2),
            "details": bets[:50],
        }
        return bets

    def backtest_high_confidence(self, min_books=4, min_edge=0.05):
        """
        Strategy 4: High-confidence plays only.
        Only bet when 4+ books agree AND edge is 5%+.
        Fewer bets but higher quality.
        """
        print(f"\n{'='*60}")
        print(f"  STRATEGY 4: High Confidence ({min_books}+ books, {min_edge:.0%}+ edge)")
        print(f"{'='*60}")

        groups = defaultdict(list)
        for p in self.props_data:
            key = (p["date"], p["player"].lower(), p["market"], p["line"], p["side"])
            groups[key].append(p)

        bets = []
        bankroll = 1000.0

        for key, book_props in groups.items():
            books = set(p["book"] for p in book_props)
            if len(books) < min_books:
                continue

            implieds = [(p["book"], p["odds_decimal"],
                        decimal_to_implied(p["odds_decimal"])) for p in book_props]
            avg_implied = sum(imp for _, _, imp in implieds) / len(implieds)

            for book, dec, imp in implieds:
                edge = avg_implied - imp
                ev = avg_implied * (dec - 1) - (1 - avg_implied)

                if edge >= min_edge and ev >= 0.03:
                    date, player, market, line, side = key
                    outcome = self._resolve_outcome(player, market, line, side, date)
                    if outcome is None:
                        continue

                    kf = kelly_fraction(avg_implied, dec)
                    stake = min(bankroll * kf, bankroll * 0.02)
                    if stake < 5:
                        continue

                    pnl = stake * (dec - 1) if outcome else -stake
                    bankroll += pnl

                    bets.append({
                        "date": date, "player": player, "market": market,
                        "line": line, "side": side, "book": book,
                        "odds": dec, "edge": round(edge, 4),
                        "ev": round(ev, 4), "n_books": len(books),
                        "won": outcome, "stake": round(stake, 2),
                        "pnl": round(pnl, 2), "bankroll": round(bankroll, 2),
                    })

        if bets:
            wins = sum(1 for b in bets if b["won"])
            total_staked = sum(b["stake"] for b in bets)
            total_pnl = bankroll - 1000
            roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0

            print(f"\n  Results:")
            print(f"  Bets: {len(bets)}")
            print(f"  Win rate: {wins}/{len(bets)} ({wins/len(bets)*100:.1f}%)")
            print(f"  P&L: ${total_pnl:+.2f}")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Final bankroll: ${bankroll:.2f}")
        else:
            print("  No bets placed")

        self.results["high_confidence"] = {
            "bets": len(bets),
            "final_bankroll": round(bankroll, 2),
        }
        return bets

    def run_all(self):
        """Run all backtest strategies."""
        print(f"\n{'='*60}")
        print(f"  CROSS-BOOK HISTORICAL BACKTESTER")
        print(f"  {datetime.now(tz=None).strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        self.load_data()

        self.backtest_cross_book_ev()
        self.backtest_steam_chasing()
        self.backtest_fanduel_value()
        self.backtest_high_confidence()

        # Also test with different parameters
        print(f"\n{'='*60}")
        print(f"  PARAMETER SENSITIVITY ANALYSIS")
        print(f"{'='*60}")

        # Test different edge thresholds for cross-book EV
        for edge in [0.02, 0.04, 0.06, 0.08, 0.10]:
            bets = self.backtest_cross_book_ev(min_edge=edge, min_ev=0.01)
            n = len(bets) if bets else 0
            br = self.results.get("cross_book_ev", {}).get("final_bankroll", 1000)
            print(f"    edge>={edge:.0%}: {n} bets, bankroll=${br:.2f}")

        # Save all results
        outpath = os.path.join(DATA_DIR, "backtest_cross_book.json")
        with open(outpath, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n  Results saved to {outpath}")


if __name__ == "__main__":
    bt = CrossBookBacktester()
    bt.run_all()

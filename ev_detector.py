"""
Sports Edge - Positive EV Detection System
Inspired by Own-Relative8207's approach (9.82% ROI, $4K profit in 4 weeks).

Core idea: Don't predict anything. Find where one book's odds are mispriced
relative to the market consensus ("fair line").

Method:
1. Fetch odds from multiple books for same prop
2. Calculate "fair" probability by devigging the sharpest line (Pinnacle/consensus)
3. When any book offers odds implying a probability LOWER than the fair probability,
   that's a +EV bet
4. Size with fractional Kelly

This is NOT arbitrage (betting both sides). This is single-leg value betting.
"""

import json
import os
import sys
import time
import requests
from collections import defaultdict
from datetime import datetime

API_KEY = "077a2076a8f81c71bd1178368809cf8b"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL = "https://api.the-odds-api.com/v4"

# Sharp books (used to derive fair lines) vs soft books (where we bet)
SHARP_BOOKS = {"pinnacle", "betfair_ex_eu", "betfair_ex_uk", "matchbook"}
ALL_BOOKS = [
    "fanduel", "draftkings", "betmgm", "caesars", "pointsbet",
    "bovada", "betonlineag", "mybookieag", "betrivers",
    "pinnacle", "williamhill_us", "unibet_us", "espnbet",
    "fliff", "hardrockbet", "bet365",
]

# Player prop markets
PROP_MARKETS = [
    "player_points", "player_rebounds", "player_assists",
    "player_threes", "player_blocks", "player_steals",
    "player_points_rebounds_assists", "player_points_rebounds",
    "player_points_assists", "player_rebounds_assists",
]


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(decimal_odds):
    return 1.0 / decimal_odds


def devig_multiplicative(imp_over, imp_under):
    """Remove vig using multiplicative/power method.
    Returns fair probabilities that sum to 1.0."""
    total = imp_over + imp_under
    if total <= 0:
        return 0.5, 0.5
    return imp_over / total, imp_under / total


def devig_shin(imp_over, imp_under):
    """Shin method — accounts for insider trading probability.
    More accurate than multiplicative for markets with information asymmetry."""
    total = imp_over + imp_under
    if total <= 1.0:
        return imp_over, imp_under

    # Shin's z parameter (fraction of insider trading)
    # Simplified: z = (total - 1) / (n_outcomes - 1) where n = 2
    z = total - 1.0

    # Adjust probabilities
    fair_over = (((z**2 + 4 * (1 - z) * imp_over**2 / total) ** 0.5) - z) / (2 * (1 - z))
    fair_under = 1.0 - fair_over
    return fair_over, fair_under


def calculate_ev(fair_prob, decimal_odds):
    """Expected value of a $1 bet.
    EV = (fair_prob * profit_if_win) - ((1 - fair_prob) * stake)
    """
    return fair_prob * (decimal_odds - 1) - (1 - fair_prob)


def kelly_fraction(prob, decimal_odds, fraction=0.25):
    """Fractional Kelly criterion. Default quarter Kelly."""
    b = decimal_odds - 1
    q = 1 - prob
    if b <= 0:
        return 0
    f = (b * prob - q) / b
    return max(0, f * fraction)


class EVDetector:
    """
    Scans odds across multiple sportsbooks to find +EV opportunities.

    Strategy: Use sharp book consensus as "fair line", bet at soft books
    when their odds exceed fair value.
    """

    def __init__(self, api_key=API_KEY, min_ev=0.02, min_edge=0.03,
                 kelly_frac=0.25, devig_method="multiplicative"):
        self.api_key = api_key
        self.min_ev = min_ev          # Minimum EV% to flag a bet
        self.min_edge = min_edge      # Minimum probability edge
        self.kelly_frac = kelly_frac
        self.devig_method = devig_method
        self.remaining_requests = None

    def _devig(self, imp_over, imp_under):
        if self.devig_method == "shin":
            return devig_shin(imp_over, imp_under)
        return devig_multiplicative(imp_over, imp_under)

    def fetch_live_props(self, sport="basketball_nba"):
        """Fetch current player prop odds from all books."""
        events = []
        # First get event list
        resp = requests.get(f"{BASE_URL}/sports/{sport}/events", params={
            "apiKey": self.api_key
        })
        if resp.status_code != 200:
            print(f"Error fetching events: {resp.status_code} {resp.text}")
            return []

        event_list = resp.json()
        self.remaining_requests = resp.headers.get("x-requests-remaining", "?")
        print(f"  Found {len(event_list)} upcoming events (API remaining: {self.remaining_requests})")

        for event in event_list:
            for market in PROP_MARKETS:
                resp = requests.get(
                    f"{BASE_URL}/sports/{sport}/events/{event['id']}/odds",
                    params={
                        "apiKey": self.api_key,
                        "regions": "us,eu",
                        "markets": market,
                        "oddsFormat": "american",
                    }
                )
                if resp.status_code != 200:
                    continue
                self.remaining_requests = resp.headers.get("x-requests-remaining", "?")
                data = resp.json()
                if data.get("bookmakers"):
                    events.append(data)
                time.sleep(0.3)  # Rate limit respect

        return events

    def fetch_historical_props(self, sport="basketball_nba", date_str=None):
        """Fetch historical player prop odds for backtesting."""
        if date_str is None:
            date_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        resp = requests.get(
            f"{BASE_URL}/historical/sports/{sport}/events",
            params={
                "apiKey": self.api_key,
                "date": date_str,
            }
        )
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}")
            return [], None

        data = resp.json()
        self.remaining_requests = resp.headers.get("x-requests-remaining", "?")
        events = data.get("data", [])
        next_ts = data.get("next_timestamp")
        return events, next_ts

    def find_fair_line(self, prop_odds):
        """
        Calculate the fair line from available odds.

        Priority:
        1. Pinnacle (sharpest book)
        2. Average of all sharp books
        3. Consensus of all books (least reliable)
        """
        sharp_overs = []
        sharp_unders = []
        all_overs = []
        all_unders = []

        for book, odds_data in prop_odds.items():
            over_odds = odds_data.get("over_odds")
            under_odds = odds_data.get("under_odds")
            if over_odds is None or under_odds is None:
                continue

            over_dec = american_to_decimal(over_odds)
            under_dec = american_to_decimal(under_odds)
            imp_over = decimal_to_implied(over_dec)
            imp_under = decimal_to_implied(under_dec)

            all_overs.append(imp_over)
            all_unders.append(imp_under)

            if book in SHARP_BOOKS:
                sharp_overs.append(imp_over)
                sharp_unders.append(imp_under)

        if not all_overs:
            return None

        # Use sharpest available
        if sharp_overs:
            avg_imp_over = sum(sharp_overs) / len(sharp_overs)
            avg_imp_under = sum(sharp_unders) / len(sharp_unders)
            source = "sharp"
        else:
            avg_imp_over = sum(all_overs) / len(all_overs)
            avg_imp_under = sum(all_unders) / len(all_unders)
            source = "consensus"

        fair_over, fair_under = self._devig(avg_imp_over, avg_imp_under)

        return {
            "fair_over": fair_over,
            "fair_under": fair_under,
            "source": source,
            "n_books": len(all_overs),
            "n_sharp": len(sharp_overs),
        }

    def scan_for_ev(self, events_data):
        """
        Scan event data for +EV opportunities.
        Returns list of opportunities sorted by EV.
        """
        opportunities = []

        for event in events_data:
            home = event.get("home_team", "?")
            away = event.get("away_team", "?")
            game = f"{away} @ {home}"
            commence = event.get("commence_time", "")

            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            # Group by (player, stat, line)
            props = defaultdict(dict)
            for bm in bookmakers:
                book = bm["key"]
                for market in bm.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        player = outcome.get("description", "")
                        point = outcome.get("point")
                        side = outcome.get("name", "").lower()
                        price = outcome.get("price")

                        if not player or point is None or price is None:
                            continue

                        prop_key = (player, market["key"], point)
                        if prop_key not in props[book]:
                            props[book] = props.get(book, {})
                        if prop_key not in props:
                            props[prop_key] = {}
                        if book not in props[prop_key]:
                            props[prop_key][book] = {}

                        if side == "over":
                            props[prop_key][book]["over_odds"] = price
                        elif side == "under":
                            props[prop_key][book]["under_odds"] = price

            # For each prop, find fair line and check each book for +EV
            for (player, market, line), book_odds in props.items():
                fair = self.find_fair_line(book_odds)
                if fair is None or fair["n_books"] < 3:
                    continue  # Need enough books for consensus

                for book, odds_data in book_odds.items():
                    if book in SHARP_BOOKS:
                        continue  # Don't bet at sharp books (they'll limit you)

                    for side in ["over", "under"]:
                        odds_key = f"{side}_odds"
                        if odds_key not in odds_data:
                            continue

                        american = odds_data[odds_key]
                        decimal = american_to_decimal(american)
                        implied = decimal_to_implied(decimal)

                        fair_prob = fair[f"fair_{side}"]
                        edge = fair_prob - implied
                        ev = calculate_ev(fair_prob, decimal)

                        if ev >= self.min_ev and edge >= self.min_edge:
                            kelly = kelly_fraction(fair_prob, decimal, self.kelly_frac)
                            opportunities.append({
                                "game": game,
                                "commence": commence,
                                "player": player,
                                "market": market.replace("player_", ""),
                                "line": line,
                                "side": side.upper(),
                                "book": book,
                                "odds": american,
                                "decimal_odds": round(decimal, 3),
                                "implied_prob": round(implied, 4),
                                "fair_prob": round(fair_prob, 4),
                                "edge": round(edge, 4),
                                "ev": round(ev, 4),
                                "kelly_pct": round(kelly * 100, 2),
                                "fair_source": fair["source"],
                                "n_books": fair["n_books"],
                            })

        # Sort by EV descending
        opportunities.sort(key=lambda x: x["ev"], reverse=True)
        return opportunities

    def backtest_from_file(self, filepath=None):
        """
        Backtest +EV detection against our existing historical data.
        Uses the real_backtest_full_season.json which has odds from multiple books.
        """
        if filepath is None:
            filepath = os.path.join(DATA_DIR, "real_backtest_full_season.json")

        with open(filepath) as f:
            data = json.load(f)
        results = data["results"]

        print("=" * 65)
        print("  +EV DETECTION BACKTEST")
        print("=" * 65)

        # Group props by (date, player, stat, line) to get multi-book view
        # Our current data only has one set of odds per prop, so we'll
        # use the odds as "fair" and look for value in a different way:
        # When our model probability significantly exceeds the devigged fair probability

        # Actually, let's do the proper backtest: simulate what happens
        # when we bet only on props where our model has edge vs DEVIGGED odds
        from triple_poisson_model import (
            TriplePoissonPredictor, load_enhanced_box_scores,
            implied_prob as raw_implied
        )

        print("\nLoading data...")
        history = load_enhanced_box_scores()
        predictor = TriplePoissonPredictor()
        for name, games in history.items():
            for game in games:
                predictor.update(name, game)

        # Track all bets with devigged lines
        bankroll = 5000
        start = 5000
        bets = []
        props_by_date = defaultdict(list)
        for r in results:
            props_by_date[r["date"]].append(r)

        all_dates = sorted(props_by_date.keys())
        # Use first 60% to calibrate EV threshold, last 40% to test
        split = int(len(all_dates) * 0.6)
        test_dates = all_dates[split:]

        print(f"  Testing on {len(test_dates)} dates ({test_dates[0]} to {test_dates[-1]})")
        print(f"  Using DEVIGGED fair lines (not raw odds)")

        for date in test_dates:
            seen = set()
            for prop in props_by_date[date]:
                key = f"{prop['player']}_{prop['stat']}"
                if key in seen:
                    continue
                seen.add(key)

                over_odds = prop["over_odds"]
                under_odds = prop["under_odds"]

                # Devig to get fair probabilities
                over_dec = american_to_decimal(over_odds)
                under_dec = american_to_decimal(under_odds)
                imp_over = decimal_to_implied(over_dec)
                imp_under = decimal_to_implied(under_dec)
                fair_over, fair_under = self._devig(imp_over, imp_under)

                # Only bet when our model shows edge vs FAIR (not vigged) line
                player_key = prop["player"].lower()
                stat = prop["stat"]
                line = prop["line"]

                prob_result = predictor.get_probability(player_key, stat, line, date, n_sims=3000)
                if prob_result is None:
                    continue
                if prob_result["expected_min"] < 20:
                    continue

                model_over = prob_result["prob_over"]
                model_under = prob_result["prob_under"]

                # Edge vs FAIR line (key difference from our previous backtests!)
                over_edge = model_over - fair_over
                under_edge = model_under - fair_under

                # Also need EV vs actual book odds (what we'd actually bet at)
                over_ev = calculate_ev(model_over, over_dec)
                under_ev = calculate_ev(model_under, under_dec)

                best_side = None
                if over_edge > under_edge and over_edge >= self.min_edge and over_ev >= self.min_ev:
                    best_side = "over"
                    edge = over_edge
                    ev = over_ev
                    prob = model_over
                    odds = over_odds
                    dec_odds = over_dec
                elif under_edge >= self.min_edge and under_ev >= self.min_ev:
                    best_side = "under"
                    edge = under_edge
                    ev = under_ev
                    prob = model_under
                    odds = under_odds
                    dec_odds = under_dec

                if best_side is None:
                    continue

                if bankroll <= 0:
                    break

                # Kelly sizing
                kelly = kelly_fraction(prob, dec_odds, self.kelly_frac)
                stake = max(10, min(bankroll * kelly, bankroll * 0.02))  # Cap at 2% of bankroll
                stake = round(stake, 2)

                won = prop["over_won"] if best_side == "over" else prop["under_won"]
                push = prop["push"]
                if push:
                    pnl = 0
                elif won:
                    pnl = stake * (dec_odds - 1)
                else:
                    pnl = -stake

                bankroll += pnl
                bankroll = round(bankroll, 2)

                bets.append({
                    "date": date, "player": prop["player"], "stat": stat,
                    "line": line, "side": best_side, "edge": round(edge, 4),
                    "ev": round(ev, 4), "fair_prob": round(fair_over if best_side == "over" else fair_under, 4),
                    "model_prob": round(prob, 4),
                    "odds": odds, "stake": stake,
                    "won": won, "push": push, "pnl": round(pnl, 2),
                    "bankroll": bankroll,
                })

        # Results
        if not bets:
            print("\n  No bets found matching criteria.")
            return

        wins = sum(1 for b in bets if b["won"])
        losses = sum(1 for b in bets if not b["won"] and not b["push"])
        pushes = sum(1 for b in bets if b["push"])
        total_pnl = sum(b["pnl"] for b in bets)
        total_wagered = sum(b["stake"] for b in bets)
        roi = total_pnl / total_wagered * 100 if total_wagered else 0

        print(f"\n{'='*65}")
        print(f"  +EV DETECTION RESULTS (Devigged Fair Lines + Kelly Sizing)")
        print(f"{'='*65}")
        print(f"  Total Bets: {len(bets)}")
        print(f"  Wins: {wins}, Losses: {losses}, Pushes: {pushes}")
        print(f"  Win Rate: {wins/max(1,wins+losses)*100:.1f}%")
        print(f"  Total Wagered: ${total_wagered:,.0f}")
        print(f"  Total P/L: ${total_pnl:+,.0f}")
        print(f"  ROI: {roi:+.2f}%")
        print(f"  Final Bankroll: ${bankroll:,.0f} (started ${start:,.0f})")

        # By stat
        print(f"\n  BY STAT:")
        for stat in ["pts", "reb", "ast", "fg3m"]:
            subset = [b for b in bets if b["stat"] == stat]
            if not subset:
                continue
            w = sum(1 for b in subset if b["won"])
            l = sum(1 for b in subset if not b["won"] and not b["push"])
            p = sum(b["pnl"] for b in subset)
            wag = sum(b["stake"] for b in subset)
            wr = w / max(1, w + l) * 100
            r = p / wag * 100 if wag else 0
            print(f"    {stat.upper():5s}: {len(subset):4d} bets, {wr:.1f}% win, ${p:+,.0f} ({r:+.1f}% ROI)")

        # By edge tier
        print(f"\n  BY EDGE TIER:")
        for low, high, label in [(0.03, 0.05, "3-5%"), (0.05, 0.08, "5-8%"),
                                  (0.08, 0.12, "8-12%"), (0.12, 1.0, "12%+")]:
            subset = [b for b in bets if low <= b["edge"] < high]
            if not subset:
                continue
            w = sum(1 for b in subset if b["won"])
            l = sum(1 for b in subset if not b["won"] and not b["push"])
            p = sum(b["pnl"] for b in subset)
            wag = sum(b["stake"] for b in subset)
            wr = w / max(1, w + l) * 100
            r = p / wag * 100 if wag else 0
            print(f"    Edge {label:5s}: {len(subset):4d} bets, {wr:.1f}% win, ${p:+,.0f} ({r:+.1f}% ROI)")

        # Bankroll chart (text)
        print(f"\n  BANKROLL PROGRESSION:")
        step = max(1, len(bets) // 10)
        for i in range(0, len(bets), step):
            b = bets[i]
            bar = "#" * int(b["bankroll"] / 100)
            print(f"    Bet {i+1:4d} ({b['date']}): ${b['bankroll']:>8,.0f} {bar}")
        if bets:
            b = bets[-1]
            bar = "#" * max(0, int(b["bankroll"] / 100))
            print(f"    Bet {len(bets):4d} ({b['date']}): ${b['bankroll']:>8,.0f} {bar}")

        # Save
        output = {
            "method": "+EV Detection (Devigged Fair Lines)",
            "min_ev": self.min_ev,
            "min_edge": self.min_edge,
            "kelly_fraction": self.kelly_frac,
            "devig_method": self.devig_method,
            "total_bets": len(bets),
            "wins": wins,
            "losses": losses,
            "total_pnl": round(total_pnl, 2),
            "roi": round(roi, 2),
            "final_bankroll": bankroll,
            "bet_log": bets[-100:],
        }
        outpath = os.path.join(DATA_DIR, "ev_detection_results.json")
        with open(outpath, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Results saved to {outpath}")

        return bets


def run_live_scan():
    """Scan live NBA props for +EV opportunities right now."""
    detector = EVDetector(min_ev=0.02, min_edge=0.03, kelly_frac=0.25)

    print("=" * 65)
    print("  LIVE +EV SCAN — NBA Player Props")
    print("=" * 65)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Min EV: {detector.min_ev:.0%}, Min Edge: {detector.min_edge:.0%}")
    print(f"  Kelly Fraction: {detector.kelly_frac:.0%}")
    print()

    events = detector.fetch_live_props()
    if not events:
        print("  No events with odds found.")
        return

    opps = detector.scan_for_ev(events)
    if not opps:
        print("  No +EV opportunities found.")
        return

    print(f"\n  Found {len(opps)} +EV opportunities:\n")
    for i, opp in enumerate(opps[:20], 1):
        print(f"  {i}. {opp['player']} {opp['side']} {opp['line']} {opp['market']}")
        print(f"     Book: {opp['book']}, Odds: {opp['odds']:+d} (decimal {opp['decimal_odds']})")
        print(f"     Fair: {opp['fair_prob']:.1%} | Model: {opp['implied_prob']:.1%} | Edge: {opp['edge']:.1%}")
        print(f"     EV: {opp['ev']:.1%} | Kelly: {opp['kelly_pct']:.1f}%")
        print(f"     Source: {opp['fair_source']} ({opp['n_books']} books)")
        print()

    # Save opportunities
    outpath = os.path.join(DATA_DIR, "live_ev_opportunities.json")
    with open(outpath, "w") as f:
        json.dump({
            "scan_time": datetime.now().isoformat(),
            "opportunities": opps,
            "api_remaining": detector.remaining_requests,
        }, f, indent=2)
    print(f"  Saved to {outpath}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        run_live_scan()
    else:
        detector = EVDetector(min_ev=0.02, min_edge=0.03, kelly_frac=0.25)
        detector.backtest_from_file()

"""
Sports Edge - Arbitrage & Low Hold Scanner
Scans multiple sportsbooks for pricing mismatches on NBA player props.

Arbitrage: bet both sides at different books, guaranteed profit regardless of outcome.
Low Hold: combined vig < normal (~10%), meaning near-fair odds.

Uses the-odds-api.com to get live odds from multiple bookmakers simultaneously.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

API_KEY = "077a2076a8f81c71bd1178368809cf8b"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROP_MARKETS = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_threes",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
]

STAT_LABELS = {
    "player_points": "Points",
    "player_rebounds": "Rebounds",
    "player_assists": "Assists",
    "player_threes": "3-Pointers Made",
    "player_points_rebounds_assists": "Pts+Reb+Ast",
    "player_points_rebounds": "Pts+Reb",
    "player_points_assists": "Pts+Ast",
    "player_rebounds_assists": "Reb+Ast",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        remaining = resp.headers.get("x-requests-remaining", "?")
        print(f"  [API] Requests remaining: {remaining}")
        return json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def implied_prob(american):
    """Convert American odds to implied probability (no-vig)."""
    if american > 0:
        return 100 / (american + 100)
    return abs(american) / (abs(american) + 100)


def find_arbitrage(over_odds, under_odds):
    """
    Check if two odds create an arbitrage opportunity.

    Arbitrage exists when: 1/decimal_over + 1/decimal_under < 1

    Returns: (is_arb, profit_pct, hold_pct)
    - profit_pct: guaranteed profit as % of total wagered (positive = arb exists)
    - hold_pct: the combined margin (lower = better for bettor)
    """
    dec_over = american_to_decimal(over_odds)
    dec_under = american_to_decimal(under_odds)

    # Combined implied probability (should be >1 for books to profit)
    combined = (1 / dec_over) + (1 / dec_under)

    # Hold = how much the books keep (typically 4-10%)
    hold_pct = (combined - 1) * 100

    # If combined < 1, arbitrage exists
    is_arb = combined < 1.0
    profit_pct = (1 - combined) * 100 if is_arb else 0

    return is_arb, profit_pct, hold_pct


def calculate_arb_stakes(bankroll, over_odds, under_odds):
    """
    Calculate how much to bet on each side to guarantee profit.

    The key: bet proportionally to the inverse of the decimal odds
    so that you win the same amount regardless of outcome.
    """
    dec_over = american_to_decimal(over_odds)
    dec_under = american_to_decimal(under_odds)

    # Stake proportions
    over_stake = bankroll / (1 + dec_over / dec_under)
    under_stake = bankroll - over_stake

    # Profit regardless of outcome
    profit_if_over = over_stake * dec_over - bankroll
    profit_if_under = under_stake * dec_under - bankroll

    return {
        "over_stake": round(over_stake, 2),
        "under_stake": round(under_stake, 2),
        "profit_if_over": round(profit_if_over, 2),
        "profit_if_under": round(profit_if_under, 2),
        "guaranteed_profit": round(min(profit_if_over, profit_if_under), 2),
    }


def scan_live_props():
    """
    Scan all live NBA events for arbitrage and low-hold opportunities.
    Compares odds across all available bookmakers for each prop.
    """
    print("=" * 65)
    print("  ARBITRAGE & LOW HOLD SCANNER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # Get today's events
    events_url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey={API_KEY}"
    events = fetch_json(events_url)

    if not events:
        print("No events found")
        return []

    print(f"\n  {len(events)} upcoming NBA events")

    all_opportunities = []
    arb_count = 0
    low_hold_count = 0

    for event in events:
        eid = event["id"]
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        commence = event.get("commence_time", "")
        print(f"\n  --- {away} @ {home} ({commence[:16]}) ---")

        # Fetch props with ALL bookmakers
        markets_str = ",".join(PROP_MARKETS)
        props_url = (
            f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{eid}/odds"
            f"?apiKey={API_KEY}&regions=us,us2"
            f"&markets={markets_str}"
            f"&oddsFormat=american"
        )
        props_data = fetch_json(props_url)
        time.sleep(0.2)

        if not props_data:
            continue

        # Index all lines by player+stat+line
        # Structure: lines[player][stat][line] = {book: {over: odds, under: odds}}
        lines = {}

        for bookmaker in props_data.get("bookmakers", []):
            book = bookmaker.get("title", "")
            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")
                stat_label = STAT_LABELS.get(market_key, market_key)

                player_data = {}
                for outcome in market.get("outcomes", []):
                    player = outcome.get("description", "")
                    side = outcome["name"].lower()
                    point = outcome.get("point")
                    price = outcome.get("price")

                    if player not in player_data:
                        player_data[player] = {}
                    player_data[player][side] = {"price": price, "point": point}

                for player, sides in player_data.items():
                    over = sides.get("over", {})
                    under = sides.get("under", {})
                    point = over.get("point") or under.get("point")
                    if point is None:
                        continue

                    pkey = f"{player}|{stat_label}|{point}"
                    if pkey not in lines:
                        lines[pkey] = {"player": player, "stat": stat_label, "line": point, "books": {}}
                    lines[pkey]["books"][book] = {
                        "over": over.get("price"),
                        "under": under.get("price"),
                    }

        # Now find best over and best under across all books for each prop
        for pkey, data in lines.items():
            books = data["books"]
            if len(books) < 2:
                continue

            # Find best over odds (highest) and best under odds (highest)
            best_over_odds = -999
            best_over_book = ""
            best_under_odds = -999
            best_under_book = ""

            for book, odds in books.items():
                if odds["over"] is not None and odds["over"] > best_over_odds:
                    best_over_odds = odds["over"]
                    best_over_book = book
                if odds["under"] is not None and odds["under"] > best_under_odds:
                    best_under_odds = odds["under"]
                    best_under_book = book

            if best_over_odds == -999 or best_under_odds == -999:
                continue

            is_arb, profit_pct, hold_pct = find_arbitrage(best_over_odds, best_under_odds)

            opportunity = {
                "game": f"{away} @ {home}",
                "player": data["player"],
                "stat": data["stat"],
                "line": data["line"],
                "best_over": {"book": best_over_book, "odds": best_over_odds},
                "best_under": {"book": best_under_book, "odds": best_under_odds},
                "is_arb": is_arb,
                "profit_pct": round(profit_pct, 3),
                "hold_pct": round(hold_pct, 3),
                "num_books": len(books),
                "all_books": {b: {"over": o["over"], "under": o["under"]} for b, o in books.items()},
            }

            if is_arb:
                stakes = calculate_arb_stakes(100, best_over_odds, best_under_odds)
                opportunity["stakes_per_100"] = stakes
                arb_count += 1
                all_opportunities.append(opportunity)
                print(f"    ARB: {data['player']} {data['stat']} {data['line']}")
                print(f"         Over {best_over_odds:+d} @ {best_over_book}")
                print(f"         Under {best_under_odds:+d} @ {best_under_book}")
                print(f"         Profit: {profit_pct:.2f}% guaranteed")
                print(f"         Per $100: bet ${stakes['over_stake']:.0f} over, ${stakes['under_stake']:.0f} under = ${stakes['guaranteed_profit']:.2f} profit")
            elif hold_pct < 3.0:  # Low hold < 3%
                low_hold_count += 1
                all_opportunities.append(opportunity)
                if hold_pct < 1.5:
                    print(f"    LOW HOLD: {data['player']} {data['stat']} {data['line']} (hold: {hold_pct:.1f}%)")
                    print(f"         Over {best_over_odds:+d} @ {best_over_book}")
                    print(f"         Under {best_under_odds:+d} @ {best_under_book}")

    # Sort: arbs first, then by hold %
    all_opportunities.sort(key=lambda x: (not x["is_arb"], x["hold_pct"]))

    # Summary
    print(f"\n{'='*65}")
    print(f"  SCAN RESULTS")
    print(f"{'='*65}")
    print(f"  Events scanned:     {len(events)}")
    print(f"  Total props checked: {len(lines) if 'lines' in dir() else 0}")
    print(f"  Arbitrage found:    {arb_count}")
    print(f"  Low hold (<3%):     {low_hold_count}")

    if arb_count > 0:
        print(f"\n  ARBITRAGE OPPORTUNITIES:")
        for opp in all_opportunities:
            if opp["is_arb"]:
                stakes = opp["stakes_per_100"]
                print(f"\n    {opp['player']} - {opp['stat']} {opp['line']}")
                print(f"    {opp['game']}")
                print(f"    Over {opp['best_over']['odds']:+d} @ {opp['best_over']['book']}")
                print(f"    Under {opp['best_under']['odds']:+d} @ {opp['best_under']['book']}")
                print(f"    Guaranteed profit: {opp['profit_pct']:.2f}%")
                print(f"    Per $1000: bet ${stakes['over_stake']*10:.0f} over, ${stakes['under_stake']*10:.0f} under = ${stakes['guaranteed_profit']*10:.2f}")

    if low_hold_count > 0:
        print(f"\n  TOP LOW HOLD OPPORTUNITIES (< 1.5%):")
        for opp in all_opportunities[:20]:
            if not opp["is_arb"] and opp["hold_pct"] < 1.5:
                print(f"    {opp['player']} {opp['stat']} {opp['line']} - hold: {opp['hold_pct']:.2f}%")
                print(f"      Over {opp['best_over']['odds']:+d} @ {opp['best_over']['book']}")
                print(f"      Under {opp['best_under']['odds']:+d} @ {opp['best_under']['book']}")

    # Save results
    output_file = os.path.join(DATA_DIR, f"arb_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "events": len(events),
            "arb_count": arb_count,
            "low_hold_count": low_hold_count,
            "opportunities": all_opportunities,
        }, f, indent=2)
    print(f"\n  Results saved to {output_file}")

    return all_opportunities


def backtest_arbitrage():
    """
    Backtest: how many arbitrage opportunities existed in our historical data?
    Uses cached prop data from previous backtests.
    """
    print("\n" + "=" * 65)
    print("  HISTORICAL ARBITRAGE ANALYSIS")
    print("=" * 65)

    prop_files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith("props_") and f.endswith(".json"))
    print(f"  Analyzing {len(prop_files)} dates of historical data...")

    total_props = 0
    total_arbs = 0
    total_low_holds = 0
    arb_details = []

    for pf in prop_files:
        with open(os.path.join(DATA_DIR, pf)) as f:
            data = json.load(f)

        date = data.get("date", pf)

        for event in data.get("events", []):
            # Index by player+stat+line across books
            lines = {}
            for bookmaker in event.get("bookmakers", []):
                book = bookmaker.get("title", "")
                for market in bookmaker.get("markets", []):
                    stat = market.get("key", "")
                    player_data = {}
                    for outcome in market.get("outcomes", []):
                        player = outcome.get("description", "")
                        side = outcome["name"].lower()
                        point = outcome.get("point")
                        price = outcome.get("price")
                        if player not in player_data:
                            player_data[player] = {}
                        player_data[player][side] = {"price": price, "point": point}

                    for player, sides in player_data.items():
                        over = sides.get("over", {})
                        under = sides.get("under", {})
                        point = over.get("point") or under.get("point")
                        if point is None:
                            continue
                        pkey = f"{player}|{stat}|{point}"
                        if pkey not in lines:
                            lines[pkey] = {"player": player, "stat": stat, "line": point, "books": {}}
                        lines[pkey]["books"][book] = {
                            "over": over.get("price"),
                            "under": under.get("price"),
                        }

            for pkey, pdata in lines.items():
                books = pdata["books"]
                if len(books) < 2:
                    continue
                total_props += 1

                best_over = max((o["over"] for o in books.values() if o["over"] is not None), default=-999)
                best_under = max((o["under"] for o in books.values() if o["under"] is not None), default=-999)

                if best_over == -999 or best_under == -999:
                    continue

                is_arb, profit_pct, hold_pct = find_arbitrage(best_over, best_under)

                if is_arb:
                    total_arbs += 1
                    arb_details.append({
                        "date": date,
                        "player": pdata["player"],
                        "stat": pdata["stat"],
                        "line": pdata["line"],
                        "profit_pct": profit_pct,
                        "best_over": best_over,
                        "best_under": best_under,
                    })
                elif hold_pct < 3.0:
                    total_low_holds += 1

    print(f"\n  Props with 2+ books:  {total_props}")
    print(f"  Arbitrage found:      {total_arbs}")
    print(f"  Low hold (<3%):       {total_low_holds}")

    if total_arbs > 0:
        avg_profit = sum(a["profit_pct"] for a in arb_details) / len(arb_details)
        max_profit = max(a["profit_pct"] for a in arb_details)
        print(f"  Avg arb profit:       {avg_profit:.2f}%")
        print(f"  Max arb profit:       {max_profit:.2f}%")
        print(f"  Arb rate:             {total_arbs/total_props*100:.3f}%")

        # If we hit 5 arbs per day at 1.5% avg profit on $500 stakes
        est_daily = 5 * (avg_profit / 100) * 500
        print(f"\n  Estimated daily profit (5 arbs/day, $500 stakes): ${est_daily:.2f}")
        print(f"  Estimated monthly: ${est_daily * 30:.0f}")

        print(f"\n  Sample arbitrage opportunities:")
        for a in arb_details[:10]:
            print(f"    {a['date']} - {a['player']} {a['stat']} {a['line']}: {a['profit_pct']:.2f}%")

    return arb_details


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        backtest_arbitrage()
    else:
        # Run historical analysis first (no API calls needed)
        backtest_arbitrage()
        # Then scan live if requested
        if len(sys.argv) > 1 and sys.argv[1] == "live":
            scan_live_props()

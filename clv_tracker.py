#!/usr/bin/env python3
"""
Sports Edge - Closing Line Value (CLV) Tracker (Level 2)

CLV = the difference between our bet price and the closing price.
This is the GOLD STANDARD metric for +EV betting.

If you consistently beat closing lines, you have real edge --
even if short-term results are negative due to variance.

How it works:
1. Reads bets from paper_ledger.json (Level 2 engine output)
2. Finds Pinnacle's last recorded line for that game/side in game_lines.db
3. Calculates CLV = closing implied prob - our implied prob
4. Positive CLV = we got a better price than the market's final assessment

Usage:
    python3 clv_tracker.py          # Check CLV for all unchecked bets
    python3 clv_tracker.py summary  # Show CLV summary stats
    python3 clv_tracker.py refresh  # Force re-check all bets (even previously checked)
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LEDGER_PATH = os.path.join(DATA_DIR, "paper_ledger.json")
LINES_DB = os.path.join(DATA_DIR, "game_lines.db")

# Team abbreviation -> possible full name fragments for fuzzy matching
NHL_ABBREVS = {
    "ANA": ["Anaheim", "Ducks"],
    "ARI": ["Arizona", "Coyotes"],
    "BOS": ["Boston", "Bruins"],
    "BUF": ["Buffalo", "Sabres"],
    "CAR": ["Carolina", "Hurricanes"],
    "CBJ": ["Columbus", "Blue Jackets"],
    "CGY": ["Calgary", "Flames"],
    "CHI": ["Chicago", "Blackhawks"],
    "COL": ["Colorado", "Avalanche"],
    "DAL": ["Dallas", "Stars"],
    "DET": ["Detroit", "Red Wings"],
    "EDM": ["Edmonton", "Oilers"],
    "FLA": ["Florida", "Panthers"],
    "LAK": ["Los Angeles", "Kings"],
    "MIN": ["Minnesota", "Wild"],
    "MTL": ["Montreal", "Canadiens"],
    "NJD": ["New Jersey", "Devils"],
    "NSH": ["Nashville", "Predators"],
    "NYI": ["N.Y. Islanders", "Islanders"],
    "NYR": ["N.Y. Rangers", "Rangers"],
    "OTT": ["Ottawa", "Senators"],
    "PHI": ["Philadelphia", "Flyers"],
    "PIT": ["Pittsburgh", "Penguins"],
    "SEA": ["Seattle", "Kraken"],
    "SJS": ["San Jose", "Sharks"],
    "STL": ["St. Louis", "Blues"],
    "TBL": ["Tampa Bay", "Lightning"],
    "TOR": ["Toronto", "Maple Leafs"],
    "UTA": ["Utah", "Mammoth"],
    "VAN": ["Vancouver", "Canucks"],
    "VGK": ["Vegas", "Golden Knights"],
    "WPG": ["Winnipeg", "Jets"],
    "WSH": ["Washington", "Capitals"],
}

MLB_ABBREVS = {
    "ARI": ["Arizona", "Diamondbacks"],
    "ATL": ["Atlanta", "Braves"],
    "BAL": ["Baltimore", "Orioles"],
    "BOS": ["Boston", "Red Sox"],
    "CHC": ["Chicago Cubs", "Cubs"],
    "CHW": ["Chicago White Sox", "White Sox"],
    "CIN": ["Cincinnati", "Reds"],
    "CLE": ["Cleveland", "Guardians"],
    "COL": ["Colorado", "Rockies"],
    "DET": ["Detroit", "Tigers"],
    "HOU": ["Houston", "Astros"],
    "KC": ["Kansas City", "Royals"],
    "LAA": ["Los Angeles Angels", "Angels"],
    "LAD": ["Los Angeles Dodgers", "Dodgers"],
    "MIA": ["Miami", "Marlins"],
    "MIL": ["Milwaukee", "Brewers"],
    "MIN": ["Minnesota", "Twins"],
    "NYM": ["New York Mets", "Mets"],
    "NYY": ["New York Yankees", "Yankees"],
    "OAK": ["Oakland", "Athletics"],
    "PHI": ["Philadelphia", "Phillies"],
    "PIT": ["Pittsburgh", "Pirates"],
    "SD": ["San Diego", "Padres"],
    "SF": ["San Francisco", "Giants"],
    "SEA": ["Seattle", "Mariners"],
    "STL": ["St. Louis", "Cardinals"],
    "TB": ["Tampa Bay", "Rays"],
    "TEX": ["Texas", "Rangers"],
    "TOR": ["Toronto", "Blue Jays"],
    "WSH": ["Washington", "Nationals"],
}


def american_to_decimal(american):
    """Convert American odds to decimal odds."""
    if isinstance(american, str):
        if american.upper() in ("EVEN", "EV"):
            return 2.0
        american = int(american.replace("+", ""))
    american = int(american)
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    """Convert decimal odds to implied probability."""
    return 1.0 / dec if dec > 0 else 0


def _team_matches(abbrev, full_name, sport):
    """Check if a team abbreviation matches a full team name."""
    abbrev = abbrev.strip().upper()
    full_name = full_name.strip()

    lookup = NHL_ABBREVS if sport == "NHL" else MLB_ABBREVS
    fragments = lookup.get(abbrev, [])

    full_lower = full_name.lower()
    for frag in fragments:
        if frag.lower() in full_lower:
            return True

    # Fallback: abbrev might be in the full name somehow
    if abbrev.lower() in full_lower:
        return True

    return False


def _find_closing_line(conn, bet, sport):
    """
    Find Pinnacle's closing line for a bet.

    Returns (closing_odds, closing_timestamp) or (None, None).

    Strategy: Find the latest Pinnacle snapshot for this game where
    sport, side (over/under), and line match.
    """
    game = bet.get("game", "")  # e.g. "MTL @ PHI"
    side = bet.get("side", "").lower()  # "OVER" or "UNDER"
    line = bet.get("line")

    if " @ " not in game:
        return None, None

    away_abbrev, home_abbrev = game.split(" @ ", 1)

    # Search game_odds for matching Pinnacle lines
    # We need to match by team names (fuzzy) + side + market=total
    rows = conn.execute("""
        SELECT game, home, away, odds, line, timestamp, side
        FROM game_odds
        WHERE sport = ? AND market = 'total' AND book = 'pinnacle'
        AND LOWER(side) = ?
        ORDER BY timestamp DESC
    """, (sport, side)).fetchall()

    for row in rows:
        db_game, db_home, db_away, db_odds, db_line, db_ts, db_side = row

        # Check if teams match
        home_match = _team_matches(home_abbrev, db_home, sport) if db_home else False
        away_match = _team_matches(away_abbrev, db_away, sport) if db_away else False

        # Also try matching against the game string itself
        if not (home_match and away_match):
            game_str = db_game or ""
            home_match = home_match or _team_matches(home_abbrev, game_str, sport)
            away_match = away_match or _team_matches(away_abbrev, game_str, sport)

        if home_match and away_match:
            return db_odds, db_ts

    return None, None


def _find_market_consensus(conn, bet, sport):
    """
    Fallback: if no Pinnacle line, use the average across all books
    as a proxy for closing line.
    """
    game = bet.get("game", "")
    side = bet.get("side", "").lower()

    if " @ " not in game:
        return None, None

    away_abbrev, home_abbrev = game.split(" @ ", 1)

    rows = conn.execute("""
        SELECT home, away, odds, game, timestamp
        FROM game_odds
        WHERE sport = ? AND market = 'total' AND LOWER(side) = ?
        ORDER BY timestamp DESC
        LIMIT 200
    """, (sport, side)).fetchall()

    matching_odds = []
    latest_ts = None
    for db_home, db_away, db_odds, db_game, db_ts in rows:
        game_str = db_game or ""
        home_match = _team_matches(home_abbrev, db_home or "", sport) or _team_matches(home_abbrev, game_str, sport)
        away_match = _team_matches(away_abbrev, db_away or "", sport) or _team_matches(away_abbrev, game_str, sport)

        if home_match and away_match:
            matching_odds.append(db_odds)
            if latest_ts is None:
                latest_ts = db_ts
            if len(matching_odds) >= 10:
                break

    if matching_odds:
        avg_odds = sum(matching_odds) / len(matching_odds)
        return round(avg_odds), latest_ts

    return None, None


def check_clv(force_recheck=False):
    """
    Check CLV for all bets in paper_ledger.json.

    CLV = closing_implied_prob - our_implied_prob
    Positive = we got better odds than closing (GOOD)
    Negative = market moved against us (BAD)
    """
    if not os.path.exists(LEDGER_PATH):
        print("No paper ledger found.")
        return

    with open(LEDGER_PATH) as f:
        ledger = json.load(f)

    bets = ledger.get("bets", [])
    if not bets:
        print("No bets in ledger.")
        return

    if not os.path.exists(LINES_DB):
        print(f"No game_lines.db found at {LINES_DB}")
        return

    conn = sqlite3.connect(LINES_DB)

    checked = 0
    skipped = 0
    failed = 0
    total_clv = 0.0
    clv_results = []

    for bet in bets:
        # Skip already checked unless force
        if bet.get("clv") is not None and not force_recheck:
            # Already has CLV data
            if bet["clv"] != 0 or bet.get("closing_odds") is not None:
                clv_results.append(bet)
                total_clv += bet.get("clv", 0)
                checked += 1
                continue

        sport = bet.get("sport", "NHL")
        our_odds = bet.get("odds")

        if our_odds is None or our_odds == 0:
            skipped += 1
            continue

        # Find Pinnacle closing line
        closing_odds, closing_ts = _find_closing_line(conn, bet, sport)

        # Fallback to market consensus
        if closing_odds is None:
            closing_odds, closing_ts = _find_market_consensus(conn, bet, sport)

        if closing_odds is None:
            failed += 1
            continue

        # Calculate CLV
        try:
            our_dec = american_to_decimal(our_odds)
            our_imp = decimal_to_implied(our_dec)

            close_dec = american_to_decimal(closing_odds)
            close_imp = decimal_to_implied(close_dec)

            # For OVER/UNDER bets:
            # If we bet UNDER at -110 (imp=52.38%) and closing is -120 (imp=54.55%)
            # CLV = 54.55% - 52.38% = +2.17% (we got better odds - GOOD)
            clv = close_imp - our_imp

            bet["closing_odds"] = closing_odds
            bet["clv"] = round(clv, 4)
            bet["clv_checked_at"] = datetime.now(timezone.utc).isoformat()

            total_clv += clv
            checked += 1
            clv_results.append(bet)

        except Exception as e:
            failed += 1
            continue

    conn.close()

    # Update ledger with CLV data
    ledger["summary"]["clv_checks"] = checked
    if clv_results:
        ledger["summary"]["clv_sum"] = round(total_clv, 4)
        ledger["summary"]["clv_positive"] = sum(1 for b in clv_results if b.get("clv", 0) > 0)

    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)

    # Report
    print(f"\n  CLV CHECK RESULTS")
    print(f"  {'='*50}")
    print(f"  Checked: {checked} | Skipped: {skipped} | No line found: {failed}")

    if clv_results:
        avg_clv = total_clv / len(clv_results)
        pos_clv = sum(1 for b in clv_results if b.get("clv", 0) > 0)

        print(f"\n  Average CLV: {avg_clv*100:+.2f}%")
        print(f"  Positive CLV: {pos_clv}/{len(clv_results)} ({pos_clv/len(clv_results)*100:.0f}%)")

        if avg_clv > 0:
            print(f"  VERDICT: BEATING CLOSING LINES (edge likely real)")
        elif avg_clv > -0.01:
            print(f"  VERDICT: ROUGHLY BREAK-EVEN WITH MARKET (need more data)")
        else:
            print(f"  VERDICT: LOSING TO CLOSING LINES (model may not have real edge)")

        print(f"\n  Per-bet breakdown:")
        for b in clv_results:
            clv_val = b.get("clv", 0)
            tag = "+" if clv_val > 0 else ""
            side = b.get("side", "?")
            game = b.get("game", "?")
            our = b.get("odds", "?")
            close = b.get("closing_odds", "?")
            result = b.get("result", "pending")

            our_imp = decimal_to_implied(american_to_decimal(our)) if our else 0
            close_imp = decimal_to_implied(american_to_decimal(close)) if close else 0

            status = "WIN" if result == "win" else "LOSS" if result == "loss" else "PEND"
            clv_status = "GOOD" if clv_val > 0 else "BAD"

            print(f"    [{status}] [{clv_status}] {game} {side} {b.get('line','')} | "
                  f"Our: {our} ({our_imp:.1%}) | Close: {close} ({close_imp:.1%}) | "
                  f"CLV: {tag}{clv_val*100:.2f}%")
    else:
        print("  No CLV data available yet.")


def show_summary():
    """Show CLV tracking summary."""
    if not os.path.exists(LEDGER_PATH):
        print("No paper ledger found.")
        return

    with open(LEDGER_PATH) as f:
        ledger = json.load(f)

    bets = ledger.get("bets", [])
    clv_bets = [b for b in bets if b.get("clv") is not None and b.get("closing_odds") is not None]
    unchecked = len(bets) - len(clv_bets)

    print(f"\n  CLV TRACKING SUMMARY")
    print(f"  {'='*50}")
    print(f"  Total bets: {len(bets)}")
    print(f"  CLV tracked: {len(clv_bets)}")
    print(f"  Awaiting CLV: {unchecked}")

    if clv_bets:
        clvs = [b.get("clv", 0) for b in clv_bets]
        avg = sum(clvs) / len(clvs)
        pos = sum(1 for c in clvs if c > 0)

        print(f"\n  Average CLV: {avg*100:+.2f}%")
        print(f"  Positive CLV rate: {pos}/{len(clv_bets)} ({pos/len(clv_bets)*100:.0f}%)")

        # Split by sport
        by_sport = {}
        for b in clv_bets:
            sport = b.get("sport", "?")
            by_sport.setdefault(sport, []).append(b.get("clv", 0))

        for sport, vals in sorted(by_sport.items()):
            sport_avg = sum(vals) / len(vals)
            sport_pos = sum(1 for v in vals if v > 0)
            print(f"\n  {sport}: avg CLV {sport_avg*100:+.2f}%, positive {sport_pos}/{len(vals)}")

        # Split by tier
        by_tier = {}
        for b in clv_bets:
            tier = b.get("tier", "?")
            by_tier.setdefault(tier, []).append(b.get("clv", 0))

        for tier, vals in sorted(by_tier.items()):
            tier_avg = sum(vals) / len(vals)
            print(f"  Tier {tier}: avg CLV {tier_avg*100:+.2f}% (n={len(vals)})")

        verdict = "EDGE CONFIRMED" if avg > 0.005 else "PROMISING" if avg > 0 else "NO EDGE YET"
        print(f"\n  VERDICT: {verdict}")

        if len(clv_bets) < 50:
            print(f"  NOTE: {len(clv_bets)} bets is too small for conclusions. Need 200+.")
    else:
        print("  No CLV data yet. Run: python3 clv_tracker.py")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            show_summary()
        elif sys.argv[1] == "refresh":
            check_clv(force_recheck=True)
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python3 clv_tracker.py [summary|refresh]")
    else:
        check_clv()

#!/usr/bin/env python3
"""
Sports Edge - Multi-Book Odds Comparison

Scrapes NHL and MLB totals odds from SportsBookReview to compare
across sportsbooks. Tracks how retail book odds compare to Pinnacle
and identifies where our edge is biggest.

Used to:
1. Find best available odds for our picks
2. Track Hard Rock / retail vs Pinnacle vig over time
3. Confirm edge survives at the book where we'll actually bet
"""

import json
import os
import re
import requests
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COMPARISON_DIR = os.path.join(DATA_DIR, "odds_comparison")
os.makedirs(COMPARISON_DIR, exist_ok=True)

# SBR sportsbook mapping (books shown on their totals page)
RETAIL_BOOKS = ["BetMGM", "FanDuel", "Caesars", "bet365", "DraftKings", "Fanatics"]
SHARP_BOOKS = ["Pinnacle"]


def american_to_implied(odds):
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def implied_to_american(prob):
    """Convert implied probability to American odds."""
    if prob >= 0.5:
        return int(-prob / (1 - prob) * 100)
    else:
        return int((1 - prob) / prob * 100)


def fetch_sbr_odds(sport="nhl"):
    """Fetch current totals odds from SportsBookReview."""
    try:
        from urllib.request import Request, urlopen
        url = f"https://www.sportsbookreview.com/betting-odds/{sport}-hockey/totals/" if sport == "nhl" else \
              f"https://www.sportsbookreview.com/betting-odds/mlb-baseball/totals/"

        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return html
    except Exception as e:
        print(f"  Error fetching SBR odds: {e}")
        return None


def parse_odds_from_webfetch(text):
    """Parse odds data from a structured text format (WebFetch output)."""
    games = []
    current_game = None

    for line in text.strip().split("\n"):
        line = line.strip()

        # Match game header like "## Dallas vs Buffalo (7:00 PM ET)"
        game_match = re.match(r"##?\s+(.+?)\s+vs\s+(.+?)\s+\(", line)
        if game_match:
            if current_game:
                games.append(current_game)
            current_game = {
                "away": game_match.group(1).strip(),
                "home": game_match.group(2).strip(),
                "books": {}
            }
            continue

        # Match table row like "| BetMGM | 6.5 | +100 | -120 |"
        row_match = re.match(r"\|\s*(\w[\w\d]*)\s*\|\s*([\d.]+)\s*\|\s*([+-]\d+)\s*\|\s*([+-]\d+)\s*\|", line)
        if row_match and current_game:
            book = row_match.group(1)
            total = float(row_match.group(2))
            over_odds = int(row_match.group(3))
            under_odds = int(row_match.group(4))
            current_game["books"][book] = {
                "total": total,
                "over": over_odds,
                "under": under_odds,
                "over_implied": round(american_to_implied(over_odds), 4),
                "under_implied": round(american_to_implied(under_odds), 4),
            }

    if current_game:
        games.append(current_game)

    return games


def compare_to_picks(games, picks_path=None):
    """Compare scraped odds to our model picks. Find best odds for each pick."""
    if picks_path is None:
        picks_path = os.path.join(DATA_DIR, "unified_picks", "latest.json")

    if not os.path.exists(picks_path):
        print("  No picks file found")
        return []

    with open(picks_path) as f:
        picks_data = json.load(f)

    picks = picks_data.get("picks", [])
    comparisons = []

    # NHL/MLB abbreviation to city/name mapping for matching
    ABBREV_MAP = {
        "ANA": "ANAHEIM", "ARI": "ARIZONA", "BOS": "BOSTON", "BUF": "BUFFALO",
        "CGY": "CALGARY", "CAR": "CAROLINA", "CHI": "CHICAGO", "COL": "COLORADO",
        "CBJ": "COLUMBUS", "DAL": "DALLAS", "DET": "DETROIT", "EDM": "EDMONTON",
        "FLA": "FLORIDA", "LAK": "LOS ANGELES", "MIN": "MINNESOTA", "MTL": "MONTREAL",
        "NSH": "NASHVILLE", "NJD": "NEW JERSEY", "NYI": "NY ISLANDERS", "NYR": "NY RANGERS",
        "OTT": "OTTAWA", "PHI": "PHILADELPHIA", "PIT": "PITTSBURGH", "SJS": "SAN JOSE",
        "SEA": "SEATTLE", "STL": "ST. LOUIS", "TBL": "TAMPA BAY", "TOR": "TORONTO",
        "UTA": "UTAH", "VAN": "VANCOUVER", "VGK": "VEGAS", "WSH": "WASHINGTON",
        "WPG": "WINNIPEG",
        # MLB
        "KC": "KANSAS CITY", "CWS": "WHITE SOX", "LAA": "ANGELS", "LAD": "DODGERS",
        "NYM": "METS", "NYY": "YANKEES", "OAK": "ATHLETICS", "SD": "SAN DIEGO",
        "SF": "SAN FRANCISCO", "TB": "TAMPA BAY", "TEX": "TEXAS", "MIA": "MIAMI",
        "ATL": "ATLANTA", "BAL": "BALTIMORE", "CIN": "CINCINNATI", "CLE": "CLEVELAND",
        "HOU": "HOUSTON", "MIL": "MILWAUKEE",
    }

    for pick in picks:
        game_name = pick.get("game", "")
        side = pick.get("side", "").upper()
        our_line = pick.get("market_line", 0) or pick.get("line", 0)
        our_odds = pick.get("odds", -110)
        our_edge = pick.get("edge", 0)
        model_prob = pick.get("our_prob", 0) or pick.get("model_prob", 0) or pick.get("fair_prob", 0)

        # Expand abbreviations in our game name (e.g. "DAL @ BUF" -> "DALLAS @ BUFFALO")
        game_expanded = game_name.upper()
        for abbrev, full in ABBREV_MAP.items():
            game_expanded = game_expanded.replace(abbrev, full)

        # Find matching game in scraped data
        matched_game = None
        for g in games:
            away_up = g["away"].upper()
            home_up = g["home"].upper()
            # Check if both team names appear in our expanded game string
            away_words = [w for w in away_up.split() if len(w) > 2]
            home_words = [w for w in home_up.split() if len(w) > 2]
            away_match = any(w in game_expanded for w in away_words)
            home_match = any(w in game_expanded for w in home_words)
            if away_match and home_match:
                matched_game = g
                break

        if not matched_game:
            continue

        # Find best odds for our side across all books
        best_book = None
        best_odds = None
        best_implied = 1.0

        book_comparison = []
        for book, data in matched_game["books"].items():
            book_line = data["total"]
            if side == "OVER":
                book_odds = data["over"]
                book_implied = data["over_implied"]
            else:
                book_odds = data["under"]
                book_implied = data["under_implied"]

            # Only compare same line or better
            if side == "UNDER" and book_line <= our_line:
                edge_at_book = model_prob - book_implied if model_prob else our_edge
                book_comparison.append({
                    "book": book,
                    "line": book_line,
                    "odds": book_odds,
                    "implied": round(book_implied, 4),
                    "edge": round(edge_at_book, 4),
                })
                if book_implied < best_implied:
                    best_implied = book_implied
                    best_odds = book_odds
                    best_book = book
            elif side == "OVER" and book_line >= our_line:
                edge_at_book = model_prob - book_implied if model_prob else our_edge
                book_comparison.append({
                    "book": book,
                    "line": book_line,
                    "odds": book_odds,
                    "implied": round(book_implied, 4),
                    "edge": round(edge_at_book, 4),
                })
                if book_implied < best_implied:
                    best_implied = book_implied
                    best_odds = book_odds
                    best_book = book

        if book_comparison:
            comparisons.append({
                "game": game_name,
                "side": side,
                "our_line": our_line,
                "our_odds": our_odds,
                "model_prob": model_prob,
                "our_edge": our_edge,
                "best_book": best_book,
                "best_odds": best_odds,
                "best_edge": round(model_prob - best_implied, 4) if model_prob else None,
                "books": sorted(book_comparison, key=lambda x: -x["edge"]),
            })

    return comparisons


def print_comparison(comparisons):
    """Pretty-print the odds comparison."""
    if not comparisons:
        print("  No matching games found between picks and scraped odds")
        return

    print(f"\n{'='*70}")
    print(f"  ODDS COMPARISON - MODEL PICKS vs RETAIL BOOKS")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*70}")

    for comp in comparisons:
        print(f"\n  {comp['game']} - {comp['side']} {comp['our_line']}")
        print(f"  Model probability: {comp['model_prob']*100:.1f}%" if comp['model_prob'] else "")
        print(f"  Our pick odds: {comp['our_odds']} (edge: {comp['our_edge']*100:.1f}%)")
        print(f"  Best available: {comp['best_book']} at {comp['best_odds']} (edge: {comp['best_edge']*100:.1f}%)" if comp['best_edge'] else "")
        print(f"  {'Book':<15} {'Line':<6} {'Odds':<8} {'Implied':<10} {'Edge':<8}")
        print(f"  {'-'*50}")
        for b in comp["books"]:
            edge_str = f"{b['edge']*100:+.1f}%" if b['edge'] else "?"
            print(f"  {b['book']:<15} {b['line']:<6} {b['odds']:<+8} {b['implied']*100:<10.1f}% {edge_str:<8}")

    print(f"\n{'='*70}")


def save_comparison(comparisons):
    """Save comparison data for historical tracking."""
    now = datetime.now(timezone.utc)
    path = os.path.join(COMPARISON_DIR, f"compare_{now.strftime('%Y%m%d_%H%M')}.json")
    with open(path, "w") as f:
        json.dump({
            "timestamp": now.isoformat(),
            "comparisons": comparisons,
        }, f, indent=2)
    print(f"  Saved to {path}")


def run_comparison(odds_text=None):
    """Run full comparison pipeline. If odds_text provided, parse that instead of scraping."""
    if odds_text:
        games = parse_odds_from_webfetch(odds_text)
    else:
        print("  Provide odds_text from WebFetch (SBR scraping requires browser)")
        return []

    print(f"  Parsed {len(games)} games with odds")
    comparisons = compare_to_picks(games)
    print_comparison(comparisons)
    save_comparison(comparisons)
    return comparisons


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1]) as f:
            text = f.read()
        run_comparison(text)
    else:
        print("Usage: python3 odds_comparison.py <odds_text_file>")
        print("  Or import and call run_comparison(odds_text)")

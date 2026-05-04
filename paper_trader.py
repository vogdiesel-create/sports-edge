#!/usr/bin/env python3
"""
Sports Edge - Paper Trading System

Logs every pick with timestamp, tracks results automatically,
builds the statistical proof needed before real money.

Target: 200+ graded bets with positive CLV and ROI.

Runs after each scanner cycle:
1. Log all new picks with exact odds/timestamp
2. Grade completed games from previous picks
3. Check CLV on picks where closing lines are available
4. Generate daily P&L report
"""

import json
import os
import time
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LEDGER_PATH = os.path.join(DATA_DIR, "paper_ledger.json")
DAILY_PATH = os.path.join(DATA_DIR, "daily_reports")
os.makedirs(DAILY_PATH, exist_ok=True)

BANKROLL = 5000  # Paper bankroll


def load_ledger():
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH) as f:
            return json.load(f)
    return {
        "bankroll": BANKROLL,
        "started": datetime.now(timezone.utc).isoformat(),
        "bets": [],
        "summary": {
            "total_bets": 0,
            "graded": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "total_wagered": 0,
            "total_pnl": 0,
            "clv_checks": 0,
            "clv_sum": 0,
            "clv_positive": 0,
        }
    }


def save_ledger(ledger):
    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)


def log_picks():
    """Log new picks from the latest scanner output."""
    ledger = load_ledger()
    scan_path = os.path.join(DATA_DIR, "game_line_scan.json")

    if not os.path.exists(scan_path):
        print("  No scan data found")
        return

    with open(scan_path) as f:
        scan = json.load(f)

    opportunities = scan.get("opportunities", [])
    existing_ids = {b["pick_id"] for b in ledger["bets"]}
    new_count = 0
    now = datetime.now(timezone.utc)

    for opp in opportunities:
        edge = opp.get("edge", 0)
        book = opp.get("book", "")

        # Apply our proven filters: 3-6% edge, exclude bodog
        if edge < 0.03 or edge > 0.06:
            continue
        if book in ("bodog",):
            continue

        # Create unique ID
        pick_id = f"{opp.get('sport','')}|{opp.get('game','')}|{opp.get('market','')}|{opp.get('side','')}|{opp.get('line','')}|{book}"

        if pick_id in existing_ids:
            continue

        # Kelly sizing
        kelly_pct = opp.get("kelly_pct", 1.5)
        wager = round(ledger["bankroll"] * min(kelly_pct, 3.0) / 100, 2)

        # Determine American odds
        odds = opp.get("odds", 0)
        if isinstance(odds, (int, float)):
            if odds > 0:
                profit_if_win = wager * odds / 100
            else:
                profit_if_win = wager * 100 / abs(odds)
        else:
            profit_if_win = wager  # Even money fallback

        bet = {
            "pick_id": pick_id,
            "date": now.strftime("%Y-%m-%d"),
            "logged_at": now.isoformat(),
            "sport": opp.get("sport", ""),
            "game": opp.get("game", ""),
            "market": opp.get("market", ""),
            "side": opp.get("side", ""),
            "line": opp.get("line", ""),
            "book": book,
            "odds": odds,
            "edge": round(edge, 4),
            "ev": opp.get("ev", 0),
            "fair_prob": opp.get("fair_prob", 0),
            "pinnacle_odds": opp.get("pinnacle_odds", ""),
            "kelly_pct": kelly_pct,
            "wager": wager,
            "profit_if_win": round(profit_if_win, 2),
            "result": None,  # win/loss/push
            "actual_total": None,
            "closing_odds": None,
            "clv": None,
            "graded_at": None,
        }

        ledger["bets"].append(bet)
        ledger["summary"]["total_bets"] += 1
        ledger["summary"]["total_wagered"] += wager
        existing_ids.add(pick_id)
        new_count += 1

    save_ledger(ledger)
    print(f"  Logged {new_count} new picks ({ledger['summary']['total_bets']} total)")


def _fetch_nhl_scores(dates: list) -> dict:
    """Fetch NHL final scores for given dates. Returns {date: {game_key: {total, home_score, away_score}}}."""
    import urllib.request
    scores_by_date = {}

    # NHL team name -> abbreviation mapping for matching
    NAME_TO_ABBREV = {
        "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
        "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
        "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
        "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
        "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
        "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
        "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
        "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
        "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
        "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Utah Mammoth": "UTA",
        "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH",
        "Winnipeg Jets": "WPG",
        "Los Angeles": "LAK", "N.Y. Rangers": "NYR", "N.Y. Islanders": "NYI",
        "New Jersey": "NJD", "Tampa Bay": "TBL", "St. Louis": "STL",
        "San Jose": "SJS", "Vegas": "VGK",
    }

    for date in dates:
        scores_by_date[date] = {}
        try:
            url = f"https://api-web.nhle.com/v1/schedule/{date}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            for day in data.get("gameWeek", []):
                if day.get("date") != date:
                    continue
                for g in day.get("games", []):
                    state = g.get("gameState", "")
                    if state not in ("OFF", "FINAL"):
                        continue
                    home_abbrev = g["homeTeam"]["abbrev"]
                    away_abbrev = g["awayTeam"]["abbrev"]
                    hs = g["homeTeam"].get("score", 0) or 0
                    a_s = g["awayTeam"].get("score", 0) or 0
                    total = hs + a_s
                    score_data = {"total": total, "home_score": hs, "away_score": a_s}

                    scores_by_date[date][f"{away_abbrev} @ {home_abbrev}"] = score_data
                    scores_by_date[date][f"{away_abbrev}@{home_abbrev}"] = score_data
        except Exception as e:
            print(f"    NHL scores fetch error for {date}: {e}")

    # Build reverse lookup: full names and partial names per date
    for date in scores_by_date:
        for name, abbrev in NAME_TO_ABBREV.items():
            for key, val in list(scores_by_date[date].items()):
                if abbrev in key:
                    scores_by_date[date][key.replace(abbrev, name)] = val

    return scores_by_date


def _fetch_mlb_scores(dates: list) -> dict:
    """Fetch MLB final scores for given dates. Returns {date: {game_key: score_data}}."""
    scores_by_date = {}
    for date in dates:
        scores_by_date[date] = {}
        try:
            resp = requests.get(
                f"https://statsapi.mlb.com/api/v1/schedule?date={date}&sportId=1",
                timeout=10
            )
            data = resp.json()
            for d in data.get("dates", []):
                for g in d.get("games", []):
                    status = g.get("status", {}).get("detailedState", "")
                    if status not in ("Final", "Game Over", "Completed Early"):
                        continue
                    away = g.get("teams", {}).get("away", {}).get("team", {}).get("name", "")
                    home = g.get("teams", {}).get("home", {}).get("team", {}).get("name", "")
                    a_s = g.get("teams", {}).get("away", {}).get("score", 0) or 0
                    hs = g.get("teams", {}).get("home", {}).get("score", 0) or 0
                    total = a_s + hs
                    score_data = {"total": total, "home_score": hs, "away_score": a_s}
                    scores_by_date[date][f"{away} @ {home}"] = score_data
        except Exception as e:
            print(f"    MLB scores fetch error for {date}: {e}")
    return scores_by_date


MLB_ABBREV_TO_FULL = {
    "ARI": "ARIZONA DIAMONDBACKS", "ATL": "ATLANTA BRAVES", "BAL": "BALTIMORE ORIOLES",
    "BOS": "BOSTON RED SOX", "CHC": "CHICAGO CUBS", "CWS": "CHICAGO WHITE SOX",
    "CIN": "CINCINNATI REDS", "CLE": "CLEVELAND GUARDIANS", "COL": "COLORADO ROCKIES",
    "DET": "DETROIT TIGERS", "HOU": "HOUSTON ASTROS", "KC": "KANSAS CITY ROYALS",
    "LAA": "LOS ANGELES ANGELS", "LAD": "LOS ANGELES DODGERS", "MIA": "MIAMI MARLINS",
    "MIL": "MILWAUKEE BREWERS", "MIN": "MINNESOTA TWINS", "NYM": "NEW YORK METS",
    "NYY": "NEW YORK YANKEES", "OAK": "ATHLETICS", "PHI": "PHILADELPHIA PHILLIES",
    "PIT": "PITTSBURGH PIRATES", "SD": "SAN DIEGO PADRES", "SF": "SAN FRANCISCO GIANTS",
    "SEA": "SEATTLE MARINERS", "STL": "ST. LOUIS CARDINALS", "TB": "TAMPA BAY RAYS",
    "TEX": "TEXAS RANGERS", "TOR": "TORONTO BLUE JAYS", "WSH": "WASHINGTON NATIONALS",
}

def _expand_abbrev(team_str: str) -> str:
    """Expand a team abbreviation to full name for matching."""
    return MLB_ABBREV_TO_FULL.get(team_str.upper(), team_str.upper())


def _match_game(bet_game: str, score_key: str) -> bool:
    """Fuzzy match a bet's game string to a score key."""
    bg = bet_game.strip().upper().replace("  ", " ")
    sk = score_key.strip().upper().replace("  ", " ")
    if bg == sk:
        return True
    # Expand abbreviations and try again
    bg_parts = [p.strip() for p in bg.replace("@", " @ ").split()]
    sk_parts = [p.strip() for p in sk.replace("@", " @ ").split()]
    bg_teams = [_expand_abbrev(p) for p in bg_parts if p != "@" and len(p) >= 2]
    sk_teams = [p for p in sk_parts if p != "@" and len(p) >= 2]
    # Check if expanded abbreviations match words in full team names
    matches = 0
    for bt in bg_teams:
        for st in sk_teams:
            if bt in st or st in bt:
                matches += 1
                break
    return matches >= 2


def grade_bets():
    """Grade completed bets against actual scores. Fetches scores for all relevant dates."""
    ledger = load_ledger()
    ungraded = [b for b in ledger["bets"] if b["result"] is None]

    if not ungraded:
        print("  No ungraded bets")
        return

    # Determine which dates to fetch scores for
    dates_needed = set()
    today = datetime.now(timezone.utc)
    for b in ungraded:
        logged = b.get("logged_at", "")
        if logged:
            bet_date = logged[:10]
            dates_needed.add(bet_date)
    # Also check today and yesterday
    dates_needed.add(today.strftime("%Y-%m-%d"))
    dates_needed.add((today - timedelta(days=1)).strftime("%Y-%m-%d"))
    dates_needed = sorted(dates_needed)

    print(f"  Fetching scores for {len(dates_needed)} dates: {', '.join(dates_needed)}")

    # Fetch all scores (now keyed by date)
    nhl_scores_by_date = _fetch_nhl_scores(dates_needed)
    mlb_scores_by_date = _fetch_mlb_scores(dates_needed)

    # Count totals for logging
    nhl_total = sum(len(v) for v in nhl_scores_by_date.values())
    mlb_total = sum(len(v) for v in mlb_scores_by_date.values())
    print(f"  Found {nhl_total} NHL finals, {mlb_total} MLB finals")

    graded_count = 0
    for bet in ungraded:
        game = bet["game"]
        sport = bet.get("sport", "")

        # Determine the bet's date for date-aware score matching
        bet_date = bet.get("date") or (bet.get("logged_at", "")[:10] if bet.get("logged_at") else None)

        # Only match scores from the bet's date (prevents cross-day grading bugs)
        if not bet_date:
            continue

        if sport == "NHL":
            score_pool = nhl_scores_by_date.get(bet_date, {})
        elif sport == "MLB":
            score_pool = mlb_scores_by_date.get(bet_date, {})
        else:
            score_pool = {**nhl_scores_by_date.get(bet_date, {}), **mlb_scores_by_date.get(bet_date, {})}

        score = None
        for key, val in score_pool.items():
            if _match_game(game, key):
                score = val
                break

        if not score:
            continue

        actual_total = score["total"]
        bet["actual_total"] = actual_total
        line = bet.get("line", 0)

        if isinstance(line, str):
            try:
                line = float(line)
            except ValueError:
                continue

        side = bet.get("side", "").lower()
        market = bet.get("market", "").lower()

        # Grade totals bets
        is_total = ("total" in market or "over" in side or "under" in side)
        is_moneyline = "moneyline" in market or side in ("home", "away")

        if is_total:
            if "over" in side:
                if actual_total > line:
                    bet["result"] = "win"
                elif actual_total < line:
                    bet["result"] = "loss"
                else:
                    bet["result"] = "push"
            elif "under" in side:
                if actual_total < line:
                    bet["result"] = "win"
                elif actual_total > line:
                    bet["result"] = "loss"
                else:
                    bet["result"] = "push"
        elif is_moneyline:
            home_score = score.get("home_score", 0)
            away_score = score.get("away_score", 0)
            if home_score != away_score:  # No ties in NHL/MLB
                home_won = home_score > away_score
                if side == "home":
                    bet["result"] = "win" if home_won else "loss"
                elif side == "away":
                    bet["result"] = "win" if not home_won else "loss"

        if bet["result"]:
            bet["graded_at"] = datetime.now(timezone.utc).isoformat()
            # Ensure date field exists
            if not bet.get("date"):
                if bet.get("logged_at"):
                    bet["date"] = bet["logged_at"][:10]
                elif "|" in bet.get("pick_id", ""):
                    for p in bet["pick_id"].split("|"):
                        if len(p) == 10 and p.count("-") == 2:
                            bet["date"] = p
                            break
            graded_count += 1

            if bet["result"] == "win":
                bet["pnl"] = round(bet["profit_if_win"], 2)
                ledger["summary"]["wins"] += 1
                ledger["summary"]["total_pnl"] += bet["profit_if_win"]
                ledger["bankroll"] += bet["profit_if_win"]
            elif bet["result"] == "loss":
                bet["pnl"] = round(-bet["wager"], 2)
                ledger["summary"]["losses"] += 1
                ledger["summary"]["total_pnl"] -= bet["wager"]
                ledger["bankroll"] -= bet["wager"]
            else:
                bet["pnl"] = 0.0
                ledger["summary"]["pushes"] += 1

            ledger["summary"]["graded"] += 1

    save_ledger(ledger)
    print(f"  Graded {graded_count} bets ({ledger['summary']['graded']} total graded)")


def generate_report():
    """Generate daily summary report."""
    ledger = load_ledger()
    s = ledger["summary"]
    now = datetime.now(timezone.utc)

    graded = s["graded"]
    if graded == 0:
        wr = 0
        roi = 0
    else:
        wr = s["wins"] / graded * 100
        roi = s["total_pnl"] / s["total_wagered"] * 100 if s["total_wagered"] > 0 else 0

    clv_avg = s["clv_sum"] / s["clv_checks"] * 100 if s["clv_checks"] > 0 else 0
    clv_pos_rate = s["clv_positive"] / s["clv_checks"] * 100 if s["clv_checks"] > 0 else 0

    report = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now.isoformat(),
        "bankroll": round(ledger["bankroll"], 2),
        "total_bets": s["total_bets"],
        "graded": graded,
        "pending": s["total_bets"] - graded,
        "record": f"{s['wins']}W-{s['losses']}L-{s['pushes']}P",
        "win_rate": round(wr, 1),
        "total_pnl": round(s["total_pnl"], 2),
        "roi": round(roi, 1),
        "clv_checks": s["clv_checks"],
        "clv_avg": round(clv_avg, 2),
        "clv_positive_rate": round(clv_pos_rate, 1),
        "target_bets": 200,
        "progress": f"{graded}/200 ({graded/200*100:.0f}%)",
    }

    # Print report
    print(f"\n{'='*50}")
    print(f"  PAPER TRADING DAILY REPORT")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")
    print(f"  Bankroll: ${report['bankroll']:,.2f} (started ${BANKROLL:,})")
    print(f"  Record: {report['record']} ({report['win_rate']}% WR)")
    print(f"  P&L: ${report['total_pnl']:+,.2f} ({report['roi']:+.1f}% ROI)")
    print(f"  CLV: {report['clv_avg']:+.2f}% avg ({report['clv_positive_rate']:.0f}% positive)")
    print(f"  Progress: {report['progress']}")
    print(f"  Pending: {report['pending']} ungraded bets")
    print(f"{'='*50}")

    # Kill criteria check
    kill_triggered = False
    kill_reason = None
    clv_checks = s["clv_checks"]
    if clv_checks >= 30 and clv_avg < -2.0:
        kill_triggered = True
        kill_reason = f"CLV {clv_avg:+.2f}% at {clv_checks} checks (threshold: -2% at 30+)"
    elif clv_checks >= 50 and clv_avg < -1.0:
        kill_triggered = True
        kill_reason = f"CLV {clv_avg:+.2f}% at {clv_checks} checks (threshold: -1% at 50+)"
    elif graded >= 50 and roi < -10.0:
        kill_triggered = True
        kill_reason = f"ROI {roi:+.1f}% at {graded} graded bets (threshold: -10% at 50+)"

    if kill_triggered:
        print(f"\n  *** KILL CRITERIA TRIGGERED ***")
        print(f"  Reason: {kill_reason}")
        print(f"  ACTION: Pause all betting. Review model before continuing.")
        report["kill_triggered"] = True
        report["kill_reason"] = kill_reason
    else:
        report["kill_triggered"] = False

    # Save daily report
    rpath = os.path.join(DAILY_PATH, f"report_{now.strftime('%Y%m%d')}.json")
    with open(rpath, "w") as f:
        json.dump(report, f, indent=2)

    return report


def run_paper_cycle():
    """Run one full paper trading cycle.
    NOTE: log_picks() is DISABLED. Level 2 engine (edge_detector.py) handles all pick logging.
    This function only grades existing bets and generates reports.
    """
    print(f"\n  Paper Trading Cycle - {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    # log_picks()  # DISABLED - Level 2 engine handles pick logging via edge_detector.py
    grade_bets()
    generate_report()

    # Check CLV for all bets
    try:
        from clv_tracker import check_clv
        check_clv()
    except Exception as e:
        print(f"  [CLV] Warning: {e}")


if __name__ == "__main__":
    run_paper_cycle()

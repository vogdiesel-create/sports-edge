#!/usr/bin/env python3
"""
Sports Edge - Prop Bet Grader

Grades OddsTrader +EV prop picks against actual game results.
Uses free NHL API and MLB Stats API for player-level box scores.

This is the CRITICAL verification loop:
1. OddsTrader gives us +EV props with their model's cover probability
2. We log the picks before games start
3. After games complete, we grade each pick (win/loss)
4. We track hit rate, P&L, and compare model predictions to reality

If the model hits >55% on +EV props, we have real edge.
If not, we need our own devigging model.
"""

import json
import os
import re
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PROP_LEDGER = os.path.join(DATA_DIR, "prop_ledger.json")
PROP_LOG = os.path.join(DATA_DIR, "prop_picks_log.json")


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def american_to_decimal(american_str):
    if not american_str:
        return 2.0
    american = int(str(american_str).replace('+', ''))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


# ==================== NHL API ====================

def get_nhl_schedule(date_str=None):
    """Get NHL schedule. date_str format: YYYY-MM-DD"""
    if date_str:
        url = f"https://api-web.nhle.com/v1/score/{date_str}"
    else:
        url = "https://api-web.nhle.com/v1/score/now"
    resp = requests.get(url, timeout=10)
    return resp.json().get('games', [])


def get_nhl_boxscore(game_id):
    """Get NHL game boxscore with player stats."""
    resp = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore", timeout=10)
    return resp.json()


def get_nhl_player_stats(date_str=None):
    """Get all NHL player stats for today's completed games.

    Uses playerByGameStats from the boxscore API which contains the actual
    player stat lines (forwards, defense, goalies) nested under awayTeam/homeTeam.

    Also stores abbreviated names (e.g. "A. Copp") alongside full lookup keys
    to improve matching against OddsTrader pick names.
    """
    games = get_nhl_schedule(date_str)
    player_stats = {}

    for game in games:
        state = game.get('gameState', '')
        if state not in ('FINAL', 'OFF'):
            continue

        game_id = game.get('id')
        away_abbrev = game.get('awayTeam', {}).get('abbrev', '?')
        home_abbrev = game.get('homeTeam', {}).get('abbrev', '?')
        game_desc = f"{away_abbrev} @ {home_abbrev}"

        try:
            box = get_nhl_boxscore(game_id)
        except:
            continue

        # Player stats live under playerByGameStats, NOT the top-level team objects
        pbgs = box.get('playerByGameStats', {})

        for team_key in ['awayTeam', 'homeTeam']:
            team = pbgs.get(team_key, {})
            all_players = team.get('forwards', []) + team.get('defense', [])
            for player in all_players:
                name_obj = player.get('name', {})
                display_name = name_obj.get('default', '')
                if not display_name:
                    continue

                stat_entry = {
                    "name": display_name,
                    "game": game_desc,
                    "goals": player.get('goals', 0),
                    "assists": player.get('assists', 0),
                    "points": player.get('points', 0),
                    "shots": player.get('sog', 0),
                    "scored": player.get('goals', 0) > 0,
                }

                # Store under the display name (often abbreviated like "A. Copp")
                player_stats[display_name.lower()] = stat_entry

    return player_stats


# ==================== MLB API ====================

def get_mlb_schedule(date_str=None):
    """Get MLB schedule. date_str format: YYYY-MM-DD"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?date={date_str}&sportId=1"
    resp = requests.get(url, timeout=10)
    dates = resp.json().get('dates', [])
    return dates[0].get('games', []) if dates else []


def get_mlb_boxscore(game_pk):
    """Get MLB boxscore with player stats."""
    resp = requests.get(f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore", timeout=10)
    return resp.json()


def get_mlb_player_stats(date_str=None):
    """Get all MLB player stats for today's completed games."""
    games = get_mlb_schedule(date_str)
    player_stats = {}

    for game in games:
        status = game.get('status', {}).get('detailedState', '')
        if status not in ('Final', 'Game Over', 'Completed Early'):
            continue

        game_pk = game.get('gamePk')
        away_name = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '?')
        home_name = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '?')

        # Build abbreviated game string
        away_short = game.get('teams', {}).get('away', {}).get('team', {}).get('abbreviation', '?')
        home_short = game.get('teams', {}).get('home', {}).get('team', {}).get('abbreviation', '?')
        game_desc = f"{away_short} @ {home_short}"

        try:
            box = get_mlb_boxscore(game_pk)
        except:
            continue

        for side in ['away', 'home']:
            team_data = box.get('teams', {}).get(side, {})
            players = team_data.get('players', {})

            for pid_key, p_data in players.items():
                person = p_data.get('person', {})
                full_name = person.get('fullName', '')
                if not full_name:
                    continue

                batting = p_data.get('stats', {}).get('batting', {})
                pitching = p_data.get('stats', {}).get('pitching', {})

                stat = {
                    "name": full_name,
                    "game": game_desc,
                    "hits": batting.get('hits', 0),
                    "rbi": batting.get('rbi', 0),
                    "total_bases": batting.get('totalBases', 0),
                    "strikeouts_pitched": pitching.get('strikeOuts', 0),
                    "hits_allowed": pitching.get('hits', 0),
                    "earned_runs": pitching.get('earnedRuns', 0),
                    "had_rbi": batting.get('rbi', 0) > 0,
                    "had_hit": batting.get('hits', 0) > 0,
                }
                player_stats[full_name.lower()] = stat

    return player_stats


# ==================== GRADING ====================

def normalize_name(name):
    """Normalize player name for matching."""
    name = name.lower().strip()
    name = re.sub(r'[.\'-]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def find_player(player_name, stats_dict):
    """Fuzzy match player name against stats.

    Handles cases where the API returns abbreviated names like "A. Copp"
    but the pick has full names like "Andrew Copp", and vice versa.
    """
    norm = normalize_name(player_name)

    # Exact match
    if norm in stats_dict:
        return stats_dict[norm]

    # Normalized match
    for key, val in stats_dict.items():
        if normalize_name(key) == norm:
            return val

    # Last name + first initial match (handles "A. Copp" vs "Andrew Copp")
    parts = norm.split()
    if len(parts) >= 2:
        last = parts[-1]
        first_initial = parts[0][0] if parts[0] else ''
        for key, val in stats_dict.items():
            norm_key = normalize_name(key)
            key_parts = norm_key.split()
            if len(key_parts) >= 2:
                key_last = key_parts[-1]
                key_first_initial = key_parts[0][0] if key_parts[0] else ''
                # Match if last names equal and first initials match
                if key_last == last and key_first_initial == first_initial:
                    return val

    # Broader partial match: last name substring + first initial
    if len(parts) >= 2:
        last = parts[-1]
        first_initial = parts[0][0] if parts[0] else ''
        for key, val in stats_dict.items():
            norm_key = normalize_name(key)
            if last in norm_key and norm_key.startswith(first_initial):
                return val

    return None


def grade_prop(prop, nhl_stats, mlb_stats):
    """Grade a single prop bet. Returns dict with result or None if game not done."""
    sport = prop.get('sport', '')
    player = prop.get('player', '')
    market = prop.get('market', '')
    line_str = prop.get('line', '')
    odds_str = prop.get('best_odds', '')

    # Find player stats
    if sport == 'NHL':
        stats = find_player(player, nhl_stats)
    elif sport == 'MLB':
        stats = find_player(player, mlb_stats)
    else:
        return None

    if not stats:
        return None

    # Grade based on market type
    won = None
    actual = None

    market_lower = market.lower()

    # NHL markets
    if 'player to score' in market_lower and '2+' in market_lower:
        actual = stats.get('goals', 0)
        won = actual >= 2
    elif 'player to score first' in market_lower:
        # Can't easily grade first/last goal from boxscore
        return None
    elif 'player to score last' in market_lower:
        return None
    elif 'player to score' in market_lower:
        won = stats.get('scored', False)
        actual = stats.get('goals', 0)
    elif 'shots on goal' in market_lower or 'total shots' in market_lower:
        actual = stats.get('shots', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'total goals' in market_lower:
        actual = stats.get('goals', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'total points' in market_lower:
        actual = stats.get('points', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'total assists' in market_lower:
        actual = stats.get('assists', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)

    # MLB markets
    elif 'total hits' in market_lower or 'player hits' in market_lower:
        actual = stats.get('hits', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'rbi' in market_lower:
        won = stats.get('had_rbi', False)
        actual = stats.get('rbi', 0)
    elif 'total bases' in market_lower:
        actual = stats.get('total_bases', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'strikeout' in market_lower:
        actual = stats.get('strikeouts_pitched', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'hits allowed' in market_lower or 'pitching hits' in market_lower:
        actual = stats.get('hits_allowed', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)
    elif 'earned run' in market_lower:
        actual = stats.get('earned_runs', 0)
        line = parse_line(line_str)
        if line is not None:
            won = grade_ou(actual, line, line_str)

    if won is None:
        return None

    # Calculate P&L
    try:
        dec = american_to_decimal(odds_str)
    except:
        dec = 2.0
    stake = 20  # $20 unit
    pnl = stake * (dec - 1) if won else -stake

    return {
        "won": won,
        "pnl": round(pnl, 2),
        "actual": actual,
        "player_stats": stats,
    }


def parse_line(line_str):
    """Parse OddsTrader line string like 'u1½', 'o2½', 'u½'."""
    if not line_str:
        return None
    line_str = line_str.strip()
    # Remove o/u prefix
    num_part = re.sub(r'^[ou]', '', line_str)
    # Handle ½
    if '½' in num_part:
        num_part = num_part.replace('½', '.5')
        if num_part == '.5':
            num_part = '0.5'
    try:
        return float(num_part)
    except:
        return None


def grade_ou(actual, line, line_str):
    """Grade over/under bet."""
    if line_str.startswith('o'):
        return actual > line
    elif line_str.startswith('u'):
        return actual < line
    return None


# ==================== LOGGING ====================

def log_props():
    """Log current OddsTrader picks for grading later."""
    props_path = os.path.join(DATA_DIR, "oddstrader_ev_props.json")
    if not os.path.exists(props_path):
        print("No OddsTrader props to log.")
        return

    with open(props_path) as f:
        data = json.load(f)

    log = load_json(PROP_LOG, {"picks": []})
    existing = {(p.get("player"), p.get("market"), p.get("game")) for p in log["picks"]}

    new_count = 0
    for prop in data.get("props", []):
        key = (prop.get("player"), prop.get("market"), prop.get("game"))
        if key not in existing:
            prop["logged_at"] = datetime.now(timezone.utc).isoformat()
            prop["graded"] = False
            log["picks"].append(prop)
            new_count += 1

    save_json(PROP_LOG, log)
    print(f"  Logged {new_count} new prop picks ({len(log['picks'])} total)")


def _parse_game_date(pick):
    """Extract the actual game date (YYYY-MM-DD) from a pick's date_time field.

    date_time looks like 'MON 04/13 6:35 PM' or 'TUE 04/14 7:40 PM'.
    We combine with the year from logged_at.
    """
    dt = pick.get('date_time', '')
    logged = pick.get('logged_at', '')
    if not dt:
        return logged[:10] if logged else None

    # Extract MM/DD from date_time
    import re as _re
    m = _re.search(r'(\d{2})/(\d{2})', dt)
    if not m:
        return logged[:10] if logged else None

    month, day = m.group(1), m.group(2)
    # Get year from logged_at
    year = logged[:4] if logged else str(datetime.now().year)
    return f"{year}-{month}-{day}"


def grade_props(date_str=None):
    """Grade all ungraded prop picks against actual results.

    If date_str is None, automatically determines all game dates from
    ungraded picks and fetches stats for each date.
    """
    log = load_json(PROP_LOG, {"picks": []})
    if not log["picks"]:
        print("  No prop picks to grade.")
        return

    ledger = load_json(PROP_LEDGER, {
        "bets": [],
        "bankroll": 1000.0,
        "started": datetime.now(timezone.utc).isoformat(),
        "summary": {},
    })

    # Determine which dates to fetch stats for
    if date_str:
        dates_to_fetch = [date_str]
    else:
        # Auto-detect all game dates from ungraded picks
        dates_needed = set()
        for pick in log["picks"]:
            if pick.get("graded"):
                continue
            game_date = _parse_game_date(pick)
            if game_date:
                dates_needed.add(game_date)
        dates_to_fetch = sorted(dates_needed)

    if not dates_to_fetch:
        print("  No dates to fetch for ungraded picks.")
        return

    print(f"  Loading player stats for {len(dates_to_fetch)} date(s): {', '.join(dates_to_fetch)}")

    # Fetch and merge stats across all dates
    nhl_stats = {}
    mlb_stats = {}
    for d in dates_to_fetch:
        try:
            nhl_day = get_nhl_player_stats(d)
            nhl_stats.update(nhl_day)
            print(f"    NHL {d}: {len(nhl_day)} players")
        except Exception as e:
            print(f"    NHL {d} error: {e}")
        try:
            mlb_day = get_mlb_player_stats(d)
            mlb_stats.update(mlb_day)
            print(f"    MLB {d}: {len(mlb_day)} players")
        except Exception as e:
            print(f"    MLB {d} error: {e}")

    print(f"    Total: {len(nhl_stats)} NHL, {len(mlb_stats)} MLB players")

    graded = 0
    wins = 0
    total_pnl = 0
    by_market = defaultdict(lambda: {"total": 0, "wins": 0, "pnl": 0})
    by_ev_tier = defaultdict(lambda: {"total": 0, "wins": 0, "pnl": 0})

    for pick in log["picks"]:
        if pick.get("graded"):
            continue

        result = grade_prop(pick, nhl_stats, mlb_stats)
        if result is None:
            continue

        pick["graded"] = True
        pick["result"] = result
        graded += 1

        if result["won"]:
            wins += 1
        total_pnl += result["pnl"]

        # Track by market
        market = pick.get("market", "unknown")
        by_market[market]["total"] += 1
        by_market[market]["wins"] += int(result["won"])
        by_market[market]["pnl"] += result["pnl"]

        # Track by EV tier
        ev = pick.get("ev_pct", 0)
        if ev >= 20:
            tier = "20%+"
        elif ev >= 15:
            tier = "15-20%"
        elif ev >= 10:
            tier = "10-15%"
        else:
            tier = "5-10%"
        by_ev_tier[tier]["total"] += 1
        by_ev_tier[tier]["wins"] += int(result["won"])
        by_ev_tier[tier]["pnl"] += result["pnl"]

        ledger["bets"].append({
            "timestamp": pick.get("logged_at", ""),
            "player": pick.get("player", ""),
            "market": pick.get("market", ""),
            "game": pick.get("game", ""),
            "ev_pct": pick.get("ev_pct", 0),
            "odds": pick.get("best_odds", ""),
            "won": result["won"],
            "pnl": result["pnl"],
            "actual": result.get("actual"),
        })
        ledger["bankroll"] += result["pnl"]

    save_json(PROP_LOG, log)
    save_json(PROP_LEDGER, ledger)

    # Report
    print(f"\n  PROP GRADING RESULTS")
    print(f"  {'=' * 50}")
    print(f"  Graded: {graded} | W: {wins} L: {graded - wins}")
    if graded > 0:
        wr = wins / graded * 100
        roi = total_pnl / (graded * 20) * 100
        print(f"  Win Rate: {wr:.1f}% | P&L: ${total_pnl:+.2f} | ROI: {roi:+.1f}%")

    if by_market:
        print(f"\n  By Market:")
        for market, stats in sorted(by_market.items(), key=lambda x: -x[1]["total"]):
            wr = stats["wins"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"    {market:30s} {stats['total']:3d} bets  {wr:.0f}% WR  ${stats['pnl']:+.2f}")

    if by_ev_tier:
        print(f"\n  By EV Tier:")
        for tier, stats in sorted(by_ev_tier.items()):
            wr = stats["wins"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"    {tier:10s} {stats['total']:3d} bets  {wr:.0f}% WR  ${stats['pnl']:+.2f}")

    print(f"\n  Running bankroll: ${ledger['bankroll']:.2f}")
    print(f"  Total prop bets: {len(ledger['bets'])}")

    # Individual results
    recent = [b for b in ledger["bets"][-20:]]
    if recent:
        print(f"\n  Recent Results:")
        for b in recent:
            status = "W" if b["won"] else "L"
            print(f"    [{status}] {b['player']:20s} {b['market']:25s} "
                  f"EV:+{b['ev_pct']:.0f}% actual:{b.get('actual','-')} ${b['pnl']:+.2f}")


def show_summary():
    """Show prop betting summary."""
    ledger = load_json(PROP_LEDGER, {"bets": [], "bankroll": 1000.0})
    bets = ledger.get("bets", [])

    if not bets:
        print("  No prop bets graded yet.")
        return

    total = len(bets)
    wins = sum(1 for b in bets if b.get("won"))
    total_pnl = sum(b.get("pnl", 0) for b in bets)
    total_staked = total * 20

    print(f"\n  PROP BETTING SUMMARY")
    print(f"  {'=' * 50}")
    print(f"  Total bets: {total}")
    print(f"  Record: {wins}W - {total - wins}L ({wins/total*100:.1f}% WR)")
    print(f"  P&L: ${total_pnl:+.2f}")
    print(f"  ROI: {total_pnl/total_staked*100:+.1f}%")
    print(f"  Bankroll: ${ledger['bankroll']:.2f}")

    # Break-even analysis
    print(f"\n  Model Accuracy:")
    print(f"  OddsTrader predicted these picks would be +EV.")
    if wins/total > 0.55:
        print(f"  RESULT: Model appears profitable ({wins/total*100:.1f}% > 55%)")
    elif total < 30:
        print(f"  RESULT: Too few bets to judge ({total} < 30 minimum)")
    else:
        print(f"  RESULT: Model may not have edge ({wins/total*100:.1f}% <= 55%)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        date = sys.argv[2] if len(sys.argv) > 2 else None
        if cmd == "log":
            log_props()
        elif cmd == "grade":
            grade_props(date)
        elif cmd == "summary":
            show_summary()
    else:
        log_props()
        grade_props()
        show_summary()

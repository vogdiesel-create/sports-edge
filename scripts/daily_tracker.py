#!/usr/bin/env python3
"""
Sports Edge - Unified Daily Tracker
====================================

Aggregates all pick sources, grades against actual results, and tracks
running P&L with flat $10 bets.

Pick sources:
  1. paper_ledger.json    - Game line picks (totals, moneylines) from edge_detector
  2. model_prop_picks.json - Batter/K prop model picks
  3. oddstrader_sim_ledger.json - OddsTrader EV simulation picks

Grading:
  - MLB: statsapi.mlb.com (box scores + game scores)
  - NHL: statsapi.web.nhl.com (game scores)
  - Marks each pick WIN / LOSS / PUSH

Tracking:
  - Flat $10 per bet (normalizes across sources for apples-to-apples comparison)
  - Daily and cumulative P&L
  - Breakdown by source, sport, market type
  - Tracks only picks from 2026-04-20 onward (post-model-fix)

Output:
  /home/aiciv/sports-edge/tracking/daily_results.json

Usage:
    python3 scripts/daily_tracker.py                # Grade + summary
    python3 scripts/daily_tracker.py --grade        # Grade only
    python3 scripts/daily_tracker.py --summary      # Summary only
    python3 scripts/daily_tracker.py --date 2026-04-20  # Grade specific date
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
RESULTS_PATH = os.path.join(TRACKING_DIR, "daily_results.json")
os.makedirs(TRACKING_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FLAT_BET = 10.0          # $10 flat bet for tracking
CUTOFF_DATE = "2026-04-20"  # Post-fix tracking start
REQUEST_TIMEOUT = 15

# ---------------------------------------------------------------------------
# Odds helpers
# ---------------------------------------------------------------------------


def american_to_decimal(odds):
    """Convert American odds (int or str) to decimal."""
    if isinstance(odds, str):
        if odds.lower() in ("even", "ev"):
            return 2.0
        odds = int(odds.replace("+", ""))
    if not odds or odds == 0:
        return 2.0
    if odds > 0:
        return 1 + odds / 100
    else:
        return 1 + 100 / abs(odds)


def calc_pnl(won, odds, stake=FLAT_BET):
    """Calculate P&L for a bet outcome."""
    if won is None:
        return 0.0  # push
    dec = american_to_decimal(odds)
    if won:
        return round(stake * (dec - 1), 2)
    else:
        return round(-stake, 2)


# ---------------------------------------------------------------------------
# Data loading: read all three source ledgers
# ---------------------------------------------------------------------------


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def load_paper_ledger():
    """Load game-line picks from paper_ledger.json."""
    data = load_json(os.path.join(DATA_DIR, "paper_ledger.json"))
    if not data:
        return []
    picks = []
    for b in data.get("bets", []):
        date = b.get("date", b.get("logged_at", ""))[:10]
        if date < CUTOFF_DATE:
            continue
        picks.append({
            "id": b.get("pick_id", ""),
            "source": "edge_detector",
            "date": date,
            "sport": b.get("sport", "MLB"),
            "game": b.get("game", ""),
            "market_type": _classify_market(b.get("market", ""), b.get("side", "")),
            "description": f"{b.get('side', '')} {b.get('line', '')} ({b.get('market', '')})",
            "player": "",
            "side": b.get("side", ""),
            "line": b.get("line"),
            "odds": b.get("odds", 0),
            "edge": b.get("edge", 0),
            "tier": b.get("tier", ""),
            # Grading fields
            "result": _normalize_result(b),
            "actual": b.get("actual_total"),
            "pnl": None,  # recalculated with flat bet
        })
    return picks


def load_model_props():
    """Load batter/K prop picks from model_prop_picks.json."""
    data = load_json(os.path.join(DATA_DIR, "model_prop_picks.json"))
    if not data:
        return []
    picks = []
    for p in data.get("picks", []):
        date = p.get("game_date", "")[:10]
        if date < CUTOFF_DATE:
            continue
        picks.append({
            "id": f"prop|{date}|{p.get('player','')}|{p.get('market','')}",
            "source": "model_props",
            "date": date,
            "sport": p.get("sport", "MLB"),
            "game": p.get("game", ""),
            "market_type": _classify_prop_market(p.get("market", "")),
            "description": p.get("market", ""),
            "player": p.get("player", ""),
            "side": "",
            "line": None,
            "odds": p.get("odds", 0),
            "edge": p.get("edge", 0),
            "tier": "",
            "result": "win" if p.get("won") is True else ("loss" if p.get("won") is False else None) if p.get("graded") else None,
            "actual": p.get("actual"),
            "pnl": None,
        })
    return picks


def load_oddstrader():
    """Load OddsTrader simulation picks from oddstrader_sim_ledger.json."""
    data = load_json(os.path.join(DATA_DIR, "oddstrader_sim_ledger.json"))
    if not data:
        return []
    picks = []
    for b in data.get("bets", []):
        date = b.get("date", "")[:10]
        if date < CUTOFF_DATE:
            continue
        picks.append({
            "id": f"ot|{date}|{b.get('player','')}|{b.get('market','')}|{b.get('line','')}",
            "source": "oddstrader",
            "date": date,
            "sport": "MLB",
            "game": b.get("game", ""),
            "market_type": _classify_prop_market(b.get("market", "")),
            "description": f"{b.get('player','')} {b.get('market','')} {b.get('line','')}",
            "player": b.get("player", ""),
            "side": "",
            "line": b.get("line", ""),
            "odds": b.get("odds", "0"),
            "edge": b.get("ev_pct", 0),
            "tier": b.get("tier", ""),
            "result": "win" if b.get("won") is True else ("loss" if b.get("won") is False else None) if b.get("graded") else None,
            "actual": b.get("actual"),
            "pnl": None,
        })
    return picks


def _normalize_result(bet):
    """Normalize result field from paper_ledger format."""
    r = bet.get("result", "")
    if r == "win":
        return "win"
    elif r == "loss":
        return "loss"
    elif r == "push":
        return "push"
    # Check graded/won fields as fallback
    if bet.get("graded") or bet.get("graded_at"):
        if bet.get("won") is True or r == "win":
            return "win"
        elif bet.get("won") is False or r == "loss":
            return "loss"
    return None  # ungraded


def _classify_market(market, side):
    """Classify game-line market type."""
    m = (market or "").lower()
    s = (side or "").lower()
    if "total" in m or "over" in s or "under" in s:
        return "totals"
    if "moneyline" in m or "ml" in m:
        return "moneyline"
    if "spread" in m or "puck" in m or "run" in m:
        return "spread"
    return "game_other"


def _classify_prop_market(market):
    """Classify prop market type."""
    m = (market or "").lower()
    if "strikeout" in m or " k " in m or " ks" in m:
        return "K_props"
    if "home run" in m or "hr" in m:
        return "HR_props"
    if "total bases" in m or "total base" in m:
        return "TB_props"
    if "hit" in m:
        return "hits_props"
    if "rbi" in m:
        return "RBI_props"
    if "run" in m and "earned" not in m:
        return "runs_props"
    if "stolen" in m:
        return "SB_props"
    if "earned run" in m:
        return "ER_props"
    if "hits allowed" in m or "pitching hits" in m:
        return "HA_props"
    return "other_props"


# ---------------------------------------------------------------------------
# Grading: fetch actual results and grade ungraded picks
# ---------------------------------------------------------------------------


def fetch_mlb_scores(date_str):
    """Fetch MLB game scores for a date. Returns dict of game_key -> scores."""
    url = f"https://statsapi.mlb.com/api/v1/schedule?date={date_str}&sportId=1&hydrate=linescore"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"  MLB scores fetch error: {e}")
        return {}

    games = {}
    for date_entry in resp.json().get("dates", []):
        for g in date_entry.get("games", []):
            status = g.get("status", {}).get("detailedState", "")
            if status not in ("Final", "Game Over", "Completed Early"):
                continue
            away = g.get("teams", {}).get("away", {})
            home = g.get("teams", {}).get("home", {})
            away_name = away.get("team", {}).get("abbreviation", "")
            home_name = home.get("team", {}).get("abbreviation", "")
            away_score = away.get("score", 0)
            home_score = home.get("score", 0)
            game_pk = g.get("gamePk")

            key = f"{away_name} @ {home_name}"
            games[key] = {
                "away": away_name,
                "home": home_name,
                "away_score": int(away_score),
                "home_score": int(home_score),
                "total": int(away_score) + int(home_score),
                "game_pk": game_pk,
            }
    return games


def fetch_mlb_player_stats(date_str):
    """Fetch MLB player box scores for a date. Returns dict of player_name_lower -> stats."""
    url = f"https://statsapi.mlb.com/api/v1/schedule?date={date_str}&sportId=1"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"  MLB player stats fetch error: {e}")
        return {}

    player_stats = {}
    for date_entry in resp.json().get("dates", []):
        for game in date_entry.get("games", []):
            status = game.get("status", {}).get("detailedState", "")
            if status not in ("Final", "Game Over", "Completed Early"):
                continue
            game_pk = game.get("gamePk")
            try:
                box_resp = requests.get(
                    f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore",
                    timeout=REQUEST_TIMEOUT)
                box_resp.raise_for_status()
                box = box_resp.json()
            except Exception:
                continue

            for side in ["away", "home"]:
                players = box.get("teams", {}).get(side, {}).get("players", {})
                for _, p_data in players.items():
                    name = p_data.get("person", {}).get("fullName", "")
                    if not name:
                        continue
                    batting = p_data.get("stats", {}).get("batting", {})
                    pitching = p_data.get("stats", {}).get("pitching", {})
                    player_stats[name.lower()] = {
                        "name": name,
                        "hits": batting.get("hits", 0),
                        "home_runs": batting.get("homeRuns", 0),
                        "rbi": batting.get("rbi", 0),
                        "runs": batting.get("runs", 0),
                        "total_bases": batting.get("totalBases", 0),
                        "stolen_bases": batting.get("stolenBases", 0),
                        "at_bats": batting.get("atBats", 0),
                        "strikeouts_pitched": pitching.get("strikeOuts", 0),
                        "innings_pitched": pitching.get("inningsPitched", "0"),
                        "hits_allowed": pitching.get("hits", 0),
                        "earned_runs": pitching.get("earnedRuns", 0),
                    }
    return player_stats


def fetch_nhl_scores(date_str):
    """Fetch NHL game scores for a date."""
    url = f"https://api-web.nhle.com/v1/score/{date_str}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  NHL scores fetch error: {e}")
        return {}

    games = {}
    for g in data.get("games", []):
        state = g.get("gameState", "")
        if state not in ("OFF", "FINAL"):
            continue
        away_abbr = g.get("awayTeam", {}).get("abbrev", "")
        home_abbr = g.get("homeTeam", {}).get("abbrev", "")
        away_score = g.get("awayTeam", {}).get("score", 0)
        home_score = g.get("homeTeam", {}).get("score", 0)
        key = f"{away_abbr} @ {home_abbr}"
        games[key] = {
            "away": away_abbr,
            "home": home_abbr,
            "away_score": int(away_score),
            "home_score": int(home_score),
            "total": int(away_score) + int(home_score),
        }
    return games


def _find_game(pick_game, score_dict):
    """Fuzzy match a pick's game string against score keys."""
    pg = (pick_game or "").upper().strip()
    if not pg:
        return None

    # Direct match
    if pg in score_dict:
        return score_dict[pg]

    # Try matching abbreviations
    for key, val in score_dict.items():
        key_up = key.upper()
        # Check if both team abbreviations appear
        parts = pg.replace(" VS ", " @ ").split(" @ ")
        if len(parts) == 2:
            a, h = parts[0].strip(), parts[1].strip()
            # Match if abbreviations match
            if (a in key_up or key_up.startswith(a)) and (h in key_up or key_up.endswith(h)):
                return val
            # Match by any contained abbreviation
            if val["away"] in pg and val["home"] in pg:
                return val
        # Partial match
        if val["away"] in pg or val["home"] in pg:
            return val

    return None


def grade_game_line_pick(pick, scores):
    """Grade a totals or moneyline pick against game scores."""
    game = _find_game(pick["game"], scores)
    if not game:
        return None

    side = (pick.get("side") or "").upper()
    line = pick.get("line")
    total = game["total"]

    market = pick.get("market_type", "")

    if market == "totals" or "OVER" in side or "UNDER" in side:
        if line is None:
            return None
        try:
            line_val = float(line)
        except (ValueError, TypeError):
            return None
        if total == line_val:
            return "push", total
        if "OVER" in side:
            return ("win" if total > line_val else "loss"), total
        elif "UNDER" in side:
            return ("win" if total < line_val else "loss"), total

    if market == "moneyline":
        if "HOME" in side:
            return ("win" if game["home_score"] > game["away_score"] else "loss"), f"{game['away_score']}-{game['home_score']}"
        elif "AWAY" in side:
            return ("win" if game["away_score"] > game["home_score"] else "loss"), f"{game['away_score']}-{game['home_score']}"

    return None


def _parse_ot_line(line_str):
    """Parse OddsTrader line format: u4 1/2 -> (under, 4.5)."""
    if not line_str:
        return None, None
    s = str(line_str).strip().lower()
    direction = None
    if s.startswith("u"):
        direction = "under"
        s = s[1:]
    elif s.startswith("o"):
        direction = "over"
        s = s[1:]
    s = s.replace("\u00bd", ".5")  # half symbol
    try:
        return direction, float(s)
    except (ValueError, TypeError):
        return direction, None


def grade_prop_pick(pick, player_stats):
    """Grade a prop pick against player box score stats."""
    player = pick.get("player", "")
    if not player:
        return None

    # Find player in stats (exact then fuzzy)
    stats = player_stats.get(player.lower())
    if not stats:
        last = player.split()[-1].lower() if player else ""
        for key, val in player_stats.items():
            if last and last in key:
                stats = val
                break
    if not stats:
        return None

    desc = (pick.get("description") or "").lower()
    market = pick.get("market_type", "")
    line_str = pick.get("line", "")

    # Parse over/under line (for OddsTrader format)
    direction, line_val = _parse_ot_line(line_str) if line_str else (None, None)

    # Also check description for over/under patterns
    if not direction:
        import re
        m = re.search(r"(over|under)\s+(\d+\.?\d*)", desc)
        if m:
            direction = m.group(1)
            line_val = float(m.group(2))

    # Strikeouts (pitcher)
    if market == "K_props" or "strikeout" in desc:
        actual = stats["strikeouts_pitched"]
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        return None

    # Hits allowed (pitcher)
    if market == "HA_props" or "hits allowed" in desc:
        actual = stats.get("hits_allowed", 0)
        if stats.get("innings_pitched", "0") == "0":
            return None
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        return None

    # Earned runs (pitcher)
    if market == "ER_props" or "earned run" in desc:
        actual = stats.get("earned_runs", 0)
        if stats.get("innings_pitched", "0") == "0":
            return None
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        return None

    # Total bases
    if market == "TB_props" or "total base" in desc:
        actual = stats["total_bases"]
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        import re
        m = re.search(r"(\d+)\+", desc)
        if m:
            return ("win" if actual >= int(m.group(1)) else "loss"), actual
        return ("win" if actual >= 2 else "loss"), actual

    # Hits
    if market == "hits_props" or ("hit" in desc and "rbi" not in desc):
        actual = stats["hits"]
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        import re
        m = re.search(r"(\d+)\+", desc)
        if m:
            return ("win" if actual >= int(m.group(1)) else "loss"), actual
        return ("win" if actual >= 1 else "loss"), actual

    # Home runs
    if market == "HR_props" or "home run" in desc:
        actual = stats["home_runs"]
        if "2+" in desc:
            return ("win" if actual >= 2 else "loss"), actual
        return ("win" if actual >= 1 else "loss"), actual

    # RBI
    if market == "RBI_props" or "rbi" in desc:
        actual = stats["rbi"]
        if direction and line_val is not None:
            if direction == "under":
                return ("win" if actual < line_val else "loss"), actual
            else:
                return ("win" if actual > line_val else "loss"), actual
        if "2+" in desc:
            return ("win" if actual >= 2 else "loss"), actual
        return ("win" if actual >= 1 else "loss"), actual

    # Runs scored
    if market == "runs_props" or ("run" in desc and "record" in desc):
        actual = stats["runs"]
        if "2+" in desc:
            return ("win" if actual >= 2 else "loss"), actual
        return ("win" if actual >= 1 else "loss"), actual

    # Stolen bases
    if market == "SB_props" or "stolen" in desc:
        actual = stats["stolen_bases"]
        if "2+" in desc:
            return ("win" if actual >= 2 else "loss"), actual
        return ("win" if actual >= 1 else "loss"), actual

    return None


# ---------------------------------------------------------------------------
# Results tracking: unified results file
# ---------------------------------------------------------------------------


def load_results():
    """Load the unified tracking results."""
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            return json.load(f)
    return {
        "created": datetime.now(timezone.utc).isoformat(),
        "cutoff_date": CUTOFF_DATE,
        "flat_bet": FLAT_BET,
        "picks": [],
        "daily_summaries": {},
    }


def save_results(results):
    """Save tracking results."""
    results["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)


def merge_picks(results, new_picks):
    """Merge new picks into results, deduplicating by ID."""
    existing_ids = {p["id"] for p in results["picks"]}
    added = 0
    for p in new_picks:
        if p["id"] not in existing_ids:
            results["picks"].append(p)
            existing_ids.add(p["id"])
            added += 1
    return added


def grade_ungraded(results):
    """Grade all ungraded picks by fetching actual results."""
    ungraded = [p for p in results["picks"] if p.get("result") is None]
    if not ungraded:
        print("All picks already graded.")
        return 0

    # Group by date and sport
    dates_sports = defaultdict(set)
    for p in ungraded:
        dates_sports[p["date"]].add(p["sport"])

    # Fetch results per date
    mlb_scores_cache = {}
    mlb_player_cache = {}
    nhl_scores_cache = {}

    graded_count = 0

    for date_str in sorted(dates_sports.keys()):
        sports = dates_sports[date_str]
        print(f"  Fetching results for {date_str}...")

        if "MLB" in sports:
            if date_str not in mlb_scores_cache:
                mlb_scores_cache[date_str] = fetch_mlb_scores(date_str)
            if date_str not in mlb_player_cache:
                mlb_player_cache[date_str] = fetch_mlb_player_stats(date_str)

        if "NHL" in sports:
            if date_str not in nhl_scores_cache:
                nhl_scores_cache[date_str] = fetch_nhl_scores(date_str)

        for pick in results["picks"]:
            if pick.get("result") is not None or pick["date"] != date_str:
                continue

            result = None
            sport = pick["sport"]
            mtype = pick["market_type"]

            # Game-line picks (totals, moneylines)
            if mtype in ("totals", "moneyline", "spread", "game_other"):
                scores = mlb_scores_cache.get(date_str, {}) if sport == "MLB" else nhl_scores_cache.get(date_str, {})
                graded = grade_game_line_pick(pick, scores)
                if graded:
                    result, actual = graded
                    pick["actual"] = actual

            # Prop picks
            elif "props" in mtype:
                player_stats = mlb_player_cache.get(date_str, {})
                graded = grade_prop_pick(pick, player_stats)
                if graded:
                    result, actual = graded
                    pick["actual"] = actual

            if result:
                pick["result"] = result
                pick["pnl"] = calc_pnl(
                    True if result == "win" else (False if result == "loss" else None),
                    pick["odds"]
                )
                pick["graded_at"] = datetime.now(timezone.utc).isoformat()
                graded_count += 1

    return graded_count


def compute_daily_summaries(results):
    """Compute daily summary stats and store in results."""
    graded = [p for p in results["picks"] if p.get("result") in ("win", "loss", "push")]

    by_date = defaultdict(list)
    for p in graded:
        by_date[p["date"]].append(p)

    cumulative_pnl = 0.0
    cumulative_wins = 0
    cumulative_losses = 0
    cumulative_pushes = 0

    for date_str in sorted(by_date.keys()):
        day_picks = by_date[date_str]
        wins = sum(1 for p in day_picks if p["result"] == "win")
        losses = sum(1 for p in day_picks if p["result"] == "loss")
        pushes = sum(1 for p in day_picks if p["result"] == "push")
        day_pnl = sum(p.get("pnl", 0) for p in day_picks)

        cumulative_wins += wins
        cumulative_losses += losses
        cumulative_pushes += pushes
        cumulative_pnl += day_pnl

        total_bets = wins + losses  # pushes don't count for ROI
        day_roi = (day_pnl / (total_bets * FLAT_BET) * 100) if total_bets > 0 else 0.0

        cum_total = cumulative_wins + cumulative_losses
        cum_roi = (cumulative_pnl / (cum_total * FLAT_BET) * 100) if cum_total > 0 else 0.0

        # Breakdown by source
        by_source = defaultdict(lambda: {"w": 0, "l": 0, "push": 0, "pnl": 0.0})
        for p in day_picks:
            src = p["source"]
            if p["result"] == "win":
                by_source[src]["w"] += 1
            elif p["result"] == "loss":
                by_source[src]["l"] += 1
            else:
                by_source[src]["push"] += 1
            by_source[src]["pnl"] += p.get("pnl", 0)

        # Breakdown by market type
        by_market = defaultdict(lambda: {"w": 0, "l": 0, "push": 0, "pnl": 0.0})
        for p in day_picks:
            mt = p["market_type"]
            if p["result"] == "win":
                by_market[mt]["w"] += 1
            elif p["result"] == "loss":
                by_market[mt]["l"] += 1
            else:
                by_market[mt]["push"] += 1
            by_market[mt]["pnl"] += p.get("pnl", 0)

        results["daily_summaries"][date_str] = {
            "date": date_str,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "day_pnl": round(day_pnl, 2),
            "day_roi_pct": round(day_roi, 2),
            "cumulative_wins": cumulative_wins,
            "cumulative_losses": cumulative_losses,
            "cumulative_pushes": cumulative_pushes,
            "cumulative_pnl": round(cumulative_pnl, 2),
            "cumulative_roi_pct": round(cum_roi, 2),
            "by_source": dict(by_source),
            "by_market": dict(by_market),
        }

    # Overall stats
    total_graded = cumulative_wins + cumulative_losses
    results["overall"] = {
        "total_picks": len(results["picks"]),
        "graded": len(graded),
        "ungraded": len(results["picks"]) - len(graded),
        "wins": cumulative_wins,
        "losses": cumulative_losses,
        "pushes": cumulative_pushes,
        "win_rate_pct": round(cumulative_wins / total_graded * 100, 2) if total_graded > 0 else 0.0,
        "total_pnl": round(cumulative_pnl, 2),
        "roi_pct": round(cumulative_pnl / (total_graded * FLAT_BET) * 100, 2) if total_graded > 0 else 0.0,
        "flat_bet": FLAT_BET,
    }


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def print_summary(results):
    """Print the daily summary to stdout."""
    overall = results.get("overall", {})
    daily = results.get("daily_summaries", {})

    if not overall or overall.get("graded", 0) == 0:
        print("\nNo graded picks yet.")
        ungraded = overall.get("ungraded", 0)
        if ungraded:
            print(f"  {ungraded} picks pending grading.")
        return

    print()
    print("=" * 65)
    print("  SPORTS EDGE - UNIFIED DAILY TRACKER")
    print(f"  Tracking since: {CUTOFF_DATE} | Flat bet: ${FLAT_BET:.0f}")
    print("=" * 65)

    # Yesterday's results
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if yesterday in daily:
        d = daily[yesterday]
        print(f"\n  YESTERDAY ({yesterday}):")
        print(f"    Record: {d['wins']}W - {d['losses']}L", end="")
        if d["pushes"]:
            print(f" - {d['pushes']}P", end="")
        print(f"  |  P&L: ${d['day_pnl']:+.2f}  |  ROI: {d['day_roi_pct']:+.1f}%")

        # Yesterday by source
        if d.get("by_source"):
            for src, s in d["by_source"].items():
                t = s["w"] + s["l"]
                wr = s["w"] / t * 100 if t > 0 else 0
                print(f"      {src:<18} {s['w']}W-{s['l']}L ({wr:.0f}%)  ${s['pnl']:+.2f}")
    else:
        print(f"\n  YESTERDAY ({yesterday}): No picks graded.")

    # Running totals
    print(f"\n  RUNNING TOTALS (since {CUTOFF_DATE}):")
    print(f"    Record: {overall['wins']}W - {overall['losses']}L", end="")
    if overall.get("pushes"):
        print(f" - {overall['pushes']}P", end="")
    print(f"  |  Win Rate: {overall['win_rate_pct']:.1f}%")
    print(f"    P&L: ${overall['total_pnl']:+.2f}  |  ROI: {overall['roi_pct']:+.1f}%")
    print(f"    Total picks: {overall['total_picks']}  |  Graded: {overall['graded']}  |  Pending: {overall['ungraded']}")

    # Running by source
    all_graded = [p for p in results["picks"] if p.get("result") in ("win", "loss", "push")]
    by_source = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0.0})
    for p in all_graded:
        src = p["source"]
        if p["result"] == "win":
            by_source[src]["w"] += 1
        elif p["result"] == "loss":
            by_source[src]["l"] += 1
        by_source[src]["pnl"] += p.get("pnl", 0)

    print(f"\n  BY SOURCE:")
    print(f"    {'Source':<20} {'W':>4} {'L':>4} {'WR':>6} {'P&L':>9} {'ROI':>7}")
    print(f"    {'-'*52}")
    for src in sorted(by_source.keys()):
        s = by_source[src]
        t = s["w"] + s["l"]
        wr = s["w"] / t * 100 if t > 0 else 0
        roi = s["pnl"] / (t * FLAT_BET) * 100 if t > 0 else 0
        print(f"    {src:<20} {s['w']:>4} {s['l']:>4} {wr:>5.1f}% ${s['pnl']:>+8.2f} {roi:>+6.1f}%")

    # Running by market type
    by_market = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0.0})
    for p in all_graded:
        mt = p["market_type"]
        if p["result"] == "win":
            by_market[mt]["w"] += 1
        elif p["result"] == "loss":
            by_market[mt]["l"] += 1
        by_market[mt]["pnl"] += p.get("pnl", 0)

    print(f"\n  BY MARKET TYPE:")
    print(f"    {'Market':<20} {'W':>4} {'L':>4} {'WR':>6} {'P&L':>9} {'ROI':>7}")
    print(f"    {'-'*52}")
    for mt in sorted(by_market.keys(), key=lambda x: -by_market[x]["pnl"]):
        s = by_market[mt]
        t = s["w"] + s["l"]
        wr = s["w"] / t * 100 if t > 0 else 0
        roi = s["pnl"] / (t * FLAT_BET) * 100 if t > 0 else 0
        print(f"    {mt:<20} {s['w']:>4} {s['l']:>4} {wr:>5.1f}% ${s['pnl']:>+8.2f} {roi:>+6.1f}%")

    # Daily P&L trend
    if len(daily) > 1:
        print(f"\n  DAILY P&L TREND:")
        for date_str in sorted(daily.keys()):
            d = daily[date_str]
            bar_len = int(abs(d["day_pnl"]) / FLAT_BET)
            bar = ("+" * bar_len) if d["day_pnl"] >= 0 else ("-" * bar_len)
            print(f"    {date_str}  {d['wins']}W-{d['losses']}L  ${d['day_pnl']:>+8.2f}  cum: ${d['cumulative_pnl']:>+8.2f}  {bar}")

    print()
    print("=" * 65)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_grade(target_date=None):
    """Run the grading pipeline."""
    print("Sports Edge Daily Tracker")
    print(f"  Cutoff: {CUTOFF_DATE} | Flat bet: ${FLAT_BET:.0f}")
    print()

    # Load existing results
    results = load_results()

    # Load all pick sources
    print("Loading pick sources...")
    paper_picks = load_paper_ledger()
    model_picks = load_model_props()
    ot_picks = load_oddstrader()
    print(f"  edge_detector: {len(paper_picks)} picks")
    print(f"  model_props:   {len(model_picks)} picks")
    print(f"  oddstrader:    {len(ot_picks)} picks")

    # Merge into results
    all_picks = paper_picks + model_picks + ot_picks
    added = merge_picks(results, all_picks)
    print(f"  New picks added: {added}")
    print(f"  Total tracked: {len(results['picks'])}")
    print()

    # Picks that already have results from source grading get imported as-is
    # Only grade the ungraded ones via API
    already_graded = sum(1 for p in results["picks"] if p.get("result") is not None and p.get("pnl") is None)
    for p in results["picks"]:
        if p.get("result") is not None and p.get("pnl") is None:
            p["pnl"] = calc_pnl(
                True if p["result"] == "win" else (False if p["result"] == "loss" else None),
                p["odds"]
            )

    # Grade any ungraded picks
    ungraded = [p for p in results["picks"] if p.get("result") is None]
    if ungraded:
        print(f"Grading {len(ungraded)} ungraded picks...")
        graded = grade_ungraded(results)
        print(f"  Graded: {graded}")
    else:
        print("All picks already graded.")

    # Compute summaries
    compute_daily_summaries(results)

    # Save
    save_results(results)
    print(f"\nResults saved to {RESULTS_PATH}")

    return results


def run_summary():
    """Show summary only (no grading)."""
    results = load_results()
    if not results["picks"]:
        print("No tracking data yet. Run with --grade first.")
        return
    compute_daily_summaries(results)
    print_summary(results)


def main():
    args = sys.argv[1:]
    target_date = None

    # Parse --date argument
    for i, arg in enumerate(args):
        if arg == "--date" and i + 1 < len(args):
            target_date = args[i + 1]

    if "--summary" in args:
        run_summary()
    elif "--grade" in args:
        results = run_grade(target_date)
        print_summary(results)
    else:
        # Default: grade + summary
        results = run_grade(target_date)
        print_summary(results)


if __name__ == "__main__":
    main()

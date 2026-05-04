#!/usr/bin/env python3
"""
Sports Edge - Auto Grader

Checks picks from previous scans against actual results.
Uses sbrscrape for game line results and FanDuel API for prop results.

Tracks cumulative P&L over time.
"""

import json
import os
import time
from datetime import datetime, timezone

try:
    from sbrscrape import Scoreboard
except ImportError:
    print("Install: pip3 install --break-system-packages sbrscrape")
    raise

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LEDGER_PATH = os.path.join(DATA_DIR, "bet_ledger.json")


def load_ledger():
    if os.path.exists(LEDGER_PATH):
        with open(LEDGER_PATH) as f:
            return json.load(f)
    return {"bets": [], "bankroll": 1000.0, "started": datetime.now(timezone.utc).isoformat()}


def save_ledger(ledger):
    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)


def american_to_decimal(american):
    if isinstance(american, str):
        if american in ("EVEN", "even"):
            return 2.0
        american = int(american.replace("+", ""))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def get_completed_games():
    """Get all completed games from SBR."""
    games = {}
    for sport in ["NBA", "MLB"]:  # NHL disabled Apr 29 per Braxton
        try:
            sb = Scoreboard(sport)
            for g in sb.games:
                if g.get("status") != "complete":
                    continue
                home = g.get("home_team", "")
                away = g.get("away_team", "")
                hs = g.get("home_score")
                asc = g.get("away_score")
                if hs is None or asc is None:
                    continue
                try:
                    hs, asc = int(hs), int(asc)
                except:
                    continue
                game_key = f"{away} @ {home}"
                games[game_key] = {
                    "sport": sport,
                    "home": home,
                    "away": away,
                    "home_score": hs,
                    "away_score": asc,
                    "total": hs + asc,
                }
            time.sleep(0.3)
        except Exception as e:
            print(f"Error loading {sport}: {e}")
    return games


def grade_pick(pick, games):
    """Grade a single pick against actual results. Returns (won, pnl, details) or None if game not found."""
    game_name = pick.get("game", "")
    bet = pick.get("bet", "")
    source = pick.get("source", "")

    # Find the game in completed games
    game = None
    for gk, gv in games.items():
        # Fuzzy match on team names
        if game_name and (game_name in gk or gk in game_name):
            game = gv
            break
        # Also try matching individual team names
        teams = game_name.split(" @ ") if " @ " in game_name else game_name.split(" vs ")
        if len(teams) == 2:
            for gk2, gv2 in games.items():
                if any(t.strip().lower() in gk2.lower() for t in teams):
                    game = gv2
                    break

    if game is None:
        return None

    # Parse bet details
    if source == "game_line_v2":
        # Format: "total over 6.5 @ unibet" or "moneyline home @ book"
        parts = bet.split(" @ ")
        if len(parts) < 2:
            return None
        bet_desc = parts[0].strip()
        book = parts[1].strip()

        if "total" in bet_desc:
            # Parse: "total over 6.5" or "total under 209"
            words = bet_desc.split()
            if len(words) >= 3:
                direction = words[1]  # over/under
                try:
                    line = float(words[2])
                except:
                    return None
                actual = game["total"]
                if actual == line:
                    return {"won": None, "result": "push", "actual": actual, "line": line}
                if direction == "over":
                    won = actual > line
                else:
                    won = actual < line

                # Calculate P&L
                odds_str = pick.get("odds", "+100")
                try:
                    dec = american_to_decimal(odds_str)
                except:
                    dec = 2.0
                stake = 20  # Default $20 unit
                pnl = stake * (dec - 1) if won else -stake

                return {
                    "won": won,
                    "pnl": round(pnl, 2),
                    "actual_total": actual,
                    "line": line,
                    "direction": direction,
                    "book": book,
                    "score": f"{game['away_score']}-{game['home_score']}",
                }

        elif "moneyline" in bet_desc:
            words = bet_desc.split()
            side = words[1] if len(words) > 1 else ""
            if side == "home":
                won = game["home_score"] > game["away_score"]
            elif side == "away":
                won = game["away_score"] > game["home_score"]
            else:
                return None

            odds_str = pick.get("odds", "+100")
            try:
                dec = american_to_decimal(odds_str)
            except:
                dec = 2.0
            stake = 20
            pnl = stake * (dec - 1) if won else -stake

            return {
                "won": won,
                "pnl": round(pnl, 2),
                "side": side,
                "score": f"{game['away_score']}-{game['home_score']}",
            }

    return None


def grade_all():
    """Grade all picks from latest scan."""
    scan_path = os.path.join(DATA_DIR, "unified_scan.json")
    if not os.path.exists(scan_path):
        print("No scan data found.")
        return

    with open(scan_path) as f:
        scan = json.load(f)

    picks = scan.get("picks", [])
    if not picks:
        print("No picks to grade.")
        return

    print(f"\nLoading completed games...")
    games = get_completed_games()
    print(f"Found {len(games)} completed games")

    print(f"\nGrading {len(picks)} picks...")
    print(f"{'='*60}")

    ledger = load_ledger()
    graded = 0
    wins = 0
    total_pnl = 0

    # Build set of already-graded pick keys to prevent duplicates
    existing_keys = set()
    for b in ledger["bets"]:
        p = b.get("pick", {})
        key = f"{p.get('game', '')}|{p.get('bet', '')}"
        existing_keys.add(key)

    for pick in picks:
        # Skip if already graded
        pick_key = f"{pick.get('game', '')}|{pick.get('bet', '')}"
        if pick_key in existing_keys:
            continue

        result = grade_pick(pick, games)
        if result is None:
            print(f"  ? {pick.get('game', '?')} - {pick.get('bet', '?')}: Game not found/incomplete")
            continue

        if result.get("won") is None:
            print(f"  - {pick.get('game', '?')} - {pick.get('bet', '?')}: PUSH")
            continue

        won = result["won"]
        pnl = result.get("pnl", 0)
        graded += 1
        if won:
            wins += 1
        total_pnl += pnl

        status = "W" if won else "L"
        print(f"  {status} {pick.get('game', '?')} | {pick.get('bet', '?')} | ${pnl:+.2f}")
        if "actual_total" in result:
            print(f"    Total: {result['actual_total']} vs line {result['line']} ({result['direction']})")
        if "score" in result:
            print(f"    Score: {result['score']}")

        # Add to ledger
        ledger["bets"].append({
            "timestamp": scan.get("timestamp", ""),
            "pick": pick,
            "result": result,
        })
        existing_keys.add(pick_key)
        ledger["bankroll"] += pnl

    save_ledger(ledger)

    print(f"\n{'='*60}")
    print(f"  GRADING SUMMARY")
    print(f"  Graded: {graded}/{len(picks)} | W: {wins} L: {graded-wins}")
    if graded > 0:
        print(f"  WR: {wins/graded*100:.0f}% | P&L: ${total_pnl:+.2f}")
    print(f"  Running bankroll: ${ledger['bankroll']:.2f}")
    print(f"  Total ledger bets: {len(ledger['bets'])}")

    return {"graded": graded, "wins": wins, "pnl": total_pnl}


if __name__ == "__main__":
    grade_all()

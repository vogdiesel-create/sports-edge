"""
Sports Edge - Game Line Backtester

Uses sbrscrape to get completed game results and their pre-game odds.
Tests our Pinnacle-benchmark strategy against actual results.

For each completed game:
1. Devig Pinnacle lines to get fair probabilities
2. Find books offering better odds than Pinnacle fair
3. Check if the bet would have won
4. Calculate P&L with Kelly sizing

This gives us real backtest results on game lines across NBA, MLB, NHL.
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

try:
    from sbrscrape import Scoreboard
except ImportError:
    print("Install: pip3 install --break-system-packages sbrscrape")
    raise

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def american_to_decimal(american):
    if isinstance(american, str):
        if american in ("EVEN", "even"):
            return 2.0
        american = int(american.replace("+", ""))
    if american > 0:
        return 1 + american / 100
    else:
        return 1 + 100 / abs(american)


def decimal_to_implied(dec):
    return 1.0 / dec if dec > 0 else 0


def devig_pinnacle(odds_a, odds_b):
    if odds_a is None or odds_b is None:
        return None, None
    imp_a = decimal_to_implied(american_to_decimal(odds_a))
    imp_b = decimal_to_implied(american_to_decimal(odds_b))
    total = imp_a + imp_b
    if total <= 0:
        return None, None
    return imp_a / total, imp_b / total


def kelly_fraction(prob, decimal_odds, fraction=0.25):
    b = decimal_odds - 1
    q = 1 - prob
    if b <= 0:
        return 0
    f = (b * prob - q) / b
    return max(0, f * fraction)


def backtest_sport(sport, min_edge=0.02):
    """Backtest game line strategy for a sport using today's completed games."""
    print(f"\n  [{sport}] Fetching games...")
    try:
        sb = Scoreboard(sport)
        games = sb.games
    except Exception as e:
        print(f"  [{sport}] Error: {e}")
        return None

    completed = [g for g in games if g.get("status") == "complete"]
    upcoming = [g for g in games if g.get("status") != "complete"]
    print(f"  [{sport}] {len(completed)} completed, {len(upcoming)} upcoming")

    if not completed:
        return None

    bets = []
    bankroll = 1000.0

    for game in completed:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        home_score = game.get("home_score", 0)
        away_score = game.get("away_score", 0)
        if home_score is None or away_score is None:
            continue
        total_score = home_score + away_score
        game_name = f"{away} @ {home}"

        # MONEYLINE bets
        home_ml = game.get("home_ml", {})
        away_ml = game.get("away_ml", {})
        if isinstance(home_ml, dict) and isinstance(away_ml, dict):
            pin_home = home_ml.get("pinnacle")
            pin_away = away_ml.get("pinnacle")
            if pin_home is not None and pin_away is not None:
                fair_home, fair_away = devig_pinnacle(pin_home, pin_away)
                if fair_home is not None:
                    home_won = home_score > away_score

                    for book, odds in home_ml.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_home - imp
                        ev = fair_home * (dec - 1) - (1 - fair_home)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_home, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            won = home_won
                            pnl = stake * (dec - 1) if won else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "moneyline",
                                "side": f"home ({home})", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": won,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score}",
                            })

                    for book, odds in away_ml.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_away - imp
                        ev = fair_away * (dec - 1) - (1 - fair_away)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_away, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            won = not home_won
                            pnl = stake * (dec - 1) if won else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "moneyline",
                                "side": f"away ({away})", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": won,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score}",
                            })

        # TOTAL bets
        totals = game.get("total", {})
        over_odds = game.get("over_odds", {})
        under_odds = game.get("under_odds", {})
        if isinstance(over_odds, dict) and isinstance(under_odds, dict):
            pin_over = over_odds.get("pinnacle")
            pin_under = under_odds.get("pinnacle")
            pin_total = totals.get("pinnacle") if isinstance(totals, dict) else totals

            if pin_over is not None and pin_under is not None and pin_total is not None:
                fair_over, fair_under = devig_pinnacle(pin_over, pin_under)
                if fair_over is not None:
                    for book, odds in over_odds.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        book_total = totals.get(book, pin_total) if isinstance(totals, dict) else totals
                        if book_total is None or book_total != pin_total:
                            continue  # Only compare same total line

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_over - imp
                        ev = fair_over * (dec - 1) - (1 - fair_over)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_over, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            won = total_score > pin_total
                            if total_score == pin_total:
                                continue  # Push
                            pnl = stake * (dec - 1) if won else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "total",
                                "side": f"over {pin_total}", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": won,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score} (total={total_score})",
                            })

                    for book, odds in under_odds.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        book_total = totals.get(book, pin_total) if isinstance(totals, dict) else totals
                        if book_total is None or book_total != pin_total:
                            continue

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_under - imp
                        ev = fair_under * (dec - 1) - (1 - fair_under)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_under, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            won = total_score < pin_total
                            if total_score == pin_total:
                                continue
                            pnl = stake * (dec - 1) if won else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "total",
                                "side": f"under {pin_total}", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": won,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score} (total={total_score})",
                            })

        # SPREAD bets
        home_spread = game.get("home_spread", {})
        home_spread_odds = game.get("home_spread_odds", {})
        away_spread = game.get("away_spread", {})
        away_spread_odds = game.get("away_spread_odds", {})

        if isinstance(home_spread_odds, dict) and isinstance(away_spread_odds, dict):
            pin_h_odds = home_spread_odds.get("pinnacle")
            pin_a_odds = away_spread_odds.get("pinnacle")
            pin_h_line = home_spread.get("pinnacle") if isinstance(home_spread, dict) else None
            pin_a_line = away_spread.get("pinnacle") if isinstance(away_spread, dict) else None

            if all(x is not None for x in [pin_h_odds, pin_a_odds, pin_h_line]):
                fair_home, fair_away = devig_pinnacle(pin_h_odds, pin_a_odds)
                if fair_home is not None:
                    margin = home_score - away_score  # Positive = home won

                    for book, odds in home_spread_odds.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        book_line = home_spread.get(book) if isinstance(home_spread, dict) else None
                        if book_line is None or book_line != pin_h_line:
                            continue

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_home - imp
                        ev = fair_home * (dec - 1) - (1 - fair_home)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_home, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            covered = margin + pin_h_line > 0
                            if margin + pin_h_line == 0:
                                continue  # Push
                            pnl = stake * (dec - 1) if covered else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "spread",
                                "side": f"home {pin_h_line:+.1f}", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": covered,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score}",
                            })

                    for book, odds in away_spread_odds.items():
                        if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                            continue
                        book_line = away_spread.get(book) if isinstance(away_spread, dict) else None
                        if book_line is None or (pin_a_line is not None and book_line != pin_a_line):
                            continue

                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except (ValueError, TypeError):
                            continue

                        edge = fair_away - imp
                        ev = fair_away * (dec - 1) - (1 - fair_away)

                        if edge >= min_edge and ev >= 0.01:
                            kf = kelly_fraction(fair_away, dec)
                            stake = min(bankroll * kf, bankroll * 0.02)
                            if stake < 1:
                                continue
                            covered = -margin + (pin_a_line or 0) > 0
                            if -margin + (pin_a_line or 0) == 0:
                                continue
                            pnl = stake * (dec - 1) if covered else -stake
                            bankroll += pnl
                            bets.append({
                                "game": game_name, "market": "spread",
                                "side": f"away {pin_a_line:+.1f}", "book": book,
                                "odds": odds, "edge": round(edge, 4),
                                "ev": round(ev, 4), "won": covered,
                                "stake": round(stake, 2), "pnl": round(pnl, 2),
                                "bankroll": round(bankroll, 2),
                                "score": f"{away_score}-{home_score}",
                            })

    return {
        "sport": sport,
        "games": len(completed),
        "bets": bets,
        "bankroll": round(bankroll, 2),
    }


def main():
    print(f"\n{'='*70}")
    print(f"  GAME LINE BACKTEST (Today's Completed Games)")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*70}")

    all_bets = []

    for sport in ["NBA", "MLB", "NHL"]:
        result = backtest_sport(sport)
        if not result:
            continue

        bets = result["bets"]
        if bets:
            wins = sum(1 for b in bets if b["won"])
            total_staked = sum(b["stake"] for b in bets)
            pnl = result["bankroll"] - 1000
            roi = pnl / total_staked * 100 if total_staked > 0 else 0

            print(f"\n  [{sport}] Results:")
            print(f"    Games: {result['games']}")
            print(f"    Bets: {len(bets)}")
            print(f"    Win rate: {wins}/{len(bets)} ({wins/len(bets)*100:.1f}%)")
            print(f"    P&L: ${pnl:+.2f}")
            print(f"    ROI: {roi:+.1f}%")
            print(f"    Bankroll: ${result['bankroll']:.2f}")

            for b in bets:
                w = "W" if b["won"] else "L"
                print(f"      [{w}] {b['game']} | {b['market']} {b['side']} "
                      f"@ {b['book']} {b['odds']:+d} | edge={b['edge']:.1%} "
                      f"| ${b['pnl']:+.2f} | {b['score']}")

            all_bets.extend(bets)
        else:
            print(f"\n  [{sport}] {result['games']} completed games, no +EV bets found")
        time.sleep(0.5)

    # Combined summary
    if all_bets:
        total_wins = sum(1 for b in all_bets if b["won"])
        total_staked = sum(b["stake"] for b in all_bets)
        total_pnl = sum(b["pnl"] for b in all_bets)
        roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

        print(f"\n{'='*70}")
        print(f"  COMBINED RESULTS")
        print(f"{'='*70}")
        print(f"  Total bets: {len(all_bets)}")
        print(f"  Win rate: {total_wins}/{len(all_bets)} ({total_wins/len(all_bets)*100:.1f}%)")
        print(f"  Total staked: ${total_staked:.2f}")
        print(f"  P&L: ${total_pnl:+.2f}")
        print(f"  ROI: {roi:+.1f}%")

        # By market
        by_mkt = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "staked": 0})
        for b in all_bets:
            by_mkt[b["market"]]["n"] += 1
            by_mkt[b["market"]]["w"] += 1 if b["won"] else 0
            by_mkt[b["market"]]["pnl"] += b["pnl"]
            by_mkt[b["market"]]["staked"] += b["stake"]

        print(f"\n  By market:")
        for mkt, s in sorted(by_mkt.items(), key=lambda x: -x[1]["pnl"]):
            wr = s["w"]/s["n"]*100
            mroi = s["pnl"]/s["staked"]*100 if s["staked"] else 0
            print(f"    {mkt}: {s['n']} bets, {wr:.0f}% WR, ${s['pnl']:+.2f} ({mroi:+.1f}%)")

        # Save
        outpath = os.path.join(DATA_DIR, "game_line_backtest.json")
        with open(outpath, "w") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bets": all_bets,
                "summary": {
                    "total_bets": len(all_bets),
                    "win_rate": total_wins / len(all_bets) if all_bets else 0,
                    "roi": roi,
                    "pnl": total_pnl,
                },
            }, f, indent=2)
        print(f"\n  Saved to {outpath}")
    else:
        print("\n  No +EV bets found across any sport today")


if __name__ == "__main__":
    main()

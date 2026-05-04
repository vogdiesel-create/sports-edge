"""
Sports Edge - Historical Game Line Backtester (Multi-Day)

Uses sbrscrape with date parameter to backtest our Pinnacle benchmark
strategy over many days of completed games.

This is the definitive test: does beating Pinnacle's fair line
actually produce profit over hundreds of bets?
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

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
    try:
        imp_a = decimal_to_implied(american_to_decimal(odds_a))
        imp_b = decimal_to_implied(american_to_decimal(odds_b))
    except (ValueError, TypeError):
        return None, None
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


def process_game(game, sport, min_edge=0.02, bankroll=None):
    """Process a single completed game for +EV bets."""
    bets = []
    home = game.get("home_team", "")
    away = game.get("away_team", "")
    home_score = game.get("home_score")
    away_score = game.get("away_score")

    if home_score is None or away_score is None:
        return bets

    try:
        home_score = int(home_score)
        away_score = int(away_score)
    except (ValueError, TypeError):
        return bets

    total_score = home_score + away_score
    game_name = f"{away} @ {home}"

    # MONEYLINE
    home_ml = game.get("home_ml", {})
    away_ml = game.get("away_ml", {})
    if isinstance(home_ml, dict) and isinstance(away_ml, dict):
        pin_h = home_ml.get("pinnacle")
        pin_a = away_ml.get("pinnacle")
        if pin_h is not None and pin_a is not None:
            fair_h, fair_a = devig_pinnacle(pin_h, pin_a)
            if fair_h is not None:
                home_won = home_score > away_score

                for book, odds in home_ml.items():
                    if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                        continue
                    try:
                        dec = american_to_decimal(odds)
                        imp = decimal_to_implied(dec)
                    except:
                        continue
                    edge = fair_h - imp
                    ev = fair_h * (dec - 1) - (1 - fair_h)
                    if edge >= min_edge and ev >= 0.01:
                        kf = kelly_fraction(fair_h, dec)
                        br = bankroll or 1000
                        stake = min(br * kf, br * 0.02)
                        if stake < 1:
                            continue
                        pnl = stake * (dec - 1) if home_won else -stake
                        bets.append({
                            "sport": sport, "game": game_name, "market": "moneyline",
                            "side": "home", "book": book, "odds": odds,
                            "edge": round(edge, 4), "ev": round(ev, 4),
                            "won": home_won, "stake": round(stake, 2),
                            "pnl": round(pnl, 2), "fair": round(fair_h, 4),
                            "score": f"{away_score}-{home_score}",
                        })

                for book, odds in away_ml.items():
                    if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                        continue
                    try:
                        dec = american_to_decimal(odds)
                        imp = decimal_to_implied(dec)
                    except:
                        continue
                    edge = fair_a - imp
                    ev = fair_a * (dec - 1) - (1 - fair_a)
                    if edge >= min_edge and ev >= 0.01:
                        kf = kelly_fraction(fair_a, dec)
                        br = bankroll or 1000
                        stake = min(br * kf, br * 0.02)
                        if stake < 1:
                            continue
                        pnl = stake * (dec - 1) if not home_won else -stake
                        bets.append({
                            "sport": sport, "game": game_name, "market": "moneyline",
                            "side": "away", "book": book, "odds": odds,
                            "edge": round(edge, 4), "ev": round(ev, 4),
                            "won": not home_won, "stake": round(stake, 2),
                            "pnl": round(pnl, 2), "fair": round(fair_a, 4),
                            "score": f"{away_score}-{home_score}",
                        })

    # TOTALS
    totals = game.get("total", {})
    over_odds = game.get("over_odds", {})
    under_odds = game.get("under_odds", {})
    if isinstance(over_odds, dict) and isinstance(under_odds, dict):
        pin_o = over_odds.get("pinnacle")
        pin_u = under_odds.get("pinnacle")
        pin_t = totals.get("pinnacle") if isinstance(totals, dict) else totals
        if pin_o is not None and pin_u is not None and pin_t is not None:
            fair_o, fair_u = devig_pinnacle(pin_o, pin_u)
            if fair_o is not None:
                for book, odds in over_odds.items():
                    if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                        continue
                    bt = totals.get(book, pin_t) if isinstance(totals, dict) else totals
                    if bt is None or bt != pin_t:
                        continue
                    try:
                        dec = american_to_decimal(odds)
                        imp = decimal_to_implied(dec)
                    except:
                        continue
                    edge = fair_o - imp
                    ev = fair_o * (dec - 1) - (1 - fair_o)
                    if edge >= min_edge and ev >= 0.01:
                        if total_score == pin_t:
                            continue
                        won = total_score > pin_t
                        kf = kelly_fraction(fair_o, dec)
                        br = bankroll or 1000
                        stake = min(br * kf, br * 0.02)
                        if stake < 1:
                            continue
                        pnl = stake * (dec - 1) if won else -stake
                        bets.append({
                            "sport": sport, "game": game_name, "market": "total",
                            "side": f"over {pin_t}", "book": book, "odds": odds,
                            "edge": round(edge, 4), "ev": round(ev, 4),
                            "won": won, "stake": round(stake, 2),
                            "pnl": round(pnl, 2), "fair": round(fair_o, 4),
                            "score": f"{total_score}",
                        })

                for book, odds in under_odds.items():
                    if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                        continue
                    bt = totals.get(book, pin_t) if isinstance(totals, dict) else totals
                    if bt is None or bt != pin_t:
                        continue
                    try:
                        dec = american_to_decimal(odds)
                        imp = decimal_to_implied(dec)
                    except:
                        continue
                    edge = fair_u - imp
                    ev = fair_u * (dec - 1) - (1 - fair_u)
                    if edge >= min_edge and ev >= 0.01:
                        if total_score == pin_t:
                            continue
                        won = total_score < pin_t
                        kf = kelly_fraction(fair_u, dec)
                        br = bankroll or 1000
                        stake = min(br * kf, br * 0.02)
                        if stake < 1:
                            continue
                        pnl = stake * (dec - 1) if won else -stake
                        bets.append({
                            "sport": sport, "game": game_name, "market": "total",
                            "side": f"under {pin_t}", "book": book, "odds": odds,
                            "edge": round(edge, 4), "ev": round(ev, 4),
                            "won": won, "stake": round(stake, 2),
                            "pnl": round(pnl, 2), "fair": round(fair_u, 4),
                            "score": f"{total_score}",
                        })

    # SPREADS
    hs = game.get("home_spread", {})
    hso = game.get("home_spread_odds", {})
    aws = game.get("away_spread", {})
    aso = game.get("away_spread_odds", {})
    if isinstance(hso, dict) and isinstance(aso, dict):
        pin_ho = hso.get("pinnacle")
        pin_ao = aso.get("pinnacle")
        pin_hl = hs.get("pinnacle") if isinstance(hs, dict) else None
        if all(x is not None for x in [pin_ho, pin_ao, pin_hl]):
            fair_h, fair_a = devig_pinnacle(pin_ho, pin_ao)
            if fair_h is not None:
                margin = home_score - away_score

                for book, odds in hso.items():
                    if book in ("consensus", "pinnacle", "lowvig") or odds is None:
                        continue
                    bl = hs.get(book) if isinstance(hs, dict) else None
                    if bl is None or bl != pin_hl:
                        continue
                    try:
                        dec = american_to_decimal(odds)
                        imp = decimal_to_implied(dec)
                    except:
                        continue
                    edge = fair_h - imp
                    ev = fair_h * (dec - 1) - (1 - fair_h)
                    if edge >= min_edge and ev >= 0.01:
                        result = margin + pin_hl
                        if result == 0:
                            continue
                        won = result > 0
                        kf = kelly_fraction(fair_h, dec)
                        br = bankroll or 1000
                        stake = min(br * kf, br * 0.02)
                        if stake < 1:
                            continue
                        pnl = stake * (dec - 1) if won else -stake
                        bets.append({
                            "sport": sport, "game": game_name, "market": "spread",
                            "side": f"home {pin_hl:+.1f}", "book": book, "odds": odds,
                            "edge": round(edge, 4), "ev": round(ev, 4),
                            "won": won, "stake": round(stake, 2),
                            "pnl": round(pnl, 2), "fair": round(fair_h, 4),
                            "score": f"{away_score}-{home_score}",
                        })

    return bets


def run_backtest(days=30, sports=None, min_edge=0.02):
    """Run multi-day backtest across sports."""
    if sports is None:
        sports = ["NBA", "MLB", "NHL"]

    print(f"\n{'='*70}")
    print(f"  HISTORICAL GAME LINE BACKTEST")
    print(f"  Days: {days} | Sports: {', '.join(sports)} | Min edge: {min_edge:.0%}")
    print(f"{'='*70}")

    all_bets = []
    bankroll = 1000.0
    daily_results = []
    errors = 0

    today = datetime.now(timezone.utc).date()

    for day_offset in range(days, 0, -1):
        date = today - timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")
        day_bets = []

        for sport in sports:
            try:
                sb = Scoreboard(sport, date=date_str)
                games = sb.games
                completed = [g for g in games if g.get("status") == "complete"]

                for game in completed:
                    bets = process_game(game, sport, min_edge, bankroll)
                    for bet in bets:
                        bankroll += bet["pnl"]
                        bet["bankroll"] = round(bankroll, 2)
                        bet["date"] = date_str
                        day_bets.append(bet)
                        all_bets.append(bet)

                time.sleep(0.3)  # Rate limit
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  [{date_str}] [{sport}] Error: {e}")
                continue

        if day_bets:
            wins = sum(1 for b in day_bets if b["won"])
            pnl = sum(b["pnl"] for b in day_bets)
            daily_results.append({
                "date": date_str,
                "bets": len(day_bets),
                "wins": wins,
                "pnl": round(pnl, 2),
                "bankroll": round(bankroll, 2),
            })
            print(f"  {date_str}: {len(day_bets)} bets, {wins}W/{len(day_bets)-wins}L, "
                  f"${pnl:+.2f}, bankroll=${bankroll:.2f}")
        else:
            daily_results.append({
                "date": date_str, "bets": 0, "wins": 0, "pnl": 0, "bankroll": round(bankroll, 2),
            })

    # Summary
    print(f"\n{'='*70}")
    print(f"  RESULTS ({days} days)")
    print(f"{'='*70}")

    if all_bets:
        total_wins = sum(1 for b in all_bets if b["won"])
        total_staked = sum(b["stake"] for b in all_bets)
        total_pnl = bankroll - 1000
        roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

        print(f"  Total bets: {len(all_bets)}")
        print(f"  Win rate: {total_wins}/{len(all_bets)} ({total_wins/len(all_bets)*100:.1f}%)")
        print(f"  Total staked: ${total_staked:.2f}")
        print(f"  P&L: ${total_pnl:+.2f}")
        print(f"  ROI: {roi:+.1f}%")
        print(f"  Final bankroll: ${bankroll:.2f} (started $1000)")

        # By sport
        print(f"\n  BY SPORT:")
        by_sport = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in all_bets:
            by_sport[b["sport"]]["n"] += 1
            by_sport[b["sport"]]["w"] += 1 if b["won"] else 0
            by_sport[b["sport"]]["pnl"] += b["pnl"]
            by_sport[b["sport"]]["stk"] += b["stake"]
        for s, d in sorted(by_sport.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {s}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By market
        print(f"\n  BY MARKET:")
        by_mkt = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in all_bets:
            by_mkt[b["market"]]["n"] += 1
            by_mkt[b["market"]]["w"] += 1 if b["won"] else 0
            by_mkt[b["market"]]["pnl"] += b["pnl"]
            by_mkt[b["market"]]["stk"] += b["stake"]
        for m, d in sorted(by_mkt.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {m}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By book
        print(f"\n  BY BOOK:")
        by_book = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in all_bets:
            by_book[b["book"]]["n"] += 1
            by_book[b["book"]]["w"] += 1 if b["won"] else 0
            by_book[b["book"]]["pnl"] += b["pnl"]
            by_book[b["book"]]["stk"] += b["stake"]
        for bk, d in sorted(by_book.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {bk}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By edge bucket
        print(f"\n  BY EDGE BUCKET:")
        for lo, hi, label in [(0.02, 0.03, "2-3%"), (0.03, 0.04, "3-4%"),
                               (0.04, 0.06, "4-6%"), (0.06, 0.10, "6-10%"),
                               (0.10, 1.0, "10%+")]:
            bucket = [b for b in all_bets if lo <= b["edge"] < hi]
            if bucket:
                bw = sum(1 for b in bucket if b["won"])
                bp = sum(b["pnl"] for b in bucket)
                bs = sum(b["stake"] for b in bucket)
                br = bp/bs*100 if bs else 0
                print(f"    {label}: {len(bucket)} bets, {bw/len(bucket)*100:.0f}% WR, "
                      f"${bp:+.2f} ({br:+.1f}% ROI)")

        # Bankroll curve
        print(f"\n  BANKROLL CURVE:")
        for dr in daily_results:
            if dr["bets"] > 0:
                bar = "+" * max(0, int(dr["pnl"] / 5)) if dr["pnl"] > 0 else "-" * max(0, int(-dr["pnl"] / 5))
                print(f"    {dr['date']}: ${dr['bankroll']:.0f} ({dr['bets']} bets, ${dr['pnl']:+.0f}) {bar}")

    else:
        print("  No bets found")

    # Save results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {"days": days, "sports": sports, "min_edge": min_edge},
        "summary": {
            "total_bets": len(all_bets),
            "win_rate": sum(1 for b in all_bets if b["won"]) / len(all_bets) if all_bets else 0,
            "pnl": round(bankroll - 1000, 2),
            "roi": round((bankroll - 1000) / max(1, sum(b["stake"] for b in all_bets)) * 100, 2) if all_bets else 0,
            "final_bankroll": round(bankroll, 2),
        },
        "daily": daily_results,
        "bets": all_bets[-100:],  # Last 100 bets
        "errors": errors,
    }
    outpath = os.path.join(DATA_DIR, "historical_backtest.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Saved to {outpath}")

    return results


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    sports = sys.argv[2].split(",") if len(sys.argv) > 2 else ["NBA", "MLB", "NHL"]
    min_edge = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
    run_backtest(days, sports, min_edge)

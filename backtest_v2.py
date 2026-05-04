"""
Sports Edge - Backtester V2 (Fixed Deduplication)

SBR returns ALL completed games in a window regardless of date parameter.
This version queries once per sport and uses each game's own date field.

Tests multiple strategy configurations side-by-side.
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


def find_bets(game, sport, min_edge=0.02, max_edge=1.0,
              excluded_books=None, markets=None, kelly_frac=0.25, max_bet_pct=0.02):
    """Find +EV bets in a single game."""
    if excluded_books is None:
        excluded_books = {"consensus", "pinnacle", "lowvig"}
    if markets is None:
        markets = ["moneyline", "total"]

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
    if "moneyline" in markets:
        home_ml = game.get("home_ml", {})
        away_ml = game.get("away_ml", {})
        if isinstance(home_ml, dict) and isinstance(away_ml, dict):
            pin_h = home_ml.get("pinnacle")
            pin_a = away_ml.get("pinnacle")
            if pin_h is not None and pin_a is not None:
                fair_h, fair_a = devig_pinnacle(pin_h, pin_a)
                if fair_h is not None:
                    home_won = home_score > away_score

                    for side, ml_dict, fair, won in [
                        ("home", home_ml, fair_h, home_won),
                        ("away", away_ml, fair_a, not home_won)
                    ]:
                        for book, odds in ml_dict.items():
                            if book in excluded_books or odds is None:
                                continue
                            try:
                                dec = american_to_decimal(odds)
                                imp = decimal_to_implied(dec)
                            except:
                                continue
                            edge = fair - imp
                            ev = fair * (dec - 1) - (1 - fair)
                            if min_edge <= edge < max_edge and ev >= 0.01:
                                kf = kelly_fraction(fair, dec, kelly_frac)
                                stake = min(1000 * kf, 1000 * max_bet_pct)
                                if stake < 1:
                                    continue
                                pnl = stake * (dec - 1) if won else -stake
                                bets.append({
                                    "sport": sport, "game": game_name, "market": "moneyline",
                                    "side": side, "book": book, "odds": odds,
                                    "edge": round(edge, 4), "ev": round(ev, 4),
                                    "won": won, "stake": round(stake, 2),
                                    "pnl": round(pnl, 2), "fair": round(fair, 4),
                                    "score": f"{away_score}-{home_score}",
                                })

    # TOTALS
    if "total" in markets:
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
                    for side_name, odds_dict, fair, check_won in [
                        ("over", over_odds, fair_o, lambda: total_score > pin_t),
                        ("under", under_odds, fair_u, lambda: total_score < pin_t),
                    ]:
                        for book, odds in odds_dict.items():
                            if book in excluded_books or odds is None:
                                continue
                            bt = totals.get(book, pin_t) if isinstance(totals, dict) else totals
                            if bt is None or bt != pin_t:
                                continue
                            try:
                                dec = american_to_decimal(odds)
                                imp = decimal_to_implied(dec)
                            except:
                                continue
                            edge = fair - imp
                            ev = fair * (dec - 1) - (1 - fair)
                            if min_edge <= edge < max_edge and ev >= 0.01:
                                if total_score == pin_t:
                                    continue
                                won = check_won()
                                kf = kelly_fraction(fair, dec, kelly_frac)
                                stake = min(1000 * kf, 1000 * max_bet_pct)
                                if stake < 1:
                                    continue
                                pnl = stake * (dec - 1) if won else -stake
                                bets.append({
                                    "sport": sport, "game": game_name, "market": "total",
                                    "side": f"{side_name} {pin_t}", "book": book, "odds": odds,
                                    "edge": round(edge, 4), "ev": round(ev, 4),
                                    "won": won, "stake": round(stake, 2),
                                    "pnl": round(pnl, 2), "fair": round(fair, 4),
                                    "score": str(total_score),
                                })

    # SPREADS
    if "spread" in markets:
        hs = game.get("home_spread", {})
        hso = game.get("home_spread_odds", {})
        aso = game.get("away_spread_odds", {})
        if isinstance(hso, dict) and isinstance(aso, dict):
            pin_ho = hso.get("pinnacle")
            pin_ao = aso.get("pinnacle")
            pin_hl = hs.get("pinnacle") if isinstance(hs, dict) else None
            if all(x is not None for x in [pin_ho, pin_ao, pin_hl]):
                fair_h, _ = devig_pinnacle(pin_ho, pin_ao)
                if fair_h is not None:
                    margin = home_score - away_score
                    for book, odds in hso.items():
                        if book in excluded_books or odds is None:
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
                        if min_edge <= edge < max_edge and ev >= 0.01:
                            result = margin + pin_hl
                            if result == 0:
                                continue
                            won = result > 0
                            kf = kelly_fraction(fair_h, dec, kelly_frac)
                            stake = min(1000 * kf, 1000 * max_bet_pct)
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


STRATEGIES = {
    "v1_all": {
        "name": "V1: All sports, 2%+ edge, all books",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.02, "max_edge": 1.0,
        "excluded_books": {"consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total", "spread"],
    },
    "v2a_edge_filter": {
        "name": "V2a: All sports, 3-6% edge, all books",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.03, "max_edge": 0.06,
        "excluded_books": {"consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total"],
    },
    "v2b_book_filter": {
        "name": "V2b: All sports, 3-6% edge, no bodog",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.03, "max_edge": 0.06,
        "excluded_books": {"consensus", "pinnacle", "lowvig", "bodog"},
        "markets": ["moneyline", "total"],
    },
    "v2c_nhl_only": {
        "name": "V2c: NHL only, 3-6% edge",
        "sports": ["NHL"],
        "min_edge": 0.03, "max_edge": 0.06,
        "excluded_books": {"consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total"],
    },
    "v2d_selective": {
        "name": "V2d: All sports, 3-5% edge, select books",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.03, "max_edge": 0.05,
        "excluded_books": {"consensus", "pinnacle", "lowvig", "bodog", "bovada", "betonline"},
        "markets": ["moneyline", "total"],
    },
    "v2e_wider": {
        "name": "V2e: All sports, 2.5-5% edge, no bodog",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.025, "max_edge": 0.05,
        "excluded_books": {"consensus", "pinnacle", "lowvig", "bodog"},
        "markets": ["moneyline", "total"],
    },
}


def run_backtest():
    """Run all strategies on deduplicated game data."""
    print(f"\n{'='*70}")
    print(f"  BACKTESTER V2 - DEDUPLICATED")
    print(f"{'='*70}")

    # Step 1: Collect ALL games, deduplicated by game signature
    print(f"\n  Loading games from SBR...")
    all_games = {}  # key: "sport|away@home|score" -> game dict

    for sport in ["NBA", "MLB", "NHL"]:
        try:
            sb = Scoreboard(sport)
            completed = [g for g in sb.games if g.get("status") == "complete"]
            for g in completed:
                away = g.get("away_team", "")
                home = g.get("home_team", "")
                ascore = g.get("away_score", "")
                hscore = g.get("home_score", "")
                game_date = g.get("date", "")[:10]
                # Unique key: sport + teams + score + date
                key = f"{sport}|{away}@{home}|{ascore}-{hscore}|{game_date}"
                if key not in all_games:
                    all_games[key] = (sport, game_date, g)
            print(f"  {sport}: {len(completed)} completed, {len([k for k in all_games if k.startswith(sport)])} unique")
            time.sleep(0.5)
        except Exception as e:
            print(f"  {sport} error: {e}")

    # Group by date
    games_by_date = defaultdict(list)
    for key, (sport, date, game) in all_games.items():
        games_by_date[date].append((sport, game))

    dates = sorted(games_by_date.keys())
    print(f"\n  Total unique games: {len(all_games)}")
    print(f"  Date range: {dates[0] if dates else 'none'} to {dates[-1] if dates else 'none'}")
    print(f"  Days with games: {len(dates)}")
    for d in dates:
        sports_count = defaultdict(int)
        for s, _ in games_by_date[d]:
            sports_count[s] += 1
        sc = ", ".join(f"{s}:{n}" for s, n in sorted(sports_count.items()))
        print(f"    {d}: {len(games_by_date[d])} games ({sc})")

    # Step 2: Run each strategy
    print(f"\n{'='*70}")
    print(f"  RUNNING {len(STRATEGIES)} STRATEGIES")
    print(f"{'='*70}")

    results = {}
    for strat_key, cfg in STRATEGIES.items():
        bankroll = 1000.0
        all_bets = []
        daily = []

        for date in dates:
            day_bets = []
            for sport, game in games_by_date[date]:
                if sport not in cfg["sports"]:
                    continue
                bets = find_bets(
                    game, sport,
                    min_edge=cfg["min_edge"],
                    max_edge=cfg["max_edge"],
                    excluded_books=cfg["excluded_books"],
                    markets=cfg["markets"],
                )
                for bet in bets:
                    bankroll += bet["pnl"]
                    bet["date"] = date
                    bet["bankroll"] = round(bankroll, 2)
                    day_bets.append(bet)
                    all_bets.append(bet)

            if day_bets:
                wins = sum(1 for b in day_bets if b["won"])
                pnl = sum(b["pnl"] for b in day_bets)
                daily.append({"date": date, "bets": len(day_bets), "wins": wins, "pnl": round(pnl, 2)})

        total_staked = sum(b["stake"] for b in all_bets) if all_bets else 0
        total_pnl = bankroll - 1000
        total_wins = sum(1 for b in all_bets if b["won"])
        roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

        results[strat_key] = {
            "name": cfg["name"],
            "bets": len(all_bets),
            "wins": total_wins,
            "win_rate": round(total_wins / len(all_bets) * 100, 1) if all_bets else 0,
            "pnl": round(total_pnl, 2),
            "roi": round(roi, 2),
            "bankroll": round(bankroll, 2),
            "staked": round(total_staked, 2),
            "daily": daily,
            "all_bets": all_bets,
        }

    # Print comparison table
    print(f"\n{'='*70}")
    print(f"  STRATEGY COMPARISON")
    print(f"{'='*70}")
    print(f"\n  {'Strategy':<42} {'Bets':>5} {'WR':>6} {'Staked':>8} {'P&L':>10} {'ROI':>8}")
    print(f"  {'-'*42} {'-'*5} {'-'*6} {'-'*8} {'-'*10} {'-'*8}")

    for key, res in sorted(results.items(), key=lambda x: -x[1]["roi"]):
        print(f"  {res['name']:<42} {res['bets']:>5} {res['win_rate']:>5.0f}% "
              f"${res['staked']:>7.0f} ${res['pnl']:>+8.2f} {res['roi']:>+6.1f}%")

    # Detailed breakdown of top 3 strategies
    top3 = sorted(results.items(), key=lambda x: -x[1]["roi"])[:3]
    for key, res in top3:
        if not res["all_bets"]:
            continue

        print(f"\n{'='*70}")
        print(f"  DETAIL: {res['name']}")
        print(f"  {res['bets']} bets, {res['win_rate']:.0f}% WR, ${res['pnl']:+.2f} ({res['roi']:+.1f}% ROI)")
        print(f"{'='*70}")

        # By sport
        print(f"\n  By Sport:")
        by_sport = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in res["all_bets"]:
            by_sport[b["sport"]]["n"] += 1
            by_sport[b["sport"]]["w"] += 1 if b["won"] else 0
            by_sport[b["sport"]]["pnl"] += b["pnl"]
            by_sport[b["sport"]]["stk"] += b["stake"]
        for s, d in sorted(by_sport.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {s}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By book
        print(f"\n  By Book:")
        by_book = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in res["all_bets"]:
            by_book[b["book"]]["n"] += 1
            by_book[b["book"]]["w"] += 1 if b["won"] else 0
            by_book[b["book"]]["pnl"] += b["pnl"]
            by_book[b["book"]]["stk"] += b["stake"]
        for bk, d in sorted(by_book.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {bk}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By market
        print(f"\n  By Market:")
        by_mkt = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in res["all_bets"]:
            by_mkt[b["market"]]["n"] += 1
            by_mkt[b["market"]]["w"] += 1 if b["won"] else 0
            by_mkt[b["market"]]["pnl"] += b["pnl"]
            by_mkt[b["market"]]["stk"] += b["stake"]
        for m, d in sorted(by_mkt.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {m}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # By edge bucket
        print(f"\n  By Edge Bucket:")
        for lo, hi, label in [(0.02, 0.025, "2-2.5%"), (0.025, 0.03, "2.5-3%"),
                               (0.03, 0.04, "3-4%"), (0.04, 0.06, "4-6%"),
                               (0.06, 0.10, "6-10%"), (0.10, 1.0, "10%+")]:
            bucket = [b for b in res["all_bets"] if lo <= b["edge"] < hi]
            if bucket:
                bw = sum(1 for b in bucket if b["won"])
                bp = sum(b["pnl"] for b in bucket)
                bs = sum(b["stake"] for b in bucket)
                br = bp/bs*100 if bs else 0
                print(f"    {label}: {len(bucket)} bets, {bw/len(bucket)*100:.0f}% WR, "
                      f"${bp:+.2f} ({br:+.1f}% ROI)")

        # Individual bets
        print(f"\n  All Bets:")
        for b in res["all_bets"]:
            won_str = "W" if b["won"] else "L"
            print(f"    {b['date']} [{b['sport']}] {b['game']} | {b['market']} {b['side']} "
                  f"@ {b['book']} {b['odds']} | edge={b['edge']:.1%} | {won_str} ${b['pnl']:+.2f}")

    # Save
    save = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "game_dates": dates,
        "total_games": len(all_games),
        "strategies": {k: {kk: vv for kk, vv in v.items() if kk != "all_bets"}
                       for k, v in results.items()},
    }
    outpath = os.path.join(DATA_DIR, "backtest_v2.json")
    with open(outpath, "w") as f:
        json.dump(save, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")

    return results


if __name__ == "__main__":
    run_backtest()

"""
Sports Edge - Refined Strategy Engine

Applies backtest learnings to filter bets for maximum profitability:

FILTERS (from 14-day backtest of 188 bets):
1. NHL only (was +16.5% ROI vs NBA -33.7%, MLB -23.9%)
2. Edge 3-6% sweet spot (3-4% was +84% ROI, 2-3% was -25.8%, 6%+ all losers)
3. Exclude bodog (131 bets, -23.5% ROI -- likely stale lines)
4. Prefer unibet, sportsbetting (combined +137.8% and +105% ROI)
5. Cap max edge at 6% (anything higher = stale line, not real edge)
6. Totals only for secondary (ML was -13.7% overall, totals -8.4%)

Also runs: full-spectrum scan with v1 rules for comparison.
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


# Strategy configs
STRATEGIES = {
    "v2_refined": {
        "name": "V2 Refined (NHL + edge 3-6% + book filter)",
        "sports": ["NHL"],
        "min_edge": 0.03,
        "max_edge": 0.06,
        "excluded_books": {"bodog", "bovada", "betonline", "consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total"],  # both, but NHL ML is profitable
        "kelly_frac": 0.25,
        "max_bet_pct": 0.02,
    },
    "v2_nhl_all_books": {
        "name": "V2 NHL All Books (edge 3-6%)",
        "sports": ["NHL"],
        "min_edge": 0.03,
        "max_edge": 0.06,
        "excluded_books": {"consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total"],
        "kelly_frac": 0.25,
        "max_bet_pct": 0.02,
    },
    "v2_multi_sport": {
        "name": "V2 Multi-Sport (edge 3-6%, no bodog)",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.03,
        "max_edge": 0.06,
        "excluded_books": {"bodog", "consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total"],
        "kelly_frac": 0.25,
        "max_bet_pct": 0.02,
    },
    "v1_original": {
        "name": "V1 Original (all sports, edge 2%+, all books)",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.02,
        "max_edge": 1.0,
        "excluded_books": {"consensus", "pinnacle", "lowvig"},
        "markets": ["moneyline", "total", "spread"],
        "kelly_frac": 0.25,
        "max_bet_pct": 0.02,
    },
    "v2_totals_only": {
        "name": "V2 Totals Only (all sports, edge 3-5%)",
        "sports": ["NBA", "MLB", "NHL"],
        "min_edge": 0.03,
        "max_edge": 0.05,
        "excluded_books": {"bodog", "consensus", "pinnacle", "lowvig"},
        "markets": ["total"],
        "kelly_frac": 0.25,
        "max_bet_pct": 0.02,
    },
}


def process_game(game, sport, strategy):
    """Process game using strategy config. Returns list of bets."""
    bets = []
    cfg = strategy
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
    if "moneyline" in cfg["markets"]:
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
                        if book in cfg["excluded_books"] or odds is None:
                            continue
                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except:
                            continue
                        edge = fair_h - imp
                        ev = fair_h * (dec - 1) - (1 - fair_h)
                        if cfg["min_edge"] <= edge < cfg["max_edge"] and ev >= 0.01:
                            kf = kelly_fraction(fair_h, dec, cfg["kelly_frac"])
                            stake = min(1000 * kf, 1000 * cfg["max_bet_pct"])
                            if stake < 1:
                                continue
                            pnl = stake * (dec - 1) if home_won else -stake
                            bets.append({
                                "sport": sport, "game": game_name, "market": "moneyline",
                                "side": "home", "book": book, "odds": odds,
                                "edge": round(edge, 4), "ev": round(ev, 4),
                                "won": home_won, "stake": round(stake, 2),
                                "pnl": round(pnl, 2), "fair": round(fair_h, 4),
                            })

                    for book, odds in away_ml.items():
                        if book in cfg["excluded_books"] or odds is None:
                            continue
                        try:
                            dec = american_to_decimal(odds)
                            imp = decimal_to_implied(dec)
                        except:
                            continue
                        edge = fair_a - imp
                        ev = fair_a * (dec - 1) - (1 - fair_a)
                        if cfg["min_edge"] <= edge < cfg["max_edge"] and ev >= 0.01:
                            kf = kelly_fraction(fair_a, dec, cfg["kelly_frac"])
                            stake = min(1000 * kf, 1000 * cfg["max_bet_pct"])
                            if stake < 1:
                                continue
                            pnl = stake * (dec - 1) if not home_won else -stake
                            bets.append({
                                "sport": sport, "game": game_name, "market": "moneyline",
                                "side": "away", "book": book, "odds": odds,
                                "edge": round(edge, 4), "ev": round(ev, 4),
                                "won": not home_won, "stake": round(stake, 2),
                                "pnl": round(pnl, 2), "fair": round(fair_a, 4),
                            })

    # TOTALS
    if "total" in cfg["markets"]:
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
                        if book in cfg["excluded_books"] or odds is None:
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
                        if cfg["min_edge"] <= edge < cfg["max_edge"] and ev >= 0.01:
                            if total_score == pin_t:
                                continue
                            won = total_score > pin_t
                            kf = kelly_fraction(fair_o, dec, cfg["kelly_frac"])
                            stake = min(1000 * kf, 1000 * cfg["max_bet_pct"])
                            if stake < 1:
                                continue
                            pnl = stake * (dec - 1) if won else -stake
                            bets.append({
                                "sport": sport, "game": game_name, "market": "total",
                                "side": f"over {pin_t}", "book": book, "odds": odds,
                                "edge": round(edge, 4), "ev": round(ev, 4),
                                "won": won, "stake": round(stake, 2),
                                "pnl": round(pnl, 2), "fair": round(fair_o, 4),
                            })

                    for book, odds in under_odds.items():
                        if book in cfg["excluded_books"] or odds is None:
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
                        if cfg["min_edge"] <= edge < cfg["max_edge"] and ev >= 0.01:
                            if total_score == pin_t:
                                continue
                            won = total_score < pin_t
                            kf = kelly_fraction(fair_u, dec, cfg["kelly_frac"])
                            stake = min(1000 * kf, 1000 * cfg["max_bet_pct"])
                            if stake < 1:
                                continue
                            pnl = stake * (dec - 1) if won else -stake
                            bets.append({
                                "sport": sport, "game": game_name, "market": "total",
                                "side": f"under {pin_t}", "book": book, "odds": odds,
                                "edge": round(edge, 4), "ev": round(ev, 4),
                                "won": won, "stake": round(stake, 2),
                                "pnl": round(pnl, 2), "fair": round(fair_u, 4),
                            })

    # SPREADS
    if "spread" in cfg["markets"]:
        hs = game.get("home_spread", {})
        hso = game.get("home_spread_odds", {})
        if isinstance(hso, dict):
            pin_ho = hso.get("pinnacle")
            aso = game.get("away_spread_odds", {})
            pin_ao = aso.get("pinnacle") if isinstance(aso, dict) else None
            pin_hl = hs.get("pinnacle") if isinstance(hs, dict) else None
            if all(x is not None for x in [pin_ho, pin_ao, pin_hl]):
                fair_h, fair_a = devig_pinnacle(pin_ho, pin_ao)
                if fair_h is not None:
                    margin = home_score - away_score
                    for book, odds in hso.items():
                        if book in cfg["excluded_books"] or odds is None:
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
                        if cfg["min_edge"] <= edge < cfg["max_edge"] and ev >= 0.01:
                            result = margin + pin_hl
                            if result == 0:
                                continue
                            won = result > 0
                            kf = kelly_fraction(fair_h, dec, cfg["kelly_frac"])
                            stake = min(1000 * kf, 1000 * cfg["max_bet_pct"])
                            if stake < 1:
                                continue
                            pnl = stake * (dec - 1) if won else -stake
                            bets.append({
                                "sport": sport, "game": game_name, "market": "spread",
                                "side": f"home {pin_hl:+.1f}", "book": book, "odds": odds,
                                "edge": round(edge, 4), "ev": round(ev, 4),
                                "won": won, "stake": round(stake, 2),
                                "pnl": round(pnl, 2), "fair": round(fair_h, 4),
                            })

    return bets


def run_strategy_comparison(days=14):
    """Run all strategies side-by-side over historical data."""
    today = datetime.now(timezone.utc).date()

    print(f"\n{'='*70}")
    print(f"  STRATEGY COMPARISON BACKTEST")
    print(f"  Days: {days} | Testing {len(STRATEGIES)} strategies")
    print(f"{'='*70}")

    # Collect all game data first
    all_games = {}
    for day_offset in range(days, 0, -1):
        date = today - timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")
        all_games[date_str] = {}

        for sport in ["NBA", "MLB", "NHL"]:
            try:
                sb = Scoreboard(sport, date=date_str)
                games = sb.games
                completed = [g for g in games if g.get("status") == "complete"]
                all_games[date_str][sport] = completed
                time.sleep(0.3)
            except Exception as e:
                all_games[date_str][sport] = []

    # Run each strategy
    results = {}
    for strat_key, cfg in STRATEGIES.items():
        bankroll = 1000.0
        all_bets = []
        daily = []

        for day_offset in range(days, 0, -1):
            date = today - timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            day_bets = []

            for sport in cfg["sports"]:
                games = all_games.get(date_str, {}).get(sport, [])
                for game in games:
                    bets = process_game(game, sport, cfg)
                    for bet in bets:
                        bankroll += bet["pnl"]
                        bet["date"] = date_str
                        bet["bankroll"] = round(bankroll, 2)
                        day_bets.append(bet)
                        all_bets.append(bet)

            if day_bets:
                wins = sum(1 for b in day_bets if b["won"])
                pnl = sum(b["pnl"] for b in day_bets)
                daily.append({"date": date_str, "bets": len(day_bets), "pnl": round(pnl, 2)})

        total_staked = sum(b["stake"] for b in all_bets) if all_bets else 0
        total_pnl = bankroll - 1000
        total_wins = sum(1 for b in all_bets if b["won"])
        roi = total_pnl / total_staked * 100 if total_staked > 0 else 0

        results[strat_key] = {
            "name": cfg["name"],
            "bets": len(all_bets),
            "wins": total_wins,
            "win_rate": total_wins / len(all_bets) * 100 if all_bets else 0,
            "pnl": round(total_pnl, 2),
            "roi": round(roi, 2),
            "bankroll": round(bankroll, 2),
            "daily": daily,
            "all_bets": all_bets,
        }

    # Print comparison
    print(f"\n{'='*70}")
    print(f"  STRATEGY COMPARISON RESULTS ({days} days)")
    print(f"{'='*70}")
    print(f"\n  {'Strategy':<45} {'Bets':>5} {'WR':>6} {'P&L':>10} {'ROI':>8} {'Final':>8}")
    print(f"  {'-'*45} {'-'*5} {'-'*6} {'-'*10} {'-'*8} {'-'*8}")

    for key, res in sorted(results.items(), key=lambda x: -x[1]["roi"]):
        wr = f"{res['win_rate']:.0f}%"
        pnl = f"${res['pnl']:+.2f}"
        roi = f"{res['roi']:+.1f}%"
        final = f"${res['bankroll']:.0f}"
        print(f"  {res['name']:<45} {res['bets']:>5} {wr:>6} {pnl:>10} {roi:>8} {final:>8}")

    # Detailed breakdown of best strategy
    best_key = max(results, key=lambda k: results[k]["roi"])
    best = results[best_key]
    print(f"\n{'='*70}")
    print(f"  BEST STRATEGY: {best['name']}")
    print(f"{'='*70}")
    print(f"  {best['bets']} bets, {best['win_rate']:.0f}% WR, ${best['pnl']:+.2f} ({best['roi']:+.1f}% ROI)")

    if best["all_bets"]:
        # By book
        print(f"\n  By Book:")
        by_book = defaultdict(lambda: {"n": 0, "w": 0, "pnl": 0, "stk": 0})
        for b in best["all_bets"]:
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
        for b in best["all_bets"]:
            by_mkt[b["market"]]["n"] += 1
            by_mkt[b["market"]]["w"] += 1 if b["won"] else 0
            by_mkt[b["market"]]["pnl"] += b["pnl"]
            by_mkt[b["market"]]["stk"] += b["stake"]
        for m, d in sorted(by_mkt.items(), key=lambda x: -x[1]["pnl"]):
            wr = d["w"]/d["n"]*100 if d["n"] else 0
            r = d["pnl"]/d["stk"]*100 if d["stk"] else 0
            print(f"    {m}: {d['n']} bets, {wr:.0f}% WR, ${d['pnl']:+.2f} ({r:+.1f}% ROI)")

        # Daily P&L
        print(f"\n  Daily P&L:")
        for d in best["daily"]:
            bar = "+" * max(0, int(d["pnl"] / 3)) if d["pnl"] > 0 else "-" * max(0, int(-d["pnl"] / 3))
            print(f"    {d['date']}: {d['bets']} bets, ${d['pnl']:+.2f} {bar}")

    # Save all results
    save = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "strategies": {k: {kk: vv for kk, vv in v.items() if kk != "all_bets"}
                       for k, v in results.items()},
        "best_strategy": best_key,
        "best_bets": best["all_bets"][-50:] if best["all_bets"] else [],
    }
    outpath = os.path.join(DATA_DIR, "strategy_comparison.json")
    with open(outpath, "w") as f:
        json.dump(save, f, indent=2, default=str)
    print(f"\n  Saved to {outpath}")

    return results


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    run_strategy_comparison(days)

"""
Sports Edge - Kalman + Monte Carlo Backtester
Tests the upgraded prediction engine against our full season of real data.
Compares: Old weighted average vs Kalman filter vs Kalman+MonteCarlo
"""
import json
import os
import sys
import random
from collections import defaultdict
from kalman_model import (
    KalmanPredictor, monte_carlo_probability, calculate_edge,
    kelly_fraction, american_to_decimal
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
random.seed(42)  # Reproducible Monte Carlo results


def load_data():
    """Load full season backtest results and box score history."""
    # Load matched props
    with open(os.path.join(DATA_DIR, "real_backtest_full_season.json")) as f:
        props_data = json.load(f)

    # Load all box scores to build chronological player history
    history = defaultdict(list)
    box_files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith("box_"))

    for bf in box_files:
        with open(os.path.join(DATA_DIR, bf)) as f:
            data = json.load(f)

        game = data.get("game", {})
        game_date = game.get("gameTimeUTC", "")[:10]
        if not game_date:
            continue

        for tk in ["homeTeam", "awayTeam"]:
            team = game.get(tk, {})
            for p in team.get("players", []):
                s = p.get("statistics", {})
                mins_str = s.get("minutes", "PT00M")
                mins = 0
                try:
                    mins = int(mins_str.split("T")[1].split("M")[0])
                except:
                    pass
                if mins == 0:
                    continue

                name = p.get("name", "").lower()
                history[name].append({
                    "date": game_date,
                    "pts": s.get("points", 0),
                    "reb": s.get("reboundsTotal", 0),
                    "ast": s.get("assists", 0),
                    "fg3m": s.get("threePointersMade", 0),
                    "min": mins,
                })

    # Sort each player's history
    for name in history:
        history[name].sort(key=lambda x: x["date"])

    return props_data, history


def old_weighted_average(games, stat, lookback=10):
    """The old prediction model for comparison."""
    if len(games) < 5:
        return None

    recent = games[-lookback:] if len(games) >= lookback else games
    total_w = 0
    weighted_sum = 0
    for i, game in enumerate(recent):
        weight = 1 + (i / len(recent))
        weighted_sum += game.get(stat, 0) * weight
        total_w += weight
    recent_avg = weighted_sum / total_w if total_w > 0 else 0
    season_avg = sum(g.get(stat, 0) for g in games) / len(games)
    return season_avg * 0.35 + recent_avg * 0.65


def run_old_model(props, history, min_edge_pct=5, sizing="flat", unit=100):
    """Run the old weighted average model for comparison."""
    bets = []
    bankroll = 5000
    start = bankroll

    by_date = defaultdict(list)
    for r in props:
        by_date[r["date"]].append(r)

    for date in sorted(by_date.keys()):
        seen = set()
        for prop in by_date[date]:
            key = f"{prop['player']}_{prop['stat']}"
            if key in seen:
                continue
            seen.add(key)

            player_key = prop["player"].lower()
            player_hist = history.get(player_key, [])
            prior = [g for g in player_hist if g["date"] < prop["date"]]
            if len(prior) < 5:
                continue

            avg_min = sum(g["min"] for g in prior[-10:]) / min(10, len(prior))
            if avg_min < 20:
                continue

            pred = old_weighted_average(prior, prop["stat"])
            if pred is None:
                continue

            line = prop["line"]
            edge_pct = abs(pred - line) / line * 100 if line > 0 else 0
            if edge_pct < min_edge_pct:
                continue

            if pred < line:
                side = "under"
                odds = prop["under_odds"]
            else:
                side = "over"
                odds = prop["over_odds"]

            bet_amount = unit
            won = prop["over_won"] if side == "over" else prop["under_won"]
            push = prop["push"]

            if push:
                pnl = 0
            elif won:
                pnl = bet_amount * (american_to_decimal(odds) - 1)
            else:
                pnl = -bet_amount

            bankroll += pnl
            bets.append({
                "date": date, "player": prop["player"], "stat": prop["stat"],
                "line": line, "pred": round(pred, 2), "edge_pct": round(edge_pct, 1),
                "side": side, "actual": prop["actual"], "won": won, "push": push,
                "odds": odds, "bet": bet_amount, "pnl": round(pnl, 2),
            })

    return bets, bankroll, start


def run_kalman_model(props, history, min_edge=0.03, use_monte_carlo=True,
                     sizing="flat", unit=100, kelly_frac=0.25, bankroll_start=5000):
    """
    Run the Kalman filter (+ optional Monte Carlo) prediction engine.

    min_edge: minimum edge as decimal (0.03 = 3%)
    use_monte_carlo: if True, use MC simulation for probability; if False, use normal CDF approx
    """
    predictor = KalmanPredictor()
    bets = []
    bankroll = bankroll_start
    start = bankroll

    # First pass: feed all historical games into Kalman filters chronologically
    # We need to process games in date order, updating filters as we go
    all_games_by_date = defaultdict(list)
    for name, games in history.items():
        for g in games:
            all_games_by_date[g["date"]].append((name, g))

    # Also index props by date
    props_by_date = defaultdict(list)
    for r in props:
        props_by_date[r["date"]].append(r)

    all_dates = sorted(set(list(all_games_by_date.keys()) + list(props_by_date.keys())))

    for date in all_dates:
        # FIRST: make predictions for today's props (BEFORE updating with today's results)
        if date in props_by_date:
            seen = set()
            for prop in props_by_date[date]:
                key = f"{prop['player']}_{prop['stat']}"
                if key in seen:
                    continue
                seen.add(key)

                player_key = prop["player"].lower()
                stat = prop["stat"]

                # Check we have enough data
                if predictor.get_n_updates(player_key, stat) < 5:
                    continue

                mean, std = predictor.predict(player_key, stat)
                if mean is None:
                    continue

                line = prop["line"]

                if use_monte_carlo:
                    prob_over, prob_under, prob_push = monte_carlo_probability(
                        mean, std, line, n_sims=5000
                    )
                else:
                    # Normal CDF approximation
                    from math import erf
                    z = (line - mean) / std if std > 0 else 0
                    prob_under = 0.5 * (1 + erf(z / 1.4142))
                    prob_over = 1 - prob_under
                    prob_push = 0.0

                # Calculate edge for both sides
                over_edge, over_implied = calculate_edge(prob_over, prop["over_odds"])
                under_edge, under_implied = calculate_edge(prob_under, prop["under_odds"])

                # Pick the side with more edge
                if over_edge > under_edge and over_edge >= min_edge:
                    side = "over"
                    edge = over_edge
                    prob = prob_over
                    odds = prop["over_odds"]
                elif under_edge >= min_edge:
                    side = "under"
                    edge = under_edge
                    prob = prob_under
                    odds = prop["under_odds"]
                else:
                    continue

                # Bet sizing
                dec_odds = american_to_decimal(odds)
                if sizing == "kelly":
                    kf = kelly_fraction(edge, dec_odds, kelly_frac)
                    bet_amount = round(kf * bankroll, 2)
                    bet_amount = min(bet_amount, bankroll * 0.05)  # Cap at 5% of bankroll
                else:
                    bet_amount = unit

                if bet_amount < 5 or bankroll <= 0:
                    continue

                bet_amount = min(bet_amount, bankroll)

                # Result
                won = prop["over_won"] if side == "over" else prop["under_won"]
                push = prop["push"]

                if push:
                    pnl = 0
                elif won:
                    pnl = bet_amount * (dec_odds - 1)
                else:
                    pnl = -bet_amount

                bankroll += pnl
                bankroll = round(bankroll, 2)

                bets.append({
                    "date": date,
                    "player": prop["player"],
                    "stat": stat,
                    "line": line,
                    "kalman_mean": round(mean, 2),
                    "kalman_std": round(std, 2),
                    "prob": round(prob, 4),
                    "edge": round(edge, 4),
                    "side": side,
                    "actual": prop["actual"],
                    "won": won,
                    "push": push,
                    "odds": odds,
                    "bet": round(bet_amount, 2),
                    "pnl": round(pnl, 2),
                    "bankroll": round(bankroll, 2),
                })

        # THEN: update Kalman filters with today's actual results
        if date in all_games_by_date:
            for name, game in all_games_by_date[date]:
                predictor.update_game(
                    name,
                    game["pts"], game["reb"], game["ast"], game["fg3m"]
                )

    return bets, bankroll, start


def print_summary(name, bets, final_br, start_br):
    """Print strategy summary."""
    if not bets:
        print(f"\n  {name}: No bets placed")
        return

    wins = sum(1 for b in bets if b["won"])
    losses = sum(1 for b in bets if not b["won"] and not b["push"])
    pushes = sum(1 for b in bets if b["push"])
    total_wagered = sum(b["bet"] for b in bets)
    total_pnl = sum(b["pnl"] for b in bets)
    roi = (total_pnl / total_wagered * 100) if total_wagered > 0 else 0

    # Max drawdown
    peak = start_br
    max_dd = 0
    running = start_br
    for b in bets:
        running += b["pnl"]
        if running > peak:
            peak = running
        dd = (peak - running) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)

    # By stat
    stat_data = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0, "n": 0})
    for b in bets:
        sd = stat_data[b["stat"]]
        sd["n"] += 1
        if b["won"]:
            sd["w"] += 1
        elif not b["push"]:
            sd["l"] += 1
        sd["pnl"] += b["pnl"]

    # By edge bucket
    edge_data = defaultdict(lambda: {"w": 0, "l": 0, "n": 0, "pnl": 0})
    for b in bets:
        edge_pct = b.get("edge", b.get("edge_pct", 0))
        if isinstance(edge_pct, float) and edge_pct < 1:
            edge_pct *= 100  # Convert decimal to pct
        bucket = int(edge_pct // 3) * 3
        ed = edge_data[bucket]
        ed["n"] += 1
        if b["won"]:
            ed["w"] += 1
        elif not b["push"]:
            ed["l"] += 1
        ed["pnl"] += b["pnl"]

    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")
    print(f"  Bets:           {len(bets)}")
    print(f"  Win/Loss/Push:  {wins}/{losses}/{pushes}")
    print(f"  Win Rate:       {wins/(wins+losses)*100:.1f}%" if (wins+losses) > 0 else "  Win Rate: N/A")
    print(f"  Total Wagered:  ${total_wagered:,.0f}")
    print(f"  Total P/L:      ${total_pnl:+,.0f}")
    print(f"  ROI:            {roi:+.2f}%")
    print(f"  Final Bankroll: ${final_br:,.0f} (started ${start_br:,.0f})")
    print(f"  Max Drawdown:   {max_dd:.1f}%")

    print(f"\n  By Stat:")
    for stat in sorted(stat_data.keys()):
        sd = stat_data[stat]
        wr = sd["w"] / (sd["w"] + sd["l"]) * 100 if (sd["w"] + sd["l"]) > 0 else 0
        print(f"    {stat.upper():5s}: {sd['n']:4d} bets, {wr:.1f}% win, ${sd['pnl']:+,.0f}")

    print(f"\n  By Edge Bucket:")
    for bucket in sorted(edge_data.keys()):
        ed = edge_data[bucket]
        wr = ed["w"] / (ed["w"] + ed["l"]) * 100 if (ed["w"] + ed["l"]) > 0 else 0
        print(f"    {bucket:2d}-{bucket+2}%: {ed['n']:4d} bets, {wr:.1f}% win, ${ed['pnl']:+,.0f}")


def main():
    print("=" * 65)
    print("  KALMAN + MONTE CARLO vs WEIGHTED AVERAGE")
    print("  Full 2025-26 Season Backtest")
    print("=" * 65)

    print("\nLoading data...")
    props_data, history = load_data()
    results = props_data["results"]
    print(f"  {len(results)} matched props")
    print(f"  {len(history)} players with history")
    print(f"  {sum(len(g) for g in history.values())} total game observations")

    # ============================================================
    # BASELINE: Old weighted average (what we had before)
    # ============================================================
    print("\n\nRunning OLD model (weighted average, 5% edge, $100 flat)...")
    old_bets, old_final, old_start = run_old_model(results, history, min_edge_pct=5, unit=100)
    print_summary("OLD MODEL: Weighted Average (5% edge, $100 flat)", old_bets, old_final, old_start)

    # ============================================================
    # KALMAN ONLY (no Monte Carlo, normal CDF)
    # ============================================================
    print("\n\nRunning KALMAN model (no MC, 3% edge, $100 flat)...")
    k_bets, k_final, k_start = run_kalman_model(
        results, history, min_edge=0.03, use_monte_carlo=False,
        sizing="flat", unit=100
    )
    print_summary("KALMAN FILTER (3% edge, $100 flat, no MC)", k_bets, k_final, k_start)

    # ============================================================
    # KALMAN + MONTE CARLO (the full upgrade)
    # ============================================================
    print("\n\nRunning KALMAN + MONTE CARLO (3% edge, $100 flat)...")
    km_bets, km_final, km_start = run_kalman_model(
        results, history, min_edge=0.03, use_monte_carlo=True,
        sizing="flat", unit=100
    )
    print_summary("KALMAN + MONTE CARLO (3% edge, $100 flat)", km_bets, km_final, km_start)

    # ============================================================
    # KALMAN + MC + KELLY SIZING (full system)
    # ============================================================
    print("\n\nRunning KALMAN + MC + QUARTER KELLY...")
    kmk_bets, kmk_final, kmk_start = run_kalman_model(
        results, history, min_edge=0.03, use_monte_carlo=True,
        sizing="kelly", kelly_frac=0.25
    )
    print_summary("KALMAN + MC + QUARTER KELLY (3% edge)", kmk_bets, kmk_final, kmk_start)

    # ============================================================
    # KALMAN + MC - HIGH CONVICTION ONLY (5% edge minimum)
    # ============================================================
    print("\n\nRunning KALMAN + MC HIGH CONVICTION (5% edge, $100 flat)...")
    hc_bets, hc_final, hc_start = run_kalman_model(
        results, history, min_edge=0.05, use_monte_carlo=True,
        sizing="flat", unit=100
    )
    print_summary("KALMAN + MC HIGH CONVICTION (5% edge, $100 flat)", hc_bets, hc_final, hc_start)

    # ============================================================
    # KALMAN + MC - ULTRA SELECTIVE (8% edge minimum)
    # ============================================================
    print("\n\nRunning KALMAN + MC ULTRA SELECTIVE (8% edge, $100 flat)...")
    us_bets, us_final, us_start = run_kalman_model(
        results, history, min_edge=0.08, use_monte_carlo=True,
        sizing="flat", unit=100
    )
    print_summary("KALMAN + MC ULTRA SELECTIVE (8% edge, $100 flat)", us_bets, us_final, us_start)

    # ============================================================
    # Save results
    # ============================================================
    output = {
        "old_model": {
            "bets": len(old_bets), "final": old_final, "start": old_start,
            "pnl": sum(b["pnl"] for b in old_bets),
            "roi": sum(b["pnl"] for b in old_bets) / max(1, sum(b["bet"] for b in old_bets)) * 100,
        },
        "kalman_only": {
            "bets": len(k_bets), "final": k_final, "start": k_start,
            "pnl": sum(b["pnl"] for b in k_bets),
            "roi": sum(b["pnl"] for b in k_bets) / max(1, sum(b["bet"] for b in k_bets)) * 100,
        },
        "kalman_mc": {
            "bets": len(km_bets), "final": km_final, "start": km_start,
            "pnl": sum(b["pnl"] for b in km_bets),
            "roi": sum(b["pnl"] for b in km_bets) / max(1, sum(b["bet"] for b in km_bets)) * 100,
            "bet_log": km_bets[-100:],
        },
        "kalman_mc_kelly": {
            "bets": len(kmk_bets), "final": kmk_final, "start": kmk_start,
            "pnl": sum(b["pnl"] for b in kmk_bets),
            "roi": sum(b["pnl"] for b in kmk_bets) / max(1, sum(b["bet"] for b in kmk_bets)) * 100,
        },
        "high_conviction": {
            "bets": len(hc_bets), "final": hc_final, "start": hc_start,
            "pnl": sum(b["pnl"] for b in hc_bets),
            "roi": sum(b["pnl"] for b in hc_bets) / max(1, sum(b["bet"] for b in hc_bets)) * 100,
        },
        "ultra_selective": {
            "bets": len(us_bets), "final": us_final, "start": us_start,
            "pnl": sum(b["pnl"] for b in us_bets),
            "roi": sum(b["pnl"] for b in us_bets) / max(1, sum(b["bet"] for b in us_bets)) * 100,
        },
    }

    with open(os.path.join(DATA_DIR, "kalman_backtest_results.json"), "w") as f:
        json.dump(output, f, indent=2)

    # Print comparison table
    print(f"\n\n{'='*65}")
    print(f"  HEAD-TO-HEAD COMPARISON")
    print(f"{'='*65}")
    print(f"  {'Model':<40} {'Bets':>6} {'ROI':>8} {'P/L':>10} {'Final':>10}")
    print(f"  {'-'*75}")
    for name, data in output.items():
        label = name.replace("_", " ").upper()
        print(f"  {label:<40} {data['bets']:>6} {data['roi']:>+7.2f}% ${data['pnl']:>+9,.0f} ${data['final']:>9,.0f}")

    print(f"\n  Results saved to data/kalman_backtest_results.json")


if __name__ == "__main__":
    main()

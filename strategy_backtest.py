"""
Sports Edge - Model-Filtered Strategy Backtester
Takes real prop lines + real results and tests prediction model strategies.
Builds player history from box scores, predicts performance, filters bets.
"""
import json
import os
import sys
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_results():
    with open(os.path.join(DATA_DIR, "real_backtest.json")) as f:
        return json.load(f)


def load_all_box_scores():
    """Load all cached box scores to build player history."""
    history = defaultdict(list)  # player_name -> [{date, pts, reb, ast, fg3m, min, opp, home}, ...]

    box_files = [f for f in os.listdir(DATA_DIR) if f.startswith("box_")]
    for bf in sorted(box_files):
        with open(os.path.join(DATA_DIR, bf)) as f:
            data = json.load(f)

        game = data.get("game", {})
        game_date = game.get("gameTimeUTC", "")[:10]
        if not game_date:
            game_date = game.get("gameId", "")  # fallback

        home_tri = game.get("homeTeam", {}).get("teamTricode", "")
        away_tri = game.get("awayTeam", {}).get("teamTricode", "")

        for tk, is_home in [("homeTeam", True), ("awayTeam", False)]:
            team = game.get(tk, {})
            tri = team.get("teamTricode", "")
            opp = away_tri if is_home else home_tri

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

                name = p.get("name", "")
                history[name.lower()].append({
                    "date": game_date,
                    "pts": s.get("points", 0),
                    "reb": s.get("reboundsTotal", 0),
                    "ast": s.get("assists", 0),
                    "fg3m": s.get("threePointersMade", 0),
                    "min": mins,
                    "opp": opp,
                    "home": is_home,
                    "team": tri,
                })

    # Sort each player's history by date
    for name in history:
        history[name].sort(key=lambda x: x["date"])

    return history


def predict(player_history, stat, lookback=10):
    """Predict a player's stat based on their recent history.
    Returns predicted value or None if insufficient data.
    """
    if len(player_history) < 5:
        return None

    recent = player_history[-lookback:] if len(player_history) >= lookback else player_history

    # Weighted recent average (more recent = higher weight)
    total_w = 0
    weighted_sum = 0
    for i, game in enumerate(recent):
        weight = 1 + (i / len(recent))  # Linear increasing
        weighted_sum += game.get(stat, 0) * weight
        total_w += weight

    recent_avg = weighted_sum / total_w if total_w > 0 else 0

    # Season average (all games)
    season_avg = sum(g.get(stat, 0) for g in player_history) / len(player_history)

    # Blend: 35% season, 65% recent (recent-heavy)
    prediction = season_avg * 0.35 + recent_avg * 0.65

    return prediction


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def kelly_bet(edge_pct, odds, bankroll, fraction=0.5, max_pct=0.05):
    """Half-Kelly bet sizing."""
    dec = american_to_decimal(odds)
    b = dec - 1
    p = 0.5 + edge_pct / 200
    q = 1 - p
    if b <= 0:
        return 0
    k = (b * p - q) / b
    bet = max(0, k * fraction * bankroll)
    return min(bet, bankroll * max_pct)


def run_strategy(results, history, config):
    """Run a filtered betting strategy."""
    bets = []
    bankroll = config.get("bankroll", 1000)
    start_bankroll = bankroll
    bankroll_curve = [bankroll]
    unit = config.get("unit", 50)
    min_edge = config.get("min_edge", 3)
    stat_filter = config.get("stat_filter", None)  # None = all stats
    side_filter = config.get("side_filter", None)  # "over", "under", or None
    sizing = config.get("sizing", "flat")  # "flat" or "half-kelly"
    lookback = config.get("lookback", 10)
    min_minutes = config.get("min_minutes", 20)

    # Group results by date for chronological processing
    by_date = defaultdict(list)
    for r in results:
        by_date[r["date"]].append(r)

    dates = sorted(by_date.keys())

    # Dedupe: only keep the best odds per player+stat+date+side
    for date in dates:
        props = by_date[date]

        # Dedupe
        seen = {}
        for prop in props:
            if stat_filter and prop["stat"] != stat_filter:
                continue

            key = f"{prop['player']}_{prop['stat']}"
            if key not in seen:
                seen[key] = prop
            # Keep the one with better odds for unders (or overs)

        for key, prop in seen.items():
            player_key = prop["player"].lower()
            player_hist = history.get(player_key, [])

            # Get games before this date
            prior = [g for g in player_hist if g["date"] < prop["date"]]
            if len(prior) < 5:
                continue

            # Skip low-minutes players
            avg_min = sum(g["min"] for g in prior[-10:]) / min(10, len(prior))
            if avg_min < min_minutes:
                continue

            # Model prediction
            pred = predict(prior, prop["stat"], lookback)
            if pred is None:
                continue

            line = prop["line"]
            model_says_over = pred > line
            model_says_under = pred < line
            model_edge = abs(pred - line) / line * 100 if line > 0 else 0

            # Determine bet
            side = None
            odds = 0

            if side_filter == "under" and model_says_under and model_edge >= min_edge:
                side = "under"
                odds = prop["under_odds"]
            elif side_filter == "over" and model_says_over and model_edge >= min_edge:
                side = "over"
                odds = prop["over_odds"]
            elif side_filter is None:
                if model_says_under and model_edge >= min_edge:
                    side = "under"
                    odds = prop["under_odds"]
                elif model_says_over and model_edge >= min_edge:
                    side = "over"
                    odds = prop["over_odds"]

            if side is None or bankroll <= 0:
                continue

            # Bet sizing
            if sizing == "half-kelly":
                bet_amount = kelly_bet(model_edge, odds, bankroll, 0.5, 0.05)
            else:
                bet_amount = unit

            bet_amount = min(bet_amount, bankroll)
            bet_amount = round(bet_amount, 2)
            if bet_amount < 5:
                continue

            # Determine result
            won = prop["over_won"] if side == "over" else prop["under_won"]
            push = prop["push"]

            if push:
                pnl = 0
            elif won:
                pnl = bet_amount * (american_to_decimal(odds) - 1)
            else:
                pnl = -bet_amount

            bankroll += pnl
            bankroll = round(bankroll, 2)
            bankroll_curve.append(bankroll)

            bets.append({
                "date": prop["date"],
                "player": prop["player"],
                "stat": prop["stat"],
                "line": line,
                "prediction": round(pred, 1),
                "edge": round(model_edge, 1),
                "side": side,
                "actual": prop["actual"],
                "won": won,
                "push": push,
                "odds": odds,
                "bet": bet_amount,
                "pnl": round(pnl, 2),
                "bankroll": bankroll,
            })

    return bets, bankroll_curve, start_bankroll


def print_results(name, bets, curve, start_br):
    if not bets:
        print(f"\n  {name}: No bets placed")
        return

    wins = sum(1 for b in bets if b["won"])
    losses = sum(1 for b in bets if not b["won"] and not b["push"])
    pushes = sum(1 for b in bets if b["push"])
    total_wagered = sum(b["bet"] for b in bets)
    total_pnl = sum(b["pnl"] for b in bets)
    roi = (total_pnl / total_wagered * 100) if total_wagered > 0 else 0
    final_br = curve[-1]

    # Max drawdown
    peak = start_br
    max_dd = 0
    for br in curve:
        if br > peak:
            peak = br
        dd = (peak - br) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    # Worst losing streak
    worst_streak = 0
    cur_streak = 0
    for b in bets:
        if not b["won"] and not b["push"]:
            cur_streak += 1
            worst_streak = max(worst_streak, cur_streak)
        else:
            cur_streak = 0

    # By stat breakdown
    stat_results = defaultdict(lambda: {"w": 0, "l": 0, "pnl": 0, "n": 0})
    for b in bets:
        sr = stat_results[b["stat"]]
        sr["n"] += 1
        if b["won"]:
            sr["w"] += 1
        elif not b["push"]:
            sr["l"] += 1
        sr["pnl"] += b["pnl"]

    # By edge bucket
    edge_buckets = defaultdict(lambda: {"w": 0, "l": 0, "n": 0})
    for b in bets:
        bucket = int(b["edge"] // 5) * 5  # 0-4, 5-9, 10-14, etc.
        eb = edge_buckets[bucket]
        eb["n"] += 1
        if b["won"]:
            eb["w"] += 1
        elif not b["push"]:
            eb["l"] += 1

    print(f"\n{'=' * 60}")
    print(f"  STRATEGY: {name}")
    print(f"{'=' * 60}")
    print(f"  Bets:          {len(bets)}")
    print(f"  Win/Loss/Push: {wins}/{losses}/{pushes}")
    print(f"  Win Rate:      {wins/(wins+losses)*100:.1f}%")
    print(f"  Total Wagered: ${total_wagered:,.0f}")
    print(f"  Total P/L:     ${total_pnl:+,.0f}")
    print(f"  ROI:           {roi:+.2f}%")
    print(f"  Final Bankroll:${final_br:,.0f} (started ${start_br:,.0f})")
    print(f"  Max Drawdown:  {max_dd:.1f}%")
    print(f"  Worst Streak:  {worst_streak}L")

    print(f"\n  By Stat:")
    for stat in sorted(stat_results.keys()):
        sr = stat_results[stat]
        wr = sr["w"] / (sr["w"] + sr["l"]) * 100 if (sr["w"] + sr["l"]) > 0 else 0
        print(f"    {stat.upper():5s}: {sr['n']:4d} bets, {wr:.1f}% win, ${sr['pnl']:+,.0f}")

    print(f"\n  By Edge Bucket:")
    for bucket in sorted(edge_buckets.keys()):
        eb = edge_buckets[bucket]
        wr = eb["w"] / (eb["w"] + eb["l"]) * 100 if (eb["w"] + eb["l"]) > 0 else 0
        print(f"    {bucket:2d}-{bucket+4}%: {eb['n']:4d} bets, {wr:.1f}% win rate")

    # Show last 20 bets
    print(f"\n  Last 20 bets:")
    print(f"  {'Date':<12} {'Player':<22} {'Stat':<5} {'Line':>5} {'Pred':>5} {'Edge':>5} {'Side':<6} {'Actual':>6} {'Result':<5} {'P/L':>8}")
    print(f"  {'-'*95}")
    for b in bets[-20:]:
        result = "WIN" if b["won"] else "PUSH" if b["push"] else "LOSS"
        print(f"  {b['date']:<12} {b['player'][:21]:<22} {b['stat']:<5} {b['line']:>5.1f} {b['prediction']:>5.1f} {b['edge']:>4.1f}% {b['side']:<6} {b['actual']:>6} {result:<5} ${b['pnl']:>+7.0f}")


def main():
    print("Loading real backtest data...")
    data = load_results()
    results = data["results"]
    print(f"  {len(results)} matched props across {len(data['dates'])} dates")

    print("Loading box score history...")
    history = load_all_box_scores()
    print(f"  {len(history)} players with game history")

    # ============================================================
    # STRATEGY 1: Blind unders (baseline)
    # ============================================================
    bets1, curve1, sb1 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 0,
        "side_filter": "under", "sizing": "flat",
        "stat_filter": None, "lookback": 10, "min_minutes": 20,
    })
    # Blind unders doesn't use model, so override
    blind_bets = []
    br = 1000
    blind_curve = [br]
    seen_keys = set()
    for r in sorted(results, key=lambda x: x["date"]):
        if r["minutes"] < 20:
            continue
        key = f"{r['date']}_{r['player']}_{r['stat']}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        odds = r["under_odds"]
        bet = 50
        won = r["under_won"]
        push = r["push"]
        pnl = 0
        if push:
            pnl = 0
        elif won:
            pnl = bet * (american_to_decimal(odds) - 1)
        else:
            pnl = -bet
        br += pnl
        br = round(br, 2)
        blind_curve.append(br)
        blind_bets.append({
            "date": r["date"], "player": r["player"], "stat": r["stat"],
            "line": r["line"], "prediction": 0, "edge": 0,
            "side": "under", "actual": r["actual"], "won": won,
            "push": push, "odds": odds, "bet": bet, "pnl": round(pnl, 2),
            "bankroll": br,
        })
    print_results("BLIND UNDERS (baseline, $50 flat)", blind_bets, blind_curve, 1000)

    # ============================================================
    # STRATEGY 2: Model-filtered unders only (min 5% edge)
    # ============================================================
    bets2, curve2, sb2 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 5,
        "side_filter": "under", "sizing": "flat",
        "stat_filter": None, "lookback": 10, "min_minutes": 20,
    })
    print_results("MODEL UNDERS (5% edge, $50 flat)", bets2, curve2, sb2)

    # ============================================================
    # STRATEGY 3: Model-filtered unders, 10% min edge (high conviction)
    # ============================================================
    bets3, curve3, sb3 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 10,
        "side_filter": "under", "sizing": "flat",
        "stat_filter": None, "lookback": 10, "min_minutes": 20,
    })
    print_results("MODEL UNDERS (10% edge, $50 flat)", bets3, curve3, sb3)

    # ============================================================
    # STRATEGY 4: Model-filtered unders, half-kelly sizing
    # ============================================================
    bets4, curve4, sb4 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 5,
        "side_filter": "under", "sizing": "half-kelly",
        "stat_filter": None, "lookback": 10, "min_minutes": 20,
    })
    print_results("MODEL UNDERS (5% edge, half-kelly)", bets4, curve4, sb4)

    # ============================================================
    # STRATEGY 5: Model both sides (over + under), 8% min edge
    # ============================================================
    bets5, curve5, sb5 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 8,
        "side_filter": None, "sizing": "flat",
        "stat_filter": None, "lookback": 10, "min_minutes": 20,
    })
    print_results("MODEL BOTH SIDES (8% edge, $50 flat)", bets5, curve5, sb5)

    # ============================================================
    # STRATEGY 6: 3-pointers unders only (strongest signal)
    # ============================================================
    bets6, curve6, sb6 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 5,
        "side_filter": "under", "sizing": "flat",
        "stat_filter": "fg3m", "lookback": 10, "min_minutes": 20,
    })
    print_results("3PT UNDERS ONLY (5% edge, $50 flat)", bets6, curve6, sb6)

    # ============================================================
    # STRATEGY 7: Points unders only
    # ============================================================
    bets7, curve7, sb7 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 5,
        "side_filter": "under", "sizing": "flat",
        "stat_filter": "pts", "lookback": 10, "min_minutes": 20,
    })
    print_results("POINTS UNDERS ONLY (5% edge, $50 flat)", bets7, curve7, sb7)

    # ============================================================
    # STRATEGY 8: Conservative - high edge, kelly, filtered
    # ============================================================
    bets8, curve8, sb8 = run_strategy(results, history, {
        "bankroll": 1000, "unit": 50, "min_edge": 15,
        "side_filter": "under", "sizing": "half-kelly",
        "stat_filter": None, "lookback": 10, "min_minutes": 25,
    })
    print_results("CONSERVATIVE (15% edge, half-kelly, 25min)", bets8, curve8, sb8)

    # Save best strategy details for frontend
    all_strategies = {
        "blind_unders": {"bets": len(blind_bets), "win_rate": sum(1 for b in blind_bets if b["won"]) / max(1, sum(1 for b in blind_bets if not b["push"])) * 100, "final_br": blind_curve[-1]},
    }
    for name, bts, crv in [
        ("model_5pct", bets2, curve2),
        ("model_10pct", bets3, curve3),
        ("model_kelly", bets4, curve4),
        ("model_both", bets5, curve5),
        ("fg3m_under", bets6, curve6),
        ("pts_under", bets7, curve7),
        ("conservative", bets8, curve8),
    ]:
        if bts:
            wins = sum(1 for b in bts if b["won"])
            losses = sum(1 for b in bts if not b["won"] and not b["push"])
            all_strategies[name] = {
                "bets": len(bts),
                "win_rate": wins / max(1, wins + losses) * 100,
                "roi": sum(b["pnl"] for b in bts) / max(1, sum(b["bet"] for b in bts)) * 100,
                "final_br": crv[-1],
                "bankroll_curve": crv,
                "bet_log": bts[-50:],
            }

    with open(os.path.join(DATA_DIR, "strategy_results.json"), "w") as f:
        json.dump(all_strategies, f, indent=2)
    print(f"\nStrategy results saved to data/strategy_results.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Backtest MLB model on MONEYLINE vs Pinnacle closing.
Uses the same Poisson/NB team-strength model from backtest_mlb_pinnacle.py.
"""

import sqlite3
import os
import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import nbinom

sys.path.insert(0, os.path.dirname(__file__))
from backtest_mlb_pinnacle import MLBPoissonModel, MLB_FULL_TO_ABBREV, OVERDISPERSION

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

MIN_TRAIN_GAMES = 300
BET_SIZE = 100


def predict_home_win_prob(model, home_team, away_team):
    """P(home wins) using negative binomial score distribution."""
    if not model.fitted:
        return None
    if home_team not in model.params or away_team not in model.params:
        return None

    h = model.params[home_team]
    a = model.params[away_team]
    lambda_h = math.exp(h["attack"] + a["defense"] + model.home_adv)
    mu_a = math.exp(a["attack"] + h["defense"])

    lambda_h = max(0.5, min(lambda_h, 15.0))
    mu_a = max(0.5, min(mu_a, 15.0))

    def nb_params(mu):
        r = mu / (OVERDISPERSION - 1)
        p = r / (r + mu)
        return r, p

    r_h, p_h = nb_params(lambda_h)
    r_a, p_a = nb_params(mu_a)

    max_runs = 20
    p_home_win = 0.0
    p_draw = 0.0
    for hr in range(max_runs + 1):
        ph = nbinom.pmf(hr, r_h, p_h)
        for ar in range(max_runs + 1):
            pa = nbinom.pmf(ar, r_a, p_a)
            if hr > ar:
                p_home_win += ph * pa
            elif hr == ar:
                p_draw += ph * pa

    # MLB has no draws - extra innings. Split draws 52/48 home advantage
    p_home_win += p_draw * 0.52
    return p_home_win


def run_backtest():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load games from totals (have results) and get moneyline odds
    totals = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='totals' AND period=0
        AND score_home IS NOT NULL
        ORDER BY game_date
    """).fetchall()

    games = []
    seen = set()
    for r in totals:
        eid = r[0]
        if eid in seen:
            continue
        seen.add(eid)

        ml = conn.execute("""
            SELECT odds_over, odds_under, todds_over, todds_under
            FROM pinnacle_closing
            WHERE event_id=? AND market='moneyline' AND period=0
            LIMIT 1
        """, (eid,)).fetchone()

        if not ml or not ml[2] or not ml[3] or ml[2] <= 1 or ml[3] <= 1:
            continue

        home = r[2]
        away = r[3]
        h_abbr = MLB_FULL_TO_ABBREV.get(home)
        a_abbr = MLB_FULL_TO_ABBREV.get(away)
        if not h_abbr or not a_abbr:
            continue

        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": h_abbr,
            "away_team": a_abbr,
            "home_score": r[4],
            "away_score": r[5],
            "home_won": r[4] > r[5],
            "ml_todds_home": ml[2],
            "ml_todds_away": ml[3],
            "ml_odds_home": ml[0],
            "ml_odds_away": ml[1],
        })

    df = pd.DataFrame(games)
    print(f"Loaded {len(df)} MLB games with moneyline data")
    print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

    model = MLBPoissonModel()
    bets = []
    no_pred = 0

    for i in range(MIN_TRAIN_GAMES, len(df)):
        game = df.iloc[i]

        if i == MIN_TRAIN_GAMES or i % 100 == 0:
            model.fit(df.iloc[:i], reference_date=game["game_date"])

        p_home = predict_home_win_prob(model, game["home_team"], game["away_team"])
        if p_home is None:
            no_pred += 1
            continue

        p_away = 1.0 - p_home
        impl_home = 1.0 / game["ml_todds_home"]
        impl_away = 1.0 / game["ml_todds_away"]

        edge_home = p_home - impl_home
        edge_away = p_away - impl_away

        best_edge = max(edge_home, edge_away)
        if best_edge > 0:
            if edge_home >= edge_away:
                side = "HOME"
                won = game["home_won"]
                edge = edge_home
                model_p = p_home
                market_p = impl_home
                odds = game["ml_odds_home"]
            else:
                side = "AWAY"
                won = not game["home_won"]
                edge = edge_away
                model_p = p_away
                market_p = impl_away
                odds = game["ml_odds_away"]

            if odds and odds > 1:
                profit = BET_SIZE * (odds - 1) if won else -BET_SIZE
            else:
                continue

            bets.append({
                "date": game["game_date"],
                "home": game["home_team"],
                "away": game["away_team"],
                "side": side,
                "model_prob": model_p,
                "market_prob": market_p,
                "edge": edge,
                "clv": edge * 100,
                "odds": odds,
                "won": won,
                "profit": profit,
            })

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(df)} processed, {len(bets)} bets so far...")

    # Results
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)

    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, "mlb_moneyline_bets.csv")
    bets_df.to_csv(csv_path, index=False)

    print(f"\n{'='*60}")
    print(f"  MLB MONEYLINE BACKTEST vs PINNACLE CLOSING")
    print(f"{'='*60}")
    print(f"  Games processed: {len(df) - MIN_TRAIN_GAMES}")
    print(f"  No prediction: {no_pred}")
    print(f"  Total bets: {len(bets)}")

    if not bets:
        print("  No bets found.")
        return

    thresholds = [0.01, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]
    print(f"\n  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} "
          f"{'Profit':>10} {'ROI':>8} {'CLV':>7}")
    print(f"  {'-'*58}")

    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh]
        if not tb:
            continue
        tw = sum(1 for b in tb if b["won"])
        tl = len(tb) - tw
        tprofit = sum(b["profit"] for b in tb)
        twagered = BET_SIZE * len(tb)
        troi = (tprofit / twagered * 100) if twagered > 0 else 0
        tclv = np.mean([b["clv"] for b in tb])
        twr = tw / len(tb) * 100
        print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} "
              f"{twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}% {tclv:>+6.1f}%")

    for side_label in ["HOME", "AWAY"]:
        print(f"\n  --- {side_label}-only ---")
        print(f"  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} "
              f"{'Profit':>10} {'ROI':>8}")
        print(f"  {'-'*50}")
        for thresh in thresholds:
            tb = [b for b in bets if b["edge"] >= thresh and b["side"] == side_label]
            if not tb:
                continue
            tw = sum(1 for b in tb if b["won"])
            tl = len(tb) - tw
            tprofit = sum(b["profit"] for b in tb)
            twagered = BET_SIZE * len(tb)
            troi = (tprofit / twagered * 100) if twagered > 0 else 0
            twr = tw / len(tb) * 100
            print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} "
                  f"{twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}%")

    # Yearly
    filtered = [b for b in bets if b["edge"] >= 0.05]
    if filtered:
        print(f"\n  Yearly Breakdown (at 5%):")
        years = {}
        for b in filtered:
            y = b["date"][:4]
            if y not in years:
                years[y] = {"bets": 0, "wins": 0, "profit": 0}
            years[y]["bets"] += 1
            if b["won"]:
                years[y]["wins"] += 1
            years[y]["profit"] += b["profit"]

        for y in sorted(years):
            d = years[y]
            wr = d["wins"] / d["bets"] * 100
            roi = d["profit"] / (BET_SIZE * d["bets"]) * 100
            print(f"    {y}: {d['bets']}B {d['wins']}W ({wr:.1f}%) "
                  f"${d['profit']:+.0f} ROI {roi:+.1f}%")

    print(f"\n  Results saved to {csv_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_backtest()

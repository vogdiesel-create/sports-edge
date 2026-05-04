#!/usr/bin/env python3
"""
Backtest NHL Dixon-Coles model on MONEYLINE (match outcome) vs Pinnacle closing.

The Dixon-Coles model predicts exact scoreline probabilities.
From the score matrix we derive P(home_win) including OT/SO.
Compare against Pinnacle devigged moneyline implied probabilities.
"""

import sqlite3
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from nhl_model import DixonColesModel, TEAM_ABBREV_TO_FULL

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")
FULL_TO_ABBREV = {v: k for k, v in TEAM_ABBREV_TO_FULL.items()}

MIN_TRAIN_GAMES = 200
BET_SIZE = 100


def home_win_prob_from_matrix(matrix):
    """
    Derive P(home wins game) from score matrix.

    NHL rules: if tied after regulation, game goes to OT/SO.
    One team always wins. We model:
      - P(home wins in regulation) = sum of matrix[i][j] where i > j
      - P(draw after regulation) = sum of diagonal
      - P(home wins OT/SO | draw) = ~52% (slight home advantage in OT)
    """
    n = matrix.shape[0]
    p_home_reg = 0.0
    p_away_reg = 0.0
    p_draw = 0.0

    for i in range(n):
        for j in range(n):
            if i > j:
                p_home_reg += matrix[i][j]
            elif j > i:
                p_away_reg += matrix[i][j]
            else:
                p_draw += matrix[i][j]

    # In OT/SO, home team wins ~52% historically
    OT_HOME_ADV = 0.52
    p_home_win = p_home_reg + p_draw * OT_HOME_ADV
    return p_home_win


def run_backtest():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load games with moneyline closing odds
    rows = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away,
               odds_over, odds_under, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='moneyline' AND period=0
        AND score_home IS NOT NULL AND score_away IS NOT NULL
        ORDER BY game_date
    """).fetchall()

    if not rows:
        # Try alternate market names
        rows = conn.execute("""
            SELECT DISTINCT event_id, game_date, home_team, away_team,
                   score_home, score_away,
                   odds_over, odds_under, todds_over, todds_under
            FROM pinnacle_closing
            WHERE sport='NHL' AND period=0
            AND score_home IS NOT NULL AND score_away IS NOT NULL
            ORDER BY game_date
        """).fetchall()

    # Check what markets exist
    markets = conn.execute("""
        SELECT DISTINCT market, COUNT(*) as cnt
        FROM pinnacle_closing
        WHERE sport='NHL'
        GROUP BY market
    """).fetchall()
    print("Available NHL markets:")
    for m in markets:
        print(f"  {m[0]}: {m[1]} records")

    # Load moneyline data specifically
    ml_rows = conn.execute("""
        SELECT event_id, game_date, home_team, away_team,
               score_home, score_away, line,
               odds_over, odds_under, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='moneyline' AND period=0
        AND score_home IS NOT NULL
        ORDER BY game_date
    """).fetchall()

    print(f"\nMoneyline records: {len(ml_rows)}")

    if not ml_rows:
        # Moneyline might be stored differently. Check line=0 entries
        ml_rows = conn.execute("""
            SELECT event_id, game_date, home_team, away_team,
                   score_home, score_away, line,
                   odds_over, odds_under, todds_over, todds_under, market
            FROM pinnacle_closing
            WHERE sport='NHL' AND period=0 AND line=0
            AND score_home IS NOT NULL
            ORDER BY game_date
            LIMIT 10
        """).fetchall()
        print(f"\nLine=0 records sample:")
        for r in ml_rows:
            print(f"  {r[1]} {r[2]} vs {r[3]}: market={r[11]} line={r[6]} "
                  f"odds={r[7]}/{r[8]} todds={r[9]}/{r[10]}")

        # Try just the moneyline market
        ml_rows = conn.execute("""
            SELECT event_id, game_date, home_team, away_team,
                   score_home, score_away, line,
                   odds_over, odds_under, todds_over, todds_under
            FROM pinnacle_closing
            WHERE sport='NHL' AND market='moneyline' AND period=0
            ORDER BY game_date
        """).fetchall()
        print(f"\nStrict moneyline: {len(ml_rows)} records")

    if len(ml_rows) < MIN_TRAIN_GAMES:
        print(f"\nNot enough moneyline data ({len(ml_rows)} games). "
              f"Need {MIN_TRAIN_GAMES}.")
        print("\nFalling back to totals-based approach with score results...")
        run_backtest_from_totals(conn)
        return

    # Build games list
    games = []
    seen = set()
    for r in ml_rows:
        eid = r[0]
        if eid in seen:
            continue
        seen.add(eid)
        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": FULL_TO_ABBREV.get(r[2], r[2][:3].upper()),
            "away_team": FULL_TO_ABBREV.get(r[3], r[3][:3].upper()),
            "home_score": r[4],
            "away_score": r[5],
            "home_won": r[4] > r[5],
        })

    df = pd.DataFrame(games)
    run_moneyline_backtest(conn, df)


def run_backtest_from_totals(conn):
    """
    Use totals data for game results + moneyline odds from same events.
    """
    # Get all games from totals (for results)
    totals = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='totals' AND period=0
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

        # Get moneyline odds for this event
        ml = conn.execute("""
            SELECT odds_over, odds_under, todds_over, todds_under
            FROM pinnacle_closing
            WHERE event_id=? AND market='moneyline' AND period=0
            LIMIT 1
        """, (eid,)).fetchone()

        if not ml:
            continue

        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": FULL_TO_ABBREV.get(r[2], r[2][:3].upper()),
            "away_team": FULL_TO_ABBREV.get(r[3], r[3][:3].upper()),
            "home_score": r[4],
            "away_score": r[5],
            "home_won": r[4] > r[5],
            "ml_home_odds": ml[0],
            "ml_away_odds": ml[1],
            "ml_home_todds": ml[2],
            "ml_away_todds": ml[3],
        })

    df = pd.DataFrame(games)
    print(f"Games with both totals and moneyline: {len(df)}")
    if len(df) < MIN_TRAIN_GAMES:
        print("Not enough data.")
        return

    run_moneyline_backtest(conn, df, preloaded_odds=True)


def run_moneyline_backtest(conn, df, preloaded_odds=False):
    print(f"\nLoaded {len(df)} unique NHL games")
    print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

    dc_model = DixonColesModel()
    bets = []
    no_closing = 0
    no_pred = 0
    no_edge = 0

    # Need training data for Dixon-Coles (home/away scores)
    train_df = df[["game_date", "home_team", "away_team",
                    "home_score", "away_score"]].copy()
    train_df.columns = ["game_date", "home_team", "away_team",
                        "home_score", "away_score"]

    for i in range(MIN_TRAIN_GAMES, len(df)):
        game = df.iloc[i]

        if i == MIN_TRAIN_GAMES or i % 50 == 0:
            dc_model.fit(train_df.iloc[:i], reference_date=game["game_date"])

        if not dc_model.fitted:
            continue

        # Get model's home win probability
        try:
            matrix = dc_model.predict_score_matrix(
                game["home_team"], game["away_team"])
            model_home_p = home_win_prob_from_matrix(matrix)
        except Exception:
            no_pred += 1
            continue

        model_away_p = 1.0 - model_home_p

        # Get Pinnacle closing moneyline odds
        if preloaded_odds:
            todds_home = game.get("ml_home_todds")
            todds_away = game.get("ml_away_todds")
            odds_home = game.get("ml_home_odds")
            odds_away = game.get("ml_away_odds")
        else:
            eid = int(game["event_id"])
            ml = conn.execute("""
                SELECT odds_over, odds_under, todds_over, todds_under
                FROM pinnacle_closing
                WHERE event_id=? AND market='moneyline' AND period=0
                LIMIT 1
            """, (eid,)).fetchone()
            if not ml:
                no_closing += 1
                continue
            odds_home = ml[0]
            odds_away = ml[1]
            todds_home = ml[2]
            todds_away = ml[3]

        if not todds_home or not todds_away or todds_home <= 1 or todds_away <= 1:
            no_closing += 1
            continue

        # Devigged implied probabilities
        impl_home = 1.0 / todds_home
        impl_away = 1.0 / todds_away

        edge_home = model_home_p - impl_home
        edge_away = model_away_p - impl_away

        home_won = game["home_score"] > game["away_score"]

        best_edge = max(edge_home, edge_away)
        if best_edge > 0:
            if edge_home >= edge_away:
                side = "HOME"
                won = home_won
                edge = edge_home
                model_p = model_home_p
                market_p = impl_home
                odds = odds_home
            else:
                side = "AWAY"
                won = not home_won
                edge = edge_away
                model_p = model_away_p
                market_p = impl_away
                odds = odds_away

            if odds and odds > 1:
                profit = BET_SIZE * (odds - 1) if won else -BET_SIZE
            else:
                profit = 0
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
        else:
            no_edge += 1

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(df)} processed, {len(bets)} bets so far...")

    # Results
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)

    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, "nhl_moneyline_bets.csv")
    bets_df.to_csv(csv_path, index=False)

    print(f"\n{'='*60}")
    print(f"  NHL MONEYLINE BACKTEST vs PINNACLE CLOSING")
    print(f"{'='*60}")
    print(f"  Games processed: {len(df) - MIN_TRAIN_GAMES}")
    print(f"  No closing data: {no_closing}")
    print(f"  No prediction: {no_pred}")
    print(f"  No edge found: {no_edge}")
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
            print(f"  {thresh*100:>6.0f}% {0:>6}")
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

    # HOME vs AWAY breakdown
    for side_label in ["HOME", "AWAY"]:
        print(f"\n  --- {side_label}-only at various thresholds ---")
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

    # Yearly breakdown at best threshold
    best_thresh = 0.05
    filtered = [b for b in bets if b["edge"] >= best_thresh]
    if filtered:
        print(f"\n  Yearly Breakdown (at {best_thresh*100:.0f}%):")
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

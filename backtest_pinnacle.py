#!/usr/bin/env python3
"""
Backtest NHL model against REAL Pinnacle closing lines.
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

MIN_EDGE = 0.10
MIN_TRAIN_GAMES = 200
BET_SIZE = 100


def run_backtest():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load games
    rows = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away, total_goals
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='totals' AND period=0
        AND score_home IS NOT NULL AND score_away IS NOT NULL
        ORDER BY game_date
    """).fetchall()

    games = []
    seen = set()
    for r in rows:
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
            "total_goals": r[6],
        })

    df = pd.DataFrame(games)
    print(f"Loaded {len(df)} unique NHL games")
    print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

    dc_model = DixonColesModel()
    bets = []
    no_closing = 0
    no_pred = 0
    no_edge = 0

    for i in range(MIN_TRAIN_GAMES, len(df)):
        game = df.iloc[i]

        if i == MIN_TRAIN_GAMES or i % 50 == 0:
            dc_model.fit(df.iloc[:i], reference_date=game["game_date"])

        if not dc_model.fitted:
            continue

        eid = int(game["event_id"])

        # Get closing line
        crows = conn.execute("""
            SELECT line, odds_over, odds_under, todds_over, todds_under
            FROM pinnacle_closing WHERE event_id=? AND market='totals' AND period=0
            ORDER BY ABS(odds_over - odds_under) ASC
        """, (eid,)).fetchall()

        if not crows:
            no_closing += 1
            continue

        r = crows[0]
        line = r[0]
        odds_over = r[1]
        odds_under = r[2]
        todds_o = r[3]
        todds_u = r[4]

        prob = dc_model.predict_over_prob(game["home_team"], game["away_team"], line)
        if prob is None:
            no_pred += 1
            continue

        impl_over = 1.0 / todds_o if todds_o and todds_o > 0 else 0.5
        impl_under = 1.0 / todds_u if todds_u and todds_u > 0 else 0.5

        edge_over = prob - impl_over
        edge_under = (1.0 - prob) - impl_under

        actual_total = game["total_goals"]

        # Store ALL bets with any positive edge (filter at analysis time)
        best_edge = max(edge_over, edge_under)
        if best_edge > 0:
            if edge_over >= edge_under:
                side = "OVER"
                won = actual_total > line
                push = actual_total == line
                edge = edge_over
                model_p = prob
                market_p = impl_over
                odds = odds_over
            else:
                side = "UNDER"
                won = actual_total < line
                push = actual_total == line
                edge = edge_under
                model_p = 1.0 - prob
                market_p = impl_under
                odds = odds_under

            profit = 0 if push else (BET_SIZE * (odds - 1) if won else -BET_SIZE)
            bets.append({
                "date": game["game_date"], "home": game["home_team"],
                "away": game["away_team"], "side": side, "line": line,
                "model_prob": model_p, "market_prob": market_p,
                "edge": edge, "clv": edge * 100,
                "odds": odds, "actual_total": actual_total,
                "won": won, "push": push, "profit": profit,
            })
        else:
            no_edge += 1

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(df)} processed, {len(bets)} bets so far...")

    conn.close()

    # Save all bets to CSV for analysis
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)

    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, "all_bets.csv")
    bets_df.to_csv(csv_path, index=False)
    print(f"\n  Saved {len(bets)} bets to {csv_path}")

    # Results at multiple edge thresholds
    print(f"\n{'='*60}")
    print(f"  NHL BACKTEST vs REAL PINNACLE CLOSING LINES")
    print(f"{'='*60}")
    print(f"  Games processed: {len(df) - MIN_TRAIN_GAMES}")
    print(f"  No closing data: {no_closing}")
    print(f"  No prediction: {no_pred}")
    print(f"  No edge found: {no_edge}")
    print(f"  Total bets with any edge: {len(bets)}")

    if not bets:
        print("  No bets found.")
        return

    # Test multiple thresholds
    thresholds = [0.01, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]
    print(f"\n  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} {'Profit':>10} {'ROI':>8} {'CLV':>7}")
    print(f"  {'-'*58}")

    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh]
        if not tb:
            print(f"  {thresh*100:>6.0f}% {0:>6} {'--':>5} {'--':>5} {'--':>6} {'--':>10} {'--':>8} {'--':>7}")
            continue
        tw = sum(1 for b in tb if b["won"])
        tl = sum(1 for b in tb if not b["won"] and not b["push"])
        tp = sum(1 for b in tb if b["push"])
        tprofit = sum(b["profit"] for b in tb)
        twagered = BET_SIZE * (len(tb) - tp)
        troi = (tprofit / twagered * 100) if twagered > 0 else 0
        tclv = np.mean([b["clv"] for b in tb])
        twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
        print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} {twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}% {tclv:>+6.1f}%")

    # Detailed breakdown at best threshold (MIN_EDGE)
    filtered = [b for b in bets if b["edge"] >= MIN_EDGE]
    wins = sum(1 for b in filtered if b["won"])
    losses = sum(1 for b in filtered if not b["won"] and not b["push"])
    pushes = sum(1 for b in filtered if b["push"])
    total_profit = sum(b["profit"] for b in filtered)
    total_wagered = BET_SIZE * (len(filtered) - pushes)
    roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
    avg_clv = np.mean([b["clv"] for b in filtered])
    positive_clv = sum(1 for b in filtered if b["clv"] > 0)

    print(f"\n  --- Detailed at {MIN_EDGE*100:.0f}% threshold ---")
    print(f"  Record: {wins}W-{losses}L-{pushes}P ({wins/(wins+losses)*100:.1f}% WR)")
    print(f"  Total wagered: ${total_wagered:,.0f}")
    print(f"  Total profit: ${total_profit:,.2f}")
    print(f"  ROI: {roi:+.2f}%")
    print(f"  Average CLV: {avg_clv:+.2f}%")

    overs = [b for b in filtered if b["side"] == "OVER"]
    unders = [b for b in filtered if b["side"] == "UNDER"]
    if overs:
        o_w = sum(1 for b in overs if b["won"])
        o_p = sum(b["profit"] for b in overs)
        print(f"  OVER bets: {len(overs)} ({o_w}W, ${o_p:+.2f})")
    if unders:
        u_w = sum(1 for b in unders if b["won"])
        u_p = sum(b["profit"] for b in unders)
        print(f"  UNDER bets: {len(unders)} ({u_w}W, ${u_p:+.2f})")

    # UNDER-only analysis (since UNDERs were profitable)
    print(f"\n  --- UNDER-only at various thresholds ---")
    print(f"  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} {'Profit':>10} {'ROI':>8}")
    print(f"  {'-'*50}")
    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh and b["side"] == "UNDER"]
        if not tb:
            continue
        tw = sum(1 for b in tb if b["won"])
        tl = sum(1 for b in tb if not b["won"] and not b["push"])
        tp = sum(1 for b in tb if b["push"])
        tprofit = sum(b["profit"] for b in tb)
        twagered = BET_SIZE * (len(tb) - tp)
        troi = (tprofit / twagered * 100) if twagered > 0 else 0
        twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
        print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} {twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}%")

    print(f"\n  Monthly Breakdown (at {MIN_EDGE*100:.0f}%):")
    months = {}
    for b in filtered:
        m = b["date"][:7]
        if m not in months:
            months[m] = {"bets": 0, "wins": 0, "profit": 0, "clv": []}
        months[m]["bets"] += 1
        if b["won"]:
            months[m]["wins"] += 1
        months[m]["profit"] += b["profit"]
        months[m]["clv"].append(b["clv"])

    for m in sorted(months):
        d = months[m]
        avg_m_clv = np.mean(d["clv"])
        wr = d["wins"] / d["bets"] * 100
        print(f"    {m}: {d['bets']}B {d['wins']}W ({wr:.0f}%) "
              f"${d['profit']:+.0f} CLV {avg_m_clv:+.1f}%")

    # Save summary
    with open(os.path.join(results_dir, "pinnacle_backtest.txt"), "w") as f:
        f.write(f"NHL Backtest vs Real Pinnacle Closing Lines\n")
        f.write(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Games: {len(df) - MIN_TRAIN_GAMES} | Bets: {len(filtered)}\n")
        f.write(f"Record: {wins}W-{losses}L-{pushes}P ({wins/(wins+losses)*100:.1f}%)\n")
        f.write(f"ROI: {roi:+.2f}% | Profit: ${total_profit:,.2f}\n")
        f.write(f"Avg CLV: {avg_clv:+.2f}% | Positive CLV: {positive_clv}/{len(filtered)}\n")

    print(f"\n  Results saved to {results_dir}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_backtest()

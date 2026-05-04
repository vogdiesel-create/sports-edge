#!/usr/bin/env python3
"""
NHL Feature-Rich Model: Market Correction Approach
====================================================

Instead of predicting from scratch, this model:
1. Uses Pinnacle closing line as the baseline (market's best estimate)
2. Engineers features from game history that the market may underweight
3. XGBoost learns WHEN and HOW MUCH the market is wrong
4. Targets: both totals and moneyline

Key features the Dixon-Coles model was missing:
- Rest days / back-to-back detection
- Recent form (L5, L10 rolling averages)
- Home/away scoring splits
- Scoring volatility (variance of recent totals)
- Pinnacle line itself as anchor
- Team total lines (home_totals, away_totals)
- Market-implied team strength differential
- Season context (early season vs late, playoffs)
"""

import math
import os
import sqlite3
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.stats import poisson

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("ERROR: xgboost required. pip install xgboost")
    sys.exit(1)

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss

warnings.filterwarnings("ignore")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")
BET_SIZE = 100
MIN_HISTORY = 50  # minimum games a team must have before we generate features


def load_all_nhl_games():
    """Load all NHL games with closing lines from Pinnacle."""
    conn = sqlite3.connect(DB_PATH)

    # Get game results + totals closing
    games_raw = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away, total_goals, line,
               todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='totals' AND period=0
        AND score_home IS NOT NULL AND score_away IS NOT NULL
        ORDER BY game_date, event_id
    """).fetchall()

    # Deduplicate - take the main line (closest to even odds)
    seen = {}
    for r in games_raw:
        eid = r[0]
        if eid not in seen:
            seen[eid] = r
        else:
            # Pick line with most balanced odds
            old = seen[eid]
            old_balance = abs((old[8] or 2) - (old[9] or 2))
            new_balance = abs((r[8] or 2) - (r[9] or 2))
            if new_balance < old_balance:
                seen[eid] = r

    games = []
    for eid, r in seen.items():
        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": r[2],
            "away_team": r[3],
            "home_score": r[4],
            "away_score": r[5],
            "total_goals": r[6],
            "closing_line": r[7],
            "todds_over": r[8],
            "todds_under": r[9],
        })

    df = pd.DataFrame(games)
    df = df.sort_values("game_date").reset_index(drop=True)

    # Now load moneyline odds per event
    ml_data = {}
    ml_rows = conn.execute("""
        SELECT event_id, todds_over, todds_under, odds_over, odds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='moneyline' AND period=0
    """).fetchall()
    for r in ml_rows:
        ml_data[r[0]] = {
            "ml_todds_home": r[1], "ml_todds_away": r[2],
            "ml_odds_home": r[3], "ml_odds_away": r[4],
        }

    # Load team totals (home_totals, away_totals)
    ht_data = {}
    ht_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='home_totals' AND period=0
    """).fetchall()
    for r in ht_rows:
        ht_data[r[0]] = {"ht_line": r[1], "ht_todds_o": r[2], "ht_todds_u": r[3]}

    at_data = {}
    at_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='away_totals' AND period=0
    """).fetchall()
    for r in at_rows:
        at_data[r[0]] = {"at_line": r[1], "at_todds_o": r[2], "at_todds_u": r[3]}

    # Spread data
    spread_data = {}
    sp_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='NHL' AND market='spread' AND period=0
        AND ABS(line) = 1.5
    """).fetchall()
    for r in sp_rows:
        eid = r[0]
        if r[1] < 0:  # home favorite spread
            spread_data[eid] = {"spread_line": r[1], "sp_todds_fav": r[2], "sp_todds_dog": r[3]}

    conn.close()

    # Merge
    for i, row in df.iterrows():
        eid = row["event_id"]
        ml = ml_data.get(eid, {})
        ht = ht_data.get(eid, {})
        at = at_data.get(eid, {})
        sp = spread_data.get(eid, {})
        for k, v in {**ml, **ht, **at, **sp}.items():
            df.at[i, k] = v

    print(f"Loaded {len(df)} NHL games ({df['game_date'].min()} to {df['game_date'].max()})")
    return df


def engineer_features(df):
    """
    Build features from game history for each game.
    All features are computed using ONLY data available BEFORE the game.
    """
    # Build team history index
    team_games = defaultdict(list)  # team -> list of (idx, is_home, score_for, score_against, date)

    features = []
    feature_names = None

    for i in range(len(df)):
        game = df.iloc[i]
        home = game["home_team"]
        away = game["away_team"]
        date = game["game_date"]

        h_hist = team_games[home]
        a_hist = team_games[away]

        # Need minimum history
        if len(h_hist) < MIN_HISTORY or len(a_hist) < MIN_HISTORY:
            features.append(None)
            # Still record game for history
            team_games[home].append((i, True, game["home_score"], game["away_score"], date))
            team_games[away].append((i, False, game["away_score"], game["home_score"], date))
            continue

        f = {}

        # --- Market features (Pinnacle's view) ---
        f["closing_total_line"] = game.get("closing_line", 5.5)

        # Devigged implied over probability
        to = game.get("todds_over")
        tu = game.get("todds_under")
        if to and tu and to > 1 and tu > 1:
            impl_o = 1.0 / to
            impl_u = 1.0 / tu
            f["market_impl_over"] = impl_o / (impl_o + impl_u)
        else:
            f["market_impl_over"] = 0.5

        # Moneyline implied
        ml_h = game.get("ml_todds_home")
        ml_a = game.get("ml_todds_away")
        if ml_h and ml_a and ml_h > 1 and ml_a > 1:
            ih = 1.0 / ml_h
            ia = 1.0 / ml_a
            f["market_impl_home_win"] = ih / (ih + ia)
        else:
            f["market_impl_home_win"] = 0.5

        # Team totals
        ht_line = game.get("ht_line")
        at_line = game.get("at_line")
        f["home_team_total_line"] = ht_line if ht_line and not pd.isna(ht_line) else f["closing_total_line"] / 2
        f["away_team_total_line"] = at_line if at_line and not pd.isna(at_line) else f["closing_total_line"] / 2

        # Line - sum of team totals discrepancy
        f["team_totals_sum_vs_line"] = (f["home_team_total_line"] + f["away_team_total_line"]) - f["closing_total_line"]

        # Spread
        sp_line = game.get("spread_line")
        f["spread_line"] = sp_line if sp_line and not pd.isna(sp_line) else 0

        # --- Team history features ---
        for label, hist in [("home", h_hist), ("away", a_hist)]:
            scores_for = [h[2] for h in hist]
            scores_against = [h[3] for h in hist]
            totals = [h[2] + h[3] for h in hist]
            dates = [h[4] for h in hist]
            is_home_flags = [h[1] for h in hist]

            # Rolling averages
            for window_name, window in [("l5", 5), ("l10", 10), ("l20", 20), ("season", len(hist))]:
                recent_for = scores_for[-window:]
                recent_against = scores_against[-window:]
                recent_totals = totals[-window:]

                f[f"{label}_gf_{window_name}"] = np.mean(recent_for)
                f[f"{label}_ga_{window_name}"] = np.mean(recent_against)
                f[f"{label}_total_{window_name}"] = np.mean(recent_totals)

                if window_name != "season":
                    f[f"{label}_gf_std_{window_name}"] = np.std(recent_for) if len(recent_for) > 1 else 0
                    f[f"{label}_total_std_{window_name}"] = np.std(recent_totals) if len(recent_totals) > 1 else 0

            # Win rate
            wins = sum(1 for h in hist if h[2] > h[3])
            f[f"{label}_win_pct"] = wins / len(hist)
            wins_l10 = sum(1 for h in hist[-10:] if h[2] > h[3])
            f[f"{label}_win_pct_l10"] = wins_l10 / min(10, len(hist))

            # Home/away splits
            home_games = [(h[2], h[3]) for h in hist if h[1]]
            away_games = [(h[2], h[3]) for h in hist if not h[1]]
            if home_games:
                f[f"{label}_home_gf"] = np.mean([g[0] for g in home_games])
                f[f"{label}_home_ga"] = np.mean([g[1] for g in home_games])
            else:
                f[f"{label}_home_gf"] = np.mean(scores_for)
                f[f"{label}_home_ga"] = np.mean(scores_against)
            if away_games:
                f[f"{label}_away_gf"] = np.mean([g[0] for g in away_games])
                f[f"{label}_away_ga"] = np.mean([g[1] for g in away_games])
            else:
                f[f"{label}_away_gf"] = np.mean(scores_for)
                f[f"{label}_away_ga"] = np.mean(scores_against)

            # Streak
            streak = 0
            for h in reversed(hist):
                if h[2] > h[3]:
                    streak += 1
                else:
                    break
            f[f"{label}_win_streak"] = streak

            loss_streak = 0
            for h in reversed(hist):
                if h[2] < h[3]:
                    loss_streak += 1
                else:
                    break
            f[f"{label}_loss_streak"] = loss_streak

            # Rest days
            last_date = dates[-1]
            try:
                d1 = datetime.strptime(date, "%Y-%m-%d")
                d2 = datetime.strptime(last_date, "%Y-%m-%d")
                rest = (d1 - d2).days
            except:
                rest = 2
            f[f"{label}_rest_days"] = min(rest, 10)  # cap at 10
            f[f"{label}_b2b"] = 1 if rest <= 1 else 0

            # Games played (season context)
            f[f"{label}_games_played"] = len(hist)

            # Scoring trend (L5 vs L20)
            if len(scores_for) >= 20:
                f[f"{label}_gf_trend"] = np.mean(scores_for[-5:]) - np.mean(scores_for[-20:])
                f[f"{label}_ga_trend"] = np.mean(scores_against[-5:]) - np.mean(scores_against[-20:])
            else:
                f[f"{label}_gf_trend"] = 0
                f[f"{label}_ga_trend"] = 0

        # --- Matchup / differential features ---
        f["gf_diff_season"] = f["home_gf_season"] - f["away_gf_season"]
        f["ga_diff_season"] = f["home_ga_season"] - f["away_ga_season"]
        f["gf_diff_l10"] = f["home_gf_l10"] - f["away_gf_l10"]
        f["total_diff_l10"] = f["home_total_l10"] - f["away_total_l10"]
        f["win_pct_diff"] = f["home_win_pct"] - f["away_win_pct"]
        f["win_pct_l10_diff"] = f["home_win_pct_l10"] - f["away_win_pct_l10"]
        f["rest_diff"] = f["home_rest_days"] - f["away_rest_days"]
        f["b2b_diff"] = f["home_b2b"] - f["away_b2b"]

        # Expected total from recent form
        f["form_expected_total"] = (f["home_gf_l10"] + f["away_gf_l10"] +
                                     f["home_ga_l10"] + f["away_ga_l10"]) / 2
        f["form_vs_line"] = f["form_expected_total"] - f["closing_total_line"]

        # Volatility indicators
        f["combined_total_std_l10"] = f["home_total_std_l10"] + f["away_total_std_l10"]

        # Season month (1-12)
        try:
            f["month"] = int(date.split("-")[1])
        except:
            f["month"] = 1

        features.append(f)

        # Record game for future history
        team_games[home].append((i, True, game["home_score"], game["away_score"], date))
        team_games[away].append((i, False, game["away_score"], game["home_score"], date))

    return features


def build_dataset(df, features, target="totals"):
    """Build X, y arrays from features. target='totals' or 'moneyline'."""
    X_rows = []
    y_rows = []
    indices = []

    for i, f in enumerate(features):
        if f is None:
            continue

        game = df.iloc[i]

        if target == "totals":
            line = game.get("closing_line", 5.5)
            actual = game["total_goals"]
            if actual == line:  # push
                continue
            y = 1 if actual > line else 0
        elif target == "moneyline":
            y = 1 if game["home_score"] > game["away_score"] else 0

        X_rows.append(f)
        y_rows.append(y)
        indices.append(i)

    X = pd.DataFrame(X_rows)
    y = np.array(y_rows)
    return X, y, indices


def run_backtest(target="totals"):
    """Walk-forward backtest with expanding window."""
    df = load_all_nhl_games()
    print("Engineering features...")
    features = engineer_features(df)

    valid_count = sum(1 for f in features if f is not None)
    print(f"Valid feature rows: {valid_count} / {len(features)}")

    X, y, indices = build_dataset(df, features, target=target)
    print(f"Dataset: {len(X)} samples, {X.shape[1]} features")
    print(f"Target distribution: {y.mean():.3f} positive rate")

    # Walk-forward: train on first N, test on next chunk
    MIN_TRAIN = 1500
    TEST_CHUNK = 200  # retrain every 200 games

    bets = []
    all_preds = []

    i = MIN_TRAIN
    while i < len(X):
        test_end = min(i + TEST_CHUNK, len(X))

        X_train = X.iloc[:i]
        y_train = y[:i]
        X_test = X.iloc[i:test_end]
        y_test = y[i:test_end]
        test_indices = indices[i:test_end]

        # XGBoost with conservative hyperparameters
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=2.0,
            min_child_weight=10,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        model.fit(X_train, y_train)

        preds = model.predict_proba(X_test)[:, 1]

        for j, (pred, actual, game_idx) in enumerate(zip(preds, y_test, test_indices)):
            game = df.iloc[game_idx]
            all_preds.append({"pred": pred, "actual": actual})

            if target == "totals":
                to = game.get("todds_over")
                tu = game.get("todds_under")
                if not to or not tu or to <= 1 or tu <= 1:
                    continue

                impl_o = 1.0 / to
                impl_u = 1.0 / tu
                devig_o = impl_o / (impl_o + impl_u)
                devig_u = 1 - devig_o

                edge_over = pred - devig_o
                edge_under = (1 - pred) - devig_u

                line = game["closing_line"]
                actual_total = game["total_goals"]

                if edge_over > 0 and edge_over >= edge_under:
                    won = actual_total > line
                    push = actual_total == line
                    profit = 0 if push else (BET_SIZE * (to - 1) if won else -BET_SIZE)
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "OVER", "line": line,
                        "model_prob": pred, "market_prob": devig_o,
                        "edge": edge_over, "won": won, "push": push,
                        "profit": profit, "odds": to,
                    })
                elif edge_under > 0:
                    won = actual_total < line
                    push = actual_total == line
                    profit = 0 if push else (BET_SIZE * (tu - 1) if won else -BET_SIZE)
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "UNDER", "line": line,
                        "model_prob": 1 - pred, "market_prob": devig_u,
                        "edge": edge_under, "won": won, "push": push,
                        "profit": profit, "odds": tu,
                    })

            elif target == "moneyline":
                ml_h = game.get("ml_todds_home")
                ml_a = game.get("ml_todds_away")
                if not ml_h or not ml_a or ml_h <= 1 or ml_a <= 1:
                    continue

                ih = 1.0 / ml_h
                ia = 1.0 / ml_a
                devig_h = ih / (ih + ia)
                devig_a = 1 - devig_h

                edge_home = pred - devig_h
                edge_away = (1 - pred) - devig_a

                home_won = game["home_score"] > game["away_score"]

                if edge_home > 0 and edge_home >= edge_away:
                    won = home_won
                    profit = BET_SIZE * (ml_h - 1) if won else -BET_SIZE
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "HOME",
                        "model_prob": pred, "market_prob": devig_h,
                        "edge": edge_home, "won": won, "push": False,
                        "profit": profit, "odds": ml_h,
                    })
                elif edge_away > 0:
                    won = not home_won
                    profit = BET_SIZE * (ml_a - 1) if won else -BET_SIZE
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "AWAY",
                        "model_prob": 1 - pred, "market_prob": devig_a,
                        "edge": edge_away, "won": won, "push": False,
                        "profit": profit, "odds": ml_a,
                    })

        i = test_end

    # Print feature importance
    print(f"\nTop 20 features:")
    importance = model.feature_importances_
    feat_imp = sorted(zip(X.columns, importance), key=lambda x: x[1], reverse=True)
    for fname, imp in feat_imp[:20]:
        print(f"  {fname:40s} {imp:.4f}")

    # Calibration check
    if all_preds:
        preds_arr = np.array([p["pred"] for p in all_preds])
        actuals_arr = np.array([p["actual"] for p in all_preds])
        try:
            ll = log_loss(actuals_arr, preds_arr)
            bs = brier_score_loss(actuals_arr, preds_arr)
            print(f"\nCalibration: log_loss={ll:.4f}, brier_score={bs:.4f}")
        except:
            pass

    # Results
    print(f"\n{'='*60}")
    print(f"  NHL {target.upper()} - FEATURE-RICH XGBoost vs PINNACLE")
    print(f"{'='*60}")
    print(f"  Total bets: {len(bets)}")

    if not bets:
        print("  No bets generated.")
        return

    thresholds = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15]
    print(f"\n  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} "
          f"{'Profit':>10} {'ROI':>8} {'AvgEdge':>8}")
    print(f"  {'-'*60}")

    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh]
        if not tb:
            continue
        tw = sum(1 for b in tb if b["won"])
        tl = sum(1 for b in tb if not b["won"] and not b.get("push", False))
        tp = sum(1 for b in tb if b.get("push", False))
        tprofit = sum(b["profit"] for b in tb)
        twagered = BET_SIZE * (len(tb) - tp)
        troi = (tprofit / twagered * 100) if twagered > 0 else 0
        twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
        avg_edge = np.mean([b["edge"] for b in tb]) * 100
        print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} "
              f"{twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}% {avg_edge:>+6.1f}%")

    # Side breakdown
    if target == "totals":
        for side in ["OVER", "UNDER"]:
            print(f"\n  --- {side}-only ---")
            for thresh in [0.01, 0.03, 0.05, 0.07, 0.10]:
                tb = [b for b in bets if b["edge"] >= thresh and b["side"] == side]
                if not tb:
                    continue
                tw = sum(1 for b in tb if b["won"])
                tl = sum(1 for b in tb if not b["won"] and not b.get("push"))
                tp = sum(1 for b in tb if b.get("push"))
                tprofit = sum(b["profit"] for b in tb)
                twagered = BET_SIZE * (len(tb) - tp)
                troi = (tprofit / twagered * 100) if twagered > 0 else 0
                twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
                print(f"    {thresh*100:>4.0f}%: {len(tb):>5}B {tw}W {tl}L "
                      f"({twr:.1f}%) ${tprofit:+.0f} ROI {troi:+.1f}%")

    elif target == "moneyline":
        for side in ["HOME", "AWAY"]:
            print(f"\n  --- {side}-only ---")
            for thresh in [0.01, 0.03, 0.05, 0.07, 0.10]:
                tb = [b for b in bets if b["edge"] >= thresh and b["side"] == side]
                if not tb:
                    continue
                tw = sum(1 for b in tb if b["won"])
                tl = len(tb) - tw
                tprofit = sum(b["profit"] for b in tb)
                twagered = BET_SIZE * len(tb)
                troi = (tprofit / twagered * 100) if twagered > 0 else 0
                twr = tw / len(tb) * 100
                print(f"    {thresh*100:>4.0f}%: {len(tb):>5}B {tw}W {tl}L "
                      f"({twr:.1f}%) ${tprofit:+.0f} ROI {troi:+.1f}%")

    # Yearly breakdown
    best_thresh = 0.03
    filtered = [b for b in bets if b["edge"] >= best_thresh]
    if filtered:
        print(f"\n  Yearly (at {best_thresh*100:.0f}%):")
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

    # Save bets
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)
    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, f"nhl_feature_{target}_bets.csv")
    bets_df.to_csv(csv_path, index=False)
    print(f"\n  Saved to {csv_path}")
    print(f"{'='*60}")

    return bets


class NHLFeaturePredictor:
    """
    Live prediction engine using the feature-rich XGBoost model.

    Trains on all historical Pinnacle data, then predicts today's games
    using current market lines from sports_edge.db.
    """

    def __init__(self):
        self.totals_model = None
        self.ml_model = None
        self.feature_names = None
        self.fitted = False
        self._df = None
        self._features = None
        self._team_games = None

    def fit(self):
        """Train models on all historical data."""
        self._df = load_all_nhl_games()
        self._features = engineer_features(self._df)

        # Build and train totals model
        X_tot, y_tot, _ = build_dataset(self._df, self._features, target="totals")
        if len(X_tot) < 500:
            print(f"  [NHL Feature] Not enough data to train ({len(X_tot)} samples)")
            return

        self.feature_names = list(X_tot.columns)
        self.totals_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=1.0, reg_lambda=2.0, min_child_weight=10,
            eval_metric="logloss", random_state=42, verbosity=0,
        )
        self.totals_model.fit(X_tot, y_tot)

        # Build and train moneyline model
        X_ml, y_ml, _ = build_dataset(self._df, self._features, target="moneyline")
        self.ml_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=1.0, reg_lambda=2.0, min_child_weight=10,
            eval_metric="logloss", random_state=42, verbosity=0,
        )
        self.ml_model.fit(X_ml, y_ml)

        self.fitted = True
        print(f"  [NHL Feature] Trained on {len(X_tot)} totals + {len(X_ml)} ML samples, {len(self.feature_names)} features")

    def _build_team_history(self):
        """Rebuild team history from all loaded games for feature engineering."""
        if self._team_games is not None:
            return self._team_games

        team_games = defaultdict(list)
        for i in range(len(self._df)):
            game = self._df.iloc[i]
            home = game["home_team"]
            away = game["away_team"]
            date = game["game_date"]
            team_games[home].append((i, True, game["home_score"], game["away_score"], date))
            team_games[away].append((i, False, game["away_score"], game["home_score"], date))

        self._team_games = team_games
        return team_games

    def _engineer_single_game(self, home_team, away_team, game_date, market_data):
        """
        Engineer features for a single upcoming game.

        market_data: dict with keys like closing_line, todds_over, todds_under,
                     ml_todds_home, ml_todds_away, ht_line, at_line, spread_line
        """
        team_games = self._build_team_history()
        h_hist = team_games.get(home_team, [])
        a_hist = team_games.get(away_team, [])

        if len(h_hist) < MIN_HISTORY or len(a_hist) < MIN_HISTORY:
            return None

        f = {}

        # Market features
        f["closing_total_line"] = market_data.get("closing_line", 5.5)

        to = market_data.get("todds_over")
        tu = market_data.get("todds_under")
        if to and tu and to > 1 and tu > 1:
            impl_o = 1.0 / to
            impl_u = 1.0 / tu
            f["market_impl_over"] = impl_o / (impl_o + impl_u)
        else:
            f["market_impl_over"] = 0.5

        ml_h = market_data.get("ml_todds_home")
        ml_a = market_data.get("ml_todds_away")
        if ml_h and ml_a and ml_h > 1 and ml_a > 1:
            ih = 1.0 / ml_h
            ia = 1.0 / ml_a
            f["market_impl_home_win"] = ih / (ih + ia)
        else:
            f["market_impl_home_win"] = 0.5

        ht_line = market_data.get("ht_line")
        at_line = market_data.get("at_line")
        f["home_team_total_line"] = ht_line if ht_line else f["closing_total_line"] / 2
        f["away_team_total_line"] = at_line if at_line else f["closing_total_line"] / 2
        f["team_totals_sum_vs_line"] = (f["home_team_total_line"] + f["away_team_total_line"]) - f["closing_total_line"]

        sp_line = market_data.get("spread_line")
        f["spread_line"] = sp_line if sp_line else 0

        # Team history features (same logic as engineer_features)
        for label, hist in [("home", h_hist), ("away", a_hist)]:
            scores_for = [h[2] for h in hist]
            scores_against = [h[3] for h in hist]
            totals = [h[2] + h[3] for h in hist]
            dates = [h[4] for h in hist]

            for window_name, window in [("l5", 5), ("l10", 10), ("l20", 20), ("season", len(hist))]:
                recent_for = scores_for[-window:]
                recent_against = scores_against[-window:]
                recent_totals = totals[-window:]
                f[f"{label}_gf_{window_name}"] = np.mean(recent_for)
                f[f"{label}_ga_{window_name}"] = np.mean(recent_against)
                f[f"{label}_total_{window_name}"] = np.mean(recent_totals)
                if window_name != "season":
                    f[f"{label}_gf_std_{window_name}"] = np.std(recent_for) if len(recent_for) > 1 else 0
                    f[f"{label}_total_std_{window_name}"] = np.std(recent_totals) if len(recent_totals) > 1 else 0

            wins = sum(1 for h in hist if h[2] > h[3])
            f[f"{label}_win_pct"] = wins / len(hist)
            wins_l10 = sum(1 for h in hist[-10:] if h[2] > h[3])
            f[f"{label}_win_pct_l10"] = wins_l10 / min(10, len(hist))

            home_games = [(h[2], h[3]) for h in hist if h[1]]
            away_games = [(h[2], h[3]) for h in hist if not h[1]]
            if home_games:
                f[f"{label}_home_gf"] = np.mean([g[0] for g in home_games])
                f[f"{label}_home_ga"] = np.mean([g[1] for g in home_games])
            else:
                f[f"{label}_home_gf"] = np.mean(scores_for)
                f[f"{label}_home_ga"] = np.mean(scores_against)
            if away_games:
                f[f"{label}_away_gf"] = np.mean([g[0] for g in away_games])
                f[f"{label}_away_ga"] = np.mean([g[1] for g in away_games])
            else:
                f[f"{label}_away_gf"] = np.mean(scores_for)
                f[f"{label}_away_ga"] = np.mean(scores_against)

            streak = 0
            for h in reversed(hist):
                if h[2] > h[3]:
                    streak += 1
                else:
                    break
            f[f"{label}_win_streak"] = streak
            loss_streak = 0
            for h in reversed(hist):
                if h[2] < h[3]:
                    loss_streak += 1
                else:
                    break
            f[f"{label}_loss_streak"] = loss_streak

            last_date = dates[-1]
            try:
                d1 = datetime.strptime(game_date, "%Y-%m-%d")
                d2 = datetime.strptime(last_date, "%Y-%m-%d")
                rest = (d1 - d2).days
            except:
                rest = 2
            f[f"{label}_rest_days"] = min(rest, 10)
            f[f"{label}_b2b"] = 1 if rest <= 1 else 0
            f[f"{label}_games_played"] = len(hist)

            if len(scores_for) >= 20:
                f[f"{label}_gf_trend"] = np.mean(scores_for[-5:]) - np.mean(scores_for[-20:])
                f[f"{label}_ga_trend"] = np.mean(scores_against[-5:]) - np.mean(scores_against[-20:])
            else:
                f[f"{label}_gf_trend"] = 0
                f[f"{label}_ga_trend"] = 0

        # Matchup differentials
        f["gf_diff_season"] = f["home_gf_season"] - f["away_gf_season"]
        f["ga_diff_season"] = f["home_ga_season"] - f["away_ga_season"]
        f["gf_diff_l10"] = f["home_gf_l10"] - f["away_gf_l10"]
        f["total_diff_l10"] = f["home_total_l10"] - f["away_total_l10"]
        f["win_pct_diff"] = f["home_win_pct"] - f["away_win_pct"]
        f["win_pct_l10_diff"] = f["home_win_pct_l10"] - f["away_win_pct_l10"]
        f["rest_diff"] = f["home_rest_days"] - f["away_rest_days"]
        f["b2b_diff"] = f["home_b2b"] - f["away_b2b"]
        f["form_expected_total"] = (f["home_gf_l10"] + f["away_gf_l10"] +
                                     f["home_ga_l10"] + f["away_ga_l10"]) / 2
        f["form_vs_line"] = f["form_expected_total"] - f["closing_total_line"]
        f["combined_total_std_l10"] = f["home_total_std_l10"] + f["away_total_std_l10"]

        try:
            f["month"] = int(game_date.split("-")[1])
        except:
            f["month"] = 1

        return f

    def predict_today(self):
        """
        Predict all today's NHL games using current market lines.
        Returns list of prediction dicts with edges for both totals and moneyline.

        Uses game_line_snapshots as primary game source (has actual market data)
        with nhl_schedule as fallback.
        """
        if not self.fitted:
            return []

        from nhl_model import TEAM_FULL_TO_ABBREV, TEAM_ABBREV_TO_FULL

        se_db = os.path.join(DATA_DIR, "sports_edge.db")
        if not os.path.exists(se_db):
            print("  [NHL Feature] sports_edge.db not found")
            return []

        conn = sqlite3.connect(se_db)
        conn.row_factory = sqlite3.Row
        today = datetime.now().strftime("%Y-%m-%d")

        # Get unique games from line snapshots (most reliable source)
        game_rows = conn.execute("""
            SELECT DISTINCT home_team, away_team
            FROM game_line_snapshots
            WHERE sport='NHL' AND game_date=?
        """, (today,)).fetchall()

        # Deduplicate by abbreviation
        seen_games = set()
        games = []
        for r in game_rows:
            h_abbr = TEAM_FULL_TO_ABBREV.get(r["home_team"], r["home_team"])
            a_abbr = TEAM_FULL_TO_ABBREV.get(r["away_team"], r["away_team"])
            key = (h_abbr, a_abbr)
            if key not in seen_games:
                seen_games.add(key)
                games.append((h_abbr, a_abbr))

        # Fallback to schedule if no line snapshots
        if not games:
            schedule = conn.execute(
                "SELECT home_team, away_team FROM nhl_schedule WHERE game_date = ?",
                (today,)
            ).fetchall()
            for g in schedule:
                games.append((g["home_team"], g["away_team"]))

        if not games:
            conn.close()
            return []

        predictions = []
        for home_abbr, away_abbr in games:
            home_full = TEAM_ABBREV_TO_FULL.get(home_abbr, home_abbr)
            away_full = TEAM_ABBREV_TO_FULL.get(away_abbr, away_abbr)

            # Get Pinnacle market lines from game_line_snapshots
            market = self._get_market_data(conn, today, home_full, away_full, home_abbr, away_abbr)
            if not market.get("closing_line"):
                continue

            # Engineer features
            feats = self._engineer_single_game(home_full, away_full, today, market)
            if feats is None:
                continue

            # Build feature vector matching training columns
            X = pd.DataFrame([feats])
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_names]

            # Predict totals
            p_over = self.totals_model.predict_proba(X)[0, 1]

            # Predict moneyline (home win prob)
            p_home_win = self.ml_model.predict_proba(X)[0, 1]

            # Devig market probabilities
            to = market.get("todds_over")
            tu = market.get("todds_under")
            ml_h = market.get("ml_todds_home")
            ml_a = market.get("ml_todds_away")

            # --- Totals edge ---
            if to and tu and to > 1 and tu > 1:
                impl_o = 1.0 / to
                impl_u = 1.0 / tu
                devig_o = impl_o / (impl_o + impl_u)
                devig_u = 1 - devig_o

                edge_over = p_over - devig_o
                edge_under = (1 - p_over) - devig_u

                # Totals pick
                if edge_over > 0 or edge_under > 0:
                    if edge_over >= edge_under:
                        side = "OVER"
                        edge = edge_over
                        our_prob = p_over
                        odds = market.get("over_odds", -110)
                    else:
                        side = "UNDER"
                        edge = edge_under
                        our_prob = 1 - p_over
                        odds = market.get("under_odds", -110)

                    predictions.append({
                        "source": "nhl_feature",
                        "sport": "NHL",
                        "market_type": "totals",
                        "game": f"{away_abbr} @ {home_abbr}",
                        "home_team": home_abbr,
                        "away_team": away_abbr,
                        "side": side,
                        "market_line": market["closing_line"],
                        "odds": int(odds) if odds else -110,
                        "model_total": round(float(market["closing_line"]), 1),
                        "our_prob": round(float(our_prob), 4),
                        "edge": round(float(edge), 4),
                        "p_over": round(float(p_over), 4),
                        "model_confidence": round(float(max(p_over, 1 - p_over)), 4),
                    })

            # --- Moneyline edge ---
            if ml_h and ml_a and ml_h > 1 and ml_a > 1:
                ih = 1.0 / ml_h
                ia = 1.0 / ml_a
                devig_h = ih / (ih + ia)
                devig_a = 1 - devig_h

                edge_home = p_home_win - devig_h
                edge_away = (1 - p_home_win) - devig_a

                if edge_home > 0 or edge_away > 0:
                    if edge_home >= edge_away:
                        side = "HOME"
                        edge = edge_home
                        our_prob = p_home_win
                        odds = market.get("ml_home_odds", -110)
                    else:
                        side = "AWAY"
                        edge = edge_away
                        our_prob = 1 - p_home_win
                        odds = market.get("ml_away_odds", -110)

                    predictions.append({
                        "source": "nhl_feature",
                        "sport": "NHL",
                        "market_type": "moneyline",
                        "game": f"{away_abbr} @ {home_abbr}",
                        "home_team": home_abbr,
                        "away_team": away_abbr,
                        "side": side,
                        "market_line": None,
                        "odds": int(odds) if odds else -110,
                        "our_prob": round(float(our_prob), 4),
                        "edge": round(float(edge), 4),
                        "p_home_win": round(float(p_home_win), 4),
                        "model_confidence": round(float(max(p_home_win, 1 - p_home_win)), 4),
                    })

        conn.close()
        return predictions

    def _get_market_data(self, conn, game_date, home_full, away_full, home_abbr, away_abbr):
        """Extract market data for a game from game_line_snapshots."""
        market = {}

        from nhl_model import TEAM_FULL_TO_ABBREV

        # Try both full and short names, plus city-only
        name_pairs = [
            (home_full, away_full),
            (home_abbr, away_abbr),
        ]
        # City-only names (e.g., "Chicago" from "Chicago Blackhawks")
        for full in [home_full, away_full]:
            parts = full.rsplit(" ", 1)
            if len(parts) == 2:
                pass  # Will be tried below
        home_city = home_full.split(" ")[0] if " " in home_full else home_full
        away_city = away_full.split(" ")[0] if " " in away_full else away_full
        # Handle multi-word cities: "St. Louis", "New York", "San Jose", etc.
        for sep_count in [1, 2]:
            parts_h = home_full.split(" ")
            parts_a = away_full.split(" ")
            if len(parts_h) > sep_count:
                hc = " ".join(parts_h[:sep_count])
                name_pairs.append((hc, None))
            if len(parts_a) > sep_count:
                ac = " ".join(parts_a[:sep_count])
                name_pairs.append((None, ac))

        # Strategy: search by each pair, then fall back to matching any of the team's names
        books_priority = ["pinnacle", "consensus", "heritage", "betonline"]
        for book in books_priority:
            for h_name, a_name in name_pairs:
                if h_name is None or a_name is None:
                    continue
                rows = conn.execute("""
                    SELECT market, side, line, odds
                    FROM game_line_snapshots
                    WHERE sport='NHL' AND game_date=? AND book=?
                    AND home_team=? AND away_team=?
                    ORDER BY collected_at DESC
                """, (game_date, book, h_name, a_name)).fetchall()
                if rows:
                    self._parse_market_rows(rows, market)
                    if market.get("closing_line"):
                        return market

            # Fallback: search by LIKE for team abbreviation in home_team
            if not market.get("closing_line"):
                rows = conn.execute("""
                    SELECT market, side, line, odds, home_team, away_team
                    FROM game_line_snapshots
                    WHERE sport='NHL' AND game_date=? AND book=?
                    ORDER BY collected_at DESC
                """, (game_date, book)).fetchall()

                for r in rows:
                    h = TEAM_FULL_TO_ABBREV.get(r["home_team"], r["home_team"])
                    a = TEAM_FULL_TO_ABBREV.get(r["away_team"], r["away_team"])
                    if h == home_abbr and a == away_abbr:
                        self._parse_single_row(r, market)

                if market.get("closing_line"):
                    return market

        return market

    def _parse_market_rows(self, rows, market):
        """Parse market rows into market dict."""
        for r in rows:
            self._parse_single_row(r, market)

    def _parse_single_row(self, r, market):
        """Parse a single market row."""
        mkt = r["market"]
        side = r["side"]
        line = r["line"]
        odds = r["odds"]

        if mkt == "total":
            if side == "over" and line:
                if "closing_line" not in market:
                    market["closing_line"] = line
                    market["over_odds"] = odds
                    market["todds_over"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
            elif side == "under" and line:
                if "under_odds" not in market:
                    market["under_odds"] = odds
                    market["todds_under"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
        elif mkt == "moneyline":
            if side == "home" and "ml_home_odds" not in market:
                market["ml_home_odds"] = odds
                market["ml_todds_home"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
            elif side == "away" and "ml_away_odds" not in market:
                market["ml_away_odds"] = odds
                market["ml_todds_away"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
        elif mkt == "spread" and line and abs(line) == 1.5:
            if "spread_line" not in market:
                market["spread_line"] = line


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        # Live prediction mode
        print("\n=== NHL Feature Model - Live Predictions ===\n")
        predictor = NHLFeaturePredictor()
        predictor.fit()
        preds = predictor.predict_today()
        for p in preds:
            print(f"  {p['game']} | {p['market_type']} {p['side']} "
                  f"| edge: {p['edge']:.1%} | prob: {p['our_prob']:.1%}")
    else:
        target = sys.argv[1] if len(sys.argv) > 1 else "totals"
        print(f"\n=== Running NHL Feature Model backtest: {target} ===\n")
        run_backtest(target=target)

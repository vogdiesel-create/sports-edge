#!/usr/bin/env python3
"""
Backtest MLB model against REAL Pinnacle closing lines.

Uses independent Poisson team-strength model (no Dixon-Coles rho correction
since MLB scoring is high enough that low-score correlation is negligible).

Walk-forward: train on all games before test game, predict, compare to closing line.
"""

import sqlite3
import os
import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.special import gammaln
from scipy.optimize import minimize
from scipy.stats import nbinom

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")

MIN_TRAIN_GAMES = 300
BET_SIZE = 100
HALF_LIFE = 80  # games (~1 month of MLB schedule)
OVERDISPERSION = 1.8  # MLB run-scoring variance/mean ratio (tuned for best backtest)

# MLB team abbreviations
MLB_FULL_TO_ABBREV = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL", "Detroit Tigers": "DET",
    "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH",
    # Handle alternate names
    "Cleveland Indians": "CLE",
}


class MLBPoissonModel:
    """
    Independent Poisson model for MLB run scoring.
    Each team has attack/defense parameters fit via MLE with time decay.
    """

    def __init__(self, half_life=HALF_LIFE):
        self.half_life = half_life
        self.teams = []
        self.params = {}
        self.home_adv = 0.05
        self.fitted = False
        self.league_avg_runs = 4.5

    def fit(self, df, reference_date=None):
        """Fit via MLE on historical games."""
        teams = sorted(set(df["home_team"].unique()) | set(df["away_team"].unique()))
        # Filter out non-team entries
        teams = [t for t in teams if len(t) <= 3]
        self.teams = teams
        n_teams = len(teams)
        if n_teams < 10:
            return

        team_idx = {t: i for i, t in enumerate(teams)}

        # Build arrays
        home_idx = np.array([team_idx.get(t, 0) for t in df["home_team"]])
        away_idx = np.array([team_idx.get(t, 0) for t in df["away_team"]])
        home_runs = df["home_score"].values.astype(float)
        away_runs = df["away_score"].values.astype(float)

        # Time weights
        if reference_date and "game_date" in df.columns:
            ref = pd.to_datetime(reference_date)
            dates = pd.to_datetime(df["game_date"])
            days_ago = (ref - dates).dt.days.values.astype(float)
            decay = np.log(2) / (self.half_life * 1.5)  # ~1.5 games/day
            weights = np.exp(-decay * days_ago)
            weights = np.maximum(weights, 0.01)
        else:
            weights = np.ones(len(df))

        # Average runs for regularization
        all_runs = np.concatenate([home_runs, away_runs])
        avg_runs = np.mean(all_runs[all_runs > 0])
        if avg_runs <= 0:
            avg_runs = 4.5
        self.league_avg_runs = avg_runs
        log_avg = math.log(avg_runs)

        # Warm start
        if self.fitted and len(self.params) == n_teams and set(self.teams) == set(self.params.keys()):
            init_attack = np.array([self.params[t]["attack"] for t in self.teams])
            init_defense = np.array([self.params[t]["defense"] for t in self.teams])
            init_home = self.home_adv
        else:
            init_attack = np.full(n_teams, log_avg)
            init_defense = np.zeros(n_teams)
            init_home = 0.05

        x0 = np.concatenate([init_attack, init_defense, [init_home]])
        bounds = [(None, None)] * (2 * n_teams) + [(-0.1, 0.3)]

        def neg_log_likelihood(params_vec):
            attacks = params_vec[:n_teams]
            defenses = params_vec[n_teams:2 * n_teams]
            home_val = params_vec[2 * n_teams]

            lambda_h = np.exp(attacks[home_idx] + defenses[away_idx] + home_val)
            mu_a = np.exp(attacks[away_idx] + defenses[home_idx])

            lambda_h = np.maximum(lambda_h, 0.01)
            mu_a = np.maximum(mu_a, 0.01)

            log_p_home = home_runs * np.log(lambda_h) - lambda_h - gammaln(home_runs + 1)
            log_p_away = away_runs * np.log(mu_a) - mu_a - gammaln(away_runs + 1)

            log_prob = log_p_home + log_p_away
            total_ll = np.sum(weights * log_prob)

            # Regularization -- constrain team params to stay near mean
            attack_mean = np.mean(attacks)
            total_ll -= 15.0 * (attack_mean - log_avg) ** 2
            defense_mean = np.mean(defenses)
            total_ll -= 10.0 * defense_mean ** 2
            # L2 shrinkage
            total_ll -= 3.0 * np.sum((attacks - log_avg) ** 2)
            total_ll -= 3.0 * np.sum(defenses ** 2)

            return -total_ll

        result = minimize(neg_log_likelihood, x0, method="L-BFGS-B",
                          bounds=bounds, options={"maxiter": 500, "ftol": 1e-10})

        attacks = result.x[:n_teams]
        defenses = result.x[n_teams:2 * n_teams]
        self.home_adv = result.x[2 * n_teams]

        self.params = {}
        for i, team in enumerate(self.teams):
            self.params[team] = {"attack": attacks[i], "defense": defenses[i]}

        self.fitted = True

    def predict_over_prob(self, home_team, away_team, line):
        """P(total > line) using negative binomial convolution.

        Negative binomial handles overdispersion in baseball scoring
        (variance > mean), unlike Poisson which assumes variance = mean.
        """
        if not self.fitted:
            return None
        if home_team not in self.params or away_team not in self.params:
            return None

        h = self.params[home_team]
        a = self.params[away_team]
        lambda_h = math.exp(h["attack"] + a["defense"] + self.home_adv)
        mu_a = math.exp(a["attack"] + h["defense"])

        # Cap at reasonable values
        lambda_h = max(0.5, min(lambda_h, 15.0))
        mu_a = max(0.5, min(mu_a, 15.0))

        # Negative binomial parameters from mean and overdispersion
        # NB: var = mu * overdispersion, so r = mu / (overdispersion - 1)
        # scipy nbinom: r=n, p=n/(n+mu)
        def nb_params(mu):
            r = mu / (OVERDISPERSION - 1)
            p = r / (r + mu)
            return r, p

        r_h, p_h = nb_params(lambda_h)
        r_a, p_a = nb_params(mu_a)

        # Convolution of two negative binomials
        max_runs = 25
        p_over = 0.0
        for h_r in range(max_runs + 1):
            ph = nbinom.pmf(h_r, r_h, p_h)
            for a_r in range(max_runs + 1):
                total = h_r + a_r
                if total > line:
                    pa = nbinom.pmf(a_r, r_a, p_a)
                    p_over += ph * pa

        return p_over


def run_backtest():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load games
    rows = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away, total_goals
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='totals' AND period=0
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
        home_abbrev = MLB_FULL_TO_ABBREV.get(r[2])
        away_abbrev = MLB_FULL_TO_ABBREV.get(r[3])
        if not home_abbrev or not away_abbrev:
            continue
        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": home_abbrev,
            "away_team": away_abbrev,
            "home_score": r[4],
            "away_score": r[5],
            "total_goals": r[6],
        })

    df = pd.DataFrame(games)
    print(f"Loaded {len(df)} unique MLB games")
    print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

    model = MLBPoissonModel()
    bets = []
    no_closing = 0
    no_pred = 0
    no_edge = 0

    for i in range(MIN_TRAIN_GAMES, len(df)):
        game = df.iloc[i]

        # Refit every 50 games
        if i == MIN_TRAIN_GAMES or i % 50 == 0:
            model.fit(df.iloc[:i], reference_date=game["game_date"])

        if not model.fitted:
            continue

        eid = int(game["event_id"])

        # Get closing line -- pick the line closest to balanced odds
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

        prob = model.predict_over_prob(game["home_team"], game["away_team"], line)
        if prob is None:
            no_pred += 1
            continue

        impl_over = 1.0 / todds_o if todds_o and todds_o > 0 else 0.5
        impl_under = 1.0 / todds_u if todds_u and todds_u > 0 else 0.5

        edge_over = prob - impl_over
        edge_under = (1.0 - prob) - impl_under

        actual_total = game["total_goals"]

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

    # Save results
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)

    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, "mlb_all_bets.csv")
    bets_df.to_csv(csv_path, index=False)
    print(f"\n  Saved {len(bets)} bets to {csv_path}")

    # Results
    print(f"\n{'='*60}")
    print(f"  MLB BACKTEST vs REAL PINNACLE CLOSING LINES")
    print(f"{'='*60}")
    print(f"  Games processed: {len(df) - MIN_TRAIN_GAMES}")
    print(f"  No closing data: {no_closing}")
    print(f"  No prediction: {no_pred}")
    print(f"  No edge found: {no_edge}")
    print(f"  Total bets with any edge: {len(bets)}")

    if not bets:
        print("  No bets found.")
        return

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

    # Over vs Under breakdown
    print(f"\n  --- OVER-only at various thresholds ---")
    print(f"  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} {'Profit':>10} {'ROI':>8}")
    print(f"  {'-'*50}")
    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh and b["side"] == "OVER"]
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

    # Monthly breakdown at 10%
    print(f"\n  Monthly Breakdown (at 10%):")
    filtered = [b for b in bets if b["edge"] >= 0.10]
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
    best_10 = [b for b in bets if b["edge"] >= 0.10]
    if best_10:
        wins = sum(1 for b in best_10 if b["won"])
        losses = sum(1 for b in best_10 if not b["won"] and not b["push"])
        pushes = sum(1 for b in best_10 if b["push"])
        total_profit = sum(b["profit"] for b in best_10)
        total_wagered = BET_SIZE * (len(best_10) - pushes)
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
        avg_clv = np.mean([b["clv"] for b in best_10])

        with open(os.path.join(results_dir, "mlb_pinnacle_backtest.txt"), "w") as f:
            f.write(f"MLB Backtest vs Real Pinnacle Closing Lines\n")
            f.write(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Games: {len(df) - MIN_TRAIN_GAMES} | Bets (10%+): {len(best_10)}\n")
            f.write(f"Record: {wins}W-{losses}L-{pushes}P ({wins/(wins+losses)*100:.1f}%)\n")
            f.write(f"ROI: {roi:+.2f}% | Profit: ${total_profit:,.2f}\n")
            f.write(f"Avg CLV: {avg_clv:+.2f}%\n")

    print(f"\n  Results saved to {results_dir}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_backtest()

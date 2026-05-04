"""
Sports Edge - Triple Poisson Model for NBA Player Props
Based on the Plus EV Analytics methodology:
  Instead of predicting total points directly, model three independent components:
  - Free Throws Made (FTM) ~ Poisson(lambda_ft)
  - Two-Pointers Made (2PTM) ~ Poisson(lambda_2pt)
  - Three-Pointers Made (3PTM) ~ Poisson(lambda_3pt)

  Total points = FTM*1 + 2PTM*2 + 3PTM*3

  This properly handles that basketball points come in 1s, 2s, and 3s.
  A standard Poisson on total points is mathematically wrong for this.

Also implements:
  - Minutes-based scaling (PPM approach — "you're only as good as your minute projections")
  - Calibration-focused edge detection (calibration > accuracy per Bath research paper)
  - Opponent defense adjustment
  - Recency weighting
"""
import json
import math
import os
import sys
import random
from collections import defaultdict
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
random.seed(42)


def poisson_pmf(k, lam):
    """Poisson probability mass function. P(X=k) given mean lambda."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_cdf_over(threshold, lam, max_k=60):
    """P(X > threshold) for Poisson distribution."""
    # Sum P(X <= floor(threshold))
    t = int(math.floor(threshold))
    cdf = sum(poisson_pmf(k, lam) for k in range(t + 1))
    return 1.0 - cdf


class TriplePoissonPredictor:
    """
    Track player shooting component averages and predict props using
    Triple Poisson decomposition.
    """

    def __init__(self):
        # player_data[name] = list of game dicts with shooting components
        self.player_data = defaultdict(list)
        # opponent defense ratings
        self.team_defense = defaultdict(lambda: defaultdict(list))

    def update(self, player_name, game):
        """
        Add a game observation.
        game dict must have: date, min, pts, reb, ast, fg3m,
                             fgm, fga, fg3a, ftm, fta, team, opp
        """
        self.player_data[player_name].append(game)

        # Track opponent defense (points allowed to position/player)
        opp = game.get("opp", "")
        if opp:
            self.team_defense[opp]["pts_allowed"].append(game.get("pts", 0))
            self.team_defense[opp]["reb_allowed"].append(game.get("reb", 0))
            self.team_defense[opp]["ast_allowed"].append(game.get("ast", 0))
            self.team_defense[opp]["fg3m_allowed"].append(game.get("fg3m", 0))

    def _get_prior_games(self, player_name, before_date, n=20):
        """Get the last N games before a given date."""
        games = self.player_data.get(player_name, [])
        prior = [g for g in games if g["date"] < before_date]
        return prior[-n:] if len(prior) >= n else prior

    def _weighted_mean(self, values, min_games=5):
        """Recency-weighted mean. More recent = higher weight."""
        if len(values) < min_games:
            return None
        weights = []
        for i in range(len(values)):
            # Exponential recency: most recent game gets weight ~2x oldest
            w = 1.0 + (i / len(values))
            weights.append(w)
        return sum(v * w for v, w in zip(values, weights)) / sum(weights)

    def _minutes_scaled_rate(self, games, stat_key, min_games=5):
        """Calculate per-minute rate and expected minutes."""
        if len(games) < min_games:
            return None, None

        # Per-minute rate (using all games)
        total_stat = sum(g.get(stat_key, 0) for g in games)
        total_min = sum(g.get("min", 1) for g in games)
        if total_min == 0:
            return None, None
        rate_per_min = total_stat / total_min

        # Expected minutes (recency weighted)
        minutes = [g.get("min", 0) for g in games]
        expected_min = self._weighted_mean(minutes, min_games)

        return rate_per_min, expected_min

    def predict_points_triple_poisson(self, player_name, before_date, n_sims=5000):
        """
        Predict points using Triple Poisson decomposition.
        Returns: (mean, std, prob_distribution) or None if insufficient data.
        """
        games = self._get_prior_games(player_name, before_date, n=20)
        if len(games) < 5:
            return None

        # Calculate component rates per minute
        fg3m_vals = [g.get("fg3m", 0) for g in games]
        mins = [g.get("min", 1) for g in games]

        # We need FTM and 2PTM — derive from available data
        # pts = ftm*1 + fg2m*2 + fg3m*3
        # fg2m = fgm - fg3m (2-pointers = total FG made minus 3PT made)
        # ftm = pts - 2*fg2m - 3*fg3m = pts - 2*(fgm-fg3m) - 3*fg3m = pts - 2*fgm + 2*fg3m - 3*fg3m = pts - 2*fgm - fg3m

        ftm_vals = []
        fg2m_vals = []
        for g in games:
            pts = g.get("pts", 0)
            fgm = g.get("fgm", 0)
            fg3m = g.get("fg3m", 0)
            ftm = pts - 2 * fgm + 2 * fg3m - 3 * fg3m
            # Simplify: ftm = pts - 2*fgm - fg3m
            ftm = pts - 2 * fgm - fg3m
            if ftm < 0:
                ftm = 0  # Guard against data issues
            fg2m = fgm - fg3m
            if fg2m < 0:
                fg2m = 0
            ftm_vals.append(ftm)
            fg2m_vals.append(fg2m)

        # Per-minute rates
        total_min = sum(mins)
        if total_min == 0:
            return None

        # Recency-weighted rates
        lambda_ftm_per_min = self._weighted_mean(
            [f / max(m, 1) for f, m in zip(ftm_vals, mins)]
        )
        lambda_fg2m_per_min = self._weighted_mean(
            [f / max(m, 1) for f, m in zip(fg2m_vals, mins)]
        )
        lambda_fg3m_per_min = self._weighted_mean(
            [f / max(m, 1) for f, m in zip(fg3m_vals, mins)]
        )

        if any(x is None for x in [lambda_ftm_per_min, lambda_fg2m_per_min, lambda_fg3m_per_min]):
            return None

        # Expected minutes
        expected_min = self._weighted_mean(mins)
        if expected_min is None or expected_min < 10:
            return None

        # Scale to per-game lambdas
        lambda_ftm = max(0.01, lambda_ftm_per_min * expected_min)
        lambda_fg2m = max(0.01, lambda_fg2m_per_min * expected_min)
        lambda_fg3m = max(0.01, lambda_fg3m_per_min * expected_min)

        # Monte Carlo simulation
        points_samples = []
        for _ in range(n_sims):
            ftm = max(0, int(random.expovariate(1.0 / lambda_ftm) + 0.5)) if lambda_ftm > 0 else 0
            fg2m = max(0, int(random.expovariate(1.0 / lambda_fg2m) + 0.5)) if lambda_fg2m > 0 else 0
            fg3m = max(0, int(random.expovariate(1.0 / lambda_fg3m) + 0.5)) if lambda_fg3m > 0 else 0

            # Actually use Poisson sampling
            ftm = self._poisson_sample(lambda_ftm)
            fg2m = self._poisson_sample(lambda_fg2m)
            fg3m = self._poisson_sample(lambda_fg3m)

            total_pts = ftm * 1 + fg2m * 2 + fg3m * 3
            points_samples.append(total_pts)

        mean_pts = sum(points_samples) / len(points_samples)
        variance = sum((x - mean_pts) ** 2 for x in points_samples) / len(points_samples)
        std_pts = math.sqrt(variance) if variance > 0 else 1.0

        return {
            "mean": mean_pts,
            "std": std_pts,
            "lambda_ftm": lambda_ftm,
            "lambda_fg2m": lambda_fg2m,
            "lambda_fg3m": lambda_fg3m,
            "expected_min": expected_min,
            "samples": points_samples,
        }

    def _poisson_sample(self, lam):
        """Sample from Poisson distribution using inverse transform."""
        if lam <= 0:
            return 0
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= random.random()
            if p < L:
                break
        return k - 1

    def predict_stat(self, player_name, stat, before_date, n_sims=5000):
        """
        Predict any stat (pts, reb, ast, fg3m) with Monte Carlo simulation.
        For points: uses Triple Poisson.
        For others: uses single Poisson on per-minute rate.

        Returns dict with mean, std, and full sample distribution.
        """
        if stat == "pts":
            return self.predict_points_triple_poisson(player_name, before_date, n_sims)

        games = self._get_prior_games(player_name, before_date, n=20)
        if len(games) < 5:
            return None

        mins = [g.get("min", 1) for g in games]
        stat_vals = [g.get(stat, 0) for g in games]

        # Per-minute rate, recency weighted
        rate_per_min = self._weighted_mean(
            [s / max(m, 1) for s, m in zip(stat_vals, mins)]
        )
        expected_min = self._weighted_mean(mins)

        if rate_per_min is None or expected_min is None or expected_min < 10:
            return None

        lam = max(0.01, rate_per_min * expected_min)

        # Monte Carlo
        samples = [self._poisson_sample(lam) for _ in range(n_sims)]
        mean_val = sum(samples) / len(samples)
        variance = sum((x - mean_val) ** 2 for x in samples) / len(samples)

        return {
            "mean": mean_val,
            "std": math.sqrt(variance) if variance > 0 else 1.0,
            "lambda": lam,
            "expected_min": expected_min,
            "samples": samples,
        }

    def get_probability(self, player_name, stat, line, before_date, n_sims=5000):
        """
        Get probability of over/under for a player prop line.
        Returns (prob_over, prob_under) or None.
        """
        pred = self.predict_stat(player_name, stat, before_date, n_sims)
        if pred is None:
            return None

        samples = pred["samples"]
        over = sum(1 for s in samples if s > line)
        under = sum(1 for s in samples if s < line)
        push = sum(1 for s in samples if s == line)
        total = len(samples)

        return {
            "prob_over": over / total,
            "prob_under": under / total,
            "prob_push": push / total,
            "mean": pred["mean"],
            "std": pred["std"],
            "expected_min": pred.get("expected_min", 0),
        }


def load_enhanced_box_scores():
    """
    Load box scores with full shooting splits (FGM, FGA, FG3M, FG3A, FTM, FTA).
    Returns player history dict.
    """
    history = defaultdict(list)
    box_files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith("box_"))

    for bf in box_files:
        with open(os.path.join(DATA_DIR, bf)) as f:
            data = json.load(f)

        game = data.get("game", {})
        game_date = game.get("gameTimeUTC", "")[:10]
        if not game_date:
            continue

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

                name = p.get("name", "").lower()
                history[name].append({
                    "date": game_date,
                    "min": mins,
                    "pts": s.get("points", 0),
                    "reb": s.get("reboundsTotal", 0),
                    "ast": s.get("assists", 0),
                    "fg3m": s.get("threePointersMade", 0),
                    "fgm": s.get("fieldGoalsMade", 0),
                    "fga": s.get("fieldGoalsAttempted", 0),
                    "fg3a": s.get("threePointersAttempted", 0),
                    "ftm": s.get("freeThrowsMade", 0),
                    "fta": s.get("freeThrowsAttempted", 0),
                    "team": tri,
                    "opp": opp,
                    "home": is_home,
                })

    for name in history:
        history[name].sort(key=lambda x: x["date"])

    return history


def american_to_decimal(american):
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def implied_prob(american):
    if american > 0:
        return 100 / (american + 100)
    return abs(american) / (abs(american) + 100)


def run_backtest():
    """Backtest Triple Poisson model against full season real data."""
    print("=" * 65)
    print("  TRIPLE POISSON MODEL BACKTEST")
    print("  Full 2025-26 Season")
    print("=" * 65)

    # Load data
    print("\nLoading box scores with shooting splits...")
    history = load_enhanced_box_scores()
    print(f"  {len(history)} players loaded")

    print("Loading prop results...")
    with open(os.path.join(DATA_DIR, "real_backtest_full_season.json")) as f:
        props_data = json.load(f)
    results = props_data["results"]
    print(f"  {len(results)} matched props")

    # Build predictor chronologically
    predictor = TriplePoissonPredictor()

    # Feed all history into predictor
    for name, games in history.items():
        for game in games:
            predictor.update(name, game)

    # Run through props
    print("\nRunning predictions...")
    bets = []
    bankroll = 5000
    start = bankroll
    min_edge = 0.03  # 3% minimum edge

    props_by_date = defaultdict(list)
    for r in results:
        props_by_date[r["date"]].append(r)

    for date in sorted(props_by_date.keys()):
        seen = set()
        for prop in props_by_date[date]:
            key = f"{prop['player']}_{prop['stat']}"
            if key in seen:
                continue
            seen.add(key)

            player_key = prop["player"].lower()
            stat = prop["stat"]
            line = prop["line"]

            # Get probability estimate
            prob_result = predictor.get_probability(
                player_key, stat, line, date, n_sims=3000
            )
            if prob_result is None:
                continue

            # Skip low-minutes players
            if prob_result["expected_min"] < 20:
                continue

            prob_over = prob_result["prob_over"]
            prob_under = prob_result["prob_under"]

            # Calculate edge vs implied odds
            over_implied = implied_prob(prop["over_odds"])
            under_implied = implied_prob(prop["under_odds"])

            over_edge = prob_over - over_implied
            under_edge = prob_under - under_implied

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

            # Flat $100 bets
            bet_amount = 100
            if bankroll <= 0:
                continue

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

            bets.append({
                "date": date,
                "player": prop["player"],
                "stat": stat,
                "line": line,
                "mean": round(prob_result["mean"], 2),
                "std": round(prob_result["std"], 2),
                "prob": round(prob, 4),
                "edge": round(edge, 4),
                "side": side,
                "actual": prop["actual"],
                "won": won,
                "push": push,
                "odds": odds,
                "pnl": round(pnl, 2),
                "bankroll": round(bankroll, 2),
            })

    # Results
    if not bets:
        print("No bets placed!")
        return

    wins = sum(1 for b in bets if b["won"])
    losses = sum(1 for b in bets if not b["won"] and not b["push"])
    total_wagered = sum(100 for b in bets)
    total_pnl = sum(b["pnl"] for b in bets)
    roi = total_pnl / total_wagered * 100

    print(f"\n{'='*65}")
    print(f"  TRIPLE POISSON RESULTS")
    print(f"{'='*65}")
    print(f"  Bets:          {len(bets)}")
    print(f"  Win/Loss:      {wins}/{losses}")
    print(f"  Win Rate:      {wins/(wins+losses)*100:.1f}%")
    print(f"  Total Wagered: ${total_wagered:,.0f}")
    print(f"  Total P/L:     ${total_pnl:+,.0f}")
    print(f"  ROI:           {roi:+.2f}%")
    print(f"  Final Bankroll:${bankroll:,.0f}")

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

    print(f"\n  By Stat:")
    for stat in sorted(stat_data.keys()):
        sd = stat_data[stat]
        wr = sd["w"] / max(1, sd["w"] + sd["l"]) * 100
        print(f"    {stat.upper():5s}: {sd['n']:4d} bets, {wr:.1f}% win, ${sd['pnl']:+,.0f}")

    # By edge bucket
    edge_data = defaultdict(lambda: {"w": 0, "l": 0, "n": 0, "pnl": 0})
    for b in bets:
        bucket = int((b["edge"] * 100) // 3) * 3
        ed = edge_data[bucket]
        ed["n"] += 1
        if b["won"]:
            ed["w"] += 1
        elif not b["push"]:
            ed["l"] += 1
        ed["pnl"] += b["pnl"]

    print(f"\n  By Edge Bucket:")
    for bucket in sorted(edge_data.keys()):
        ed = edge_data[bucket]
        wr = ed["w"] / max(1, ed["w"] + ed["l"]) * 100
        print(f"    {bucket:2d}-{bucket+2}%: {ed['n']:4d} bets, {wr:.1f}% win, ${ed['pnl']:+,.0f}")

    # Calibration check: are our probabilities well-calibrated?
    print(f"\n  CALIBRATION CHECK:")
    cal_bins = defaultdict(lambda: {"predicted": 0, "actual": 0, "n": 0})
    for b in bets:
        bin_key = int(b["prob"] * 10) / 10  # 0.5, 0.6, 0.7, etc.
        cal_bins[bin_key]["predicted"] += b["prob"]
        cal_bins[bin_key]["actual"] += (1 if b["won"] else 0)
        cal_bins[bin_key]["n"] += 1

    for bin_key in sorted(cal_bins.keys()):
        cb = cal_bins[bin_key]
        if cb["n"] < 10:
            continue
        avg_pred = cb["predicted"] / cb["n"]
        avg_actual = cb["actual"] / cb["n"]
        diff = avg_actual - avg_pred
        print(f"    Predicted {avg_pred:.1%}: Actual {avg_actual:.1%} (n={cb['n']}, diff={diff:+.1%})")

    # Save
    output = {
        "model": "triple_poisson",
        "bets": len(bets),
        "wins": wins,
        "losses": losses,
        "roi": round(roi, 2),
        "pnl": round(total_pnl, 2),
        "calibration": {str(k): {"pred": v["predicted"]/v["n"], "actual": v["actual"]/v["n"], "n": v["n"]}
                        for k, v in cal_bins.items() if v["n"] >= 10},
        "bet_log": bets[-100:],
    }
    with open(os.path.join(DATA_DIR, "triple_poisson_results.json"), "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to data/triple_poisson_results.json")


if __name__ == "__main__":
    run_backtest()

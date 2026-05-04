"""
Sports Edge - Calibrated Prediction Model
Key insight from research: calibration > accuracy for profitability.

Our models are OVERCONFIDENT — they think 80% when reality is 55%.
This module learns a calibration curve from historical predictions
and adjusts future probabilities to match observed reality.

Implements isotonic regression calibration (non-parametric, monotonic).
"""
import json
import math
import os
import sys
import random
from collections import defaultdict
from triple_poisson_model import (
    TriplePoissonPredictor, load_enhanced_box_scores,
    implied_prob, american_to_decimal
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
random.seed(42)


class IsotonicCalibrator:
    """
    Isotonic regression calibrator.
    Learns a monotonic mapping from raw model probabilities to calibrated ones.

    Training: feed it (predicted_prob, actual_outcome) pairs
    Prediction: map new raw probabilities through the learned curve
    """

    def __init__(self):
        self.bins = []  # list of (raw_prob, calibrated_prob)
        self.fitted = False

    def fit(self, predictions, outcomes, n_bins=20):
        """
        Learn calibration mapping.
        predictions: list of raw model probabilities
        outcomes: list of 0/1 actual outcomes
        """
        if len(predictions) < 50:
            self.fitted = False
            return

        # Sort by predicted probability
        paired = sorted(zip(predictions, outcomes))

        # Bin into groups
        bin_size = max(1, len(paired) // n_bins)
        self.bins = []

        for i in range(0, len(paired), bin_size):
            chunk = paired[i:i + bin_size]
            if len(chunk) < 5:
                continue
            avg_pred = sum(p for p, _ in chunk) / len(chunk)
            avg_outcome = sum(o for _, o in chunk) / len(chunk)
            self.bins.append((avg_pred, avg_outcome))

        # Enforce monotonicity (pool adjacent violators)
        self._pool_adjacent_violators()
        self.fitted = True

    def _pool_adjacent_violators(self):
        """Ensure calibration curve is monotonically increasing."""
        if len(self.bins) < 2:
            return

        result = [self.bins[0]]
        for i in range(1, len(self.bins)):
            raw, cal = self.bins[i]
            if cal < result[-1][1]:
                # Pool: average the violating bins
                prev_raw, prev_cal = result[-1]
                merged_raw = (prev_raw + raw) / 2
                merged_cal = (prev_cal + cal) / 2
                result[-1] = (merged_raw, merged_cal)
            else:
                result.append((raw, cal))
        self.bins = result

    def calibrate(self, raw_prob):
        """Map raw model probability to calibrated probability."""
        if not self.fitted or len(self.bins) < 2:
            return raw_prob  # No calibration available

        # Linear interpolation between bins
        if raw_prob <= self.bins[0][0]:
            return self.bins[0][1]
        if raw_prob >= self.bins[-1][0]:
            return self.bins[-1][1]

        for i in range(1, len(self.bins)):
            if raw_prob <= self.bins[i][0]:
                # Interpolate between bins[i-1] and bins[i]
                r0, c0 = self.bins[i - 1]
                r1, c1 = self.bins[i]
                if r1 == r0:
                    return c0
                t = (raw_prob - r0) / (r1 - r0)
                return c0 + t * (c1 - c0)

        return self.bins[-1][1]


def run_calibrated_backtest():
    """
    Two-pass backtest:
    Pass 1: Generate raw predictions on first half of season to learn calibration curve
    Pass 2: Apply calibrated probabilities on second half of season
    """
    print("=" * 65)
    print("  CALIBRATED TRIPLE POISSON BACKTEST")
    print("=" * 65)

    # Load data
    print("\nLoading data...")
    history = load_enhanced_box_scores()
    with open(os.path.join(DATA_DIR, "real_backtest_full_season.json")) as f:
        props_data = json.load(f)
    results = props_data["results"]
    print(f"  {len(results)} props, {len(history)} players")

    # Build predictor
    predictor = TriplePoissonPredictor()
    for name, games in history.items():
        for game in games:
            predictor.update(name, game)

    # Split dates into calibration period and test period
    props_by_date = defaultdict(list)
    for r in results:
        props_by_date[r["date"]].append(r)
    all_dates = sorted(props_by_date.keys())

    # Use first 60% of dates for calibration, last 40% for testing
    split_idx = int(len(all_dates) * 0.6)
    cal_dates = all_dates[:split_idx]
    test_dates = all_dates[split_idx:]
    print(f"  Calibration period: {cal_dates[0]} to {cal_dates[-1]} ({len(cal_dates)} dates)")
    print(f"  Test period: {test_dates[0]} to {test_dates[-1]} ({len(test_dates)} dates)")

    # PASS 1: Generate raw predictions on calibration period
    print("\nPass 1: Learning calibration curve...")
    cal_predictions = []
    cal_outcomes = []
    cal_stats = defaultdict(lambda: {"preds": [], "outcomes": []})

    for date in cal_dates:
        seen = set()
        for prop in props_by_date[date]:
            key = f"{prop['player']}_{prop['stat']}"
            if key in seen:
                continue
            seen.add(key)

            player_key = prop["player"].lower()
            stat = prop["stat"]
            line = prop["line"]

            prob_result = predictor.get_probability(player_key, stat, line, date, n_sims=3000)
            if prob_result is None:
                continue
            if prob_result["expected_min"] < 20:
                continue

            # For each prop, record both over and under predictions
            # We'll calibrate the "bet side" probability
            prob_over = prob_result["prob_over"]
            prob_under = prob_result["prob_under"]

            over_implied = implied_prob(prop["over_odds"])
            under_implied = implied_prob(prop["under_odds"])

            over_edge = prob_over - over_implied
            under_edge = prob_under - under_implied

            if over_edge > under_edge and over_edge > 0:
                raw_prob = prob_over
                actual = 1 if prop["over_won"] else 0
            elif under_edge > 0:
                raw_prob = prob_under
                actual = 1 if prop["under_won"] else 0
            else:
                continue

            cal_predictions.append(raw_prob)
            cal_outcomes.append(actual)
            cal_stats[stat]["preds"].append(raw_prob)
            cal_stats[stat]["outcomes"].append(actual)

    print(f"  Collected {len(cal_predictions)} prediction-outcome pairs")

    # Fit calibrators (one global + per-stat)
    global_calibrator = IsotonicCalibrator()
    global_calibrator.fit(cal_predictions, cal_outcomes, n_bins=15)

    stat_calibrators = {}
    for stat, data in cal_stats.items():
        cal = IsotonicCalibrator()
        cal.fit(data["preds"], data["outcomes"], n_bins=10)
        stat_calibrators[stat] = cal
        if cal.fitted:
            print(f"  {stat} calibrator: {len(cal.bins)} bins")

    # Show calibration curve
    if global_calibrator.fitted:
        print(f"\n  Global calibration curve:")
        for raw, calibrated in global_calibrator.bins:
            print(f"    Raw {raw:.1%} -> Calibrated {calibrated:.1%}")

    # PASS 2: Test with calibrated probabilities
    print(f"\nPass 2: Testing with calibrated probabilities...")

    bets_raw = []      # Uncalibrated (for comparison)
    bets_calibrated = []  # Calibrated
    bankroll_raw = 5000
    bankroll_cal = 5000
    start = 5000
    min_edge = 0.03

    for date in test_dates:
        seen = set()
        for prop in props_by_date[date]:
            key = f"{prop['player']}_{prop['stat']}"
            if key in seen:
                continue
            seen.add(key)

            player_key = prop["player"].lower()
            stat = prop["stat"]
            line = prop["line"]

            prob_result = predictor.get_probability(player_key, stat, line, date, n_sims=3000)
            if prob_result is None:
                continue
            if prob_result["expected_min"] < 20:
                continue

            raw_prob_over = prob_result["prob_over"]
            raw_prob_under = prob_result["prob_under"]
            over_implied = implied_prob(prop["over_odds"])
            under_implied = implied_prob(prop["under_odds"])

            # --- RAW (uncalibrated) bets ---
            raw_over_edge = raw_prob_over - over_implied
            raw_under_edge = raw_prob_under - under_implied

            if raw_over_edge > raw_under_edge and raw_over_edge >= min_edge:
                raw_side = "over"
                raw_edge = raw_over_edge
                raw_odds = prop["over_odds"]
            elif raw_under_edge >= min_edge:
                raw_side = "under"
                raw_edge = raw_under_edge
                raw_odds = prop["under_odds"]
            else:
                raw_side = None

            if raw_side and bankroll_raw > 0:
                won = prop["over_won"] if raw_side == "over" else prop["under_won"]
                push = prop["push"]
                pnl = 0 if push else (100 * (american_to_decimal(raw_odds) - 1) if won else -100)
                bankroll_raw += pnl
                bets_raw.append({"won": won, "push": push, "pnl": round(pnl, 2), "stat": stat})

            # --- CALIBRATED bets ---
            # Use stat-specific calibrator if available, else global
            cal = stat_calibrators.get(stat, global_calibrator)
            if not cal.fitted:
                cal = global_calibrator
            if not cal.fitted:
                continue

            cal_prob_over = cal.calibrate(raw_prob_over)
            cal_prob_under = cal.calibrate(raw_prob_under)

            # Renormalize (calibrated probs may not sum to 1)
            total = cal_prob_over + cal_prob_under
            if total > 0:
                cal_prob_over /= total
                cal_prob_under /= total

            cal_over_edge = cal_prob_over - over_implied
            cal_under_edge = cal_prob_under - under_implied

            if cal_over_edge > cal_under_edge and cal_over_edge >= min_edge:
                cal_side = "over"
                cal_edge = cal_over_edge
                cal_odds = prop["over_odds"]
                cal_prob = cal_prob_over
            elif cal_under_edge >= min_edge:
                cal_side = "under"
                cal_edge = cal_under_edge
                cal_odds = prop["under_odds"]
                cal_prob = cal_prob_under
            else:
                continue

            if bankroll_cal <= 0:
                continue

            won = prop["over_won"] if cal_side == "over" else prop["under_won"]
            push = prop["push"]
            pnl = 0 if push else (100 * (american_to_decimal(cal_odds) - 1) if won else -100)
            bankroll_cal += pnl
            bankroll_cal = round(bankroll_cal, 2)

            bets_calibrated.append({
                "date": date, "player": prop["player"], "stat": stat,
                "line": line, "raw_prob": round(raw_prob_over if cal_side == "over" else raw_prob_under, 4),
                "cal_prob": round(cal_prob, 4), "edge": round(cal_edge, 4),
                "side": cal_side, "actual": prop["actual"],
                "won": won, "push": push, "odds": cal_odds,
                "pnl": round(pnl, 2), "bankroll": bankroll_cal,
            })

    # Print results
    def summarize(name, bets, final_br):
        if not bets:
            print(f"\n  {name}: No bets")
            return
        wins = sum(1 for b in bets if b["won"])
        losses = sum(1 for b in bets if not b["won"] and not b["push"])
        total_pnl = sum(b["pnl"] for b in bets)
        total_wagered = len(bets) * 100
        roi = total_pnl / total_wagered * 100 if total_wagered > 0 else 0
        print(f"\n  {name}:")
        print(f"    Bets: {len(bets)}, Win Rate: {wins/(max(1,wins+losses))*100:.1f}%")
        print(f"    P/L: ${total_pnl:+,.0f}, ROI: {roi:+.2f}%")
        print(f"    Final Bankroll: ${final_br:,.0f}")

        # By stat
        for stat in ["pts", "reb", "ast", "fg3m"]:
            subset = [b for b in bets if b["stat"] == stat]
            if not subset:
                continue
            w = sum(1 for b in subset if b["won"])
            l = sum(1 for b in subset if not b["won"] and not b["push"])
            p = sum(b["pnl"] for b in subset)
            wr = w / max(1, w + l) * 100
            print(f"      {stat.upper():5s}: {len(subset):4d} bets, {wr:.1f}% win, ${p:+,.0f}")

    print(f"\n{'='*65}")
    print(f"  TEST PERIOD RESULTS ({test_dates[0]} to {test_dates[-1]})")
    print(f"{'='*65}")

    summarize("RAW (uncalibrated) Triple Poisson", bets_raw, bankroll_raw)
    summarize("CALIBRATED Triple Poisson", bets_calibrated, bankroll_cal)

    # Calibration check on test period
    if bets_calibrated:
        print(f"\n  POST-CALIBRATION ACCURACY CHECK:")
        cal_check = defaultdict(lambda: {"pred": 0, "actual": 0, "n": 0})
        for b in bets_calibrated:
            bin_key = round(b["cal_prob"] * 10) / 10
            cal_check[bin_key]["pred"] += b["cal_prob"]
            cal_check[bin_key]["actual"] += (1 if b["won"] else 0)
            cal_check[bin_key]["n"] += 1

        for bk in sorted(cal_check.keys()):
            cc = cal_check[bk]
            if cc["n"] < 10:
                continue
            avg_p = cc["pred"] / cc["n"]
            avg_a = cc["actual"] / cc["n"]
            print(f"    Predicted {avg_p:.1%}: Actual {avg_a:.1%} (n={cc['n']}, diff={avg_a-avg_p:+.1%})")

    # Save
    output = {
        "raw_bets": len(bets_raw),
        "raw_pnl": sum(b["pnl"] for b in bets_raw) if bets_raw else 0,
        "cal_bets": len(bets_calibrated),
        "cal_pnl": sum(b["pnl"] for b in bets_calibrated) if bets_calibrated else 0,
        "cal_roi": sum(b["pnl"] for b in bets_calibrated) / max(1, len(bets_calibrated) * 100) * 100 if bets_calibrated else 0,
        "calibration_curve": [(r, c) for r, c in global_calibrator.bins] if global_calibrator.fitted else [],
        "bet_log": bets_calibrated[-50:] if bets_calibrated else [],
    }
    with open(os.path.join(DATA_DIR, "calibrated_results.json"), "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to data/calibrated_results.json")


if __name__ == "__main__":
    run_calibrated_backtest()

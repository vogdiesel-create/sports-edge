# Pre-Fetch Research Analysis: Actionable Insights for Sports Edge MLB Models

**Date**: 2026-04-20
**Analyst**: researcher agent
**Files Analyzed**: 33 files across blogs, academic papers, Reddit threads, FanGraphs articles, Statcast docs, Pinnacle resources, and forum posts

---

## TOP 10 RANKED ACTIONABLE INSIGHTS

### #1. REPLACE POISSON WITH NEGATIVE BINOMIAL FOR ALL COUNT MODELS
**Source**: fg-negbin-runs.txt, cmp-bivariate-2024.txt
**Impact**: HIGH -- fixes fundamental distributional assumption
**Current problem**: Our K prop model, batter prop model, and totals model all use Poisson distribution. MLB data is overdispersed (variance >> mean). Poisson assumes mean = variance, so it produces overconfident probabilities -- systematically overestimating the probability of extreme outcomes.
**Implementation**:
1. In `prop_model.py`: Replace Poisson CDF with NegBin CDF where r and p are fit from historical K count data
2. In `mlb_batter_prop_model.py`: Replace `poisson_at_least()` with negative binomial equivalent
3. In `mlb_model.py`: Already imports `nbinom` -- verify the game total model actually uses it
4. Calibrate r parameter from historical variance/mean ratio of pitcher K counts per game (~1.3-1.5x overdispersion expected)

### #2. IMPLEMENT PROPER MATCHUP K% FORMULA (LOG5-STYLE)
**Source**: fg-matchup-k.txt
**Impact**: HIGH -- replaces crude scalar with validated formula
**Current problem**: prop_model.py uses `opp_k_rate / league_avg_k_rate` as a simple multiplier. This ignores that batter and pitcher contribute equally, and doesn't account for handedness.
**Implementation**:
1. Replace scalar matchup adjustment with: `matchup_K% = B * P / (0.84 * B * P + 0.16)` where B = opponent batters' aggregate K% vs pitcher hand, P = pitcher's K% vs batter hand
2. Sum expected K% across each batter in the projected lineup (top 9) to get game-level expected Ks
3. Weight by expected PAs per lineup spot (leadoff ~4.5 PA, 9th ~3.5 PA)

### #3. ADD TIMES-THROUGH-ORDER ADJUSTMENT TO K MODEL
**Source**: mlbprops-tto.txt
**Impact**: HIGH -- creates differential edge for short vs deep starts
**Current problem**: We use flat K/9 rate regardless of projected innings depth. But K rate DECLINES in later innings as batters see pitcher's stuff repeatedly.
**Implementation**:
1. Split K/9 projection into TTO segments:
   - 1st TTO (innings 1-3): K rate at ~110% of season average
   - 2nd TTO (innings 4-5): K rate at ~100% of season average
   - 3rd TTO (innings 6+): K rate at ~85% of season average
2. Short-leash pitchers (sub-5 IP) become K OVER candidates; deep starters become K UNDER candidates
3. This directly explains why UNDER picks work better -- deep starters hit TTO penalty

### #4. SELECT MODELS BY CALIBRATION, NOT ACCURACY
**Source**: walsh-calibration-2024.txt, sportsai-calibration.txt
**Impact**: HIGH -- foundational model evaluation change
**Finding**: Walsh (2024) shows calibration-selected models yield +34.69% ROI vs -35.17% ROI for accuracy-selected models.
**Implementation**:
1. Compute Brier Score and ECE (Expected Calibration Error) for all models weekly
2. Build reliability curves: bin predictions by probability decile, plot predicted vs actual
3. Use Platt Scaling (logistic on logits) as fast nightly recalibration
4. If ECE > 0.015 for any market, trigger recalibration

### #5. USE QUANTILE REGRESSION FOR TOTALS MODEL
**Source**: dmochowski-optimal-2023.txt
**Impact**: MEDIUM-HIGH -- theoretically optimal approach
**Finding**: Optimal wagering requires the MEDIAN and 0.476/0.524 quantiles. Only bet when sportsbook total falls outside the 0.476-0.524 quantile range.
**Implementation**: Train quantile regression models (LightGBM with pinball loss) predicting the 0.476, 0.50, and 0.524 quantiles of game total.

### #6. ADD UNDERLYING STRIKE-TYPE FEATURES TO K MODEL
**Source**: fg-xk-formula.txt
**Impact**: MEDIUM
**Finding**: xK% = -0.61 + (L/Str * 1.1538) + (S/Str * 1.4696) + (F/Str * 0.9417), R-squared=0.892
**Implementation**: Fetch Looking Strike Rate, Swinging Strike Rate, Foul Strike Rate from Statcast. Use xK% as the pitcher's "true" K rate instead of raw K/9.

### #7. BATTER PROP OVERESTIMATION: POISSON IS THE ROOT CAUSE
**Source**: fg-negbin-runs.txt, cmp-bivariate-2024.txt
**Why Poisson/Binomial models fail for batter props**:
1. **Overdispersion**: Variance >> mean. Poisson assumes variance = mean, making P(X >= threshold) too high.
2. **Zero-inflation**: Batters go 0-for much more often than Poisson predicts.
3. **Non-independence**: At-bats within a game are correlated (same pitcher, TTO effects, bullpen changes).
4. **Per-game vs per-PA mismatch**: PA count varies 3.0 to 5.5. Model assumes full exposure.
**Fix**: Replace with zero-inflated Negative Binomial. Estimate zero-inflation from empirical 0-outcome rates.

### #8. ADD UMPIRE STRIKE ZONE AND PARK K-FACTORS
**Source**: kprop-spots.txt, mlbprops-tto.txt
**Implementation**: Track umpire K-rate above/below average from UmpScorecards. Umpire assignment available day-of from MLB API.

### #9. IMPLEMENT xROI FOR SMALL-SAMPLE EVALUATION
**Source**: unabated-beyond-clv.txt
**Implementation**: For each graded bet, compute xCOVER% using NORM.DIST(line, actual_result, historical_SD, TRUE). De-lucks results, reveals true model skill faster.

### #10. CLV IS IRRELEVANT FOR PROP MARKETS
**Source**: unabated-clv-precise.txt, algobetting-CLV-analysis-thread-3.txt
**Key**: Jack Andrews (Unabated founder) explicitly states CLV "doesn't mean anything in props." Use ROI + calibration instead.

---

## File-by-File Analysis

### sportsai-calibration.txt (Quality: 7/10)
- Platt Scaling and Isotonic Regression as post-hoc calibration methods
- ECE target of 0.015 as weekly monitoring threshold; Brier Score for optimization
- Segment miscalibration by market type, season phase

### mlbprops-tto.txt (Quality: 9/10) -- HIGHEST ACTIONABILITY
- OPS+ jumps from 91 (1st TTO) to 117 (3rd TTO) -- 28% offensive explosion
- ERA goes from 4.08 to 4.57 (12% worse) by 3rd time through
- K rate DECLINES each time through -- directly impacts our K prop model
- **CONTRADICTS** our model: we use flat K/9 regardless of projected innings depth

### walsh-calibration-2024.txt (Quality: 8/10)
- Calibration-selected model: +34.69% ROI vs accuracy-selected: -35.17% ROI
- **CONTRADICTS** common practice of optimizing for accuracy

### cmp-bivariate-2024.txt (Quality: 7/10)
- CMP handles both over and under-dispersed count data
- MLB runs: variance ~2x mean. Poisson assumes mean=variance -- WRONG
- **CONTRADICTS** our Poisson assumptions

### dmochowski-optimal-2023.txt (Quality: 9/10) -- HIGHEST THEORETICAL VALUE
- Only need to estimate MEDIAN, not mean, for optimal wagering
- If spread within 0.476-0.524 quantiles, wagering ALWAYS yields negative expected profit
- **STRONGLY advocates quantile regression** over OLS

### fg-matchup-k.txt (Quality: 9/10) -- HIGHEST K MODEL RELEVANCE
- matchup_K% = B * P / (0.84 * B * P + 0.16)
- Based on 1.5M+ plate appearances, 2002-2012
- **CONTRADICTS** our simple `opp_k_rate / league_avg` scalar

### fg-xk-formula.txt (Quality: 8/10)
- xK% = -0.61 + (L/Str * 1.1538) + (S/Str * 1.4696) + (F/Str * 0.9417)
- R-squared = 0.892; S/Str has 0.81 correlation with K%
- Adding Looking Strike Rate and Foul Strike Rate captures K ability much better than K/9 alone

### fg-negbin-runs.txt (Quality: 8/10) -- CRITICAL FOR TOTALS MODEL
- Poisson FAILS: variance ~2x mean for MLB run scoring
- Negative Binomial dramatically better fit
- Even NBD underestimates shutout rate (zero-inflation needed)
- **DIRECTLY CONTRADICTS** our totals model using Poisson

### Reddit/forum highlights
- algobetting CLV thread: "CLV doesn't mean anything in props" -- confirmed by multiple experts
- algobetting prop-model thread: Multiple successful modelers use Negative Binomial, not Poisson
- ~1000 bets needed to distinguish 54% win rate from coin flip at standard confidence

### Low-value files (reference only)
- Statcast: API reference, CSV docs, glossary pages (no actionable data)
- Pinnacle: title-only pages (kelly, CLV, theory)
- Forums: listing pages, no content

---

## SUMMARY TABLE

| Rank | Insight | Affects | Effort | Expected Impact |
|------|---------|---------|--------|-----------------|
| 1 | Replace Poisson with Negative Binomial | K props, batter props, totals | Medium | Fix 33-100% overestimation |
| 2 | Log5 matchup K% formula | K props | Medium | Better per-game K estimates |
| 3 | Times-Through-Order adjustment | K props | Medium | Differential short/deep start edge |
| 4 | Model selection by calibration | All models | Low | +35% ROI vs -35% ROI |
| 5 | Quantile regression for totals | Totals | High | Theoretically optimal wagering |
| 6 | Strike-type features (xK%) | K props | Medium | R-squared 0.892 vs current K/9 |
| 7 | Zero-inflated NegBin for batters | Batter props | High | Explain/fix overestimation |
| 8 | Umpire + park K-factors | K props | Low | Additional edge signal |
| 9 | xROI for small-sample eval | Evaluation | Low | Better signal from 40 bets |
| 10 | Drop CLV for props | Evaluation | None | Correct methodology |

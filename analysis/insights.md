# Sports Edge - Accumulated Insights

## 2026-05-03: Week 18 Deep Dive - System Clarity (376 graded bets)

### THE PORTFOLIO IS NOW CLEAN

After 3+ weeks of pruning:
- K-Props: DEAD (51W-50L, -$599)
- RBI: DEAD (11W-28L, -$956)
- Batter Ks: DEAD (12W-13L, -$279)
- Moneyline: DEAD (2W-6L, -$468)
- Game UNDER: DEAD (merged into OVER-only)

What remains: **TB + HA + ER = 97W-45L (68.3%), +$2,237, 15.2% ROI.**

### WEEK 18 WAS A BRUTAL TEACHER

K-props collapsed: 11W-19L this week (-$1,072). The model's systematic K overestimation was always there, but 8 straight losses made it undeniable. The decision to shut down saves ~$200-500/week in expected losses.

Meanwhile TB kept printing: 31W-11L on active markets this week (+$471). The contrast is stark.

### THE CONCENTRATION THESIS IS VALIDATED

| Strategy | N=142 active-only | N=376 all bets |
|----------|-------------------|----------------|
| WR | 68.3% | 54.3% |
| ROI | 15.2% | 2.8% |
| PnL | +$2,237 | +$356 |

Cutting losers didn't just improve ROI - it revealed that the alpha was **4x larger** than it appeared in the mixed portfolio.

### FORWARD TRACKING FRAMEWORK ESTABLISHED

Three experiments running forward simultaneously:
1. EXP-011: TB juice cap (need 22 more within-cap bets)
2. EXP-012: HA line filter (need 20 u4.5 bets)
3. EXP-006: Game model OVER-only (need 31 more bets to 100)

Each has clear kill criteria. No ambiguity about when to act.

---

## 2026-05-03: HA Line Filter + Dead Zone Resolved (376 graded bets)

### THE BIG FINDING: HA Line Value Is the Critical Variable (Not Pitcher Quality)

H042 proposed pitcher quality filter for HA. Data says it's the LINE, not the pitcher:

| Line | Record | WR | PnL |
|------|--------|----|-----|
| u4½ | 8W-3L | 73% | +$281 |
| u5½ | 7W-7L | 50% | -$126 |
| u6½ | 1W-1L | 50% | -$83 |

u4½ is the sweet spot: pitcher needs ≤4 hits, most competent arms manage this. u5½+ is a coin flip where bad innings compound (Cecconi: 10 HA on u6½ = -$174 blowup).

**Action: HA line filter implemented.** Only u4½ or tighter. u5½+ skipped. Retroactive: would cut 7 of 11 losses.

### DEAD ZONE RESOLVED: Juice Cap Already Handles It

H040 (stale-line theory) validated and resolved:

| EV Band | Within -160 Cap | Beyond Cap |
|---------|----------------|------------|
| 8-15% | Strong WR | Limited data |
| 15-25% | 15W-7L (68.2%), +$419 | 13W-13L (50%), -$542 |
| 25%+ | 14W-0L, +$1,073 | N/A |

The dead zone only exists in heavy-juice territory. Since EXP-011 (juice cap) is already active, no additional EV filter needed.

### TB EV BAND PERFORMANCE (Updated N=111)

| Band | Record | WR | PnL | ROI |
|------|--------|-----|-----|-----|
| 8-15% | 36W-13L | 73.5% | +$1,048 | ~20% |
| 15-25% | 28W-20L | 58.3% | -$123 | ~-3% |
| 25%+ | 14W-0L | 100% | +$1,073 | ~70% |

The 8-15% band is the workhorse. 25%+ is perfection. 15-25% is only profitable within the juice cap.

### GAME MODEL CLV SPLIT

CLV+ bets: 15W-7L (68%), +$944. CLV- bets: 16W-19L (46%), -$522. The model finds real edges when it beats the close, but ~60% of bets are stale-line captures.

---

## 2026-05-02: Dead Zone Root Cause + Model Calibration Map (370 graded bets)

### THE BIG FINDING: The EV Dead Zone Is Stale-Line Noise, Not Juice

Previous hypothesis: 15-20% EV TB bets lose because of heavy juice.
**DISPROVEN.** Dead zone avg juice (-141) is LIGHTER than the golden zone (-160).

The real explanation: **the model captures lines mid-transition.** Books are actively moving these lines, and by game time the "edge" has evaporated. Evidence:
- 15-20% EV (Tier A): avg odds -141, 19W-15L, -9.6% ROI
- 12-15% EV (Tier B): avg odds -160, 18W-4L, +34.5% ROI
- If juice caused the problem, lighter juice should WIN more. It doesn't.

### THE MODEL CALIBRATION MAP

| EV Band | Tier | Record | ROI | Interpretation |
|---------|------|--------|-----|----------------|
| 8-12% | B | 17W-9L | +7.7% | Baseline structural edge |
| 12-15% | B | 18W-4L | +34.5% | SWEET SPOT: small genuine edges |
| 15-20% | A | 19W-15L | -9.6% | NOISE: stale line captures |
| 20-25% | A | 8W-5L | +7.2% | Marginal (recovering signal) |
| 25%+ | A | 14W-0L | +69.5% | TRUE SIGNAL: massive mispricings |

The model is well-calibrated at EXTREMES (small edges 10-15%, huge edges 25%+) but poorly calibrated in the MIDDLE (15-20%). This is consistent with stale-line theory: small persistent inefficiencies are real, huge mispricings are real, but moderate EV often represents lines in transit.

### JUICE CAP HANDLES THE WORST OF IT

The -160 cap blocks 56% of dead zone bets (the ones with heavy juice layered on top of stale lines). Remaining within-cap dead zone: 9W-6L, -0.0% ROI. Break-even is tolerable.

### K-PROPS PERMANENTLY SHUTDOWN

51W-47L, -$363. Last 10 picks ALL losses. Model over-predicts by 2-5 Ks consistently. Systematic miscalibration cannot be fixed without fundamental model rebuild. Pick generation disabled in cron.

### GAME MODEL OVER-ONLY: Working (EXP-006)

Since OVER-only (Apr 26+): 9W-5L-2P, +$331, 64.3% WR. Strong performance.

---

## 2026-05-01: Juice Analysis & TB Cap (349 graded bets)

### THE BIG FINDING: Juice Is the Primary ROI Killer on TB

Deep analysis of all 103 graded TB bets by odds bucket:

| Odds Range | Record | WR | ROI |
|-----------|--------|-----|-----|
| -100 to -130 | 11W-1L | 91.7% | +68.5% |
| -135 to -160 | 17W-7L | 70.8% | +10.3% |
| -165 to -190 | 34W-17L | 66.7% | +5.1% |
| -200+ | 6W-3L | 66.7% | -2.9% |

The alpha degrades monotonically with juice. Light juice (-100 to -130) is by far the most profitable segment. Heavy juice eats edge even when WR stays above 60%.

**Action: Implemented TB_JUICE_CAP = -160.**
- Within cap: 32W-11L (74.4%, 29.4% ROI)
- Beyond cap: 40W-20L (66.7%, 3.8% ROI)

### SECOND: EV Dead Zone Is Real but Partially Explained by Juice

| EV Range | Record | WR | ROI |
|----------|--------|-----|-----|
| 25%+ | 13W-0L | 100% | +70.4% |
| 20-25% | 8W-4L | 66.7% | +7.8% |
| 15-20% | 17W-14L | 54.8% | -13.7% |
| 10-15% | 34W-13L | 72.3% | +18.4% |

The 15-20% EV dead zone persists even within the juice cap (7W-5L = 58.3% within cap). But the juice cap removes 19/31 dead zone bets. Monitoring whether the cap is sufficient.

### THIRD: 25%+ EV TB Is Perfect (13-0)

All 13 bets with 25%+ EV are wins. Mostly u1.5 TB (player doesn't hit for extra bases). Spread across 6 dates. The model excels at identifying low-output hitters against tough pitching. These are high-conviction, high-edge bets.

### FOURTH: Tier A vs B Driven by Juice, Not Market Type

Previous analysis blamed Tier A for losses (-$230, -2.2% ROI). But drilling down:
- Tier A TB: 38W-18L (67.9%), +$648, +11.2% ROI
- Tier B TB: 34W-13L (72.3%), +$836, +18.4% ROI

Both are profitable on TB. Tier A's losses came entirely from RBI (-$1173) and other disabled markets. The juice cap is a cleaner filter than tier.

---

## 2026-04-30: System Realignment (334 graded bets)

### THE BIG FINDING: OT Total Bases is the ONLY Statistically Significant Alpha

With 334 graded bets across all models, the picture is now clear:

| Signal | Record | WR | PnL | p-value | Verdict |
|--------|--------|-----|-----|---------|---------|
| OT Total Bases | 67W-28L | 70.5% | +$1,553 | <0.001 | **REAL ALPHA** |
| OT Hits Allowed | 15W-9L | 62.5% | +$178 | ~0.10 | Promising, small N |
| K-Prop OVER | 20W-12L | 62.5% | +$486 | 0.08 | Partially luck |
| Game Model OVER | 7W-4L-2P | 63.6% | +$337 | ~0.15 | Not significant |

Everything else was a leak:
- OT RBI: 11W-28L (28.2%), **-$956** -- DISABLED
- OT Ks: 11W-12L (47.8%), -$171 -- DISABLED
- K-Prop UNDER: 31W-29L (51.7%), -$330 -- DISABLED
- Game Model UNDER: 18W-17L, +$127 -- DISABLED
- Moneyline: 2W-6L, -$468 -- DISABLED

### SECOND FINDING: K-Prop Model Has Structural OVER Bias

Calibration at N=92 reveals the model over-predicts K counts for OVER picks by 0.83 Ks. The 0.86 correction factor is too weak for OVER bets (ideal: 0.728). This means:
- OVER edges are inflated (some are false positives)
- Tightening the correction would generate even fewer picks
- The model needs fundamentally new features (SwStr%, CSW%) to find real OVER alpha

### THIRD FINDING: TB EV "Dead Zone" at 16-20%

Granular EV analysis reveals a curious pattern:
- 10-16% EV: 37W-12L (75.5%), +$1,064 -- Sweet spot
- **16-20% EV: 11W-13L (45.8%), -$486 -- LOSING**
- 20%+ EV: 19W-3L (86.4%), +$975 -- Best tier

The 16-20% zone is the only losing TB tier. Small sample (24 bets) so not actionable yet, but worth monitoring.

### FOURTH: Concentration Works

Retroactive analysis: if we'd only taken OT TB + Hits Allowed + Earned Runs from the start:
- Record: 84W-38L (68.9%)
- PnL: +$1,766
- ROI: 15.4%

vs actual system with all markets: 106W-78L (57.6%), +$639, 3.7% ROI.

**The alpha was always there. The leaks were drowning it.**

---

## 2026-04-26: Week 17 Deep Dive (199 graded bets)

### THE BIG FINDING: Game Model OVERs Are Statistically Significant (p=0.017)

Game model OVER picks: 5W-0L, +$642, 100% WR. Statistically significant at 95% confidence (z=2.13, p=0.017). This is a tiny sample (5 bets) but the signal is strong:
- Positive CLV (+0.44%) means we're beating the closing line on OVERs
- UNDER CLV is -0.49% - we're consistently buying worse on unders
- The under-bias hypothesis from W16 has been REVERSED for game model

### SECOND BIG FINDING: OddsTrader TB is the Strongest Signal (p=0.006)

27W-10L (73% WR) on Total Bases market. z=2.51, p=0.006. This is the most statistically significant strategy in the entire system. It survives even stringent multiple-comparison corrections.

### THIRD: K-Prop Pitcher Misrate Pattern Identified

4 pitchers account for ~47% of all K-prop losses: Ragans (-$95), Skubal (-$101), Sasaki (-$190), Misiorowski (-$190). All are high-K arms with ceiling risk that the model's regression can't capture. A simple blacklist on these arms for UNDER bets would dramatically reduce variance.

### K-Prop Bias Quantified Precisely

| Side | Model Bias | Interpretation |
|------|-----------|----------------|
| UNDER | -0.84 Ks | Model under-predicts (actual Ks higher than expected) |
| OVER | +0.96 Ks | Model over-predicts (actual Ks lower than expected) |

This asymmetry explains why UNDER bets win at 63% (model's probability is conservative) while OVER bets win at 59% (some false positive edges).

### Combined System NOT Significant Yet

At 199 bets, combined WR is 54.0% (107W-91L). z=0.47, p=0.32. The profitable sub-strategies are diluted by game model UNDERs (10W-12L) and dead ML bets. Cutting the losers would sharpen the portfolio.

### Focus, Don't Diversify

The alpha is concentrated in 4 markets:
1. OddsTrader TB: +$616, 84% ROI, p=0.006
2. K-prop UNDER: +$451, 63% WR
3. Game model OVER: +$642, p=0.017
4. OddsTrader KS: +$101, 34% ROI

Everything else is noise or drag. The path to 15% ROI is through concentration, not diversification.

---

## 2026-04-25: Under-Bias Discovery (91 graded bets)

### THE BIG FINDING: Model Has Systematic Under-Bias in Game Totals

CLV analysis by side reveals the model is buying worse prices on unders:
- **UNDER CLV: -0.62%** (10/26 positive = 38%)
- **OVER CLV: +0.47%** (3/5 positive = 60%)

84% of game model picks are unders. We were filtering out profitable overs.

### Over Bets in 8-12% Sweet Spot Are Crushing
- OVER 8-12% edge: **3W-0L, +$399**
- OVER 12%+ edge: 0W-2L, -$300

Same pattern as unders - 12%+ toxic, 8-12% golden. The PREFERRED_SIDE=UNDER filter was removing the best-CLV picks.

**Change made**: Removed MLB UNDER-only restriction. Both sides now allowed at 8%+ edge with 12% cap. (EXP-005)

### K-Prop Bias Correction Working
- 0.91x correction already applied, overall bias now +0.28 Ks (down from ~+0.86)
- OVER bets still biased high (+1.12 Ks) but both sides profitable
- UNDER: 12W-7L +$348 (19.9% ROI) | OVER: 15W-11L +$155 (7.0% ROI)
- No further correction needed yet - monitor

### Bug Fixed: Auto-Grader Duplicate Entries
- auto_grader.py appended to bet_ledger without checking for existing entries
- 10 duplicate bets removed from multi-book ledger
- Actual multi-book: 10W-11L -$10 (was showing -$45 with dupes)

---

## 2026-04-19: Week 1 Summary (68 graded bets, 87 with scanner)

### WEEKLY PATTERN: Totals Model Has Real Edge, Everything Else Is Noise or Drag

The week told a clear story:
- **Totals-only game model**: 19W-13L-1P, +$725, 16.1% ROI - this is the engine
- **K-prop UNDER**: 6W-2L, +$331, 75% WR - secondary engine
- **Everything else** (ML, K-prop OVER, NHL, 5-8% edge bets): net negative or break-even

If we had run ONLY totals 8%+ edge AND K-prop UNDER from day 1, estimated ROI would be 25%+.

### NEW: Edge Floor Should Be 8%, Not 5%

Updated edge tier analysis with full week data:
| Edge Range | Record | PnL | WR |
|-----------|--------|-----|-----|
| 5-8% | 7W-8L | +$12 | 47% |
| 8-10% | 3W-2L-1P | +$122 | 60% |
| 10-12% | 6W-2L | +$521 | 75% |

The 5-8% tier is pure noise (47% WR). Raising the floor to 8% cuts ~40% of volume but should dramatically improve ROI.

### NEW (Research): Overdispersion Parameter Is Wrong
Our `MLB_OVERDISPERSION = 1.8` is too low. Empirical data (FanGraphs community, 2008-2013): AL variance/mean = 2.22, NL = 2.15, per-inning = 2.11. Our tails are too thin, meaning we underestimate extreme scores. Change to 2.1 and re-backtest. Quick config change with potential calibration improvement.

### NEW (Research): SwStr% Is the Dominant K Predictor
Podhorzer's xK% formula achieves R-squared = 0.892 vs our K/9-based model (~0.70). Swinging strike rate has r=0.81 correlation with K%. If we integrate Statcast SwStr% data, our K-prop accuracy could improve dramatically. Plus the platoon matchup formula: `(B*P)/(0.84*B*P+0.16)` for per-lineup-slot K estimation.

### NEW (Research): Correlated Bets Need Kelly Reduction
When betting totals + K-prop on same game, reduce each to ~60-70% of individual Kelly. JQAS 2023 paper confirms correlated outcomes require lower individual sizing.

### NEW: Model Sub-Component Disagreement Matters

When Poisson and XGBoost disagree by >1 run on a totals game, the bet seems riskier. Need to track this formally. Initial observation: all 3 totals picks on Apr 17 had >1 run Poisson/XGBoost spread, and 2 of 3 lost.

### NEW: Repeat Matchup Degradation

Betting the same series matchup 3 days in a row (BAL@CLE UNDER, MIL@MIA UNDER) shows diminishing returns. The market adjusts to the specific pitching matchup after game 1. Series game number should be a penalty factor.

---

## 2026-04-19: Deep Analysis (68 graded bets, 87 with scanner)

### THE BIG FINDING: CLV Predicts Winners
- Positive CLV bets: **76.9% win rate** (10/13)
- Negative CLV bets: **45.0% win rate** (9/20)
- **32 percentage point spread** - this is enormous
- Average CLV remains -0.42%, meaning most bets are behind the close
- Implication: if we could predict CLV pre-game, we'd have a massive filter

### K-Prop Model Has Systematic Bias
- Model overestimates strikeouts by **+0.58 Ks** on average (MAE 1.85)
- This explains everything: UNDER 6W-2L (+$331) vs OVER 11W-8L (-$164)
- UNDER bets benefit from the bias (model thinks UNDER is less likely than it is)
- OVER bets hurt by bias (model thinks OVER is more likely than it is)
- Fix options: calibration offset, raise OVER edge threshold, or both

### Double Exposure Costs Money
- 3 instances of same-pitcher double bets: net -$91
- Fixed: MAX_BETS_PER_PITCHER 2 -> 1

### Edge Tier Update (41 graded game bets)
| Edge Range | Record | PnL | ROI |
|-----------|--------|-----|-----|
| 5-8% | 6W-4L | +$320 | ~16% |
| 8-12% | 8W-3L | +$642 | ~26% |
| 12%+ | 4W-5L | -$211 | ~-12% |

**8-12% is the sweet spot.** Consider tightening cap from 12% to 10%.

### Smart Scanner is Quietly Profitable
- 11W-8L, +$75, 19.7% ROI on $20 flat bets
- UNDER: 7W-2L (+$107) vs OVER: 4W-6L (-$32)
- Cross-book devigging works for line shopping

---

## 2026-04-18: Updated Findings (52 graded bets)

### Edge Tiers (TOTALS ONLY - excludes moneylines)
| Edge Range | Record | PnL | ROI |
|-----------|--------|-----|-----|
| 5-8% | 5W-3L | +$328.10 | 36.7% |
| 8-10% | 1W-1L-1P | +$4.15 | 1.0% |
| 10-12% | 4W-2L | +$243.60 | 27.9% |
| 12-15% | 2W-3L | -$158.62 | -21.0% |
| 15-20% | 2W-2L | -$52.67 | -8.3% |
| 20%+ | 1W-1L | -$25.85 | -8.2% |

**5-12% is the profit zone: 10W-6L, +$575.85, 21.9% ROI**
**12%+ is destruction: 5W-6L, -$237.14, -11.8% ROI**

### Moneyline is Overfit
- Backtest: AWAY ML +4.1% ROI across 1332 bets
- Live: AWAY 0-6, HOME 2-0
- Conclusion: Backtest was overfit. ML DISABLED as of 2026-04-18.

### CLV Analysis
- Average: -0.35% (39% positive)
- NHL CLV: -0.44% (25% positive) -- model is weaker on hockey
- MLB CLV: -0.28% (50% positive) -- closer to market
- Winners had +0.19% avg CLV, losers had -0.73% -- CLV is predictive
- UNDER CLV: -0.52%, OVER CLV: +0.47% -- market adjusts toward our UNDERs by close

### K-Props Remain the Star
- 13W-5L, 72% WR, +$369.74, 12.3% ROI
- UNDER: 4W-1L, +$267.39 (dominant)
- OVER: 9W-4L, +$102.35 (solid but lower edge)

### Bugs Fixed 2026-04-18
1. **Grading bug**: Bets were graded against wrong-date scores when same teams play consecutive days
2. **Duplicate bet bug**: Same game could be logged twice when line moves between scan runs
3. **ML not actually paused**: PREFERRED_ML_SIDE was set but never emptied. Added explicit disable flag.

## 2026-04-17: Initial Findings (from paper trading days 1-10)

- **Edge cap at 12% is critical.** Confirmed with more data: 5-12% = profitable, 12%+ = net negative.

- **UNDER bias is real and large.** Game model, K-props all show UNDER outperforms OVER.

- **K-props are promising.** Now 13W-5L, 12.3% ROI. Poisson K distribution is strong.

- **CLV is roughly break-even.** -0.35% avg, not yet confirming persistent edge vs market.

- **FanDuel player props are one-sided.** All "To Record X" markets have no UNDER option. Killed batter hits model.

# Strategic Memo: Sports Edge System Assessment

**Date**: 2026-04-14
**Author**: Chief Strategist
**Classification**: Internal - Brutally Honest

---

## What's Working

**The architecture is sound.** Dixon-Coles + Elo + rest days produced a backtest Sharpe of 1.844 over 3 seasons and 1,829 bets. That is a real signal. The key evidence:

1. **The model is selective, and selectivity adds alpha.** Always-under at fixed 6.0 loses money (-13.7% to -0.3% per season). The model picking WHICH games to bet on is the entire value proposition. This is the single most important finding.

2. **The edge threshold analysis is clean.** ROI rises monotonically from 3% to 10% threshold, then collapses at 12%+ and goes negative at 15%+. This is exactly what you'd expect from a model with real but modest signal -- high claimed edges are miscalibration, not opportunity. The system correctly caps at 12%.

3. **Elo + rest days doubled ROI** from 2.02% to 4.19%. These are theoretically grounded features (team quality differential and fatigue) that don't overfit. Good feature engineering instinct.

4. **The tiering system is disciplined.** No C tier. L1 alone doesn't generate picks. The model is primary. This is correct architecture.

---

## What's Concerning

### The Backtest Report Contradicts the Design Doc

This is the single biggest red flag in the entire system. Stop and read this carefully.

The **design doc** says: "DC + Elo + rest days = +4.19% ROI, Sharpe 1.844, 1,829 bets, 55.6% WR"

The **latest_report.txt** says: "+1.80% ROI, Sharpe 1.077, 1,937 bets, 54.2% WR"

These are completely different results from supposedly the same system. The latest report header says "Enhanced features: Elo + rolling windows + rest days" but produces numbers matching the "DC + XGBoost residual correction" row in the design doc comparison table (1,937 bets, +1.80% ROI, 1.077 Sharpe).

**Either the design doc is outdated, the report was generated from a different config, or someone is quoting the wrong numbers as "best proven config."** This must be resolved before any real money touches this system. You cannot have your backtest report showing one set of numbers and your strategy document claiming another.

### The Calibration Table Is Alarming

Look at the calibration from latest_report.txt:

- When the model predicts 27% over probability, actual is 43%. Off by +16 points.
- When the model predicts 60% over probability, actual is 52%. Off by -9 points.
- When the model predicts 72% over, actual is 20% (n=5, but still).

The model is **systematically overconfident on unders** (predicts low over% but games go over more than expected) and **systematically overconfident on extreme predictions** in both directions. This maps directly to the edge bucket problem: the 3-5% and 5-8% edge buckets are both LOSING money (-4.49% and -2.37% ROI respectively). Only 8%+ edges are profitable.

This means the model's probability estimates are not well-calibrated in exactly the range where most bets are placed. The profitable bets are a subset, and you're diluting them with unprofitable ones.

### Paper Trading Sample Is Statistically Meaningless

3 graded bets. 1 win, 2 losses. -$163.64 P&L. This tells you absolutely nothing. You need 200+ graded bets minimum to draw any conclusion, and realistically 500+ for the confidence interval to be narrow enough to matter. The design doc acknowledges this but I want to be explicit: **you have zero live evidence that this system works.**

### Declining ROI By Season

The correct backtest (DC + Elo + rest days) shows:
- 2022-23: +6.02% ROI (572 bets, 56.8% WR)
- 2023-24: +3.91% ROI (581 bets, 55.5% WR)
- 2024-25: +2.45% ROI (676 bets, 54.7% WR)

**INVESTIGATED (Apr 14 2026). Root causes identified:**

1. **NHL scoring is declining toward the 6.0 line.** Avg total: 6.34 -> 6.20 -> 6.04. Over-6.0 rate: 48.9% -> 44.3% -> 41.3%. As scoring converges to the fixed backtest line, there's less signal to exploit. This is a structural issue with the BACKTEST, not necessarily the model.

2. **Over bets are disappearing.** The model's under-bias is worsening: 70% -> 77% -> 88% unders. But overs are far more profitable (2022-23: $7,723 from overs vs $2,175 from unders). As the model generates fewer over bets, total profitability drops.

3. **Claimed edges are INCREASING while ROI decreases.** Avg claimed edge: 9.7% -> 10.3% -> 10.7%. This suggests miscalibration is growing -- the model is more confident but less accurate. Classic overconfidence drift.

**Key nuance:** The fixed 6.0 line backtest may overstate the decline. In live betting, market lines adjust to scoring trends (5.5-6.5 range). Our model would see different, potentially better opportunities against varied lines.

### The Model Is Heavily Under-Biased

From the paper ledger: of 10 bets, 7 are unders. From the backtest: 1,636 under bets vs 301 over bets (84% unders). The over bets are far more profitable ($6,741 vs $260 P&L).

The model has a systematic lean toward unders, and the unders barely break even. The overs carry the P&L. This suggests the model's under-bias is a structural flaw, not a feature.

### Live Edge Claims Are Enormous

The paper ledger shows edges of 7-17%. The backtest shows edges above 12% are model errors (-2.67% ROI at 15%+ threshold). The live system is claiming edges that the backtest says are miscalibrated. The MAX_EDGE cap is 12% in the code, but the paper ledger has a bet with 16.87% edge. Something is wrong with either the cap enforcement or the edge calculation between backtest and live.

---

## Hard Questions Nobody Has Asked

1. **Is the fixed 6.0 line backtest actually predictive of live performance?** Real lines range 5.5-7.0. The model was backtested on a fixed 6.0 line because historical odds data isn't available. But a model that beats a fixed line is fundamentally different from a model that beats a market-set line. The market line already incorporates goalie announcements, injuries, rest days, etc. You might be backtesting against a straw man.

2. **What is the model's CLV?** CLV (closing line value) is the gold standard for whether a bettor has real edge. The paper ledger has zero CLV data after 3 graded bets. Without CLV tracking, you have no way to distinguish skill from variance. This should have been the FIRST metric implemented.

3. **How correlated are the Dixon-Coles and XGBoost outputs?** If they're highly correlated (likely, since they see similar inputs), the "ensemble" is just a complicated way to average with noise. The ensemble weighting (0.35/0.35/0.30) appears arbitrary. Has anyone measured whether the ensemble actually beats the best single model on out-of-sample data?

4. **Why did the XGBoost residual correction HURT performance?** The backtest shows XGBoost residual correction produced the worst results of any config (+1.80% ROI). Yet XGBoost gets 35% weight in the live ensemble. If XGBoost can't even improve on Dixon-Coles as a correction factor, why should we believe it adds value as an ensemble member?

5. **What is the actual vig you'd pay live?** The backtest assumes -110 standard juice. Real books vary. Some totals are -115/-105 or worse. At +1.80% ROI (the actual latest report number), even 5 cents of extra juice wipes out all profit.

6. **Is the MLB model backtested at all?** I see no MLB backtest results anywhere. You're paper trading MLB bets based on a model with zero historical validation. The design doc hand-waves about extending to MLB "same Level 2 framework, different features" as if that's trivial. Baseball and hockey have completely different scoring dynamics.

7. **Who is actually going to place these bets?** The system finds edges at "model" odds of -110. But you need to actually get -110 or better at a real sportsbook. What's the execution layer? Are you accounting for line movement between pick generation and bet placement?

---

## What a World-Class Quant Fund Would Do Differently

1. **They would not ship a model with a contradictory backtest report.** The discrepancy between the design doc claims (+4.19% ROI) and the actual latest report (+1.80% ROI) would be a fireable offense at any serious shop. You need one source of truth, version-controlled, reproducible.

2. **They would build a proper walk-forward backtest with actual market lines.** Fixed 6.0 is a toy. Without historical odds data, you cannot validate the system. Period. They would buy or scrape historical closing lines from Pinnacle and backtest against real market prices. This is not optional -- it is the minimum viable backtest.

3. **They would track CLV from day one of paper trading.** Not "we'll add it later." The CLV tracker exists in the codebase (clv_tracker.py) but the paper ledger shows zero CLV data. This is the single most important validation metric and it's not being captured.

4. **They would run a proper calibration analysis and fix the probability estimates.** Isotonic regression is imported in nhl_model.py but the calibration table shows massive miscalibration. Either the calibration isn't working or it's not being applied. A well-calibrated model with 2% edge beats a miscalibrated model with 5% "edge" every time.

5. **They would never put the MLB model live without a backtest.** Zero tolerance. No backtest, no bets. Full stop.

6. **They would size positions based on actual measured edge, not claimed edge.** Given the calibration problems, the Kelly sizing is based on probabilities the model gets wrong. This means systematic over-betting on miscalibrated games.

7. **They would have a P&L attribution system.** Which model component is generating the alpha? Is it Dixon-Coles team strength? Elo adjustments? Rest day signal? Market anchor? Without attribution, you can't improve what you don't measure.

8. **They would set a hard stop-loss and drawdown limit for paper trading.** The backtest shows max drawdown of $5,245 on a $5,000 bankroll -- over 100% of starting capital (bankroll grew before the drawdown hit). There's no risk management beyond Kelly sizing.

---

## Next Strategic Move

**RESOLVED (Apr 14 2026): Backtest discrepancy explained.**

The +4.19% and +1.80% numbers are from DIFFERENT configs, not a bug:
- +4.19% ROI, Sharpe 1.844 = DC + Elo + rest days (OUR LIVE CONFIG)
- +1.80% ROI, Sharpe 1.077 = DC + XGBoost residual correction (rejected config)

The latest_report.txt was overwritten by the XGBoost run. Report has been regenerated from the correct run. The design doc's +4.19% is accurate.

**This changes the strategic picture significantly:**
- The system IS viable (not borderline). +4.19% gives ~2% margin after vig.
- The 3-5% edge bucket is PROFITABLE (+3.37% ROI) in the correct backtest, not -4.49%.
- The 3% minimum edge threshold is justified. No need to raise to 8%.
- Declining ROI is still real (+6.02% -> +3.91% -> +2.45%) but from a much stronger base.

**NEW #1 priority: Investigate declining ROI.** If the -60% trend continues, we're at ~+1% by next season. Possible causes: market sharpening, model staleness, or seasonal artifacts. This needs a deep dive.

---

## Kill List

**Stop doing these things immediately:**

1. **Stop paper trading MLB without a backtest.** You're generating noise that will contaminate your assessment of the system. The BOS @ MIN "win" (actual total: 19 on an over 7.5 line) tells you nothing about model quality -- a dart thrown at a wall would have hit that one.

2. ~~**Stop quoting +4.19% ROI.**~~ **RESOLVED**: +4.19% IS the correct number for the live config. The +1.80% was from a different (XGBoost) config. Quote +4.19% with the caveat: "against fixed 6.0 line, 3 seasons walk-forward."

3. ~~**Stop betting 3-5% edges.**~~ **REVISED**: In the correct backtest, 3-5% edges produce +3.37% ROI (not -4.49%). The 3% minimum is justified. However, 8%+ edges still produce the best ROI (+5.10%), so consider weighting toward higher-edge bets.

4. **Stop treating the fixed-6.0 backtest as definitive evidence.** It's a useful signal but it's not testing what you'd actually do live. Every time you cite these numbers, add the caveat "against a fixed 6.0 line, not real market lines."

5. **Stop adding features that haven't been validated.** Goalie GSAX hurt. Form divergence hurt. XGBoost residual correction hurt. The reflex to add complexity is the enemy. Only add features that survive walk-forward out-of-sample testing.

6. **Stop logging bets with 15%+ claimed edge.** The backtest proves these are model errors. The MAX_EDGE cap exists in the code at 12% but the paper ledger shows a 16.87% edge bet got through. Fix the leak.

---

## Bottom Line

You have a system with real but modest signal in NHL totals, built on sound principles (Dixon-Coles is a proven framework, Elo and rest days are theoretically grounded features). The architecture is professional-grade.

But the execution has gaps that would prevent any serious quant from deploying capital: contradictory performance claims, no CLV tracking on live bets, miscalibrated probabilities, an unvalidated MLB model running live, and declining ROI across seasons.

The edge, if it's real, is small. Small edges require flawless execution. Right now, execution is not flawless.

Fix the foundation before building higher.

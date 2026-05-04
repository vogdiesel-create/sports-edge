# Sports Edge - Dead Ends

Things we tried that didn't work. Don't revisit without new evidence.

## 2026-04-16: Batter Hits Model
- **What:** Poisson model for MLB batter hits (over/under)
- **Result:** OVER = -15% ROI across all thresholds in backtest. UNDER = +34% ROI but FanDuel doesn't offer UNDER on hit props (all markets are "To Record X Hits", one-sided)
- **Why it failed:** The profitable side has no market. The available side is unprofitable.
- **File:** batter_hits_model.py (exists but NOT in pipeline)
- **Revisit if:** A sportsbook starts offering UNDER on batter hit props

## 2026-04-18: Moneyline AWAY Bets
- **What:** Betting moneyline AWAY based on model edge (backtest showed +4.1% ROI on 1332 bets)
- **Result:** 0-6 AWAY live, -$452. HOME 2-0 but tiny sample.
- **Why it failed:** Backtest was overfit. The AWAY ML edge likely captured noise in the training data. Live market is more efficient than backtest suggested. Small sample but 0-6 is damning.
- **Action taken:** MONEYLINE_DISABLED=True in edge_detector.py. All 3 ML code paths blocked.
- **File:** edge_detector.py (MONEYLINE_DISABLED flag)
- **Revisit if:** Fundamentally different model architecture with out-of-sample validation on ML specifically

## 2026-04-29: K-Prop Model (ALL sides, ALL thresholds)
- **What:** Poisson K-distribution model for MLB pitcher strikeout props
- **Result:** 51W-50L final. -$599. 8 straight losses to end. PERMANENTLY DEAD.
- **Why it failed:** K/9-based prediction systematically overestimates K counts (+0.84 on UNDER, +0.96 on OVER). Model can't price elite K arms (Ragans 11K, Suarez 10K, Cecconi 3K). The bias is structural, not correctable with offsets.
- **Action taken:** Pick generation disabled. Model shut down permanently.
- **Revisit if:** Complete rebuild with SwStr%/CSW% via Statcast (Podhorzer xK% R2=0.892 vs our 0.70). This is a full rewrite, not a tweak.
- **Key learning:** K/9 regression to mean is the wrong approach for K prediction. Swinging strike rate is the dominant predictor.

## 2026-04-19: K-Prop OVER Bets at 5% Edge (subset of above)
- **What:** K-prop OVER bets with 5%+ minimum edge threshold
- **Result:** 11W-8L, -$164 net loss. 58% WR insufficient at standard juice.
- **Why it failed:** Model overestimates Ks by +0.58 avg. This inflates OVER edge calculations, making many OVER bets look attractive when they're actually marginal or negative EV.
- **Superseded by:** Full K-prop shutdown (Apr 29).

## 2026-04-26: Game Model UNDER Bets (Totals)
- **What:** Betting game totals UNDER based on model edge (was our primary game-model strategy)
- **Result:** 10W-12L-1P, -$170, 45% WR. Negative CLV (-0.49%).
- **Why it failed:** Model's UNDER probability estimates attract the same market as everyone else. We consistently buy worse than closing line. Meanwhile OVERs beat closing (+0.44% CLV) and are 5W-0L.
- **Action taken:** Proposing EXP-006 to disable or severely restrict.
- **Revisit if:** CLV flips positive on UNDERs OR model is rebuilt with fundamentally different run-scoring methodology

## 2026-04-30: OddsTrader RBI Market
- **What:** OddsTrader "Player to hit a RBI" prop bets
- **Result:** 11W-28L (28.2%), -$956. Catastrophic.
- **Why it failed:** RBI is highly correlated with RISP opportunity (teammate-dependent). Model can't predict baserunner situations. Worse than random.
- **Action taken:** Added to DISABLED_MARKETS.
- **Revisit if:** Never. The market is structurally unpredictable from individual player stats.

## 2026-04-30: OddsTrader Strikeouts (Batter Ks)
- **What:** OddsTrader batter strikeout over/under props
- **Result:** 12W-13L (48%), -$279.
- **Why it failed:** Similar to pitcher K-props - batter K rate prediction is noisy. Model accuracy insufficient to overcome vig.
- **Action taken:** Added to DISABLED_MARKETS.
- **Revisit if:** Strong batter K-rate prediction model developed (plate discipline metrics, SwStr% against).

## 2026-04-16: Edges above 12%
- **What:** Betting on picks with model edges >12%
- **Result:** 3W-7L, massive losses. The model's probability estimates become unreliable at extreme edges.
- **Why it failed:** Model overconfidence on extreme lines. Likely these represent data issues or model blind spots, not real edges.
- **Action taken:** MAX_EDGE capped at 12%
- **Revisit if:** Model is fundamentally rebuilt with better calibration at extremes

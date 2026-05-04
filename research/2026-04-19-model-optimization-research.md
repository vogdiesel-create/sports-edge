# Sports Edge Model Optimization Research
**Date**: 2026-04-19
**Purpose**: Actionable findings for CLV prediction, K props, totals calibration, Kelly sizing, and line timing

---

## 1. CLV Prediction: Pre-Game Edge Estimation

### What Sharps Actually Do

CLV is measured post-bet, but sharps use these **pre-game signals** to predict which bets will have positive CLV:

**Feature set for CLV prediction models:**
- **Opening line vs. your model's fair value**: The gap between opening line and your estimated true probability is the strongest predictor of future CLV. If your model says true prob = 55% and the opening line implies 50%, that 5% gap tends to persist or widen as sharp money confirms.
- **Line movement direction after opening**: If the line moves toward your number in the first 1-2 hours, it confirms sharp agreement. Track whether your model's picks historically correlate with early sharp movement.
- **Book-to-book spread**: If one book posts a line 3+ cents off the Pinnacle consensus, that's a soft line likely to correct — capturing CLV.
- **Market efficiency by sport/league/prop type**: CLV opportunity varies. MLB totals and props are less efficient than NFL sides. Player props are the least efficient market.
- **Information timing advantage**: Betting before lineup confirmations (3-4h pre-game in MLB) on pitching matchups where you've already modeled the probable starter.

**Actionable for Sports Edge:**
Build a meta-model that predicts CLV from: (1) your model's edge size, (2) time of bet placement relative to game, (3) which book you're betting, (4) market type. Track these features on every bet in paper_ledger.json. After 200+ bets, regress actual CLV on these features to optimize bet selection.

**Key finding**: Pinnacle's study confirmed bettors with consistent positive CLV are profitable long-term. Aim for >60% of bets beating CLV over 200+ sample.

Sources:
- [Pinnacle CLV Study / Sharp Football Analysis](https://www.sharpfootballanalysis.com/sportsbook/clv-betting/)
- [ProbWin CLV Guide](https://en.probwin.com/guides/closing-line-value-clv-ultimate-metric-measure-your-edge/)
- [BetStamp CLV Methods](https://betpredictionsite.com/blog/closing-line-value-clv-gambling/)

---

## 2. Strikeout Prop Modeling Improvements

### Current Model Gaps (vs. State of Art)

Your current K prop model uses: K/9 rolling averages, opponent team K%, park factor, weather, home/away. Here's what's missing:

### A. Pitch Mix Data: YES, It Outperforms Simple K/9

**MIT Sloan paper** (2.5M pitches, 402 pitchers, 2012-2017): Pitch characteristic models achieved **median absolute error of 2.47 percentage points** for K%. Key finding: **relationships among all pitches matter more than individual pitch characteristics**. Specifically:
- Maximum pitch velocity + strike rate = most important
- **Vertical movement range** among a pitcher's pitches = next most important (more predictive than number of pitch types or speed differential)
- Pitch mix diversity matters, but movement profile is the driver

**FanGraphs "Stuff" metric** (revised): Correlation with K/9 = **R = 0.53** (up from 0.42 in original version). Components: peak velocity, velocity differential (range between fastest/slowest), and pitch break distance. Critical finding: **weight by usage frequency** — a filthy slider thrown 30% of the time is worth more than one thrown 5%.

**Stuff+ year-over-year stability**: Very high (R = 0.74 year-to-year), making it a reliable input for season-long models. However, K:BB ratio actually has *better* year-to-year predictive correlation (R = 0.58) than Stuff+ alone.

### B. Platoon Splits: YES, Use Them

**FanGraphs matchup K% formula** (1.5M plate appearances, 2002-2012):

```
Expected Matchup K% = (B * P) / (0.84 * B * P + 0.16)
```

Where B = batter's K% vs. that pitcher handedness, P = pitcher's K% vs. that batter handedness.

This is a proper odds-ratio formula that accounts for the fact that both pitcher and batter contribute to K probability. **Apply this at the lineup level** by computing expected K% per lineup slot and aggregating.

### C. Best Predictive Feature: Swinging Strike Rate

**Podhorzer's xK% formula** (FanGraphs, R-squared = **0.892**):

```
xK% = -0.61 + (L/Str * 1.1538) + (S/Str * 1.4696) + (F/Str * 0.9417)
```

Where:
- S/Str = Swinging Strike Rate (correlation with K% = **0.81** — dominant predictor)
- F/Str = Foul Strike Rate (correlation = 0.20)
- L/Str = Looking Strike Rate (correlation = 0.01)

**This is the single most predictive K formula available.** If you can get pitcher SwStr% data (available via Statcast), it should be your primary feature, far outperforming K/9.

### D. Practical Upgrade Path for Your Model

1. **Immediate**: Add pitcher SwStr% as primary feature (biggest single improvement)
2. **Next**: Add platoon-adjusted K% using the FanGraphs matchup formula per lineup slot
3. **Later**: Add Stuff+ or PitchingBot grades as supplementary features for pitchers with limited recent sample (< 3 starts)

Sources:
- [Sloan Conference: Pitch Mix & K Rate](https://www.sloansportsconference.com/research-papers/predicting-major-league-baseball-strikeout-rates-from-differences-in-velocity-and-movement-among-player-pitch-types)
- [FanGraphs: Definitive xK% Formula](https://fantasy.fangraphs.com/the-definitive-pitcher-expected-k-formula/)
- [FanGraphs: Matchup K% Forecasting](https://blogs.fangraphs.com/bettermatch-up-data-forecasting-strikeout-rate/)
- [FanGraphs: Revisiting Stuff Metric](https://community.fangraphs.com/revisiting-the-stuff-metric/)
- [Steven Martinez K% Model (Ridge, R2=0.699)](https://steven-martinez-colon.github.io/projects/mlb-kpercent.html)
- [FanGraphs: PitchingBot ML model](https://community.fangraphs.com/pitchingbot-using-machine-learning-to-understand-what-makes-a-good-pitch/)
- [Baseball Prospectus: Stuff+ ERA Prediction Limits](https://www.baseballprospectus.com/news/article/82426/prospectus-feature-an-updated-evaluation-of-hitting-and-pitching-including-stuff-metrics/)

---

## 3. MLB Totals Model Calibration

### Your Current Setup

Your `mlb_model.py` uses: `MLB_OVERDISPERSION = 1.8` (variance/mean ratio), with negative binomial distribution, separate home/away lambdas convolved independently.

### Research Findings

**Empirical overdispersion values** (FanGraphs community research, 2008-2013 MLB):
- AL: Mean = 4.50, Variance = 10.00 → **ratio = 2.22**
- NL: Mean = 4.26, Variance = 9.14 → **ratio = 2.15**
- Per-inning: Mean = 0.48, Variance = 1.01 → **ratio = 2.11**

Your current `1.8` is **too low**. The data shows variance/mean closer to **2.1-2.2**. This means your model has tails that are too thin — you're underestimating probability of extreme scores, which affects over/under pricing at the tails.

**Recommendation**: Increase `MLB_OVERDISPERSION` to **2.1** and re-backtest. This should improve calibration on games that land 3+ runs away from the posted total.

### Separate Home/Away: YES, It Helps

**You're already doing this** with separate `lambda_home` and `lambda_away`. This is correct and validated by the research.

The bivariate CMP paper (2024, Journal of Quantitative Analysis in Sports) goes further: it models **correlation between home and away scoring** through a random effect. In baseball, this correlation is modest but real — game state (blowouts, bullpen usage in close games) creates scoring dependence. For now, independent distributions are a reasonable approximation, but if you want to squeeze more accuracy:

- **Conway-Maxwell-Poisson (CMP)** model outperforms both Poisson and NB at large samples (n > 1900), because it handles both over- AND under-dispersion dynamically per game context
- However, implementation complexity is high. NB with correct overdispersion parameter gets you 90% of the way there.

### Bullpen Quality/Fatigue: Significant Factor

**Academic finding** (JQAS, "Out of Gas: Quantifying Fatigue in MLB Relievers"):
- Relievers who threw 15+ pitches show short-term velocity decreases in subsequent games
- At 20+ pitches, the effect amplifies
- Effect halves per day of rest

**Practical implementation for totals:**
- Track bullpen innings over trailing 3 days
- If a team's pen threw 5+ innings over last 2 days, add +0.2 to 0.4 runs to their expected scoring allowance
- High-K% rested bullpen = lean under; fatigued/overworked pen = lean over

**Your `compute_bullpen_fatigue` function already exists in `mlb_data_pipeline.py`** — verify it's being weighted appropriately in the ensemble.

Sources:
- [FanGraphs: NB Distribution for Run Scoring](https://community.fangraphs.com/run-distribution-using-the-negative-binomial-distribution/)
- [Dolinar: Poisson Run Distribution by Inning](https://stats.seandolinar.com/mlb-poisson-distribution-to-model-runs-scored-per-inning/)
- [Dolinar: Negative Binomial Run Distribution](https://stats.seandolinar.com/mlb-run-distribution-neg-binomial/)
- [Bivariate CMP for Sports (arXiv 2024)](https://arxiv.org/abs/2409.17129)
- [JQAS: Bullpen Fatigue Study](https://www.degruyterbrill.com/document/doi/10.1515/jqas-2018-0007/html?lang=en)
- [Data Jocks: Runs Per Game Modeling](https://thedatajocks.com/modeling-runs-per-inning-runs-per-game/)

---

## 4. Kelly Criterion Refinements

### Key Academic Papers

**1. Chu, Wu, Swartz (SFU) — "Modified Kelly Criteria"**

Core finding: When true win probability p is **estimated** (not known), the Kelly fraction should shrink. Their modified Kelly is smaller than standard Kelly and accounts for estimation uncertainty via a decision-theoretic framework.

Simulation results:
- Modified Kelly profitable 65% of runs vs. original Kelly profitable only 53%
- 3/5 modified Kelly runs outperformed original by end of wagering season
- Original Kelly has higher variance with greater potential both up and down

**2. Beggy (Wharton, 2023) — "Sports Betting Selection and Sizing"**

Critical finding: **Full Kelly leads to bankruptcy in 100% of realistic simulations.**

Recommended strategy: **Half Kelly (0.50 coefficient) with a 10% threshold** (only bet when your estimated edge exceeds 10% of the odds-implied probability).

Performance: ~80% annual ROI over 11-year backtest with this approach.

Volume impact of threshold:
- 2.5% margin threshold: 79,860 bets
- 5% margin: 10,275 bets
- 10% margin: 369 bets

**3. Matthew Downey — Fractional Kelly Simulations**

Tested pure uncertainty impact on bet sizing:
- At 5% std dev in probability estimate: optimal fraction drops from 0.40 to 0.38
- At 20% std dev: drops to 0.36
- Only at extreme 50% uncertainty does it drop significantly

The bigger reasons for fractional Kelly:
1. **Systematic overestimation bias** — bettors overestimate edge, making underbetting protective
2. **Risk of ruin** — even 1-2% catastrophic loss probability cuts optimal size dramatically (0.80 to 0.46)
3. **Downside percentile optimization** — optimizing 10th-percentile outcomes rather than median cuts bet size from 0.40 to 0.28

### Correlated Bets

JQAS (2023) paper on non-mutually exclusive bets: When betting multiple correlated outcomes (e.g., same-game props, or totals + moneyline), the Kelly fraction for each individual bet must be reduced. The total allocation across correlated bets should not exceed what a single Kelly bet would suggest for the combined position.

**For your system**: If betting both the total and a K prop in the same game, treat them as correlated and reduce each bet to ~60-70% of individual Kelly.

### Practical Recommendation for Sports Edge

Use **quarter Kelly (0.25x)** initially while validating model accuracy. Move to half Kelly (0.50x) only after 500+ graded bets with confirmed positive CLV. Apply a minimum edge threshold of 5-7% before any bet qualifies.

Sources:
- [Chu/Wu/Swartz: Modified Kelly Criteria (SFU)](https://www.sfu.ca/~tswartz/papers/kelly.pdf)
- [Beggy: Wharton Sports Betting & Kelly (2023)](https://wsb.wharton.upenn.edu/wp-content/uploads/2023/05/Beggy_2023__Betting_Kelly.pdf)
- [Matthew Downey: Fractional Kelly Simulations](https://matthewdowney.github.io/uncertainty-kelly-criterion-optimal-bet-size.html)
- [JQAS: Kelly for Non-Mutually Exclusive Bets](https://ideas.repec.org/a/bpj/jqsprt/v19y2023i1p37-42n6.html)
- [Thorp: Kelly in Blackjack/Sports/Stocks](https://gwern.net/doc/statistics/decision/2006-thorp.pdf)

---

## 5. Line Timing: When to Place MLB Bets

### Research Consensus

**MLB lines open**: Day before or morning of, once probable pitchers are confirmed.

**Sharp money enters**: Within the first hour of line posting, with heavier action on totals, F5, and alternate run lines (less monitored markets).

**Lineup release**: 3-4 hours before first pitch. This is when lines sharpen significantly as books incorporate confirmed lineups.

**Optimal windows by bet type:**

| Bet Type | Best Timing | Why |
|----------|-------------|-----|
| Totals (pitcher-driven) | Morning open, before lineup release | Sharp K on totals moves early; once lineups confirm, value evaporates |
| Moneyline (lineup-dependent) | After lineup release, before sharp wave | Need confirmed lineup, but bet before sharps adjust |
| K props | Morning, 6-12h before game | Props are least efficient; lines set early and don't sharpen as fast |
| Run line | After lineup release | Lineup composition affects run distribution more than pitching alone |

**Key patterns:**
- A sudden line shift at 9 AM on a West Coast game = almost certainly sharp money
- Totals sharps move first and early — if you see a total move immediately after opening, that's sharp action
- MLB lines move 5-10 cents at a time, which represents meaningful implied probability shifts
- **Reverse line movement** (line moves opposite to public betting %) = strongest sharp signal

**Actionable for your system:**
- Place totals and K prop bets at morning open (6-12h before game)
- Place moneyline bets 2-3h before game (after lineup release, before sharp wave)
- Track your CLV by time-of-bet to validate empirically with your own data

Sources:
- [WagerLab: 2025 MLB Line Movement](https://www.wagerlab.app/tracking-line-movement-in-2025-mlb-betting-markets/)
- [Sports Insights: Identify Sharp Money](https://www.sportsinsights.com/blog/identify-mlb-sharp-money-on-the-go/)
- [TheSpread: MLB Betting Strategies](https://www.thespread.com/betting-guides/mlb-betting-strategies/)
- [BoydsBets: Opening vs Closing Line](https://www.boydsbets.com/opening-vs-closing-line/)
- [ATS Stats: Reading Line Movement](https://www.atsstats.com/how-to-read-line-movement-before-you-bet/)

---

## Summary: Priority Implementation Order

1. **Increase MLB_OVERDISPERSION from 1.8 to 2.1** — Quick config change, should improve tail calibration immediately
2. **Add SwStr% to K prop model** — Single biggest accuracy gain for strikeout predictions (R2 jumps from ~0.70 to ~0.89 territory)
3. **Implement platoon-adjusted K% formula** — `(B*P) / (0.84*B*P + 0.16)` per lineup slot
4. **Switch to quarter Kelly (0.25x)** until 500+ graded bets confirm edge
5. **Log bet placement time** in paper_ledger.json for CLV-by-timing analysis
6. **Verify bullpen fatigue weighting** in your ensemble — the feature exists, confirm it's impactful

These are ordered by effort-to-impact ratio. Items 1 and 5 are config/logging changes. Items 2-3 require new data sources (Statcast/FanGraphs). Item 4 is a parameter change. Item 6 is validation of existing code.

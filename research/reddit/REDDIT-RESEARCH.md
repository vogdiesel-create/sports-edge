# Reddit & Community Sports Betting Model Research

**Date**: 2026-04-20
**Agent**: web-researcher
**Purpose**: Deep research into sports betting model-building community wisdom

---

## EXECUTIVE SUMMARY

This research synthesizes insights from Reddit communities (r/algobetting, r/sportsbook), sports betting forums (SBR Handicapper Think Tank), academic papers, and practitioner blogs. Key findings challenge several assumptions and validate others in our Sports Edge model approach.

**Critical Findings:**
1. Calibration >> Accuracy for betting profit (69.86% higher returns)
2. Props markets are least efficient and most beatable (low liquidity = edge)
3. CLV is meaningless for props (not enough sharp money for price discovery)
4. Negative binomial >> Poisson for MLB run modeling (variance ~2x mean)
5. Historical K rate beats granular pitch metrics for strikeout prediction
6. Sample size minimum: 300+ bets before drawing conclusions
7. Fractional Kelly (quarter to half) is professional standard

---

## TOPIC 1: MODEL CALIBRATION vs ACCURACY

### [TECHNIQUE] Calibration-Optimized Model Selection

**Source**: Walsh & Joshi (2024), "Machine learning for sports betting: should model selection be based on accuracy or calibration?" (arXiv:2303.06021)

**Key Finding**: Sports bettors selecting models based on calibration achieved +34.69% average ROI versus -35.17% with accuracy-based selection. The calibration-optimized model generated 69.86% higher average returns.

**Methodology**: Trained ML models on NBA data across multiple seasons, evaluated betting performance using published sportsbook odds.

**Credibility**: HIGH - Peer-reviewed academic paper with empirical results.

**Tag**: TECHNIQUE

**Implication for Sports Edge**: Our model evaluation should prioritize Brier score / calibration metrics over raw prediction accuracy. A model that says "60% chance" and is right 60% of the time beats a model that's "correct" more often but miscalibrated.

---

### [VALIDATION] Brier Score Does NOT Predict Profit

**Source**: beatthebookie.blog analysis of multiple football betting models across 8,375 bets

**Key Finding**: The most profitable model (Vanilla Poisson, short-term) had the WORST Brier score. Models with superior Brier scores ranked 2nd and 3rd in profit. The best model for profit had the lowest accuracy at 52.7%.

**Quote**: "A predictive model which is able to better predict the correct result in comparison to another model does not automatically also provide a better betting profit."

**Credibility**: MEDIUM-HIGH - Empirical analysis with large sample, single author blog.

**Tag**: CONTRADICTION (partially - calibration still matters but the relationship is complex)

**Implication**: Standard metrics alone don't predict profit. Need custom loss functions or empirical simulation for model selection. The disconnect exists because standard metrics optimize for prediction, not for market advantage.

---

### [TECHNIQUE] Calibration Implementation

**Source**: sports-ai.dev model calibration guide

**Key Techniques (ranked by effectiveness)**:
1. **Isotonic Regression** - Non-parametric monotonic mapping; most powerful with sufficient data
2. **Platt Scaling** - Simple but may underfit complex shapes
3. **Beta Calibration** - Captures tail skew in probability distributions
4. **Hybrid** - Temperature scaling followed by isotonic regression for residual correction

**Target Threshold**: Expected Calibration Error (ECE) < 0.015
**Maintenance**: Weekly reliability curve monitoring, monthly refit if ECE exceeds threshold

**Tag**: TECHNIQUE

---

## TOPIC 2: MARKET EFFICIENCY & WHERE EDGE EXISTS

### [TECHNIQUE] Props Are Least Efficient

**Source**: Unabated.com (Captain Jack Andrews), conordurkin.com liquidity analysis

**Key Finding**: Props markets lack sufficient sharp money for efficient price discovery. "CLV doesn't mean anything in props. There are very few market-making books when it comes to props. There's not a lot of sharp money to the point where there's enough liquidity in the market."

**Market Efficiency Hierarchy** (most to least efficient):
1. NFL sides/totals (highest liquidity, tightest spreads)
2. MLB/NBA moneylines
3. College sports (games with significant action)
4. MLB totals
5. **Player props** (widest spreads, lowest liquidity, most beatable)
6. Live betting (wider spreads due to time pressure)

**Credibility**: HIGH - Captain Jack Andrews is a well-known professional bettor.

**Tag**: VALIDATION (confirms our focus on K props is the right market)

**Implication**: Our K props focus targets the right market. The inefficiency means:
- Our model doesn't need to be as good as what beats NFL sides
- CLV is NOT a valid evaluation metric for our prop bets
- Book pricing may lag pitcher form changes significantly
- Less competition from syndicates in this space

---

### [WARNING] CLV Cannot Validate Props Models

**Source**: Unabated.com CLV analysis

**Key Finding**: Standard CLV calculation (beat closing line = long-term profit) breaks down in props because:
1. Not enough sharp money to move lines to "true" price
2. Few market-making books for props
3. Lines don't close efficiently

**Proper CLV calculation**: (Closing probability - Placed probability) / Placed probability, using vig-free closing line.

**Tag**: WARNING

**Implication**: We CANNOT use CLV to validate our K props model. Must use:
- Actual profit/loss over large sample
- Comparison to Pinnacle vig-free lines (where available)
- Internal calibration metrics
- Win rate vs. break-even rate at average odds

---

## TOPIC 3: MLB TOTALS MODELING (NEGATIVE BINOMIAL)

### [TECHNIQUE] Negative Binomial >> Poisson for Run Scoring

**Source**: FanGraphs community, WalkLikeASabermetrician, stats.seandolinar.com

**Core Problem with Poisson**: Mean equals variance assumption fails badly for MLB.
- Historical (1981-96): Mean R/G = 4.4558, Variance = 9.3603
- AL 2008-2013: Mean R/G = 4.4995, Variance = 9.9989
- NL 2008-2013: Mean R/G = 4.2577, Variance = 9.1394

**Variance is approximately 2x the mean** -- Poisson is fundamentally wrong.

**Poisson Problems**:
- Bunches too much probability around the mean
- Underestimates shutouts (31% actual vs 16% Poisson estimate)
- Underestimates blowouts
- Overestimates 1-run games

**Negative Binomial Parameters**:
- alpha (odds in favor of getting out) = Expected Value / (Variance - Expected Value)
- r = Expected Value * alpha
- Formula: P(X=k) = [gamma(k+r) / (gamma(k+1)*gamma(r))] * [(alpha/(1+alpha))^r] * [(1/(1+alpha))^k]

**Even Better Alternatives**:
- Tango Distribution (discovered by tangotiger)
- Ordered logistic regression
- Composite models: batters faced + runners left on base

**Limitation**: Both Poisson and NB underestimate shutouts due to non-random pitcher usage (managers pull starters strategically).

**Tag**: TECHNIQUE

**Implication for Sports Edge**: If we model totals, negative binomial is the minimum. But for K props specifically, this is less directly relevant -- though understanding the scoring environment helps contextualize pitcher workload and game script.

---

## TOPIC 4: STRIKEOUT PREDICTION & K PROPS

### [TECHNIQUE] Core K Prop Model Features

**Source**: Multiple - Outlier, Baseball Prospectus, Pitcher List, community consensus

**Primary Metrics (ranked by predictive power)**:
1. **Historical K rate** (K%) - Most predictive single feature
2. **CSW Rate** (Called Strike + Whiff) - Best single-number predictor of K ability, 30%+ = elite
3. **Opponent team K%** (by handedness) - Lineup vulnerability
4. **Recent form** (last 3 starts) - Captures changes in stuff/approach
5. **Projected pitch count / innings** - More pitches = more K opportunity
6. **Ballpark K factor** - Some parks favor Ks
7. **Umpire tendency** - Can add/remove ~0.5 runs per game

**Key Formula for Spot Identification**:
High-CSW pitcher (30%+) + High team K% opponent + deep start projection = Over value

**Tag**: TECHNIQUE

---

### [CONTRADICTION] Granular Pitch Metrics Add Little Over K Rate

**Source**: Baseball Prospectus, "Ahead in the Count" analysis

**Key Finding**: When controlling for prior K rate, swinging-strike rate adds almost NOTHING to next-year K rate prediction.
- With SwStr%: R-squared = 0.6118
- Without SwStr%: R-squared = 0.6110
- Incremental improvement: <0.1%

**Same-year correlations are strong** (SwStr% to K rate: 0.84), but for PREDICTION (next year), prior K rate dominates everything. SwStr% coefficient drops to 0.1236 (p=0.251, not significant) when K rate is included.

**Credibility**: HIGH - Baseball Prospectus rigorous statistical analysis

**Tag**: CONTRADICTION

**Implication**: For our K props model, historical K rate should be the primary feature. Granular pitch metrics (SwStr%, whiff rate) may help for WITHIN-SEASON form detection but are "virtually useless" for prediction once prior performance is known. Don't over-engineer with Statcast data when K% does 99% of the work.

---

### [TECHNIQUE] Third Time Through the Order Effect

**Source**: mlbprops.com analysis with historical data

**Key Data**:
- OPS: 91 (1st) -> 101 (2nd) -> 117 (3rd time through)
- ERA: 4.08 (1st) -> 4.20 (2nd) -> 4.57 (3rd)
- K rate declines measurably in later innings
- Only 22,470 PA 3rd time through vs 37,803 1st time through (managers pulling starters)

**Betting Application**:
- K prop UNDER favored when starters pitch deep (6+ innings)
- K prop OVER favored for short-leash pitchers (<5 innings, exit before penalty)
- Hitter props OVER favored when facing starter 3rd time through

**Critical Edge**: "Sportsbooks set props based on the blended average--that gap is where edges live."

**Tag**: TECHNIQUE

**Implication**: Factor projected innings pitched / pitch count into K props. A pitcher projected for 5 IP vs 7 IP faces dramatically different 3rd-time-through exposure.

---

### [TECHNIQUE] Umpire Impact on Strikeouts

**Source**: FanGraphs Hardball Times, FantasyGuru umpire reports

**Findings**:
- Umpire strike zone differences can add/remove ~0.5 runs per game
- GAMs (Generalized Additive Models) used to model umpire zones (oval, not rectangle)
- Some umpires call 2-3 more Ks per game than others consistently
- Umpire assignment known day-of-game (late information advantage)

**Tag**: TECHNIQUE

---

## TOPIC 5: BANKROLL MANAGEMENT (KELLY CRITERION)

### [TECHNIQUE] Fractional Kelly Is Professional Standard

**Source**: Multiple - Wikipedia, Wizard of Odds, matthewdowney.github.io simulations

**Key Numbers**:
- Full Kelly: 1/3 chance of halving bankroll before doubling
- Half Kelly: 1/9 chance of halving before doubling, growth reduced by only 25%
- Quarter Kelly: ~1/81 chance of halving before doubling

**Professional practice**: Most use Quarter to Half Kelly

**Critical Warning**: "If you wrongly believe you have an edge, it doesn't matter what fraction of Kelly you use--you're still going to lose all of your money eventually, as fractional Kelly only delays the obvious."

**Under Uncertainty (simulation findings)**:
- At 5% probability estimation error: optimal drops from full Kelly to 0.95 Kelly
- At 20% error: drops to 0.90 Kelly
- The bigger risk is SYSTEMATIC OVERESTIMATION of edge, not random error
- Overbetting produces worse outcomes than underbetting

**Tag**: TECHNIQUE

**Implication**: Use Quarter Kelly minimum given our model uncertainty. The risk of overestimating edge (which we have limited data to validate) means conservative sizing is critical. Paper bet first to establish true edge measurement.

---

## TOPIC 6: VALIDATION & SAMPLE SIZE

### [WARNING] Minimum Sample Sizes

**Source**: Community consensus from SBR, algobetting, Champion Bets

**Key Numbers**:
- **20 bets**: Completely meaningless (12-8 happens 25% of the time by chance)
- **100 bets**: Bare minimum to BEGIN evaluating consistency
- **300+ bets**: Clearer view of ROI, strike rate, and volatility
- **500+ bets**: CLV analysis becomes meaningful (for sides/totals)
- **1000+ bets**: Mathematically "almost impossible to lose if consistently generating significant positive CLV"
- **Full season paper trade**: Community recommendation before real money

**Tag**: WARNING

**Implication**: We need 300+ graded bets before drawing ANY conclusions about model quality. Current sample of ~50 is far too small.

---

### [TECHNIQUE] Paper Betting Before Real Money

**Source**: Multiple - community consensus

**Recommended timeline**: 30-60 days of paper betting, or one full season
**Key insight**: Paper betting validates the model AND validates your execution (can you actually get the lines your model prices?)

**What to track during paper phase**:
- Win rate vs. break-even rate
- Average odds obtained vs. model's target odds
- Consistency across different line ranges
- Drawdown patterns
- Time-of-bet vs. closing line (even if CLV imperfect for props)

**Tag**: VALIDATION (confirms our "paper first" approach)

---

## TOPIC 7: OVERFITTING & WHAT DOESN'T WORK

### [WARNING] Complexity Paradox

**Source**: Medium article (David Katzman), SportsInsights

**Key Finding**: More complex models (Random Forest, XGBoost) FAILED to beat simple linear regression despite extensive feature engineering.

**Reasons**:
1. Unnecessary variables introduce noise
2. Understanding variable RELATIONSHIPS matters more than quantity
3. Some features encode redundant information (e.g., SRS already encompasses other stats)
4. Game-specific factors (injuries, matchups) > season-long averages

**Quote**: "More complicated doesn't always mean better"

**Tag**: WARNING

**Implication**: Don't chase complexity. A well-calibrated model using K%, opponent K%, projected IP, and a couple contextual features may outperform a 50-feature ML model.

---

### [WARNING] The SportsInsights 10+ Filter Rule

**Source**: SportsInsights overfitting analysis

**Key Finding**: Systems with 10+ filters are almost certainly overfit. They work by "over-emphasizing random fluctuations, leading to horrible predictions."

**Three criteria for valid systems**:
1. Consistent year-to-year results (not just aggregate)
2. Large sample sizes
3. An EXPLAINABLE edge (why should this work?)

**Cautionary Example**: NBA system showing +154.87 units and 29.5% ROI by combining profitable teams + profitable officials + arbitrary spreads. No theoretical justification = no predictive power going forward.

**Tag**: WARNING

---

### [WARNING] Prediction Accuracy != Profitability

**Source**: Quant Galore Medium post (MLB algorithm story)

**Story**: Built MLB game prediction model with 60%+ accuracy across 20 years of data. Modified to bet mid-game when odds shifted favorably.

**Result**: 44% win rate, -$17.74 expected value per bet. Complete failure.

**Why**: "Even when the probability of the predicted team winning decreases, the books don't decrease the odds so drastically." Sportsbooks proved too sharp on game markets.

**Lesson**: Prediction accuracy alone doesn't ensure profitability when competing against sophisticated market makers. You need to beat the MARKET, not just predict the event.

**Tag**: WARNING

---

## TOPIC 8: WEATHER EFFECTS ON MLB

### [TECHNIQUE] Wind & Temperature Impact on Totals

**Source**: Multiple betting analysis sites, community consensus

**Wind (most impactful factor)**:
- Blowing out 10+ mph: Fly balls carry further, lean over
- Blowing out 15+ mph: Can shift expected totals by 1-2 runs
- Blowing in 10+ mph: Suppresses fly balls, lean under

**Temperature**:
- Below 55F: Suppressed ball flight
- 65-75F: Neutral
- Above 80F: Elevated scoring (avg ~4.2 R/G below 60F vs 4.7+ above 80F)

**Humidity** (counterintuitive):
- Humid air is LESS dense (water vapor lighter than N2/O2)
- But humid baseball weighs MORE
- Net effect: slight suppression, but minimal compared to wind/temp

**Rule of thumb**: Wind out 10+ mph + temp above 75F = lean over. Wind in 10+ mph + temp below 60F = lean under.

**Tag**: TECHNIQUE

**Implication for K Props**: Weather affects K props INDIRECTLY through:
- Cold weather may reduce bat speed (more whiffs?)
- Wind direction less relevant for strikeouts
- BUT game script matters: high-scoring game = quicker hook for starters = fewer late-inning Ks

---

## TOPIC 9: DATA SOURCES

### [TECHNIQUE] Free MLB Data for Model Building

**Sources identified**:
1. **MLB Stats API** - Official, real-time game data
2. **pybaseball** (Python) / **baseballr** (R) - Wrappers for multiple sources
3. **FanGraphs** - Advanced metrics, leaderboards, Statcast
4. **Baseball Reference** - Historical stats
5. **Statcast** (via Baseball Savant) - Pitch-level data
6. **SportsDataverse** (GitHub) - Multi-sport data tools

**Note**: Modern data (post-2000) most complete. Pitch-level Statcast data available from 2015+.

**Tag**: TECHNIQUE

---

## TOPIC 10: SHARP BETTOR METHODOLOGY

### [TECHNIQUE] How Sharps Actually Operate

**Source**: Multiple community sources, VSiN, Action Network

**Key Practices**:
1. **Line shopping across multiple books** - Always bet the best available price
2. **Timing**: Pros often wait until last minute (latest info, higher limits, don't tip hand)
3. **Focus on VALUE not winners** - "It's not about guessing right, it's about getting the best price"
4. **Specialization** - Deep knowledge in narrow markets beats broad surface knowledge
5. **Bankroll discipline** - Fixed 1-5% per wager, never chase losses
6. **Process over results** - Judge decisions by process quality, not short-term outcomes
7. **Use Pinnacle as benchmark** - 2-3% vig, sharpest lines in industry

**Steam Moves as Signal**:
- Sudden market-wide line shift from heavy one-sided money
- MLB lines move 5-10 cents at a time (small but significant)
- Reverse line movement (70%+ public on one side, line moves other way) = sharp signal

**Tag**: TECHNIQUE

---

## TOPIC 11: Pinnacle as Benchmark

### [TECHNIQUE] Using Pinnacle No-Vig Lines

**Source**: pinnacleoddsdropper.com, multiple analysis sites

**Method**: Strip Pinnacle's 2-3% margin to get "true" fair probability. If another book offers higher odds than Pinnacle's vig-free line, you have a value bet.

**Limitation tested**: One study found Pinnacle accurate 30/58 times vs DraftKings (51.7%) -- below the 52.4% needed to break even. However, study only checked once daily; more frequent sampling may reveal better opportunities.

**Props Caveat**: Pinnacle doesn't offer all props markets, and where they do, limits may be low enough that lines aren't fully efficient.

**Tag**: TECHNIQUE (with caveats for props)

---

## SYNTHESIS: KEY IMPLICATIONS FOR SPORTS EDGE

### What the Community Validates in Our Approach:
1. **K props market is correct target** - Low efficiency, beatable with good model
2. **Paper betting first** - Universal recommendation, 300+ bets minimum
3. **Simple features dominate** - K%, opponent K%, projected IP > complex ML
4. **Fractional Kelly sizing** - Quarter Kelly given our uncertainty level
5. **Calibration focus** - Our model should output true probabilities

### What the Community Challenges:
1. **SwStr%/whiff rate** may not add much over raw K rate for prediction
2. **CLV is NOT a valid metric for our prop bets** - Must use profit/loss directly
3. **Complex models often underperform simple ones** - Watch for overengineering
4. **Brier score paradox** - Better calibration metrics don't always = more profit

### Critical Unknowns the Community Can't Resolve:
1. What's the realistic edge in K props? (2%? 5%? 10%?)
2. How quickly do books adjust to sustained sharp action on props?
3. Is there enough volume to scale (bet limits on props are low)?
4. Does automated execution actually capture the model's theoretical edge?

### Recommended Model Architecture (from community wisdom):
1. **Primary features**: K%, opponent K% (by handedness), projected IP
2. **Secondary features**: Recent 3-start form, CSW rate, umpire, park factor
3. **Tertiary features**: Weather (cold/warm), game script projection, TTO effect
4. **Distribution**: Negative binomial for any totals work
5. **Calibration**: Isotonic regression or beta calibration
6. **Sizing**: Quarter Kelly with minimum 300 bet paper validation
7. **Evaluation**: Actual profit/loss, NOT CLV (invalid for props)

---

## SOURCES

### Academic Papers
- [Walsh & Joshi (2024) - Calibration vs Accuracy](https://arxiv.org/abs/2303.06021)
- [Morgan Allen & Savala (2025) - MLB Win Prediction](https://arxiv.org/abs/2511.02815)
- [Systematic Review of ML in Sports Betting (2024)](https://arxiv.org/html/2410.21484v1)

### Analytical Sites
- [Unabated - Getting Precise About CLV](https://unabated.com/articles/getting-precise-about-closing-line-value)
- [Beat the Bookie Blog - Scoring Functions vs Profit](https://beatthebookie.blog/2022/03/29/scoring-functions-vs-betting-profit-measuring-the-performance-of-a-football-betting-model/)
- [FanGraphs Community - Negative Binomial](https://community.fangraphs.com/run-distribution-using-the-negative-binomial-distribution/)
- [Baseball Prospectus - SwStr% vs K Prediction](https://www.baseballprospectus.com/news/article/12050/ahead-in-the-count-predicting-strikeouts-with-whiff-and-swing-rates/)
- [Conor Durkin - Liquidity in Betting Markets](https://conordurkin.com/liquidity-in-sports-betting-markets/)
- [sports-ai.dev - CLV and AI Model Performance](https://www.sports-ai.dev/blog/closing-line-value-and-ai-model-performance)
- [sports-ai.dev - Model Calibration](https://www.sports-ai.dev/blog/ai-model-calibration-brier-score)

### Practitioner Stories
- [Quant Galore - I Almost Got Rich (MLB algorithm)](https://medium.com/the-financial-journal/i-almost-got-rich-from-a-sports-betting-algorithm-b3e2bf2b3780)
- [David Katzman - Lessons from Betting Model](https://medium.com/@dkatzman_3920/important-insights-learned-from-attempting-to-perfect-a-sports-betting-model-e00d4cb8d0f8)
- [SportsInsights - Dangers of Overfitting](https://www.sportsinsights.com/blog/dangers-overfitting-sports-betting-systems/)

### Data & Distribution
- [Sean Dolinar - MLB Run Distribution NB](https://stats.seandolinar.com/mlb-run-distribution-neg-binomial/)
- [Walk Like a Sabermetrician - Negative Binomial](http://walksaber.blogspot.com/2012/06/on-run-distributions-pt-2.html)
- [MLBProps - Third Time Through Order](https://mlbprops.com/third-time-through-order-penalty-pitcher-prop-betting-mlb.html)

### Kelly Criterion & Sizing
- [Matthew Downey - Fractional Kelly Simulations](https://matthewdowney.github.io/uncertainty-kelly-criterion-optimal-bet-size.html)
- [Harry Crane - Two Arguments for Fractional Kelly](https://harrycrane.substack.com/p/two-arguments-for-fractional-kelly)

### Betting Tools & Methodology
- [Betstamp - MLB Betting Strategy 2025](https://betstamp.com/education/mlb-betting-strategy-guide)
- [HeatCheck HQ - MLB Weather Betting Guide](https://heatcheckhq.io/blog/mlb-weather-betting-guide)
- [Fast Break Bets - Clutchwrap Supreme MLB Model](https://www.fastbreakbets.com/mlb-picks/mlb-betting-model-clutchwrap-supreme/)

---

## RESEARCH LIMITATIONS

1. **Reddit direct access failed** - Web search tools cannot reliably surface specific Reddit thread content. The research pivoted to community-adjacent sources (SBR forums, Medium posts by practitioners, academic papers) that cover the same ground.

2. **No verified track records found** - Could not locate Reddit users with publicly verified 1000+ bet profitable records for K props specifically.

3. **Props-specific research is thin** - Most academic work focuses on sides/totals. Props modeling research is largely proprietary (held by sharp bettors/syndicates who don't share).

4. **Recency** - Some statistical analyses use pre-2020 data. Post-COVID MLB changes (rule changes, universal DH, pitch clock) may have shifted some relationships.

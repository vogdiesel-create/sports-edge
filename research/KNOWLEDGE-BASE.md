# Sports Edge Knowledge Base
**Pre-digested insights from all research sources**
**Last Updated**: 2026-04-20
**Sources**: 19 YouTube transcripts (91K words), 9 research papers, r/algobetting archive, academic papers
**Credibility**: All claims now audited. Tags: [VERIFIED] [PLAUSIBLE] [UNVERIFIED] -- see SOURCE-AUDIT.md for full analysis

---

## CREDIBILITY WARNING

Every single source in this document monetizes sports betting content -- courses, platforms, subscriptions, or media deals. Even the most legitimate (Rufus Peabody 9.5/10, Spanky 9/10, Captain Jack 8/10) profit from making betting seem learnable. Fewer than 3% of bettors are profitable long-term. Claims tagged [UNVERIFIED] should be validated against our own data before acting on them.

**Source tiers**: Tier 1 (verified pros): Peabody, Spanky, Captain Jack. Tier 2 (legit analysts): Kerner, Zerillo, Outlier. Tier 3 (educational/unverified): Wagered On Tilt, OddsJam. Tier 4 (entertainment): Betting Analyst Tony.

Full audit: /home/aiciv/sports-edge/research/youtube/SOURCE-AUDIT.md

---

## THE BIG PICTURE: What Separates Winners from Losers

### From the Sharpest Bettors (Rufus Peabody, Captain Jack, Sean Zerillo)

1. **CLV is the ONLY metric that matters FOR GAME LINES** -- [VERIFIED] If you consistently beat the closing line at Pinnacle, you WILL profit long-term. BUT: CLV is meaningless for props (see warning below).

2. **"Don't predict outcomes, predict the market"** -- Your model doesn't need to know who wins. It needs to know when the line is wrong. Subtle but critical difference.

3. **"Be early, not just right"** -- Opening lines have the most inefficiency. By game time, sharps have corrected most errors. Bet at morning open for totals/props.

4. **One deep model beats many shallow models** -- Don't spread across 10 sports with mediocre models. Go deep on one market until it's printing money, then expand.

5. **Bankroll management is 50% of the game** -- Even a profitable model goes bankrupt with bad sizing. Quarter Kelly until you have 500+ graded bets.

6. **Calibration >> Accuracy for profit** -- [VERIFIED, Walsh & Joshi 2024, peer-reviewed] Calibration-based model selection: +34.69% ROI. Accuracy-based: -35.17%. A model that says "60% chance" and IS right 60% of the time beats one that's "correct" more often but miscalibrated. Optimize for Brier score/ECE, NOT accuracy.

7. **Simple models often beat complex ones** -- [VERIFIED, multiple sources] More features and ML complexity (XGBoost, Random Forest) frequently UNDERPERFORM simple regression when given noisy sports data. K%, opponent K%, projected IP may be all you need. Systems with 10+ filters are almost certainly overfit.

8. **Weekend day games in MLB have exploitable inefficiency** -- [VERIFIED, Simon 2024, Management Science] Forecasts at game start are WORSE than 90 minutes earlier for weekend day games. Contrarian strategy: 10-13% ROI. Lines exhibit overreaction patterns.

---

## MODEL-SPECIFIC INSIGHTS

### MLB Totals (Our Strongest Edge)

**Current: UNDER totals 5-12% edge = 23.9% ROI (small sample)**

Key improvements identified:
- **Overdispersion parameter too low**: Our `MLB_OVERDISPERSION = 1.8`. [UNVERIFIED] The 2.1-2.2 figure CANNOT be traced to any source -- no FanGraphs post, no academic paper. MUST validate empirically against actual run distributions before changing.
- **Bullpen fatigue**: Track pen innings over trailing 3 days. 5+ innings in last 2 days = add 0.2-0.4 runs to scoring allowance.
- **Umpire data**: Different umps have measurably different strike zones. Add ump identity as a feature.
- **Game environment**: Day games after night games, altitude, humidity all affect run scoring.

**Action items:**
1. Change MLB_OVERDISPERSION to 2.1
2. Verify bullpen fatigue weighting in ensemble
3. Add umpire features when data available

### K Props (OVERs DISABLED Apr 20)

**Model K picks (live Apr 19): 5W-8L, -$73. UNDERs: 5-5 (-$13), OVERs: 0-3 (-$60) -- DISABLED**
**OddsTrader K picks: 93.9% WR (31/33), +$585 -- BEST EDGE IN ENTIRE SYSTEM**

Key improvements from Zerillo, Kerner, + academic research:
- **Putaway rate vs whiff rate divergence** (from Kerner, Action Network): [PLAUSIBLE] Both metrics are real Statcast data. The "divergence as PRIMARY trigger" framing may be our interpretation -- couldn't verify this specific claim outside our transcript notes. Logic is sound but treat as one input among many, not a silver bullet.
- **Model PULL POINT, not just innings** (from Kerner): Project how many batters pitcher faces and WHERE in the lineup they get pulled. Manager hook tendencies are the single biggest swing factor for K props. If pulled before facing bottom-of-order high-K batters 3rd time through, under has massive hidden value.
- **Times-through-the-order K degradation** (Kerner, Captain Jack): K rate drops significantly 2nd and especially 3rd time through. Model per-pitcher, not league average. This is THE fundamental reason K prop unders are +EV.
- **SwStr% is THE predictor**: [VERIFIED] Swinging strike rate correlates with K% at R=0.81. Podhorzer's xK% formula (R2=0.892) uses SwStr% as dominant input.
- **CSW% (Called Strikes + Whiffs)**: More comprehensive than SwStr% alone. Elite K pitchers: CSW% above 30%. Forum consensus says this is a better single metric.
- **In-Zone Whiff Rate (IZWR)**: Percentage of in-zone swings that miss. Another validated K predictor from forum research.
- **CONTRADICTION: Granular pitch metrics may add NOTHING over raw K rate** (Baseball Prospectus): When controlling for prior K rate, SwStr% adds <0.1% to prediction R-squared (0.6118 vs 0.6110). For PREDICTION, prior K% dominates everything. SwStr% helps detect within-season form but is "virtually useless" for prediction once K% is included. Don't over-engineer with Statcast data when K% does 99% of the work.
- **Platoon splits matter**: FanGraphs matchup formula: `Expected K% = (B * P) / (0.84 * B * P + 0.16)` where B=batter K% vs handedness, P=pitcher K% vs handedness.
- **Pitch-arsenal-vs-lineup matchup** (Outlier, Kerner): Compute per-batter whiff rates against each specific pitch type the pitcher throws, weighted by usage. A lineup that crushes sinkers but can't hit curves changes the K projection when facing a curve-heavy pitcher.
- **Our OVER bias is known (+0.58)**: Model overestimates K totals because it doesn't model pull-point dynamics or TTO degradation.
- **Only bet two-way over/under props**: Two-way holds ~4% vs multi-way exact-outcome at ~14%. Massive vig difference.

**Action items (P0 = highest priority):**
1. P0: Replace Poisson with Negative Binomial for K distribution (overdispersion ~1.3-1.5x)
2. P0: Implement log5 matchup formula: `K% = B * P / (0.84 * B * P + 0.16)`
3. P0: Add TTO adjustment (1st TTO: K rate ~110%, 2nd: ~100%, 3rd: ~85%)
4. P0: K bias correction 0.91x APPLIED (Apr 20)
5. P0: K OVERs DISABLED (Apr 20, 0-3 live)
6. P1: Add xK% features (L/Str, S/Str, F/Str -- R-squared 0.892)
7. P1: Add umpire K-rate factor (from UmpScorecards)
8. P1: Apply platoon-adjusted K% per lineup slot
9. P2: Model pull point / batters faced (manager hook tendencies)
10. P2: Add Stuff+ for pitchers with <3 starts (small sample stabilizer)

### Batter Props (EMERGENCY FIX APPLIED Apr 20)

**LIVE RESULTS CATASTROPHIC**: 404 picks, 80W-324L (19.8% WR), -$2,721
- HR: 0/29 (0% WR) -- DISABLED
- SB: 0/17 (0% WR) -- DISABLED
- Runs: 7/48 (15% WR) -- DISABLED
- RBI: 16/77 (21% WR) -- 0.50x calibration multiplier
- TB: 42/184 (23% WR) -- 0.55x calibration multiplier
- Hits: 15/49 (31% WR) -- 0.65x calibration multiplier

**ROOT CAUSE IDENTIFIED** [VERIFIED, fg-negbin-runs.txt, cmp-bivariate-2024.txt]:
Poisson distribution assumes variance = mean. MLB batter outcomes are overdispersed (variance ~2x mean). This makes Poisson systematically overestimate P(X >= threshold), especially for rare events (HR, SB). Fix: replace with zero-inflated Negative Binomial.

**OddsTrader batter props ARE profitable**: 872 graded OddsTrader picks = +$125 raw, +$1,734 after filtering out NHL goals and sub-10% EV. Our MODEL is broken, but the MARKET has exploitable inefficiency.

**Action items:**
1. Replace Poisson with Negative Binomial for all batter prop probabilities
2. Add zero-inflation parameter from empirical 0-outcome rates
3. Keep heavy ad-hoc calibration until NegBin is validated
4. Focus on OddsTrader cross-book edge (93% WR on K props, 92% on pitching hits allowed)

### Moneyline (DISABLED -- 2W-6L, -$468)

- Live results: 0-4 vs +4.1% backtest. Paused.
- Multiple YouTube sources confirm: ML is the MOST efficient market, hardest to beat
- Captain Jack: "Totals and props are where recreational bettors make their edge"
- Re-enable only after totals CLV validation passes 50+ bets

---

## KELLY CRITERION & SIZING

### Academic Consensus (3 papers agree)

- **Full Kelly = bankruptcy in 100% of realistic simulations** (Wharton 2023)
- **Quarter Kelly (0.25x)** recommended during validation phase
- **Half Kelly (0.50x)** after 500+ graded bets with confirmed positive CLV
- **Minimum edge threshold**: Only bet when estimated edge > 5-7% of implied probability
- **Modified Kelly** (Chu/Wu/Swartz): When probability is estimated (not known), Kelly fraction must shrink

### Practical Rules
- 1-5% of bankroll per position (community standard)
- r/algobetting community uses 15% fractional Kelly
- Correlated bets (same game): reduce each to 60-70% of individual Kelly
- **Never** withdraw winnings until account gets limited (don't flag yourself)

---

## CLV (CLOSING LINE VALUE) -- The North Star

### CRITICAL: CLV Is NOT Reliable for Props (from Spanky/Unabated)
CLV is only valid in markets with: (1) sharp money shaping prices, (2) sufficient liquidity, (3) no unknowable pre-game information. **K props fail all three tests.** No book is truly sharp on props. Our 77% WR when beating closing line on props may be partially illusory -- prop line moves are driven by touts and square action, not sharp price discovery.

**For props**: Use ROI and calibration as primary evaluation metrics, not CLV.
**For game totals**: CLV is meaningful where Pinnacle-equivalent sharp books exist.
**Separate CLV reporting by market type in the paper ledger.**

### What Our Data Shows
- 77% win rate when beating closing line vs 45% when not (game totals -- more reliable)
- Current CLV: -0.38% (needs to go positive)
- GATE: Need 50+ bets with positive CLV before scaling

### How to Improve CLV
1. **Bet earlier**: Totals and K props at morning open (6-12h before game)
2. **Track bet timing**: Log placement time in paper_ledger.json
3. **Build CLV prediction model**: After 200+ bets, regress actual CLV on: edge size, time of placement, book, market type
4. **Reverse line movement** = strongest sharp signal: line moves opposite to public betting %

### CLV by Market Efficiency (most to least efficient)
1. NFL sides/totals (hardest to beat)
2. NBA game lines
3. MLB moneylines
4. MLB totals (our sweet spot)
5. K props
6. Player props (least efficient -- most opportunity)

---

## LINE TIMING -- When to Bet

| Bet Type | Best Window | Why |
|----------|------------|-----|
| MLB Totals | Morning open, before lineup release | Sharp money moves totals early |
| K Props | Morning, 6-12h before game | Props least efficient, lines don't sharpen fast |
| Moneyline | After lineup release, before sharp wave | Need confirmed lineup first |
| Batter Props | Morning open | Same as K props -- least efficient market |

- MLB lines open: day before or morning of
- Lineup release: 3-4h before first pitch
- Sharp money enters: within first hour of posting

---

## BOOK MANAGEMENT

### From Pro Bettors (Captain Jack, Spanky, Rufus Peabody)
- **Pinnacle** = the truth. Their closing lines are the benchmark.
- **FanDuel** = sharpest retail book for props. Openers are garbage, sharpen near game time.
- **DraftKings/BetMGM** = softer on props. Bet deviations from FD lines here.
- **Getting limited is inevitable** -- it's a sign you're winning, not a problem to solve
- Bet enough to look recreational: mix in some parlays, don't always bet the same market
- Don't withdraw until limited
- Use multiple books: Pinnacle/Circa (non-limiting) for volume, retail for soft lines

---

## WHAT YOUTUBE'S TOP BETTORS SAY ABOUT MLB SPECIFICALLY

### Captain Jack (professional bettor, MLB specialist)
- Baseball is "the most modelable sport" due to pitcher-dependent outcomes
- Totals are where the edge is, not moneylines
- Weather data is underrated by most modelers
- Park factors compound with weather (wind + altitude = massive run variance)
- Bullpen management is the #1 overlooked factor

### Sean Kerner (Action Network, MLB K prop modeler -- MOST VALUABLE SOURCE)
- Simulates each pitcher start 10,000 times by computing per-batter K probability for every PA
- Times-through-order degradation + expected pull point = primary edge drivers
- Putaway rate vs whiff rate divergence is his #1 bet trigger
- Manager hook tendencies are the single biggest swing factor
- "A lot of times where the edge comes from" is modeling exactly which batters get faced 2x vs 3x

### Sean Zerillo (Action Network, MLB K prop expert)
- K props are the most modelable prop market because pitcher controls the outcome
- SwStr% dominates all other features for K prediction
- Season-to-date K/9 is a trap for early-season (use career SwStr% with regression)
- L/R splits are essential for accurate K totals

### Rufus Peabody (legendary sharp, $70K MLB seasons)
- "I made $70K in a single MLB season" -- primarily on totals and F5 lines
- Prediction markets (Polymarket, Kalshi) offer even softer lines than sportsbooks in 2026
- Model evaluation should optimize log-likelihood, not ROI
- **Year-to-year model stability matters more than peak performance**

---

## r/algobetting COMMUNITY WISDOM

1. **Data quality is 80% of the battle** -- player name matching between sources is a huge pain
2. **"USE BACKTESTS TO VALIDATE, NOT OPTIMIZE"** -- optimize for statistical properties (log-loss, MAE), not ROI
3. You need hundreds to thousands of bets to be sure your system works
4. **Build infra for speed** -- try many ideas fast, reject fast
5. "You will not beat the market on every line, find WHERE you're more accurate"
6. Quality over quantity of features
7. Baseball "has been so beaten by statisticians that it offers no value" -- COUNTER: our UNDER filter proves otherwise
8. High-scoring sports (basketball, handball) are more predictable, but less profitable per bet
9. **Don't p-hack** -- you'll overfit to weird patterns that don't repeat
10. Playoff/postseason requires completely different models (don't use regular season model)

---

## MISTAKES WE MIGHT BE MAKING (from transcript analysis)

1. **Using CLV to evaluate prop bets** -- unreliable, use ROI and calibration instead
2. **K overestimation (+0.58)** -- caused by not modeling pull-point dynamics or TTO degradation
3. **142 features without causal audit** -- Captain Jack: every feature needs a hypothesis for WHY it affects outcome. Data-mined features without causal stories will eventually fail.
4. **Not modeling K distribution shape** -- two pitchers with identical median K projections can have very different edge profiles based on lineup composition. Need full probability distributions.
5. **Ignoring market hold %** -- betting multi-way props at 14% hold destroys edge. Only bet over/under (4% hold).
6. **Not exploiting early-season window** -- April-May is when markets are most inefficient for player props. Bet more aggressively then.

---

## PRIORITY ACTION LIST (Ordered by Impact/Effort)

### Quick Wins (config changes, no new data needed)
1. [BLOCKED] Validate MLB_OVERDISPERSION empirically against actual data BEFORE changing (2.1-2.2 source is unverified)
2. Switch to quarter Kelly (0.25x) sizing
3. Log bet placement time in paper_ledger.json
4. Disable K prop OVERs (stop the bleeding: -$164)
5. Separate CLV tracking by market type (game totals vs props)

### K Prop Model Overhaul (P0 -- from Kerner analysis)
6. Add putaway rate vs whiff rate delta per pitch type
7. Model expected batters faced + pull point (manager hook tendencies)
8. Add times-through-order K rate per pitcher (1st/2nd/3rd)
9. Add pitcher SwStr% as primary feature
10. Apply platoon-adjusted K% per lineup slot

### Medium Effort (new data sources)
11. Add pitch-type-vs-batter whiff rate matchup
12. Build batter prop grading system (872 ungraded bets)
13. Verify bullpen fatigue weighting in ensemble
14. Audit all 142 features for causal plausibility
15. De-vig Pinnacle as truth benchmark for game totals

### Larger Projects
16. Build CLV prediction meta-model (after 200+ bets)
17. Add umpire features to totals model
18. Implement Conway-Maxwell-Poisson for dynamic dispersion (replaces fixed 2.1)
19. Multi-book line comparison for soft-line detection
20. Explore correlated betting (K over + opposing batter unders)

---

## CROSS-SPORT EXPANSION (from academic research)

| Sport | Model Type | Beatable? | Key Insight |
|-------|-----------|-----------|-------------|
| MLB totals/props | NegBin/CMP | YES | Least efficient prop market, our sweet spot |
| NHL | Poisson | YES | JQAS 2016 demonstrated profitable strategies. Poisson works (unlike MLB). Model manpower situations. |
| NBA | XGBoost+SHAP | HARD | Most modeled sport. Edge exists in player props (minutes projection is key) |
| NFL | Simple models | HARD | Most efficient market. Simple Naive Bayes beat spread at 67.5%. Weather critical for outdoor games. |
| Tennis | Weighted Elo | YES | 3.56% ROI over 8 years (peer-reviewed). Surface-adjusted Elo with scoreline weighting. Worth exploring. |
| Soccer | xG aggregation | MAYBE | Most advanced analytics field. Model shot-by-shot xG, aggregate to match. |
| College sports | Various | YES | More games = more pricing errors (Spanky prefers college markets) |

**Expansion priority**: NHL first (Poisson works, market less efficient than NFL/NBA), then tennis (simple Elo = proven 3.5% ROI), then NBA props.

---

## SCALABILITY WALL (brutal math)

Even with a perfect prop model:
- $500 max bet at 5% edge = $25 EV per bet
- $70K season = ~2,800 bets at $500 average
- That's 17 bets/day across 162 games
- Getting limited kills volume fast

**Solutions**:
1. Translate prop insights into game totals/sides where limits are $5K-$50K+
2. Multi-book accounts (5+ books minimum)
3. DFS/Prize Picks correlation plays (different limit structure)
4. Scale bankroll (quarter Kelly means larger bets with larger bankroll)

---

## STILL TO REVIEW

47 more YouTube videos queued for transcript pull (rate-limited, will continue tomorrow).

Key channels/creators still to cover:
- More Captain Jack deep dives
- Unabated Line (analytics platform)
- Sports Analytics Group (academic approaches)
- More Rufus Peabody prediction market content
- Bet Labs / Sports Insights methodology videos

---

## REALITY CHECKS (from forum research -- hard truths)

1. **200 bets tells you NOTHING** -- 54% win rate on 200 bets is statistically indistinguishable from coin-flipping. Need 1000+ for real confidence. Our 50-bet gate is fine for CLV direction but not for model validation.
2. **If backtest shows 15%+ ROI, you're probably overfitting** -- legitimate edges are single-digit ROI (3-7%). Our 23.9% ROI on UNDER filters is either a very small sample or we're fooling ourselves.
3. **Prop limits cap revenue** -- even with perfect 5% edge, $500 max bet = $25 EV per bet. $70K season on props alone would need ~2,800 bets at $500. That's 17/day across 162 games.
4. **Our model expansion (109 to 3641 training games) needs walk-forward validation** -- did accuracy improve because we have more data, or because we fit more noise?
5. **Red flags for overfitting**: smooth equity curve, >10% ROI, using season-end stats mid-season, testing thousands of parameter combos without correction.
6. **Characteristics of REAL signal**: has a mechanistic explanation, robust across parameter variations, shows natural decay over time, single-digit ROI.
7. **Add a top-down layer** -- compare model output to Pinnacle sharp line. If our model says over 5.5 K but Pinnacle already prices it there efficiently, there may be no edge even if we're "right."
8. **Keep model methodology PRIVATE** -- shared edges get arbitraged away. Our proprietary model is our advantage.
9. **Everyone gets limited eventually** -- plan for it. 5+ book accounts, gradual size increases, mix in recreational-looking bets.

---

*This file is the single source of truth for what we know. Updated as new transcripts and research are analyzed.*
*Last research wave: 9 agents running Apr 20 2026*

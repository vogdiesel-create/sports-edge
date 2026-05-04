# YouTube Transcript Insights Report: Sports Edge Model Improvements

**Date**: 2026-04-20
**Author**: Researcher Agent (Timosha)
**Sources**: 10 YouTube transcripts from professional sports bettors and analysts
**Purpose**: Extract actionable improvements for Sports Edge MLB betting model

---

## Executive Summary

Analysis of 10 transcripts from professional bettors (Sean Kerner, Captain Jack Andrews, Spanky/Unabated, OddsJam analysts, and others) reveals several specific improvements for our model. The highest-impact findings are: (1) our K prop model needs per-batter simulation with pull-point modeling, not aggregate K rates; (2) CLV is unreliable for evaluating prop bets; (3) putaway rate vs whiff rate divergence is a primary sharp bettor edge; (4) our feature set needs a causal-plausibility audit; and (5) we should only target two-way over/under props (4% hold) and avoid multi-way markets (14% hold).

---

## Top 10 Actionable Improvements (Ranked by Expected Impact)

### 1. ADD PUTAWAY RATE vs WHIFF RATE DIVERGENCE (HIGH IMPACT)
**Source**: Sean Kerner (Action Network K prop modeler)
**What**: Compare a pitcher's whiff rates on each pitch type to their actual putaway (2-strike conversion) rates. Divergence = luck that will regress.
**Why**: Kerner explicitly says this was his primary bet trigger last season. A pitcher with high whiff rates but low putaway rates is due for K rate improvement (bet over). The reverse = bet under.
**How**: Pull Statcast whiff% and putaway% per pitch type. Compute delta. Use as feature in K prop model. Positive delta (whiff > putaway) = unlucky pitcher, K rate should increase.

### 2. MODEL PULL POINT AND BATTERS FACED (HIGH IMPACT)
**Source**: Sean Kerner
**What**: Project how many batters each pitcher will face (not just innings), and critically, WHERE in the lineup they get pulled. If they get pulled before facing high-K batters in the 6-7-8-9 slots the third time through, the under has massive hidden value.
**Why**: Kerner says this is "a lot of times where the edge comes from" on his under/over calls. Manager tendencies on when to pull a pitcher are the single biggest swing factor for K props.
**How**: Build pitcher-specific expected batters-faced model using: historical pitch counts, recent workload, manager tendencies (hook speed), game context. Map pull point to lineup order to determine which batters get faced 2x vs 3x.

### 3. ADD TIMES-THROUGH-THE-ORDER K DEGRADATION (HIGH IMPACT)
**Source**: Sean Kerner, Captain Jack
**What**: K rate drops significantly 2nd and especially 3rd time through the order. Model this per-pitcher, not as a league average.
**Why**: First time through = pitcher's biggest K edge. Second time = moderate drop. Third time = significant drop. This is the fundamental reason K prop unders are +EV (public doesn't account for this degradation).
**How**: Compute per-pitcher K rate by TTO (1st, 2nd, 3rd) from Statcast. Weight K projection by expected number of batters faced in each TTO bucket.

### 4. STOP USING CLV AS PRIMARY PROP EVALUATION METRIC (HIGH IMPACT)
**Source**: Spanky/Unabated "Using CLV Wrong"
**What**: CLV is only meaningful in markets with sharp money, high liquidity, and no unknowable pre-game information. K props fail all three tests. No book is truly sharp on props.
**Why**: Our 77% WR when beating closing line on props may be partially illusory -- prop line moves are driven by touts and square action, not sharp price discovery. We could be measuring noise.
**How**: Track ROI and calibration as primary metrics for props. Use CLV only for game totals where Pinnacle-equivalent sharp books exist. Separate CLV reporting by market type in the paper ledger.

### 5. AUDIT FEATURES FOR CAUSAL PLAUSIBILITY (MEDIUM-HIGH IMPACT)
**Source**: Captain Jack Andrews
**What**: Every feature in our 142-feature model must have a causal hypothesis for WHY it affects the outcome. Features discovered through data mining without a theory will eventually fail.
**Why**: Captain Jack: "if you just jump into the data and start looking around for patterns without any inkling of what you're looking for, you might stumble across things that look valuable but are random."
**How**: Review all 142 features. For each, write one sentence explaining the causal mechanism. Any feature without a clear causal story should be tested for removal.

### 6. DE-VIG PINNACLE AS TRUTH BENCHMARK FOR GAME TOTALS (MEDIUM IMPACT)
**Source**: OddsJam "Pinnacle Is Truth", Spanky CLV video
**What**: Pinnacle's no-vig line is the closest thing to true probability in sports betting. De-vig their lines to compute fair odds, then measure our edge against that.
**Why**: Instead of comparing to soft book closing lines (noisy), compare to Pinnacle no-vig. This gives us a cleaner measure of true edge.
**How**: Acquire Pinnacle closing lines for MLB totals. De-vig using odds-ratio method. Compute: our model probability minus Pinnacle fair probability = true edge.

### 7. TARGET EARLY-SEASON WINDOW AGGRESSIVELY (MEDIUM IMPACT)
**Source**: Captain Jack, Sean Kerner, Outlier researcher
**What**: The first 2-4 weeks of the MLB season is the highest-edge window for player props. Markets haven't calibrated to current-year form.
**Why**: Kerner says he is "more cautious on opening start" but "ready to pounce on second start." The market is slowest to adjust early-season.
**How**: Increase position sizing (within 1-2% cap) during April-May for K props. Target pitchers whose spring metrics diverge from market-implied projection.

### 8. ADD PITCH-ARSENAL-vs-LINEUP MATCHUP ANALYSIS (MEDIUM IMPACT)
**Source**: Outlier K Prop Research, Sean Kerner
**What**: For each K prop, compute how the opposing lineup performs specifically against each pitch type the pitcher throws, weighted by usage.
**Why**: If a lineup crushes sinkers but can't hit curveballs, and the pitcher throws 40% curveballs, the K projection changes significantly.
**How**: From Statcast, get per-batter whiff rates by pitch type. Cross-reference with pitcher's pitch mix. Compute weighted expected whiff rate.

### 9. ONLY BET TWO-WAY OVER/UNDER PROPS (MEDIUM IMPACT)
**Source**: Captain Jack "Betting Baseball"
**What**: Two-way prop markets (over/under) carry ~4% theoretical hold. Multi-way exact-outcome markets carry ~14% hold.
**Why**: Betting into 14% hold markets means you need 14% edge just to break even.
**How**: Filter bet generation to only produce over/under prop picks. Avoid exact strikeout count or other multi-way markets.

### 10. EXPLORE CORRELATED BETTING (LOWER IMPACT BUT +EV)
**Source**: $70K MLB Season (Alex/OddsJam)
**What**: When betting a pitcher K over, simultaneously look at opposing batter prop unders (hits, total bases). These are positively correlated.
**Why**: If a pitcher is dealing, opposing batters go under. Betting both captures correlation premium.
**How**: When our model signals K over for a pitcher, automatically generate corresponding under signals for opposing lineup batters.

---

## Specific Features to Add

| Feature/Technique | Source | Priority |
|---|---|---|
| Putaway rate - whiff rate delta per pitch type | Kerner | P0 |
| Expected batters faced (not innings) | Kerner, Outlier | P0 |
| Pull-point modeling (which lineup slot pitcher exits at) | Kerner | P0 |
| Times-through-order K rate per pitcher (1st/2nd/3rd) | Kerner | P0 |
| Pitch-type-vs-batter whiff rate matchup | Outlier, Kerner | P1 |
| Pinnacle no-vig line as truth benchmark | OddsJam, Spanky | P1 |
| Manager hook tendencies (hook speed metric) | Kerner | P1 |
| Umpire called strike rate | Kerner | P2 |
| Barometric pressure (may still have signal for props) | Captain Jack | P2 |
| Bullpen fatigue for correlated game total bets | Captain Jack | P2 |

---

## Mistakes We Might Be Making

1. **Using CLV to evaluate prop bets**: CLV is unreliable for props. No sharp book prices props efficiently. Use ROI and calibration instead.
2. **Overestimating Ks by +0.58**: Aligns with Kerner's insight that K rate drops through the order and pitchers get pulled before facing bottom-of-order high-K batters. Our model doesn't properly model pull-point dynamics.
3. **142 features without causal audit**: Some may be data-mined noise. Every feature needs a hypothesis.
4. **Not modeling distribution shape**: Two pitchers with identical median K projections can have very different edge profiles based on lineup composition. We should compute full probability distributions.
5. **Ignoring market hold %**: Betting into multi-way props at 14% hold destroys edge. Exclusively target over/under (two-way) props at ~4% hold.
6. **Not exploiting early-season edge window**: April-May is when markets are most inefficient for player props.

---

## Books Recommended by Experts

- "The Book" by Tom Tango, Mitchel Lichtman, Andrew Dolphin -- baseball probability fundamentals
- "The Physics of Baseball" by Robert Adair -- weather/park effects
- "Trading Bases" by Joe Peta -- player valuation approach to MLB betting
- "Analyzing Baseball with R" (2nd Ed) -- Statcast data analysis
- "Introduction to Empirical Bayes" -- Bayesian analysis applied to baseball

---

## Sources (Videos Analyzed)

1. Sean Zerillo & Sean Kerner - MLB K Prop Model (Action Network Payoff Pitch)
2. Captain Jack Andrews - Creating an Edge (Better IQ Course)
3. Wagered On Tilt - End to End Model Building
4. Spanky/Unabated - Using CLV Wrong
5. OddsJam - Pinnacle Is Truth (Sharp Sports Betting Math)
6. Outlier - K Prop Research Walkthrough
7. OddsJam Alex - $70K MLB Season Strategy
8. Captain Jack Andrews - Betting Baseball 2020
9. OddsJam Matt Modi - CLV Fundamentals
10. Tony/Betty - Pro Gambler Easiest Path

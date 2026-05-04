# Sports Edge V2 - Design Document

## What does world-class look like?

A world-class sports betting system doesn't just find pricing errors. It **understands the game better than the market does.** The best quant funds (Starlizard, Mustard, Priomha Capital) build proprietary models that generate their own probabilities from first principles, then bet when the market disagrees with THEM - not when one book disagrees with another book.

We should be building toward that.

---

## Where we are now (Level 1: Price Comparison)

We scrape Pinnacle odds, devig them, and find US books offering worse prices. This works (+30% ROI in backtest, +2.5% CLV live) but it's the floor, not the ceiling.

**Limitations:**
- We're borrowing Pinnacle's intelligence, not building our own
- When Pinnacle is wrong, we're wrong
- Edge disappears as books get sharper
- Can't bet props (no Pinnacle prop data)
- Zero predictive capability
- Anyone with the same data can copy this

---

## Where we should be going (Level 3: Predictive Model)

### The Vision

Build a model that generates its own game total probability distributions from raw data. When our model says over 6 is 58% likely but the market says 52%, we bet - whether Pinnacle agrees or not.

### Phase 1: Feature Engineering (weeks 1-2)

**NHL Totals Model - inputs:**
- Team offensive/defensive ratings (goals for/against per game, last 10/20/season)
- Goaltender stats (save %, GAA, starts/rest days)
- Special teams (PP%, PK%)
- Pace metrics (shots per game, Corsi, Fenwick)
- Head-to-head history
- Home/away splits
- Back-to-back/rest days
- Injury impact (missing top-6 forwards, top-4 D, starting goalie)
- Line movement (where is smart money going?)
- Time of season (regular season vs playoff race)

**MLB Totals Model - inputs:**
- Starting pitcher stats (ERA, FIP, xFIP, WHIP, K/9, BB/9)
- Bullpen fatigue/availability
- Team batting stats vs LHP/RHP
- Ballpark factors
- Weather (wind speed/direction, temperature, humidity)
- Umpire tendencies (zone size affects strikeouts/walks)
- Lineup confirmed vs projected

**Data sources (all free):**
- NHL: api-web.nhle.com (box scores, player stats, schedules)
- MLB: statsapi.mlb.com (everything), baseballsavant.mlb.com (Statcast)
- Weather: Open-Meteo API (free, no key)
- Odds: SBR scrape (Pinnacle + 10 books), Bovada API, OddsPapi (game lines)

### Phase 2: Model Architecture (weeks 2-4)

**Approach: Ensemble of specialized models**

1. **Base rate model** - Historical average total for matchup type (strong offense vs weak defense, etc.). Simple but surprisingly powerful baseline.

2. **Regression model** - XGBoost/LightGBM on engineered features. Predicts expected total with confidence interval.

3. **Poisson model** - Model each team's goals/runs as independent Poisson processes. More theoretically grounded for low-scoring sports (NHL). Allows simulation of exact score distributions.

4. **Market model** - What does the market (Pinnacle + consensus) say? This is our current Level 1 strategy embedded as one input, not the whole system.

5. **Ensemble** - Weight the models by recent accuracy. Market model gets high weight initially, decreases as our proprietary models prove themselves.

**Output:** For each game, a probability distribution over possible totals. Not just "over 6 is +EV" but "there's a 12% chance of 9+ goals that the market is pricing at 8%."

### Phase 3: Prop Model (weeks 4-8)

Once the game-level model works, extend to player props:

**NHL player props:**
- SOG model: player shot rate x ice time x opponent shot suppression
- Goals model: SOG model x shooting % x goalie save %
- Assists model: player assist rate x linemate goal probability
- Points = goals + assists (correlated, not independent)

**MLB player props:**
- Hits model: batting average vs pitcher type x park factor
- Strikeouts model: batter K% x pitcher K/9 x umpire zone
- RBI model: hit probability x runners on base probability (lineup dependent)
- Pitcher strikeouts: K/9 x opponent K% x game environment

**Key insight:** Player props are correlated with game totals. A high-total game means more counting stats for everyone. Our game model feeds the prop model.

### Phase 4: Edge Detection (ongoing)

Compare our model's probabilities to market odds. When we disagree by >3%, bet.

**Advantages over Level 1:**
- We find edges Pinnacle misses (they're sharp but not perfect)
- Works on props without Pinnacle data
- Gets smarter over time as we accumulate results
- Unique - can't be copied without our feature engineering
- Can model things the market is slow to price (injuries announced 30 min before game, weather changes, lineup surprises)

---

## What would a quant fund do?

1. **Hire domain experts** - We use public stats APIs + sports analytics research
2. **Build proprietary data pipelines** - We have this (SBR, Bovada, OddsPapi, NHL/MLB APIs)
3. **Feature engineer relentlessly** - This is where the alpha is. The model is 20% of the work, the features are 80%.
4. **Backtest rigorously** - Full season historical data, walk-forward validation, out-of-sample testing
5. **Track CLV religiously** - Already doing this
6. **Size positions mathematically** - Kelly criterion, already doing this
7. **Automate everything** - Already doing this
8. **Never stop improving** - This is the piece we were missing

---

## What are we NOT considering?

1. **Live/in-play betting** - Lines are softest pre-game. In-play is faster, more competitive. Skip for now.
2. **Futures/season markets** - Long tie-up of capital. Skip.
3. **Correlated parlays** - Some books misprice parlays of correlated outcomes. Worth exploring later.
4. **Market making** - Selling our model to others. Way later.
5. **Alternative data** - Social media sentiment, injury rumor tracking, travel/fatigue data. Level 4.

---

## Current Architecture (Level 2 - Live as of Apr 14 2026)

**The predictive model is the PRIMARY decision engine. Level 1 is confirmation only.**

Pipeline:
1. Dixon-Coles + Elo + rest days evaluates ALL games (NO XGBoost - it hurts ROI)
2. Model finds edges: model_prob vs market_implied_prob (3%+ threshold)
3. Level 1 (Pinnacle devig) runs as confirmation signal only
4. Tier assignment: S (model 5%+ AND L1), A (model 5%+), B (model 3-5% AND L1)
5. No C tier - L1 alone does NOT generate picks
6. Deduplicated: 1 bet per game at best available odds
7. Quarter-Kelly sizing by tier
8. CLV tracking: Pinnacle closing lines captured for every bet

**Key change from Level 1**: Model generates ALL picks. Pinnacle just boosts confidence.

**Backtest discrepancy RESOLVED (Apr 14 2026):**
- Design doc claimed +4.19% ROI (DC + Elo + rest days) -- CORRECT, this is the live config
- latest_report.txt showed +1.80% ROI -- this was from a different run (DC + XGBoost) that overwrote the report file
- Report regenerated from correct backtest run. Single source of truth established.

---

## Immediate Next Steps

1. **Accumulate Level 2 paper trades** - Target 200 graded bets for statistical significance.
2. **Auto-grader** - DONE. Fetches NHL/MLB final scores, grades bets automatically.
3. **CLV tracking** - DONE. Captures Pinnacle closing lines, calculates CLV per bet.
4. **Investigate declining ROI** - +6.02% -> +3.91% -> +2.45% across 3 seasons. Still profitable but trending down.
5. **MLB backtest** - Required before re-enabling MLB model (currently disabled).
6. **Calibration fix** - Model overconfident at extremes (27% predicted -> 43% actual).

---

## Success Metrics

- **Level 1 (current):** +2% CLV, profitable paper trading over 200 bets
- **Level 2 (regression):** Model beats Pinnacle on >5% of games
- **Level 3 (ensemble):** Sustained +5% ROI on 500+ bets with prop coverage
- **Level 4 (mature):** Proprietary edge independent of any single data source

---

## Backtest Results (2022-2025, Updated Apr 13 2026)

### Full Comparison Table (3 Seasons, Fixed 6.0 Line)

| Config | Bets | WR% | ROI% | Sharpe | P&L |
|--------|------|-----|------|--------|-----|
| Base DC (no features) | 1,905 | 54.1% | +2.02% | 1.172 | +$8,034 |
| **DC + Elo + rest days** | **1,829** | **55.6%** | **+4.19%** | **1.844** | **+$18,251** |
| DC + Elo/rest/form fix/goalie | 1,865 | 55.2% | +3.49% | 1.679 | +$16,249 |
| DC + form fix only (no goalie) | 1,851 | 55.3% | +3.61% | 1.658 | +$15,890 |
| DC + XGBoost residual correction | 1,937 | 54.2% | +1.80% | 1.077 | +$7,002 |

**Winner: DC + Elo + rest days = +4.19% ROI, Sharpe 1.844**

Features tested and rejected (all hurt ROI):
- Goalie GSAX: season-level data too coarse, DC already captures via team defense
- Form divergence (L5 vs L20 goals): too noisy, adds no signal
- XGBoost residual correction: overfits on ~800 training samples per season

**Best proven config: DC + Elo + rest days = +4.19% ROI, Sharpe 1.844**

### Key Findings

1. **Elo + rest days doubled ROI** (2.02% -> 4.19%). These two features capture signal Dixon-Coles misses.
2. **Goalie GSAX hurt performance** (-0.7% ROI when added). DC already captures most goalie quality through team defense parameters. Season-level goalie data is too coarse.
3. **Form divergence (L5 vs L20 goals) also hurt** (-0.58% ROI). Too noisy. Disabled.
4. **Always-under at fixed 6.0 is a LOSING strategy** (-13.7% to -0.3% per season). The model's selectivity adds real alpha.
5. **Break-even at -110 = 52.38% win rate**. Our 55.6% is 3.2 points above.
6. **Edge threshold sweet spot: 5-10%**. Below 5% = noise. Above 12% = model miscalibration.

### Edge Threshold Analysis (Best Config)

| Threshold | Bets | WR% | ROI% | P&L |
|-----------|------|-----|------|-----|
| >= 3% | 1,829 | 55.6% | +4.19% | +$18,251 |
| >= 5% | 1,508 | 55.8% | +4.30% | +$16,439 |
| >= 8% | 1,092 | 56.1% | +5.10% | +$14,023 |
| >= 10% | 855 | 56.5% | +5.72% | +$12,326 |
| >= 12% | 626 | 54.3% | +2.59% | +$4,055 |
| >= 15% | 340 | 51.2% | -2.67% | -$2,330 |

Very high edges (15%+) are model errors, not real opportunities.

### What +4.19% ROI Means Concretely
- Start with $5,000 bankroll
- After 3 full NHL seasons (~1,800 bets): bankroll = $23,251
- Average $100 bet returns $4.19 profit
- The model identifies ~600 bets per season where it sees edge
- Quarter-Kelly sizing means bigger bets when edge is bigger

### What This Means
Dixon-Coles foundation + Elo + rest days = the strongest proven signal. Adding more features doesn't automatically help - each one must be validated via backtest. Feature engineering (finding the RIGHT features) matters more than model sophistication - confirming the quant fund principle that features are 80% of the work.

---

## Timeline

- Now: Paper trading Level 1 + start building Level 2 features
- After 200 graded Level 1 bets: Begin Level 2 model training
- After Level 2 backtest validates: Add props (Level 3)
- Continuous: Feature engineering, model improvement, data expansion

---

*This document will be updated as we learn. The strategy should evolve faster than the market.*

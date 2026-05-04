# Deep Research Sweep: Sports Betting Models & Algorithms

**Date**: 2026-04-12
**Scope**: NBA prop models, calibration science, CLV tracking, Poisson methods, value betting, +EV detection, APIs, monetization

---

## TABLE OF CONTENTS

1. [Open-Source NBA Prop Betting Models](#1-open-source-nba-prop-betting-models)
2. [The Calibration vs Accuracy Paper (Walsh & Joshi 2024)](#2-calibration-vs-accuracy-the-definitive-paper)
3. [Calibration Science & Implementation](#3-calibration-science--implementation)
4. [Closing Line Value (CLV) Tracking Systems](#4-closing-line-value-clv-tracking-systems)
5. [Poisson Distribution for Player Props](#5-poisson-distribution-for-player-props)
6. [Value Betting Software & Frameworks](#6-value-betting-software--frameworks)
7. [OddsJam & Positive EV Detection](#7-oddsjam--positive-ev-detection-architecture)
8. [Kelly Criterion & Bankroll Management](#8-kelly-criterion--bankroll-management)
9. [Sports Betting APIs & Data Sources](#9-sports-betting-apis--data-sources)
10. [Backtesting Methodologies](#10-backtesting-methodologies)
11. [Key Mistakes & Warnings](#11-key-mistakes--warnings-aggregated)
12. [Architecture Recommendations](#12-architecture-recommendations-for-sports-edge)

---

## 1. Open-Source NBA Prop Betting Models

### 1.1 plus-ev-model (chevyphillip)
**URL**: https://github.com/chevyphillip/plus-ev-model
**Rating**: BEST open-source prop model found

**Architecture**:
- Python (95.6%), DuckDB + MotherDuck for storage
- Ridge regression for predictions
- Poetry for dependency management
- Modular: `nba_stats.py`, `player_props_model.py`, `predict_props.py`, `edge_calculator.py`, `devig.py`, `monte_carlo.py`

**Methodology**:
1. Ridge regression generates prop predictions
2. Predictions convert to implied probabilities
3. Compare against sportsbook-derived probabilities
4. Kelly criterion for bet sizing
5. Confidence thresholds filter recommendations

**Feature Engineering**:
- Rolling averages across multiple windows (5, 10, 20 games)
- Home/away performance splits
- Opponent strength metrics
- Recent trends
- Consistency measurements

**Data Sources**: NBA API (with 1.0s delay between requests)

**Tracked Metrics**: RMSE, MAE, R-squared, prediction-to-actual correlation, historical ROI

**Key Insight**: The devig module is critical -- converting sportsbook odds to fair probabilities is the foundation of edge detection.

---

### 1.2 nba-models / Three-Point Model (bendominguez0111)
**URL**: https://github.com/bendominguez0111/nba-models

**Methodology**:
- Monte Carlo simulations: 50,000-200,000 games per simulation
- Bootstrap resamples: 100,000 suggested
- Focus on three-point prop predictions

**Data Sources**: NBA Stats API + The Odds API (500 free requests/month)

**Tech Stack**: Python <= 3.10.5, NumPy, nba_api, Jupyter

**Architecture**:
```
model/models/threes.py    (core model)
model/odds_api/           (betting data)
model/utils/betting_math.py (calculations)
model/nba_api_helpers.py  (data fetching)
```

**Key Insight**: Monte Carlo approach with bootstrap confidence intervals provides uncertainty quantification, not just point estimates.

---

### 1.3 NBA Betting Model with Streamlit (mc156-lgtm)
**URL**: https://github.com/mc156-lgtm/nba-betting-model

**Models**:
- XGBoost: spread, totals, moneyline (n_estimators=200, max_depth=6, learning_rate=0.1)
- Ridge Regression: player props
- Half-Kelly for bet sizing

**Reported Metrics** (synthetic data caveat):
- Spread: MAE=2.37pts, RMSE=2.94pts, R-squared=0.9687
- Moneyline: 95% accuracy, ROC AUC=0.9920
- Totals: MAE=12.46pts, RMSE=15.82pts, R-squared=0.1012

**Features**: Rolling averages (5/10/20 game windows) for points, FG%, rebounds, assists, steals, blocks, turnovers, plus/minus, offensive/defensive efficiency, possessions per game

**WARNING**: Trained on synthetic data for demonstration. Real-world performance unverified.

---

### 1.4 NBA_Betting (NBA-Betting org)
**URL**: https://github.com/NBA-Betting/NBA_Betting

**Framework**: 4-level prediction hierarchy:
1. Player Prediction (individual performance)
2. Player Interaction (lineup effects)
3. Team Prediction (team-vs-team)
4. Game Prediction (context: location, rest, referees, injuries, schedule)

**Tech Stack**: AutoGluon (automated ML), SQLite, Flask + Dash, NBA Stats API

**Key Finding**: Analyzed ~23,000 games (2006-2026). Vegas lines miss by ~9.12pts (2006-2016) and ~10.49pts (2020-2026).

**Honest Assessment**: "Consistently outperforming Vegas lines remains a challenge." No profitability claims made.

**Data Sources Used**: Play-by-play, box scores, advanced metrics (EPM, PER, RAPTOR), Vegas lines, schedule effects, injury reports, referee assignments, power rankings, NBA2K ratings

---

### 1.5 Prop_Betting_Regression_Project (VinceDiR)
**URL**: https://github.com/VinceDiR/Prop_Betting_Regression_Project

**Pipeline**:
1. Web Scraping (Selenium, Beautiful Soup) from BettingPros.com
2. Merge player + team stats from Stathead.com
3. Feature engineering
4. Linear regression modeling

**Tech Stack**: Selenium, Beautiful Soup, Pandas, NumPy, Seaborn, scikit-learn

---

### 1.6 betModel (mmyoung77)
**URL**: https://github.com/mmyoung77/betModel

**Minimal**: Uses `nba_api`, Jupyter notebooks. Stated as employer demonstration only. No methodology disclosed in README.

---

### 1.7 nba-prop-prediction-model (parlayparlor)
**URL**: https://github.com/parlayparlor/nba-prop-prediction-model

**Methodology**: Weighted averages + matchup deltas
1. Calculate projections using last N games (default: 5)
2. Compare season averages vs. opponent-specific performance
3. Evaluate opponent defensive rankings
4. Apply delta adjustment for final projection

**Stats**: Points, rebounds, assists, combo stats (P+R, P+A, R+A, P+R+A)

**Simple but useful**: Good baseline approach for comparison.

---

## 2. Calibration vs Accuracy: The Definitive Paper

**Paper**: "Machine learning for sports betting: should model selection be based on accuracy or calibration?"
**Authors**: Conor Walsh & Alok Joshi (2024)
**Published**: Machine Learning with Applications, Volume 16, pages 100539
**Code**: https://github.com/conorwalsh99/ml-for-sports-betting

### THE KEY FINDING (This is the most important insight in this entire document):

| Selection Method | Average ROI | Best Case ROI |
|-----------------|-------------|---------------|
| **Calibration-based** | **+34.69%** | **+36.93%** |
| Accuracy-based | -35.17% | +5.56% |

**Conclusion**: "For sports betting (or any probabilistic decision-making problem), calibration is a more important metric than accuracy."

### What This Means Practically:
- A model that's 75% accurate but poorly calibrated will LOSE money
- A model that's 60% accurate but well-calibrated can be HIGHLY profitable
- The market doesn't care if you're "right" -- it cares if your PROBABILITIES are right
- When your model says 65%, outcomes should occur ~65% of the time

### Implementation:
- Tech: Python (36.9%), Jupyter (63.1%), Poetry
- Full pipeline: `poetry run python src/run_pipeline.py` (~45 min runtime)
- Has unit tests and published corrigendum correcting initial errors
- NBA historical data, tested against actual published betting odds

**ACTION ITEM**: Our model selection process MUST use calibration metrics (Brier score, calibration plots) not accuracy.

---

## 3. Calibration Science & Implementation

### 3.1 What Calibration Means (OpticOdds)
**Source**: https://opticodds.com/blog/calibration-the-key-to-smarter-sports-betting

- A calibrated model assigning 60% win probability should see that team win ~60% of such games over time
- Calibrated models "consistently flagged underdogs with higher-than-expected win chances, yielding positive returns"
- Miscalibrated models lead to overconfidence: overestimating favorites causes systematic losses
- Sportsbooks use calibration to "minimize losses to sharp bettors"

### 3.2 Calibration Metrics to Implement

**Brier Score**: Mean squared difference between predicted probability and actual outcome
```python
brier_score = np.mean((predicted_prob - actual_outcome) ** 2)
# Lower is better. Perfect = 0, worst = 1
```

**Calibration Plot**: Bin predictions by probability range, plot predicted vs actual frequency
```python
from sklearn.calibration import calibration_curve
fraction_of_positives, mean_predicted_value = calibration_curve(
    y_true, y_prob, n_bins=10
)
```

**Expected Calibration Error (ECE)**:
```python
ECE = sum(|fraction_positive_i - mean_predicted_i| * n_i) / N
```

### 3.3 Calibration Techniques

**Platt Scaling (Sigmoid)**:
```python
from sklearn.calibration import CalibratedClassifierCV
calibrated = CalibratedClassifierCV(base_model, method='sigmoid', cv=5)
```

**Isotonic Regression**:
```python
calibrated = CalibratedClassifierCV(base_model, method='isotonic', cv=5)
```

**Temperature Scaling** (for neural nets):
```python
# Divide logits by learned temperature parameter T
calibrated_probs = softmax(logits / T)
```

---

## 4. Closing Line Value (CLV) Tracking Systems

### 4.1 Why CLV Matters
CLV is THE gold standard metric for evaluating betting skill. Not ROI, not win rate -- CLV. If you consistently get better odds than the closing line, you have edge.

### 4.2 CLV Calculation

**Implied probability from decimal odds**:
```python
implied_prob = 1.0 / decimal_odds
```

**CLV percentage**:
```python
CLV = (closing_implied - bet_implied) / bet_implied
```

**Example**: Bet at 2.50 (40% implied), closes at 2.20 (45.5% implied) = **+13.7% CLV**

**No-vig line conversion** (strip vig):
```python
total = imp_a + imp_b  # Sum of both sides' implied probs (>100%)
fair_a = imp_a / total
fair_b = imp_b / total
# Now fair_a + fair_b = 100%
```

### 4.3 Implementation Architecture (AgentBets.ai)
**Source**: https://agentbets.ai/sharp-betting/closing-line-value-api/

**Database Schema (SQLite)**:
```sql
-- Odds snapshots table
CREATE TABLE odds_snapshots (
    event_id TEXT,
    book TEXT,
    market TEXT,
    side TEXT,
    odds REAL,
    fetched_at TIMESTAMP
);
CREATE INDEX idx_odds_event ON odds_snapshots(event_id);

-- Bets table
CREATE TABLE bets (
    event_id TEXT,
    book TEXT,
    market TEXT,
    side TEXT,
    odds REAL,
    stake REAL,
    placed_at TIMESTAMP
);
```

**Python Classes**:
- `BetRecord`: Dataclass for placement details
- `CLVResult`: Output with calculated CLV metrics
- `CLVTracker`: Main class with `snapshot_odds()`, `record_bet()`, `get_closing_line()`, `calculate_clv()`, `clv_report()`

**5-Step Process**:
1. Set up odds data collection via The Odds API (poll every 5-15 min)
2. Record bet placement odds with exact timestamps
3. Capture closing lines 1-5 min before game start
4. Calculate CLV comparing placement to closing
5. Analyze trends across 500+ bets

**Profitability Thresholds**:
- +1-3% CLV: Strong edge
- +0.5-1% CLV: Moderate edge
- Below +0.5% CLV: Marginal

**Key Insight**: Segment CLV analysis by sport, market type, and timing for actionable insights.

---

## 5. Poisson Distribution for Player Props

### 5.1 Why Poisson Works for Player Props
Poisson distribution models discrete event counts where timing is independent. Works for: pass attempts, three-pointers made, rebounds, assists -- any countable stat with a consistent rate.

**Limitation**: In NBA, close games in final minutes follow Power Law, not Poisson. Model accuracy degrades for end-of-game scenarios.

### 5.2 Core Implementation

```python
import numpy as np

# Step 1: Calculate lambda (mean rate) from historical data
lambda_value = player_game_log['stat'].mean()

# Step 2: Simulate N games
n_simulations = 200_000
poisson_arr = np.random.poisson(lam=lambda_value, size=n_simulations)

# Step 3: Calculate probability of over
prop_line = 25.5  # e.g., over/under points
prob_over = sum(poisson_arr > prop_line) / n_simulations
```

### 5.3 Implied Probability from Moneyline

```python
def implied_probability(money_line, round_n=2):
    if money_line < 0:
        return round(money_line / (money_line - 100), round_n)
    else:
        return round(1 - (money_line / (money_line + 100)), round_n)
```

### 5.4 Bootstrap Confidence Intervals

```python
# Quantify uncertainty in your lambda estimate
xs = np.array([])
for _ in range(n_simulations):
    boot_x = np.random.choice(
        player_stats, size=len(player_stats), replace=True
    ).mean()
    xs = np.append(xs, boot_x)

lower_bound = np.quantile(xs, 0.025)  # 2.5th percentile
upper_bound = np.quantile(xs, 0.975)  # 97.5th percentile
# 95% CI for true lambda
```

### 5.5 Edge Detection

```python
calculated_prob = prob_over  # From Poisson simulation
implied_prob = implied_probability(moneyline_odds)

if calculated_prob > implied_prob:
    edge = calculated_prob - implied_prob
    print(f"POSITIVE EV: {edge:.2%} edge on OVER")
elif calculated_prob < (1 - implied_prob):
    edge = (1 - implied_prob) - calculated_prob
    print(f"POSITIVE EV: {edge:.2%} edge on UNDER")
```

### 5.6 Practical Notes
- Bootstrap resampling validates that sample statistics generalize
- Only bet when edge exceeds variance threshold (suggest >3%)
- Use multiple window sizes (last 5, 10, 20 games) and weight recent more
- Account for opponent defensive rating adjustments to lambda

---

## 6. Value Betting Software & Frameworks

### 6.1 sports-betting (Python Package)
**URL**: https://github.com/georgedouzas/sports-betting
**Stars**: 685 | **License**: MIT

**Features**:
- GUI (Reflex), Python API, CLI interfaces
- Dataloaders for historical and fixture data
- Backtesting with time-series cross-validation
- Value bet detection and prediction

**Value Bet Formula**:
```
If estimated_probability > implied_probability_from_odds:
    bet = VALUE BET
```

**Backtesting Approach**:
- TimeSeriesSplit cross-validation (preserves temporal ordering)
- Configurable initial cash and stake per bet
- Multiple betting markets simultaneously

**Example Setup**:
```python
from sportsbet.datasets import SoccerDataLoader
from sportsbet.evaluation import ClassifierBettor
from sklearn.linear_model import LogisticRegression

# Currently focused on soccer -- adapt patterns for NBA
bettor = ClassifierBettor(
    classifier=MultiOutputClassifier(LogisticRegression()),
    init_cash=10000, stake=50
)
bettor.backtest(X_train, Y_train, cv=TimeSeriesSplit(n_splits=5))
```

**Design Philosophy**: "The bettor should aim to systematically estimate value bets, backtest their performance, and not create arbitrarily accurate predictive models."

### 6.2 keeks (Bankroll Management Library)
**URL**: https://github.com/wdm0006/keeks

Python library providing:
- FractionalKellyCriterion class
- Parameters: payoff, loss, transaction_cost, fraction (0.5 = half Kelly)
- Bankroll tracking with loss protection

---

## 7. OddsJam & Positive EV Detection Architecture

### 7.1 How OddsJam Works

**Core Algorithm**:
```
EV = (fair_win_probability * profit_if_win) - (fair_loss_probability * stake)
```

**Detection Method**:
1. Scrape real-time odds from 100+ sportsbooks
2. Calculate no-vig "fair odds" from sharp books (Pinnacle) or market consensus
3. Compare each book's odds against fair odds
4. Flag positive EV when book odds > fair odds

**Processing Scale**: Millions of odds processed per second

**Key Filters**:
- Sportsbook selection (include/exclude)
- League/sport filter
- Market type (main lines, alternates, player props)
- "Market width" -- how much vig the book is charging

### 7.2 No-Vig Fair Odds Calculation

The industry-standard approach for devigging:

**Method 1: Multiplicative (Power Method)**:
```python
# For two-way market
def devig_power(odds_a, odds_b):
    imp_a = 1 / odds_a
    imp_b = 1 / odds_b
    total = imp_a + imp_b  # Overround (e.g., 1.05 = 5% vig)
    fair_a = imp_a / total
    fair_b = imp_b / total
    return fair_a, fair_b
```

**Method 2: Shin Method** (accounts for insider trading probability):
More sophisticated, used by sharper operations. Adjusts for the fact that vig is not evenly distributed.

### 7.3 OddsJam Business Model
- Subscription: Multiple tiers (Positive EV Global being premium)
- Real-time odds comparison
- Bet tracker with CLV tracking
- Kelly criterion calculator
- Educational content funnel

### 7.4 What We Can Replicate
- Real-time odds comparison via The Odds API
- No-vig fair odds calculation
- Positive EV detection
- CLV tracking
- Kelly-based bet sizing

What we CANNOT easily replicate: Their processing speed (millions/sec) and coverage depth (100+ books).

---

## 8. Kelly Criterion & Bankroll Management

### 8.1 Full Kelly Formula

```python
def kelly_criterion(prob_win, decimal_odds):
    """
    f* = (bp - q) / b
    where:
      b = decimal_odds - 1 (net profit per unit)
      p = probability of winning
      q = 1 - p (probability of losing)
    """
    b = decimal_odds - 1
    p = prob_win
    q = 1 - p
    f_star = (b * p - q) / b
    return max(0, f_star)  # Never bet negative
```

### 8.2 Fractional Kelly (Recommended)

**Half Kelly**: Get 75% of the growth with dramatically lower variance.
```python
def half_kelly(prob_win, decimal_odds):
    return kelly_criterion(prob_win, decimal_odds) * 0.5

def quarter_kelly(prob_win, decimal_odds):
    return kelly_criterion(prob_win, decimal_odds) * 0.25
```

**Why fractional**: Full Kelly assumes your probability estimates are PERFECT. They never are. Fractional Kelly provides insurance against model error.

### 8.3 Critical Warning
"When a gambler overestimates their true probability of winning, the criterion value calculated will diverge from the optimal, increasing the risk of ruin."

**Recommendation**: Start with quarter Kelly until model proves calibrated over 500+ bets, then move to half Kelly.

---

## 9. Sports Betting APIs & Data Sources

### 9.1 The Odds API
**URL**: https://the-odds-api.com/
**Best for**: Odds comparison, historical data, backtesting

**Coverage**: 40+ sports, dozens of bookmakers
**Historical Data**: From June 2020 (featured markets), May 2023 (player props)
**Snapshot Frequency**: 5-minute intervals (post Sept 2022)
**Cost**: 10 quota units per region per market per request

**Endpoints**:
```
GET /v4/sports/{sport}/odds                              # Live odds
GET /v4/historical/sports/{sport}/odds                   # Historical featured
GET /v4/historical/sports/{sport}/events/{id}/odds       # Historical additional
```

**Key Feature**: `previous_timestamp` / `next_timestamp` navigation for chronological walkthrough of odds history.

### 9.2 NBA API (nba_api)
**URL**: https://github.com/swar/nba_api
**Best for**: Player stats, game logs, historical performance
**Cost**: Free
**Caveat**: Rate-limited, use 1s delay between requests

### 9.3 OpticOdds
**URL**: https://opticodds.com/
**Best for**: Premium real-time odds data
**Differentiator**: Focus on calibration and smart betting

### 9.4 Sportmonks
**Best for**: Soccer data + odds + probability predictions
**Used by**: Octosport backtesting study

### 9.5 Other Notable APIs
- **Sportradar**: Premium, comprehensive (used by leagues)
- **API-Sports**: REST API for multiple sports
- **SportsGameOdds**: Focus on betting integration
- **Unabated API**: Sharp-focused odds data

### 9.6 Monetization Models for Sports Data Products
- Tiered API subscriptions (free/basic/premium/enterprise)
- Affiliate links on odds comparison displays
- Premium features (real-time vs delayed data)
- Historical data as separate paid product

---

## 10. Backtesting Methodologies

### 10.1 Value Bet Backtesting Framework (Octosport/Medium)
**Source**: https://medium.com/geekculture/quantitative-betting-with-python-how-to-backtest-a-value-bet-strategy-1b8a0dc62a6c

**Core Logic**:
```python
value = (bet_usd * probability) - 1
if value > 0:
    # This is a value bet
    pnl = odds[result] * is_win_bet - 1
```

**Results** (16,114 matches, Oct-Dec 2021):
- Value bets identified: 779 (~5% of matches)
- Best-odds strategy: +125.60 EUR cumulative P&L
- Average-odds strategy: +47.20 EUR cumulative P&L
- Highest-value selection outperformed highest-probability by 40 EUR

### 10.2 Critical Backtesting Rules

**Rule 1**: "Probabilities must not rely on odds" -- External predictions cannot use bookmaker odds as features (circular reasoning)

**Rule 2**: "Probabilities must not use future data" -- Only info available at bet placement time

**Rule 3**: Odds timestamp validation -- Only odds updated within 15 minutes pre-match qualify (in the study, only 2 of 10 bookmakers met this)

**Rule 4**: Account for variance -- P&L ranged from 8.50 to 125.60 EUR depending on assumptions (35% spread)

### 10.3 Backtesting Architecture with Historical Odds API

```python
import requests

def walk_historical_odds(sport, start_date, end_date, interval_hours=1):
    """Walk through historical odds snapshots"""
    current = start_date
    while current < end_date:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/historical/sports/{sport}/odds",
            params={
                'apiKey': API_KEY,
                'date': current.isoformat() + 'Z',
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'decimal'
            }
        )
        data = response.json()
        # Process snapshot: data['data'] contains events + odds
        # Navigate: data['next_timestamp'] for next snapshot
        yield data
```

### 10.4 Overfitting Warning
"Testing strategies across all leagues then selecting winners introduces selection bias that won't persist in future data." -- Always hold out a test period never used during development.

---

## 11. Key Mistakes & Warnings (Aggregated)

### From the Research Papers
1. **Accuracy is NOT calibration**: A 75% accurate model can lose money. A well-calibrated model with 60% accuracy can profit. (Walsh & Joshi, +34.69% ROI vs -35.17%)
2. **Implementation errors in academic code**: Walsh & Joshi published a corrigendum after finding bugs during modularization. Always test rigorously.

### From Open-Source Projects
3. **Synthetic data illusion**: mc156-lgtm model shows near-perfect R-squared but is trained on SYNTHETIC data. Real performance unknown.
4. **No one publicly claims sustained profitability**: Even the most sophisticated projects (NBA_Betting with 23,000 games) admit "consistently outperforming Vegas remains a challenge."
5. **Data leakage**: Point-in-time accuracy is the #1 technical challenge. Using future data in features invalidates everything.

### From Industry Sources
6. **Odds timestamp validation**: Only use odds that were actually available when your model would have bet. In one study, only 2/10 bookmakers had timely odds.
7. **Full Kelly is ruin**: Never use full Kelly. Overestimating edge + full Kelly = guaranteed blowup. Use quarter or half Kelly.
8. **CLV > ROI for skill measurement**: Short-term ROI is noise. CLV across 500+ bets is signal.
9. **Variance is brutal**: Even with genuine edge, expect 35%+ swings in outcomes depending on conditions.

### From Market Structure
10. **Sportsbooks have more data, compute, and expertise**: The edge must come from specific niches or speed, not from generally being "smarter."
11. **Account limits**: Consistently winning accounts get limited or banned. This is THE business constraint.
12. **Line shopping is mandatory**: Best-odds strategy returned 2.6x more than average-odds in backtesting.

---

## 12. Architecture Recommendations for Sports-Edge

Based on this research, here is the recommended technical architecture:

### Core Pipeline
```
Data Collection (nba_api + The Odds API)
    |
Feature Engineering (rolling windows: 5/10/20 games)
    |
Model Training (Ridge/XGBoost with calibration layer)
    |
Calibration Layer (Platt scaling or isotonic regression)  <-- CRITICAL
    |
Probability Output (calibrated probabilities per prop)
    |
Devig Module (convert book odds to fair probabilities)
    |
Edge Calculator (model_prob - fair_prob = edge)
    |
Kelly Sizing (quarter Kelly initially, half Kelly after validation)
    |
CLV Tracker (measure actual edge vs closing lines)
    |
Performance Dashboard (Brier score, calibration plots, CLV%, ROI)
```

### Technology Stack (Based on What Works)
- **Language**: Python 3.11+
- **Data**: DuckDB or SQLite (DuckDB preferred for analytics)
- **ML**: scikit-learn (Ridge, XGBoost) + CalibratedClassifierCV
- **Stats**: NumPy, SciPy (Poisson), pandas
- **Odds API**: The Odds API (historical + live)
- **Player Data**: nba_api
- **Simulation**: Monte Carlo with bootstrap confidence intervals
- **UI**: Streamlit (for dashboard)
- **Bankroll**: Custom Kelly implementation or keeks library

### Key Design Principles
1. **Calibration over accuracy** -- Every model must pass calibration checks before deployment
2. **Devig everything** -- Never compare raw model probability to vigged odds
3. **Bootstrap your confidence** -- Report confidence intervals, not point estimates
4. **Track CLV religiously** -- 500+ bet minimum before trusting any edge signal
5. **Start small** -- Quarter Kelly until calibration proven
6. **Line shop** -- Always compare across books; 2.6x return difference is real
7. **Time-series validation** -- Never shuffle temporal data; use walk-forward testing

### Monetization Paths
1. **Picks service** -- Subscription model for bet recommendations
2. **API product** -- Sell calibrated probability estimates
3. **Data product** -- Historical odds + analysis packaged for researchers
4. **Affiliate** -- Sportsbook referrals through odds comparison tools

---

## Sources Index

### GitHub Repositories
- https://github.com/chevyphillip/plus-ev-model
- https://github.com/bendominguez0111/nba-models
- https://github.com/mc156-lgtm/nba-betting-model
- https://github.com/NBA-Betting/NBA_Betting
- https://github.com/VinceDiR/Prop_Betting_Regression_Project
- https://github.com/mmyoung77/betModel
- https://github.com/parlayparlor/nba-prop-prediction-model
- https://github.com/conorwalsh99/ml-for-sports-betting
- https://github.com/georgedouzas/sports-betting
- https://github.com/wdm0006/keeks

### Papers & Articles
- Walsh & Joshi (2024). "ML for sports betting: accuracy or calibration?" Machine Learning with Applications, Vol 16
- https://arxiv.org/abs/2303.06021
- https://opticodds.com/blog/calibration-the-key-to-smarter-sports-betting
- https://medium.com/geekculture/quantitative-betting-with-python-how-to-backtest-a-value-bet-strategy-1b8a0dc62a6c
- https://www.fantasydatapros.com/betting/blog/nfl/1
- https://www.justintodata.com/improve-sports-betting-odds-guide-in-python/
- https://moldham74.github.io/AussieCAS/papers/Gon.pdf (Poisson limits in NBA)

### Industry / Tools
- https://oddsjam.com/betting-education/how-to-use-the-oddsjam-positive-ev-tool
- https://oddsjam.com/betting-education/closing-line-value
- https://agentbets.ai/sharp-betting/closing-line-value-api/
- https://the-odds-api.com/historical-odds-data/
- https://the-odds-api.com/

### API Providers
- https://opticodds.com/
- https://sportbex.com/
- https://api-sports.io/
- https://oddsjam.com/odds-api
- https://unabated.com/get-unabated-api

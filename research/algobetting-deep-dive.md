# r/algobetting Deep Research Digest
## Compiled from scraped posts + comments

### CRITICAL INSIGHTS FOR OUR MODEL

---

## WHAT ACTUALLY WORKS (from proven profitable bettors)

### 1. The 30K EUR Guy (Hurthaba) - MOST DETAILED SOURCE
**Stats**: 30K EUR profit in 2022, targeting 50K next year
**Method**: Pre-match probability calculation, NOT live betting
**ROI**: Targets 4%, materialized 3.5%
**Volume**: avg 5,000 EUR/day, max 16,000 EUR/day
**Accuracy**: ~60% at avg odds of 1.95
**Timeline**: 14 months from scratch to real profit

**KEY REVELATIONS FROM COMMENTS:**
- "Prediction algorithms are 50%, optimal risk/staking is the OTHER 50%"
- Uses Python + NumPy + Numba, NO ML frameworks
- "There is no esoteric AI or post-PhD-level number theory involved, just clever problem solving"
- "I never tried to build a sport-specific perfect method, but something universal across sports"
- Uses basic data (results, not player-level stats) for MOST sports
- "It is better to have certain, simple data for 10,000 matches than detailed, error-prone data for 1,000"
- "Overfitting is the worst thing you could do building models"
- Women's and men's basketball are "essentially different sports" - don't combine them
- Got limited by 8+ bookmakers, now mainly uses Pinnacle (never limits) and Coolbet
- Baseball: "so beaten by other statisticians that it offers no value"
- Best sports: handball, basketball, volleyball (high scoring = more predictable)
- Football/soccer: market too sharp for the volume it offers
- Tennis: hasn't been able to make it work
- "Don't try to copy others - if it's been done, you won't be best at it"
- Fractional Kelly is MANDATORY: 0.1 during high-volume seasons, up to 0.5 in summer
- "I could write a book on edge-determining alone" — confidence calculations more complex than the model
- Bookmaker margin: "If odds are 3.0 the probability needs to be 33.33%, no matter the overround"

### 2. The +EV Odds Comparison Guy (Own-Relative8207) - 9.82% ROI
**Stats**: 4,290 bets, 6.30% all-time ROI, $3,220 profit from $700 start
**Last 4 weeks**: 2,132 bets, 9.82% ROI, $4,038 profit
**Method**: NOT a prediction model — compares 25,000 odds updates/second across books

**KEY REVELATIONS:**
- "I found a way to filter out most of the false positives" — the breakthrough
- Stores 14 BILLION odds updates for March alone (~150GB compressed)
- Uses PostgreSQL + Clickhouse for odds timeline
- "The edge was there all along, just hidden among bad signals"
- Built a historic replay system to backtest strategies retroactively
- Everything automated — bot places bets
- Only bets on sharp books with APIs and exchanges (NOT soft books)
- 500-600 hours of development
- "I completely started over twice"
- "I have not reinvented the wheel here" — just +EV detection + execution
- Works across ALL sports (not sport-specific)
- Paid odds providers (not cheap)

### 3. NBA Full Season Model (JimmyRazzo75)
- "Combination of top down and bottom up"
- "Simulation based algorithm to formulate edge"
- 2,734 bets tracked
- Got limited at PointsBet despite being careful
- Key inputs: projected possessions and minutes (from commenter)

### 4. Market Sharpness (CremeHoliday8857)
- NFL: sharpest by limits and liquidity, hardest to find edge
- NBA totals: move fast but on tiny info — different mechanics
- MLB/NHL: can be sharp despite lower liquidity
- "A tiny edge in a high-limit market is worth more than a massive edge in a $50 limit market"
- Framework: Limits > Liquidity > Time-to-move (not sport ranking)

### 5. How Books Flag Advantage Players (Economist article)
- Bets over 100 EUR get flagged
- Bets on minor markets get flagged
- Bets placed on PCs (phones are safer)
- Bets placed 30+ minutes before event start flagged
- First 10 bets determine "estimated lifetime worth"
- If first 10 bets beat closing line → likely limited
- Women's names get flagged
- E-currency wallets (Skrill) get flagged

---

## WHAT THIS MEANS FOR US

### Our Current Model is Wrong in Multiple Ways:

1. **We're trying to predict player stats directly** — the 30K guy says "predict the market, not outcomes"
2. **We're using complex per-player data** — he says simple, universal data works better than detailed data
3. **We're focused on one sport (NBA)** — proven bettors spread across many sports
4. **We haven't invested enough in edge-sizing** — "50% is staking strategy" and we've barely touched it
5. **We're comparing to soft book lines** — should benchmark against Pinnacle
6. **Our Kalman filter approach is too sophisticated for the wrong problem** — it's predicting stats well but not finding where books are wrong

### The Two Viable Paths:

**Path A: Odds Comparison / +EV Detection (Like Own-Relative8207)**
- Don't predict anything — find where books disagree
- Compare odds across many books in real-time
- When one book's line is an outlier vs market consensus, bet it
- This is essentially what our arbitrage scanner does, but for single-leg bets
- Requires: fast odds feeds, many book accounts, speed
- ROI: 6-10% proven

**Path B: Universal Probability Model (Like Hurthaba)**
- Build a model that works across many sports
- Use simple, reliable data (results, not player stats)
- Focus on where the MARKET is wrong, not where individual outcomes are wrong
- The model itself is only half — the other half is edge-sizing and bankroll management
- Requires: 14+ months of development, backtesting, deep statistical knowledge
- ROI: 3.5-4% proven

### Path C (Our Arbitrage Scanner) is Already Proven:
- 354 arb opportunities found in our historical data
- 1.58% average guaranteed profit per arb
- No prediction needed, pure math
- But: getting limited is inevitable and fast

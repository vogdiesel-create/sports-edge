# r/algobetting Research Digest
Compiled 2026-04-12 from PullPush API

## Key Posts Analyzed

### 1. "I made 30K EUR algobetting in 2022" (32 upvotes, 75 comments)
- Pre-match probability calculation, NOT live betting
- "Prediction algorithms are 50%, optimal risk/staking is the other 50%"
- ROI target: 4% (materialized 3.5%)
- Daily betting volume: avg 5000 EUR, max 16000 EUR
- Accuracy: ~60% on avg odds of 1.95
- Took 14 months from scratch to real profit
- Got limited by 8+ bookmakers (bet365, William Hill, Betway, etc.)
- Uses Pinnacle/Coolbet (non-limiting books)
- Best sports: handball, basketball, volleyball (high scoring = more predictable)
- "Don't try to predict outcomes, predict the market"
- "To succeed, you must be the best at SOMETHING unique"
- "Don't copy others - if it's been done, you won't be best at it"
- "Baseball has been so beaten by other statisticians that it offers no value"
- Python + NumPy + Numba, no ML frameworks needed
- "There is no esoteric AI or post-phd-level number theory involved"

### 2. "Lessons from Building a Winning Prop Prediction System"
- Data quality is 80% of the battle
- Player name matching between sources is a huge pain
- Use Supabase for storage, master pandas/polars
- "USE BACKTESTS TO VALIDATE, NOT OPTIMIZE"
- Optimize for statistical properties (log-likelihood, MAE), not ROI
- "You need hundreds to thousands of bets to be sure your system works"
- Build infra for speed - try many ideas fast
- Uses Modal for cloud compute
- Guard rails against data leakage are critical
- "You will not beat the market on every line, find WHERE you're more accurate"
- "Quality over quantity of features"

### 3. "A Dumb Manifesto - NFL Modeling Lessons"
- "Don't try to predict outcomes, just try to predict the market"
- "Don't try to BEAT the market, try to BE EARLY"
- "Don't make a meta model that ingests other models - blend outputs instead"
- Track CLV AND actual edge (wins/losses)
- "Don't p-hack - you'll overfit to weird shit"
- Use sharp books (Pinnacle) that don't limit winners
- Use retail accounts (DraftKings) only when off-market
- "Make DraftKings account look like you'll lose the money back"
- Iterate on ONE model, ONE market constantly before scaling

### 4. "How Sharp is FanDuel on NBA Props?"
- FanDuel is considered sharpest retail book for NBA props
- FD openers are garbage, they sharpen close to tip-off
- Pinnacle is NOT sharp on props (outsourced, low limits)
- FD takes the most action from sharps ($50-100 limits on limited accounts)
- Devig FanDuel lines, bet deviations at DraftKings/BetMGM
- DK and MGM have limits but you'll profit before getting cut

### 5. "Beating Books on NBA Props"
- Using Wayback Machine on Rotowire for historical props
- Monte Carlo simulations on ~1500 tests
- Playoff models fail: different defenses, adjustments each game
- Regular season != playoffs for modeling purposes

### 6. "Model Evaluation" (7 seasons backtest)
- 53.48% avg win rate, 38.78% avg ROI using Kelly
- Massive variance: -21% ROI one year, +117% the next
- Log loss better than historical in most years
- $2,714 total profit over 7 seasons starting with $1K each

### 7. "Fractional Kelly Criterion"
- Community uses 15% fractional Kelly
- Halving perceived edge to reduce Kelly recommendations
- Under-allocating rare longshots where real edge was large
- 1-5% of bankroll per position typical

## Critical Insights for Our Project

1. Our weighted average model is primitive vs what works (Kalman filters, ensembles, simulation)
2. 2.2% ROI is below the 3.5-4% that proven profitable bettors target
3. Data quality/cleaning is where most time should go
4. Backtests should validate statistical properties, not optimize for profit
5. Getting limited by sportsbooks is inevitable and THE biggest problem
6. Pinnacle/sharp books should be the benchmark, not retail books
7. "Be early" > "be right" - opening line value matters
8. One deep model beats many shallow models
9. Player props market is less efficient than game lines (opportunity)
10. Playoff/postseason requires completely different models

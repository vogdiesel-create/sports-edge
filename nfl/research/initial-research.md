# NFL Player Props: Initial Research

**Date**: 2026-05-04
**Status**: Foundation research for pre-season model development
**Author**: Sports Edge NFL Division

---

## 1. NFL Prop Market Landscape

### Available Player Prop Markets

**Passing:**
- Passing yards (most liquid QB prop)
- Passing touchdowns
- Passing attempts
- Completions
- Interceptions thrown
- Longest completion
- Passer rating (rare, some books)

**Rushing:**
- Rushing yards (most liquid RB prop)
- Rushing attempts
- Rushing touchdowns
- Longest rush
- Rushing + receiving yards (combo)

**Receiving:**
- Receiving yards
- Receptions
- Receiving touchdowns
- Longest reception
- Targets (rare)

**Defense/Special Teams:**
- Sacks (player-level)
- Tackles + assists
- Interceptions (player-level, rare)

**Kicking:**
- Field goals made
- Extra points made
- Longest field goal
- Total kicking points

**Scoring:**
- Anytime touchdown scorer (very popular, high juice)
- First touchdown scorer (lottery ticket, massive juice)
- 2+ touchdowns

**Game Props (player-adjacent):**
- Total points (team or game)
- First half/second half splits
- Quarters scoring

### Market Liquidity Ranking (Most to Least Liquid)

1. Passing yards (QB) -- highest volume, tightest spreads
2. Rushing yards (RB)
3. Receiving yards (WR/TE)
4. Anytime TD scorer
5. Receptions
6. Passing TDs
7. Completions
8. Rushing + receiving yards
9. Passing attempts
10. Everything else

### Where Books Make Mistakes (Likely Inefficiencies)

**High potential:**
- **Receiving yards for secondary targets** -- Books focus on WR1/WR2, less attention on slot receivers, TEs, and pass-catching RBs. Coverage matchups and game script shifts can create value.
- **Rushing yards in blowout-prone games** -- When a team is expected to dominate, the RB1 line may not fully account for garbage time where the backup RB gets 10+ carries. Conversely, the RB1 line may be inflated if the team goes up big and pulls starters.
- **Weather-affected passing totals** -- Books adjust for weather but often not enough. Wind over 15 mph and rain crush passing volume. Cold weather games (<25F) significantly reduce passing efficiency.
- **Post-bye-week adjustments** -- Players returning from bye weeks show different performance patterns. Offensive coordinators often install new wrinkles after the break.
- **Cross-sport correlation blindness** -- Same-game parlays price props independently, but NFL props are massively correlated. If a team is up 28-3, every offensive prop for the losing team craters.

**Medium potential:**
- **Completions in specific matchup types** -- QBs facing zone-heavy defenses throw more short completions. QBs facing man-heavy defenses throw fewer but longer completions. If the line is set to a flat average, there is value on both sides depending on matchup.
- **Thursday Night Football** -- Short rest creates more variance. Books may not fully account for the pass/run ratio shifts on short rest.
- **Divisional games** -- Familiarity breeds defensive scheming. Passing stats tend to be lower in divisional rematches, especially late season.

**Lower potential (but worth investigating):**
- **Kicker props** -- High weather sensitivity, low attention from sharps, but also low limits and high juice.
- **Sack props** -- Extremely high variance game to game. Hard to model, but that variance cuts both ways.

### NFL Prop Pricing vs MLB

**Key differences:**
- **Sharper lines**: NFL gets massively more betting volume. Lines are sharper by kickoff than MLB lines ever get.
- **Earlier setting**: NFL lines are posted Tuesday/Wednesday for Sunday games. They have 4-5 days to sharpen vs MLB's ~18 hours.
- **Opener value**: The best NFL value is at the opener on Tuesday/Wednesday before the market has fully digested injury reports, weather, and matchup data.
- **Juice structure**: NFL props typically carry -110/-110 to -115/-115. Less exploitative than MLB props which can hit -160 on one side.
- **Limits**: NFL prop limits are higher than MLB (more money flows through NFL), but books are faster to limit sharp bettors.

---

## 2. Data Sources Available

### Free / Already Accessible

**Pro Football Reference (pro-football-reference.com)**
- Complete game logs for every player, every season
- Snap counts, targets, touches
- Advanced stats (DVOA, ANY/A)
- Structured tables, scrapeable
- Rate limited but accessible
- **Priority: HIGH -- primary historical data source**

**NFL.com / ESPN**
- Current season stats and box scores
- Injury reports, depth charts
- Game previews and matchup data
- Less structured than PFR but more current
- **Priority: MEDIUM -- supplement during season**

**nfl_data_py (Python package)**
- Aggregates nflverse data (play-by-play, player stats, rosters)
- Covers 1999-present with weekly granularity
- Includes Next Gen Stats, expected stats
- Easy programmatic access
- **Priority: HIGH -- best path for bulk historical data download**

**nfelo.com**
- Elo ratings for every team
- Win probability models
- Useful for game-script prediction
- **Priority: MEDIUM -- game script modeling input**

### Already Have Access (via MLB model)

**OddsTr (oddstrader.com)**
- Currently used for MLB +EV prop scraping
- **Unknown**: Does OddsTr cover NFL props? Must verify before season.
- If yes: can reuse/adapt the existing oddstrader_scraper.py
- **Priority: CRITICAL to verify during pre-season**

### Paid / Would Need to Acquire

**PrizePicks / Underdog (DFS props)**
- Useful for cross-referencing lines
- Not direct betting sources but show market consensus
- Free to view, no scraper needed initially

**Pinnacle**
- The sharpest book. Pinnacle closing lines are the gold standard for CLV measurement.
- Already tracking for MLB -- extend to NFL
- **Priority: HIGH for CLV validation**

### Data Download Plan (May-August)

| Priority | Data Source | Seasons | What | When |
|----------|-----------|---------|------|------|
| 1 | nfl_data_py | 2023-2025 | Weekly player stats, roster, schedule | NOW |
| 2 | PFR | 2023-2025 | Game logs for target players | June |
| 3 | Historical weather | 2023-2025 | Game-day weather for all outdoor stadiums | June |
| 4 | OddsTr verification | N/A | Confirm NFL prop coverage | July |
| 5 | Historical odds (if available) | 2023-2025 | Opening/closing lines for backtesting | July-Aug |

---

## 3. Key Differences from MLB

### Sample Size (The Core Problem)

MLB: 162 games per team, ~600 plate appearances per regular player. Massive sample. Individual player stats stabilize by mid-season. We can detect real skill vs noise with confidence.

NFL: 17 games per team. A running back might get 200-250 carries total. A receiver might get 80-120 targets. Individual player stat lines have enormous variance game to game.

**Implication:** We cannot rely on simple season averages. We need to use multi-season data, matchup adjustments, and regression to the mean more aggressively. Bayesian approaches (prior from historical + update with recent data) will be essential.

### Line Sharpening Timeline

MLB: Lines open in the morning, game at 7pm. Maybe 8-12 hours for the market to find value. Lines at open are softer.

NFL: Lines open Tuesday/Wednesday. Game on Sunday. The market has 4-5 days to sharpen. By Sunday morning, the lines are much tighter than any MLB line.

**Implication:** We need to either (a) find value early in the week and bet at the opener, or (b) find edges the market systematically misses even with a full week to correct. Option (b) is harder but more durable.

### Weather

MLB: Rain delays/postponements exist. Some parks play differently (Coors). But weather is rarely a dominant factor in player prop outcomes.

NFL: Weather is massive. Games are played outdoors in 22 of 30 stadiums. Wind over 15 mph reduces passing yards by ~15-20%. Rain reduces passing efficiency. Cold weather (<25F) reduces passing volume and increases rushing attempts. Snow games are their own category.

**Implication:** A weather model is not optional. It is a core feature. Every prop projection must be weather-adjusted, especially for passing stats.

### Injury Impact

MLB: If a player is in the lineup, they are roughly 100% effective. No "playing through injuries" at the same level as NFL.

NFL: Players routinely play at 60-80% health. An offensive lineman with an ankle injury reduces QB passing time. A receiver with a hamstring issue runs fewer deep routes. The injury report (Questionable/Doubtful/Out) is public but the actual impact is opaque.

**Implication:** Injury reports must be a core input. Not just "is the player active" but "who else is injured on the offense/defense" and "what is their practice participation pattern."

### Game Script Dependency (Correlation)

MLB: Relatively independent outcomes. A first baseman's at-bats are largely independent of the game score (some late-inning pinch-hitting exceptions).

NFL: Game script dominates everything. A team trailing by 21 in the second half will abandon the run entirely. Their QB will throw 50+ times. Their receivers will get volume inflated. Their RB will get zero touches in the second half.

**Implication:** Predicting game script is as important as predicting individual player talent. We need:
- A spread/total model to predict likely game flow
- Conditional projections: "If Team X is trailing by 14+, what happens to Player Y's rushing yards?"
- Correlation awareness: if you like the QB passing yards OVER, the WR receiving yards OVER is correlated, not independent value

### Positional Volatility

MLB: A batter's Total Bases in a game is variable but within a range. 0-4 TB covers most outcomes.

NFL: A running back can rush for 150 yards or 30 yards based on game script alone, independent of skill. A receiver can have 2 targets or 12 targets based on the defensive scheme adjustment.

**Implication:** Variance is higher, which means (a) we need bigger edges to overcome it, and (b) there may be more systematic mispricing because the noise makes it harder for the market to find the signal.

---

## 4. Initial Hypotheses to Test

Based on what we learned from MLB (edge on mispriced OVER totals for specific player types in specific conditions), here are analogous NFL hypotheses:

### Hypothesis 1: Slot Receiver Yards in High-Total Games

**Theory:** When the game total is set at 50+, both offenses are expected to score a lot. Slot receivers (who run short/intermediate routes) see increased volume because teams are passing more frequently. Books may not fully adjust slot receiver yardage lines for high-total game environments.

**Test:** Compare slot receiver yards in games with O/U >= 50 vs O/U <= 42. If the delta is larger than what the books price, there is an edge on the OVER.

**Data needed:** Weekly receiving stats, game totals, receiver alignment data (slot vs outside).

### Hypothesis 2: Backup RB Rushing in Blowout-Prone Matchups

**Theory:** When a heavy favorite (-10 or more) wins big, the backup RB often gets 10-15 carries in the 4th quarter. These carries are not reflected in the backup RB's prop line (if one is even posted). More practically, the starting RB's UNDER becomes attractive because they sit out the 4th quarter.

**Test:** In games where the favorite won by 17+, what percentage of the time did the starting RB hit their yardage OVER? If it is significantly below 50%, the UNDER on starting RBs for heavy favorites has systematic value.

**Data needed:** Weekly rushing stats, game spreads, game results, carry distribution by quarter (play-by-play data).

### Hypothesis 3: QB Passing Yards and Game Total Correlation

**Theory:** QB passing yards lines are partially derived from the game total, but the adjustment may be imprecise. In very high total games (52+), QBs throw more because both teams are scoring. In low total games (38 or below), QBs throw less and the running game is featured.

**Test:** Build a regression: QB passing yards ~ game total + spread + opponent pass defense rank. See if the residuals (actual vs predicted) show systematic patterns the market misses.

**Data needed:** QB weekly stats, game totals, spreads, opponent defensive rankings.

### Hypothesis 4: Thursday Night Football Unders

**Theory:** TNF games are played on short rest (4 days instead of 7). Offenses are less sharp, playcalling is more conservative, and overall scoring is lower. Player prop lines may not fully discount for the short rest effect.

**Test:** Compare average passing yards, rushing yards, and total points in TNF games vs Sunday games. If player props are set to Sunday-equivalent levels, UNDERs may have systematic value on TNF.

**Data needed:** Weekly stats flagged by day of week, TNF-specific performance data.

### Hypothesis 5: Weather Crushes Passing Props

**Theory:** Books adjust for weather, but may not adjust enough. In games with sustained wind over 15 mph, passing yards drop 15-20%. In rain games, interception rates rise and passing efficiency drops. If the market only partially adjusts, UNDER on passing props in bad-weather games has edge.

**Test:** Get historical weather data for every outdoor game. Regress passing performance on weather variables. Compare the actual impact to how much the market adjusts (would need historical line data to fully test this, but can at least quantify the statistical impact).

**Data needed:** Game-day weather (wind speed, precipitation, temperature), stadium type (indoor/outdoor/retractable), passing stats.

### Hypothesis 6: Divisional Rematch Unders (Late Season)

**Theory:** When teams play a divisional opponent for the second time in a season, defensive coordinators have more film and more specific game plans. Passing stats tend to be lower in the rematch. Books may not fully account for the "rematch discount."

**Test:** Compare QB passing yards in first meeting vs second meeting for divisional games. If the drop-off is larger than what lines suggest, UNDER on passing props in divisional rematches has value.

**Data needed:** Schedule data (identify divisional rematches), weekly passing stats.

### Hypothesis 7: Kicker Props in Dome Games

**Theory:** Kickers in dome games (controlled environment, no wind) are more consistent and hit longer field goals. If kicker prop lines are set to a flat average across all venues, OVERs on kicker props in dome games may have value.

**Test:** Compare kicker FG% and total kicking points in dome vs outdoor games. Quantify the dome advantage.

**Data needed:** Kicker game logs, stadium type, weather data.

---

## 5. Pre-Season Research Plan (May - August 2026)

### May: Data Collection and Foundation

**Week 1 (May 4-10):**
- [x] Set up NFL directory structure
- [x] Download 3 seasons of player game logs via nfl_data_py
- [ ] Download roster and schedule data
- [ ] Initial data exploration: distributions of key stats (passing yards, rushing yards, receiving yards per game)

**Week 2-4 (May 11-31):**
- [ ] Build baseline projections from 3-year historical averages
- [ ] Calculate per-game averages with appropriate regression to mean
- [ ] Identify which players have the most stable game-to-game production (low variance = more predictable = easier to project)
- [ ] Study positional archetypes: pocket passer vs mobile QB, bell-cow RB vs committee, WR1 vs slot

### June: Advanced Modeling

- [ ] Download historical weather data for all outdoor stadiums
- [ ] Build weather adjustment model (wind, rain, temperature effects on passing/rushing)
- [ ] Build game-script model using spread + total as inputs
- [ ] Create conditional projections (blowout scenario, close game scenario, trailing scenario)
- [ ] Study correlations between props (receiving yards ~ passing yards, rushing yards ~ game script)

### July: Market Research

- [ ] Verify OddsTr NFL prop coverage
- [ ] If OddsTr covers NFL: adapt scraper for NFL prop format
- [ ] If not: identify alternative prop odds sources
- [ ] Research historical NFL prop odds data availability
- [ ] Study typical NFL prop juice structure (by market, by book)
- [ ] Identify which prop markets have the loosest lines (least efficient)

### August: Backtesting and Strategy

- [ ] Backtest candidate strategies against any available historical odds data
- [ ] If no historical odds data: forward-test strategies against early preseason lines
- [ ] Rank hypotheses by expected edge and testability
- [ ] Select top 2-3 strategies for Week 1 paper trading
- [ ] Build automated pipeline: scrape props -> apply model -> flag +EV bets
- [ ] Set up daily workflow for regular season

### September: Go Live (Paper Trading)

- [ ] Paper trade starting Week 1 (September 10, 2026)
- [ ] Track every pick in sim_ledger.json
- [ ] Grade results weekly against actual box scores
- [ ] Minimum 4 weeks of paper trading before considering any real exposure
- [ ] Weekly journal entries documenting what is working and what is not

---

## 6. Open Questions

1. **Does OddsTr cover NFL props?** This is the single most important question. If yes, we can reuse the existing scraper infrastructure. If no, we need a new data source for live odds.

2. **Historical NFL prop odds** -- Is there any source for what NFL prop lines were in past seasons? Without historical odds, we cannot do true backtesting (only forward testing once the season starts).

3. **Same-game parlay correlation** -- Can we exploit correlation blindness in SGP pricing? Books price same-game parlays by multiplying individual prop odds, but NFL props are heavily correlated. This might be a separate edge.

4. **Alternate lines** -- NFL props often have alternate lines (e.g., Tyreek Hill over 99.5 yards at +150 vs over 79.5 at -115). Are alternate lines systematically mispriced differently than primary lines?

5. **Live props** -- NFL live props (in-game) update slower than the actual game flow. Is there an edge in live betting during the game when the score changes dramatically?

---

## 7. Risk Factors

- **Small sample size**: 17 games per team means we might need 2+ full seasons to validate a strategy with statistical confidence.
- **Sharp market**: NFL is the most bet sport in America. The lines are very efficient. Any edge we find will be thinner than MLB.
- **Model overfitting**: With only 17 data points per player per season, it is extremely easy to overfit a model to noise. Must use proper cross-validation and out-of-sample testing.
- **Injury risk**: A single injury can invalidate weeks of modeling. Must build injury-robust projections.
- **Regulatory risk**: Florida sports betting landscape could change. Hard Rock Bet availability should be confirmed for NFL season.

---

## Summary

The NFL prop market is deeper, sharper, and more complex than MLB. The edge, if it exists, will be thinner and harder to find. But the same core philosophy applies: find systematic mispricing, prove it in simulation, then exploit it with discipline.

The four-month research window (May-August) is a luxury. Use it to do the work the market participants skip: deep historical analysis, weather modeling, game-script prediction, and rigorous backtesting.

The MLB model taught us that the edge lives in specificity: not "all TB props" but "TB OVERs within a -160 juice cap." The NFL edge will be similarly specific. The research phase is about finding exactly where that specificity lives.

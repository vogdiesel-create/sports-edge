# Prop Model Research Report

**Date**: 2026-04-15
**Author**: Timosha (research agent)
**Status**: Research complete, ready for implementation planning

---

## 1. Data Inventory

### 1.1 FanDuel Prop Snapshots (fd_prop_snapshots)

**Location**: `data/sports_edge.db`, table `fd_prop_snapshots`

| Metric | Value |
|--------|-------|
| Total rows | 268,566 |
| Date range | 2026-04-13 to 2026-04-15 (3 days) |
| Unique players | 3,450 |
| Snapshots/day | ~89K avg (55K-130K range) |
| Sports | NBA only |
| Collection frequency | Every ~15 min (245 collection runs logged) |

**Schema**: `id, collected_at, sport, game, player, market, line, over_odds, under_odds`

**Markets collected**:

| Market | Count |
|--------|-------|
| Combos | 83,284 |
| Points | 65,206 |
| Rebounds | 50,648 |
| Threes | 36,018 |
| Assists | 33,410 |

**Critical finding**: The automated collector (`data_collector.py`) is collecting NBA props from FanDuel but NOT NHL or MLB props. The FanDuel API tabs it uses are NBA-specific (player-points, player-assists, player-rebounds, player-threes, player-combos). NHL and MLB props exist in FanDuel's API but require different tab endpoints.

### 1.2 Production Props (production.db)

**Location**: `data/production.db`, table `props`

| Metric | Value |
|--------|-------|
| Total rows | 23,712 |
| MLB props | 19,363 |
| NBA props | 3,719 |
| NHL props | 630 |

**MLB markets**: Total Bases (3,505), Strikeouts (3,505), RBIs (3,505), Home Runs (3,505), Hits (3,505), Batter Props (1,718), Pitcher Props (120)

**NHL markets**: Shots (126), Saves (126), Points (126), Goals (126), Assists (126)

**Schema**: `id, timestamp, sport, game, player, market, market_name, line, odds_american, odds_decimal, side`

This table has the right data structure but limited NHL/MLB volume. It appears to be from a one-time or infrequent collection run rather than continuous monitoring.

### 1.3 Historical Prop JSON Files

**Location**: `data/props_*.json` (74 files, Oct 2025 - Apr 2026)

These files come from the-odds-api and contain multi-book prop odds (primarily NBA). The API credits are now exhausted (0/20K remaining). Format: events with bookmaker-level market data including FanDuel, DraftKings, etc.

**Sports coverage**: Almost exclusively `basketball_nba`. No NHL or MLB prop data in this source.

### 1.4 OddsTrader / Devig Data

| File | Content |
|------|---------|
| `oddstrader_ev_props.json` | 304 NHL/MLB +EV picks (never graded, 0 of 304 graded) |
| `devigged_props.json` | 1,126 devigged props (262 NHL, 864 MLB) from Bovada+FD |
| `multi_book_props.json` | Cross-book scan results (mostly empty last run) |
| `prop_picks_log.json` | 304 logged picks (178 MLB, 126 NHL, 0 graded) |

### 1.5 Player Stats Tables (sports_edge.db)

**MLB Batters** (`mlb_batters`): 1,072 players, 2026 season
- Fields: batting avg, OBP, SLG, OPS, K%, BB%, wOBA, xwOBA, exit velo, launch angle, hard hit%, barrel%, sprint speed
- Splits: vs LHP and vs RHP (nullable, mostly empty)
- Statcast metrics: mostly NULL (not yet populated)

**MLB Pitchers** (`mlb_pitchers`): 1,050 players, 2026 season
- Fields: ERA, FIP, xFIP, WHIP, IP, K, BB, K/9, BB/9, HR/9, BAA
- Statcast: fastball velo, spin rate, whiff%, hard hit against, barrel% against, xERA (all NULL)

**NHL Skaters** (`nhl_skaters`): 13,975 rows (920 players x 5 situations x 3 seasons)
- Seasons: 2022, 2023, 2024 (no 2025 data)
- Situations: all, 5on5, 5on4, 4on5, other
- Fields: GP, ice time, goals, assists, points, shots, SOG, shot attempts, high-danger shots/goals, xGoals, xOnGoal, on-ice corsi/fenwick %, game score, penalty minutes

**NHL Goalies** (`nhl_goalies`): 1,540 rows
- Seasons: 2022, 2023, 2024
- Fields: GP, ice time, xGoals, goals, saves, save%, xSave%, GSAX, danger-zone breakdowns, rebounds, freeze

**Game History**:
- `nhl_games`: 109 games (limited)
- `mlb_games`: 5,204 games (solid)

### 1.6 What We Have vs What We Need

| Data | Have | Need | Gap |
|------|------|------|-----|
| FanDuel NHL/MLB prop lines | One-time snapshots only | Continuous collection (every 15 min) | Extend data_collector.py to NHL/MLB tabs |
| Bovada NHL/MLB prop lines | Live fetch via multi_book_props.py | Historical accumulation | Not stored in DB, only JSON snapshots |
| NHL skater season stats | 3 seasons, 5 situations | Current 2025 season + per-game logs | Need 2025 data + game-level stats for rolling averages |
| MLB batter season stats | 2026 season, 1,072 players | Statcast metrics (exit velo, barrel%) + game logs | Statcast fields all NULL, no game-level data |
| MLB pitcher season stats | 2026 season, 1,050 players | Statcast + game logs for rolling averages | Statcast fields all NULL |
| NHL goalie per-game stats | Season aggregates only | Per-game starts, save%, shots against | Need game-level data |
| Pinnacle prop lines | None | Sharp benchmark for devigging | OddsPapi.io signup pending (free tier, 250 req/mo) |
| Prop grading / outcomes | 0 graded out of 304 logged | Graded results for calibration | prop_grader.py exists but was never run successfully |
| Player game logs | Not in DB | Essential for rolling averages | Need NHL API + MLB Stats API game log fetchers |

---

## 2. Devigging: How to Get Fair Probabilities

### 2.1 Current Approaches

Three devigging methods already exist in the codebase:

**Multiplicative (devig_pair in multi_book_props.py)**:
```
fair_over = implied_over / (implied_over + implied_under)
```
Simple, fast, slightly biased toward the favorite. Used in cross-book comparison.

**Power method (devig_power in devig_engine.py)**:
```
Solves: implied_over^k + implied_under^k = 1
```
More accurate for balanced markets. Already implemented with binary search fallback.

**Cross-book consensus (multi_book_props.py)**:
```
consensus = average(bovada_devigged, fanduel_devigged)
edge = consensus_fair_prob - book_implied_prob
```

### 2.2 The Prop Devigging Challenge

Props are harder to devig than game totals because:

1. **No Pinnacle prop lines**: Pinnacle is the sharpest book for game lines, and our game model uses Pinnacle as the market anchor (45% weight). For props, we have no sharp benchmark. OddsPapi would provide this but signup is pending.

2. **One-sided markets**: Many FanDuel prop markets are threshold-style ("Player to score 2+ goals") with only an Over price, no Under. The code in multi_book_props.py estimates Under odds by assuming ~4.5% vig total, but this is unreliable.

3. **Wider vig on props**: Books charge 5-10% vig on props vs 3-5% on game totals. This means devigging errors are amplified.

### 2.3 Recommended Devigging Strategy for Prop Model

**Tier 1 (best available)**: Power method devig of FanDuel O/U pairs where both sides are quoted. FanDuel has the most liquid prop markets and posts real O/U pairs for main markets (strikeouts, SOG, hits).

**Tier 2 (cross-book)**: When both Bovada and FanDuel quote the same prop, average their power-devigged fair probabilities. This is the "wisdom of crowds" approach -- already implemented in multi_book_props.py.

**Tier 3 (when Pinnacle available)**: If OddsPapi signup happens, use Pinnacle prop lines as the primary benchmark, same as the game model does. This would be a step-change in accuracy.

**For the prop MODEL** (as distinct from prop DEVIGGING): The goal is not just to devig existing lines but to generate our own fair probabilities from player stats + game environment, then compare against the market. The devigged market line becomes a sanity check, not the primary signal.

---

## 3. Proposed Architecture

### 3.1 Core Insight

The DESIGN-DOC-V2.md already nails it (Phase 3, lines 78-91): player props are correlated with game totals. A high-total game means more counting stats for everyone. The game model feeds the prop model.

This is the key architectural advantage: we already have validated game-total models (NHL: +4.19% ROI, MLB: in development). Player props are decompositions of game totals.

### 3.2 Architecture Overview

```
                    GAME ENVIRONMENT
                    (from existing models)
                          |
              +-----------+-----------+
              |                       |
    NHL Game Model              MLB Game Model
    (Dixon-Coles + Elo)        (Pitcher-Adj Poisson)
              |                       |
        Expected goals          Expected runs
        per team                per team
              |                       |
              v                       v
         PROP MODEL LAYER
         +--------------------------------------------------+
         |                                                  |
         |  Player Baseline Stats (season + rolling window) |
         |  + Game Environment Adjustments                  |
         |  + Opponent Adjustments                          |
         |  = Player-Level Expected Stat Distribution       |
         |                                                  |
         +--------------------------------------------------+
              |
              v
         EDGE DETECTION
         model_fair_prob vs FD/Bovada devigged line
         edge > threshold -> signal
              |
              v
         SIZING + OUTPUT
         Quarter-Kelly, same as game model
```

### 3.3 NHL Prop Models

**Shots on Goal (SOG)** -- most exploitable NHL prop market:
```
Expected SOG = player_shot_rate_per_60 * expected_ice_time
             * (opponent_shots_against_rate / league_avg_shots_against)
             * pace_factor(game_total / league_avg_total)
```

Inputs needed:
- `nhl_skaters.shotsOnGoal / nhl_skaters.icetime * 60` = per-60 shot rate
- Expected ice time: derive from `nhl_skaters.icetime / nhl_skaters.games_played`
- Opponent shot suppression: from team-level metrics (already in nhl_model.py)
- Game pace from our game total prediction

Distribution: Poisson (SOG are count data, low mean ~3, variance roughly equals mean)

**Goals** -- lower volume, harder to model:
```
P(goals >= N) = SOG_distribution * shooting_pct * (1 - goalie_save_pct)
```
Goals are rare events (0-1 per game for most players). Poisson with very low lambda. Most value is in "anytime goalscorer" markets.

**Points (G+A)** -- correlated with goals:
```
Expected points = expected_goals + expected_assists
Expected assists = player_assist_rate * linemate_goal_probability
```
Points are correlated across linemates. Need to model the line combination, not just individual players.

### 3.4 MLB Prop Models

**Pitcher Strikeouts** -- best MLB prop market:
```
Expected Ks = pitcher_K_per_9 / 9 * expected_innings
            * (opponent_K_pct / league_avg_K_pct)
            * park_factor * ump_factor
```

Inputs:
- `mlb_pitchers.k_per_9` (have)
- Expected innings: `mlb_pitchers.innings_pitched / mlb_pitchers.games_started`
- Opponent K%: from `mlb_batters.k_pct` aggregated by team
- Park and ump factors (need to build)

Distribution: Poisson or Negative Binomial (pitcher Ks have slight overdispersion)

**Batter Hits**:
```
Expected hits = at_bats * batting_avg_adjusted
              * (matchup_factor vs pitcher type)
              * park_factor
```

**Batter Total Bases**:
```
Expected TB = hits * avg_bases_per_hit
            = H * (1*1B_pct + 2*2B_pct + 3*3B_pct + 4*HR_pct)
```

**Batter RBIs** -- hardest, most context-dependent:
```
Expected RBI = P(hit_with_RISP) * avg_runners_scored_per_hit
             + P(HR) * avg_runners_on_per_HR
```
RBIs depend heavily on lineup position and runners on base. This is the hardest prop to model and likely the least exploitable.

### 3.5 How It Connects to Existing Code

| Existing Component | Role in Prop Model |
|---|---|
| `nhl_model.py` | Provides game-level expected goals per team (pace/environment) |
| `mlb_model.py` | Provides game-level expected runs per team (environment) |
| `nhl_data_pipeline.py` | Source for team-level features used in environment adjustment |
| `mlb_data_pipeline.py` | Source for pitcher features, team batting, park factors |
| `devig_engine.py` | Devig FD/Bovada prop lines for market comparison |
| `multi_book_props.py` | Cross-book consensus for edge detection |
| `prop_grader.py` | Grade prop picks against actual box scores (verification loop) |
| `data_collector.py` | Needs extension: collect NHL/MLB props (currently NBA only) |

---

## 4. Market Exploitability Analysis

### 4.1 Why Props Are Softer Than Game Lines

1. **Lower limits**: Books accept less action on props, so they invest less in sharp pricing
2. **More markets**: A single game has 50+ prop markets vs 3-4 game lines. Books can't sharpen all of them.
3. **No Pinnacle benchmark**: Pinnacle offers limited prop markets. Other books can't easily copy sharp pricing.
4. **Player-level info lag**: Lineup changes, minor injuries, hot/cold streaks take longer to price into props than game lines.
5. **Correlation mispricing**: Books price props independently but they are correlated (all counting stats go up in high-scoring games).

### 4.2 Most Exploitable Markets (Ranked)

**Tier 1 -- Highest Edge Potential**:

1. **NHL Shots on Goal**: Stable, high-volume stat. Player shot rates are consistent game-to-game. Opponent shot suppression is modelable. Books set lines based on season averages but don't adjust well for pace (our game model does).

2. **MLB Pitcher Strikeouts**: K rates are the most stable pitcher stat. Opponent K% is well-documented. The model can capture matchup-specific edges (high-K pitcher vs high-K lineup = Over value). FanDuel and Bovada both offer O/U markets with both sides priced.

**Tier 2 -- Good Edge Potential**:

3. **MLB Batter Hits**: Batting average is fairly stable. Pitcher matchup matters (LHP/RHP splits). Park factors are significant (Coors, Fenway). We have the data in `mlb_batters` to model this.

4. **NHL Points**: Combines goals and assists. More variance than SOG but higher-juice markets (more vig = more potential mispricing). Linemate effects are a modeling advantage.

5. **MLB Total Bases**: Similar to hits but includes extra-base hit power. Statcast data (exit velo, barrel%) would be powerful here but is currently NULL in our DB.

**Tier 3 -- Lower Edge / Harder to Model**:

6. **NHL Goals (anytime goalscorer)**: Very low-frequency event. High variance. Threshold markets ("to score 1+ goals") dominate, making devigging harder. Still, books systematically overprice popular players and underprice depth scorers.

7. **MLB RBIs**: Too context-dependent (requires modeling baserunner state). Low modeling advantage.

8. **NBA Props**: We have the most data (268K snapshots) but NBA props are the sharpest market. Books have sophisticated NBA models. Lower edge opportunity despite better data availability.

### 4.3 Where Books Are Weakest

Based on analysis of the existing devigged data and cross-book comparison code:

- **Threshold markets** (e.g., "3+ SOG", "2+ Goals"): These have only one priced side. Books cannot easily balance action, so they add extra vig. Our model can find value the market is over-charging for.
- **Late-announced lineup changes**: When a backup goalie is announced 30 min before puck drop, game lines adjust fast but prop lines lag. Our pipeline already monitors FanDuel in real-time.
- **Pace-correlated props**: Books price each player's props independently of the game total. If our model predicts a high-scoring game (over 7 total), ALL offensive props for players in that game should be adjusted upward. This correlation is our biggest structural advantage.

---

## 5. Development Plan

### Phase 1: Data Infrastructure (Effort: 2-3 days)

1. **Extend `data_collector.py`** to collect NHL and MLB props from FanDuel
   - Add NHL tabs: shots, goals, assists, points, saves
   - Add MLB tabs: pitcher-props (strikeouts), batter-props (hits, total bases, RBIs, HRs)
   - Store in `fd_prop_snapshots` with sport-specific market labels
   - Run continuously alongside existing NBA collection

2. **Build player game log fetcher**
   - NHL: Use `api-web.nhle.com` for per-game player stats (SOG, goals, assists, ice time)
   - MLB: Use `statsapi.mlb.com` for per-game batter/pitcher stats
   - Store in new tables: `nhl_player_game_logs`, `mlb_player_game_logs`
   - Need rolling 10/20/season windows for baseline calculations

3. **Populate Statcast fields** in `mlb_batters` and `mlb_pitchers`
   - Source: Baseball Savant API (free)
   - Exit velocity, barrel%, hard hit%, sprint speed for batters
   - Whiff%, fastball velo for pitchers

4. **Fix prop grading** (`prop_grader.py`)
   - 304 logged picks, 0 graded -- something is broken in the grading pipeline
   - Fix and backfill grading to establish baseline accuracy

### Phase 2: Core Prop Model (Effort: 5-7 days)

5. **Build `prop_model.py`** -- the central prediction engine
   - Input: player_id, stat_type, game_context (from game model)
   - Output: probability distribution over stat outcomes (Poisson/NegBin)
   - Start with NHL SOG and MLB pitcher Ks (highest edge, cleanest data)

6. **Player baseline module**
   - Rolling averages (L5, L10, L20, season) from game logs
   - Situational adjustments (home/away, vs team, rest days)
   - Regression to mean for small samples (Bayesian shrinkage)

7. **Game environment integration**
   - Pull expected team scoring from `nhl_model.py` / `mlb_model.py`
   - Compute pace multiplier: `model_expected_total / league_avg_total`
   - Apply to player baselines

8. **Opponent adjustment module**
   - NHL: opponent shots against rate, goalie save% for goals props
   - MLB: opponent K% for pitcher Ks, pitcher quality for batter props

### Phase 3: Edge Detection + Paper Trading (Effort: 3-4 days)

9. **Build `prop_edge_detector.py`**
   - Compare model fair probability to FanDuel devigged line
   - Apply same tiering system as game model (S/A/B tiers)
   - Kelly sizing with prop-specific bankroll allocation

10. **Integrate into `edge_detector.py`**
    - Add prop picks alongside game total picks
    - Separate bankroll allocation: X% for game totals, Y% for props
    - Deduplicate: don't bet both game total and correlated props in same game

11. **Paper trading + grading loop**
    - Log prop picks to production.db
    - Grade nightly using prop_grader.py
    - Track ROI, CLV (where possible), calibration

### Phase 4: Calibration + Expansion (Effort: Ongoing)

12. **Calibration analysis** after 100+ graded prop bets
    - Is model overconfident? Underconfident?
    - Which markets are most profitable?
    - Adjust thresholds based on empirical results

13. **Expand to additional markets**
    - NHL goals, points, assists
    - MLB hits, total bases
    - Correlated parlays (game total + player props)

---

## 6. Estimated Revenue Impact

### Conservative Estimate

Using the game model as reference (+4.19% ROI on ~600 bets/season for NHL):

- Props have wider vig (more room for edge) but also more noise
- Assume +3% ROI on props (below game model due to higher variance)
- NHL + MLB combined: ~15 prop bets/day during season = ~2,700 bets/year
- At $50 avg bet: 2,700 * $50 * 3% = **$4,050/year from props alone**
- This roughly doubles the game-total revenue

### Optimistic Estimate

If we achieve game-model-level accuracy (+4-5% ROI):
- 2,700 bets * $50 * 5% = **$6,750/year from props**
- Combined with game totals: potentially $12K+/year

### Break-Even Requirement

At -110 average odds on props: need 52.4% win rate to break even.
Target: 54%+ win rate (1.6 points above break-even, similar to game model's 3.2 points above).

---

## 7. Risks and Unknowns

### High Risk

1. **No historical prop line data**: We cannot backtest the prop model the way we backtested the game model (3 seasons of Pinnacle data). We will be live-testing from day one. Mitigation: paper trade aggressively, require 200+ graded bets before real money.

2. **Player stat variance**: Individual player stats are inherently noisier than team totals. A team scores ~3 goals/game (moderate variance); a single player gets 0-7 SOG (high variance). Larger sample sizes needed to prove edge.

3. **No Pinnacle prop benchmark**: Without Pinnacle, our "fair probability" comes from devigging soft books against each other. This is circular -- if both FanDuel and Bovada are wrong in the same direction, our consensus is also wrong. Mitigation: our model-generated probability is the primary signal, devigged lines are confirmation only.

### Medium Risk

4. **FanDuel API stability**: The API endpoints used are undocumented and can change without notice. The `FD_AK` parameter may stop working. Mitigation: monitor for errors, have Bovada as backup.

5. **Statcast data gaps**: MLB batter/pitcher Statcast fields are all NULL. Without exit velocity and barrel%, the MLB batter prop model loses a major feature. Mitigation: can start with traditional stats (BA, OBP, SLG) and add Statcast as populated.

6. **NHL season data gap**: nhl_skaters has 2022-2024 seasons but not 2025. Need current season data for accurate baselines. Source: MoneyPuck or NHL API.

### Low Risk

7. **Compute/complexity**: Prop model is fundamentally simple (Poisson distribution with adjusted parameters). No neural nets or expensive training required.

8. **Correlation modeling**: Getting the game-environment adjustment right is important but the principle is straightforward (multiply by pace factor). Can iterate.

---

## 8. Recommended Priorities

Given the current state of the system, the optimal sequencing is:

1. **Extend data_collector.py to NHL/MLB props** -- without continuous data collection, nothing else matters. This is the foundation. (Day 1)

2. **Build player game log fetchers** -- season stats are too coarse for props. Need per-game data for rolling windows. (Day 1-2)

3. **Fix prop grading pipeline** -- 304 ungraded picks is diagnostic data being wasted. (Day 2)

4. **Build NHL SOG prop model first** -- cleanest data, most stable stat, highest edge potential, smallest implementation surface area. (Day 3-5)

5. **Build MLB pitcher K prop model second** -- similar rationale, leverages existing pitcher data. (Day 5-7)

6. **Paper trade and grade for 2+ weeks** before expanding to other markets. (Ongoing)

**Do not build**: NBA props (sharp market, low edge), RBI props (too context-dependent), correlated parlays (premature optimization).

---

## Appendix: Key File Paths

| File | Purpose |
|------|---------|
| `data/sports_edge.db` | Main database (player stats, prop snapshots, game results) |
| `data/production.db` | Production prop lines (23K rows, mostly MLB) |
| `data_collector.py` | Continuous data collection (needs NHL/MLB prop extension) |
| `multi_book_props.py` | Cross-book prop comparison (Bovada vs FanDuel) |
| `devig_engine.py` | Power method + multiplicative devigging |
| `prop_grader.py` | Grade props against actual box scores |
| `nhl_model.py` | NHL game total model (Dixon-Coles, +4.19% ROI) |
| `mlb_model.py` | MLB game total model (Pitcher-Adj Poisson) |
| `edge_detector.py` | Unified edge detection pipeline |
| `nhl_data_pipeline.py` | NHL feature engineering |
| `mlb_data_pipeline.py` | MLB feature engineering |

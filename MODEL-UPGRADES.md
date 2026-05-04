# Model Upgrade Roadmap

No changes until 50+ graded paper bets. This is the priority list for when we get there.

## Tier 1: High Impact (do first)

### 1. MLB Starting Pitcher Integration
- **Status**: Data pipeline built, pitcher stats in DB, not wired into model
- **Impact**: 1-2 run swing on game totals depending on pitcher quality
- **What**: Query `mlb_pitchers` table, adjust Poisson lambda based on pitcher ERA/WHIP/K9
- **Why**: Pitcher IS the game in baseball. Model currently uses team averages which ignores the biggest variable

### 2. NHL Goalie Starter Integration
- **Status**: Data pipeline built, goalie data in DB, not wired into model
- **Impact**: 0.5+ goal swing between backup and starter
- **What**: Query `nhl_goalies` table, adjust expected goals based on goalie save percentage
- **Why**: Backup goalies allow significantly more goals. Market prices this in, we don't

### 3. Real Pinnacle Lines in Backtest
- **Status**: Historical data downloading now (2023-2025)
- **Impact**: Validates whether our edge is real or an artifact of fake lines
- **What**: Replace fixed 6.0 line backtest with actual Pinnacle closing lines per game
- **Why**: Current backtest is meaningless without real market lines to test against

## Tier 2: Medium Impact (do after Tier 1 proves out)

### 4. Line Movement Detection
- **Status**: `line_snapshots` table collecting data daily
- **Impact**: Sharp money indicator - if line moves toward our side, confirms edge
- **What**: Track opening vs closing lines, weight picks where sharp money agrees with model
- **Why**: Line movement tells you where the smart money went

### 5. MLB Weather Integration
- **Status**: Not built yet
- **Impact**: 0.5-1 run at extreme venues (Wrigley wind, Coors altitude)
- **What**: NWS API for wind speed/direction at outdoor parks, adjust totals
- **Why**: Wind blowing out at Wrigley or playing at Coors adds runs the model doesn't account for

### 6. Pitcher Handedness Splits
- **Status**: Not built
- **Impact**: Lineup-dependent, moderate
- **What**: Adjust team batting projections based on lineup vs LHP/RHP matchup
- **Why**: Some lineups mash lefties but struggle against righties

## Tier 3: Lower Impact (optimization phase)

### 7. Rest Days / Schedule Spots
- **Status**: Not built
- **Impact**: Small but consistent (back-to-back, travel)
- **What**: Factor in days rest, travel distance, time zone changes
- **Why**: Tired teams underperform, especially goalies on back-to-backs

### 8. Umpire/Referee Tendencies
- **Status**: Not built
- **Impact**: Small for totals
- **What**: Track which MLB umpires have wider/tighter zones affecting run scoring
- **Why**: Some umpires consistently produce higher/lower scoring games

### 9. Model Ensemble Weighting
- **Status**: Currently 50/50 Dixon-Coles/XGBoost blend
- **Impact**: Depends on component accuracy
- **What**: Dynamically weight models based on recent accuracy
- **Why**: One model may be better in certain situations

### 10. Market-Aware Sizing
- **Status**: Basic Kelly criterion implemented
- **Impact**: Better capital efficiency
- **What**: Adjust bet sizing based on CLV track record, correlation between bets, drawdown state
- **Why**: Smarter sizing compounds edge faster

## Gate Rules
- No upgrade ships without backtest showing improvement
- No upgrade ships without 50+ graded paper bets proving baseline
- Each upgrade gets A/B tested: run old model and new model side by side for 2 weeks
- If an upgrade makes CLV worse, revert immediately

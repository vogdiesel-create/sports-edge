# Sports Edge - Change Log

Every model/pipeline change with date, what changed, why, and expected impact.

## 2026-04-16

### MAX_EDGE reduced from 15% to 12%
- **File:** edge_detector.py
- **Why:** Data showed 5-12% edge = +48% ROI, 12%+ = disaster (-$351)
- **Expected impact:** Filter out bad bets, higher ROI at cost of fewer bets

### K-prop split thresholds added
- **File:** prop_model.py
- **Changes:** MIN_EDGE_UNDER=3% (was 5%), MAX_EDGE_OVER=15%
- **Why:** Backtest showed UNDER +30% ROI vs OVER +8%. Lower bar for UNDER, cap OVER.
- **Expected impact:** More UNDER bets, fewer questionable OVER bets

### IP regression added to K-prop model
- **File:** prop_model.py
- **Changes:** REGRESSION_STARTS_IP=15, regresses pitcher avg IP toward league average for small samples
- **Why:** Pitchers with few starts had noisy IP projections
- **Expected impact:** Better K projections for early-season pitchers

### Pitcher deduplication fix
- **File:** prop_model.py
- **Changes:** Added seen_pids set to prevent duplicate pitcher entries
- **Why:** Chase Burns and Foster Griffin appearing twice in results
- **Expected impact:** Clean results, no duplicate bets

### Both-sides conflict prevention
- **File:** prop_model.py
- **Changes:** Added pitcher_sides tracking, skip if already bet other side
- **Why:** Patrick Corbin was getting UNDER 4.5 AND OVER 4.5 -- guaranteed vig loss
- **Expected impact:** Eliminate guaranteed-loss bets

### Daily exposure cap added
- **File:** prop_model.py
- **Changes:** MAX_DAILY_EXPOSURE=0.25 (25% of bankroll per day)
- **Why:** $2,428 wagered on $3,000 bankroll (81%) in one day
- **Expected impact:** Risk management, survive bad days

### K-prop grading fixed (live feed API)
- **File:** prop_model.py
- **Changes:** Switched from schedule?hydrate=boxscore to /api/v1.1/game/{gpk}/feed/live
- **Why:** The hydrate endpoint doesn't return boxscore data
- **Expected impact:** K-props actually get graded

### Second daily pipeline run added
- **Crontab:** Added 20:00 UTC run
- **Why:** Capture pre-game line movements
- **Expected impact:** More current odds for edge detection

## 2026-04-17

### PnL field added to game model grading
- **File:** paper_trader.py
- **Changes:** grade_bets() now writes pnl field to each bet on grading
- **Why:** All 28 graded bets had $0 PnL -- couldn't analyze per-bet performance
- **Expected impact:** Accurate per-bet tracking

### Date field backfilled on all bets
- **File:** paper_trader.py + manual backfill script
- **Changes:** Extracts date from logged_at or pick_id
- **Why:** No date field meant couldn't filter or analyze by day
- **Expected impact:** Daily performance tracking possible

### Grading moved to 04:30 UTC
- **Crontab:** Changed from 22:43 to 04:30 UTC
- **Why:** West coast games don't finish until ~03:00 UTC. Old time missed late games.
- **Expected impact:** All games graded same night

### Autonomous analyst system deployed
- **Files:** state/, sessions/, analysis/ directories + cron schedule
- **Why:** No continuous monitoring or improvement was happening between sessions
- **Expected impact:** 24/7 analytical coverage, continuous model improvement

### K-prop model None handling fix
- **File:** prop_model.py
- **Changes:** Added None checks for pitcher_k9 and pitcher_ip fallback values
- **Why:** Pitcher with no stats data (Matt Waldron) caused TypeError crash, blocked all K-prop generation
- **Expected impact:** K-prop model runs even when pitcher stats are missing

### Session launcher mkdir fix
- **File:** sessions/run-session.sh
- **Changes:** Added `mkdir -p logs/sessions` at start
- **Why:** Morning session at 12:00 UTC failed silently because logs/sessions/ didn't exist yet
- **Expected impact:** Autonomous sessions will create their log directory if needed

### Hard Rock Bet research completed
- **File:** analysis/hard-rock-bet-research.md
- **Why:** Braxton lives in Florida where only Hard Rock Bet is legal. Must validate our model against HRB's actual lines.
- **Expected impact:** Pipeline evolution to source and compare HRB odds; adjusted edge thresholds for higher vig

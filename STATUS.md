# Sports Edge - Status (Single Source of Truth)

Last verified: 2026-05-04

## Active Markets (MLB only)

| Market | Status | Record | ROI | Sample | Methodology |
|--------|--------|--------|-----|--------|-------------|
| Total Bases (UNDER) | ACTIVE | 68W-34L (66.7%) | +11.9% | n=102 | OddsTrader EV% >= 10%, Pinnacle no-vig benchmark, graded vs MLB Stats API box scores. 15/15 spot-checks passed May 4. |
| Pitching Hits Allowed | ACTIVE (filtered) | 18W-12L (60.0%) | +4.5% | n=30 | u4.5 or tighter only. Needs more data. |
| Total Earned Runs | ACTIVE | 2W-1L (66.7%) | +11.9% | n=3 | Too small to evaluate. |

## Disabled Markets

| Market | Record | Why Disabled | Re-enable Criteria |
|--------|--------|-------------|-------------------|
| Total Strikeouts | 12W-13L (48.0%) | -11.4% ROI (n=25) | Positive ROI at n>=50 |
| Player to hit a RBI | 11W-28L (28.2%) | -26.0% ROI (n=39) | Never - structural disadvantage |
| NHL (all) | N/A | Braxton directive Apr 29 | Braxton decision only |

## Measurement Infrastructure

- **Ledger**: `data/oddstrader_sim_ledger.json` (216 bets, unified schema with side/line/odds)
- **Grader**: `grade_oddstrader.py` (AB=0 DNP check added May 4)
- **CLV capture**: `clv_capture.py` (cron at 17:25 + 22:55 UTC, collecting from May 5)
- **Spot-check**: 15/15 passed on May 4 (10 TB + 5 non-TB, verified vs MLB Stats API)

## Known Issues

1. MLB totals backtest (`mlb_model.py`) has look-ahead leak in feature pipeline. +7.83% ROI is uninterpretable. Fix: thread as_of_date through mlb_data_pipeline.py.
2. Batter prop backtest "ROI" was a discrimination test, not real ROI. Renamed May 4.
3. CLV not yet collecting - starts May 5. Need n>=30 with positive median CLV to confirm edge.
4. No real-money bets placed yet. Paper only.

## Cron Schedule (all times UTC)

| Time | Script | What |
|------|--------|------|
| 11:00 | refresh_2026_logs.py | Refresh season data |
| 16:00 | oddstrader_scraper.py | Morning scrape + bet logging |
| 17:25 | clv_capture.py | Closing lines before afternoon games |
| 19:00 | oddstrader_scraper.py | Pre-evening scrape |
| 22:00 | oddstrader_scraper.py | Evening scrape |
| 22:55 | clv_capture.py | Closing lines before night games |
| 04:30 | grade_and_log.sh | Grade yesterday's bets |

## Legacy (Archived to disabled/)

- `prop_grader.py` - old grader, no side/line fields
- `prop_ledger.json` - 1,126 entries, unverifiable OVER/UNDER P&L
- `STRATEGIC-MEMO.md` - stale, contradicts code
- `AUDIT-RESULTS.md` - claimed fixes that weren't deployed

## Key Files

| File | Purpose |
|------|---------|
| `oddstrader_scraper.py` | Scrapes OddsTrader +EV props, logs to sim ledger |
| `grade_oddstrader.py` | Grades bets against MLB Stats API box scores |
| `clv_capture.py` | Captures closing lines for CLV measurement |
| `mlb_batter_prop_model.py` | Walk-forward batter projection model (NegBin) |
| `mlb_model.py` | DC + Poisson + XGBoost game totals (leak in backtest) |
| `mlb_data_pipeline.py` | Feature pipeline (needs as_of_date fix) |
| `data/oddstrader_sim_ledger.json` | Single source of truth for all bets |

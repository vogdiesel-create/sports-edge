# Sports Edge Session Notes

## Apr 24 2026: Grading Results (59 OddsTrader Sim Picks)

### Key Finding: TB and K Markets Are Profitable
- **Total Bases**: 9W-2L (81.8%), +$243.33, **+97.3% ROI**
- **Total Strikeouts**: 3W-1L (75%), +$96.06, **+90.9% ROI**
- **Pitching Hits Allowed**: 2W-3L, -$105.67 (small sample, keep monitoring)
- **Player to hit RBI**: 11W-28L (28.2%), -$406.49, -37.6% ROI (ALREADY DISABLED)

Overall: 25W-34L, -$172.77, -11.2% ROI (dragged by RBI which is now filtered)
TB + K combined: 12W-3L, +$339.39, **+94% ROI**

### Actions Taken
- RBI filter was already in place (disabled Apr 20)
- No new RBI bets since filter applied (verified)
- 0 pending ungraded bets
- Next: Need 50+ more graded TB/K picks for statistical significance

### Game Line Grading
- 1 gradeable game: Dallas @ Minnesota total over 6 -> W (+$19.05)
- 7 other picks: games not found/incomplete
- Running bankroll: $914.05 (29 total bets)

### OddsTrader Scraper Status
- 0 props found today (too early, games start ~7PM ET)
- Cron scheduled for 4pm, 7pm, 10pm ET

---

# Sports Edge Session Notes - Apr 20 2026 (Session 2)

## Session Summary: NegBin Distribution Replacement

### What Changed This Session
3 code changes across 2 files:

1. `mlb_prop_model.py`: Added NegBin functions, backtest shows Poisson is still better for K props (kept Poisson)
2. `mlb_batter_prop_model.py`: Replaced Poisson with NegBin for TB/RBI/HR/runs/SB
3. `mlb_batter_prop_model.py`: Removed emergency calibration multipliers (0.50-0.65x) -- NegBin handles overdispersion directly

---

## NegBin Implementation Results

### Empirical Overdispersion (variance/mean from 221K+ batter games, 23K+ pitcher starts)
| Stat | Overdispersion | Action |
|------|---------------|--------|
| Total Bases | 2.122 | NegBin (massive improvement) |
| RBI | 1.558 | NegBin (near-perfect calibration) |
| Pitcher Ks | 1.173 | Kept Poisson (NegBin worse -- model already captures between-pitcher variance) |
| Home Runs | 1.007 | Poisson-equivalent (disabled anyway) |
| Runs | 0.978 | Underdispersed (disabled anyway) |
| Hits | 0.863 | Underdispersed (binomial, not Poisson) |

### Key Finding: K Props Stay Poisson
Backtest (21,585 starts) showed NegBin INCREASES calibration error at every line:
- Line 3.5: Poisson +0.020 err vs NegBin +0.035 err
- Line 5.5: Poisson +0.007 err vs NegBin +0.008 err (close)
- Line 7.5: Poisson -0.012 err vs NegBin -0.022 err

Why: The 1.17 unconditional overdispersion is mostly between-pitcher variance that the projection model already captures. Conditional on the projection, K counts are approximately Poisson.

### Batter Prop Calibration: Before vs After
| Market | Poisson Bias | NegBin Bias | Improvement |
|--------|-------------|-------------|-------------|
| 2+ TB | +20% | **-0.5%** | 40x better |
| RBI >= 1 | +14% | **-0.1%** | 140x better |
| Hit >= 1 | +12% | **-6.2%** | 2x better |
| 2+ Hits | +10% | **-2.3%** | 4x better |

### Simulated ROI (Walk-Forward Backtest, 98K game-projections)
| Market | Edge Threshold | Bets | Actual WR | ROI |
|--------|---------------|------|-----------|-----|
| 2+ TB | 5%+ | 29,748 | 39.2% | **+17.5%** |
| 2+ TB | 10%+ | 15,375 | 40.4% | **+21.1%** |
| RBI >= 1 | 5%+ | 29,927 | 32.6% | **+15.9%** |
| RBI >= 1 | 10%+ | 16,137 | 33.5% | **+19.1%** |
| Hit >= 1 | 5%+ | 12,744 | 64.9% | **+11.1%** |

### Zero-Inflation: Not Needed
Tested ZI 0.0 to 0.10 for TB. ZI=0.0 gives best calibration (-2.6% err). Any ZI overcorrects. NegBin alone handles the excess zeros adequately.

### Calibration Multipliers Removed
Old emergency corrections (0.50-0.65x) were compensating for Poisson overestimation. NegBin fixes the root cause. Removed all multipliers except a conservative 0.85x for hits (which uses binomial, not NegBin).

---

## Previous Session Changes (kept)
- K prop OVERs disabled
- OddsTrader filters: 10%+ EV, no NHL goals (31% ROI)
- Batter HR/SB/Runs markets disabled
- K prop bias correction removed (raw model has +0.02 bias)

## Log5 Matchup Formula (Implemented)
Replaced crude `opp_k_rate / league_avg` scalar with proper log5:
`matchup_K% = (P * B / L) / (P * B / L + (1-P) * (1-B) / (1-L))`

Results: Bias improved from +0.02 to -0.01. MAE/RMSE unchanged (improvement is in individual matchup accuracy, not aggregate).

Note: Initial implementation used FanGraphs 0.84/0.16 coefficients (2002-2012 era, lower league K%). Updated to proper log5 with current 22.2% league K rate.

## TTO Adjustment (Deferred)
Attempted blanket innings-based TTO (1.10/1.00/0.85 multipliers). Two problems:
1. Normalizing to preserve total Ks = no net effect
2. Not normalizing = +0.20 bias (double-counts TTO already embedded in K/9)

Real TTO value requires per-lineup-slot modeling (which batters face TTO1 vs TTO2 vs TTO3). Deferred to future iteration.

## Edge Thresholds Restored
- Batter prop edge threshold: 8% -> 5% (NegBin now handles calibration)
- TB and RBI markets: re-enabled at correct calibration (no multipliers)

## CRITICAL: Prop Ledger Audit (Session 2)

**The 93% K prop WR and 92% hits allowed WR were based on broken data.**

Full audit revealed:
- 67% of bets had `actual=0` (grading never checked box scores)
- No line/side info stored (can't determine if a pick won or lost)
- Spot-checks against MLB API show real actuals differ from ledger
- Only 3 K prop bets had real actuals: 1W-2L (33% WR)

The old prop_ledger.json is unreliable. New simulation ledger built with proper
line/side tracking. Real validation starts now.

See: AUDIT-RESULTS.md for full details.

## OddsTrader Today (Apr 20)
38 actionable picks scraped (now logged to sim ledger with Kelly sizing):
- 2 Total Strikeouts
- 3 Pitching Hits Allowed
- 9 Total Bases, 24 RBI

## Post-Audit Cleanup (Apr 20, Session 3)
1. Removed 871 migrated broken bets from sim ledger (kept 38 new picks only)
2. Reset bankroll to clean $5,000
3. Fixed `prop_pick_tracker.py`: added `hits_allowed` and `earned_runs` fields from pitching stats
4. Fixed `grade_oddstrader.py`: pitching hits allowed now grades correctly against MLB API
5. Fixed `grade_oddstrader.py`: earned runs grading now works

## Next Steps
1. Collect live grading data with NegBin + Log5 model (validate backtest ROI)
2. ~~Increase OddsTrader scan frequency~~ DONE: cron 3x/day (noon, 3pm, 6pm ET)
3. TTO per-lineup-slot model (deeper refactor for K props)
4. Implement calibration monitoring (ECE, Brier Score weekly)
5. ~~Build automated daily pipeline~~ DONE: `daily_runner.py`
6. Wait for 50+ properly graded OddsTrader picks before making any WR claims

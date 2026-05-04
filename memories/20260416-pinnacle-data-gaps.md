# Pinnacle Closing Line Data Gap Analysis - 2026-04-16

## Current Inventory (game_lines.db)

### NHL (6,559 total unique games)
| Season | Games | Status |
|--------|-------|--------|
| 2019-20 | 0 | MISSING - entire season |
| 2020-21 | 963 | Complete (COVID shortened) |
| 2021-22 | 1,426 | Complete |
| 2022-23 | 1,383 | Complete |
| 2023-24 | 1,403 | Complete |
| 2024-25 | 1,384 | Complete (season ending) |

### MLB (4,510 total unique games)
| Season | Games | Status |
|--------|-------|--------|
| 2021 | 1,364 | Complete |
| 2022 | 266 | MAJOR GAP - only Apr data, May-Oct missing |
| 2023 | 1,445 | Complete |
| 2024 | 1,433 | Complete |
| 2025 | 0 | Season just started (Apr 2025) |

## Key Finding
BettingIsCool returns ~1,400 games per MLB season (not 2,430). This is the Pinnacle-covered subset.

## API Details
- BettingIsCool API: pk_da1eb76a9e24b77c360874fc0d1e57b677bf85fcbeea5e33
- Rate limit: 50 req/min, 5,000 req/day (Starter tier)
- Quota resets: midnight UTC daily
- NHL league_id: 1456, MLB league_id: 246

## Backfill Plan
- Created: backfill_pinnacle_gaps.py (targets only missing data)
- Estimated API calls: ~3,573 (fits in one daily quota)
- Scheduled to run at 00:05 UTC 2026-04-17 (PID 40524)
- Gaps targeted: NHL 2019-20, MLB 2022 May-Oct, MLB 2025

## After Backfill Expected Totals
- NHL: ~7,900 unique games (6 full seasons)
- MLB: ~5,600 unique games (4 full seasons + partial 2025)

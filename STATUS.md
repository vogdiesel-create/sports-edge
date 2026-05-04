# Sports Edge - Status Report

## Dashboard
**Live**: https://sports-edge-dashboard.netlify.app

## Architecture (V3)

### Data Pipeline
```
OddsTrader (Playwright scrape) -> 400+ props with model EV%
SBR Scrape (requests) ----------> 10+ books game lines with Pinnacle
Bovada API (free) --------------> 800+ prop O/U lines for devigging
FanDuel API (free) -------------> Player props + correlation alerts
                                      |
                              smart_scanner.py (unified pipeline)
                                      |
                              data/unified_scan.json -> dashboard
                                      |
                  prop_grader.py + auto_grader.py (verify picks)
                                      |
                              data/prop_ledger.json (P&L tracking)
```

### Proven Edge: Game Lines
- **Source**: SBR scrape -> Pinnacle devig -> find soft book mispricing
- **CLV**: +2.5% average, 62% positive rate (8 checked picks)
- **Graded bets**: 2W/2L, +$4 P&L (small sample)
- **Filter**: 3-6% edge, exclude bodog, tier by book profitability
- **Status**: RUNNING in background every 60 min

### Unverified: OddsTrader Prop Picks
- **Source**: OddsTrader page scrape (Playwright)
- **What we get**: 200+ "plus EV" props with cover probability and best odds
- **CRITICAL FINDING**: OddsTrader's EV% = cover_prob - implied_prob (probability edge, NOT monetary EV)
- **CRITICAL FINDING**: Cover probabilities appear inflated (39% for a defenseman to score = 2x historical rate)
- **CRITICAL FINDING**: No Pinnacle prop data on OddsTrader (only DraftKings)
- **Status**: Logging all picks, will grade after games complete tonight

### Cross-Validation Engine (NEW)
- **Source**: Bovada O/U lines -> power method devig -> cross-ref OddsTrader
- **CRITICAL FINDING**: Only 3 of 209 OddsTrader picks confirmed by Bovada devig
- **103 DISAGREED**: Bovada fair odds say these OT picks are NOT +EV
- **Confirmed picks**: Ohtani hits (+20.4% edge), Hoerner RBI (+7.5%), Turner RBI (+2.1%)
- **Implication**: OddsTrader's model is likely unreliable for most picks

### Pinnacle Prop Data (PENDING)
- **OddsPapi.io**: Free tier, 250 req/month, includes Pinnacle props
- **Status**: Client built (`oddspapi_client.py`), needs API key signup
- **Action**: Sign up at oddspapi.io/en/sign-up (free, no credit card)
- **Impact**: Would give us REAL Pinnacle prop devigging (game-line quality for props)

## Key Learnings

### Game Lines (PROVEN)
1. Edge 2-3% = noise (-25.8% ROI). Need 3%+ minimum.
2. Edge >6% = stale/incorrect line. Cap at 6%.
3. Bodog is net negative. Exclude.
4. NHL most profitable sport for game lines.
5. +2.5% CLV avg (8 picks), 62% positive. Real edge confirmed.

### Props (UNVERIFIED - GRADING IN PROGRESS)
1. OddsTrader EV% is NOT true monetary EV. It's probability edge.
2. No Pinnacle prop data available on OddsTrader - model-based only.
3. Cover probabilities look inflated vs historical rates.
4. Need 30+ graded bets to judge model accuracy.
5. Will know after tonight's games complete.

### Data Sources
| Source | Status | Data |
|--------|--------|------|
| SBR scrape | ACTIVE | 10+ books, game lines, Pinnacle included |
| OddsTrader scrape | ACTIVE | 200+ props, model-based EV (unverified) |
| Bovada API | ACTIVE | 800+ prop O/U lines, free |
| FanDuel API | INTERMITTENT | Player props, correlation alerts |
| NHL API | ACTIVE | Free boxscores for grading |
| MLB Stats API | ACTIVE | Free boxscores for grading |
| the-odds-api | EXHAUSTED | 0/20K remaining |
| OddsPapi.io | PENDING SIGNUP | 350+ books incl Pinnacle, free 250 req/mo |

## Files

| File | Purpose |
|------|---------|
| `smart_scanner.py` | Unified pipeline (game lines + OT props + FD + grading + CLV) |
| `oddstrader_scraper.py` | OddsTrader Playwright scraper for +EV props |
| `prop_grader.py` | Grade prop picks against actual results (NHL/MLB APIs) |
| `devig_engine.py` | Independent devigging from Bovada O/U lines |
| `auto_grader.py` | Grade game line picks against actual results |
| `clv_tracker.py` | Closing line value tracking |
| `data_collector.py` | Historical data accumulation (SQLite) |
| `multi_book_props.py` | Cross-book prop comparison (Bovada vs FanDuel) |
| `grade_all.py` | Combined grading runner (props + game lines) |
| `dashboard.html` | Web dashboard (Netlify) |
| `game_line_scanner.py` | SBR-based cross-book scanner |

## Background Processes
- Smart Scanner: Every 60 min, 8 cycles (PID in process)
- Data Collector: Every 15 min (if running)

## Next Steps (Priority Order)
1. **Grade tonight's props** - Run grade_all.py after MLB games complete (~midnight ET)
2. **Accumulate grading data** - Need 30+ graded OT props to judge model accuracy
3. **Fix Bovada market matching** - Match Bovada devigged lines to correct OT markets
4. **If OT model works** -> Scale up, add more sports
5. **If OT model fails** -> Build own devigging from Bovada + FanDuel consensus
6. **NHL SOG/assists/points** - These markets missing from OddsTrader scrape (dropdown issue)

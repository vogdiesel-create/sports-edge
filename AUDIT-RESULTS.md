# OddsTrader Prop Ledger Audit - Apr 20 2026

## FINDING: Historical prop_ledger.json is unreliable

### What we claimed
- 33 K prop bets at 93.9% WR
- 25 pitching hits allowed at 92.0% WR
- 872 total bets, +$125 profit

### What the audit found

**67% of bets (580/872) have `actual=0`** -- the grading process never recorded what actually happened. The `won: true/false` flags were set without verifying against box scores.

**Spot-check against MLB Stats API:**
- Will Warren (Apr 13, LAA @ NYY): ledger says actual=0, won=true. Real: 6 Ks.
- Tyler Glasnow (Apr 17, LAD @ COL): ledger says actual=0, won=true. Real: 7 Ks.
- Roki Sasaki (Apr 19, LAD @ COL): ledger says actual=0, won=true. Real: 2 Ks.

**We can't verify these bets because:**
1. No line/side information stored (was it OVER 4.5? UNDER 6.5? No idea)
2. Without knowing the line, we can't determine if 6 Ks was a win or loss
3. The grading process that set `won: true` was clearly broken

**Only 3 K prop bets have real actuals**: 1W-2L (33% WR)

### Verified results (actual > 0 only)
The 292 bets with real actuals show inverted patterns:
- Total Hits: 6W-117L (4.9% WR) -- grading may have been inverted
- RBI: 71W-0L (100%) -- suspicious, likely grading bug
- K props: 1W-2L (33% WR on 3 bets)

### Root Cause
The OddsTrader scraper (`oddstrader_scraper.py`) saves props to `oddstrader_ev_props.json` but does NOT record line/side info in the prop_ledger. A separate process (likely `grade_all.py`) attempted to grade but didn't have the information needed.

### Fix Applied
New simulation ledger (`oddstrader_sim_ledger.json`) captures:
- Side (over/under)
- Line value (4.5, 5.5, etc.)
- Kelly-sized wagers
- 15% daily exposure cap
- Proper grading via `grade_oddstrader.py`

### What we actually know
- OddsTrader's Pinnacle devig methodology is sound (structural edge, not prediction)
- The CONCEPT of pitching prop edges is supported by research
- But we have ZERO verified win rate data on historical OddsTrader picks
- All confidence numbers I reported earlier were based on broken data
- Real validation starts now with the new sim ledger

### Going Forward
- Old prop_ledger.json is archived, not used for decisions
- New sim ledger is the only source of truth
- Need 50+ properly graded pitching prop bets before making any WR claims
- Every bet must have: player, market, side, line, odds, actual result

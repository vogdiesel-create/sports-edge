# Hard Rock Bet - Florida Execution Research

**Date**: 2026-04-17
**Status**: Research complete, action items identified

## Key Findings

### Markets: ALL AVAILABLE
- MLB game totals (over/under): YES
- NHL game totals: YES
- Pitcher strikeout props (over/under on Ks): YES
- Full player prop menu for MLB and NHL

### Odds API: SOLVABLE ($59/mo)
- The Odds API (the-odds-api.com) covers Hard Rock Bet FL explicitly
- MLB K-props confirmed available via API
- Free tier: 500 credits/mo; $59/mo: 100K credits (recommended)
- Pinnacle NOT on The Odds API -- keep our existing Pinnacle feed separate

### Line Quality: HIGHER VIG (25-30 cent lines on MLB totals)
- Standard book: -110/-110 (20 cent line)
- Hard Rock typical: -115/-105 or -130/+105 (25-30 cent lines)
- Kambi odds engine (professional, algorithmic) -- center lines are decent
- Monopoly = no competitive pressure to sharpen
- 51% effective tax rate passed to bettors via wider spreads

### Promotions: 10x 100% PROFIT BOOSTS on signup
- Available through June 30, 2026
- Each boost doubles winnings on a qualifying bet
- Massive +EV -- use on highest-confidence plays

### Bet Limits: AGGRESSIVE LIMITING OF WINNERS
- Reports of $10 max bet limits after winning streaks
- BBB complaints about accounts restricted/suspended after winning
- Standard US book playbook, made worse by monopoly status
- Mitigation: small bets, mix in recreational activity, use promos

## Impact on Our Model

### Edge Thresholds Must Increase
- Game totals: minimum 3-4% edge (was 2%) to overcome HRB vig
- K-props: minimum 5%+ edge (props have even wider juice)
- With profit boosts: any +EV play is a bet

### Pipeline Changes Needed
1. Subscribe to The Odds API ($59/mo) for HRB odds
2. Build comparison engine: model fair value vs HRB actual odds
3. Paper bet on HRB lines for 2-3 weeks before going live
4. Adjust edge thresholds for HRB vig structure

### Execution Strategy
- Start with $25-50 bets to avoid early limiting
- Use all 10 profit boosts on strongest plays first
- Diversify across prop types (don't just hammer K-props)
- Mix in occasional recreational bets to look casual
- Avoid betting immediately when lines post

## Action Items
1. [ ] Braxton: Sign up for Hard Rock Bet, claim 10x profit boosts
2. [ ] Subscribe to The Odds API ($59/mo tier)
3. [ ] Integrate HRB odds into edge detection pipeline
4. [ ] Adjust minimum edge thresholds for HRB vig
5. [ ] Paper trade on HRB lines for validation period
6. [ ] Research Kambi odds patterns for systematic edge opportunities

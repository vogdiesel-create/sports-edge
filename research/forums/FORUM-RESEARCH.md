# Sports Betting Forum Research: Hard-Won Knowledge from Experienced Bettors

**Date**: 2026-04-20
**Agent**: web-researcher
**Focus**: What experienced bettors say actually works (and doesn't) for model building, MLB props, and sustainable profitability

---

## Executive Summary

Researched sharp bettor accounts (Zerillo, Captain Jack, Rufus Peabody, Spanky), betting forums (Covers, SBR, Two+Two, betting-forum.com), and Pinnacle's research library. Three dominant themes emerged:

1. **CLV is the only reliable short-term measure of edge** - Everything else is noise until 1000+ bets
2. **Prop markets have real inefficiency but brutal structural limits** - $200-500 max bets, fast limiting, high juice
3. **Overfitting is the #1 killer of promising models** - Backtested edges routinely collapse in production

---

## FINDINGS

---

### 1. CLV (Closing Line Value) Is King

**Tag**: TECHNIQUE / VALIDATION

**Source**: Pinnacle Betting Resources - https://www.pinnacle.com/betting-resources/en/educational/what-is-closing-line-value-clv-in-sports-betting

**Key Insight**: CLV is universally accepted by professional bettors as THE measure of edge. If you consistently beat the closing line at Pinnacle, you have a real edge. Period.

**Specific Data Points**:
- +1-2% CLV = you are beating the market (good sign)
- +5% CLV = excellent, strong long-term edge
- CLV stabilizes much faster than actual results - as few as 50 bets can show statistical significance
- Pinnacle's closing line is the benchmark because they don't limit winners, so their lines incorporate maximum sharp information

**Why This Matters For Us**: Our model MUST track CLV against Pinnacle closing lines. ROI alone is meaningless in small samples. If we're not beating Pinnacle's close, we don't have an edge - we have variance.

**Credibility**: HIGH - This is consensus among every credible source examined. No one disputes CLV's importance.

---

### 2. The Overfitting Trap - Why Backtested Models Fail

**Tag**: WARNING / TECHNIQUE

**Source**: betting-forum.com thread + Great Bets backtesting guide
- https://www.betting-forum.com/threads/the-overfitting-problem-why-backtested-betting-systems-fail-in-production.47444/
- https://www.greatbets.co.uk/how-to-backtest-a-sports-betting-strategy-without-overfitting/

**Key Insights**:

**Minimum Sample Sizes**:
- 200 bets = INSUFFICIENT for edge detection (uncertainty too wide)
- 1,000 observations = minimum for initial evidence
- 5,000 observations = publication-level confidence
- A 54% win rate on 200 bets cannot be distinguished from variance

**Red Flags for Overfitting**:
- Backtest showing >10% ROI over large sample (legitimate edges are single-digit ROI)
- Smooth equity curve with minimal drawdowns
- Extremely high win/loss ratios
- Using season-end stats in mid-season predictions (look-ahead bias)
- Testing 10,000 parameter combinations without significance adjustment (Bonferroni corrections needed)

**Characteristics of Real Signal**:
- Must have a MECHANISTIC EXPLANATION (not just "the data says so")
- Robust across parameter variations (small changes don't kill it)
- Shows natural decay over time (markets adapt)
- Single-digit ROI, not double-digit sustained performance

**Proper Testing Protocol**:
- Walk-forward testing: Train on period 1, test on period 2, then train on 1+2, test on 3
- Out-of-sample test gets ONE shot - if it fails, don't tweak and re-run
- Must demonstrate positive CLV against closing odds (backtest profit + negative CLV = overfitting red flag)

**Why This Matters For Us**: CRITICAL. Our model went from 109 to 3641 training games and calibration from 66 to 2187. We need to verify this isn't just fitting noise. Walk-forward testing and CLV tracking are non-negotiable.

**Credibility**: HIGH - This is basic statistical methodology, confirmed across multiple sources.

---

### 3. MLB Strikeout Prop Model Features

**Tag**: TECHNIQUE

**Sources**:
- https://aibettingedge.com/using-in-zone-whiff-rate-to-predict-pitcher-strikeout-mlb-prop-bets/
- https://thisdayinbaseball.com/strikeout-props-betting-how-to-identify-elite-k-over-under-spots/
- Covers MLB prop guide

**Key Model Features (Consensus)**:

**Pitcher Metrics (Primary)**:
- K% (strikeout rate) - most important single metric
- SwStr% (swinging strike rate) - measures whiff generation
- CSW% (called strikes + whiffs) - more comprehensive than SwStr%
  - Elite K pitchers: CSW% above 30%
- In-Zone Whiff Rate (IZWR) - percentage of in-zone swings that miss
- Pitch count limits / workload management status

**Opposing Lineup Factors**:
- Team K% vs RHP/LHP (split-specific)
  - Teams K-ing 25%+ = prime over targets
- O-Swing% (chasing rate outside zone)
- Z-Contact% (ability to make contact on strikes)
- Lineup construction for that day (not season averages)

**External/Context Factors**:
- Umpire strike zone tendencies
- Ballpark foul territory (more foul territory = more foul outs, fewer Ks)
- Weather conditions affecting pitch movement
- Day/night split performance
- Rest days between starts

**Why This Matters For Us**: Feature checklist for our K prop model. We should prioritize CSW%, IZWR, and opponent K% splits. Day-of lineup and umpire assignment are the edge factors most casual models miss.

**Credibility**: HIGH - These are standard sabermetric inputs, well-documented.

---

### 4. Prop Market Structure: Real Edge, Brutal Limits

**Tag**: WARNING / TECHNIQUE

**Sources**:
- MLB official announcement on pitch-level markets
- Multiple forum discussions
- https://www.oddsshopper.com/articles/betting-101/why-sportsbooks-limits-ev-bettors-and-what-to-do-about-it-y10

**Key Realities**:

**Bet Limits**:
- Strikeout props: typically $200-500 max at most books
- Compare to sides/totals: $5,000-50,000+ limits
- MLB pitch-level markets capped at $200 (MLB/sportsbook agreement)
- Props have HIGHER juice than main markets

**The Limiting Problem**:
- Consistent +EV betting on props gets you limited FAST
- Player props and alt lines trigger restrictions faster than main markets
- Sportsbooks monitor: bet timing, niche market success, sharp line patterns
- Once limited, options are: P2 accounts (gray area), selling picks, or finding new books

**Mitigation Strategies (from experienced bettors)**:
- Occasionally place recreational-looking bets (parlays, SGPs)
- Bet mainstream markets at peak hours
- Increase bet sizes gradually, not overnight
- Maintain multiple book accounts as backups
- Target books that are slower to limit (Circa, Pinnacle welcome winners)

**The Math Problem**:
- Even with a 5% edge on props, at $500 max bet = $25 expected value per bet
- Need massive volume to make real money
- $70K season on props alone would require ~2,800 bets at $500 avg with 5% edge
- That's ~17 bets per day across a 162-game season

**Why This Matters For Us**: This is the scalability constraint. A great K model might prove edge but not generate life-changing money on props alone. We either need massive multi-book volume or need to translate prop edge into side/total insights where limits are higher.

**Credibility**: HIGH - Structural reality confirmed by every source.

---

### 5. Top-Down vs. Bottom-Up Betting (Two Schools)

**Tag**: TECHNIQUE / VALIDATION

**Sources**:
- Spanky/Unabated: https://unabated.com/articles/how-do-sharps-win-at-sports-betting
- https://www.bettored.org/post/case-study-spanky-top-down-betting

**Top-Down (Spanky's Method)**:
- "The market is correct. I look for where it's mispriced temporarily."
- Monitor dozens of books in real-time for line discrepancies
- When sharp book (Pinnacle, Asian books) shows -7 and soft books show -6, bet the -6
- Watch for steam moves (coordinated sharp action) and follow on slower books
- College sports preferred (more games = more pricing errors)
- CLV is the ONLY metric that matters: "If you beat the closing number, you're going to make money long term"

**Bottom-Up (Model Building)**:
- Build statistical models from player/team data
- Generate your own probability estimates
- Compare your odds to market odds for +EV identification
- Requires domain expertise + statistical sophistication
- Risk: overfitting, look-ahead bias, model decay

**Which Actually Works?**
- Spanky has 20+ years of profitable track record with top-down
- Bottom-up modelers rarely share results (survivorship bias concern)
- Consensus: top-down is more accessible, bottom-up has higher ceiling if done right
- Many pros use BOTH: model generates ideas, market confirms/denies

**Why This Matters For Us**: We're bottom-up modelers. We should add a top-down layer: compare our model output to sharp market lines. If our model says over 5.5 K but Pinnacle's line is already priced efficiently at 5.5, there may be no edge even if our model is "right."

**Credibility**: HIGH - Spanky is universally respected, methodology is transparent.

---

### 6. Kelly Criterion: The Real Version vs. The Simplified Trap

**Tag**: TECHNIQUE / WARNING

**Source**: Pinnacle
- https://www.pinnacle.com/betting-resources/en/betting-strategy/the-real-kelly-criterion-a-critical-analysis-of-the-popular-staking-method/hzkjtfcb3knyn9cj
- https://www.pinnacle.com/betting-resources/en/educational/part-two-toward-a-theory-of-everything/uwc25wvpppzj997d

**Key Warnings**:
- The "edge/odds" simplified Kelly formula is WRONG for multiple simultaneous bets
- When betting correlated outcomes (like ML + total in same game), simplified Kelly miscalculates
- When placing multiple independent bets simultaneously, simplified Kelly can recommend >100% of bankroll
- Proper Kelly requires: listing all outcome combinations, calculating end-bankroll for each, maximizing log-bankroll

**Practical Advice**:
- Use fractional Kelly (1/4 to 1/2 Kelly) to account for edge uncertainty
- "Certainty equivalent" calculation shows risk-free value of your position
- Bayesian updating of edge estimates is more realistic than fixed-edge Kelly
- Pinnacle's "Theory of Everything" article unifies: fractional Kelly + regression to market + CLV + parameter uncertainty

**Why This Matters For Us**: If we're sizing bets, do NOT use simple Kelly. Use fractional Kelly (quarter-Kelly recommended for new models with uncertain edge) until we have 1000+ bet CLV data.

**Credibility**: HIGH - Pinnacle's articles written by academics/ex-traders.

---

### 7. The +EV Trap: Diminishing Returns on Crowded Edges

**Tag**: WARNING

**Source**: 8rainstation.com (experienced sharp's journey)
- https://8rainstation.com/blog/advice-from-my-mistake-filled-journey-to-becoming-a-sharp-sports-bettor-mastering-one-sided-line-devigging

**Key Insight**: "Many bettors chase the same positive EV edges, which leads to diminishing returns."

**The Problem**:
- Tools like OddsJam surface the same +EV opportunities to thousands of subscribers
- When thousands of bettors hit the same line, books adjust instantly
- Edge evaporates before most people can bet
- Then you get limited for trying

**The Solution (Per This Sharp)**:
- Build PROPRIETARY models, don't rely on shared tools for edge detection
- Specialize deeply (this author: baseball, using 25 years of data analytics)
- Bet at sharp books (Circa, Pinnacle, Bet365) that welcome winners and offer larger limits
- Keep your best edges PRIVATE: "The more you distribute your edge, the less unique it becomes"

**Why This Matters For Us**: Our model IS proprietary. This is the right approach. Don't share methodology publicly. Don't rely on OddsJam for edge detection - use it only for odds comparison. Our edge comes from unique model outputs, not from arbitrage everyone can see.

**Credibility**: HIGH - Written by someone who went through the full journey, honest about failures.

---

### 8. Credibility Assessments

**Tag**: CREDIBILITY-CHECK

#### OddsJam
**Verdict**: Legitimate tool, but NOT an edge generator

- Real product: odds comparison, arbitrage finder, +EV identification across 150+ books
- User results range from $1,300-$2,900/month average (realistic) to $12K first month (outlier/marketing)
- **Critical Problem**: Surfaces the SAME edges to all subscribers = crowded trades = rapid limiting
- Best used as: odds comparison tool and execution platform, NOT as your edge source
- At $100-200/month subscription, ROI depends entirely on your bankroll and account access
- **Sources**: Trustpilot reviews, RotoWire, BetMetricsLab, CaanBerry

#### Captain Jack Andrews / Unabated
**Verdict**: LEGITIMATE - among the most credible voices in sports betting education

- 20+ years professional track record
- Co-founded Unabated with genuine sharp infrastructure (SpankOdds, odds screens)
- Philosophy: education over picks, approach over predictions
- "Master of Sports Betting" course ($12,000) - he's a guest lecturer, not the main instructor
- Not selling picks. Selling understanding. That's the key differentiator.
- Also featured on MasterClass alongside other verified pros
- **Risk**: Unabated subscription ($99/month) is reasonable for tools offered, but won't make you profitable alone
- **Sources**: Chicago Sun-Times profile, USBets, Gambling With An Edge

#### Spanky (Gadoon Kyrollos) / Unabated
**Verdict**: LEGITIMATE - verified professional with transparent methodology

- Sports Gambling Hall of Fame inductee (2025)
- Top-down methodology is well-documented and reproducible in principle
- Created SpankOdds for real-time line monitoring
- Hosts BetBash (networking convention, not a sales pitch)
- 20+ year professional track record, profiled in The Ringer, Review-Journal, etc.
- The Ringer's "Requiem for a Sports Bettor" documents his experience being kicked out of sportsbooks - the ultimate validation of winning
- **Sources**: Chicago Sun-Times, Las Vegas Review-Journal, The Ringer, GGB Magazine

#### Rufus Peabody / Massey-Peabody
**Verdict**: LEGITIMATE - academic rigor applied to betting

- Massey-Peabody ratings (with Wharton professor Cade Massey) are used by Unabated
- Published methodology: game grades that strip out luck using expected final scores
- "Beyond CLV" article introduces expected ROI as more sophisticated measure
- Power ratings available through Unabated subscription
- Academic credentials + profitable track record = rare combination
- **Sources**: Unabated articles, Power Rank

#### Sean Zerillo (Action Network)
**Verdict**: CREDIBLE content creator, model methodology partially public

- Daily MLB projections posted publicly on Action Network
- Payoff Pitch podcast covers strikeout prop methodology
- Joined by Sean Koerner for model-building episodes
- His model covers moneylines, totals, F5 innings, team totals, and K props
- Content is educational, not purely pick-selling
- **Limitation**: Works for Action Network (media company), so content serves subscriber growth
- **Sources**: Action Network, X/Twitter, YouTube

#### Claims of $70K+ MLB Seasons
**Verdict**: UNVERIFIED - no documented evidence found

- No published case studies with verified results
- Structurally plausible but requires: massive volume, multi-book access, no limiting
- At $500 avg bet and 5% edge: need ~2,800 bets = unsustainable on props alone
- More likely achieved on sides/totals where limits are higher
- Treat any such claim with skepticism unless CLV data is provided

---

### 9. Forum Intelligence: What Real Bettors Are Saying (2026 Season)

**Tag**: VALIDATION

**Source**: Covers MLB Betting Forum - https://www.covers.com/forum/mlb-betting-27

**Sharp Money Activity (Early 2026)**:
- March 29, 2026: 9 steam moves in one day, 7 on away side - "coordinated sharp attack on away teams"
- Result: 5W-4L (55.6%) - sharps winning but not dominating
- Indicates early-season home team overpricing (markets adjusting to new rosters)

**AI Model Claims on Forums**:
- One poster claiming 8-2-1 record with AI model, up 11+ units, claiming 30+ units last season
- ZERO verification provided, no CLV data, no sample size context
- This is exactly the kind of claim to be skeptical of (200 bets = meaningless sample)

**Why This Matters For Us**: Forum claims without CLV data are noise. But the structural insight (early-season market inefficiency, home team overpricing) is worth investigating with our model.

---

### 10. The "Theory of Everything" in Betting

**Tag**: TECHNIQUE

**Source**: Pinnacle - https://www.pinnacle.com/betting-resources/en/educational/part-two-toward-a-theory-of-everything/uwc25wvpppzj997d

**Framework** (unifies key concepts):
- **Fractional Kelly**: Account for uncertainty in your edge estimate
- **Regression to the market**: Your model's deviation from market should be discounted toward market price
- **CLV as validation**: Consistent positive CLV proves you're not just lucky
- **Parameter uncertainty**: Use Bayesian updating as you collect more data
- **The synthesis**: Your optimal bet size depends on how CONFIDENT you are in your edge, not just the edge itself

**Why This Matters For Us**: This is the intellectual framework we should operate within. Our model generates an edge estimate. We should:
1. Discount it toward market price (regression)
2. Size using fractional Kelly based on confidence
3. Track CLV to validate
4. Update confidence as sample grows

**Credibility**: HIGHEST - Academic-quality analysis from the one sportsbook everyone respects.

---

## SYNTHESIS: What We Should Do Based on This Research

### Immediate Actions
1. **Add CLV tracking** to every bet our model recommends (measure against Pinnacle closing line)
2. **Implement walk-forward testing** - not just backtest on full dataset
3. **Use quarter-Kelly sizing** until we have 500+ bets with CLV data
4. **Track these model features for K props**: CSW%, IZWR, opponent K% splits, umpire tendencies, day-of lineup

### Strategic Decisions
5. **Don't rely on OddsJam for edge** - use it only for odds comparison/execution
6. **Keep model methodology private** - proprietary edge erodes when shared
7. **Plan for limiting** - identify 5+ books, increase sizes gradually, mix in recreational-looking bets
8. **Consider adding top-down layer** - compare model output to Pinnacle sharp line before betting

### Reality Checks
9. **Prop limits constrain revenue** - even a perfect K model maxes out at ~$25 EV per $500 bet at 5% edge
10. **Need 1000+ bets minimum** before drawing conclusions about model quality
11. **Single-digit ROI is what real edges look like** - if backtest shows 15%+ ROI, we're probably overfitting
12. **Natural edge decay** - markets adapt, model needs continuous updating

---

## Sources Index

### Pinnacle (Highest Credibility)
- [CLV Explained](https://www.pinnacle.com/betting-resources/en/educational/what-is-closing-line-value-clv-in-sports-betting)
- [Real Kelly Criterion](https://www.pinnacle.com/betting-resources/en/betting-strategy/the-real-kelly-criterion-a-critical-analysis-of-the-popular-staking-method/hzkjtfcb3knyn9cj)
- [Theory of Everything](https://www.pinnacle.com/betting-resources/en/educational/part-two-toward-a-theory-of-everything/uwc25wvpppzj997d)
- [Kelly Criterion for Betting](https://www.pinnacle.com/betting-resources/en/betting-strategy/how-to-use-kelly-criterion-for-betting/2bt2lk6k2qwq7qj8)

### Sharp Bettor Sources (High Credibility)
- [Unabated: How Sharps Win](https://unabated.com/articles/how-do-sharps-win-at-sports-betting)
- [Unabated: Beyond CLV (Peabody)](https://unabated.com/articles/beyond-clv-analyze-bet-quality-using-expected-roi)
- [Spanky Top-Down Case Study](https://www.bettored.org/post/case-study-spanky-top-down-betting)
- [Covers: Mind of a Professional Bettor](https://www.covers.com/industry/whats-the-difference-between-you-and-a-sharp-step-inside-the-mind-of-a-professional-bettor)
- [8rainstation: Sharp Bettor Journey](https://8rainstation.com/blog/advice-from-my-mistake-filled-journey-to-becoming-a-sharp-sports-bettor-mastering-one-sided-line-devigging)

### Model Building & Methodology (High Credibility)
- [Overfitting Problem (Forum Thread)](https://www.betting-forum.com/threads/the-overfitting-problem-why-backtested-betting-systems-fail-in-production.47444/)
- [Backtesting Without Overfitting](https://www.greatbets.co.uk/how-to-backtest-a-sports-betting-strategy-without-overfitting/)
- [Zerillo MLB Model (Action Network)](https://www.actionnetwork.com/mlb/daily-mlb-betting-model-projections-sean-zerillo)
- [Zerillo K Props Podcast](https://x.com/SeanZerillo/status/1904207117872976163)

### MLB K Prop Specifics (Medium-High Credibility)
- [In-Zone Whiff Rate for K Props](https://aibettingedge.com/using-in-zone-whiff-rate-to-predict-pitcher-strikeout-mlb-prop-bets/)
- [Covers: MLB Prop Tips](https://www.covers.com/mlb/prop-betting-tips-for-successful-baseball-betting)
- [K Prop Identification](https://thisdayinbaseball.com/strikeout-props-betting-how-to-identify-elite-k-over-under-spots/)

### Credibility Check Sources
- [OddsJam Review (CaanBerry)](https://caanberry.com/oddsjam-review/)
- [OddsJam Review (RotoWire)](https://www.rotowire.com/betting/oddsjam-review)
- [Captain Jack Profile (Sun-Times)](https://chicago.suntimes.com/casinos-gambling/2025/08/23/captain-jack-andrews-betbash-gadoon-spanky-kyrollos-sports-gambling-hall-of-fame-michael-roxy-roxborough-las-vegas-atlantic-city)
- [Spanky Profile (Ringer)](https://www.theringer.com/2019/06/05/gambling/sports-betting-bettors-sharps-kicked-out-spanky-william-hill-new-jersey)
- [Why Sportsbooks Limit +EV Bettors](https://www.oddsshopper.com/articles/betting-101/why-sportsbooks-limits-ev-bettors-and-what-to-do-about-it-y10)

### Forums
- [Covers MLB Forum](https://www.covers.com/forum/mlb-betting-27)
- [SBR MLB Forum](https://www.sportsbookreview.com/forum/baseball-betting)

---

*Research conducted 2026-04-20. All sources accessed same day.*

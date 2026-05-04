# Free Data Sources for NHL/MLB Predictive Sports Betting Models

**Date**: 2026-04-13
**Confidence**: High (all sources verified via web research)

---

## Executive Summary

There is an extraordinary amount of free, high-quality data available for building predictive NHL and MLB models. The NHL ecosystem centers on the undocumented but fully functional api-web.nhle.com API plus MoneyPuck's CSV dumps (1.84M shots with 124 attributes each). MLB is even richer thanks to Baseball Savant's Statcast data (80+ fields per pitch, free CSV download) and the completely open statsapi.mlb.com. The biggest gaps are: (1) historical closing line odds for backtesting (free tiers are very limited), (2) real-time injury feeds (no truly free structured API), and (3) referee/umpire tendency data (requires scraping, not API-accessible).

---

## 1. NHL API (api-web.nhle.com)

**URL**: https://api-web.nhle.com
**Authentication**: None required
**Rate Limits**: Undocumented, no known enforced limits
**Reference Docs**: https://github.com/Zmalski/NHL-API-Reference
**Python Wrapper**: https://github.com/coreyjs/nhl-api-py (`pip install nhl-api-py`)

### Key Endpoints

| Endpoint | Data |
|----------|------|
| `/v1/gamecenter/{game_id}/play-by-play` | Full play-by-play with event types, x/y coordinates, period, time, players involved |
| `/v1/gamecenter/{game_id}/boxscore` | Game boxscore |
| `/v1/gamecenter/{game_id}/landing` | Game summary with 3-stars, scoring, penalties |
| `/v1/player/{player_id}/landing` | Player bio, career stats |
| `/v1/player/{player_id}/game-log/{season}/{game_type}` | Per-game stats for a player |
| `/v1/club-stats/{team}/now` | Current team stats |
| `/v1/standings/now` | Current standings |
| `/v1/standings/{date}` | Historical standings by date |
| `/v1/schedule/{date}` | Schedule |
| `/v1/skater-stats-leaders/current` | League stat leaders |
| `/v1/roster/{team}/current` | Team roster |

### What You Get
- **Play-by-play**: Every event (shots, goals, hits, faceoffs, penalties, takeaways, giveaways) with x/y ice coordinates
- **Shot locations**: x/y coordinates in feet, centered on center ice
- **Player game logs**: Goals, assists, points, +/-, TOI, shots, hits, blocks per game
- **NO built-in xG**: You must calculate xG yourself from shot coordinates + context (MoneyPuck provides pre-calculated xG)
- **NO Corsi/Fenwick directly**: Derivable from play-by-play events (shots + missed shots + blocked shots = Corsi)
- **NO line combinations directly**: Derivable from shift data

### NHL EDGE Tracking Data
- **URL**: https://www.nhl.com/nhl-edge + accessible via nhl-api-py
- **Data**: Skating speed, shot speed, distance traveled, zone time, burst counts
- **Access**: Free via website; programmatic via undocumented API endpoints in nhl-api-py
- **Quality**: Excellent - 20 cameras per arena, puck tracked 60x/second, players 15x/second
- **Limitation**: Raw tracking data (frame-by-frame positions) is NOT publicly available - only aggregated metrics

### Data Quality: 8/10
Strong for basic and intermediate analytics. Missing raw tracking data and pre-computed advanced metrics.

---

## 2. NHL Advanced Stats Sources

### MoneyPuck (PRIMARY RECOMMENDATION)

**URL**: https://moneypuck.com/data.htm
**Authentication**: None
**Rate Limits**: None (direct CSV download)
**Format**: CSV files, ZIP archives
**Historical Coverage**: 2007-08 through 2025-26 (updated nightly during season)

#### Available Datasets

| Dataset | Description |
|---------|-------------|
| **Shot Data** | 1.84M+ shots, 124 attributes per shot including xG, shot type, distance, angle, rebound, rush, arena-adjusted coordinates |
| **Skater Stats** | Season-level and game-by-game, all situations (5v5, PP, PK, etc.) |
| **Goalie Stats** | Season-level and game-by-game with xG against |
| **Line Stats** | Forward line and defensive pair stats |
| **Team Stats** | Team-level aggregates |
| **Player Bios** | All NHL players from 2007+ with birthdate, height, weight, position |

#### Key Fields in Shot Data (124 attributes)
- xGoal (expected goals probability)
- Shot type, distance, angle
- Rebound flag, rush flag
- Game state (score differential, period, time)
- Arena-adjusted coordinates
- Shooter and goalie info
- Strength state (5v5, 5v4, etc.)

**Data Quality: 9.5/10** - This is the gold standard for free NHL analytics data. Shot-level xG is exactly what you need for modeling.

**License**: Free for non-commercial use with credit. Commercial use requires approval.

### Natural Stat Trick

**URL**: https://www.naturalstattrick.com
**Authentication**: None
**Rate Limits**: Be respectful (no documented limits)
**Format**: Tables viewable on-site, CSV export via browser

#### Available Metrics
- Corsi, Fenwick (all situations)
- Expected Goals (their own model)
- Scoring Chances, High-Danger Chances
- Zone entries/exits (limited)
- On-ice shooting %, save %
- Individual and on-ice stats
- Game-by-game breakdowns

**Data Quality: 8.5/10** - Excellent for Corsi/Fenwick/scoring chances. No bulk download API - must scrape or manually export. Community has built scrapers (github.com/gschwaeb/scraping_naturalstattrick).

### Evolving Hockey

**URL**: https://evolving-hockey.com
**Authentication**: Subscription required for most data ($5/month)
**Free Content**: Blog posts, methodology papers, xG model code on GitHub

#### What's Available (paid)
- GAR (Goals Above Replacement)
- RAPM (Regularized Adjusted Plus-Minus)
- xG model outputs
- WAR-style player valuations

**GitHub (free)**: https://github.com/evolvingwild/hockey-all - xG model code and preparation scripts

**Data Quality: 9/10** - Best single-number player valuations in hockey. The free GitHub code lets you build your own version.

### Hockey Reference

**URL**: https://www.hockey-reference.com
**Authentication**: None
**Format**: HTML tables (scrapable), some CSV export

#### Available
- Basic and some advanced stats (Corsi, Fenwick at team level)
- Historical data back to NHL founding
- Game logs, splits, on-ice stats
- Injury reports page

**Data Quality: 7/10** - Good for historical baseline data. Limited advanced metrics compared to MoneyPuck.

---

## 3. MLB Stats API (statsapi.mlb.com)

**URL**: https://statsapi.mlb.com/api/v1/
**Authentication**: None required
**Rate Limits**: Undocumented but liberal
**Python Wrapper**: `pip install MLB-StatsAPI`

### Key Endpoints

| Endpoint | Data |
|----------|------|
| `/api/v1/game/{gamePk}/feed/live` | Real-time game feed with pitch-by-pitch |
| `/api/v1/game/{gamePk}/playByPlay` | Play-by-play events |
| `/api/v1/game/{gamePk}/boxscore` | Game boxscore |
| `/api/v1/game/{gamePk}/linescore` | Line score |
| `/api/v1/people/{playerId}` | Player info |
| `/api/v1/people/{playerId}/stats` | Player stats with splits |
| `/api/v1/schedule` | Schedule with filters |
| `/api/v1/standings` | Standings |
| `/api/v1/teams/{teamId}/roster` | Team roster |

### What You Get
- **Pitch-by-pitch**: 100+ columns per pitch including velocity, movement, spin, location, result
- **Play-by-play**: Every at-bat result with context (runners, outs, count)
- **Player stats**: Career, season, splits (vs LHP/RHP, home/away, by count)
- **Game context**: Weather, venue, attendance, umpires

**Data Quality: 9/10** - Extremely comprehensive and well-structured. The live feed endpoint is particularly rich.

---

## 4. Baseball Savant / Statcast

**URL**: https://baseballsavant.mlb.com
**Direct Search**: https://baseballsavant.mlb.com/statcast_search
**CSV Docs**: https://baseballsavant.mlb.com/csv-docs
**Authentication**: None
**Rate Limits**: 30,000 rows per query; recommended to chunk by single days for large pulls

### Data Fields (80+ per pitch)

#### Pitch Mechanics
- Release speed, position (x, y, z), spin rate, spin axis
- Extension, effective speed
- Pitch movement (pfx_x, pfx_z - horizontal and vertical break)

#### Batted Ball Metrics
- **Exit velocity** (launch_speed)
- **Launch angle** (launch_angle)
- Hit distance (hit_distance_sc)
- Hit coordinates (hc_x, hc_y)
- Barrel classification

#### Expected Value Metrics
- **xBA** (expected batting average)
- **xwOBA** (expected weighted on-base average)
- xSLG, xISO
- BABIP value

#### Win Probability
- Win expectancy change per plate appearance
- Run expectancy changes

#### Game Context
- Inning, outs, count, runners, score
- Fielding alignment (shift data)
- All 9 defensive player positions

### Best Access Method: pybaseball
```python
pip install pybaseball
from pybaseball import statcast
# Pull all pitches for a date range
data = statcast(start_dt='2026-04-01', end_dt='2026-04-07')
```
- Auto-chunks large date ranges into 1-day queries
- Handles Baseball Savant's 30K row limit
- Also pulls from FanGraphs and Baseball Reference

**Historical Coverage**: 2015-present for full Statcast; some data back to 2008

**Data Quality: 10/10** - This is the single best free dataset in all of sports analytics. Every pitch, every batted ball, with Hawkeye tracking precision.

---

## 5. FanGraphs

**URL**: https://www.fangraphs.com
**Authentication**: Free tier available; FanGraphs+ ($8/mo) for CSV exports
**Access**: pybaseball scraping functions or baseballr (R)

### Free Data
- Leaderboards (batting, pitching, fielding)
- Splits (vs LHP/RHP, home/away, monthly)
- Park factors
- Steamer and ZiPS projections (pre-season free, in-season requires subscription)
- WAR calculations
- wRC+, FIP, xFIP, SIERA

### Via pybaseball (free scraping)
```python
from pybaseball import batting_stats, pitching_stats
batting = batting_stats(2026)  # Season leaderboard
```

**Data Quality: 9/10** - Industry standard for baseball analytics. Rate-limited scraping (6-second delays enforced by pybaseball).

---

## 6. Open-Meteo (Weather Data)

**URL**: https://open-meteo.com
**Authentication**: None required (no API key needed)
**Rate Limits**: No strict limits; be reasonable
**License**: Free for non-commercial use; commercial plans from EUR 29/mo

### Available Endpoints

| Endpoint | Data |
|----------|------|
| `/v1/forecast` | 7-16 day forecast, hourly resolution |
| `/v1/archive` | Historical weather data |
| `/v1/marine` | Marine/coastal forecasts |
| `/v1/air-quality` | Air quality index |
| `/v1/elevation` | Terrain elevation |

### Key Weather Variables
- Temperature (2m), feels-like temperature
- Wind speed and direction (10m, multiple levels)
- Wind gusts
- Precipitation, rain, snowfall
- Humidity, dewpoint
- Cloud cover
- Pressure
- UV index

### Application to Sports Betting
- **MLB outdoor stadiums**: Wind speed/direction affects home run rates dramatically (Wrigley Field wind is a classic factor)
- **NHL**: Less relevant (indoor), but travel weather can affect team fatigue
- **Historical weather**: Can backtest weather-adjusted models using archive endpoint

**Data Quality: 9/10** - Sub-10ms response times, excellent spatial and temporal resolution. Perfect for stadium-level weather data.

---

## 7. Odds APIs (Historical Closing Lines)

### The Odds API (Best Free Option)

**URL**: https://the-odds-api.com
**Free Tier**: 500 credits/month
**Authentication**: API key required (free registration)

#### What You Get Free
- Live odds from 70+ sports, 40+ bookmakers
- Moneylines, spreads, totals, player props
- NHL and MLB covered
- Historical odds from mid-2020 onward

#### Cost Structure
- Each live request = 1 credit per region per market
- Each historical request = 10 credits per region per market
- **500 credits/month means ~50 historical snapshots or ~500 live pulls**
- Paid plans start at $25/month for more credits

**Data Quality: 8/10** - Good coverage, but free tier is very limited for backtesting. Historical data only goes back to 2020.

### Alternative Free/Cheap Sources

| Source | What | Cost |
|--------|------|------|
| **Sports-Reference.com** | Basic closing lines for major sports, years of history | Free with registration |
| **Kaggle datasets** | Historical odds dumps (search "NHL odds" or "MLB odds") | Free |
| **odds-api.io** | Similar to The Odds API, free tier available | Free tier |
| **DonBest archive** | Professional-grade historical odds | Expensive ($200+/mo) |
| **Pinnacle odds** (via scraping community) | Sharp closing lines | Free but requires effort |

### Recommendation for Backtesting
For serious backtesting, you'll likely need to either:
1. Accumulate your own odds database going forward (free, takes time)
2. Buy historical data from a provider ($50-200/month)
3. Use Kaggle community datasets (free but quality varies)

---

## 8. Injury Data Sources

### Free Options

| Source | Format | Coverage | Quality |
|--------|--------|----------|---------|
| **NHL API roster endpoint** | JSON | Current injuries via roster status | 7/10 - basic |
| **MLB API** (`/api/v1/injuries`) | JSON | Current IL placements | 8/10 |
| **Hockey-Reference.com** | HTML | NHL injury reports, scrapable | 7/10 |
| **ESPN injury pages** | HTML | Both NHL and MLB, current status | 7/10 |
| **Puckpedia.com** | HTML | NHL injuries + cap info | 7/10 |
| **BALLDONTLIE API** | JSON | Multi-sport, free tier | 6/10 - limited |

### What's Missing
- **No truly free real-time injury API** with push notifications
- Day-to-day designations often lack detail (doesn't say "upper body" vs specific)
- Practice participation data (huge edge) requires beat reporter monitoring
- **Twitter/X monitoring** for beat reporters is how sharps get injury info first

### Recommendation
Scrape ESPN + official league APIs daily. For real-time edge, monitor beat reporter Twitter accounts programmatically (search for "day-to-day", "out", "IR" + team names).

---

## 9. Referee/Umpire Data

### MLB Umpire Data

| Source | What | Access |
|--------|------|--------|
| **UmpScorecards** (umpscorecards.com) | Daily umpire scorecards, accuracy %, consistency, favor metrics | Free website, no API |
| **Covers.com** (covers.com/sport/baseball/mlb/umpires) | Umpire betting records, over/under tendencies | Free website |
| **Baseball Savant** | Umpire data embedded in pitch-level Statcast | Free via CSV/pybaseball |
| **Statcast "plate_x" and "plate_z" fields** | Exact pitch location allows you to build your own strike zone model per umpire | Free |

**Key insight**: With Statcast data, you can build your own umpire strike zone model that's better than any third-party source. Every called ball/strike has the exact pitch location - compare to the rulebook zone to measure each umpire's tendencies.

### NHL Referee Data

| Source | What | Access |
|--------|------|--------|
| **Covers.com** (covers.com/sport/hockey/nhl/referees) | Referee betting records, O/U tendencies, home ATS | Free website |
| **NHL play-by-play** | Penalty data per game (you can aggregate by referee) | Free via API |
| **ScoutingTheRefs.com** | Referee assignments, historical tendencies | Free website |

**Key insight**: NHL referee assignments are announced ~day before games. Building your own penalty rate database from play-by-play data (which includes referee names) gives you the most accurate tendency data.

---

## 10. What a Quant Fund Would Consider Essential That Hobbyists Miss

### Data Sources Quants Prioritize

1. **Line movement / steam moves**: Not just closing lines - the trajectory of how odds move from open to close. Sharp money moves lines before the public. Free sources are very limited here.

2. **Closing Line Value (CLV)**: The single best predictor of long-term betting success. You need to compare your bet price to the closing line. Requires logging odds at bet time AND at close.

3. **Market-implied probabilities from Pinnacle**: Pinnacle is the sharpest book. Their closing lines are the best estimate of true probability. Historical Pinnacle data is gold.

4. **Roster confirmation / lineup data**: Starting goalies (NHL) and starting pitchers (MLB) confirmed vs projected. Getting this 30 minutes before game time is an edge.

5. **Travel and schedule data**: Back-to-back games (NHL), cross-timezone travel, day games after night games (MLB). Easily derived from schedule data but rarely modeled by hobbyists.

6. **Park factors by granular splits**: Not just "Coors Field inflates offense" - park factors by handedness, fly ball/ground ball, temperature. FanGraphs provides some of this.

7. **Bullpen usage / pitcher workload**: Pitch counts over trailing 3/7/14 days. Bullpen availability based on recent usage. This is reconstructable from play-by-play data.

8. **Platoon splits at granular level**: LHP vs RHB in specific counts, not just overall L/R splits.

9. **Market efficiency by sport/league/bet type**: NHL player props are less efficient than MLB moneylines. Knowing WHERE the market is inefficient matters more than having better data.

10. **Situational motivation factors**: Playoff race positioning, revenge games, division rivals, contract year players. Hard to quantify but real.

### The Real Edge: Data Others Don't Combine

Quant funds don't have secret data sources - they combine publicly available data in ways others don't:
- Weather + park factor + pitcher tendencies + umpire zone = total runs model
- Goalie confirmed + team on back-to-back + travel distance + referee tendencies = adjusted win probability
- Exit velocity trends + opposing pitcher spin rate decay + bullpen fatigue = late-inning scoring model

### Infrastructure Quants Build That Hobbyists Don't

1. **Automated daily data pipelines** - Not manual CSV downloads
2. **Real-time odds ingestion** - Capture every line movement
3. **Backtesting framework** - Simulate bets against historical closing lines
4. **Kelly criterion position sizing** - Not flat betting
5. **Multi-book execution** - Getting the best line across books
6. **Stale line detection** - Identifying books slow to update after news

---

## Summary: Recommended Data Stack (All Free)

### NHL Model

| Source | What | Priority |
|--------|------|----------|
| **MoneyPuck CSV** | Shot-level data with xG (124 attributes, 1.84M shots) | CRITICAL |
| **NHL API** (api-web.nhle.com) | Play-by-play, rosters, schedules, standings | CRITICAL |
| **Natural Stat Trick** | Corsi, Fenwick, scoring chances, zone data | HIGH |
| **NHL EDGE** (via nhl-api-py) | Skating speed, shot speed, zone time | HIGH |
| **Covers.com referees** | Referee penalty tendencies | MEDIUM |
| **The Odds API** | Odds data (limited free) | MEDIUM |
| **Open-Meteo** | Weather (limited NHL use) | LOW |

### MLB Model

| Source | What | Priority |
|--------|------|----------|
| **Baseball Savant / pybaseball** | Statcast pitch-level data (80+ fields) | CRITICAL |
| **MLB Stats API** | Play-by-play, rosters, schedules, standings | CRITICAL |
| **FanGraphs** (via pybaseball) | WAR, projections, park factors, splits | HIGH |
| **Open-Meteo** | Stadium weather (wind especially) | HIGH |
| **UmpScorecards** | Umpire zone tendencies | MEDIUM |
| **The Odds API** | Odds data (limited free) | MEDIUM |
| **Statcast umpire data** | Build own strike zone model per umpire | MEDIUM |

### Total Cost: $0 for data, invest time in pipeline automation

---

## Data Pipeline Architecture Recommendation

```
[Cron/Scheduler]
    |
    v
[Data Ingestion Layer]
    |-- NHL API -> play-by-play, rosters, schedule
    |-- MoneyPuck CSV -> shot data, xG (nightly download)
    |-- MLB Stats API -> play-by-play, pitch data
    |-- pybaseball -> Statcast bulk data
    |-- Open-Meteo -> game-day weather
    |-- The Odds API -> live odds snapshot
    |-- ESPN/injury scraper -> injury status
    |
    v
[PostgreSQL / DuckDB]
    |-- Raw tables (immutable)
    |-- Feature tables (derived metrics)
    |-- Model input views
    |
    v
[Feature Engineering]
    |-- Rolling averages (5/10/20 game)
    |-- Situational splits
    |-- Matchup-specific features
    |-- Market-derived features (implied probability)
    |
    v
[Model Layer]
    |-- Probability estimation
    |-- Edge calculation (model prob vs market prob)
    |-- Kelly sizing
    |
    v
[Backtesting / Execution]
```

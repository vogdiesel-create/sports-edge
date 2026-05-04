# Free NBA Player Prop Odds Sources

**Date**: 2026-04-12
**Purpose**: Identify $0-cost approaches for getting multi-book NBA player prop odds

---

## Executive Summary

There are several viable free approaches, ranging from free API tiers to direct DraftKings endpoint scraping. The **best immediate $0 option** is hitting DraftKings' undocumented sportsbook API directly (no auth required), combined with The Odds API's free tier for multi-book comparison. For a more robust multi-book solution, odds-api.io offers 100 req/hour free forever.

---

## 1. FREE API TIERS

### 1a. The Odds API (the-odds-api.com)

- **URL**: https://the-odds-api.com
- **Free Tier**: 500 requests/month (no credit card needed)
- **API Key**: Required (free signup)
- **NBA Player Props Supported**:
  - Points, Rebounds, Assists, Threes, Blocks, Steals O/U
  - Blocks+Steals, Turnovers, PRA, PR, PA, RA O/U
  - Field Goals, Free Throws Made/Attempted O/U
  - First Basket Scorer, Double Double, Triple Double
  - First quarter variants for pts/reb/ast
  - Alternate lines for most markets
- **Sportsbooks**: US books (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- **Rate Limit**: 500 requests/month free
- **Endpoint**: `GET /v4/sports/basketball_nba/odds/?apiKey=KEY&regions=us&markets=player_points`
- **Verdict**: Best documented free option. 500 req/month is tight but workable if you poll strategically (e.g., 16 requests/day). Each request returns odds from ALL covered books at once.

### 1b. odds-api.io

- **URL**: https://odds-api.io
- **Free Tier**: 100 requests/hour, forever, no credit card
- **API Key**: Required (free signup)
- **Sports**: NFL, NBA, MLB, NHL, soccer, tennis, 50+ sports
- **Markets**: Moneylines, spreads, totals confirmed. Player props mentioned but unclear if included on free tier
- **Sportsbooks**: 265+ bookmakers across regions
- **Format**: Clean JSON
- **Limitation**: Free tier is for "development and testing" only (commercial use requires paid)
- **Endpoint**: `GET /v1/odds?sport=basketball_nba&market=player_props`
- **Verdict**: Very generous rate limit (100/hr = 2,400/day). Needs testing to confirm player props are actually available on free tier. Worth signing up immediately to test.

### 1c. RapidAPI - NBA Player Props Odds

- **URL**: https://rapidapi.com/Rafistan/api/nba-player-props-odds
- **Free Tier**: Likely has a free tier (RapidAPI standard), needs signup to confirm
- **API Key**: Required (RapidAPI key)
- **Data**: NBA-specific player props
- **Verdict**: Worth checking but limited documentation available. May only cover 1-2 books.

### 1d. Sports Game Odds (sportsgameodds.com)

- **URL**: https://sportsgameodds.com
- **Free Tier**: 10 requests/minute, 1,000 objects/month
- **API Key**: Required (free signup)
- **Sports**: Multi-sport including NBA
- **Player Props**: Yes, dedicated player props API
- **Verdict**: 1K objects/month is very limited but usable for spot checks.

### 1e. BALLDONTLIE (balldontlie.io)

- **URL**: https://www.balldontlie.io
- **Free Tier**: Yes (basic endpoints, generous rate limits)
- **API Key**: Required (free at app.balldontlie.io)
- **Data**: Live betting odds from major sportsbooks, player props, real-time updates
- **Limitation**: Free tier scope unclear for odds data vs. stats data
- **Verdict**: Primarily known for stats. Odds/props may require paid tier. Worth testing.

---

## 2. DIRECT SPORTSBOOK API SCRAPING ($0, No API Key)

### 2a. DraftKings Sportsbook API (BEST FREE OPTION)

DraftKings exposes undocumented REST endpoints that return JSON with no authentication required. This is the single best free approach for getting real-time player prop odds from at least one major book.

**Base URL**: `https://sportsbook.draftkings.com/sites/US-SB/api/v5/`

**Endpoints (hierarchical navigation)**:

```
# Step 1: Get NBA event group (sport ID for NBA needs discovery)
GET https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/{nba_sport_id}/?format=json

# Step 2: Get categories (market types) within NBA
GET https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/{nba_sport_id}/categories/{category_id}?format=json

# Step 3: Get subcategories (specific prop markets)
GET https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/{nba_sport_id}/categories/{category_id}/subcategories/{subcategory_id}?format=json
```

**Known Sport IDs** (from community research):
- NFL: 88808
- CFB: 87637
- NBA: Needs discovery (try browsing the eventgroups endpoint)

**What You Get**:
- Player names, prop descriptions (points O/U, assists O/U, etc.)
- Lines and odds (American and decimal)
- Real-time updates
- All available prop markets DK offers

**Rate Limits**: Undocumented. Reasonable polling (every 60s) should be fine. Use residential proxy if aggressive.

**Risks**:
- Endpoints can change without notice
- Against DK Terms of Service
- Anti-bot detection (PerimeterX) may block if aggressive
- Only gives you DraftKings odds (single book)

**Reference Code**: https://gist.github.com/Adeiko/4d63fb49e2878cb5fdc737aa3cb150fa

### 2b. FanDuel Internal API

FanDuel does NOT expose unauthenticated public endpoints like DraftKings does. Access requires:
- Selenium/Playwright browser automation
- Or reverse-engineering their frontend API calls (auth tokens rotate)
- Or using a third-party aggregator

**Verdict**: Much harder than DK. Not recommended as primary approach.

---

## 3. OPEN-SOURCE SCRAPERS (GitHub)

### 3a. DKscraPy

- **URL**: https://github.com/agad495/DKscraPy
- **Language**: Python (Beautiful Soup + DK API)
- **Sports**: MLB, NFL (NBA adaptable)
- **Markets**: Game odds + NFL player props
- **How**: Uses DraftKings' undocumented API endpoints
- **Verdict**: Good starting point. Needs modification for NBA props.

### 3b. BowTiedBettor/DraftKings

- **URL**: https://github.com/BowTiedBettor/DraftKings
- **Language**: Python
- **Sports**: NHL (easily modified for NBA)
- **Features**: Pregame + live odds, JSON/Excel output, email notifications for odds changes, streaming support
- **Files**: draftkings_class.py, draftkings_script.py, draftkings_stream.py
- **Verdict**: Well-structured OOP code. Best repo to fork and adapt for NBA props.
- **Blog series**: https://www.blog.bowtiedbettor.com/p/draftkings-scraping-project-part

### 3c. sbrscrape (SportsBookReview)

- **URL**: https://github.com/nkgilley/sbrscrape
- **PyPI**: `pip install sbrscrape`
- **Language**: Python
- **Sportsbooks**: BetMGM, DraftKings, FanDuel, Caesars, PointsBet, Wynn, BetRivers
- **Sports**: NFL confirmed, NBA possible
- **Markets**: Spreads, moneylines, totals (NOT player props)
- **Verdict**: Multi-book but game-level only. Useful for game odds, not props.

### 3d. sportsbookreview-scraper (FinnedAI)

- **URL**: https://github.com/FinnedAI/sportsbookreview-scraper
- **Language**: Python
- **Sports**: NFL, NBA, MLB, NHL
- **Data**: Historical odds, 10-year datasets included
- **Format**: JSON and CSV output
- **Markets**: Game-level (spreads, ML, totals), NOT player props
- **Verdict**: Great for historical game odds. Not useful for live player props.

### 3e. OddsHarvester

- **URL**: https://github.com/jordantete/OddsHarvester
- **Language**: Python (Playwright browser automation)
- **Source**: OddsPortal.com
- **Sports**: 8 sports, 100+ leagues, NBA included
- **Markets**: Various game-level markets (no player props mentioned)
- **Output**: JSON, CSV, or S3
- **Features**: Historical + upcoming, proxy support, Docker
- **Verdict**: Comprehensive game odds from OddsPortal but no player props.

### 3f. sportsbook-odds-scraper

- **URL**: https://github.com/declanwalpole/sportsbook-odds-scraper
- **Language**: Python
- **Output**: Normalized pandas DataFrame
- **Sportsbooks**: North American and Australian books
- **Verdict**: Generic multi-book scraper, needs testing for NBA props.

### 3g. gto76/bets

- **URL**: https://github.com/gto76/bets
- **Language**: Python
- **Focus**: Multi-bookie odds scraper with NBA player points betting mentioned
- **Verdict**: Worth investigating for player-level data.

---

## 4. RECOMMENDED APPROACH (Stack for $0)

### Tier 1: Immediate (Today)

1. **Sign up for The Odds API** free tier (500 req/month)
   - Get multi-book NBA player prop odds immediately
   - Use for cross-book comparison (DK, FD, BetMGM, etc.)
   - Poll once per hour for key games = ~16 req/day = 480/month

2. **Sign up for odds-api.io** free tier (100 req/hour)
   - Test if player props are included
   - If yes, this becomes primary source (2,400 req/day is very generous)

### Tier 2: Build (This Week)

3. **Hit DraftKings API directly** for real-time DK-specific props
   - Fork BowTiedBettor/DraftKings repo
   - Adapt for NBA sport ID
   - Get DK odds with no rate limit concerns at reasonable polling
   - This gives you DK data at whatever frequency you want

4. **Build a simple FanDuel scraper** using Playwright
   - Navigate to FanDuel NBA player props page
   - Extract odds from rendered HTML
   - Run on a schedule (every 5-15 min)

### Tier 3: Enrich (Later)

5. **Add sbrscrape** for multi-book game-level odds
6. **Add OddsHarvester** for historical odds from OddsPortal
7. **Consider Pinnacle API** (free with account) for sharp lines

---

## 5. KEY URLS QUICK REFERENCE

| Source | URL | Free? | Props? | Multi-Book? |
|--------|-----|-------|--------|-------------|
| The Odds API | https://the-odds-api.com | 500 req/mo | Yes | Yes |
| odds-api.io | https://odds-api.io | 100 req/hr | Maybe | Yes (265+ books) |
| DraftKings API | sportsbook.draftkings.com/sites/US-SB/api/v5/ | Yes (no auth) | Yes | No (DK only) |
| Sports Game Odds | https://sportsgameodds.com | 1K obj/mo | Yes | Yes |
| BALLDONTLIE | https://balldontlie.io | Basic free | Maybe | Maybe |
| RapidAPI Props | rapidapi.com/Rafistan/api/nba-player-props-odds | Likely free tier | Yes | Unknown |
| sbrscrape | github.com/nkgilley/sbrscrape | Free (OSS) | No | Yes (7 books) |
| BowTiedBettor/DK | github.com/BowTiedBettor/DraftKings | Free (OSS) | Yes | No (DK only) |
| OddsHarvester | github.com/jordantete/OddsHarvester | Free (OSS) | No | Yes (OddsPortal) |
| DK Gist | gist.github.com/Adeiko/4d63fb49e2878cb5fdc737aa3cb150fa | Free | Yes | No (DK only) |

---

## 6. DRAFTKINGS API DISCOVERY SCRIPT

Quick Python to discover NBA sport ID and available prop markets:

```python
import requests

# Step 1: Find NBA sport/event group ID
# Try the main sports endpoint first
url = "https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/?format=json"
resp = requests.get(url)
# Look through response for NBA event group ID

# Alternative: Known DK NBA page scrape approach
# Visit https://sportsbook.draftkings.com/leagues/basketball/nba
# Inspect network requests to find the event group ID

# Step 2: Once you have the NBA event group ID (e.g., 42648):
nba_id = "42648"  # EXAMPLE - needs verification
url = f"https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/{nba_id}/?format=json"
resp = requests.get(url)
data = resp.json()

# Step 3: Find player props category
# Look for categories like "Player Props" in the response
# Then drill into subcategories for Points, Assists, etc.
```

---

## Sources

- The Odds API: https://the-odds-api.com/sports-odds-data/betting-markets.html
- odds-api.io free tier: https://odds-api.io/pricing/free
- DK API gist: https://gist.github.com/Adeiko/4d63fb49e2878cb5fdc737aa3cb150fa
- DK unofficial docs: https://github.com/SeanDrum/Draft-Kings-API-Documentation
- BowTiedBettor DK scraper: https://github.com/BowTiedBettor/DraftKings
- DKscraPy: https://github.com/agad495/DKscraPy
- sbrscrape: https://github.com/nkgilley/sbrscrape
- OddsHarvester: https://github.com/jordantete/OddsHarvester
- sportsbookreview-scraper: https://github.com/FinnedAI/sportsbookreview-scraper
- Sports Game Odds: https://sportsgameodds.com/pricing/
- BALLDONTLIE: https://www.balldontlie.io
- DK scraping guide (2026): https://scraperly.com/scrape/draftkings

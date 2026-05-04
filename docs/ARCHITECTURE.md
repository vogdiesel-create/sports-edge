# Sports Edge API - Architecture Design

**Status:** Proposed
**Date:** 2026-04-12
**Author:** architect-agent

---

## 1. System Overview

Sports Edge API is a subscription-based REST API that delivers model-filtered NBA player prop picks (unders only, 15%+ edge, 25+ min players) to paying subscribers. It runs nightly scan and morning grading jobs, stores all picks and results in PostgreSQL, and exposes performance data via authenticated endpoints. A public landing page shows aggregate track record to drive conversions.

```
+------------------+       +------------------+       +------------------+
|  the-odds-api    |       |   cdn.nba.com    |       |     Stripe       |
|  (prop lines)    |       |  (box scores)    |       |   (billing)      |
+--------+---------+       +--------+---------+       +--------+---------+
         |                          |                           |
         v                          v                           v
+--------+----------+     +---------+---------+     +-----------+--------+
|  Nightly Scanner  |     |  Morning Grader   |     |   Auth / Billing   |
|  (cron, 9pm ET)   |     |  (cron, 10am ET)  |     |   Middleware       |
+--------+----------+     +---------+---------+     +-----------+--------+
         |                          |                           |
         +-------------+------------+---------------------------+
                       |
                       v
              +--------+--------+
              |   PostgreSQL    |
              |   (picks, results, users) |
              +---------+-------+
                        |
                        v
              +---------+-------+
              |   FastAPI App   |
              |   REST API      |
              +---------+-------+
                        |
              +---------+-------+
              | Landing Page    |
              | (static HTML +  |
              |  public API)    |
              +-----------------+
```

---

## 2. Project File Structure

```
sports-edge/
|-- app/
|   |-- __init__.py
|   |-- main.py                  # FastAPI app factory, lifespan, CORS
|   |-- config.py                # Settings via pydantic-settings (env vars)
|   |-- database.py              # SQLAlchemy async engine + session factory
|   |-- models.py                # SQLAlchemy ORM models (users, picks, results, daily_summary)
|   |-- schemas.py               # Pydantic request/response schemas
|   |--
|   |-- routers/
|   |   |-- __init__.py
|   |   |-- auth.py              # POST /auth/register, POST /auth/login
|   |   |-- picks.py             # GET /picks/today, GET /picks/{date}
|   |   |-- track_record.py      # GET /track-record, GET /track-record/recent
|   |   |-- account.py           # GET /account
|   |   |-- public.py            # GET /public/track-record (no auth, for landing page)
|   |   |-- webhooks.py          # POST /webhooks/stripe (subscription events)
|   |
|   |-- middleware/
|   |   |-- __init__.py
|   |   |-- api_key_auth.py      # API key validation dependency
|   |   |-- rate_limit.py        # Token bucket rate limiter
|   |   |-- subscription.py      # Subscription status check dependency
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   |-- picks_service.py     # Query picks, format responses
|   |   |-- track_record_service.py  # Aggregate stats, ROI calculations
|   |   |-- auth_service.py      # User creation, API key generation, password hashing
|   |   |-- stripe_service.py    # Stripe customer/subscription management
|   |
|   |-- utils/
|       |-- __init__.py
|       |-- crypto.py            # API key generation (secrets.token_urlsafe)
|       |-- odds.py              # American-to-decimal conversion, Kelly sizing
|
|-- core/                        # Shared prediction model (extracted from existing code)
|   |-- __init__.py
|   |-- prediction.py            # predict() function, weighted average model
|   |-- box_scores.py            # NBA CDN box score fetching + parsing
|   |-- odds_client.py           # the-odds-api client (live + historical)
|   |-- name_matching.py         # Fuzzy player name matching
|   |-- constants.py             # TEAM_MAP, stat mapping, market keys
|
|-- jobs/
|   |-- __init__.py
|   |-- scanner.py               # Nightly pick scanner (main entry point)
|   |-- grader.py                # Morning result grader (main entry point)
|   |-- daily_summary.py         # Compute daily_summary row after grading
|
|-- migrations/
|   |-- alembic.ini
|   |-- env.py
|   |-- versions/
|       |-- 001_initial_schema.py
|
|-- static/
|   |-- index.html               # Landing page (existing, enhanced)
|
|-- tests/
|   |-- __init__.py
|   |-- conftest.py              # Fixtures: test DB, test client, mock APIs
|   |-- test_prediction.py       # Unit tests for predict()
|   |-- test_name_matching.py    # Unit tests for fuzzy matching
|   |-- test_scanner.py          # Integration tests for scanner job
|   |-- test_grader.py           # Integration tests for grader job
|   |-- test_api_picks.py        # API endpoint tests
|   |-- test_api_auth.py         # Auth flow tests
|   |-- test_api_track_record.py # Track record endpoint tests
|
|-- data/                        # Existing cached backtest data (gitignored in prod)
|
|-- backtest_real.py             # Existing - keep for development/research
|-- strategy_backtest.py         # Existing - keep for development/research
|-- backtest_engine.py           # Existing - keep for development/research
|
|-- pyproject.toml               # Project metadata + dependencies
|-- Dockerfile                   # Multi-stage build
|-- docker-compose.yml           # Local dev (app + postgres)
|-- .env.example                 # Template for env vars
|-- Procfile                     # Railway deployment (web + worker)
|-- railway.toml                 # Railway config
```

---

## 3. Database Schema

### 3.1 users

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key     VARCHAR(64) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255),
    subscription_status VARCHAR(20) DEFAULT 'inactive',
        -- 'active', 'inactive', 'past_due', 'canceled', 'trialing'
    subscription_id VARCHAR(255),
    plan         VARCHAR(20) DEFAULT 'free',
        -- 'free', 'pro'
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);
```

### 3.2 picks

```sql
CREATE TABLE picks (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    player_name     VARCHAR(100) NOT NULL,
    stat_type       VARCHAR(10) NOT NULL,
        -- 'pts', 'reb', 'ast', 'fg3m'
    line            NUMERIC(5,1) NOT NULL,
    prediction      NUMERIC(5,1) NOT NULL,
    edge_pct        NUMERIC(5,1) NOT NULL,
    under_odds      INTEGER NOT NULL,
    game            VARCHAR(20) NOT NULL,
        -- e.g., 'LAL @ BOS'
    book            VARCHAR(50) NOT NULL,
    confidence_tier VARCHAR(10) NOT NULL,
        -- 'A' (25%+ edge), 'B' (20-25%), 'C' (15-20%)
    player_avg_min  NUMERIC(4,1),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_picks_date ON picks(date);
CREATE INDEX idx_picks_date_stat ON picks(date, stat_type);
```

### 3.3 results

```sql
CREATE TABLE results (
    id              SERIAL PRIMARY KEY,
    pick_id         INTEGER UNIQUE NOT NULL REFERENCES picks(id),
    actual_value    NUMERIC(5,1) NOT NULL,
    won             BOOLEAN NOT NULL,
    push            BOOLEAN NOT NULL DEFAULT FALSE,
    profit_flat100  NUMERIC(7,2) NOT NULL,
        -- P/L on a flat $100 bet: +90.91 win, -100 loss, 0 push
    graded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_results_pick_id ON results(pick_id);
```

### 3.4 daily_summary

```sql
CREATE TABLE daily_summary (
    id          SERIAL PRIMARY KEY,
    date        DATE UNIQUE NOT NULL,
    total_picks INTEGER NOT NULL,
    wins        INTEGER NOT NULL,
    losses      INTEGER NOT NULL,
    pushes      INTEGER NOT NULL,
    win_rate    NUMERIC(5,2),
    roi         NUMERIC(7,2),
    profit      NUMERIC(9,2),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_daily_summary_date ON daily_summary(date);
```

### Entity Relationship

```
users (standalone - no FK to picks)

picks 1 ---> 0..1 results  (pick_id FK)

daily_summary (derived aggregate, computed from picks JOIN results)
```

Users do NOT own picks. Picks are global -- all subscribers see the same picks. The user table only controls access gating.

---

## 4. API Design

### 4.1 Authentication Flow

```
POST /auth/register
  Body: { email, password }
  Returns: { api_key, message }
  Notes: Creates Stripe customer, returns API key immediately.
         User starts on 'free' plan (can see track record, cannot see today's picks).

POST /auth/login
  Body: { email, password }
  Returns: { api_key }

All authenticated endpoints use header:
  X-API-Key: <api_key>
```

### 4.2 Subscription Gating

| Endpoint | Auth Required | Subscription Required |
|----------|--------------|----------------------|
| GET /public/track-record | No | No |
| POST /auth/register | No | No |
| POST /auth/login | No | No |
| POST /webhooks/stripe | No (Stripe signature) | No |
| GET /account | API key | No |
| GET /track-record | API key | No |
| GET /track-record/recent | API key | No |
| GET /picks/today | API key | Yes (active sub) |
| GET /picks/{date} | API key | Yes (active sub) |

Rationale: Track record is visible to all authenticated users (including free) to drive conversion. Only actual picks require a paid subscription.

### 4.3 Endpoint Specifications

**GET /picks/today**
```json
{
  "date": "2026-04-12",
  "picks": [
    {
      "player": "LeBron James",
      "stat": "pts",
      "line": 25.5,
      "prediction": 20.1,
      "edge_pct": 21.2,
      "under_odds": -115,
      "game": "LAL @ BOS",
      "book": "DraftKings",
      "confidence": "B"
    }
  ],
  "count": 8,
  "generated_at": "2026-04-12T01:30:00Z"
}
```

**GET /track-record**
```json
{
  "overall": {
    "total_picks": 1247,
    "wins": 712,
    "losses": 510,
    "pushes": 25,
    "win_rate": 58.3,
    "roi": 7.2,
    "profit_flat100": 4830.00,
    "first_pick_date": "2026-01-01",
    "last_graded_date": "2026-04-11"
  },
  "by_stat": {
    "pts": { "picks": 400, "win_rate": 57.1, "roi": 5.8 },
    "reb": { "picks": 310, "win_rate": 59.2, "roi": 8.1 },
    "ast": { "picks": 287, "win_rate": 58.8, "roi": 7.5 },
    "fg3m": { "picks": 250, "win_rate": 59.1, "roi": 8.6 }
  },
  "by_month": [
    { "month": "2026-01", "picks": 180, "win_rate": 56.2, "roi": 4.1 },
    { "month": "2026-02", "picks": 220, "win_rate": 59.1, "roi": 8.3 }
  ],
  "by_confidence": {
    "A": { "picks": 200, "win_rate": 63.5, "roi": 14.2 },
    "B": { "picks": 450, "win_rate": 58.1, "roi": 7.0 },
    "C": { "picks": 597, "win_rate": 55.8, "roi": 3.1 }
  }
}
```

**GET /track-record/recent**
```json
{
  "last_7_days": {
    "picks": 42, "wins": 26, "losses": 15, "pushes": 1,
    "win_rate": 63.4, "roi": 12.1, "profit": 508.00
  },
  "last_30_days": {
    "picks": 180, "wins": 106, "losses": 71, "pushes": 3,
    "win_rate": 59.9, "roi": 8.4, "profit": 1512.00
  },
  "daily_results": [
    { "date": "2026-04-11", "picks": 7, "wins": 5, "losses": 2, "profit": 254.55 }
  ]
}
```

**GET /public/track-record** -- Returns the same shape as GET /track-record but served without auth. Used by the landing page JavaScript to populate stats dynamically.

### 4.4 Rate Limiting

| Tier | Rate Limit |
|------|-----------|
| Free (no sub) | 30 req/min |
| Pro (active sub) | 120 req/min |
| Unauthenticated | 10 req/min (public endpoints only) |

Implementation: In-memory token bucket per API key (or IP for unauthenticated). Use a FastAPI dependency that checks a dict of `{key: (tokens, last_refill_time)}`. No Redis needed at this scale.

If the user base grows beyond a single process, swap to Redis-backed rate limiting.

---

## 5. Cron Jobs

### 5.1 Nightly Scanner (9:00 PM ET)

Purpose: Fetch tonight's prop lines, run prediction model, store qualifying picks.

```
Flow:
1. Query the-odds-api.com /v4/sports/basketball_nba/events
   for today's games
2. For each event, fetch player prop markets:
   player_points, player_rebounds, player_assists, player_threes
3. For each prop line:
   a. Look up player history from box score cache (core/box_scores.py)
   b. Check avg minutes >= 25 over last 10 games
   c. Run predict() from core/prediction.py
   d. Compute edge_pct = (line - prediction) / line * 100
   e. If edge_pct >= 15%: store as a pick
4. Assign confidence_tier:
   A = 25%+ edge
   B = 20-24.9% edge
   C = 15-19.9% edge
5. INSERT all qualifying picks into picks table
6. Log: date, games scanned, props evaluated, picks generated
```

**API budget**: ~1 request for events + 1 per game for props. Typical NBA night = 5-8 games = 6-9 requests. Well within 10K/month budget at $79/mo.

**Player history**: The scanner needs historical box scores to run the prediction model. On first run (or periodically), backfill box scores for the current season from cdn.nba.com. Cache each game's box score to disk or DB. The `load_all_box_scores()` pattern from `strategy_backtest.py` is the template.

**Cron entry** (Railway or system crontab):
```
0 21 * * * python -m jobs.scanner
```

### 5.2 Morning Grader (10:00 AM ET next day)

Purpose: After all games are final, grade each pick against actual box scores.

```
Flow:
1. Query picks table for yesterday's date WHERE no matching result exists
2. For each ungraded pick:
   a. Fetch box score for the relevant game from cdn.nba.com
   b. Find the player in the box score (using core/name_matching.py)
   c. Get actual stat value
   d. Grade: won = (actual < line), push = (actual == line)
   e. Compute profit_flat100:
      won  -> +100 * (decimal_odds - 1) where decimal = american_to_decimal(under_odds)
      loss -> -100
      push -> 0
   f. INSERT into results table
3. Compute daily_summary row:
   total_picks, wins, losses, pushes, win_rate, roi, profit
4. INSERT/UPSERT into daily_summary table
```

**Timing**: NBA games end by ~12:30 AM ET at the latest. Box scores are available on cdn.nba.com within minutes. A 10 AM grading window is conservative and safe.

**Cron entry**:
```
0 10 * * * python -m jobs.grader
```

### 5.3 Box Score Backfill (weekly)

Purpose: Keep local box score cache current for the prediction model.

```
0 6 * * 0 python -m jobs.backfill_box_scores
```

Fetches any missing box scores for the current season. Free, no API key needed.

---

## 6. Core Module Extraction

The existing code in `strategy_backtest.py` and `backtest_real.py` has duplicated logic. Extract into `core/`:

| Source Function | Target Module | Notes |
|----------------|---------------|-------|
| `predict()` from strategy_backtest.py | `core/prediction.py` | Unchanged -- weighted avg model |
| `load_all_box_scores()` from strategy_backtest.py | `core/box_scores.py` | Add live fetch, not just file cache |
| `extract_stats()` from backtest_real.py | `core/box_scores.py` | Merge with above |
| `match_name()` from backtest_real.py | `core/name_matching.py` | Standalone |
| `american_to_decimal()` from strategy_backtest.py | `app/utils/odds.py` | Utility |
| `kelly_bet()` from strategy_backtest.py | `app/utils/odds.py` | For future use |
| `TEAM_MAP` from backtest_real.py | `core/constants.py` | Single source of truth |
| `fetch_json()` from backtest_real.py | `core/odds_client.py` | Wrap with retry + rate limit |
| `get_historical_props()` from backtest_real.py | `core/odds_client.py` | Add live props endpoint |
| `get_box_score()` from backtest_real.py | `core/box_scores.py` | With caching |

---

## 7. Stripe Integration

### 7.1 Flow

```
1. User registers -> auth_service creates Stripe customer
2. User visits landing page -> clicks "Subscribe $15/mo"
3. Stripe Checkout session redirected (server creates session via Stripe API)
4. User completes payment on Stripe-hosted page
5. Stripe sends webhook to POST /webhooks/stripe
6. Webhook handler updates user.subscription_status = 'active'
7. Subscription middleware checks status on each /picks request
```

### 7.2 Webhook Events to Handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Set subscription_status='active', store subscription_id |
| `customer.subscription.updated` | Update status (active/past_due/canceled) |
| `customer.subscription.deleted` | Set status='canceled', plan='free' |
| `invoice.payment_failed` | Set status='past_due' |

### 7.3 Checkout Endpoint

Add `POST /billing/create-checkout-session` (auth required):
- Creates Stripe Checkout session with price ID for $15/mo plan
- Returns `{ checkout_url }` for the frontend to redirect to

---

## 8. Landing Page

The existing `index.html` serves as the landing page. Enhance it to:

1. Fetch `/public/track-record` on page load via JavaScript
2. Display: overall win rate, ROI, total picks, profit
3. Show recent daily results in a table
4. Display "Subscribe $15/mo" CTA button
5. Show stat breakdown and confidence tier performance

The landing page is fully static HTML + vanilla JS. No framework needed. Served by FastAPI's `StaticFiles` mount.

---

## 9. Deployment Architecture

### Railway (recommended for simplicity)

```
railway.toml:
  [build]
    builder = "dockerfile"

  [deploy]
    startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

Procfile:
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
  scanner: python -m jobs.scanner  (triggered by Railway cron)
  grader: python -m jobs.grader    (triggered by Railway cron)
```

Railway provides:
- PostgreSQL addon (free tier for dev, $5/mo for prod)
- Cron jobs (built-in)
- Custom domains
- Auto-deploy from GitHub

### VPS Alternative

If deploying to a VPS instead:
- Docker Compose with app + postgres containers
- System crontab for scanner and grader
- Caddy or nginx reverse proxy with auto-TLS
- Supervisord or systemd for process management

### Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sportsedge
ODDS_API_KEY=077a2076a8f81c71bd1178368809cf8b
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
JWT_SECRET=<random 64 char string>
ALLOWED_ORIGINS=https://sportsedge.app,http://localhost:3000
```

---

## 10. Key Design Decisions

### ADR-001: Unders Only, No Overs

**Context**: The backtesting data shows unders have a statistical edge. Overs are noisier.

**Decision**: API serves unders only. The `side` column is implicit (always "under"). This simplifies the pick schema and subscriber messaging.

**Rationale**: Focus on the proven edge. Can expand to overs later as a premium tier if the model validates.

### ADR-002: Flat $100 Profit Tracking (Not Kelly)

**Context**: Kelly sizing depends on bankroll, which varies per user. Track record needs a universal metric.

**Decision**: All profit tracking uses flat $100 per pick. Kelly sizing info can be added as an optional field but the official track record is flat-bet based.

**Rationale**: Industry standard for pick services. Transparent, comparable, not gameable.

### ADR-003: Global Picks, Not Per-User

**Context**: Should picks be personalized per user?

**Decision**: No. All subscribers see identical picks. The prediction model runs once nightly, generates picks, done.

**Rationale**: Simpler architecture. Consistent track record. No personalization complexity. The edge comes from the model, not customization.

### ADR-004: API Key Auth, Not JWT for API Access

**Context**: API keys vs JWT for subscriber authentication.

**Decision**: API keys for programmatic access (X-API-Key header). JWT only for the web login flow (short-lived, httpOnly cookie).

**Rationale**: API keys are simpler for subscribers who want to integrate programmatically. No token refresh complexity. Keys are long-lived, revocable from the account page.

### ADR-005: In-Memory Rate Limiting (No Redis)

**Context**: Rate limiting approach for a small-to-medium subscriber base.

**Decision**: In-process token bucket stored in a Python dict. No external dependency.

**Rationale**: At expected scale (< 1000 subscribers), a single FastAPI process handles all traffic. Redis adds operational complexity with no benefit. Migrate to Redis if horizontal scaling becomes necessary.

### ADR-006: Async SQLAlchemy with asyncpg

**Context**: Database driver choice.

**Decision**: Use SQLAlchemy 2.0 async with asyncpg driver.

**Rationale**: FastAPI is async-native. asyncpg is the fastest PostgreSQL driver for Python. SQLAlchemy 2.0 has mature async support. Alembic handles migrations.

---

## 11. Dependencies

```
# pyproject.toml [project.dependencies]
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
stripe>=9.0.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
httpx>=0.27.0           # For async HTTP calls to odds API and NBA CDN
```

Dev dependencies:
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx                   # For TestClient
factory-boy>=3.3.0
```

---

## 12. Implementation Plan (Ordered by Priority)

### Phase 1: Foundation (get picks flowing)
1. Set up project structure, pyproject.toml, Docker Compose
2. Create `core/` modules by extracting from existing scripts
3. Write unit tests for `predict()`, `match_name()`, odds math
4. Database schema + Alembic migrations
5. Scanner job (`jobs/scanner.py`) -- nightly pick generation
6. Grader job (`jobs/grader.py`) -- morning result grading
7. Manual test: run scanner, wait for games, run grader, verify results

### Phase 2: API (serve the data)
1. FastAPI app with config, database session
2. API key auth middleware
3. `/picks/today` and `/picks/{date}` endpoints
4. `/track-record` and `/track-record/recent` endpoints
5. `/public/track-record` (no auth)
6. Rate limiting middleware
7. Integration tests for all endpoints

### Phase 3: Billing (monetize)
1. Auth endpoints: register, login
2. Stripe customer creation on register
3. Checkout session creation endpoint
4. Stripe webhook handler
5. Subscription status middleware
6. Account endpoint

### Phase 4: Landing Page (convert visitors)
1. Enhance index.html with public track record fetch
2. Subscribe CTA with Stripe Checkout redirect
3. Login/register forms
4. Deploy to Railway with custom domain

### Phase 5: Expansion (future)
1. MLB player props (same architecture, new odds markets)
2. NFL player props (seasonal)
3. Telegram/Discord bot for pick notifications
4. Enhanced model (opponent adjustments, pace factors, rest days)
5. Premium tiers (A-tier only picks, early access)

---

## 13. Security Considerations

1. **API keys**: Generated with `secrets.token_urlsafe(32)` -- 256 bits of entropy
2. **Passwords**: Hashed with bcrypt via passlib
3. **Stripe webhooks**: Verified with `stripe.Webhook.construct_event()` using webhook secret
4. **CORS**: Restricted to allowed origins via environment variable
5. **SQL injection**: Prevented by SQLAlchemy parameterized queries (never raw SQL)
6. **Rate limiting**: Prevents abuse and API cost overruns
7. **Odds API key**: Stored in environment variable, never in code (note: current code has it hardcoded -- MUST move to env var before deployment)
8. **HTTPS**: Enforced at the reverse proxy / Railway level

---

## 14. Monitoring and Observability

1. **Structured logging**: Python `logging` with JSON formatter, log to stdout for Railway/Docker
2. **Job alerts**: Scanner and grader log success/failure counts. Add a simple health check endpoint `GET /health` that returns job last-run timestamps from a `job_runs` table
3. **Odds API budget tracking**: Log remaining requests from `x-requests-remaining` response header. Alert when below 1000.
4. **Error tracking**: Sentry (free tier) for exception capture in production

---

## 15. Sequence Diagrams

### Nightly Scanner Flow

```
sequenceDiagram
    participant Cron
    participant Scanner
    participant OddsAPI as the-odds-api
    participant NBA as cdn.nba.com
    participant DB as PostgreSQL

    Cron->>Scanner: Trigger at 9pm ET
    Scanner->>OddsAPI: GET /v4/sports/basketball_nba/events
    OddsAPI-->>Scanner: Tonight's games
    loop Each game
        Scanner->>OddsAPI: GET /events/{id}/odds (player props)
        OddsAPI-->>Scanner: Prop lines
    end
    Scanner->>NBA: Fetch recent box scores (history)
    NBA-->>Scanner: Player game logs
    Scanner->>Scanner: predict() for each prop
    Scanner->>Scanner: Filter: edge >= 15%, min >= 25
    Scanner->>DB: INSERT qualifying picks
    Scanner->>Scanner: Log summary
```

### Morning Grader Flow

```
sequenceDiagram
    participant Cron
    participant Grader
    participant NBA as cdn.nba.com
    participant DB as PostgreSQL

    Cron->>Grader: Trigger at 10am ET
    Grader->>DB: SELECT ungraded picks for yesterday
    loop Each pick
        Grader->>NBA: GET box score for game
        NBA-->>Grader: Player stats
        Grader->>Grader: Find player, get actual value
        Grader->>Grader: Grade: won/loss/push, compute profit
        Grader->>DB: INSERT result
    end
    Grader->>DB: UPSERT daily_summary
    Grader->>Grader: Log summary
```

### Subscriber API Request Flow

```
sequenceDiagram
    participant Client
    participant RateLimit as Rate Limiter
    participant Auth as API Key Auth
    participant Sub as Subscription Check
    participant API as FastAPI Handler
    participant DB as PostgreSQL

    Client->>RateLimit: GET /picks/today (X-API-Key: xxx)
    RateLimit->>RateLimit: Check token bucket
    alt Over limit
        RateLimit-->>Client: 429 Too Many Requests
    end
    RateLimit->>Auth: Pass through
    Auth->>DB: SELECT user WHERE api_key = xxx
    alt Invalid key
        Auth-->>Client: 401 Unauthorized
    end
    Auth->>Sub: Pass user object
    Sub->>Sub: Check subscription_status == 'active'
    alt No subscription
        Sub-->>Client: 403 Subscription Required
    end
    Sub->>API: Pass through
    API->>DB: SELECT picks WHERE date = today
    DB-->>API: Pick rows
    API-->>Client: 200 { picks: [...] }
```

# Technical Analysis: RaresPetrisor22/predicting-nba-games-ml

**Date**: 2026-04-13
**Source**: https://github.com/RaresPetrisor22/predicting-nba-games-ml
**Live Dashboard**: https://predict-nba-ml.streamlit.app/

---

## 1. Repository Structure

```
predicting-nba-games-ml/
├── .github/workflows/
│   ├── daily_scrape.yml          # Daily at 10:00 UTC - scrape + predict
│   └── weekly_retrain.yml        # Monday 10:00 UTC - retrain model
├── .streamlit/                   # Streamlit config
├── assets/                       # Dashboard screenshots
├── data/
│   ├── standings/                # Raw HTML schedule pages from BBRef
│   ├── scores/                   # Raw HTML box score pages from BBRef
│   ├── nba_games.csv             # Parsed raw game stats
│   ├── nba_games_processed.csv   # Feature-engineered dataset
│   └── predictions.csv           # Historical predictions with actuals
├── scripts/
│   ├── scrape_games.py           # Entry: scrape -> parse -> engineer -> save
│   ├── predict_tonight.py        # Entry: get today's games -> predict
│   └── train_model.py            # Entry: build features -> train pipeline
├── src/
│   ├── scraping/
│   │   ├── scraper.py            # BBRef HTML fetcher (standings + box scores)
│   │   └── parser.py             # HTML -> CSV parser (box score extraction)
│   ├── features/
│   │   └── feature_engineer.py   # Rolling averages, Elo, opponent history
│   └── model/
│       └── train.py              # LogReg pipeline, TimeSeriesSplit CV
├── app.py                        # Streamlit dashboard (4 tabs)
├── model_pipeline.pkl            # Serialized StandardScaler + LogReg
├── requirements.txt
├── LICENSE (MIT)
└── README.md
```

---

## 2. Data Scraping Pipeline (Basketball Reference)

### Source
Basketball Reference (`basketball-reference.com`), seasons 2016-present (currently ~12,689 games).

### Scraper (`src/scraping/scraper.py`)

**Two-stage scraping:**

1. **Stage 1 - Schedule Pages**: Fetches monthly schedule HTMLs from
   `basketball-reference.com/leagues/NBA_{season}_games-{month}.html`
   - Saves to `data/standings/`
   - Smart re-scraping: only re-fetches current month and previous month for active season
   - Skips already-downloaded months for historical seasons

2. **Stage 2 - Box Scores**: Parses schedule HTMLs for box score links, fetches each game's box score page
   - Saves to `data/scores/{game_id}.html`
   - Deduplication: skips games already in `nba_games.csv` (tracked by game ID)

**Rate Limiting:**
- `sleep_time * attempt_number` between requests (5s, 10s, 15s on retries)
- 3 retries max per URL
- User-Agent header: `Mozilla/5.0 (Windows NT 10.0; Win64; x64)`

**Upcoming Games Detection** (`scrape_upcoming_games()`):
- Parses today's schedule from the current month's standings HTML
- Uses `csk` (chronological sort key) attribute on date cells to match today's date
- Creates dummy rows for each matchup (one home, one away) with zeroed stats

### Parser (`src/scraping/parser.py`)

Extracts from each box score HTML:
- Line score (final team scores)
- Basic stats table (FG, FGA, 3P, etc.)
- Advanced stats table (TS%, eFG%, ORtg, DRtg, etc.)
- Handles commented-out HTML that BBRef uses for some tables
- Combines team stats with opponent stats (suffix `_opp`)
- Adds metadata: home/away, season, date, win/loss

---

## 3. Feature Engineering (109 Features)

### Source: `src/features/feature_engineer.py`

### Pipeline Order
```
load_raw_data -> clean_data -> create_target -> compute_rolling_averages
    -> keep_home_games_only -> compute_elo_feature
```

### Step 1: Data Cleaning
Drops columns: `mp_opp`, `index_opp`, `gmsc`, `+/-`, `gmsc_opp`, `+/-_opp`, `total`, `total_opp`
Fills NaN in `ft%` and `ft%_opp` with 0.

### Step 2: Target Creation
`target = won.astype(int)` (binary: 1 = home team win)

### Step 3: Rolling Averages (10-game window)

**Base stats rolled (33 columns):**
```
fg, fga, fg%, 3p, 3pa, 3p%, ft, fta, ft%,
orb, drb, trb, ast, stl, blk, tov, pf,
ts%, efg%, 3par, ftr,
orb%, drb%, trb%, ast%, stl%, blk%, tov%, usg%,
ortg, drtg,
won, pts
```

**Rolling computation:**
- Window: 10 games (`rolling(10, closed='left')`)
- `closed='left'` = EXCLUDES current game (proper no-leak)
- Grouped by team
- Column naming: `{stat}_roll10`

**Three categories of rolling features:**

| Category | Count | Description |
|----------|-------|-------------|
| Team rolling stats | ~33 | `fg_roll10`, `fg%_roll10`, `ortg_roll10`, etc. |
| Opponent rolling stats | ~33 | `fg_opp_roll10`, `drtg_opp_roll10`, etc. (how opponents performed against this team) |
| Opponent's own history | ~33 | `fg_roll10_opp_history`, etc. (tonight's opponent's recent form) |

**Opponent History Lookup (key technique):**
The code creates a lookup table of each team's rolling stats, then merges them back on `(game_id, opponent_team)`. This gives you: "What has tonight's opponent been averaging recently?" -- a crucial feature.

**So the rolling features alone produce approximately 99 columns** (33 x 3 categories).

### Step 4: Home Games Only
Filters to home team perspective only (each game appears once).
Drops `home` and `home_opp` columns (always 1/0 after filter).

### Step 5: Elo Ratings (adds 2 features)
- `home_elo`
- `away_elo`

### Approximate Feature Count Breakdown

| Feature Group | Approx Count |
|---------------|--------------|
| Team rolling 10-game averages | ~31 (33 minus won, pts kept as raw) |
| Opponent rolling averages (how opps do vs this team) | ~31 |
| Opponent's own recent history | ~31 |
| Elo ratings (home_elo, away_elo) | 2 |
| Remaining raw columns (season, won, pts, etc.) | ~14 |
| **Total before training drops** | **~109** |

### Training-Time Feature Drops
`prepare_training_data()` additionally drops:
- All string/object columns (team names, dates, IDs)
- `target`, `pts`, `pts_opp`, `won` (leakage prevention)
- `usg%_roll10`, `usg%_opp_roll10`, `usg%_roll10_opp_history` (dropped, possibly noisy)
- `mp` (minutes played)

**Effective feature count for model input: ~100-105 numeric features.**

---

## 4. Custom Elo Implementation

### Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Starting Elo | 1500 | All teams begin here |
| Mean reversion target | 1505 | Slight above-1500 target (compensates for expansion/contraction) |
| Mean reversion rate | 25% toward 1505 | Applied at season boundary |
| Base K-factor | 20 | Before MOV scaling |
| MOV exponent | 0.8 | Margin of victory scaling |
| MOV base constant | 3 | Added to MOV before exponent |
| Elo-diff dampening | 7.5 + 0.006 * abs(elo_diff) | Reduces K when Elo gap is large |

### K-Factor Formula

```python
k = 20 * ((mov + 3) ** 0.8) / (7.5 + 0.006 * abs(home_elo - away_elo))
```

**Interpretation:**
- Large blowouts increase K (bigger rating change)
- Large Elo differences decrease K (upset of a strong favorite moves ratings less -- prevents overreaction)
- The `+3` ensures even a 1-point game has meaningful K
- The `0.8` exponent provides diminishing returns on margin

### Update Rule

```python
E_home = 1 / (1 + 10**((away_elo - home_elo) / 400))  # Standard Elo expected score
new_home_elo = home_elo + k * (actual_result - E_home)
new_away_elo = away_elo + k * (away_result - E_away)
```

### Season Mean Reversion

```python
if new_season:
    for team in teams_dict:
        teams_dict[team] = teams_dict[team] * 0.75 + 1505 * 0.25
```

**25% regression toward 1505** at each season boundary. This handles:
- Roster turnover
- Prevents runaway ratings
- The 1505 target (not 1500) is a common technique to account for the average team being slightly above default due to new expansion teams starting at 1500

### Elo is Computed In-Order
The code iterates row by row (`itertuples()`), updating the `teams_dict` dictionary. Elo for each game uses the **pre-game** ratings, then updates after. This is correct causal ordering -- no future leakage.

---

## 5. Model Training

### Source: `src/model/train.py`

### Model Architecture

```python
model = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=200, C=0.01, tol=0.001)
)
```

| Hyperparameter | Value | Notes |
|----------------|-------|-------|
| Scaler | StandardScaler | Z-score normalization |
| Model | LogisticRegression | Chosen for calibrated probabilities |
| C (inverse regularization) | 0.01 | **Strong L2 regularization** (default is 1.0) |
| max_iter | 200 | Convergence iterations |
| tol | 0.001 | Convergence tolerance |
| solver | lbfgs (default) | Not explicitly set |

**Key insight: C=0.01 is extremely strong regularization.** This heavily constrains the coefficients, preventing overfitting to the ~100 correlated features. This is a deliberate choice for sports prediction where signal-to-noise is low.

### No XGBoost in Code
Despite the README mentioning tree-based models were evaluated, **the codebase contains only LogisticRegression**. The XGBoost comparison was likely done in exploration/notebooks not committed to the repo. The README states LogReg was chosen for "superior probability calibration."

### No Explicit Calibration
There is no `CalibratedClassifierCV` or Platt scaling in the code. They rely on LogisticRegression's **native probability calibration** (logistic function outputs are inherently calibrated when the model is well-specified). The dashboard shows calibration curves, suggesting they validate calibration but don't apply post-hoc correction.

### Train/Test Split

```python
def time_split(X, y, test_size=0.2):
    return train_test_split(X, y, test_size=0.2, shuffle=False)
```

**`shuffle=False`** is critical -- preserves temporal ordering. The last 20% of games (most recent season+) serve as validation.

### TimeSeriesSplit Cross-Validation

```python
tscv = TimeSeriesSplit(n_splits=5)
scores = cross_val_score(model, X, y, cv=tscv, scoring="accuracy")
```

- 5 expanding-window folds
- Training data grows with each fold
- Only trains on past, validates on future
- Used on training set only (not full data)
- Scoring metric: accuracy (not log loss -- a minor weakness)

### Training Pipeline Flow

```
1. prepare_training_data() -- drop leaky/string columns
2. time_split() -- 80/20 temporal split, no shuffle
3. cross_validate_model() -- 5-fold TimeSeriesSplit on train set
4. train_and_evaluate() -- fit on train, score on validation
5. retrain_full() -- refit on ALL data for production model
6. save_model() -- joblib dump to model_pipeline.pkl
```

### Reported Performance
- **Log loss: 0.620** on 2026 season predictions
- Cross-validation accuracy reported but exact number not in code

---

## 6. Prediction Pipeline (`scripts/predict_tonight.py`)

### Flow
1. Scrape today's schedule from BBRef
2. Create dummy rows (zero stats) for tonight's games
3. Append to historical data
4. Run full feature engineering pipeline (rolling averages use historical data, Elo uses accumulated ratings)
5. Extract tonight's games (tail of engineered df)
6. Drop training columns via `prepare_training_data()`
7. Load serialized model, call `predict_proba()`
8. Save predictions with `home_prob_win` and `away_prob_win`
9. Append to `data/predictions.csv` (with deduplication check)
10. `actual` column set to -1 (filled later when results are scraped)

### Backfilling Actuals
In `scrape_games.py`, after daily scraping:
```python
preds_df.update(scraped_df[['actual']])
```
This updates the `actual` column in `predictions.csv` once game results are available.

---

## 7. Streamlit Dashboard (`app.py`)

### Four Tabs

1. **Tonight's Predictions**
   - Win probability bars for each matchup
   - Expandable head-to-head stat cards (last 10 games)
   - 12 metrics compared: pts, fg%, 3p%, ft%, reb, ast, stl, blk, tov, ortg, drtg, win_rate

2. **Team Analytics**
   - Select any team
   - Last 10 games table with basic + advanced stats
   - Basic: FG, FGA, 3P, 3PA, FT, FTA, REB, AST, STL, BLK, TOV
   - Advanced: TS%, eFG%, AST%, STL%

3. **Elo Rating Tracker**
   - Plotly line chart of Elo over time
   - Multi-team comparison
   - Methodology explanation in UI

4. **Model Performance**
   - 2026 season accuracy %
   - Log loss value
   - Confusion matrix heatmap
   - Calibration curve (predicted vs actual probability)
   - Feature importance (LogReg coefficients, color-coded positive/negative)
   - Cumulative performance over time

### Styling
- NBA-themed dark UI (#0F172A, #1E293B backgrounds)
- Gold accents (#FCBF49), blue highlights (#1D428A)
- Team logos from NBA CDN via team abbreviations
- `@st.cache_data` for performance

---

## 8. CI/CD Automation

### Daily Workflow (`daily_scrape.yml`)
- **Schedule**: `cron: "0 10 * * *"` (10:00 UTC daily)
- **Also**: `workflow_dispatch` (manual trigger)
- **Steps**: checkout -> Python 3.10 -> install deps -> `scrape_games` + `predict_tonight` -> git commit+push data/
- **Runner**: ubuntu-latest

### Weekly Workflow (`weekly_retrain.yml`)
- **Schedule**: `cron: "0 10 * * 1"` (Monday 10:00 UTC)
- **Also**: `workflow_dispatch`
- **Steps**: checkout -> Python 3.10 -> install deps -> `train_model` -> git commit+push `model_pipeline.pkl`
- **Runner**: ubuntu-latest

---

## 9. What's NOT in This Repo

| Missing Element | Impact |
|-----------------|--------|
| **No odds integration** | No comparison to betting lines, no ROI tracking |
| **No XGBoost code** | Mentioned in README but not in codebase |
| **No backtesting framework** | No systematic historical evaluation |
| **No calibration correction** | Relies on LogReg native calibration only |
| **No hyperparameter tuning** | C=0.01 appears hand-selected, no grid/random search |
| **No feature selection** | All ~100 features used, no importance-based pruning |
| **No home court advantage feature** | Implicitly captured by home-only modeling, but no explicit HCA variable |
| **No rest days / B2B features** | Schedule density not considered |
| **No injury/roster data** | Major predictive signal absent |
| **No pace adjustment** | Raw stats, not per-possession |
| **No opponent-adjusted metrics** | Rolling averages are raw, not SOS-adjusted |
| **No ensemble** | Single model only |

---

## 10. Key Takeaways for Our Work

### What They Do Well
1. **Proper temporal discipline** -- `closed='left'` rolling, `shuffle=False` split, TimeSeriesSplit CV
2. **Elo implementation is solid** -- MOV-adjusted K, season regression, correct causal ordering
3. **Opponent history lookup** is clever -- merging opponent's recent form as features
4. **Strong regularization (C=0.01)** -- appropriate for noisy sports data with correlated features
5. **Automated pipeline** -- daily scrape + predict, weekly retrain, all via GitHub Actions
6. **Production-ready** -- Streamlit dashboard, serialized model, proper CI/CD

### What We Can Improve On
1. **Add rest days / back-to-back features** -- huge predictive signal they're missing
2. **Pace-adjusted stats** -- per-100-possessions normalization
3. **Strength of schedule adjustment** -- weight rolling stats by opponent quality
4. **Odds integration + Kelly criterion** -- they predict but don't evaluate against the market
5. **Ensemble methods** -- stack LogReg + XGBoost + other models
6. **Feature selection** -- use SHAP or permutation importance to prune
7. **Injury data** -- integrate injury reports for lineup-adjusted predictions
8. **Better CV scoring** -- use log loss not accuracy for CV (they use accuracy in `cross_val_score`)
9. **Hyperparameter optimization** -- Optuna/GridSearch for C, regularization type
10. **Backtesting with betting simulation** -- track hypothetical ROI against closing lines

### Their Elo Formula (For Reference)
```python
# K-factor with margin-of-victory scaling
k = 20 * ((mov + 3) ** 0.8) / (7.5 + 0.006 * abs(home_elo - away_elo))

# Season mean reversion (25% toward 1505)
new_elo = old_elo * 0.75 + 1505 * 0.25
```

This is closely based on FiveThirtyEight's NBA Elo methodology (which uses similar MOV scaling and season regression).

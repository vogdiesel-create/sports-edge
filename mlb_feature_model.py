#!/usr/bin/env python3
"""
MLB Feature-Rich Model: Market Correction Approach
====================================================

Same approach that took NHL from -8% to +11% ROI:
1. Uses Pinnacle closing line as the baseline (market's best estimate)
2. Engineers features from game history that the market may underweight
3. XGBoost learns WHEN and HOW MUCH the market is wrong
4. Targets: both totals and moneyline

MLB-specific features beyond NHL:
- Run scoring is higher/more variable → more features around variance
- Weather/park effects (implied from team totals divergence)
- Spread/run line context
- Home/away splits are more meaningful in baseball
"""

import math
import os
import sqlite3
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("ERROR: xgboost required. pip install xgboost")
    sys.exit(1)

from sklearn.metrics import log_loss, brier_score_loss

warnings.filterwarnings("ignore")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "game_lines.db")
BET_SIZE = 100
MIN_HISTORY = 40  # lower than NHL since MLB teams play more frequently

MLB_FULL_TO_ABBREV = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL", "Detroit Tigers": "DET",
    "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA", "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH",
    "Cleveland Indians": "CLE",
}

MLB_ABBREV_TO_FULL = {}
for full, abbr in MLB_FULL_TO_ABBREV.items():
    if abbr not in MLB_ABBREV_TO_FULL or len(full) > len(MLB_ABBREV_TO_FULL[abbr]):
        MLB_ABBREV_TO_FULL[abbr] = full

# Park factors (runs) and dome flags - from mlb_stadiums table
PARK_FACTORS = {
    "COL": 1.28, "CIN": 1.10, "NYY": 1.09, "BOS": 1.08, "ARI": 1.06,
    "PHI": 1.05, "BAL": 1.05, "CHC": 1.05, "CWS": 1.04, "HOU": 1.03,
    "TEX": 1.02, "TOR": 1.02, "MIL": 1.02, "MIN": 1.01, "ATL": 1.01,
    "WSH": 1.00, "LAD": 0.98, "KC": 0.98, "LAA": 0.97, "CLE": 0.96,
    "STL": 0.96, "DET": 0.95, "PIT": 0.94, "NYM": 0.93, "OAK": 0.93,
    "SD": 0.93, "SEA": 0.93, "MIA": 0.92, "TB": 0.91, "SF": 0.90,
}
IS_DOME = {"ARI", "HOU", "TEX", "TOR", "MIL", "SEA", "MIA", "TB"}

# Stadium coordinates for weather lookups
STADIUM_COORDS = {
    "LAA": (33.80, -117.88), "ARI": (33.45, -112.07), "NYM": (40.76, -73.85),
    "PHI": (39.91, -75.17), "DET": (42.34, -83.05), "COL": (39.76, -104.99),
    "BAL": (39.28, -76.62), "CLE": (41.50, -81.69), "BOS": (42.35, -71.10),
    "CHC": (41.95, -87.66), "CWS": (41.83, -87.63), "CIN": (39.10, -84.51),
    "HOU": (29.76, -95.36), "KC": (39.05, -94.48), "LAD": (34.07, -118.24),
    "MIA": (25.78, -80.22), "MIL": (43.03, -87.97), "MIN": (44.98, -93.28),
    "NYY": (40.83, -73.93), "OAK": (37.75, -122.20), "PIT": (40.45, -80.01),
    "SD": (32.71, -117.16), "SEA": (47.59, -122.33), "SF": (37.78, -122.39),
    "STL": (38.62, -90.19), "TB": (27.77, -82.65), "TEX": (32.75, -97.08),
    "TOR": (43.64, -79.39), "WSH": (38.87, -77.01), "ATL": (33.89, -84.47),
}


def load_all_mlb_games():
    """Load all MLB games with closing lines from Pinnacle."""
    conn = sqlite3.connect(DB_PATH)

    # Get game results + totals closing
    games_raw = conn.execute("""
        SELECT DISTINCT event_id, game_date, home_team, away_team,
               score_home, score_away, total_goals, line,
               todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='totals' AND period=0
        AND score_home IS NOT NULL AND score_away IS NOT NULL
        ORDER BY game_date, event_id
    """).fetchall()

    # Deduplicate - take the main line (closest to even odds)
    seen = {}
    for r in games_raw:
        eid = r[0]
        if eid not in seen:
            seen[eid] = r
        else:
            old = seen[eid]
            old_balance = abs((old[8] or 2) - (old[9] or 2))
            new_balance = abs((r[8] or 2) - (r[9] or 2))
            if new_balance < old_balance:
                seen[eid] = r

    games = []
    for eid, r in seen.items():
        h_abbr = MLB_FULL_TO_ABBREV.get(r[2])
        a_abbr = MLB_FULL_TO_ABBREV.get(r[3])
        if not h_abbr or not a_abbr:
            continue
        games.append({
            "event_id": eid,
            "game_date": r[1],
            "home_team": h_abbr,
            "away_team": a_abbr,
            "home_team_full": r[2],
            "away_team_full": r[3],
            "home_score": r[4],
            "away_score": r[5],
            "total_runs": r[4] + r[5],
            "closing_line": r[7],
            "todds_over": r[8],
            "todds_under": r[9],
        })

    df = pd.DataFrame(games)
    df = df.sort_values("game_date").reset_index(drop=True)

    # Load moneyline odds per event
    ml_data = {}
    ml_rows = conn.execute("""
        SELECT event_id, todds_over, todds_under, odds_over, odds_under
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='moneyline' AND period=0
    """).fetchall()
    for r in ml_rows:
        ml_data[r[0]] = {
            "ml_todds_home": r[1], "ml_todds_away": r[2],
            "ml_odds_home": r[3], "ml_odds_away": r[4],
        }

    # Load team totals
    ht_data = {}
    ht_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='home_totals' AND period=0
    """).fetchall()
    for r in ht_rows:
        ht_data[r[0]] = {"ht_line": r[1], "ht_todds_o": r[2], "ht_todds_u": r[3]}

    at_data = {}
    at_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='away_totals' AND period=0
    """).fetchall()
    for r in at_rows:
        at_data[r[0]] = {"at_line": r[1], "at_todds_o": r[2], "at_todds_u": r[3]}

    # Spread (run line)
    spread_data = {}
    sp_rows = conn.execute("""
        SELECT event_id, line, todds_over, todds_under
        FROM pinnacle_closing
        WHERE sport='MLB' AND market='spread' AND period=0
        AND ABS(line) = 1.5
    """).fetchall()
    for r in sp_rows:
        eid = r[0]
        if r[1] < 0:  # home favorite
            spread_data[eid] = {"spread_line": r[1], "sp_todds_fav": r[2], "sp_todds_dog": r[3]}

    # Load pitcher starter data
    starter_data = {}
    try:
        starter_rows = conn.execute("""
            SELECT game_date, home_team, away_team,
                   home_pitcher_id, home_pitcher_name,
                   away_pitcher_id, away_pitcher_name
            FROM mlb_game_starters
        """).fetchall()
        for r in starter_rows:
            key = (r[0], r[1], r[2])
            starter_data[key] = {
                "home_pitcher_id": r[3], "home_pitcher_name": r[4],
                "away_pitcher_id": r[5], "away_pitcher_name": r[6],
            }
        print(f"Loaded {len(starter_data)} game starter records")
    except sqlite3.OperationalError:
        print("No mlb_game_starters table found - run fetch_pitcher_history.py first")

    # Load pitcher game logs for rolling stats
    pitcher_logs = defaultdict(list)  # pitcher_id -> [(date, ip, er, h, bb, k, hr)]
    try:
        log_rows = conn.execute("""
            SELECT pitcher_id, game_date, innings_pitched, earned_runs,
                   hits_allowed, walks, strikeouts, home_runs_allowed
            FROM mlb_pitcher_game_logs
            WHERE game_started = 1
            ORDER BY pitcher_id, game_date
        """).fetchall()
        for r in log_rows:
            pitcher_logs[r[0]].append({
                "date": r[1], "ip": r[2] or 0, "er": r[3] or 0,
                "h": r[4] or 0, "bb": r[5] or 0, "k": r[6] or 0, "hr": r[7] or 0,
            })
        print(f"Loaded game logs for {len(pitcher_logs)} pitchers ({len(log_rows)} total starts)")
    except sqlite3.OperationalError:
        print("No mlb_pitcher_game_logs table found - run fetch_pitcher_history.py first")

    # Load historical weather data (from mlb_weather table in sports_edge.db)
    weather_data = {}
    se_db_path = os.path.join(DATA_DIR, "sports_edge.db")
    try:
        se_conn = sqlite3.connect(se_db_path)
        weather_rows = se_conn.execute("""
            SELECT game_date, team_abbrev, temperature_f, wind_speed_mph, humidity_pct
            FROM mlb_weather
        """).fetchall()
        se_conn.close()
        for r in weather_rows:
            weather_data[(r[0], r[1])] = {
                "temp": r[2] or 72, "wind": r[3] or 5, "humidity": r[4] or 50,
            }
        print(f"Loaded {len(weather_data)} weather records")
    except (sqlite3.OperationalError, Exception) as e:
        print(f"Weather data not available: {e}")

    conn.close()

    # Merge auxiliary data
    for i, row in df.iterrows():
        eid = row["event_id"]
        ml = ml_data.get(eid, {})
        ht = ht_data.get(eid, {})
        at = at_data.get(eid, {})
        sp = spread_data.get(eid, {})
        for k, v in {**ml, **ht, **at, **sp}.items():
            df.at[i, k] = v

        # Merge starter info
        h_abbr = row["home_team"]
        a_abbr = row["away_team"]
        gd = row["game_date"]
        starter = starter_data.get((gd, h_abbr, a_abbr), {})
        df.at[i, "home_pitcher_id"] = starter.get("home_pitcher_id")
        df.at[i, "away_pitcher_id"] = starter.get("away_pitcher_id")
        df.at[i, "home_pitcher_name"] = starter.get("home_pitcher_name")
        df.at[i, "away_pitcher_name"] = starter.get("away_pitcher_name")

    print(f"Loaded {len(df)} MLB games ({df['game_date'].min()} to {df['game_date'].max()})")
    has_pitchers = df["home_pitcher_id"].notna().sum()
    print(f"Games with pitcher data: {has_pitchers}/{len(df)} ({100*has_pitchers/len(df):.1f}%)")

    return df, pitcher_logs, weather_data


def _compute_pitcher_rolling(logs, game_date, n_starts):
    """Compute rolling pitcher stats from last n starts BEFORE game_date."""
    prior = [l for l in logs if l["date"] < game_date]
    if not prior:
        return None
    recent = prior[-n_starts:]
    total_ip = sum(l["ip"] for l in recent)
    if total_ip == 0:
        return None
    total_er = sum(l["er"] for l in recent)
    total_h = sum(l["h"] for l in recent)
    total_bb = sum(l["bb"] for l in recent)
    total_k = sum(l["k"] for l in recent)
    total_hr = sum(l["hr"] for l in recent)
    return {
        "era": (total_er / total_ip) * 9,
        "whip": (total_bb + total_h) / total_ip,
        "k_per_9": (total_k / total_ip) * 9,
        "bb_per_9": (total_bb / total_ip) * 9,
        "hr_per_9": (total_hr / total_ip) * 9,
        "avg_ip": total_ip / len(recent),
        "n_starts": len(recent),
    }


def engineer_features(df, pitcher_logs=None, weather_data=None):
    """
    Build features from game history for each game.
    All features computed using ONLY data available BEFORE the game.
    """
    if pitcher_logs is None:
        pitcher_logs = {}
    if weather_data is None:
        weather_data = {}
    team_games = defaultdict(list)
    features = []

    for i in range(len(df)):
        game = df.iloc[i]
        home = game["home_team"]
        away = game["away_team"]
        date = game["game_date"]

        h_hist = team_games[home]
        a_hist = team_games[away]

        if len(h_hist) < MIN_HISTORY or len(a_hist) < MIN_HISTORY:
            features.append(None)
            team_games[home].append((i, True, game["home_score"], game["away_score"], date))
            team_games[away].append((i, False, game["away_score"], game["home_score"], date))
            continue

        f = {}

        # --- Market features (Pinnacle's view) ---
        f["closing_total_line"] = game.get("closing_line", 8.5)

        to = game.get("todds_over")
        tu = game.get("todds_under")
        if to and tu and to > 1 and tu > 1:
            impl_o = 1.0 / to
            impl_u = 1.0 / tu
            f["market_impl_over"] = impl_o / (impl_o + impl_u)
        else:
            f["market_impl_over"] = 0.5

        # Moneyline implied
        ml_h = game.get("ml_todds_home")
        ml_a = game.get("ml_todds_away")
        if ml_h and ml_a and ml_h > 1 and ml_a > 1:
            ih = 1.0 / ml_h
            ia = 1.0 / ml_a
            f["market_impl_home_win"] = ih / (ih + ia)
        else:
            f["market_impl_home_win"] = 0.5

        # Team totals
        ht_line = game.get("ht_line")
        at_line = game.get("at_line")
        f["home_team_total_line"] = ht_line if ht_line and not pd.isna(ht_line) else f["closing_total_line"] / 2
        f["away_team_total_line"] = at_line if at_line and not pd.isna(at_line) else f["closing_total_line"] / 2
        f["team_totals_sum_vs_line"] = (f["home_team_total_line"] + f["away_team_total_line"]) - f["closing_total_line"]

        # Spread (run line)
        sp_line = game.get("spread_line")
        f["spread_line"] = sp_line if sp_line and not pd.isna(sp_line) else 0

        # --- Team history features ---
        for label, hist in [("home", h_hist), ("away", a_hist)]:
            scores_for = [h[2] for h in hist]
            scores_against = [h[3] for h in hist]
            totals = [h[2] + h[3] for h in hist]
            dates = [h[4] for h in hist]

            # Rolling averages - MLB uses more windows due to higher game frequency
            for wn, w in [("l5", 5), ("l10", 10), ("l20", 20), ("l40", 40), ("season", len(hist))]:
                rf = scores_for[-w:]
                ra = scores_against[-w:]
                rt = totals[-w:]
                f[f"{label}_rf_{wn}"] = np.mean(rf)
                f[f"{label}_ra_{wn}"] = np.mean(ra)
                f[f"{label}_total_{wn}"] = np.mean(rt)
                if wn not in ("season",):
                    f[f"{label}_rf_std_{wn}"] = np.std(rf) if len(rf) > 1 else 0
                    f[f"{label}_total_std_{wn}"] = np.std(rt) if len(rt) > 1 else 0

            # Win rate
            wins = sum(1 for h in hist if h[2] > h[3])
            f[f"{label}_win_pct"] = wins / len(hist)
            wins_l10 = sum(1 for h in hist[-10:] if h[2] > h[3])
            f[f"{label}_win_pct_l10"] = wins_l10 / min(10, len(hist))

            # Home/away splits (very important in MLB)
            home_games = [(h[2], h[3]) for h in hist if h[1]]
            away_games = [(h[2], h[3]) for h in hist if not h[1]]
            if home_games:
                f[f"{label}_home_rf"] = np.mean([g[0] for g in home_games])
                f[f"{label}_home_ra"] = np.mean([g[1] for g in home_games])
            else:
                f[f"{label}_home_rf"] = np.mean(scores_for)
                f[f"{label}_home_ra"] = np.mean(scores_against)
            if away_games:
                f[f"{label}_away_rf"] = np.mean([g[0] for g in away_games])
                f[f"{label}_away_ra"] = np.mean([g[1] for g in away_games])
            else:
                f[f"{label}_away_rf"] = np.mean(scores_for)
                f[f"{label}_away_ra"] = np.mean(scores_against)

            # Streaks
            streak = 0
            for h in reversed(hist):
                if h[2] > h[3]:
                    streak += 1
                else:
                    break
            f[f"{label}_win_streak"] = streak
            loss_streak = 0
            for h in reversed(hist):
                if h[2] < h[3]:
                    loss_streak += 1
                else:
                    break
            f[f"{label}_loss_streak"] = loss_streak

            # Rest days (less important in MLB but still relevant)
            last_date = dates[-1]
            try:
                d1 = datetime.strptime(date, "%Y-%m-%d")
                d2 = datetime.strptime(last_date, "%Y-%m-%d")
                rest = (d1 - d2).days
            except:
                rest = 1
            f[f"{label}_rest_days"] = min(rest, 7)

            # Games played
            f[f"{label}_games_played"] = len(hist)

            # Scoring trend
            if len(scores_for) >= 20:
                f[f"{label}_rf_trend"] = np.mean(scores_for[-5:]) - np.mean(scores_for[-20:])
                f[f"{label}_ra_trend"] = np.mean(scores_against[-5:]) - np.mean(scores_against[-20:])
            else:
                f[f"{label}_rf_trend"] = 0
                f[f"{label}_ra_trend"] = 0

        # --- Matchup / differential features ---
        f["rf_diff_season"] = f["home_rf_season"] - f["away_rf_season"]
        f["ra_diff_season"] = f["home_ra_season"] - f["away_ra_season"]
        f["rf_diff_l10"] = f["home_rf_l10"] - f["away_rf_l10"]
        f["total_diff_l10"] = f["home_total_l10"] - f["away_total_l10"]
        f["win_pct_diff"] = f["home_win_pct"] - f["away_win_pct"]
        f["win_pct_l10_diff"] = f["home_win_pct_l10"] - f["away_win_pct_l10"]
        f["rest_diff"] = f["home_rest_days"] - f["away_rest_days"]

        # Expected total from recent form
        f["form_expected_total"] = (f["home_rf_l10"] + f["away_rf_l10"] +
                                     f["home_ra_l10"] + f["away_ra_l10"]) / 2
        f["form_vs_line"] = f["form_expected_total"] - f["closing_total_line"]

        # Volatility
        f["combined_total_std_l10"] = f["home_total_std_l10"] + f["away_total_std_l10"]

        # Month (hot weather = more runs)
        try:
            f["month"] = int(date.split("-")[1])
        except:
            f["month"] = 6

        # --- Park factor features ---
        pf = PARK_FACTORS.get(home, 1.0)
        f["park_factor"] = pf
        f["is_dome"] = 1 if home in IS_DOME else 0
        # Park-adjusted expected total
        f["park_adj_form_total"] = f["form_expected_total"] * pf
        f["park_adj_vs_line"] = f["park_adj_form_total"] - f["closing_total_line"]
        # Extreme park indicator (Coors, SF, etc.)
        f["park_extreme"] = abs(pf - 1.0)

        # --- Weather features ---
        weather = weather_data.get((date, home)) if weather_data else None
        if weather and home not in IS_DOME:
            f["temperature"] = weather["temp"]
            f["wind_speed"] = weather["wind"]
            f["humidity"] = weather["humidity"]
            # Temperature impact (hot = more runs, cold = fewer)
            f["temp_impact"] = (weather["temp"] - 72) / 20  # normalized around 72F
            # Wind impact (high wind = more runs generally)
            f["wind_impact"] = weather["wind"] / 15  # normalized
        else:
            f["temperature"] = 72  # neutral defaults
            f["wind_speed"] = 5
            f["humidity"] = 50
            f["temp_impact"] = 0
            f["wind_impact"] = 0.33

        # --- Pitcher features ---
        hp_id = game.get("home_pitcher_id")
        ap_id = game.get("away_pitcher_id")

        for prefix, pid in [("hp", hp_id), ("ap", ap_id)]:
            if pid and not pd.isna(pid):
                pid = int(pid)
                logs = pitcher_logs.get(pid, [])
                # Rolling stats over last 3 and 5 starts
                for window_name, window in [("l3", 3), ("l5", 5), ("season", 999)]:
                    stats = _compute_pitcher_rolling(logs, date, window)
                    if stats:
                        f[f"{prefix}_era_{window_name}"] = stats["era"]
                        f[f"{prefix}_whip_{window_name}"] = stats["whip"]
                        f[f"{prefix}_k9_{window_name}"] = stats["k_per_9"]
                        f[f"{prefix}_bb9_{window_name}"] = stats["bb_per_9"]
                        f[f"{prefix}_hr9_{window_name}"] = stats["hr_per_9"]
                        f[f"{prefix}_avg_ip_{window_name}"] = stats["avg_ip"]
                    else:
                        f[f"{prefix}_era_{window_name}"] = 4.5  # league avg defaults
                        f[f"{prefix}_whip_{window_name}"] = 1.3
                        f[f"{prefix}_k9_{window_name}"] = 8.5
                        f[f"{prefix}_bb9_{window_name}"] = 3.2
                        f[f"{prefix}_hr9_{window_name}"] = 1.2
                        f[f"{prefix}_avg_ip_{window_name}"] = 5.0
            else:
                for window_name in ["l3", "l5", "season"]:
                    f[f"{prefix}_era_{window_name}"] = 4.5
                    f[f"{prefix}_whip_{window_name}"] = 1.3
                    f[f"{prefix}_k9_{window_name}"] = 8.5
                    f[f"{prefix}_bb9_{window_name}"] = 3.2
                    f[f"{prefix}_hr9_{window_name}"] = 1.2
                    f[f"{prefix}_avg_ip_{window_name}"] = 5.0

        # Pitcher matchup differentials (recent form)
        f["era_diff_l5"] = f["hp_era_l5"] - f["ap_era_l5"]
        f["whip_diff_l5"] = f["hp_whip_l5"] - f["ap_whip_l5"]
        f["k9_diff_l5"] = f["hp_k9_l5"] - f["ap_k9_l5"]
        f["era_diff_season"] = f["hp_era_season"] - f["ap_era_season"]
        # Combined pitcher quality (lower = better for under)
        f["combined_era_l5"] = f["hp_era_l5"] + f["ap_era_l5"]
        f["combined_whip_l5"] = f["hp_whip_l5"] + f["ap_whip_l5"]
        f["combined_k9_l5"] = f["hp_k9_l5"] + f["ap_k9_l5"]
        # Pitcher vs line (are strong pitchers starting in a game with high total?)
        f["pitcher_era_vs_line"] = f["combined_era_l5"] - f["closing_total_line"]

        features.append(f)

        # Record for future history
        team_games[home].append((i, True, game["home_score"], game["away_score"], date))
        team_games[away].append((i, False, game["away_score"], game["home_score"], date))

    return features


def build_dataset(df, features, target="totals"):
    """Build X, y arrays. target='totals' or 'moneyline'."""
    X_rows = []
    y_rows = []
    indices = []

    for i, f in enumerate(features):
        if f is None:
            continue
        game = df.iloc[i]

        if target == "totals":
            line = game.get("closing_line", 8.5)
            actual = game["total_runs"]
            if actual == line:  # push
                continue
            y = 1 if actual > line else 0
        elif target == "moneyline":
            y = 1 if game["home_score"] > game["away_score"] else 0

        X_rows.append(f)
        y_rows.append(y)
        indices.append(i)

    X = pd.DataFrame(X_rows)
    y = np.array(y_rows)
    return X, y, indices


def run_backtest(target="totals"):
    """Walk-forward backtest with expanding window."""
    df, pitcher_logs, weather_data = load_all_mlb_games()
    print("Engineering features...")
    features = engineer_features(df, pitcher_logs, weather_data)

    valid_count = sum(1 for f in features if f is not None)
    print(f"Valid feature rows: {valid_count} / {len(features)}")

    X, y, indices = build_dataset(df, features, target=target)
    print(f"Dataset: {len(X)} samples, {X.shape[1]} features")
    print(f"Target distribution: {y.mean():.3f} positive rate")

    MIN_TRAIN = 1500
    TEST_CHUNK = 200

    bets = []
    all_preds = []

    i = MIN_TRAIN
    while i < len(X):
        test_end = min(i + TEST_CHUNK, len(X))

        X_train = X.iloc[:i]
        y_train = y[:i]
        X_test = X.iloc[i:test_end]
        y_test = y[i:test_end]
        test_indices = indices[i:test_end]

        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=1.0, reg_lambda=2.0, min_child_weight=10,
            eval_metric="logloss", random_state=42, verbosity=0,
        )
        model.fit(X_train, y_train)
        preds = model.predict_proba(X_test)[:, 1]

        for j, (pred, actual, game_idx) in enumerate(zip(preds, y_test, test_indices)):
            game = df.iloc[game_idx]
            all_preds.append({"pred": pred, "actual": actual})

            if target == "totals":
                to = game.get("todds_over")
                tu = game.get("todds_under")
                if not to or not tu or to <= 1 or tu <= 1:
                    continue

                impl_o = 1.0 / to
                impl_u = 1.0 / tu
                devig_o = impl_o / (impl_o + impl_u)
                devig_u = 1 - devig_o

                edge_over = pred - devig_o
                edge_under = (1 - pred) - devig_u

                line = game["closing_line"]
                actual_total = game["total_runs"]

                if edge_over > 0 and edge_over >= edge_under:
                    won = actual_total > line
                    push = actual_total == line
                    profit = 0 if push else (BET_SIZE * (to - 1) if won else -BET_SIZE)
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "OVER", "line": line,
                        "model_prob": pred, "market_prob": devig_o,
                        "edge": edge_over, "won": won, "push": push,
                        "profit": profit, "odds": to,
                    })
                elif edge_under > 0:
                    won = actual_total < line
                    push = actual_total == line
                    profit = 0 if push else (BET_SIZE * (tu - 1) if won else -BET_SIZE)
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "UNDER", "line": line,
                        "model_prob": 1 - pred, "market_prob": devig_u,
                        "edge": edge_under, "won": won, "push": push,
                        "profit": profit, "odds": tu,
                    })

            elif target == "moneyline":
                ml_h = game.get("ml_todds_home")
                ml_a = game.get("ml_todds_away")
                if not ml_h or not ml_a or ml_h <= 1 or ml_a <= 1:
                    continue

                ih = 1.0 / ml_h
                ia = 1.0 / ml_a
                devig_h = ih / (ih + ia)
                devig_a = 1 - devig_h

                edge_home = pred - devig_h
                edge_away = (1 - pred) - devig_a

                home_won = game["home_score"] > game["away_score"]

                if edge_home > 0 and edge_home >= edge_away:
                    won = home_won
                    profit = BET_SIZE * (ml_h - 1) if won else -BET_SIZE
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "HOME",
                        "model_prob": pred, "market_prob": devig_h,
                        "edge": edge_home, "won": won, "push": False,
                        "profit": profit, "odds": ml_h,
                    })
                elif edge_away > 0:
                    won = not home_won
                    profit = BET_SIZE * (ml_a - 1) if won else -BET_SIZE
                    bets.append({
                        "date": game["game_date"], "home": game["home_team"],
                        "away": game["away_team"], "side": "AWAY",
                        "model_prob": 1 - pred, "market_prob": devig_a,
                        "edge": edge_away, "won": won, "push": False,
                        "profit": profit, "odds": ml_a,
                    })

        i = test_end

    # Feature importance
    print(f"\nTop 20 features:")
    importance = model.feature_importances_
    feat_imp = sorted(zip(X.columns, importance), key=lambda x: x[1], reverse=True)
    for fname, imp in feat_imp[:20]:
        print(f"  {fname:40s} {imp:.4f}")

    # Calibration
    if all_preds:
        preds_arr = np.array([p["pred"] for p in all_preds])
        actuals_arr = np.array([p["actual"] for p in all_preds])
        try:
            ll = log_loss(actuals_arr, preds_arr)
            bs = brier_score_loss(actuals_arr, preds_arr)
            print(f"\nCalibration: log_loss={ll:.4f}, brier_score={bs:.4f}")
        except:
            pass

    # Results
    print(f"\n{'='*60}")
    print(f"  MLB {target.upper()} - FEATURE-RICH XGBoost vs PINNACLE")
    print(f"{'='*60}")
    print(f"  Total bets: {len(bets)}")

    if not bets:
        print("  No bets generated.")
        return

    thresholds = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15]
    print(f"\n  {'Thresh':>7} {'Bets':>6} {'W':>5} {'L':>5} {'WR':>6} "
          f"{'Profit':>10} {'ROI':>8} {'AvgEdge':>8}")
    print(f"  {'-'*60}")

    for thresh in thresholds:
        tb = [b for b in bets if b["edge"] >= thresh]
        if not tb:
            continue
        tw = sum(1 for b in tb if b["won"])
        tl = sum(1 for b in tb if not b["won"] and not b.get("push", False))
        tp = sum(1 for b in tb if b.get("push", False))
        tprofit = sum(b["profit"] for b in tb)
        twagered = BET_SIZE * (len(tb) - tp)
        troi = (tprofit / twagered * 100) if twagered > 0 else 0
        twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
        avg_edge = np.mean([b["edge"] for b in tb]) * 100
        print(f"  {thresh*100:>6.0f}% {len(tb):>6} {tw:>5} {tl:>5} "
              f"{twr:>5.1f}% ${tprofit:>+9.0f} {troi:>+7.2f}% {avg_edge:>+6.1f}%")

    # Side breakdown
    if target == "totals":
        for side in ["OVER", "UNDER"]:
            print(f"\n  --- {side}-only ---")
            for thresh in [0.01, 0.03, 0.05, 0.07, 0.10]:
                tb = [b for b in bets if b["edge"] >= thresh and b["side"] == side]
                if not tb:
                    continue
                tw = sum(1 for b in tb if b["won"])
                tl = sum(1 for b in tb if not b["won"] and not b.get("push"))
                tp = sum(1 for b in tb if b.get("push"))
                tprofit = sum(b["profit"] for b in tb)
                twagered = BET_SIZE * (len(tb) - tp)
                troi = (tprofit / twagered * 100) if twagered > 0 else 0
                twr = tw / (tw + tl) * 100 if (tw + tl) > 0 else 0
                print(f"    {thresh*100:>4.0f}%: {len(tb):>5}B {tw}W {tl}L "
                      f"({twr:.1f}%) ${tprofit:+.0f} ROI {troi:+.1f}%")
    elif target == "moneyline":
        for side in ["HOME", "AWAY"]:
            print(f"\n  --- {side}-only ---")
            for thresh in [0.01, 0.03, 0.05, 0.07, 0.10]:
                tb = [b for b in bets if b["edge"] >= thresh and b["side"] == side]
                if not tb:
                    continue
                tw = sum(1 for b in tb if b["won"])
                tl = len(tb) - tw
                tprofit = sum(b["profit"] for b in tb)
                twagered = BET_SIZE * len(tb)
                troi = (tprofit / twagered * 100) if twagered > 0 else 0
                twr = tw / len(tb) * 100
                print(f"    {thresh*100:>4.0f}%: {len(tb):>5}B {tw}W {tl}L "
                      f"({twr:.1f}%) ${tprofit:+.0f} ROI {troi:+.1f}%")

    # Yearly
    best_thresh = 0.03
    filtered = [b for b in bets if b["edge"] >= best_thresh]
    if filtered:
        print(f"\n  Yearly (at {best_thresh*100:.0f}%):")
        years = {}
        for b in filtered:
            y = b["date"][:4]
            if y not in years:
                years[y] = {"bets": 0, "wins": 0, "profit": 0}
            years[y]["bets"] += 1
            if b["won"]:
                years[y]["wins"] += 1
            years[y]["profit"] += b["profit"]
        for y in sorted(years):
            d = years[y]
            wr = d["wins"] / d["bets"] * 100
            roi = d["profit"] / (BET_SIZE * d["bets"]) * 100
            print(f"    {y}: {d['bets']}B {d['wins']}W ({wr:.1f}%) "
                  f"${d['profit']:+.0f} ROI {roi:+.1f}%")

    # Save
    results_dir = os.path.join(DATA_DIR, "backtest_results")
    os.makedirs(results_dir, exist_ok=True)
    bets_df = pd.DataFrame(bets)
    csv_path = os.path.join(results_dir, f"mlb_feature_{target}_bets.csv")
    bets_df.to_csv(csv_path, index=False)
    print(f"\n  Saved to {csv_path}")
    print(f"{'='*60}")

    return bets


class MLBFeaturePredictor:
    """
    Live prediction engine using the feature-rich XGBoost model.

    Trains on all historical Pinnacle data, then predicts today's games
    using current market lines from sports_edge.db.
    """

    def __init__(self):
        self.totals_model = None
        self.ml_model = None
        self.feature_names = None
        self.fitted = False
        self._df = None
        self._features = None
        self._team_games = None

    def fit(self):
        """Train models on all historical data."""
        self._df, self._pitcher_logs, self._weather_data = load_all_mlb_games()
        self._features = engineer_features(self._df, self._pitcher_logs, self._weather_data)

        # Build and train totals model
        X_tot, y_tot, _ = build_dataset(self._df, self._features, target="totals")
        if len(X_tot) < 500:
            print(f"  [MLB Feature] Not enough data to train ({len(X_tot)} samples)")
            return

        self.feature_names = list(X_tot.columns)
        self.totals_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=1.0, reg_lambda=2.0, min_child_weight=10,
            eval_metric="logloss", random_state=42, verbosity=0,
        )
        self.totals_model.fit(X_tot, y_tot)

        # Build and train moneyline model
        X_ml, y_ml, _ = build_dataset(self._df, self._features, target="moneyline")
        self.ml_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=1.0, reg_lambda=2.0, min_child_weight=10,
            eval_metric="logloss", random_state=42, verbosity=0,
        )
        self.ml_model.fit(X_ml, y_ml)

        self.fitted = True
        print(f"  [MLB Feature] Trained on {len(X_tot)} totals + {len(X_ml)} ML samples, {len(self.feature_names)} features")

    def _build_team_history(self):
        """Rebuild team history from all loaded games for feature engineering."""
        if self._team_games is not None:
            return self._team_games

        team_games = defaultdict(list)
        for i in range(len(self._df)):
            game = self._df.iloc[i]
            home = game["home_team"]
            away = game["away_team"]
            date = game["game_date"]
            team_games[home].append((i, True, game["home_score"], game["away_score"], date))
            team_games[away].append((i, False, game["away_score"], game["home_score"], date))

        self._team_games = team_games
        return team_games

    def _engineer_single_game(self, home_team, away_team, game_date, market_data):
        """
        Engineer features for a single upcoming game.

        market_data: dict with keys like closing_line, todds_over, todds_under,
                     ml_todds_home, ml_todds_away, ht_line, at_line, spread_line
        """
        team_games = self._build_team_history()
        h_hist = team_games.get(home_team, [])
        a_hist = team_games.get(away_team, [])

        if len(h_hist) < MIN_HISTORY or len(a_hist) < MIN_HISTORY:
            return None

        f = {}

        # Market features
        f["closing_total_line"] = market_data.get("closing_line", 8.5)

        to = market_data.get("todds_over")
        tu = market_data.get("todds_under")
        if to and tu and to > 1 and tu > 1:
            impl_o = 1.0 / to
            impl_u = 1.0 / tu
            f["market_impl_over"] = impl_o / (impl_o + impl_u)
        else:
            f["market_impl_over"] = 0.5

        ml_h = market_data.get("ml_todds_home")
        ml_a = market_data.get("ml_todds_away")
        if ml_h and ml_a and ml_h > 1 and ml_a > 1:
            ih = 1.0 / ml_h
            ia = 1.0 / ml_a
            f["market_impl_home_win"] = ih / (ih + ia)
        else:
            f["market_impl_home_win"] = 0.5

        ht_line = market_data.get("ht_line")
        at_line = market_data.get("at_line")
        f["home_team_total_line"] = ht_line if ht_line else f["closing_total_line"] / 2
        f["away_team_total_line"] = at_line if at_line else f["closing_total_line"] / 2
        f["team_totals_sum_vs_line"] = (f["home_team_total_line"] + f["away_team_total_line"]) - f["closing_total_line"]

        sp_line = market_data.get("spread_line")
        f["spread_line"] = sp_line if sp_line else 0

        # Team history features -- mirrors engineer_features() exactly
        for label, hist in [("home", h_hist), ("away", a_hist)]:
            scores_for = [h[2] for h in hist]
            scores_against = [h[3] for h in hist]
            totals = [h[2] + h[3] for h in hist]
            dates = [h[4] for h in hist]

            for wn, w in [("l5", 5), ("l10", 10), ("l20", 20), ("l40", 40), ("season", len(hist))]:
                rf = scores_for[-w:]
                ra = scores_against[-w:]
                rt = totals[-w:]
                f[f"{label}_rf_{wn}"] = np.mean(rf)
                f[f"{label}_ra_{wn}"] = np.mean(ra)
                f[f"{label}_total_{wn}"] = np.mean(rt)
                if wn not in ("season",):
                    f[f"{label}_rf_std_{wn}"] = np.std(rf) if len(rf) > 1 else 0
                    f[f"{label}_total_std_{wn}"] = np.std(rt) if len(rt) > 1 else 0

            wins = sum(1 for h in hist if h[2] > h[3])
            f[f"{label}_win_pct"] = wins / len(hist)
            wins_l10 = sum(1 for h in hist[-10:] if h[2] > h[3])
            f[f"{label}_win_pct_l10"] = wins_l10 / min(10, len(hist))

            home_games = [(h[2], h[3]) for h in hist if h[1]]
            away_games = [(h[2], h[3]) for h in hist if not h[1]]
            if home_games:
                f[f"{label}_home_rf"] = np.mean([g[0] for g in home_games])
                f[f"{label}_home_ra"] = np.mean([g[1] for g in home_games])
            else:
                f[f"{label}_home_rf"] = np.mean(scores_for)
                f[f"{label}_home_ra"] = np.mean(scores_against)
            if away_games:
                f[f"{label}_away_rf"] = np.mean([g[0] for g in away_games])
                f[f"{label}_away_ra"] = np.mean([g[1] for g in away_games])
            else:
                f[f"{label}_away_rf"] = np.mean(scores_for)
                f[f"{label}_away_ra"] = np.mean(scores_against)

            streak = 0
            for h in reversed(hist):
                if h[2] > h[3]:
                    streak += 1
                else:
                    break
            f[f"{label}_win_streak"] = streak
            loss_streak = 0
            for h in reversed(hist):
                if h[2] < h[3]:
                    loss_streak += 1
                else:
                    break
            f[f"{label}_loss_streak"] = loss_streak

            last_date = dates[-1]
            try:
                d1 = datetime.strptime(game_date, "%Y-%m-%d")
                d2 = datetime.strptime(last_date, "%Y-%m-%d")
                rest = (d1 - d2).days
            except:
                rest = 1
            f[f"{label}_rest_days"] = min(rest, 7)

            f[f"{label}_games_played"] = len(hist)

            if len(scores_for) >= 20:
                f[f"{label}_rf_trend"] = np.mean(scores_for[-5:]) - np.mean(scores_for[-20:])
                f[f"{label}_ra_trend"] = np.mean(scores_against[-5:]) - np.mean(scores_against[-20:])
            else:
                f[f"{label}_rf_trend"] = 0
                f[f"{label}_ra_trend"] = 0

        # Matchup differentials
        f["rf_diff_season"] = f["home_rf_season"] - f["away_rf_season"]
        f["ra_diff_season"] = f["home_ra_season"] - f["away_ra_season"]
        f["rf_diff_l10"] = f["home_rf_l10"] - f["away_rf_l10"]
        f["total_diff_l10"] = f["home_total_l10"] - f["away_total_l10"]
        f["win_pct_diff"] = f["home_win_pct"] - f["away_win_pct"]
        f["win_pct_l10_diff"] = f["home_win_pct_l10"] - f["away_win_pct_l10"]
        f["rest_diff"] = f["home_rest_days"] - f["away_rest_days"]

        f["form_expected_total"] = (f["home_rf_l10"] + f["away_rf_l10"] +
                                     f["home_ra_l10"] + f["away_ra_l10"]) / 2
        f["form_vs_line"] = f["form_expected_total"] - f["closing_total_line"]
        f["combined_total_std_l10"] = f["home_total_std_l10"] + f["away_total_std_l10"]

        try:
            f["month"] = int(game_date.split("-")[1])
        except:
            f["month"] = 6

        # --- Park factor features ---
        pf = PARK_FACTORS.get(home_team, 1.0)
        f["park_factor"] = pf
        f["is_dome"] = 1 if home_team in IS_DOME else 0
        f["park_adj_form_total"] = f["form_expected_total"] * pf
        f["park_adj_vs_line"] = f["park_adj_form_total"] - f["closing_total_line"]
        f["park_extreme"] = abs(pf - 1.0)

        # --- Weather features ---
        # For live predictions, try to get weather from mlb_weather table
        weather = None
        try:
            se_db = os.path.join(DATA_DIR, "sports_edge.db")
            w_conn = sqlite3.connect(se_db)
            w_row = w_conn.execute("""
                SELECT temperature_f, wind_speed_mph, humidity_pct
                FROM mlb_weather WHERE team_abbrev = ? AND game_date = ?
                LIMIT 1
            """, (home_team, game_date)).fetchone()
            if w_row:
                weather = {"temp": w_row[0], "wind": w_row[1], "humidity": w_row[2]}
            w_conn.close()
        except Exception:
            pass

        if weather and home_team not in IS_DOME:
            f["temperature"] = weather["temp"]
            f["wind_speed"] = weather["wind"]
            f["humidity"] = weather["humidity"]
            f["temp_impact"] = (weather["temp"] - 72) / 20
            f["wind_impact"] = weather["wind"] / 15
        else:
            f["temperature"] = 72
            f["wind_speed"] = 5
            f["humidity"] = 50
            f["temp_impact"] = 0
            f["wind_impact"] = 0.33

        # --- Pitcher features for live predictions ---
        hp_id = None
        ap_id = None
        try:
            gl_conn = sqlite3.connect(DB_PATH)
            # Get today's starters from game_lines.db mlb_pitchers table
            for side, team in [("home", home_team), ("away", away_team)]:
                team_full = MLB_ABBREV_TO_FULL.get(team, team)
                row = gl_conn.execute("""
                    SELECT pitcher_id, era, whip, k_per_9, bb_per_9, innings_pitched
                    FROM mlb_pitchers
                    WHERE game_date = ? AND team = ?
                    LIMIT 1
                """, (game_date, team_full)).fetchone()
                if row and row[0]:
                    pid = row[0]
                    if side == "home":
                        hp_id = pid
                    else:
                        ap_id = pid

            # Also check mlb_game_starters table
            if not hp_id or not ap_id:
                starter_row = gl_conn.execute("""
                    SELECT home_pitcher_id, away_pitcher_id
                    FROM mlb_game_starters
                    WHERE game_date = ? AND home_team = ? AND away_team = ?
                """, (game_date, home_team, away_team)).fetchone()
                if starter_row:
                    if not hp_id and starter_row[0]:
                        hp_id = starter_row[0]
                    if not ap_id and starter_row[1]:
                        ap_id = starter_row[1]

            gl_conn.close()
        except Exception:
            pass

        pitcher_logs = getattr(self, '_pitcher_logs', {})
        for prefix, pid in [("hp", hp_id), ("ap", ap_id)]:
            if pid:
                logs = pitcher_logs.get(int(pid), [])
                for window_name, window in [("l3", 3), ("l5", 5), ("season", 999)]:
                    stats = _compute_pitcher_rolling(logs, game_date, window)
                    if stats:
                        f[f"{prefix}_era_{window_name}"] = stats["era"]
                        f[f"{prefix}_whip_{window_name}"] = stats["whip"]
                        f[f"{prefix}_k9_{window_name}"] = stats["k_per_9"]
                        f[f"{prefix}_bb9_{window_name}"] = stats["bb_per_9"]
                        f[f"{prefix}_hr9_{window_name}"] = stats["hr_per_9"]
                        f[f"{prefix}_avg_ip_{window_name}"] = stats["avg_ip"]
                    else:
                        f[f"{prefix}_era_{window_name}"] = 4.5
                        f[f"{prefix}_whip_{window_name}"] = 1.3
                        f[f"{prefix}_k9_{window_name}"] = 8.5
                        f[f"{prefix}_bb9_{window_name}"] = 3.2
                        f[f"{prefix}_hr9_{window_name}"] = 1.2
                        f[f"{prefix}_avg_ip_{window_name}"] = 5.0
            else:
                for window_name in ["l3", "l5", "season"]:
                    f[f"{prefix}_era_{window_name}"] = 4.5
                    f[f"{prefix}_whip_{window_name}"] = 1.3
                    f[f"{prefix}_k9_{window_name}"] = 8.5
                    f[f"{prefix}_bb9_{window_name}"] = 3.2
                    f[f"{prefix}_hr9_{window_name}"] = 1.2
                    f[f"{prefix}_avg_ip_{window_name}"] = 5.0

        f["era_diff_l5"] = f["hp_era_l5"] - f["ap_era_l5"]
        f["whip_diff_l5"] = f["hp_whip_l5"] - f["ap_whip_l5"]
        f["k9_diff_l5"] = f["hp_k9_l5"] - f["ap_k9_l5"]
        f["era_diff_season"] = f["hp_era_season"] - f["ap_era_season"]
        f["combined_era_l5"] = f["hp_era_l5"] + f["ap_era_l5"]
        f["combined_whip_l5"] = f["hp_whip_l5"] + f["ap_whip_l5"]
        f["combined_k9_l5"] = f["hp_k9_l5"] + f["ap_k9_l5"]
        f["pitcher_era_vs_line"] = f["combined_era_l5"] - f["closing_total_line"]

        return f

    def predict_today(self):
        """
        Predict all today's MLB games using current market lines.
        Returns list of prediction dicts with edges for both totals and moneyline.
        """
        if not self.fitted:
            return []

        se_db = os.path.join(DATA_DIR, "sports_edge.db")
        if not os.path.exists(se_db):
            print("  [MLB Feature] sports_edge.db not found")
            return []

        conn = sqlite3.connect(se_db)
        conn.row_factory = sqlite3.Row
        today = datetime.now().strftime("%Y-%m-%d")

        # Get unique games from line snapshots
        game_rows = conn.execute("""
            SELECT DISTINCT home_team, away_team
            FROM game_line_snapshots
            WHERE sport='MLB' AND game_date=?
        """, (today,)).fetchall()

        # Deduplicate by abbreviation
        seen_games = set()
        games = []
        for r in game_rows:
            h_abbr = MLB_FULL_TO_ABBREV.get(r["home_team"], r["home_team"])
            a_abbr = MLB_FULL_TO_ABBREV.get(r["away_team"], r["away_team"])
            key = (h_abbr, a_abbr)
            if key not in seen_games:
                seen_games.add(key)
                games.append((h_abbr, a_abbr, r["home_team"], r["away_team"]))

        # Fallback to schedule
        if not games:
            schedule = conn.execute(
                "SELECT home_team_abbrev, away_team_abbrev FROM mlb_schedule WHERE game_date = ?",
                (today,)
            ).fetchall()
            for g in schedule:
                h_abbr = g["home_team_abbrev"]
                a_abbr = g["away_team_abbrev"]
                games.append((h_abbr, a_abbr, h_abbr, a_abbr))

        if not games:
            conn.close()
            return []

        predictions = []
        for home_abbr, away_abbr, home_full, away_full in games:
            # Get market lines from game_line_snapshots
            market = self._get_market_data(conn, today, home_full, away_full, home_abbr, away_abbr)
            if not market.get("closing_line"):
                continue

            # Engineer features
            feats = self._engineer_single_game(home_abbr, away_abbr, today, market)
            if feats is None:
                continue

            # Build feature vector matching training columns
            X = pd.DataFrame([feats])
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_names]

            # Predict totals
            p_over = self.totals_model.predict_proba(X)[0, 1]

            # Predict moneyline
            p_home_win = self.ml_model.predict_proba(X)[0, 1]

            # Devig market probabilities
            to = market.get("todds_over")
            tu = market.get("todds_under")
            ml_h = market.get("ml_todds_home")
            ml_a = market.get("ml_todds_away")

            # --- Totals edge ---
            if to and tu and to > 1 and tu > 1:
                impl_o = 1.0 / to
                impl_u = 1.0 / tu
                devig_o = impl_o / (impl_o + impl_u)
                devig_u = 1 - devig_o

                edge_over = p_over - devig_o
                edge_under = (1 - p_over) - devig_u

                if edge_over > 0 or edge_under > 0:
                    if edge_over >= edge_under:
                        side = "OVER"
                        edge = edge_over
                        our_prob = p_over
                        odds = market.get("over_odds", -110)
                    else:
                        side = "UNDER"
                        edge = edge_under
                        our_prob = 1 - p_over
                        odds = market.get("under_odds", -110)

                    predictions.append({
                        "source": "mlb_feature",
                        "sport": "MLB",
                        "market_type": "totals",
                        "game": f"{away_abbr} @ {home_abbr}",
                        "home_team": home_abbr,
                        "away_team": away_abbr,
                        "side": side,
                        "market_line": market["closing_line"],
                        "odds": int(odds) if odds else -110,
                        "model_total": round(float(market["closing_line"]), 1),
                        "our_prob": round(float(our_prob), 4),
                        "edge": round(float(edge), 4),
                        "p_over": round(float(p_over), 4),
                        "model_confidence": round(float(max(p_over, 1 - p_over)), 4),
                    })

            # --- Moneyline edge ---
            if ml_h and ml_a and ml_h > 1 and ml_a > 1:
                ih = 1.0 / ml_h
                ia = 1.0 / ml_a
                devig_h = ih / (ih + ia)
                devig_a = 1 - devig_h

                edge_home = p_home_win - devig_h
                edge_away = (1 - p_home_win) - devig_a

                if edge_home > 0 or edge_away > 0:
                    if edge_home >= edge_away:
                        side = "HOME"
                        edge = edge_home
                        our_prob = p_home_win
                        odds = market.get("ml_home_odds", -110)
                    else:
                        side = "AWAY"
                        edge = edge_away
                        our_prob = 1 - p_home_win
                        odds = market.get("ml_away_odds", -110)

                    predictions.append({
                        "source": "mlb_feature",
                        "sport": "MLB",
                        "market_type": "moneyline",
                        "game": f"{away_abbr} @ {home_abbr}",
                        "home_team": home_abbr,
                        "away_team": away_abbr,
                        "side": side,
                        "market_line": None,
                        "odds": int(odds) if odds else -110,
                        "our_prob": round(float(our_prob), 4),
                        "edge": round(float(edge), 4),
                        "p_home_win": round(float(p_home_win), 4),
                        "model_confidence": round(float(max(p_home_win, 1 - p_home_win)), 4),
                    })

        conn.close()
        return predictions

    def _get_market_data(self, conn, game_date, home_full, away_full, home_abbr, away_abbr):
        """Extract market data for a game from game_line_snapshots."""
        market = {}

        name_pairs = [
            (home_full, away_full),
            (home_abbr, away_abbr),
        ]
        # Add abbreviation-to-full lookups
        h_full_from_abbr = MLB_ABBREV_TO_FULL.get(home_abbr)
        a_full_from_abbr = MLB_ABBREV_TO_FULL.get(away_abbr)
        if h_full_from_abbr and a_full_from_abbr:
            name_pairs.append((h_full_from_abbr, a_full_from_abbr))

        books_priority = ["pinnacle", "consensus", "heritage", "betonline"]
        for book in books_priority:
            for h_name, a_name in name_pairs:
                rows = conn.execute("""
                    SELECT market, side, line, odds
                    FROM game_line_snapshots
                    WHERE sport='MLB' AND game_date=? AND book=?
                    AND home_team=? AND away_team=?
                    ORDER BY collected_at DESC
                """, (game_date, book, h_name, a_name)).fetchall()
                if rows:
                    self._parse_market_rows(rows, market)
                    if market.get("closing_line"):
                        return market

            # Fallback: search all rows for this book and match by abbreviation
            if not market.get("closing_line"):
                rows = conn.execute("""
                    SELECT market, side, line, odds, home_team, away_team
                    FROM game_line_snapshots
                    WHERE sport='MLB' AND game_date=? AND book=?
                    ORDER BY collected_at DESC
                """, (game_date, book)).fetchall()

                for r in rows:
                    h = MLB_FULL_TO_ABBREV.get(r["home_team"], r["home_team"])
                    a = MLB_FULL_TO_ABBREV.get(r["away_team"], r["away_team"])
                    if h == home_abbr and a == away_abbr:
                        self._parse_single_row(r, market)

                if market.get("closing_line"):
                    return market

        return market

    def _parse_market_rows(self, rows, market):
        """Parse market rows into market dict."""
        for r in rows:
            self._parse_single_row(r, market)

    def _parse_single_row(self, r, market):
        """Parse a single market row."""
        mkt = r["market"]
        side = r["side"]
        line = r["line"]
        odds = r["odds"]

        if mkt == "total":
            if side == "over" and line:
                if "closing_line" not in market:
                    market["closing_line"] = line
                    market["over_odds"] = odds
                    market["todds_over"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
            elif side == "under" and line:
                if "under_odds" not in market:
                    market["under_odds"] = odds
                    market["todds_under"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
        elif mkt == "moneyline":
            if side == "home" and "ml_home_odds" not in market:
                market["ml_home_odds"] = odds
                market["ml_todds_home"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
            elif side == "away" and "ml_away_odds" not in market:
                market["ml_away_odds"] = odds
                market["ml_todds_away"] = 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)
        elif mkt == "spread" and line and abs(line) == 1.5:
            if "spread_line" not in market:
                market["spread_line"] = line


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        # Live prediction mode
        print("\n=== MLB Feature Model - Live Predictions ===\n")
        predictor = MLBFeaturePredictor()
        predictor.fit()
        preds = predictor.predict_today()
        if not preds:
            print("  No predictions (no games today or insufficient history)")
        for p in preds:
            print(f"  {p['game']:20s} {p['market_type']:10s} {p['side']:6s} "
                  f"edge={p['edge']:+.1%} prob={p['our_prob']:.1%} "
                  f"odds={p.get('odds', -110)}")
    else:
        target = sys.argv[1] if len(sys.argv) > 1 else "totals"
        print(f"\n=== Running MLB Feature Model backtest: {target} ===\n")
        run_backtest(target=target)

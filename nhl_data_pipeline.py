#!/usr/bin/env python3
"""
NHL Data Pipeline for Predictive Modeling
==========================================

Ingests NHL data from free public sources into SQLite for sports betting models.

Data Sources:
  - MoneyPuck (CSV): Skater, goalie, team, line stats with xG and advanced metrics
  - NHL API (api-web.nhle.com): Standings, schedule, scores, play-by-play
  - Open-Meteo: Weather data for outdoor venues (minimal NHL relevance)

Storage: SQLite at data/sports_edge.db

Usage:
  python3 nhl_data_pipeline.py                    # Full pipeline update
  python3 nhl_data_pipeline.py --moneypuck 2024   # MoneyPuck only, specific season
  python3 nhl_data_pipeline.py --schedule          # Schedule + scores only
  python3 nhl_data_pipeline.py --features          # Recompute derived features
  python3 nhl_data_pipeline.py --matchup TOR WSH  # Get features for a matchup
"""

import argparse
import io
import json
import logging
import os
import sqlite3
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sports_edge.db")

MONEYPUCK_BASE = "https://moneypuck.com/moneypuck/playerData/seasonSummary"
MONEYPUCK_SHOTS_BASE = "https://peter-tanner.com/moneypuck/downloads"
NHL_API_BASE = "https://api-web.nhle.com/v1"

# Browser-like headers required by MoneyPuck (blocks bare requests)
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/html,application/xhtml+xml,*/*",
    "Referer": "https://moneypuck.com/data.htm",
}

# Current and recent seasons for bulk download
CURRENT_SEASON = "2024"  # MoneyPuck uses start year (2024 = 2024-25 season)

# Team abbreviation mapping: NHL API abbrev -> canonical
# MoneyPuck uses its own names; we normalize everything to NHL API 3-letter codes
TEAM_ABBREV_MAP = {
    # Common mismatches between MoneyPuck and NHL API
    "L.A": "LAK", "LA": "LAK",
    "N.J": "NJD", "NJ": "NJD",
    "S.J": "SJS", "SJ": "SJS",
    "T.B": "TBL", "TB": "TBL",
    "VGK": "VGK", "VEG": "VGK",
    "WSH": "WSH", "WAS": "WSH",
    "CBJ": "CBJ", "CLB": "CBJ",
    "MTL": "MTL", "MON": "MTL",
    "ANA": "ANA",
    "ARI": "ARI", "UTA": "UTA",
    "BOS": "BOS",
    "BUF": "BUF",
    "CAR": "CAR",
    "CGY": "CGY",
    "CHI": "CHI",
    "COL": "COL",
    "DAL": "DAL",
    "DET": "DET",
    "EDM": "EDM",
    "FLA": "FLA",
    "LAK": "LAK",
    "MIN": "MIN",
    "NJD": "NJD",
    "NSH": "NSH",
    "NYI": "NYI",
    "NYR": "NYR",
    "OTT": "OTT",
    "PHI": "PHI",
    "PIT": "PIT",
    "SEA": "SEA",
    "SJS": "SJS",
    "STL": "STL",
    "TBL": "TBL",
    "TOR": "TOR",
    "VAN": "VAN",
    "WPG": "WPG",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nhl_pipeline")


# ---------------------------------------------------------------------------
# Database Setup
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Open SQLite connection with WAL mode and return it."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all NHL tables if they don't exist."""
    conn.executescript("""
        -- Team season stats from MoneyPuck (one row per team per situation per season)
        CREATE TABLE IF NOT EXISTS nhl_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            season TEXT NOT NULL,
            situation TEXT NOT NULL DEFAULT 'all',
            games_played INTEGER,
            -- xG metrics
            xGoalsPercentage REAL,
            xGoalsFor REAL,
            xGoalsAgainst REAL,
            goalsFor INTEGER,
            goalsAgainst INTEGER,
            -- Possession
            corsiPercentage REAL,
            corsiFor REAL,
            corsiAgainst REAL,
            fenwickPercentage REAL,
            fenwickFor REAL,
            fenwickAgainst REAL,
            -- Shots
            shotsOnGoalFor INTEGER,
            shotsOnGoalAgainst INTEGER,
            shotAttemptsFor INTEGER,
            shotAttemptsAgainst INTEGER,
            highDangerShotsFor INTEGER,
            highDangerShotsAgainst INTEGER,
            highDangerGoalsFor INTEGER,
            highDangerGoalsAgainst INTEGER,
            mediumDangerShotsFor INTEGER,
            mediumDangerShotsAgainst INTEGER,
            lowDangerShotsFor INTEGER,
            lowDangerShotsAgainst INTEGER,
            -- Special teams
            penaltiesFor INTEGER,
            penaltiesAgainst INTEGER,
            penalityMinutesFor REAL,
            penalityMinutesAgainst REAL,
            -- Scoring
            reboundsFor INTEGER,
            reboundsAgainst INTEGER,
            reboundGoalsFor INTEGER,
            reboundGoalsAgainst INTEGER,
            -- Adjusted
            scoreVenueAdjustedxGoalsFor REAL,
            scoreVenueAdjustedxGoalsAgainst REAL,
            -- Metadata
            iceTime REAL,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(team, season, situation)
        );

        -- Skater stats from MoneyPuck
        CREATE TABLE IF NOT EXISTS nhl_skaters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            name TEXT NOT NULL,
            team TEXT,
            position TEXT,
            season TEXT NOT NULL,
            situation TEXT NOT NULL DEFAULT 'all',
            games_played INTEGER,
            icetime REAL,
            -- Scoring
            goals INTEGER,
            assists INTEGER,
            points INTEGER,
            shots INTEGER,
            -- xG
            xGoals REAL,
            xOnGoal REAL,
            xAssists REAL,
            xPoints REAL,
            -- Shot generation
            shotsOnGoal INTEGER,
            shotAttempts INTEGER,
            highDangerShots INTEGER,
            highDangerGoals INTEGER,
            -- On-ice impact
            onIce_xGoalsPercentage REAL,
            offIce_xGoalsPercentage REAL,
            onIce_corsiPercentage REAL,
            onIce_fenwickPercentage REAL,
            -- Game score (overall impact metric)
            gameScore REAL,
            -- Penalties
            penalityMinutes REAL,
            penalties INTEGER,
            penaltiesDrawn INTEGER,
            -- Metadata
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(player_id, season, situation)
        );

        -- Goalie stats from MoneyPuck
        CREATE TABLE IF NOT EXISTS nhl_goalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            name TEXT NOT NULL,
            team TEXT,
            season TEXT NOT NULL,
            situation TEXT NOT NULL DEFAULT 'all',
            games_played INTEGER,
            icetime REAL,
            -- Goals
            xGoals REAL,
            goals INTEGER,
            -- Shot metrics
            ongoal INTEGER,
            xOnGoal REAL,
            -- Danger zones
            lowDangerShots INTEGER,
            lowDangerGoals INTEGER,
            lowDangerxGoals REAL,
            mediumDangerShots INTEGER,
            mediumDangerGoals INTEGER,
            mediumDangerxGoals REAL,
            highDangerShots INTEGER,
            highDangerGoals INTEGER,
            highDangerxGoals REAL,
            -- Rebounds / freeze
            xRebounds REAL,
            rebounds INTEGER,
            xFreeze REAL,
            freeze INTEGER,
            -- Derived (computed on insert)
            save_pct REAL,
            xSave_pct REAL,
            gsax REAL,  -- goals saved above expected
            -- Metadata
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(player_id, season, situation)
        );

        -- Game results from NHL API
        CREATE TABLE IF NOT EXISTS nhl_games (
            id INTEGER PRIMARY KEY,  -- NHL game ID
            season TEXT,
            game_type INTEGER,       -- 2=regular, 3=playoff
            game_date TEXT,
            start_time TEXT,
            game_state TEXT,         -- FUT, LIVE, OFF, FINAL
            home_team TEXT,
            away_team TEXT,
            home_score INTEGER,
            away_score INTEGER,
            period INTEGER,
            game_outcome TEXT,       -- REG, OT, SO
            venue TEXT,
            -- Derived
            home_win INTEGER,        -- 1/0
            total_goals INTEGER,
            goal_diff INTEGER,       -- home - away
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(id)
        );

        -- Individual shot data from MoneyPuck (large table)
        CREATE TABLE IF NOT EXISTS nhl_shots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season TEXT,
            game_id INTEGER,
            period INTEGER,
            time REAL,
            team TEXT,
            shooter_id INTEGER,
            shooter_name TEXT,
            goalie_id INTEGER,
            goalie_name TEXT,
            is_goal INTEGER,
            xGoal REAL,
            shot_type TEXT,
            location_x REAL,
            location_y REAL,
            shot_distance REAL,
            shot_angle REAL,
            -- Context
            home_team TEXT,
            away_team TEXT,
            is_home_team INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            strength TEXT,           -- 5v5, 5v4, etc.
            -- Metadata
            updated_at TEXT DEFAULT (datetime('now'))
        );

        -- Upcoming schedule for prediction
        CREATE TABLE IF NOT EXISTS nhl_schedule (
            id INTEGER PRIMARY KEY,  -- NHL game ID
            game_date TEXT,
            start_time TEXT,
            home_team TEXT,
            away_team TEXT,
            venue TEXT,
            game_type INTEGER,
            game_state TEXT,
            -- Prediction features (computed)
            home_rest_days INTEGER,
            away_rest_days INTEGER,
            home_b2b INTEGER DEFAULT 0,
            away_b2b INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(id)
        );

        -- Standings snapshot from NHL API
        CREATE TABLE IF NOT EXISTS nhl_standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            season TEXT,
            snapshot_date TEXT,
            games_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            ot_losses INTEGER,
            points INTEGER,
            point_pct REAL,
            regulation_wins INTEGER,
            goal_for INTEGER,
            goal_against INTEGER,
            goal_diff INTEGER,
            -- Home/Away splits
            home_wins INTEGER,
            home_losses INTEGER,
            home_ot_losses INTEGER,
            road_wins INTEGER,
            road_losses INTEGER,
            road_ot_losses INTEGER,
            -- L10
            l10_wins INTEGER,
            l10_losses INTEGER,
            l10_ot_losses INTEGER,
            l10_points INTEGER,
            -- Streak
            streak_code TEXT,
            streak_count INTEGER,
            -- Division/Conference
            division TEXT,
            conference TEXT,
            -- Metadata
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(team, snapshot_date)
        );

        -- Derived team features for prediction (computed from above tables)
        CREATE TABLE IF NOT EXISTS nhl_team_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            season TEXT NOT NULL,
            computed_at TEXT DEFAULT (datetime('now')),
            -- Offensive ratings
            goals_for_per_game REAL,
            goals_for_per_game_l10 REAL,
            goals_for_per_game_l20 REAL,
            xGoalsFor_per_game REAL,
            -- Defensive ratings
            goals_against_per_game REAL,
            goals_against_per_game_l10 REAL,
            goals_against_per_game_l20 REAL,
            xGoalsAgainst_per_game REAL,
            -- Possession
            corsi_diff REAL,
            fenwick_diff REAL,
            xGoals_pct REAL,
            -- Special teams
            pp_pct REAL,
            pk_pct REAL,
            -- Danger
            high_danger_for_pct REAL,
            high_danger_against_pct REAL,
            -- Pace
            shots_for_per_game REAL,
            shots_against_per_game REAL,
            -- Home/Away
            home_win_pct REAL,
            road_win_pct REAL,
            -- Record
            points_pct REAL,
            l10_points_pct REAL,
            -- Goaltending
            team_save_pct REAL,
            team_xSave_pct REAL,
            team_gsax REAL,
            UNIQUE(team, season, computed_at)
        );

        -- Pipeline metadata
        CREATE TABLE IF NOT EXISTS nhl_pipeline_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            action TEXT,
            rows_affected INTEGER,
            status TEXT,
            message TEXT,
            run_at TEXT DEFAULT (datetime('now'))
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_nhl_games_date ON nhl_games(game_date);
        CREATE INDEX IF NOT EXISTS idx_nhl_games_teams ON nhl_games(home_team, away_team);
        CREATE INDEX IF NOT EXISTS idx_nhl_shots_game ON nhl_shots(game_id);
        CREATE INDEX IF NOT EXISTS idx_nhl_skaters_team ON nhl_skaters(team, season);
        CREATE INDEX IF NOT EXISTS idx_nhl_goalies_team ON nhl_goalies(team, season);
        CREATE INDEX IF NOT EXISTS idx_nhl_schedule_date ON nhl_schedule(game_date);
        CREATE INDEX IF NOT EXISTS idx_nhl_standings_team ON nhl_standings(team, snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_nhl_team_features_team ON nhl_team_features(team, season);
    """)
    conn.commit()


def normalize_team(abbrev: str) -> str:
    """Normalize team abbreviation to canonical NHL API form."""
    if not abbrev:
        return abbrev
    clean = abbrev.strip().upper()
    return TEAM_ABBREV_MAP.get(clean, clean)


def log_pipeline(conn: sqlite3.Connection, source: str, action: str,
                 rows: int, status: str, message: str = "") -> None:
    """Record pipeline activity."""
    conn.execute(
        "INSERT INTO nhl_pipeline_log (source, action, rows_affected, status, message) "
        "VALUES (?, ?, ?, ?, ?)",
        (source, action, rows, status, message),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# MoneyPuck Ingestion
# ---------------------------------------------------------------------------

def _fetch_moneypuck_csv(season: str, data_type: str, game_type: str = "regular") -> Optional[pd.DataFrame]:
    """Download a MoneyPuck CSV and return as DataFrame."""
    url = f"{MONEYPUCK_BASE}/{season}/{game_type}/{data_type}.csv"
    log.info("Fetching MoneyPuck %s/%s/%s ...", season, game_type, data_type)
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=60)
        if resp.status_code != 200:
            log.warning("MoneyPuck %s returned %d", data_type, resp.status_code)
            return None
        if "<html>" in resp.text[:200].lower():
            log.warning("MoneyPuck %s returned HTML (blocked or missing)", data_type)
            return None
        df = pd.read_csv(io.StringIO(resp.text))
        log.info("  -> %d rows, %d columns", len(df), len(df.columns))
        return df
    except Exception as e:
        log.error("Failed to fetch MoneyPuck %s: %s", data_type, e)
        return None


def download_moneypuck_data(season: str = CURRENT_SEASON, conn: Optional[sqlite3.Connection] = None) -> dict:
    """
    Download all MoneyPuck season summary CSVs and store in SQLite.

    Returns dict with row counts per data type.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_db()
        init_schema(conn)

    results = {}

    # -- Teams --
    df = _fetch_moneypuck_csv(season, "teams")
    if df is not None:
        count = _store_moneypuck_teams(conn, df, season)
        results["teams"] = count
        log_pipeline(conn, "moneypuck", f"teams_{season}", count, "ok")

    # -- Skaters --
    df = _fetch_moneypuck_csv(season, "skaters")
    if df is not None:
        count = _store_moneypuck_skaters(conn, df, season)
        results["skaters"] = count
        log_pipeline(conn, "moneypuck", f"skaters_{season}", count, "ok")

    # -- Goalies --
    df = _fetch_moneypuck_csv(season, "goalies")
    if df is not None:
        count = _store_moneypuck_goalies(conn, df, season)
        results["goalies"] = count
        log_pipeline(conn, "moneypuck", f"goalies_{season}", count, "ok")

    if own_conn:
        conn.close()

    return results


def _store_moneypuck_teams(conn: sqlite3.Connection, df: pd.DataFrame, season: str) -> int:
    """Upsert MoneyPuck team data into nhl_teams."""
    count = 0
    for _, row in df.iterrows():
        team = normalize_team(str(row.get("team", "")))
        situation = str(row.get("situation", "all"))

        def g(col):
            """Get value or None."""
            v = row.get(col)
            if pd.isna(v):
                return None
            return v

        conn.execute("""
            INSERT INTO nhl_teams (
                team, season, situation, games_played,
                xGoalsPercentage, xGoalsFor, xGoalsAgainst, goalsFor, goalsAgainst,
                corsiPercentage, corsiFor, corsiAgainst,
                fenwickPercentage, fenwickFor, fenwickAgainst,
                shotsOnGoalFor, shotsOnGoalAgainst, shotAttemptsFor, shotAttemptsAgainst,
                highDangerShotsFor, highDangerShotsAgainst,
                highDangerGoalsFor, highDangerGoalsAgainst,
                mediumDangerShotsFor, mediumDangerShotsAgainst,
                lowDangerShotsFor, lowDangerShotsAgainst,
                penaltiesFor, penaltiesAgainst,
                penalityMinutesFor, penalityMinutesAgainst,
                reboundsFor, reboundsAgainst,
                reboundGoalsFor, reboundGoalsAgainst,
                scoreVenueAdjustedxGoalsFor, scoreVenueAdjustedxGoalsAgainst,
                iceTime, updated_at
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, datetime('now')
            )
            ON CONFLICT(team, season, situation) DO UPDATE SET
                games_played=excluded.games_played,
                xGoalsPercentage=excluded.xGoalsPercentage,
                xGoalsFor=excluded.xGoalsFor, xGoalsAgainst=excluded.xGoalsAgainst,
                goalsFor=excluded.goalsFor, goalsAgainst=excluded.goalsAgainst,
                corsiPercentage=excluded.corsiPercentage,
                corsiFor=excluded.corsiFor, corsiAgainst=excluded.corsiAgainst,
                fenwickPercentage=excluded.fenwickPercentage,
                fenwickFor=excluded.fenwickFor, fenwickAgainst=excluded.fenwickAgainst,
                shotsOnGoalFor=excluded.shotsOnGoalFor, shotsOnGoalAgainst=excluded.shotsOnGoalAgainst,
                shotAttemptsFor=excluded.shotAttemptsFor, shotAttemptsAgainst=excluded.shotAttemptsAgainst,
                highDangerShotsFor=excluded.highDangerShotsFor, highDangerShotsAgainst=excluded.highDangerShotsAgainst,
                highDangerGoalsFor=excluded.highDangerGoalsFor, highDangerGoalsAgainst=excluded.highDangerGoalsAgainst,
                mediumDangerShotsFor=excluded.mediumDangerShotsFor, mediumDangerShotsAgainst=excluded.mediumDangerShotsAgainst,
                lowDangerShotsFor=excluded.lowDangerShotsFor, lowDangerShotsAgainst=excluded.lowDangerShotsAgainst,
                penaltiesFor=excluded.penaltiesFor, penaltiesAgainst=excluded.penaltiesAgainst,
                penalityMinutesFor=excluded.penalityMinutesFor, penalityMinutesAgainst=excluded.penalityMinutesAgainst,
                reboundsFor=excluded.reboundsFor, reboundsAgainst=excluded.reboundsAgainst,
                reboundGoalsFor=excluded.reboundGoalsFor, reboundGoalsAgainst=excluded.reboundGoalsAgainst,
                scoreVenueAdjustedxGoalsFor=excluded.scoreVenueAdjustedxGoalsFor,
                scoreVenueAdjustedxGoalsAgainst=excluded.scoreVenueAdjustedxGoalsAgainst,
                iceTime=excluded.iceTime,
                updated_at=datetime('now')
        """, (
            team, season, situation, g("games_played"),
            g("xGoalsPercentage"), g("xGoalsFor"), g("xGoalsAgainst"),
            g("goalsFor"), g("goalsAgainst"),
            g("corsiPercentage"), g("corsiFor"), g("corsiAgainst"),
            g("fenwickPercentage"), g("fenwickFor"), g("fenwickAgainst"),
            g("shotsOnGoalFor"), g("shotsOnGoalAgainst"),
            g("shotAttemptsFor"), g("shotAttemptsAgainst"),
            g("highDangerShotsFor"), g("highDangerShotsAgainst"),
            g("highDangerGoalsFor"), g("highDangerGoalsAgainst"),
            g("mediumDangerShotsFor"), g("mediumDangerShotsAgainst"),
            g("lowDangerShotsFor"), g("lowDangerShotsAgainst"),
            g("penaltiesFor"), g("penaltiesAgainst"),
            g("penalityMinutesFor"), g("penalityMinutesAgainst"),
            g("reboundsFor"), g("reboundsAgainst"),
            g("reboundGoalsFor"), g("reboundGoalsAgainst"),
            g("scoreVenueAdjustedxGoalsFor"), g("scoreVenueAdjustedxGoalsAgainst"),
            g("iceTime"),
        ))
        count += 1

    conn.commit()
    log.info("Stored %d team-situation rows for season %s", count, season)
    return count


def _store_moneypuck_skaters(conn: sqlite3.Connection, df: pd.DataFrame, season: str) -> int:
    """Upsert MoneyPuck skater data into nhl_skaters."""
    count = 0
    for _, row in df.iterrows():
        pid = row.get("playerId")
        if pd.isna(pid):
            continue
        pid = int(pid)
        team = normalize_team(str(row.get("team", "")))
        situation = str(row.get("situation", "all"))

        def g(col):
            v = row.get(col)
            if pd.isna(v):
                return None
            return v

        # Compute points from individual stats if not directly available
        goals = g("I_F_goals") if "I_F_goals" in df.columns else g("goals")
        assists = g("I_F_primaryAssists")
        if assists is not None:
            a2 = g("I_F_secondaryAssists")
            if a2 is not None:
                assists = int(assists) + int(a2)
        elif "I_F_assists" in df.columns:
            assists = g("I_F_assists")

        points = None
        if goals is not None and assists is not None:
            try:
                points = int(goals) + int(assists)
            except (TypeError, ValueError):
                pass

        conn.execute("""
            INSERT INTO nhl_skaters (
                player_id, name, team, position, season, situation,
                games_played, icetime,
                goals, assists, points, shots,
                xGoals, xOnGoal, xAssists, xPoints,
                shotsOnGoal, shotAttempts, highDangerShots, highDangerGoals,
                onIce_xGoalsPercentage, offIce_xGoalsPercentage,
                onIce_corsiPercentage, onIce_fenwickPercentage,
                gameScore, penalityMinutes, penalties, penaltiesDrawn,
                updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                datetime('now')
            )
            ON CONFLICT(player_id, season, situation) DO UPDATE SET
                name=excluded.name, team=excluded.team, position=excluded.position,
                games_played=excluded.games_played, icetime=excluded.icetime,
                goals=excluded.goals, assists=excluded.assists, points=excluded.points,
                shots=excluded.shots,
                xGoals=excluded.xGoals, xOnGoal=excluded.xOnGoal,
                xAssists=excluded.xAssists, xPoints=excluded.xPoints,
                shotsOnGoal=excluded.shotsOnGoal, shotAttempts=excluded.shotAttempts,
                highDangerShots=excluded.highDangerShots, highDangerGoals=excluded.highDangerGoals,
                onIce_xGoalsPercentage=excluded.onIce_xGoalsPercentage,
                offIce_xGoalsPercentage=excluded.offIce_xGoalsPercentage,
                onIce_corsiPercentage=excluded.onIce_corsiPercentage,
                onIce_fenwickPercentage=excluded.onIce_fenwickPercentage,
                gameScore=excluded.gameScore,
                penalityMinutes=excluded.penalityMinutes,
                penalties=excluded.penalties, penaltiesDrawn=excluded.penaltiesDrawn,
                updated_at=datetime('now')
        """, (
            pid, g("name"), team, g("position"), season, situation,
            g("games_played"), g("icetime"),
            goals, assists, points, g("I_F_shotsOnGoal") if "I_F_shotsOnGoal" in df.columns else g("shots"),
            g("I_F_xGoals") if "I_F_xGoals" in df.columns else g("xGoals"),
            g("I_F_xOnGoal") if "I_F_xOnGoal" in df.columns else g("xOnGoal"),
            g("I_F_xAssists") if "I_F_xAssists" in df.columns else None,
            g("I_F_xPoints") if "I_F_xPoints" in df.columns else None,
            g("I_F_shotsOnGoal") if "I_F_shotsOnGoal" in df.columns else g("shotsOnGoal"),
            g("I_F_shotAttempts") if "I_F_shotAttempts" in df.columns else g("shotAttempts"),
            g("I_F_highDangerShots") if "I_F_highDangerShots" in df.columns else None,
            g("I_F_highDangerGoals") if "I_F_highDangerGoals" in df.columns else None,
            g("onIce_xGoalsPercentage"), g("offIce_xGoalsPercentage"),
            g("onIce_corsiPercentage"), g("onIce_fenwickPercentage"),
            g("gameScore"), g("penalityMinutes"), g("penalties"), g("penaltiesDrawn"),
        ))
        count += 1

    conn.commit()
    log.info("Stored %d skater-situation rows for season %s", count, season)
    return count


def _store_moneypuck_goalies(conn: sqlite3.Connection, df: pd.DataFrame, season: str) -> int:
    """Upsert MoneyPuck goalie data into nhl_goalies."""
    count = 0
    for _, row in df.iterrows():
        pid = row.get("playerId")
        if pd.isna(pid):
            continue
        pid = int(pid)
        team = normalize_team(str(row.get("team", "")))
        situation = str(row.get("situation", "all"))

        def g(col):
            v = row.get(col)
            if pd.isna(v):
                return None
            return v

        # Compute derived goalie metrics
        ongoal = g("ongoal")
        goals = g("goals")
        xGoals = g("xGoals")

        save_pct = None
        xSave_pct = None
        gsax = None

        if ongoal is not None and goals is not None and int(ongoal) > 0:
            save_pct = 1.0 - (float(goals) / float(ongoal))
        if ongoal is not None and xGoals is not None and float(ongoal) > 0:
            xSave_pct = 1.0 - (float(xGoals) / float(ongoal))
        if xGoals is not None and goals is not None:
            gsax = float(xGoals) - float(goals)  # positive = saved more than expected

        conn.execute("""
            INSERT INTO nhl_goalies (
                player_id, name, team, season, situation,
                games_played, icetime,
                xGoals, goals, ongoal, xOnGoal,
                lowDangerShots, lowDangerGoals, lowDangerxGoals,
                mediumDangerShots, mediumDangerGoals, mediumDangerxGoals,
                highDangerShots, highDangerGoals, highDangerxGoals,
                xRebounds, rebounds, xFreeze, freeze,
                save_pct, xSave_pct, gsax,
                updated_at
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                datetime('now')
            )
            ON CONFLICT(player_id, season, situation) DO UPDATE SET
                name=excluded.name, team=excluded.team,
                games_played=excluded.games_played, icetime=excluded.icetime,
                xGoals=excluded.xGoals, goals=excluded.goals,
                ongoal=excluded.ongoal, xOnGoal=excluded.xOnGoal,
                lowDangerShots=excluded.lowDangerShots, lowDangerGoals=excluded.lowDangerGoals,
                lowDangerxGoals=excluded.lowDangerxGoals,
                mediumDangerShots=excluded.mediumDangerShots, mediumDangerGoals=excluded.mediumDangerGoals,
                mediumDangerxGoals=excluded.mediumDangerxGoals,
                highDangerShots=excluded.highDangerShots, highDangerGoals=excluded.highDangerGoals,
                highDangerxGoals=excluded.highDangerxGoals,
                xRebounds=excluded.xRebounds, rebounds=excluded.rebounds,
                xFreeze=excluded.xFreeze, freeze=excluded.freeze,
                save_pct=excluded.save_pct, xSave_pct=excluded.xSave_pct,
                gsax=excluded.gsax,
                updated_at=datetime('now')
        """, (
            pid, g("name"), team, season, situation,
            g("games_played"), g("icetime"),
            xGoals, goals, ongoal, g("xOnGoal"),
            g("lowDangerShots"), g("lowDangerGoals"), g("lowDangerxGoals"),
            g("mediumDangerShots"), g("mediumDangerGoals"), g("mediumDangerxGoals"),
            g("highDangerShots"), g("highDangerGoals"), g("highDangerxGoals"),
            g("xRebounds"), g("rebounds"), g("xFreeze"), g("freeze"),
            save_pct, xSave_pct, gsax,
        ))
        count += 1

    conn.commit()
    log.info("Stored %d goalie-situation rows for season %s", count, season)
    return count


def download_moneypuck_shots(season: str = CURRENT_SEASON, conn: Optional[sqlite3.Connection] = None) -> int:
    """
    Download shot-level data from the peter-tanner MoneyPuck mirror.
    WARNING: These files are large (100MB+). Only download if needed.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_db()
        init_schema(conn)

    url = f"{MONEYPUCK_SHOTS_BASE}/shots_{season}.zip"
    log.info("Fetching shot data from %s (this may take a while)...", url)

    try:
        resp = requests.get(url, timeout=300, stream=True)
        if resp.status_code != 200:
            log.warning("Shot data download returned %d", resp.status_code)
            log_pipeline(conn, "moneypuck", f"shots_{season}", 0, "error",
                         f"HTTP {resp.status_code}")
            if own_conn:
                conn.close()
            return 0

        # Read zip into memory and extract CSV
        zip_data = io.BytesIO(resp.content)
        with zipfile.ZipFile(zip_data) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                log.warning("No CSV found in shot zip")
                if own_conn:
                    conn.close()
                return 0

            with zf.open(csv_names[0]) as f:
                df = pd.read_csv(f)

        log.info("Shot data: %d rows, %d columns", len(df), len(df.columns))

        # Store in batches
        count = 0
        batch_size = 5000
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            rows = []
            for _, r in batch.iterrows():
                def g(col):
                    v = r.get(col)
                    if pd.isna(v):
                        return None
                    return v

                rows.append((
                    season, g("game_id"), g("period"), g("time"),
                    normalize_team(str(g("teamCode") or "")),
                    g("shooterPlayerId"), g("shooterName"),
                    g("goalieIdForShot"), g("goalieNameForShot"),
                    1 if g("goal") == 1 else 0,
                    g("xGoal"), g("shotType"),
                    g("arenaAdjustedXCord"), g("arenaAdjustedYCord"),
                    g("shotDistance"), g("shotAngle"),
                    normalize_team(str(g("homeTeamCode") or "")),
                    normalize_team(str(g("awayTeamCode") or "")),
                    g("isHomeTeam"),
                    g("homeTeamGoals"), g("awayTeamGoals"),
                    g("shotReplayUrl"),  # placeholder for strength column
                ))
                count += 1

            conn.executemany("""
                INSERT INTO nhl_shots (
                    season, game_id, period, time,
                    team, shooter_id, shooter_name,
                    goalie_id, goalie_name,
                    is_goal, xGoal, shot_type,
                    location_x, location_y,
                    shot_distance, shot_angle,
                    home_team, away_team, is_home_team,
                    home_score, away_score, strength
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()

            if (start // batch_size) % 20 == 0:
                log.info("  Shot progress: %d / %d rows", count, len(df))

        log_pipeline(conn, "moneypuck", f"shots_{season}", count, "ok")
        log.info("Stored %d shot rows for season %s", count, season)

    except Exception as e:
        log.error("Failed to download shot data: %s", e)
        log_pipeline(conn, "moneypuck", f"shots_{season}", 0, "error", str(e))
        count = 0

    if own_conn:
        conn.close()
    return count


# ---------------------------------------------------------------------------
# NHL API Ingestion
# ---------------------------------------------------------------------------

def _nhl_api_get(endpoint: str) -> Optional[dict]:
    """Fetch from NHL API with error handling."""
    url = f"{NHL_API_BASE}/{endpoint}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            log.warning("NHL API %s returned %d", endpoint, resp.status_code)
            return None
        return resp.json()
    except Exception as e:
        log.error("NHL API %s failed: %s", endpoint, e)
        return None


def download_nhl_standings(conn: Optional[sqlite3.Connection] = None) -> int:
    """Fetch current NHL standings and store in nhl_standings."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()
        init_schema(conn)

    log.info("Fetching NHL standings...")
    data = _nhl_api_get("standings/now")
    if not data or "standings" not in data:
        log.warning("No standings data received")
        if own_conn:
            conn.close()
        return 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0

    for s in data["standings"]:
        team = s.get("teamAbbrev", {})
        if isinstance(team, dict):
            team = team.get("default", "")
        team = normalize_team(str(team))

        season_id = str(s.get("seasonId", ""))
        # Convert 20242025 -> 2024
        season = season_id[:4] if len(season_id) >= 4 else CURRENT_SEASON

        conn.execute("""
            INSERT INTO nhl_standings (
                team, season, snapshot_date,
                games_played, wins, losses, ot_losses, points, point_pct,
                regulation_wins, goal_for, goal_against, goal_diff,
                home_wins, home_losses, home_ot_losses,
                road_wins, road_losses, road_ot_losses,
                l10_wins, l10_losses, l10_ot_losses, l10_points,
                streak_code, streak_count,
                division, conference,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(team, snapshot_date) DO UPDATE SET
                games_played=excluded.games_played, wins=excluded.wins,
                losses=excluded.losses, ot_losses=excluded.ot_losses,
                points=excluded.points, point_pct=excluded.point_pct,
                regulation_wins=excluded.regulation_wins,
                goal_for=excluded.goal_for, goal_against=excluded.goal_against,
                goal_diff=excluded.goal_diff,
                home_wins=excluded.home_wins, home_losses=excluded.home_losses,
                home_ot_losses=excluded.home_ot_losses,
                road_wins=excluded.road_wins, road_losses=excluded.road_losses,
                road_ot_losses=excluded.road_ot_losses,
                l10_wins=excluded.l10_wins, l10_losses=excluded.l10_losses,
                l10_ot_losses=excluded.l10_ot_losses, l10_points=excluded.l10_points,
                streak_code=excluded.streak_code, streak_count=excluded.streak_count,
                division=excluded.division, conference=excluded.conference,
                updated_at=datetime('now')
        """, (
            team, season, today,
            s.get("gamesPlayed"), s.get("wins"), s.get("losses"),
            s.get("otLosses"), s.get("points"), s.get("pointPctg"),
            s.get("regulationWins"), s.get("goalFor"), s.get("goalAgainst"),
            s.get("goalDifferential"),
            s.get("homeWins"), s.get("homeLosses"), s.get("homeOtLosses"),
            s.get("roadWins"), s.get("roadLosses"), s.get("roadOtLosses"),
            s.get("l10Wins"), s.get("l10Losses"), s.get("l10OtLosses"),
            s.get("l10Points"),
            s.get("streakCode"), s.get("streakCount"),
            s.get("divisionName"), s.get("conferenceName"),
        ))
        count += 1

    conn.commit()
    log_pipeline(conn, "nhl_api", "standings", count, "ok")
    log.info("Stored standings for %d teams", count)

    if own_conn:
        conn.close()
    return count


def download_nhl_schedule(conn: Optional[sqlite3.Connection] = None) -> int:
    """Fetch upcoming schedule and store in nhl_schedule."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()
        init_schema(conn)

    log.info("Fetching NHL schedule...")
    data = _nhl_api_get("schedule/now")
    if not data or "gameWeek" not in data:
        log.warning("No schedule data received")
        if own_conn:
            conn.close()
        return 0

    count = 0
    for day in data["gameWeek"]:
        game_date = day.get("date", "")
        for g in day.get("games", []):
            game_id = g.get("id")
            if not game_id:
                continue

            home = g.get("homeTeam", {})
            away = g.get("awayTeam", {})
            home_abbrev = normalize_team(home.get("abbrev", ""))
            away_abbrev = normalize_team(away.get("abbrev", ""))

            venue = g.get("venue", {})
            venue_name = venue.get("default", "") if isinstance(venue, dict) else str(venue)

            conn.execute("""
                INSERT INTO nhl_schedule (
                    id, game_date, start_time, home_team, away_team,
                    venue, game_type, game_state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(id) DO UPDATE SET
                    game_date=excluded.game_date, start_time=excluded.start_time,
                    home_team=excluded.home_team, away_team=excluded.away_team,
                    venue=excluded.venue, game_type=excluded.game_type,
                    game_state=excluded.game_state, updated_at=datetime('now')
            """, (
                game_id, game_date, g.get("startTimeUTC"),
                home_abbrev, away_abbrev,
                venue_name, g.get("gameType"), g.get("gameState"),
            ))
            count += 1

    conn.commit()

    # Compute rest days and back-to-back flags
    _compute_rest_days(conn)

    log_pipeline(conn, "nhl_api", "schedule", count, "ok")
    log.info("Stored %d scheduled games", count)

    if own_conn:
        conn.close()
    return count


def download_nhl_scores(days_back: int = 7, conn: Optional[sqlite3.Connection] = None) -> int:
    """Fetch recent game results from NHL API and store in nhl_games."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()
        init_schema(conn)

    count = 0
    today = datetime.now(timezone.utc).date()

    for offset in range(days_back + 1):
        d = today - timedelta(days=offset)
        date_str = d.strftime("%Y-%m-%d")

        data = _nhl_api_get(f"score/{date_str}")
        if not data:
            continue

        games = data.get("games", [])
        if not games:
            # Try gameWeek format
            for day in data.get("gameWeek", []):
                games.extend(day.get("games", []))

        for g in games:
            game_id = g.get("id")
            if not game_id:
                continue

            state = g.get("gameState", "")
            # Only store completed games
            if state not in ("OFF", "FINAL"):
                continue

            home = g.get("homeTeam", {})
            away = g.get("awayTeam", {})
            home_abbrev = normalize_team(home.get("abbrev", ""))
            away_abbrev = normalize_team(away.get("abbrev", ""))
            home_score = home.get("score")
            away_score = away.get("score")

            home_win = None
            total = None
            diff = None
            if home_score is not None and away_score is not None:
                home_win = 1 if home_score > away_score else 0
                total = home_score + away_score
                diff = home_score - away_score

            outcome = g.get("gameOutcome", {})
            if isinstance(outcome, dict):
                outcome = outcome.get("lastPeriodType", "REG")

            venue = g.get("venue", {})
            venue_name = venue.get("default", "") if isinstance(venue, dict) else ""

            season_id = str(g.get("season", ""))
            season = season_id[:4] if len(season_id) >= 4 else CURRENT_SEASON

            conn.execute("""
                INSERT INTO nhl_games (
                    id, season, game_type, game_date, start_time, game_state,
                    home_team, away_team, home_score, away_score,
                    period, game_outcome, venue,
                    home_win, total_goals, goal_diff,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(id) DO UPDATE SET
                    game_state=excluded.game_state,
                    home_score=excluded.home_score, away_score=excluded.away_score,
                    period=excluded.period, game_outcome=excluded.game_outcome,
                    home_win=excluded.home_win, total_goals=excluded.total_goals,
                    goal_diff=excluded.goal_diff,
                    updated_at=datetime('now')
            """, (
                game_id, season, g.get("gameType"),
                g.get("gameDate", date_str), g.get("startTimeUTC"), state,
                home_abbrev, away_abbrev, home_score, away_score,
                g.get("period"), outcome, venue_name,
                home_win, total, diff,
            ))
            count += 1

    conn.commit()
    log_pipeline(conn, "nhl_api", "scores", count, "ok")
    log.info("Stored %d game results (last %d days)", count, days_back)

    if own_conn:
        conn.close()
    return count


def _compute_rest_days(conn: sqlite3.Connection) -> None:
    """Compute rest days and back-to-back flags for scheduled games."""
    # Get all scheduled games
    rows = conn.execute(
        "SELECT id, game_date, home_team, away_team FROM nhl_schedule ORDER BY game_date"
    ).fetchall()

    # Also get recent completed games for rest day calculation
    recent_games = conn.execute(
        "SELECT game_date, home_team, away_team FROM nhl_games ORDER BY game_date DESC LIMIT 500"
    ).fetchall()

    # Build last-game-date index per team
    team_dates: dict[str, list[str]] = {}
    for g in recent_games:
        for t in [g["home_team"], g["away_team"]]:
            if t:
                team_dates.setdefault(t, []).append(g["game_date"])
    for g in rows:
        for t in [g["home_team"], g["away_team"]]:
            if t:
                team_dates.setdefault(t, []).append(g["game_date"])

    # Sort dates
    for t in team_dates:
        team_dates[t] = sorted(set(team_dates[t]))

    for g in rows:
        gd = g["game_date"]
        for team_col, rest_col, b2b_col in [
            ("home_team", "home_rest_days", "home_b2b"),
            ("away_team", "away_rest_days", "away_b2b"),
        ]:
            team = g[team_col]
            if not team or team not in team_dates:
                continue
            dates = team_dates[team]
            idx = None
            for i, d in enumerate(dates):
                if d == gd:
                    idx = i
                    break
            if idx is not None and idx > 0:
                prev = dates[idx - 1]
                try:
                    d1 = datetime.strptime(prev, "%Y-%m-%d")
                    d2 = datetime.strptime(gd, "%Y-%m-%d")
                    rest = (d2 - d1).days - 1  # 0 = back-to-back
                    b2b = 1 if rest == 0 else 0
                    conn.execute(
                        f"UPDATE nhl_schedule SET {rest_col}=?, {b2b_col}=? WHERE id=?",
                        (rest, b2b, g["id"]),
                    )
                except ValueError:
                    pass

    conn.commit()


# ---------------------------------------------------------------------------
# Feature Computation
# ---------------------------------------------------------------------------

def compute_team_features(team: str, season: str = CURRENT_SEASON,
                          conn: Optional[sqlite3.Connection] = None) -> Optional[dict]:
    """
    Compute comprehensive team features for predictive modeling.

    Returns a dict of features, or None if insufficient data.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    team = normalize_team(team)
    features = {"team": team, "season": season}

    # --- From MoneyPuck team stats (5v5 situation for possession) ---
    mp_all = conn.execute(
        "SELECT * FROM nhl_teams WHERE team=? AND season=? AND situation='all'",
        (team, season),
    ).fetchone()

    mp_5v5 = conn.execute(
        "SELECT * FROM nhl_teams WHERE team=? AND season=? AND situation='5on5'",
        (team, season),
    ).fetchone()

    if mp_all:
        gp = mp_all["games_played"] or 1
        features["goals_for_per_game"] = round((mp_all["goalsFor"] or 0) / gp, 3)
        features["goals_against_per_game"] = round((mp_all["goalsAgainst"] or 0) / gp, 3)
        features["xGoalsFor_per_game"] = round((mp_all["xGoalsFor"] or 0) / gp, 3)
        features["xGoalsAgainst_per_game"] = round((mp_all["xGoalsAgainst"] or 0) / gp, 3)
        features["xGoals_pct"] = mp_all["xGoalsPercentage"]
        features["shots_for_per_game"] = round((mp_all["shotsOnGoalFor"] or 0) / gp, 2)
        features["shots_against_per_game"] = round((mp_all["shotsOnGoalAgainst"] or 0) / gp, 2)
        features["high_danger_for_pct"] = (
            round((mp_all["highDangerShotsFor"] or 0) /
                  max((mp_all["highDangerShotsFor"] or 0) + (mp_all["highDangerShotsAgainst"] or 0), 1), 3)
        )
        features["high_danger_against_pct"] = 1.0 - features["high_danger_for_pct"]

    if mp_5v5:
        # Corsi = all shot attempts (shots on goal + missed + blocked)
        corsi_for = mp_5v5["shotAttemptsFor"] or 0
        corsi_against = mp_5v5["shotAttemptsAgainst"] or 0
        features["corsi_diff"] = corsi_for - corsi_against
        # Fenwick = unblocked shot attempts = Corsi - blocked shots
        # MoneyPuck stores blockedShotAttempts separately but we store the totals
        # Fenwick% is available; compute raw Fenwick from shot attempts - blocked
        fenwick_pct = mp_5v5["fenwickPercentage"]
        if fenwick_pct and corsi_for + corsi_against > 0:
            # Use fenwick% to derive differential (more reliable than column arithmetic)
            total_fenwick = (corsi_for + corsi_against) * 0.75  # ~75% of Corsi is unblocked
            features["fenwick_diff"] = round(total_fenwick * (fenwick_pct - 0.5) * 2, 0)
        else:
            features["fenwick_diff"] = 0

    # --- From MoneyPuck team stats: special teams ---
    mp_pp = conn.execute(
        "SELECT * FROM nhl_teams WHERE team=? AND season=? AND situation='5on4'",
        (team, season),
    ).fetchone()
    mp_pk = conn.execute(
        "SELECT * FROM nhl_teams WHERE team=? AND season=? AND situation='4on5'",
        (team, season),
    ).fetchone()

    if mp_pp and mp_all:
        pp_goals = mp_pp["goalsFor"] or 0
        pp_opps = mp_all["penaltiesAgainst"] or 1  # opponent penalties = our PP opportunities
        features["pp_pct"] = round(pp_goals / max(pp_opps, 1) * 100, 1)
    if mp_pk and mp_all:
        pk_goals_against = mp_pk["goalsAgainst"] or 0
        pk_opps = mp_all["penaltiesFor"] or 1  # our penalties = their PP
        features["pk_pct"] = round((1 - pk_goals_against / max(pk_opps, 1)) * 100, 1)

    # --- From NHL standings ---
    standings = conn.execute(
        "SELECT * FROM nhl_standings WHERE team=? ORDER BY snapshot_date DESC LIMIT 1",
        (team,),
    ).fetchone()

    if standings:
        features["points_pct"] = standings["point_pct"]
        features["l10_points_pct"] = round((standings["l10_points"] or 0) / max((standings["l10_wins"] or 0) + (standings["l10_losses"] or 0) + (standings["l10_ot_losses"] or 0), 1) / 2, 3)

        total_home = (standings["home_wins"] or 0) + (standings["home_losses"] or 0) + (standings["home_ot_losses"] or 0)
        total_road = (standings["road_wins"] or 0) + (standings["road_losses"] or 0) + (standings["road_ot_losses"] or 0)
        features["home_win_pct"] = round((standings["home_wins"] or 0) / max(total_home, 1), 3)
        features["road_win_pct"] = round((standings["road_wins"] or 0) / max(total_road, 1), 3)

    # --- Rolling goals from game results (L10, L20) ---
    home_games = conn.execute(
        "SELECT home_score as gf, away_score as ga FROM nhl_games "
        "WHERE home_team=? AND season=? AND game_state='OFF' ORDER BY game_date DESC",
        (team, season),
    ).fetchall()

    away_games = conn.execute(
        "SELECT away_score as gf, home_score as ga FROM nhl_games "
        "WHERE away_team=? AND season=? AND game_state='OFF' ORDER BY game_date DESC",
        (team, season),
    ).fetchall()

    # Merge and sort by recency (already sorted from each query, interleave)
    all_results = []
    for g in home_games:
        all_results.append((g["gf"], g["ga"]))
    for g in away_games:
        all_results.append((g["gf"], g["ga"]))

    if all_results:
        def rolling_avg(results, n):
            subset = results[:n] if n else results
            if not subset:
                return None, None
            gf = sum(r[0] for r in subset if r[0] is not None) / len(subset)
            ga = sum(r[1] for r in subset if r[1] is not None) / len(subset)
            return round(gf, 3), round(ga, 3)

        gf10, ga10 = rolling_avg(all_results, 10)
        gf20, ga20 = rolling_avg(all_results, 20)

        features["goals_for_per_game_l10"] = gf10
        features["goals_against_per_game_l10"] = ga10
        features["goals_for_per_game_l20"] = gf20
        features["goals_against_per_game_l20"] = ga20

    # --- Goaltending ---
    goalies = conn.execute(
        "SELECT * FROM nhl_goalies WHERE team=? AND season=? AND situation='all' "
        "ORDER BY games_played DESC",
        (team, season),
    ).fetchall()

    if goalies:
        # Weighted by games played
        total_gp = sum(g_["games_played"] or 0 for g_ in goalies)
        if total_gp > 0:
            w_save = sum((g_["save_pct"] or 0) * (g_["games_played"] or 0) for g_ in goalies) / total_gp
            w_xsave = sum((g_["xSave_pct"] or 0) * (g_["games_played"] or 0) for g_ in goalies) / total_gp
            w_gsax = sum((g_["gsax"] or 0) for g_ in goalies)
            features["team_save_pct"] = round(w_save, 4)
            features["team_xSave_pct"] = round(w_xsave, 4)
            features["team_gsax"] = round(w_gsax, 2)

    # --- Store computed features ---
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cols = [k for k in features if k not in ("team", "season")]
    vals = [features.get(k) for k in cols]

    # Build dynamic insert
    col_str = ", ".join(cols)
    placeholder_str = ", ".join(["?"] * len(cols))
    update_str = ", ".join(f"{c}=excluded.{c}" for c in cols)

    try:
        conn.execute(
            f"INSERT INTO nhl_team_features (team, season, computed_at, {col_str}) "
            f"VALUES (?, ?, ?, {placeholder_str}) "
            f"ON CONFLICT(team, season, computed_at) DO UPDATE SET {update_str}",
            (team, season, now, *vals),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        # If column doesn't exist in table, log and continue
        log.warning("Feature storage issue for %s: %s", team, e)

    if own_conn:
        conn.close()

    return features


def compute_all_team_features(season: str = CURRENT_SEASON,
                              conn: Optional[sqlite3.Connection] = None) -> dict:
    """Compute features for all teams in the database."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    teams = conn.execute(
        "SELECT DISTINCT team FROM nhl_teams WHERE season=? AND situation='all'",
        (season,),
    ).fetchall()

    results = {}
    for t in teams:
        team = t["team"]
        feats = compute_team_features(team, season, conn)
        if feats:
            results[team] = feats

    log.info("Computed features for %d teams", len(results))
    log_pipeline(conn, "features", f"team_features_{season}", len(results), "ok")

    if own_conn:
        conn.close()
    return results


def get_game_features(home_team: str, away_team: str, season: str = CURRENT_SEASON,
                      conn: Optional[sqlite3.Connection] = None) -> dict:
    """
    Get all features for a specific matchup, ready for model consumption.

    Returns a flat dict with prefixed keys: home_*, away_*, and matchup-level features.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    home_team = normalize_team(home_team)
    away_team = normalize_team(away_team)

    home_feats = compute_team_features(home_team, season, conn)
    away_feats = compute_team_features(away_team, season, conn)

    matchup = {
        "home_team": home_team,
        "away_team": away_team,
        "season": season,
    }

    # Prefix features
    if home_feats:
        for k, v in home_feats.items():
            if k not in ("team", "season"):
                matchup[f"home_{k}"] = v

    if away_feats:
        for k, v in away_feats.items():
            if k not in ("team", "season"):
                matchup[f"away_{k}"] = v

    # Matchup-level derived features
    if home_feats and away_feats:
        hgf = home_feats.get("goals_for_per_game", 0)
        aga = away_feats.get("goals_against_per_game", 0)
        agf = away_feats.get("goals_for_per_game", 0)
        hga = home_feats.get("goals_against_per_game", 0)

        # Implied totals
        matchup["implied_home_goals"] = round((hgf + aga) / 2, 3) if hgf and aga else None
        matchup["implied_away_goals"] = round((agf + hga) / 2, 3) if agf and hga else None
        if matchup["implied_home_goals"] and matchup["implied_away_goals"]:
            matchup["implied_total"] = round(
                matchup["implied_home_goals"] + matchup["implied_away_goals"], 3
            )

        # Strength differential
        hp = home_feats.get("points_pct", 0)
        ap = away_feats.get("points_pct", 0)
        matchup["points_pct_diff"] = round((hp or 0) - (ap or 0), 4)

        hxg = home_feats.get("xGoals_pct", 0)
        axg = away_feats.get("xGoals_pct", 0)
        matchup["xGoals_pct_diff"] = round((hxg or 0) - (axg or 0), 4)

    # Rest days from schedule
    sched = conn.execute(
        "SELECT * FROM nhl_schedule WHERE home_team=? AND away_team=? "
        "ORDER BY game_date DESC LIMIT 1",
        (home_team, away_team),
    ).fetchone()

    if sched:
        matchup["home_rest_days"] = sched["home_rest_days"]
        matchup["away_rest_days"] = sched["away_rest_days"]
        matchup["home_b2b"] = sched["home_b2b"]
        matchup["away_b2b"] = sched["away_b2b"]
        matchup["game_date"] = sched["game_date"]

    if own_conn:
        conn.close()

    return matchup


def get_todays_matchups(conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """Get features for all of today's (and upcoming) scheduled games."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    games = conn.execute(
        "SELECT * FROM nhl_schedule WHERE game_date >= ? AND game_state='FUT' "
        "ORDER BY game_date, start_time",
        (today,),
    ).fetchall()

    matchups = []
    for g in games:
        feats = get_game_features(g["home_team"], g["away_team"], conn=conn)
        feats["game_id"] = g["id"]
        feats["start_time"] = g["start_time"]
        matchups.append(feats)

    if own_conn:
        conn.close()

    return matchups


# ---------------------------------------------------------------------------
# Full Pipeline
# ---------------------------------------------------------------------------

def update_all(season: str = CURRENT_SEASON, include_shots: bool = False) -> dict:
    """
    Run the full NHL data pipeline.

    1. Download MoneyPuck season summaries (teams, skaters, goalies)
    2. Download NHL API data (standings, schedule, scores)
    3. Compute derived team features
    4. Optionally download shot-level data

    Returns summary of what was updated.
    """
    conn = get_db()
    init_schema(conn)

    summary = {"started_at": datetime.now(timezone.utc).isoformat()}

    log.info("=" * 60)
    log.info("NHL DATA PIPELINE - Full Update")
    log.info("Season: %s | Shots: %s", season, include_shots)
    log.info("=" * 60)

    # 1. MoneyPuck
    log.info("")
    log.info("--- PHASE 1: MoneyPuck Season Summaries ---")
    mp_results = download_moneypuck_data(season, conn)
    summary["moneypuck"] = mp_results

    # 2. NHL API
    log.info("")
    log.info("--- PHASE 2: NHL API Data ---")
    summary["standings"] = download_nhl_standings(conn)
    summary["schedule"] = download_nhl_schedule(conn)
    summary["scores"] = download_nhl_scores(days_back=14, conn=conn)

    # 3. Features
    log.info("")
    log.info("--- PHASE 3: Feature Computation ---")
    team_feats = compute_all_team_features(season, conn)
    summary["team_features"] = len(team_feats)

    # 4. Shots (optional, large download)
    if include_shots:
        log.info("")
        log.info("--- PHASE 4: Shot Data (Large Download) ---")
        summary["shots"] = download_moneypuck_shots(season, conn)

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()

    # Print summary
    log.info("")
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE")
    log.info("  MoneyPuck teams:   %s rows", mp_results.get("teams", 0))
    log.info("  MoneyPuck skaters: %s rows", mp_results.get("skaters", 0))
    log.info("  MoneyPuck goalies: %s rows", mp_results.get("goalies", 0))
    log.info("  NHL standings:     %s teams", summary.get("standings", 0))
    log.info("  NHL schedule:      %s games", summary.get("schedule", 0))
    log.info("  NHL scores:        %s games", summary.get("scores", 0))
    log.info("  Team features:     %s teams", summary.get("team_features", 0))
    if include_shots:
        log.info("  Shot data:         %s rows", summary.get("shots", 0))
    log.info("  Database:          %s", DB_PATH)
    log.info("=" * 60)

    conn.close()
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="NHL Data Pipeline for Predictive Modeling")
    parser.add_argument("--moneypuck", metavar="SEASON",
                        help="Download MoneyPuck data for a specific season (e.g., 2024)")
    parser.add_argument("--schedule", action="store_true",
                        help="Download schedule and scores only")
    parser.add_argument("--standings", action="store_true",
                        help="Download standings only")
    parser.add_argument("--scores", action="store_true",
                        help="Download recent scores only")
    parser.add_argument("--features", action="store_true",
                        help="Recompute team features only")
    parser.add_argument("--shots", action="store_true",
                        help="Download shot-level data (large, 100MB+)")
    parser.add_argument("--matchup", nargs=2, metavar=("HOME", "AWAY"),
                        help="Get features for a specific matchup (e.g., TOR WSH)")
    parser.add_argument("--today", action="store_true",
                        help="Get features for all of today's games")
    parser.add_argument("--season", default=CURRENT_SEASON,
                        help=f"Season to process (default: {CURRENT_SEASON})")
    parser.add_argument("--init-db", action="store_true",
                        help="Initialize database schema only")

    args = parser.parse_args()

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    if args.init_db:
        conn = get_db()
        init_schema(conn)
        conn.close()
        log.info("Database schema initialized at %s", DB_PATH)
        return

    if args.matchup:
        conn = get_db()
        init_schema(conn)
        feats = get_game_features(args.matchup[0], args.matchup[1], args.season, conn)
        conn.close()
        print(json.dumps(feats, indent=2, default=str))
        return

    if args.today:
        conn = get_db()
        init_schema(conn)
        matchups = get_todays_matchups(conn)
        conn.close()
        for m in matchups:
            print(f"\n{m.get('away_team', '?')} @ {m.get('home_team', '?')} "
                  f"({m.get('game_date', '?')})")
            print(f"  Implied: {m.get('implied_away_goals', '?')}-{m.get('implied_home_goals', '?')} "
                  f"(total: {m.get('implied_total', '?')})")
            print(f"  Points% diff: {m.get('points_pct_diff', '?')}")
            print(f"  xG% diff: {m.get('xGoals_pct_diff', '?')}")
            print(f"  Rest: home={m.get('home_rest_days', '?')}d "
                  f"away={m.get('away_rest_days', '?')}d "
                  f"(B2B: H={m.get('home_b2b', '?')} A={m.get('away_b2b', '?')})")
        if not matchups:
            print("No upcoming games found. Run --schedule first.")
        return

    if args.moneypuck:
        conn = get_db()
        init_schema(conn)
        download_moneypuck_data(args.moneypuck, conn)
        conn.close()
        return

    if args.schedule:
        conn = get_db()
        init_schema(conn)
        download_nhl_schedule(conn)
        download_nhl_scores(conn=conn)
        conn.close()
        return

    if args.standings:
        conn = get_db()
        init_schema(conn)
        download_nhl_standings(conn)
        conn.close()
        return

    if args.scores:
        conn = get_db()
        init_schema(conn)
        download_nhl_scores(conn=conn)
        conn.close()
        return

    if args.features:
        conn = get_db()
        init_schema(conn)
        compute_all_team_features(args.season, conn)
        conn.close()
        return

    if args.shots:
        conn = get_db()
        init_schema(conn)
        download_moneypuck_shots(args.season, conn)
        conn.close()
        return

    # Default: full pipeline update (no shots unless --shots)
    update_all(season=args.season, include_shots=False)


if __name__ == "__main__":
    main()

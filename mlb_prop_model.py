#!/usr/bin/env python3
"""
MLB Pitcher Strikeout Prop Model
================================

Projects pitcher strikeouts using:
- Pitcher K/9 (rolling L3, L5, season)
- Pitcher average innings pitched
- Opponent team K% (how often they strike out)
- Park factor
- Weather (temperature, wind)
- Home/away

Compares projections to FanDuel posted lines to find edges.

Usage:
    python3 mlb_prop_model.py              # Generate today's K prop picks
    python3 mlb_prop_model.py backtest     # Backtest on historical data
"""

import math
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

import numpy as np
from scipy.stats import nbinom

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GL_DB = os.path.join(DATA_DIR, "game_lines.db")
SE_DB = os.path.join(DATA_DIR, "sports_edge.db")

# Park factors for strikeouts (correlated with but not identical to run factors)
# Adjustments based on known K-friendly parks
PARK_K_FACTOR = {
    "COL": 0.92,  # Coors suppresses Ks (thinner air, ball carries but batters see it better)
    "ARI": 1.02, "CIN": 1.01, "NYY": 1.00, "BOS": 0.98,
    "PHI": 1.01, "BAL": 1.00, "CHC": 0.99, "CWS": 1.00,
    "HOU": 1.03, "TEX": 1.02, "TOR": 1.01, "MIL": 1.02,
    "MIN": 1.00, "ATL": 1.00, "WSH": 1.00, "LAD": 1.01,
    "KC": 0.99, "LAA": 1.00, "CLE": 1.01, "STL": 1.00,
    "DET": 1.00, "PIT": 1.00, "NYM": 1.01, "OAK": 1.00,
    "SD": 1.02, "SEA": 1.01, "MIA": 1.03, "TB": 1.02, "SF": 1.01,
}

IS_DOME = {"ARI", "HOU", "TEX", "TOR", "MIL", "SEA", "MIA", "TB"}

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
    "Athletics": "OAK",
}


def load_pitcher_logs():
    """Load all pitcher game logs from game_lines.db."""
    conn = sqlite3.connect(GL_DB, timeout=15)
    rows = conn.execute("""
        SELECT pitcher_id, pitcher_name, game_date, team,
               innings_pitched, strikeouts, walks, hits_allowed,
               home_runs_allowed, pitches_thrown
        FROM mlb_pitcher_game_logs
        WHERE game_started = 1 AND innings_pitched > 0
        ORDER BY pitcher_id, game_date
    """).fetchall()
    conn.close()

    logs = defaultdict(list)
    for r in rows:
        logs[r[0]].append({
            "name": r[1], "date": r[2], "team": r[3],
            "ip": r[4], "k": r[5], "bb": r[6], "h": r[7],
            "hr": r[8], "pitches": r[9],
        })
    return logs


def load_team_k_rates():
    """Compute team strikeout rates from batter game logs and pitcher game logs."""
    conn = sqlite3.connect(GL_DB, timeout=15)

    # Build team K rates from pitcher game logs (opponent Ks)
    # For each game, the pitcher's K total = opponent team's Ks that game
    rows = conn.execute("""
        SELECT s.game_date,
               CASE WHEN s.home_team = l.team THEN s.away_team ELSE s.home_team END as opponent,
               l.strikeouts, l.innings_pitched
        FROM mlb_pitcher_game_logs l
        JOIN mlb_game_starters s ON l.game_date = s.game_date
            AND (l.team = s.home_team OR l.team = s.away_team)
        WHERE l.game_started = 1 AND l.innings_pitched >= 3
    """).fetchall()
    conn.close()

    # Group by team and date for rolling computation
    team_games = defaultdict(list)
    for r in rows:
        date, opp, k, ip = r
        # This game, opponent struck out 'k' times in 'ip' innings
        team_games[opp].append({"date": date, "k": k, "ip": ip})

    # Sort each team's games by date
    for team in team_games:
        team_games[team].sort(key=lambda x: x["date"])

    return team_games


def log5_matchup_k_rate(pitcher_k_pct, opponent_k_pct, league_k_pct=0.222):
    """
    Standard log5 matchup formula for K%.

    log5: matchup = (P * B / L) / (P * B / L + (1-P) * (1-B) / (1-L))

    where P = pitcher K%, B = opponent batters' K%, L = league average K%.
    Based on FanGraphs validation (1.5M+ plate appearances).
    Updated for current league K rate (22.2%, 2024 baseline).
    """
    B = opponent_k_pct  # Opponent batters' aggregate K%
    P = pitcher_k_pct   # Pitcher's K%
    L = league_k_pct
    if B <= 0 or P <= 0:
        return L
    numerator = P * B / L
    denominator = numerator + (1 - P) * (1 - B) / (1 - L)
    if denominator <= 0:
        return L
    matchup = numerator / denominator
    return max(0.05, min(0.50, matchup))


def compute_pitcher_projection(pitcher_logs, game_date, opponent_k_games, park_team, n_recent=5):
    """
    Project a pitcher's strikeouts for a game.

    Uses:
    - Pitcher's K rate (as K%)
    - Expected innings pitched
    - Log5 matchup formula (pitcher K% x opponent K%)
    - Park K factor
    """
    # Get pitcher's recent starts before this date
    prior = [l for l in pitcher_logs if l["date"] < game_date]
    if len(prior) < 3:
        return None

    # Pitcher K/9 (last 5 starts)
    recent = prior[-n_recent:]
    total_ip = sum(l["ip"] for l in recent)
    total_k = sum(l["k"] for l in recent)
    if total_ip == 0:
        return None
    k_per_9 = (total_k / total_ip) * 9

    # Season K/9
    season_ip = sum(l["ip"] for l in prior)
    season_k = sum(l["k"] for l in prior)
    season_k9 = (season_k / season_ip) * 9 if season_ip > 0 else k_per_9

    # Expected innings (rolling average)
    avg_ip = sum(l["ip"] for l in recent) / len(recent)

    # Convert pitcher K/9 to K% (K per batter faced approximation)
    # ~4.3 batters per inning on average (accounting for baserunners)
    batters_per_9 = 38.5  # ~4.28 batters/inning * 9
    blended_k9 = 0.6 * k_per_9 + 0.4 * season_k9
    pitcher_k_pct = blended_k9 / batters_per_9

    # Opponent team K rate as K%
    opp_prior = [g for g in opponent_k_games if g["date"] < game_date]
    if len(opp_prior) >= 10:
        opp_recent = opp_prior[-20:]
        opp_total_k = sum(g["k"] for g in opp_recent)
        opp_total_ip = sum(g["ip"] for g in opp_recent)
        opp_k_per_9 = (opp_total_k / opp_total_ip) * 9 if opp_total_ip > 0 else 8.5
        opp_k_pct = opp_k_per_9 / batters_per_9
    else:
        opp_k_per_9 = 8.5
        opp_k_pct = 8.5 / batters_per_9

    # Log5 matchup K rate
    matchup_k_pct = log5_matchup_k_rate(pitcher_k_pct, opp_k_pct)

    # Park factor
    park_k = PARK_K_FACTOR.get(park_team, 1.0)

    # Project total Ks: matchup K% * expected batters faced * park factor
    expected_batters = avg_ip * (batters_per_9 / 9)
    projected_k = matchup_k_pct * expected_batters * park_k

    return {
        "projected_k": projected_k,
        "k_per_9_recent": k_per_9,
        "k_per_9_season": season_k9,
        "avg_ip": avg_ip,
        "opp_k_rate": opp_k_per_9,
        "pitcher_k_pct": pitcher_k_pct,
        "opp_k_pct": opp_k_pct,
        "matchup_k_pct": matchup_k_pct,
        "park_k_factor": park_k,
        "n_starts": len(prior),
    }


def american_to_prob(odds):
    """Convert American odds to implied probability."""
    if odds is None:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def prob_to_american(prob):
    """Convert probability to American odds."""
    if prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int(100 * (1 - prob) / prob)


# Overdispersion parameter for pitcher Ks (empirical: variance/mean = 1.173 on 23K starts)
K_OVERDISPERSION = 1.173


def _nb_params_k(mu, overdispersion=K_OVERDISPERSION):
    """Convert mean + overdispersion to scipy nbinom (n, p) parameters for K props."""
    if overdispersion <= 1.0 or mu <= 0:
        # Fall back to Poisson-equivalent (very large n)
        return 1e6, 1e6 / (1e6 + mu)
    r = mu / (overdispersion - 1)
    p = r / (r + mu)
    return r, p


def negbin_over_prob(projected_k, line):
    """
    Calculate probability of going OVER a strikeout line using Negative Binomial.

    NegBin accounts for overdispersion (variance > mean) in pitcher K counts.
    Empirical overdispersion ratio is 1.173 (23K starts).
    This produces wider tails than Poisson, reducing overconfidence on extreme lines.
    """
    threshold = math.ceil(line)
    r, p = _nb_params_k(projected_k)
    # P(X >= threshold) = 1 - CDF(threshold - 1)
    return 1 - nbinom.cdf(threshold - 1, r, p)


def poisson_over_prob(projected_k, line):
    """Legacy Poisson function -- kept for backtest comparison only."""
    threshold = math.ceil(line)
    prob_under = 0
    for k in range(threshold):
        prob_under += (projected_k ** k * math.exp(-projected_k)) / math.factorial(k)
    return 1 - prob_under


def generate_today_picks():
    """Generate strikeout prop picks for today's games."""
    print("Loading pitcher data...")
    pitcher_logs = load_pitcher_logs()
    team_k_games = load_team_k_rates()

    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's starters from game_lines.db
    conn = sqlite3.connect(GL_DB, timeout=15)
    starters = conn.execute("""
        SELECT game_date, home_team, away_team,
               home_pitcher_id, home_pitcher_name,
               away_pitcher_id, away_pitcher_name
        FROM mlb_game_starters
        WHERE game_date = ?
    """, (today,)).fetchall()

    # Build starters from mlb_pitchers table if game_starters empty
    if not starters:
        pitcher_rows = conn.execute("""
            SELECT game_id, game_date, team, pitcher_name, pitcher_id
            FROM mlb_pitchers
            WHERE game_date = ?
        """, (today,)).fetchall()
        if pitcher_rows:
            # Group by game_id to pair home/away, dedup by (game_id, pitcher_id)
            game_pitchers = defaultdict(dict)
            for r in pitcher_rows:
                pid = r[4]
                game_pitchers[r[0]][pid] = r  # Dedup by pitcher_id per game

            # We need to determine home/away -- use schedule or line snapshots
            se_conn = sqlite3.connect(SE_DB)
            schedule = {}

            # Use mlb_schedule first (has home/away team IDs)
            try:
                sched_rows = se_conn.execute("""
                    SELECT home_team_abbrev, away_team_abbrev
                    FROM mlb_schedule WHERE game_date = ?
                """, (today,)).fetchall()
                for sr in sched_rows:
                    schedule[sr[0]] = sr[1]
            except Exception:
                pass

            # Also check game_line_snapshots for team matchups
            try:
                snap_rows = se_conn.execute("""
                    SELECT DISTINCT home_team, away_team
                    FROM game_line_snapshots
                    WHERE sport='MLB' AND game_date=?
                """, (today,)).fetchall()
                for sr in snap_rows:
                    h = MLB_FULL_TO_ABBREV.get(sr[0], sr[0])
                    a = MLB_FULL_TO_ABBREV.get(sr[1], sr[1])
                    if h != a:  # Skip bad "Athletics Athletics" type entries
                        schedule[h] = a
            except Exception:
                pass
            se_conn.close()

            built_starters = []
            for gid, pitcher_dict in game_pitchers.items():
                pitchers = list(pitcher_dict.values())
                if len(pitchers) == 2:
                    p1, p2 = pitchers
                    t1 = MLB_FULL_TO_ABBREV.get(p1[2], p1[2])
                    t2 = MLB_FULL_TO_ABBREV.get(p2[2], p2[2])
                    # Determine home/away
                    if t1 in schedule:
                        ht, at = t1, t2
                        hp_id, hp_name = p1[4], p1[3]
                        ap_id, ap_name = p2[4], p2[3]
                    elif t2 in schedule:
                        ht, at = t2, t1
                        hp_id, hp_name = p2[4], p2[3]
                        ap_id, ap_name = p1[4], p1[3]
                    else:
                        # Can't determine home/away, use first as home
                        ht, at = t1, t2
                        hp_id, hp_name = p1[4], p1[3]
                        ap_id, ap_name = p2[4], p2[3]
                    built_starters.append((today, ht, at, hp_id, hp_name, ap_id, ap_name))

            starters = built_starters
            print(f"  Built {len(starters)} starter matchups from mlb_pitchers table")
    conn.close()

    # Get today's FanDuel K props
    props = {}
    try:
        se_conn = sqlite3.connect(SE_DB)
        # Main K line: market="Player Name - Strikeouts", has line + over/under odds
        prop_rows = se_conn.execute("""
            SELECT player, market, line, over_odds, under_odds, game
            FROM fd_prop_snapshots
            WHERE sport='MLB' AND market LIKE '% - Strikeouts'
            AND line > 0
            AND collected_at >= ?
            ORDER BY collected_at DESC
        """, (today,)).fetchall()

        for r in prop_rows:
            name = r[0]
            if name not in props:
                props[name] = {
                    "line": r[2],
                    "game": r[5],
                    "over_odds": r[3],
                    "under_odds": r[4],
                }

        se_conn.close()
        print(f"  Found {len(props)} pitcher K props from FanDuel")
    except Exception as e:
        print(f"  Error loading props: {e}")

    # Generate projections
    print(f"\nProjecting strikeouts for {today}...")
    picks = []

    if starters:
        for s in starters:
            gd, ht, at, hp_id, hp_name, ap_id, ap_name = s

            for pid, pname, team, opp, is_home in [
                (hp_id, hp_name, ht, at, True),
                (ap_id, ap_name, at, ht, False),
            ]:
                if not pid or pid not in pitcher_logs:
                    continue

                opp_k = team_k_games.get(opp, [])
                proj = compute_pitcher_projection(
                    pitcher_logs[pid], gd, opp_k, ht
                )
                if proj is None:
                    continue

                # Look up FanDuel line
                fd = props.get(pname, {})
                fd_line = fd.get("line")
                fd_over = fd.get("over_odds")
                fd_under = fd.get("under_odds")

                pick = {
                    "pitcher": pname,
                    "team": team,
                    "opponent": opp,
                    "venue": ht,
                    "is_home": is_home,
                    "projected_k": proj["projected_k"],
                    "k9_recent": proj["k_per_9_recent"],
                    "k9_season": proj["k_per_9_season"],
                    "avg_ip": proj["avg_ip"],
                    "opp_k_rate": proj["opp_k_rate"],
                    "park_k": proj["park_k_factor"],
                    "n_starts": proj["n_starts"],
                }

                if fd_line:
                    # Poisson outperforms NegBin for K props (backtest: 21K starts)
                    # K overdispersion (1.17) is mostly between-pitcher variance
                    # already captured by the projection model
                    p_over = poisson_over_prob(proj["projected_k"], fd_line)
                    p_under = 1 - p_over

                    # Devig FanDuel odds
                    fd_over_prob = american_to_prob(fd_over) if fd_over else None
                    fd_under_prob = american_to_prob(fd_under) if fd_under else None

                    if fd_over_prob and fd_under_prob:
                        total_prob = fd_over_prob + fd_under_prob
                        fd_fair_over = fd_over_prob / total_prob
                        fd_fair_under = fd_under_prob / total_prob
                    elif fd_over_prob:
                        fd_fair_over = fd_over_prob
                        fd_fair_under = 1 - fd_over_prob
                    elif fd_under_prob:
                        fd_fair_under = fd_under_prob
                        fd_fair_over = 1 - fd_under_prob
                    else:
                        fd_fair_over = 0.5
                        fd_fair_under = 0.5

                    over_edge = p_over - fd_fair_over
                    under_edge = p_under - fd_fair_under

                    pick["fd_line"] = fd_line
                    pick["fd_over_odds"] = fd_over
                    pick["fd_under_odds"] = fd_under
                    pick["p_over"] = p_over
                    pick["p_under"] = p_under
                    pick["fd_fair_over"] = fd_fair_over
                    pick["fd_fair_under"] = fd_fair_under
                    pick["over_edge"] = over_edge
                    pick["under_edge"] = under_edge

                    # Pick the side with more edge
                    if over_edge > under_edge and over_edge > 0.03:
                        pick["side"] = "OVER"
                        pick["edge"] = over_edge
                        pick["odds"] = fd_over
                    elif under_edge > 0.03:
                        pick["side"] = "UNDER"
                        pick["edge"] = under_edge
                        pick["odds"] = fd_under
                    else:
                        pick["side"] = None
                        pick["edge"] = max(over_edge, under_edge)

                picks.append(pick)

    # Sort by edge
    picks.sort(key=lambda x: x.get("edge", 0), reverse=True)

    # Print results
    print(f"\n{'='*70}")
    print(f"  MLB PITCHER STRIKEOUT PROPS - {today}")
    print(f"{'='*70}")

    if not picks:
        print("  No projections available (check starters data)")
        return picks

    # All projections
    print(f"\n  All Projections ({len(picks)} pitchers):")
    print(f"  {'Pitcher':20} {'Team':4} {'vs':4} {'Proj':>5} {'FD':>5} {'Side':>6} {'Edge':>6} {'Odds':>6} {'K/9':>5} {'IP':>4}")
    print(f"  {'-'*68}")

    for p in picks:
        fd_line = f"{p.get('fd_line', '-'):5.1f}" if p.get('fd_line') else "  -  "
        side = p.get('side', '-') or '-'
        edge = f"{p.get('edge', 0)*100:+5.1f}%" if p.get('edge') else "   -  "
        odds = f"{p.get('odds', '-'):>6}" if p.get('odds') else "     -"
        print(f"  {p['pitcher']:20} {p['team']:4} {p['opponent']:4} "
              f"{p['projected_k']:5.1f} {fd_line} {side:>6} {edge} {odds} "
              f"{p['k9_recent']:5.1f} {p['avg_ip']:4.1f}")

    # Picks with edge
    edge_picks = [p for p in picks if p.get("side")]
    if edge_picks:
        print(f"\n  ACTIONABLE PICKS ({len(edge_picks)}):")
        print(f"  {'-'*68}")
        for p in edge_picks:
            print(f"  {p['side']:>5} {p['fd_line']:.1f} Ks - {p['pitcher']} ({p['team']} vs {p['opponent']})")
            print(f"        Projected: {p['projected_k']:.1f} K | Edge: {p['edge']*100:+.1f}% | Odds: {p['odds']}")
            print(f"        K/9 L5: {p['k9_recent']:.1f} | Avg IP: {p['avg_ip']:.1f} | Opp K rate: {p['opp_k_rate']:.1f}/9")
    else:
        print("\n  No props with sufficient edge (>3%) found")

    print(f"\n{'='*70}")
    return picks


def backtest():
    """
    Backtest strikeout projections against actual results.
    Uses only pitcher game log data (no historical FanDuel lines needed).
    Tests projection accuracy and whether Poisson model is calibrated.
    """
    print("Loading data for backtest...")
    pitcher_logs = load_pitcher_logs()
    team_k_games = load_team_k_rates()

    # Get all games with starters
    conn = sqlite3.connect(GL_DB, timeout=15)
    starters = conn.execute("""
        SELECT game_date, home_team, away_team,
               home_pitcher_id, home_pitcher_name,
               away_pitcher_id, away_pitcher_name
        FROM mlb_game_starters
        WHERE home_pitcher_id IS NOT NULL AND away_pitcher_id IS NOT NULL
        ORDER BY game_date
    """).fetchall()
    conn.close()

    print(f"Total games with both starters: {len(starters)}")

    # Project and compare
    results = []
    errors = []

    for s in starters:
        gd, ht, at, hp_id, hp_name, ap_id, ap_name = s

        for pid, pname, team, opp, is_home in [
            (hp_id, hp_name, ht, at, True),
            (ap_id, ap_name, at, ht, False),
        ]:
            if not pid or pid not in pitcher_logs:
                continue

            opp_k = team_k_games.get(opp, [])
            proj = compute_pitcher_projection(
                pitcher_logs[pid], gd, opp_k, ht
            )
            if proj is None:
                continue

            # Find actual result
            actual_games = [l for l in pitcher_logs[pid] if l["date"] == gd]
            if not actual_games:
                continue
            actual_k = actual_games[0]["k"]

            error = proj["projected_k"] - actual_k
            results.append({
                "date": gd,
                "pitcher": pname,
                "projected": proj["projected_k"],
                "actual": actual_k,
                "error": error,
                "abs_error": abs(error),
            })

    if not results:
        print("No results to analyze")
        return

    projected = [r["projected"] for r in results]
    actual = [r["actual"] for r in results]
    errors = [r["error"] for r in results]
    abs_errors = [r["abs_error"] for r in results]

    print(f"\n{'='*60}")
    print(f"  STRIKEOUT PROJECTION BACKTEST ({len(results)} pitcher starts)")
    print(f"{'='*60}")
    print(f"  Mean projected: {np.mean(projected):.2f}")
    print(f"  Mean actual:    {np.mean(actual):.2f}")
    print(f"  Mean error:     {np.mean(errors):+.2f} (bias)")
    print(f"  MAE:            {np.mean(abs_errors):.2f}")
    print(f"  RMSE:           {np.sqrt(np.mean([e**2 for e in errors])):.2f}")

    # Calibration: compare Poisson vs NegBin vs actual
    print(f"\n  Calibration (Poisson vs NegBin vs actual):")
    for line in [3.5, 4.5, 5.5, 6.5, 7.5]:
        poisson_pred = [poisson_over_prob(p, line) for p in projected]
        negbin_pred = [negbin_over_prob(p, line) for p in projected]
        actual_over = [1 if a > line else 0 for a in actual]
        p_avg = np.mean(poisson_pred)
        nb_avg = np.mean(negbin_pred)
        a_avg = np.mean(actual_over)
        print(f"    Line {line}: Poisson {p_avg:.3f} | NegBin {nb_avg:.3f} | Actual {a_avg:.3f} | P_err {a_avg-p_avg:+.3f} | NB_err {a_avg-nb_avg:+.3f}")

    # Simulated betting: if projection says OVER/UNDER, what's the ROI?
    print(f"\n  Simulated Betting (vs hypothetical -110/-110 lines):")
    for line in [4.5, 5.5, 6.5]:
        for min_edge in [0.03, 0.05, 0.07]:
            wins = 0
            losses = 0
            for r in results:
                p_over = poisson_over_prob(r["projected"], line)
                p_under = 1 - p_over
                fair = 0.5  # -110/-110 implies ~50/50

                if p_over - fair > min_edge:
                    # Bet over
                    if r["actual"] > line:
                        wins += 1
                    elif r["actual"] < line:
                        losses += 1
                elif p_under - fair > min_edge:
                    # Bet under
                    if r["actual"] < line:
                        wins += 1
                    elif r["actual"] > line:
                        losses += 1

            total = wins + losses
            if total > 0:
                wr = wins / total
                # At -110 odds, profit = wins * 100/110 - losses
                profit = wins * (100/110) - losses
                roi = profit / total * 100
                print(f"    Line {line}, Edge>{min_edge*100:.0f}%: {total:5d} bets, {wr:.1%} WR, {roi:+.1f}% ROI")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backtest":
        backtest()
    else:
        generate_today_picks()

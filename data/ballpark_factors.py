#!/usr/bin/env python3
"""
Ballpark Factors for MLB

Park factors affect run scoring, HR rates, K rates, etc.
Coors Field can inflate runs 20-30%, while Oracle Park suppresses them.

Source: ESPN/FanGraphs park factors (2024-2025 averages)
These are multipliers where 100 = neutral, >100 = hitter-friendly, <100 = pitcher-friendly.
"""

# Park factors (runs) - 2024-2025 averages
# Source: FanGraphs Guts! page
PARK_FACTORS = {
    # Team abbreviation: (runs_factor, hr_factor)
    # Runs factor: 100 = neutral. 110 = 10% more runs than average
    "COL": (115, 120),   # Coors Field - extreme hitter's park
    "BOS": (108, 105),   # Fenway Park - hitter-friendly
    "CIN": (107, 108),   # Great American - HR-friendly
    "TEX": (106, 108),   # Globe Life - still hitter-friendly with roof
    "ARI": (105, 106),   # Chase Field - dry air, ball carries
    "CHC": (104, 105),   # Wrigley - wind-dependent but generally hitter-friendly
    "PHI": (103, 105),   # Citizens Bank - hitter-friendly
    "TOR": (103, 104),   # Rogers Centre
    "BAL": (102, 106),   # Camden Yards - HR-friendly
    "ATL": (101, 103),   # Truist Park - slightly hitter-friendly
    "MIN": (101, 102),   # Target Field
    "DET": (100, 98),    # Comerica Park - neutral
    "WSH": (100, 100),   # Nationals Park - neutral
    "LAA": (100, 99),    # Angel Stadium - neutral
    "KC":  (99, 97),     # Kauffman Stadium - slightly pitcher-friendly
    "CWS": (99, 100),    # Guaranteed Rate - neutral
    "HOU": (99, 101),    # Minute Maid - with roof
    "STL": (98, 98),     # Busch Stadium - pitcher-friendly
    "MIL": (98, 99),     # American Family Field
    "NYY": (98, 104),    # Yankee Stadium - HR-friendly but not runs
    "PIT": (97, 95),     # PNC Park - pitcher-friendly
    "CLE": (97, 96),     # Progressive Field
    "TB":  (96, 94),     # Tropicana Field - pitcher-friendly
    "NYM": (96, 97),     # Citi Field - pitcher-friendly
    "SEA": (95, 94),     # T-Mobile Park - pitcher-friendly
    "MIA": (94, 93),     # LoanDepot Park - very pitcher-friendly
    "SD":  (94, 93),     # Petco Park - pitcher-friendly
    "LAD": (94, 95),     # Dodger Stadium - pitcher-friendly
    "SF":  (93, 90),     # Oracle Park - very pitcher-friendly
    "OAK": (96, 95),     # Oakland Coliseum - pitcher-friendly
}


def get_park_factor(team_abbr: str, factor_type: str = "runs") -> float:
    """Get park factor for a team's home stadium.

    Args:
        team_abbr: Team abbreviation (e.g., 'COL', 'SF')
        factor_type: 'runs' or 'hr'

    Returns:
        Park factor as a multiplier (e.g., 1.15 for Coors runs)
    """
    factors = PARK_FACTORS.get(team_abbr, (100, 100))
    idx = 0 if factor_type == "runs" else 1
    return factors[idx] / 100.0


def adjust_total_for_park(predicted_total: float, home_team: str) -> float:
    """Adjust a predicted game total for ballpark effects.

    Args:
        predicted_total: Model's raw predicted total runs
        home_team: Home team abbreviation

    Returns:
        Park-adjusted total
    """
    factor = get_park_factor(home_team, "runs")
    # Apply half the park effect (model may already partially capture it via historical data)
    adjustment = (factor - 1.0) * 0.5
    return predicted_total * (1.0 + adjustment)


if __name__ == "__main__":
    print("Ballpark Factors (Runs)")
    print("=" * 50)
    # Sort by factor
    sorted_parks = sorted(PARK_FACTORS.items(), key=lambda x: x[1][0], reverse=True)
    for team, (runs, hr) in sorted_parks:
        bar = "+" * max(0, runs - 100) + "-" * max(0, 100 - runs)
        print(f"  {team}: runs={runs:3d}  hr={hr:3d}  {bar}")

    # Example adjustment
    print(f"\nExample: 8.5 total at Coors = {adjust_total_for_park(8.5, 'COL'):.1f} adjusted")
    print(f"Example: 8.5 total at Oracle = {adjust_total_for_park(8.5, 'SF'):.1f} adjusted")

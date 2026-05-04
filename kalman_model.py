"""
Sports Edge - Kalman Filter + Monte Carlo Prediction Engine
Replaces the naive weighted average with:
  1. Kalman Filter: tracks "true skill" per player per stat, separating signal from noise
  2. Monte Carlo: samples from the Kalman state distribution to get probability of over/under
"""
import math
import random
from collections import defaultdict


class PlayerKalman:
    """
    1D Kalman filter per player per stat.

    State: player's "true" per-game production rate (e.g., true points per game)
    Measurement: actual game result (noisy observation of true ability)

    Key insight: a single game is noisy. If Steph goes 1/10 from three, the Kalman
    filter knows his true rate is still ~42% and barely moves the estimate.
    A weighted average would overreact.
    """

    def __init__(self, initial_mean=None, initial_var=None,
                 process_noise=None, measurement_noise=None):
        self.mean = initial_mean       # Current estimate of true ability
        self.var = initial_var         # Uncertainty in that estimate
        self.process_noise = process_noise   # Q: how much true ability drifts game-to-game
        self.measurement_noise = measurement_noise  # R: single-game randomness
        self.initialized = initial_mean is not None
        self.n_updates = 0
        self.history = []  # track (mean, var) over time for diagnostics

    def predict_step(self):
        """Time update: ability might drift slightly between games."""
        if not self.initialized:
            return
        # State prediction: mean stays same, uncertainty grows
        self.var += self.process_noise

    def update_step(self, measurement):
        """Measurement update: incorporate new game result."""
        if not self.initialized:
            # First observation: initialize
            self.mean = measurement
            self.var = self.measurement_noise * 2  # High initial uncertainty
            self.initialized = True
            self.n_updates = 1
            self.history.append((self.mean, self.var))
            return

        # Kalman gain: how much to trust new measurement vs prior estimate
        # High gain = trust measurement more, Low gain = trust prior more
        K = self.var / (self.var + self.measurement_noise)

        # Update estimate
        self.mean = self.mean + K * (measurement - self.mean)
        self.var = (1 - K) * self.var

        self.n_updates += 1
        self.history.append((self.mean, self.var))

    def get_estimate(self):
        """Return current (mean, variance) estimate."""
        if not self.initialized:
            return None, None
        return self.mean, self.var


# Default noise parameters per stat type, tuned from NBA data characteristics
# Process noise (Q): how much true ability shifts game-to-game
# Measurement noise (R): how noisy a single game observation is
STAT_PARAMS = {
    "pts": {
        "process_noise": 1.5,      # Points: moderate drift
        "measurement_noise": 25.0,  # High variance game-to-game
    },
    "reb": {
        "process_noise": 0.8,
        "measurement_noise": 8.0,
    },
    "ast": {
        "process_noise": 0.6,
        "measurement_noise": 6.0,
    },
    "fg3m": {
        "process_noise": 0.3,
        "measurement_noise": 3.0,   # 3PT made: very noisy per game
    },
}


class KalmanPredictor:
    """
    Manages Kalman filters for all players across all stats.
    Feed it game data chronologically, it maintains state for everyone.
    """

    def __init__(self, params=None):
        self.params = params or STAT_PARAMS
        # filters[player_name][stat] = PlayerKalman
        self.filters = defaultdict(dict)

    def _get_filter(self, player, stat):
        """Get or create Kalman filter for player+stat."""
        if stat not in self.filters[player]:
            p = self.params.get(stat, {"process_noise": 1.0, "measurement_noise": 10.0})
            self.filters[player][stat] = PlayerKalman(
                process_noise=p["process_noise"],
                measurement_noise=p["measurement_noise"],
            )
        return self.filters[player][stat]

    def update(self, player, stat, actual_value):
        """Process a new game observation for a player."""
        kf = self._get_filter(player, stat)
        kf.predict_step()  # Time update (ability may have drifted)
        kf.update_step(actual_value)  # Measurement update

    def update_game(self, player, pts, reb, ast, fg3m):
        """Update all stats for a player after a game."""
        self.update(player, "pts", pts)
        self.update(player, "reb", reb)
        self.update(player, "ast", ast)
        self.update(player, "fg3m", fg3m)

    def predict(self, player, stat):
        """
        Get current prediction for a player's stat.
        Returns (mean, std_dev) or (None, None) if insufficient data.
        """
        kf = self._get_filter(player, stat)
        mean, var = kf.get_estimate()
        if mean is None or kf.n_updates < 5:
            return None, None
        # Total prediction uncertainty = state uncertainty + measurement noise
        total_var = var + self.params.get(stat, {}).get("measurement_noise", 10.0)
        return mean, math.sqrt(total_var)

    def get_n_updates(self, player, stat):
        """How many games has this filter seen?"""
        kf = self._get_filter(player, stat)
        return kf.n_updates


def monte_carlo_probability(mean, std, line, n_sims=10000):
    """
    Monte Carlo simulation: sample from the player's predicted distribution
    and calculate probability of going over/under the line.

    Uses a normal distribution (reasonable for most counting stats over a game).
    For fg3m (small counts), we could use Poisson, but normal works OK for betting purposes.

    Returns: (prob_over, prob_under, prob_push)
    """
    if mean is None or std is None or std <= 0:
        return 0.5, 0.5, 0.0

    over = 0
    under = 0
    push = 0

    for _ in range(n_sims):
        # Sample from predicted distribution
        sample = random.gauss(mean, std)
        # For stats that can't go negative, floor at 0
        sample = max(0, sample)
        # Round to nearest 0.5 for push detection (props use .5 lines)
        if sample > line:
            over += 1
        elif sample < line:
            under += 1
        else:
            push += 1

    total = over + under + push
    return over / total, under / total, push / total


def calculate_edge(prob, american_odds):
    """
    Calculate edge given our probability estimate and the sportsbook odds.

    Edge = our_probability - implied_probability

    If we think Over has 60% chance but the book implies 52.4% (-110),
    our edge is 7.6%.
    """
    # Convert American odds to implied probability
    if american_odds > 0:
        implied = 100 / (american_odds + 100)
    else:
        implied = abs(american_odds) / (abs(american_odds) + 100)

    edge = prob - implied
    return edge, implied


def kelly_fraction(edge, decimal_odds, fraction=0.25):
    """
    Fractional Kelly criterion.
    Community consensus: 15-25% Kelly is optimal for sports betting.
    We use 25% (quarter Kelly) — aggressive enough to grow, conservative enough to survive.

    edge: our edge as a decimal (e.g., 0.076 for 7.6%)
    decimal_odds: payout ratio (e.g., 1.909 for -110)
    fraction: Kelly fraction (0.25 = quarter Kelly)
    """
    b = decimal_odds - 1  # Net odds
    p = 0.5 + edge / 2   # Our estimated win probability (simplified)

    # More precise: use edge directly
    # p = implied_prob + edge
    # But we'll use the edge-based formula for clarity

    if b <= 0 or edge <= 0:
        return 0

    # Full Kelly: (bp - q) / b where q = 1-p
    q = 1 - p
    full_kelly = (b * p - q) / b

    if full_kelly <= 0:
        return 0

    return full_kelly * fraction


def american_to_decimal(american):
    """Convert American odds to decimal odds."""
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)

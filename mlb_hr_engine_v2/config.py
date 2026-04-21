import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")

# ── Bankroll ──────────────────────────────────────────────────────────────────
BANKROLL: float = float(os.getenv("BANKROLL", "1000"))

# ── Date Override ─────────────────────────────────────────────────────────────
TARGET_DATE: str | None = os.getenv("TARGET_DATE")   # None = use today

# ── Bet Sizing ────────────────────────────────────────────────────────────────
KELLY_FRACTION: float = 0.25   # Quarter-Kelly for real-world sizing
MAX_BET_PCT: float = 0.05      # Hard cap at 5% of bankroll per bet
MIN_BET_DOLLARS: float = 5.0

# ── Filter Thresholds ─────────────────────────────────────────────────────────
MIN_EV_PCT: float = 5.0
MIN_EDGE_PCT: float = 3.0
MIN_PA_THRESHOLD: float = 3.5
MAX_PARK_PENALTY: float = 0.85     # Skip if park_factor < this
MAX_WEATHER_PENALTY: float = 0.88  # Skip if weather_factor < this
MAX_PITCHER_SUPPRESSOR: float = 0.75  # Skip elite HR suppressors

# ── Probability Model ─────────────────────────────────────────────────────────
RECENT_DAYS: int = 30
RECENT_WEIGHT: float = 0.65
SEASON_WEIGHT: float = 0.35
LEAGUE_AVG_HR_PA: float = 0.033    # ~1 HR per 30 PA league-wide
REGRESSION_PA: int = 200            # Bayes regression towards league mean
MIN_RECENT_PA: int = 30             # Need ≥30 recent PA to trust recent rate

# League-average HR/9 for pitchers (2024 MLB)
LEAGUE_AVG_HR9: float = 1.35

CURRENT_SEASON: int = 2026

# ── Expected PA by Lineup Spot ────────────────────────────────────────────────
# Based on average 38-39 team PA per 9 innings
LINEUP_PA: dict[int, float] = {
    1: 4.5, 2: 4.3, 3: 4.2, 4: 4.1, 5: 3.9,
    6: 3.7, 7: 3.6, 8: 3.4, 9: 3.2,
}
DEFAULT_PA: float = 3.8  # fallback when lineup spot unknown

# ── Parlay Settings ───────────────────────────────────────────────────────────
PARLAY_MIN_LEGS: int = 2
PARLAY_MAX_LEGS: int = 3
PARLAY_CANDIDATE_POOL: int = 8   # Top N picks to consider for parlay

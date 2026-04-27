import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def _secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets (cloud) or .env / env vars (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

# ── API Keys ──────────────────────────────────────────────────────────────────
ODDS_API_KEY: str = _secret("ODDS_API_KEY")

# ── Bankroll ──────────────────────────────────────────────────────────────────
BANKROLL: float = float(_secret("BANKROLL", "100"))

# ── Date Override ─────────────────────────────────────────────────────────────
TARGET_DATE: Optional[str] = os.getenv("TARGET_DATE")   # None = use today

# ── Bet Sizing ────────────────────────────────────────────────────────────────
KELLY_FRACTION: float = 0.25   # Quarter-Kelly for real-world sizing
MAX_BET_PCT: float = 0.05      # Hard cap at 5% of bankroll per bet
MIN_BET_DOLLARS: float = 5.0

# ── Filter Thresholds ─────────────────────────────────────────────────────────
MIN_EV_PCT: float = 3.0    # Bread-and-butter floor; anything below is noise
MIN_EDGE_PCT: float = 2.0  # Minimum model-vs-market edge to surface a play
MIN_PA_THRESHOLD: float = 3.1
MAX_PARK_PENALTY: float = 0.85     # Skip if park_factor < this
MAX_WEATHER_PENALTY: float = 0.88  # Skip if weather_factor < this
MAX_PITCHER_SUPPRESSOR: float = 0.75  # Skip elite HR suppressors

# ── Probability Model ─────────────────────────────────────────────────────────
# Game-count windows are more consistent than calendar days — unaffected by
# off-days, travel, or early-season sparseness.
RECENT_GAMES: int = 20        # last N games for recent batter rate
SHORT_FORM_GAMES: int = 10    # last N games for hot/cold streak detection
PITCHER_RECENT_GAMES: int = 5 # last N starts for pitcher recent form

# HR/PA stabilizes slowly (~300+ PA needed); 0.30 recent weight balances
# early-season noise vs capturing genuine rate changes.
RECENT_WEIGHT: float = 0.30
SEASON_WEIGHT: float = 0.70
LEAGUE_AVG_HR_PA: float = 0.033    # ~1 HR per 30 PA league-wide
REGRESSION_PA: int = 200            # Bayes regression towards league mean
MIN_RECENT_PA: int = 20             # Need ≥20 recent PA to trust recent rate

# League-average HR/9 for pitchers (2025 MLB; FOX Sports qualified starters median ~1.2-1.3)
LEAGUE_AVG_HR9: float = 1.25
LEAGUE_AVG_ISO: float = 0.148   # ISO = SLG - AVG; 2025 MLB (FanGraphs wOBA=.313)
LEAGUE_HR_FB:   float = 0.120   # HR per fly ball (2025 MLB, slight decrease from 2024)

# ── Market / EV ───────────────────────────────────────────────────────────────
VIG_FACTOR: float = 0.075  # Empirically measured on FanDuel/DraftKings HR props

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

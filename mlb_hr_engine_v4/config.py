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
assert BANKROLL > 0, f"BANKROLL must be > 0 (got {BANKROLL}). Check your .env or Streamlit secrets."

# ── Date Override ─────────────────────────────────────────────────────────────
TARGET_DATE: Optional[str] = os.getenv("TARGET_DATE")   # None = use today

# ── Bet Sizing ────────────────────────────────────────────────────────────────
KELLY_FRACTION: float = 0.25   # Quarter-Kelly for real-world sizing
MAX_BET_PCT: float = 0.05      # Hard cap at 5% of bankroll per bet
MIN_BET_DOLLARS: float = 5.0

# ── Filter Thresholds ─────────────────────────────────────────────────────────
MIN_EV_PCT: float = 3.0    # Bread-and-butter floor; anything below is noise
MIN_EDGE_PCT: float = 2.0  # Minimum model-vs-market edge to surface a play
MIN_PA_THRESHOLD: float = 3.3      # Blocks 9-hole batters (3.2 PA); 3.1 was dead (never fired)
MAX_PARK_PENALTY: float = 0.87     # Skip if park_factor < this; catches SF (0.83) + SD (0.89)
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
assert abs(RECENT_WEIGHT + SEASON_WEIGHT - 1.0) < 0.001, \
    f"RECENT_WEIGHT + SEASON_WEIGHT must equal 1.0 (got {RECENT_WEIGHT + SEASON_WEIGHT})"
LEAGUE_AVG_HR_PA: float = 0.030    # 2026 MLB May-6: broader Apr sample=0.028; qualified-only May=0.032 (biased); 0.030 splits
REGRESSION_PA: int = 200            # Bayes regression towards league mean
MIN_RECENT_PA: int = 20             # Need ≥20 recent PA to trust recent rate

# League-average HR/9 for pitchers (2026 MLB May-6; qualified starters=0.957; +relievers push higher)
LEAGUE_AVG_HR9: float = 1.05          # 2026 MLB May-6
LEAGUE_AVG_ISO: float = 0.157         # ISO = SLG - AVG; 2026 MLB May-6 (qualified bias adj from 0.164)
LEAGUE_HR_FB:   float = 0.097         # HR per fly ball; 2026 MLB May-6 (was 0.106)
# All Statcast leaderboard league averages live here — single source for mid-season refresh.
# NOTE: Savant fb_rate is pure fly balls (excludes popups). FanGraphs FB% (~34%) combines fb+pu.
# LEAGUE_AVG_FB_PCT must match Savant's definition since it's compared against the CSV fb_rate column.
LEAGUE_AVG_BARREL_RATE: float = 0.055 # barrel per PA (brl_pa); 2026 May-6 (unchanged: 0.0552)
LEAGUE_AVG_FB_PCT:      float = 0.264 # Savant pure fly ball rate (excludes popups); 2026 May-6
LEAGUE_AVG_EXIT_VELO:   float = 89.1  # mph average exit velocity; 2026 May-6
LEAGUE_AVG_HARD_HIT:    float = 0.399 # EV >95 mph rate; 2026 May-6
LEAGUE_AVG_XSLG:        float = 0.418 # expected SLG (est_slg); 2026 May-6 (was 0.407)
LEAGUE_AVG_SWEET_SPOT:  float = 0.334 # LA 8-32° sweet spot rate; 2026 May-6
LEAGUE_AVG_PULL_PCT:    float = 0.392 # pull rate; 2026 May-6
LEAGUE_AVG_GB_PCT:      float = 0.428 # ground ball rate; 2026 May-6
LEAGUE_AVG_LD_PCT:      float = 0.235 # line drive rate; 2026 May-6
LEAGUE_AVG_IFFB_PCT:    float = 0.073 # infield fly ball (popup) rate; 2026 May-6 (unchanged)
LEAGUE_AVG_STR_PCT:     float = 0.368 # straightaway/center rate; 2026 May-6 (unchanged)
LEAGUE_AVG_OPPO_PCT:    float = 0.240 # opposite field rate; 2026 May-6 (unchanged)

# ── Probability model ceiling ─────────────────────────────────────────────────
# Full-season 2025 backtest: actual HR rate in 30%+ bucket = 28.9%; ceiling aligns with observed reality.
MAX_GAME_HR_PROB: float = 0.29

# ── Statcast blending ─────────────────────────────────────────────────────────
PRIOR_YEAR_TRUST:    float = 0.85  # shrink prior-year-only signal deviation from 1.0
MIN_CURRENT_YEAR_PA: int   = 50    # below this, blend current + prior Statcast (50 BF to stabilize)

# ── Market / EV ───────────────────────────────────────────────────────────────
VIG_FACTOR: float = 0.075          # Fallback vig for unknown books; global default
DYNAMIC_VIG_ENABLED: bool = True   # Use per-book vig model (engine/vig.py)
DYNAMIC_VIG_ODDS_RANGE: bool = True  # Scale vig by implied probability (longer shots → higher vig)

_today = __import__("datetime").date.today()
# Jan–Feb: season hasn't started, use prior year; Mar–Dec: use current year
CURRENT_SEASON: int = _today.year if _today.month >= 3 else _today.year - 1
del _today

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

# ── Backtest simulation ───────────────────────────────────────────────────────
BACKTEST_FLAT_BET: float = 10.0  # dollars per pick in calibration P&L simulation

# ── Metric Stabilization Half-Lives ──────────────────────────────────────────
# PA count where each Statcast metric is ~50% reliable (n/(n+half_life)=0.5).
# Applied in statcast.py to shrink low-sample signals toward league average.
STATCAST_STABILIZATION_PA: dict = {
    "barrel_rate":       60,   # fastest-stabilizing batted-ball metric
    "exit_velocity_avg": 50,   # EV stabilizes very quickly (~50 PA)
    "hard_hit_pct":      80,
    "sweet_spot_pct":   120,
    "xslg":              60,
    "fb_pct":           150,   # batted-ball direction metrics stabilize slower
    "pull_pct":         100,
}

# ── Pitch Arsenal ─────────────────────────────────────────────────────────────
ARSENAL_LEAGUE_AVG_WHIFF: float = 0.245  # ~24.5% league-average whiff rate 2026
ARSENAL_RV_SCALE:         float = 40.0   # RV/100 ±2.0 → ±5% factor via division

# ── Velocity Decline ──────────────────────────────────────────────────────────
VELO_DECLINE_THRESHOLD_MPH: float = 0.5   # minimum YoY drop to apply factor
VELO_DECLINE_RATE:          float = 0.012 # HR factor boost per mph beyond threshold

# ── Humidity ──────────────────────────────────────────────────────────────────
LEAGUE_AVG_HUMIDITY: float = 55.0  # % RH baseline for neutral factor

# ── FB% Signal Configuration ─────────────────────────────────────────────────
# Controls FB% behavior in batter_power_multiplier (statcast.py).
# Companion fixed weights sum to 0.80 (barrel+sweet+pull+xslg+hh+ev),
# so FB_PCT_WEIGHT should equal 0.20 for a normalized composite.
# Re-run analyze_fb_pct.py after changes to validate calibration impact.
FB_PCT_WEIGHT:            float = 0.20  # batter_power_multiplier weight (was 0.15)
FB_QUALITY_GATE_ENABLED:  bool  = True  # guard FB% upside against low barrel quality
FB_QUALITY_GATE_FLOOR:    float = 0.50  # gate min (0=fully conditional, 1=disabled)
FB_PARK_SCALE:            float = 0.30  # FB% deviation scaling in fly_ball_adjusted_park_factor

# ── Probability Calibration ───────────────────────────────────────────────────
# Post-model monotone transform: maps raw model_prob → calibrated_prob.
# All methods preserve rank order. Parameters are fitted by analyze_calibration.py.
# Set CALIBRATION_ENABLED=True only after validating parameters via that script.
#
# Method "platt": sigmoid(CALIBRATION_PLATT_A × logit(p) + CALIBRATION_PLATT_B)
#   A=1.0, B=0.0 → identity. A<1.0 compresses, B<0 shifts down.
#   Crossover (where calibrated==raw): p* = sigmoid(B / (1−A)).
#   Below p*: predictions increase. Above p*: predictions decrease.
#
# Method "isotonic": piecewise monotone linear from fitted breakpoints.
#   More flexible than Platt but requires more data to fit without overfitting.
#
# Re-run analyze_calibration.py whenever the signal stack changes significantly.
# Fitted 2026-05-16 via analyze_calibration.py on 10,777 batter-games (Apr 1–May 15):
#   CV test Brier=0.09104 (baseline=0.09207), crossover=10.9%.
#   Below 10.9% model_prob: predictions increase (fixes 5-10% under-prediction).
#   Above 10.9% model_prob: predictions decrease (fixes 15-25% over-prediction).
#   Spearman ρ=0.999999 vs baseline — ranking unchanged.
#   Known trade-off: 20-25% bucket shows +2.4pp (extreme-top batters compressed into this
#   bucket genuinely HR at ~24%, so the method slightly under-corrects the very top end).
#   Rollback: set CALIBRATION_ENABLED=False.
#   Re-calibrate: run analyze_calibration.py after any signal stack change.
CALIBRATION_ENABLED: bool  = True         # activated — validated 2026-05-16
CALIBRATION_METHOD:  str   = "platt"      # "platt" | "isotonic" | "none"
CALIBRATION_PLATT_A: float = 0.7805       # slope — Platt CV-fitted
CALIBRATION_PLATT_B: float = -0.4611      # intercept — Platt CV-fitted
CALIBRATION_ISOTONIC_BREAKPOINTS: list = []  # raw prob breakpoints (fitted)
CALIBRATION_ISOTONIC_VALUES:      list = []  # calibrated prob at each breakpoint

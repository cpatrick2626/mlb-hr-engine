"""
HR Probability Engine — Poisson model with Bayesian regression.

Core model:
  1. Compute weighted HR/PA rate (recent + season, regressed to mean)
  2. Estimate expected PAs from lineup spot
  3. Apply multiplicative adjustments: park × pitcher × weather × handedness
  4. P(HR ≥ 1) = 1 − e^(−λ),  λ = adjusted_rate × expected_PA
"""

import math
from typing import Optional

import config
from data.park_factors import get_park
from clients import weather as weather_client


# ── Base HR Rate ──────────────────────────────────────────────────────────────

def base_hr_rate(season_stats: dict, recent_stats: dict) -> float:
    """
    Compute weighted, regressed HR/PA rate.

    Season stats regressed toward league mean via a Beta-Binomial prior.
    Then blended with recent form when sample size allows.
    """
    season_pa = int(season_stats.get("plateAppearances", 0))
    season_hr = int(season_stats.get("homeRuns", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    recent_hr = int(recent_stats.get("homeRuns", 0))

    # Regressed season rate (Bayesian shrinkage toward league mean)
    regressed_season = (
        (season_hr + config.REGRESSION_PA * config.LEAGUE_AVG_HR_PA)
        / (season_pa + config.REGRESSION_PA)
    ) if season_pa > 0 else config.LEAGUE_AVG_HR_PA

    # Recent rate (only trusted if enough PAs)
    if recent_pa >= config.MIN_RECENT_PA:
        recent_rate = recent_hr / recent_pa
        # Down-weight recent rate toward regressed season as sample shrinks
        recent_trust = min(recent_pa / 100.0, 1.0)
        blended_recent = recent_rate * recent_trust + regressed_season * (1 - recent_trust)
        rate = config.RECENT_WEIGHT * blended_recent + config.SEASON_WEIGHT * regressed_season
    else:
        rate = regressed_season

    return max(rate, 0.001)


# ── Expected PA ───────────────────────────────────────────────────────────────

def expected_pa(lineup_spot: Optional[int]) -> float:
    if lineup_spot and 1 <= lineup_spot <= 9:
        return config.LINEUP_PA[lineup_spot]
    return config.DEFAULT_PA


# ── Pitcher Adjustment ────────────────────────────────────────────────────────

def pitcher_hr_factor(pitcher_stats: dict) -> float:
    """
    Compare pitcher's HR/9 to league average.
    factor = league_avg / pitcher_hr9  (< 1 = HR suppressor, > 1 = homer-prone)

    Bounded to [0.65, 1.50] to prevent extreme values on small samples.
    """
    innings_str = pitcher_stats.get("inningsPitched", "0.0")
    try:
        # MLB API returns "73.1" meaning 73 and 1/3 innings
        parts = str(innings_str).split(".")
        ip = int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(innings_str)
    except (ValueError, IndexError):
        ip = 0.0

    hrs_allowed = int(pitcher_stats.get("homeRuns", 0))

    if ip < 5:
        return 1.0  # Too few innings — no adjustment

    hr9 = (hrs_allowed / ip) * 9.0

    # Regress pitcher HR/9 toward league mean proportional to IP
    regression_ip = 50  # Stabilizes around 50 IP
    regressed_hr9 = (
        (hr9 * ip + config.LEAGUE_AVG_HR9 * regression_ip)
        / (ip + regression_ip)
    )

    if regressed_hr9 == 0:
        return 1.50  # Extreme outlier — cap boost

    factor = config.LEAGUE_AVG_HR9 / regressed_hr9
    return max(0.65, min(1.50, factor))


# ── Park Adjustment ───────────────────────────────────────────────────────────

def park_factor(home_team: str, batter_is_home: bool) -> float:
    """
    Home team plays entirely in their park.
    Away team also plays in that park, so both get the full factor.
    """
    return get_park(home_team).get("hr_factor", 1.0)


# ── Weather Adjustment ────────────────────────────────────────────────────────

def weather_factor(home_team: str) -> tuple[float, dict]:
    """Fetch live weather and compute HR adjustment."""
    park = get_park(home_team)
    is_dome = home_team in weather_client.DOME_TEAMS

    weather = weather_client.get_game_weather(park["lat"], park["lon"])
    t_factor = weather_client.temp_factor(weather["temp_f"])
    w_factor = weather_client.wind_factor(
        weather["wind_mph"], weather["wind_deg"], is_dome
    )

    combined = t_factor * w_factor
    # Clip: weather shouldn't swing model more than ±20%
    combined = max(0.80, min(1.20, combined))
    return combined, weather


# ── Handedness Splits ─────────────────────────────────────────────────────────

def handedness_factor(batter_side: str, pitcher_hand: str) -> float:
    """
    Platoon advantage: batters hit for more power vs opposite-hand pitchers.
    Rough multipliers derived from Statcast 2022-2024 HR splits.
    """
    if not batter_side or not pitcher_hand:
        return 1.0

    bats = batter_side[0].upper()  # L or R
    throws = pitcher_hand[0].upper()

    # Opposite-hand matchup = slight HR boost
    if bats != throws:
        return 1.06
    # Same-hand matchup = slight suppression
    return 0.96


# ── Game HR Probability ───────────────────────────────────────────────────────

def game_hr_probability(
    hr_rate: float,
    exp_pa: float,
    p_factor: float = 1.0,
    pk_factor: float = 1.0,
    w_factor: float = 1.0,
    h_factor: float = 1.0,
) -> float:
    """
    Poisson probability of hitting at least 1 HR in a game.

    λ = adjusted_hr_rate × expected_PA
    P(X ≥ 1) = 1 − e^(−λ)
    """
    adjusted_rate = hr_rate * p_factor * pk_factor * w_factor * h_factor
    lam = adjusted_rate * exp_pa
    prob = 1.0 - math.exp(-lam)
    return max(0.001, min(0.999, prob))


# ── Confidence Score ──────────────────────────────────────────────────────────

def confidence_score(
    season_pa: int,
    recent_pa: int,
    model_prob: float,
    market_prob: float,
) -> float:
    """
    0–100 score capturing how much we should trust the edge.

    Components:
      - Sample size (up to 40 pts): more PA = more confident in true rate
      - Recent form quality (up to 25 pts): more recent PA = less noise
      - Edge magnitude vs uncertainty (up to 35 pts): edge / expected_error
    """
    sample_conf = min(season_pa / 400.0, 1.0) * 40.0

    recent_conf = min(recent_pa / 80.0, 1.0) * 25.0

    edge = abs(model_prob - market_prob)
    # Expected noise in our estimate given sample size
    se = math.sqrt(model_prob * (1 - model_prob) / max(season_pa, 1))
    snr = min(edge / (se + 0.01), 3.0) / 3.0  # signal-to-noise ratio
    edge_conf = snr * 35.0

    return round(sample_conf + recent_conf + edge_conf, 1)

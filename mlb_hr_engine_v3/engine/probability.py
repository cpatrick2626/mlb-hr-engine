"""
HR Probability Engine v2 — enhanced Poisson model.

v2 additions vs v1:
  1. Statcast power multiplier (barrel%, exit velocity)
  2. HR/FB pitcher factor — better than raw HR/9
  3. Actual platoon splits from MLB Stats API
  4. Statcast pitcher contact quality (barrel% against, EV against)
"""

import math
from typing import Optional

import config
from data.park_factors import get_park
from clients import weather as weather_client


def base_hr_rate(season_stats: dict, recent_stats: dict) -> float:
    season_pa = int(season_stats.get("plateAppearances", 0))
    season_hr = int(season_stats.get("homeRuns", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    recent_hr = int(recent_stats.get("homeRuns", 0))

    regressed_season = (
        (season_hr + config.REGRESSION_PA * config.LEAGUE_AVG_HR_PA)
        / (season_pa + config.REGRESSION_PA)
    ) if season_pa > 0 else config.LEAGUE_AVG_HR_PA

    if recent_pa >= config.MIN_RECENT_PA:
        recent_rate = recent_hr / recent_pa
        recent_trust = min(recent_pa / 100.0, 1.0)
        blended_recent = recent_rate * recent_trust + regressed_season * (1 - recent_trust)
        rate = config.RECENT_WEIGHT * blended_recent + config.SEASON_WEIGHT * regressed_season
    else:
        rate = regressed_season

    return max(rate, 0.001)


def statcast_blended_rate(raw_rate: float, statcast_power_mult: float, season_pa: int) -> float:
    """
    Blend raw HR/PA with Statcast power adjustment.
    When sample is small (early season), weight Statcast more — it stabilizes in ~50 PA.
    """
    statcast_weight = max(0.20, 1.0 - (season_pa / 400.0))
    raw_weight = 1.0 - statcast_weight
    statcast_rate = raw_rate * statcast_power_mult
    return max(raw_weight * raw_rate + statcast_weight * statcast_rate, 0.001)


def pitcher_hr_factor(pitcher_stats: dict) -> float:
    """
    v2: HR/FB composite (blends HR/9 with HR per fly ball).
    HR/FB separates fly ball rate from HR conversion rate — more predictive.
    MLB Stats API: homeRuns + airOuts => fly balls faced.
    """
    innings_str = pitcher_stats.get("inningsPitched", "0.0")
    try:
        parts = str(innings_str).split(".")
        ip = int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(innings_str)
    except Exception:
        ip = 0.0

    hrs = int(pitcher_stats.get("homeRuns", 0))
    air_outs = int(pitcher_stats.get("airOuts", 0))

    if ip < 5:
        return 1.0

    # HR/9 component (regressed)
    hr9 = (hrs / ip) * 9.0
    reg_ip = 50
    reg_hr9 = (hr9 * ip + config.LEAGUE_AVG_HR9 * reg_ip) / (ip + reg_ip)
    hr9_factor = config.LEAGUE_AVG_HR9 / max(reg_hr9, 0.1)

    # HR/FB component
    fly_balls = hrs + air_outs
    LEAGUE_HR_FB = 0.125
    if fly_balls > 20:
        hr_fb = hrs / fly_balls
        reg_fb = 100
        reg_hr_fb = (hr_fb * fly_balls + LEAGUE_HR_FB * reg_fb) / (fly_balls + reg_fb)
        hr_fb_factor = reg_hr_fb / LEAGUE_HR_FB
        fb_trust = min(fly_balls / 200.0, 1.0)
        combined = (1.0 - fb_trust) * hr9_factor + fb_trust * hr_fb_factor
    else:
        combined = hr9_factor

    return max(0.65, min(1.50, combined))


def pitcher_combined_factor(pitcher_hr_fac: float, statcast_contact_fac: float) -> float:
    """Blend HR/FB factor with Statcast contact quality (barrel% against, EV against)."""
    combined = pitcher_hr_fac * 0.55 + statcast_contact_fac * 0.45
    return max(0.60, min(1.55, combined))


def platoon_factor(splits: dict, pitcher_hand: str, batter_side: str, season_pa: int) -> float:
    """
    v2: Real L/R splits from MLB Stats API.
    splits keys: "vl" = vs LHP rate, "vr" = vs RHP rate.
    Regresses toward overall average based on split PA sample size.
    """
    if not pitcher_hand or not batter_side:
        return 1.0

    split_key = "vl" if pitcher_hand.upper().startswith("L") else "vr"
    split_rate = splits.get(split_key)
    vl = splits.get("vl", 0)
    vr = splits.get("vr", 0)

    if not split_rate or (vl + vr) == 0:
        # Fallback to v1 heuristic
        b, p = batter_side[0].upper(), pitcher_hand[0].upper()
        if b == "S":
            return 1.03
        return 1.06 if b != p else 0.96

    total_rate = (vl + vr) / 2.0
    split_pa_proxy = season_pa * 0.4
    reg_n = 200
    regressed = (split_rate * split_pa_proxy + total_rate * reg_n) / (split_pa_proxy + reg_n)
    factor = regressed / total_rate if total_rate > 0 else 1.0
    return max(0.70, min(1.50, factor))


def expected_pa(lineup_spot: Optional[int]) -> float:
    if lineup_spot and 1 <= lineup_spot <= 9:
        return config.LINEUP_PA[lineup_spot]
    return config.DEFAULT_PA


def park_factor(home_team: str, batter_is_home: bool) -> float:
    return get_park(home_team).get("hr_factor", 1.0)


def weather_factor(home_team: str) -> tuple[float, dict]:
    park = get_park(home_team)
    is_dome = home_team in weather_client.DOME_TEAMS
    weather = weather_client.get_game_weather(park["lat"], park["lon"])
    t_factor = weather_client.temp_factor(weather["temp_f"])
    w_factor = weather_client.wind_factor(weather["wind_mph"], weather["wind_deg"], is_dome)
    return max(0.80, min(1.20, t_factor * w_factor)), weather


def game_hr_probability(
    hr_rate: float, exp_pa: float,
    pk_factor: float = 1.0, pitcher_fac: float = 1.0,
    w_factor: float = 1.0, plat_factor: float = 1.0,
) -> float:
    adjusted = hr_rate * pk_factor * pitcher_fac * w_factor * plat_factor
    lam = adjusted * exp_pa
    return max(0.001, min(0.999, 1.0 - math.exp(-lam)))


def confidence_score(
    season_pa: int, recent_pa: int,
    model_prob: float, market_prob: float,
    has_statcast: bool = False,
) -> float:
    """v2: +8 pts when Statcast data improves estimate reliability."""
    sample_conf   = min(season_pa / 400.0, 1.0) * 35.0
    recent_conf   = min(recent_pa / 80.0,  1.0) * 20.0
    statcast_bonus = 8.0 if has_statcast else 0.0
    edge = abs(model_prob - market_prob)
    se = math.sqrt(model_prob * (1 - model_prob) / max(season_pa, 1))
    snr = min(edge / (se + 0.01), 3.0) / 3.0
    edge_conf = snr * 30.0
    return round(min(sample_conf + recent_conf + edge_conf + statcast_bonus, 100.0), 1)

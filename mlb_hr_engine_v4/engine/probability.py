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

    # Adaptive regression: reduce prior weight as sample grows, floored at 55% of
    # REGRESSION_PA so the league-mean anchor never disappears entirely.
    effective_reg = (config.REGRESSION_PA * max(0.55, 1.0 - season_pa / 700.0)
                     if season_pa > 0 else config.REGRESSION_PA)
    regressed_season = (
        (season_hr + effective_reg * config.LEAGUE_AVG_HR_PA)
        / (season_pa + effective_reg)
    ) if season_pa > 0 else config.LEAGUE_AVG_HR_PA

    if recent_pa >= config.MIN_RECENT_PA:
        recent_rate = recent_hr / recent_pa
        recent_trust = min(recent_pa / 100.0, 1.0)
        blended_recent = recent_rate * recent_trust + regressed_season * (1 - recent_trust)
        rate = config.RECENT_WEIGHT * blended_recent + config.SEASON_WEIGHT * regressed_season
    else:
        rate = regressed_season

    # ISO adjustment: stabilizes in ~150-200 PA vs ~300 PA for HR/PA.
    # Fades to zero influence once sample is large enough to trust HR/PA directly.
    try:
        slg = float(season_stats.get("sluggingPercentage", 0) or 0)
        avg = float(season_stats.get("avg", 0) or 0)
        iso = max(0.0, slg - avg)
        if iso > 0 and season_pa >= 30:
            iso_mult = max(0.70, min(1.50, iso / config.LEAGUE_AVG_ISO))
            iso_trust = max(0.0, min(0.20, 1.0 - season_pa / 300.0))
            rate = rate * (1.0 - iso_trust) + rate * iso_mult * iso_trust
    except (ValueError, TypeError):
        pass

    return max(rate, 0.001)


def statcast_blended_rate(raw_rate: float, statcast_power_mult: float, season_pa: int) -> float:
    """
    Blend raw HR/PA with Statcast power adjustment.
    When sample is small (early season), weight Statcast more — it stabilizes in ~50 PA.
    Asymmetric boost: when multiplier signals suppression (mult < 1), give Statcast
    extra weight so true contact/speed players get pulled down more aggressively.
    This is one-sided — we don't amplify the upside here, as the adaptive regression
    already lets large-sample power hitters rise closer to their true rate.
    """
    pa_weight = max(0.15, 1.0 - (season_pa / 350.0))
    # One-sided boost: only raise Statcast weight when the multiplier signals
    # suppression (mult < 1). This pulls true contact/speed players down harder
    # without amplifying elite HR hitters who already benefit from adaptive regression.
    suppression_signal = max(0.0, 1.0 - statcast_power_mult)
    boost = min(0.20, 0.40 * suppression_signal)
    statcast_weight = min(0.65, pa_weight + boost)
    raw_weight = 1.0 - statcast_weight
    statcast_rate = raw_rate * statcast_power_mult
    return max(raw_weight * raw_rate + statcast_weight * statcast_rate, 0.001)


def batter_k_suppressor(season_stats: dict) -> float:
    """
    High K% → fewer balls in play → fewer HR opportunities.
    One-sided: only suppresses above league avg (22.5%). Never boosts contact hitters
    since low K% power is already captured by ISO and barrel%.
    """
    k  = int(season_stats.get("strikeOuts", 0))
    pa = int(season_stats.get("plateAppearances", 0))
    if pa < 50:
        return 1.0
    k_pct = k / pa
    factor = 1.0 - max(0.0, 0.60 * (k_pct - 0.225))
    return round(max(0.85, min(1.0, factor)), 3)


def pitcher_recent_factor(recent_pitcher_stats: dict) -> float:
    """
    Blend last-30-day pitcher HR/9 into the season factor.
    Caps at ±20% influence; fades below 10 IP (too small to trust).
    Max 30% weight even at 40+ recent IP — season sample always dominates.
    """
    ip  = recent_pitcher_stats.get("inningsPitched", 0.0)
    if ip < 10:
        return 1.0
    hrs = int(recent_pitcher_stats.get("homeRuns", 0))
    recent_hr9 = (hrs / ip) * 9.0
    reg_ip = 30
    regressed = (recent_hr9 * ip + config.LEAGUE_AVG_HR9 * reg_ip) / (ip + reg_ip)
    direction = config.LEAGUE_AVG_HR9 / max(regressed, 0.1)
    trust = min(ip / 40.0, 0.30)
    return round(max(0.80, min(1.20, 1.0 + trust * (direction - 1.0))), 3)


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


def pitcher_k_gb_suppressor(pitcher_stats: dict) -> float:
    """
    K% + GB% combined suppressor.
    K% → fewer balls in play → fewer HR opportunities.
    GB% → fewer fly balls → lower HR conversion rate.
    Both are more stable indicators than raw HR/9.
    """
    k  = int(pitcher_stats.get("strikeOuts", 0))
    bf = int(pitcher_stats.get("battersFaced", 0))
    go = int(pitcher_stats.get("groundOuts", 0))
    ao = int(pitcher_stats.get("airOuts", 0))

    # K% factor — 22.5% is league avg; each 5pp above reduces HR prob ~4%
    if bf >= 30:
        k_pct  = k / bf
        k_factor = max(0.82, min(1.12, 1.0 - 0.80 * (k_pct - 0.225)))
    else:
        k_factor = 1.0

    # GB% factor — 44% is league avg on outs; high GB = strong HR suppressor
    total_outs = go + ao
    if total_outs >= 50:
        gb_pct   = go / total_outs
        gb_factor = max(0.86, min(1.12, 1.0 - 0.45 * (gb_pct - 0.44)))
    else:
        gb_factor = 1.0

    return max(0.76, min(1.18, k_factor * gb_factor))


def pitcher_combined_factor(
    pitcher_hr_fac: float,
    statcast_contact_fac: float,
    k_gb_fac: float = 1.0,
) -> float:
    """
    Weighted blend of three independent pitcher HR signals:
      40% HR/FB rate (most HR-specific)
      40% Statcast contact quality against (barrel%, FB%, EV against)
      20% K% + GB% suppressor (ball-in-play profile)
    """
    combined = pitcher_hr_fac * 0.40 + statcast_contact_fac * 0.40 + k_gb_fac * 0.20
    return max(0.55, min(1.60, combined))


def platoon_factor(splits: dict, pitcher_hand: str, batter_side: str, season_pa: int) -> float:
    """
    Stage 1 (expert pipeline): Bayesian shrinkage toward overall average.
    Formula: X_split = (n / (n + 50)) * X_platoon + (50 / (n + 50)) * X_overall
    50 PA is the standard sabermetric shrinkage constant for L/R splits.
    Uses actual split PA counts returned from the MLB Stats API.
    """
    if not pitcher_hand or not batter_side:
        return 1.0

    split_key  = "vl" if pitcher_hand.upper().startswith("L") else "vr"
    split_rate = splits.get(split_key)
    split_pa   = splits.get(f"{split_key}_pa", 0)   # actual PA count

    vl_rate = splits.get("vl", 0)
    vr_rate = splits.get("vr", 0)
    vl_pa   = splits.get("vl_pa", 0)
    vr_pa   = splits.get("vr_pa", 0)

    if not split_rate or (vl_rate + vr_rate) == 0:
        b, p = batter_side[0].upper(), pitcher_hand[0].upper()
        if b == "S":
            return 1.03
        return 1.06 if b != p else 0.96

    # Weighted overall rate (PA-weighted across both splits)
    total_pa   = vl_pa + vr_pa
    total_rate = ((vl_rate * vl_pa + vr_rate * vr_pa) / total_pa
                  if total_pa > 0 else (vl_rate + vr_rate) / 2.0)

    # Bayesian shrinkage — use actual split PA if available, else season proxy
    n = split_pa if split_pa > 0 else int(season_pa * 0.4)
    SHRINK = 50   # standard constant: 50 PA to trust a split halfway
    trust     = n / (n + SHRINK)
    regressed = trust * split_rate + (1 - trust) * total_rate

    factor = regressed / total_rate if total_rate > 0 else 1.0
    return max(0.70, min(1.50, factor))


def expected_pa(lineup_spot: Optional[int]) -> float:
    if lineup_spot and 1 <= lineup_spot <= 9:
        return config.LINEUP_PA[lineup_spot]
    return config.DEFAULT_PA


def fly_ball_adjusted_park_factor(park_factor: float, season_stats: dict) -> float:
    """
    Scale park HR impact by batter's fly-ball tendency.
    A batter who hits more fly balls benefits more (or suffers more) from park HR factor.
    League avg fly-ball rate: ~18% of AB.
    """
    fly_balls = int(season_stats.get("flyBalls", 0))
    ab        = int(season_stats.get("atBats", 1))
    if ab < 80 or fly_balls == 0:
        return park_factor

    fb_pct     = fly_balls / ab
    league_fb  = 0.18
    fb_dev     = (fb_pct - league_fb) / league_fb   # % above/below avg
    adjusted   = 1.0 + (park_factor - 1.0) * (1.0 + 0.30 * fb_dev)
    return max(0.70, min(1.45, adjusted))


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
    # Cap combined multiplier — prevents extreme stacking of park + pitcher + weather + platoon
    combined = pk_factor * pitcher_fac * w_factor * plat_factor
    combined = max(0.42, min(1.82, combined))
    lam = hr_rate * combined * exp_pa
    return max(0.001, min(0.999, 1.0 - math.exp(-lam)))


def hot_streak_factor(short_form: dict, season_stats: dict) -> float:
    """
    Detect hot/cold form over the last 14 days vs season average.
    Conservative — capped at ±8% to avoid over-reacting to small samples.
    """
    short_pa = int(short_form.get("plateAppearances", 0))
    short_hr = int(short_form.get("homeRuns", 0))
    season_pa = int(season_stats.get("plateAppearances", 0))
    season_hr = int(season_stats.get("homeRuns", 0))

    if short_pa < 8 or season_pa < 30:
        return 1.0
    season_rate = season_hr / season_pa
    if season_rate < 0.005:
        return 1.0

    short_rate = short_hr / short_pa
    relative   = short_rate / season_rate
    # tanh softens extreme ratios; max ±8% adjustment
    factor = 1.0 + 0.08 * math.tanh(math.log(max(relative, 0.05)) / 1.5)
    return max(0.93, min(1.08, factor))


def confidence_score(
    season_pa: int, recent_pa: int,
    model_prob: float, market_prob: float,
    has_statcast: bool = False,
    barrel_rate: float = 0.0,
    pitcher_hr9: float = 0.0,
) -> float:
    """
    Confidence score 0-100.
    Threshold bonuses: Barrel > 12% (+5), Pitcher HR/9 > 1.4 (+4).
    """
    sample_conf    = min(season_pa / 400.0, 1.0) * 35.0
    recent_conf    = min(recent_pa / 80.0,  1.0) * 20.0
    statcast_bonus = 8.0 if has_statcast else 0.0

    # Threshold bonuses (from the weighted factor list)
    barrel_bonus  = 5.0 if barrel_rate > 0.12 else 0.0          # Barrel > 12%
    pitcher_bonus = 4.0 if pitcher_hr9 > 1.4  else 0.0          # Pitcher HR/9 > 1.4

    edge = abs(model_prob - market_prob)
    se   = math.sqrt(model_prob * (1 - model_prob) / max(season_pa, 1))
    snr  = min(edge / (se + 0.01), 3.0) / 3.0
    edge_conf = snr * 28.0

    total = (sample_conf + recent_conf + edge_conf
             + statcast_bonus + barrel_bonus + pitcher_bonus)
    return round(min(total, 100.0), 1)

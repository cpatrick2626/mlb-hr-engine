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


def base_hr_rate(
    season_stats: dict,
    recent_stats: dict,
    statcast_mult: float = 1.0,
) -> float:
    season_pa = int(season_stats.get("plateAppearances", 0))
    season_hr = int(season_stats.get("homeRuns", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    recent_hr = int(recent_stats.get("homeRuns", 0))

    # When Statcast signals below-average power, reduce the Bayesian regression target
    # proportionally. This prevents the league-mean anchor from inflating predictions for
    # true contact hitters who are never going to hit HRs. Only adjusts downward (mult >= 1
    # keeps the unbiased league-avg prior so power hitters aren't double-boosted here).
    reg_target_adj = max(0.40, min(1.0, statcast_mult))
    regression_target = config.LEAGUE_AVG_HR_PA * reg_target_adj

    # Adaptive regression: reduce prior weight as sample grows, floored at 50% of
    # REGRESSION_PA so the league-mean anchor never disappears entirely.
    # Reduced floor 0.55→0.50: lets established hitters (300+ PA) carry slightly more
    # weight on their own observed rate; addresses 10-15% bucket under-prediction.
    effective_reg = (config.REGRESSION_PA * max(0.50, 1.0 - season_pa / 700.0)
                     if season_pa > 0 else config.REGRESSION_PA)
    regressed_season = (
        (season_hr + effective_reg * regression_target)
        / (season_pa + effective_reg)
    ) if season_pa > 0 else regression_target

    if recent_pa >= config.MIN_RECENT_PA:
        recent_rate = recent_hr / recent_pa
        recent_trust = min(recent_pa / 100.0, 1.0)
        blended_recent = recent_rate * recent_trust + regressed_season * (1 - recent_trust)
        rate = config.RECENT_WEIGHT * blended_recent + config.SEASON_WEIGHT * regressed_season
    else:
        rate = regressed_season

    # ISO adjustment: stabilizes in ~150-200 PA vs ~300 PA for HR/PA.
    # Linear fade: max 20% weight at ≤50 PA, fully phased out by 250 PA.
    # Aligns with ISO stabilization rate — use it early, drop it once HR/PA is reliable.
    try:
        slg = float(season_stats.get("sluggingPercentage", 0) or 0)
        avg = float(season_stats.get("avg", 0) or 0)
        iso = max(0.0, slg - avg)
        if iso > 0 and season_pa >= 30:
            iso_mult = max(0.70, min(1.50, iso / config.LEAGUE_AVG_ISO))
            iso_trust = max(0.0, min(0.20, (250.0 - season_pa) / 1000.0))
            rate = rate * (1.0 - iso_trust) + rate * iso_mult * iso_trust
    except (ValueError, TypeError):
        pass

    # Zero-HR evidence suppressor: zero HRs through significant PA is strong contact-hitter
    # signal the Bayesian regression can't fully capture due to its 55% floor.
    # Threshold lowered 50→30 PA: backtest showed 0-5% bucket over-predicts by 0.8pp
    # across all runs; early-season batters with 30-49 PA and 0 HRs were getting no discount.
    # Scales from 0.95x at 30 PA down to 0.50x at 250+ PA; no effect when season_hr > 0.
    if season_hr == 0 and season_pa >= 30:
        zero_hr_trust = max(0.50, 1.0 - 0.50 * min(season_pa / 250.0, 1.0))
        rate = rate * zero_hr_trust

    # Very-low-HR suppressor: extends contact-hitter discounting to players with 1-2 HRs
    # whose observed rate is below 40% of league avg (< ~1.1% HR/PA). Bayesian regression
    # still pulls them toward league mean despite near-zero power evidence.
    # Fades in from 100→250 PA so small-sample 1-HR batters aren't penalised too early.
    elif season_hr in (1, 2) and season_pa >= 100:
        obs_rate = season_hr / season_pa
        threshold = config.LEAGUE_AVG_HR_PA * 0.40
        if obs_rate < threshold:
            low_hr_fac = max(0.75, obs_rate / threshold)
            pa_trust = min(1.0, (season_pa - 100) / 150.0)
            rate = rate * (1.0 - pa_trust * (1.0 - low_hr_fac))

    return max(rate, 0.001)


def statcast_blended_rate(
    raw_rate: float,
    statcast_power_mult: float,
    season_pa: int,
    statcast_pa: int = 0,
    statcast_source: str = "current",
) -> float:
    """
    Blend raw HR/PA with Statcast power adjustment.
    When sample is small (early season), weight Statcast more — it stabilizes in ~50 PA.
    Asymmetric boost: when multiplier signals suppression (mult < 1), give Statcast
    extra weight so true contact/speed players get pulled down more aggressively.
    This is one-sided — we don't amplify the upside here, as the adaptive regression
    already lets large-sample power hitters rise closer to their true rate.

    statcast_pa: PA count in the Statcast source (0 = unknown or prior-year full season).
    statcast_source: "current", "blended", or "prior".
      - "current" with statcast_pa < 30: halve Statcast weight — multiplier built from
        too few batted balls to trust fully.
      - "prior" or "blended": prior-year data is a full season; use full base weight.
    """
    # Floor raised 0.15→0.18: at 350+ PA, Statcast now contributes 18% vs 15% of the
    # blended rate — small but systematic lift for established hitters in the 10-15% bucket.
    pa_weight = max(0.18, 1.0 - (season_pa / 350.0))

    # Reduce Statcast weight when current-year sample is sparse.
    # Only applies to "blended" players (curr_pa < MIN_CURRENT_YEAR_PA=50) — "current"
    # players by definition have >= 50 PA so 0 < pa < 50 is never true for them.
    # "prior" is a full prior season and earns full base weight.
    if statcast_source == "blended" and 0 < statcast_pa < 50:
        pa_weight *= 0.50

    suppression_signal = max(0.0, 1.0 - statcast_power_mult)
    boost = min(0.20, 0.40 * suppression_signal)
    statcast_weight = min(0.65, pa_weight + boost)
    raw_weight = 1.0 - statcast_weight

    # Damp Statcast upside so base pa_weight doesn't double-boost elite power hitters.
    # 0.42 factor — nudged down from 0.45 after backtest confirmed 20-25% still -1.6pp.
    # 0.40 previously hurt Brier by over-correcting; 0.42 is a smaller step.
    if statcast_power_mult > 1.0:
        effective_mult = 1.0 + (statcast_power_mult - 1.0) * 0.42
    else:
        effective_mult = statcast_power_mult

    statcast_rate = raw_rate * effective_mult
    return max(raw_weight * raw_rate + statcast_weight * statcast_rate, 0.001)


def early_season_suppressor(season_pa: int, statcast_source: str) -> float:
    """
    Reduces HR rate when relying on prior-year Statcast with sparse current-season PA.
    Without current-year batted-ball validation, prior-year data over-predicts average hitters.

    source="prior"  : 0.80x at 0 PA → 1.0x at 100 PA (pure prior-year, no 2026 signal)
    source="blended": 0.88x at 0 PA → 1.0x at 100 PA (some current data, less discount)
    source="current": no discount — player has established 2026 Statcast form
    """
    if statcast_source == "current" or season_pa >= 100:
        return 1.0
    base = 0.80 if statcast_source == "prior" else 0.88
    return round(base + (1.0 - base) * min(season_pa / 100.0, 1.0), 3)


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
    direction = regressed / config.LEAGUE_AVG_HR9
    trust = min(ip / 40.0, 0.30)
    return round(max(0.80, min(1.20, 1.0 + trust * (direction - 1.0))), 3)


def pitcher_fatigue_factor(days_rest: int) -> float:
    """
    Adjusts pitcher HR allowance based on days since last start.
    Short rest → more HRs; standard 5-day rest → baseline.
    """
    if days_rest <= 2:
        return 1.08
    if days_rest == 3:
        return 1.04
    if days_rest == 4:
        return 1.01
    if days_rest == 5:
        return 1.00
    return max(0.97, 1.0 - 0.01 * (days_rest - 5))


def pitcher_hr_factor(pitcher_stats: dict) -> float:
    """
    v2: HR/FB composite (blends HR/9 with HR per fly ball).
    HR/FB separates fly ball rate from HR conversion rate — more predictive.
    MLB Stats API: homeRuns + airOuts => fly balls faced.
    """
    innings_raw = pitcher_stats.get("inningsPitched", "0.0")
    try:
        if isinstance(innings_raw, (int, float)):
            ip = float(innings_raw)
        else:
            parts = str(innings_raw).split(".")
            ip = int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(innings_raw)
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
    hr9_factor = reg_hr9 / config.LEAGUE_AVG_HR9

    # HR/FB component
    fly_balls = hrs + air_outs
    if fly_balls > 20:
        hr_fb = hrs / fly_balls
        reg_fb = 100
        reg_hr_fb = (hr_fb * fly_balls + config.LEAGUE_HR_FB * reg_fb) / (fly_balls + reg_fb)
        hr_fb_factor = reg_hr_fb / config.LEAGUE_HR_FB
        fb_trust = min(fly_balls / 200.0, 1.0)
        combined = (1.0 - fb_trust) * hr9_factor + fb_trust * hr_fb_factor
    else:
        combined = hr9_factor

    return max(0.65, min(1.50, combined))


def pitcher_k_gb_suppressor(pitcher_stats: dict) -> float:
    """
    K% + GB% + BB% combined suppressor.
    K%  → fewer balls in play → fewer HR opportunities (most stable metric, r~0.85 YoY).
    GB% → fewer fly balls → lower HR conversion rate.
    BB% → poor command → more hittable counts → more HRs (each 1pp above avg adds ~0.4%).
    """
    k  = int(pitcher_stats.get("strikeOuts", 0))
    bb = int(pitcher_stats.get("baseOnBalls", 0))
    bf = int(pitcher_stats.get("battersFaced", 0))
    go = int(pitcher_stats.get("groundOuts", 0))
    ao = int(pitcher_stats.get("airOuts", 0))

    # K% factor — 22.5% league avg; each 5pp above reduces HR prob ~4%
    if bf >= 30:
        k_pct    = k / bf
        k_factor = max(0.82, min(1.12, 1.0 - 0.80 * (k_pct - 0.225)))
    else:
        k_factor = 1.0

    # GB% factor — 44% league avg on outs; high GB = strong HR suppressor
    total_outs = go + ao
    if total_outs >= 50:
        gb_pct    = go / total_outs
        gb_factor = max(0.86, min(1.12, 1.0 - 0.45 * (gb_pct - 0.44)))
    else:
        gb_factor = 1.0

    # BB% factor — 8.5% league avg; high walk rate signals poor command → more HRs
    if bf >= 30:
        bb_pct    = bb / bf
        bb_factor = max(0.92, min(1.08, 1.0 + 0.50 * (bb_pct - 0.085)))
    else:
        bb_factor = 1.0

    return max(0.72, min(1.20, k_factor * gb_factor * bb_factor))


def pitcher_combined_factor(
    pitcher_hr_fac: float,
    statcast_contact_fac: float,
    k_gb_fac: float = 1.0,
) -> float:
    """
    Weighted geometric mean of three independent pitcher HR signals:
      40% Statcast contact quality against (barrel%, FB%, EV against) — most HR-specific
      35% HR/FB rate — direct but noisy (YoY r~0.30); regressed heavily
      25% K% + GB% + BB% suppressor — stable (K% YoY r~0.85), adds command signal

    Shifted 5% weight from HR/FB to K/GB/BB: HR/FB is the noisiest signal and regresses
    heavily to the mean; K% and BB% are more stable and improve year-to-year discrimination.
    """
    combined = (statcast_contact_fac ** 0.40) * (pitcher_hr_fac ** 0.35) * (k_gb_fac ** 0.25)
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


_LEAGUE_AVG_FB_PCT = config.LEAGUE_AVG_FB_PCT  # canonical source: config.py

def fly_ball_adjusted_park_factor(park_factor: float, statcast_fb_pct: float = None) -> float:
    """
    Scale park HR impact by batter's Statcast fly-ball rate (fb_pct from batted-ball CSV).
    A high-FB% batter benefits more from a HR-friendly park (and suffers more in a suppressor).
    Falls back to raw park factor when Statcast fb_pct is unavailable.
    """
    if statcast_fb_pct is None:
        return park_factor
    fb_dev   = (statcast_fb_pct - _LEAGUE_AVG_FB_PCT) / _LEAGUE_AVG_FB_PCT
    adjusted = 1.0 + (park_factor - 1.0) * (1.0 + 0.30 * fb_dev)
    return max(0.70, min(1.45, adjusted))


def park_factor(home_team: str, batter_is_home: bool) -> float:
    return get_park(home_team).get("hr_factor", 1.0)



_MAX_GAME_HR_PROB = config.MAX_GAME_HR_PROB  # canonical source: config.py

def game_hr_probability(
    hr_rate: float, exp_pa: float,
    pk_factor: float = 1.0, pitcher_fac: float = 1.0,
    w_factor: float = 1.0, plat_factor: float = 1.0,
) -> float:
    # Cap combined multiplier — prevents extreme stacking of park + pitcher + weather + platoon.
    # 1.50 ceiling (reduced from 1.60): tightens 25-30% bucket calibration without hurting
    # lower buckets. Coors (1.28) + hittable pitcher + platoon still reaches 1.45-1.50.
    combined = pk_factor * pitcher_fac * w_factor * plat_factor
    combined = max(0.42, min(1.50, combined))
    lam = hr_rate * combined * exp_pa
    prob = max(0.001, 1.0 - math.exp(-lam))
    return min(prob, _MAX_GAME_HR_PROB)


def hot_streak_factor(short_form: dict, season_stats: dict) -> float:
    """
    Detect hot/cold form over the last SHORT_FORM_GAMES games vs season average.
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
    statcast_source: str = "none",
    has_statcast: bool = False,   # legacy; ignored when statcast_source is set
    barrel_rate: float = 0.0,
    pitcher_hr9: float = 0.0,
) -> float:
    """
    Confidence score 0-100.
    Threshold bonuses: Barrel > 12% (+5), Pitcher HR/9 > 1.4 (+4).
    Statcast source bonus: current=+8, blended=+5, prior=+3, none=+0.
    """
    sample_conf    = min(season_pa / 400.0, 1.0) * 35.0
    recent_conf    = min(recent_pa / 80.0,  1.0) * 20.0
    _SC_BONUS      = {"current": 8.0, "blended": 5.0, "prior": 3.0}
    statcast_bonus = _SC_BONUS.get(statcast_source, 8.0 if has_statcast else 0.0)

    # Threshold bonuses — tied to league constants so they adapt when config is refreshed.
    # Barrel: 2× league avg (~11% at 2026 avg of 5.5%) captures elite power-contact tier.
    # Pitcher: 1.25× league avg HR/9 (~1.36 at 2026 avg of 1.09) captures notably hittable tier.
    barrel_bonus  = 5.0 if barrel_rate > config.LEAGUE_AVG_BARREL_RATE * 2.0 else 0.0
    pitcher_bonus = 4.0 if pitcher_hr9 > config.LEAGUE_AVG_HR9 * 1.25        else 0.0

    edge = abs(model_prob - market_prob)
    se   = math.sqrt(model_prob * (1 - model_prob) / max(season_pa, 1))
    snr  = min(edge / (se + 0.005), 3.0) / 3.0
    edge_conf = snr * 28.0

    total = (sample_conf + recent_conf + edge_conf
             + statcast_bonus + barrel_bonus + pitcher_bonus)
    return round(min(total, 100.0), 1)

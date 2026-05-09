"""
Parlay builder — finds the highest-EV 2-3 leg HR parlay from top picks.

Parlay assumptions:
  - Legs are treated as independent (approximation — HR props have low correlation)
  - Combined probability = product of individual probabilities
  - Combined decimal odds = product of individual decimal odds
  - Parlay EV% computed same as single-leg EV%
"""

import itertools
from typing import Optional

import config
from engine.market import american_to_decimal, decimal_to_american
from engine.ev import expected_value_pct


# ── Profile definitions ────────────────────────────────────────────────────────

def _parse_pct(val) -> Optional[float]:
    """Parse '5.2%' → 0.052, or 0.052 → 0.052. Returns None for '--' or invalid."""
    if val is None or val == "--":
        return None
    try:
        s = str(val).replace("%", "").strip()
        f = float(s)
        return f / 100.0 if f > 1.5 else f
    except (ValueError, TypeError):
        return None


def _parse_float(val) -> Optional[float]:
    """Parse a numeric string or float. Returns None for '--' or invalid."""
    if val is None or val == "--":
        return None
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None


def _score_pure_power(player: dict) -> float:
    """
    💣 PURE POWER + LIFT — Most Reliable HR Profile.
    Signals: xSLG (power ceiling), barrel%, launch angle in 10-25° sweet zone.
    """
    score = 0.0

    # xSLG: normalised around league avg 0.405; elite players near 0.600+
    xslg = _parse_float(player.get("xslg"))
    if xslg is not None:
        score += min(2.0, max(0.0, (xslg - 0.300) / 0.250)) * 0.40

    # Barrel%: 10% barrel rate is elite; weights most heavily
    barrel = _parse_pct(player.get("barrel_pct"))
    if barrel is not None:
        score += min(2.0, max(0.0, barrel / 0.10)) * 0.40

    # Launch angle sweet zone bonus
    la = _parse_float(player.get("avg_launch_angle"))
    if la is not None:
        if 10.0 <= la <= 25.0:
            score += 0.20      # ideal HR angle band
        elif 8.0 <= la <= 30.0:
            score += 0.10

    return score


def _score_hidden_power(player: dict) -> float:
    """
    ⚡ HIDDEN POWER (BREAKOUT EDGE) — Best For Value.
    Signals: exit velocity, hard-hit% (proxy for blasts), xSLGdiff > 0
    (xSLG > actual SLG = player underperforming expected contact quality — breakout candidate).
    """
    score = 0.0

    # Exit velocity: normalised; 95+ mph is elite contact
    ev = _parse_float(player.get("exit_velo"))
    if ev is not None:
        score += min(2.0, max(0.0, (ev - 82.0) / 14.0)) * 0.35

    # Hard-hit% (proxy for blasts_contact): 50%+ is elite
    hh = _parse_pct(player.get("hard_hit"))
    if hh is not None:
        score += min(2.0, max(0.0, hh / 0.50)) * 0.35

    # xSLGdiff = xSLG − actual SLG: positive means underperforming expected → hidden power
    xslg_diff = _parse_float(player.get("xslg_diff"))
    if xslg_diff is not None:
        if xslg_diff > 0:
            score += min(1.0, xslg_diff / 0.100) * 0.30
        elif xslg_diff < -0.05:
            score -= 0.10   # slight penalty for over-performers (regression risk)

    return score


def _score_consistent_damage(player: dict) -> float:
    """
    🎯 CONSISTENT DAMAGE PROFILE — Safe + Parlay Builder.
    Signals: sweet spot% (solid contact proxy), hard-hit%, fly ball%.
    """
    score = 0.0

    # Sweet spot% (LA 8-32°, proxy for solidcontact_percent): 40%+ is elite
    ss = _parse_pct(player.get("sweet_spot_pct"))
    if ss is not None:
        score += min(2.0, max(0.0, ss / 0.40)) * 0.35

    # Hard-hit%
    hh = _parse_pct(player.get("hard_hit"))
    if hh is not None:
        score += min(2.0, max(0.0, hh / 0.50)) * 0.35

    # Fly ball%: more fly balls = more HR opportunities; 35%+ is elite (Savant fb_rate scale)
    fb = _parse_pct(player.get("fb_pct"))
    if fb is not None:
        score += min(2.0, max(0.0, fb / 0.35)) * 0.30

    return score


_PROFILES = [
    {
        "key":      "pure_power",
        "name":     "💣 PURE POWER + LIFT",
        "subtitle": "MOST RELIABLE HR PROFILE",
        "desc":     "Targets elite xSLG, barrel rate, and launch angle in the 10–25° sweet zone.",
        "score_fn": _score_pure_power,
    },
    {
        "key":      "hidden_power",
        "name":     "⚡ HIDDEN POWER (BREAKOUT EDGE)",
        "subtitle": "BEST FOR VALUE",
        "desc":     "Targets hard exit velocity and xSLG > actual SLG — players underperforming their expected contact quality.",
        "score_fn": _score_hidden_power,
    },
    {
        "key":      "consistent_damage",
        "name":     "🎯 CONSISTENT DAMAGE PROFILE",
        "subtitle": "SAFE + PARLAY BUILDER",
        "desc":     "Targets sweet spot%, hard-hit%, and fly ball% — consistent damage production regardless of matchup.",
        "score_fn": _score_consistent_damage,
    },
]


def build_profile_parlays(
    all_players: list[dict],
    n_combos: int = 3,
    leg_size: int = 3,
) -> list[dict]:
    """
    Build top-N diverse combos for each of the 3 stat profiles.
    Candidates drawn from top-20 profile scorers; ranked 60% by EV, 40% by profile fit.
    Returns a list of profile result dicts (one per profile).
    """
    # Require positive EV — profile parlays should never include -EV legs
    # even if those players have elite Statcast metrics.
    pool = [p for p in all_players
            if p.get("best_american") and p.get("model_prob", 0) > 0
            and p.get("ev_pct", 0) > 0]

    results = []
    for profile in _PROFILES:
        score_fn = profile["score_fn"]

        # Score all eligible players on this profile
        scored_players = sorted(
            [(score_fn(p), p) for p in pool],
            key=lambda x: x[0], reverse=True,
        )
        candidates = [p for _, p in scored_players[:min(20, len(scored_players))]]

        if len(candidates) < leg_size:
            results.append({**profile, "score_fn": None, "combos": []})
            continue

        # Evaluate every combination within the candidate pool
        scored_combos = []
        for combo in itertools.combinations(candidates, leg_size):
            teams = [leg.get("team", "") for leg in combo]
            if len(teams) != len(set(teams)):
                continue
            parlay = _evaluate_parlay(list(combo))
            parlay["profile_score"] = sum(score_fn(leg) for leg in combo) / leg_size
            scored_combos.append(parlay)

        if not scored_combos:
            results.append({**profile, "score_fn": None, "combos": []})
            continue

        # Normalise both dimensions then blend
        max_ev = max(c["ev_pct"]       for c in scored_combos) or 1.0
        max_ps = max(c["profile_score"] for c in scored_combos) or 1.0
        for c in scored_combos:
            ev_norm = c["ev_pct"]        / max_ev
            ps_norm = c["profile_score"] / max_ps
            c["combo_rank"] = 0.60 * ev_norm + 0.40 * ps_norm
        scored_combos.sort(key=lambda x: x["combo_rank"], reverse=True)

        # Pick diverse top-N — zero player overlap between any two selected combos.
        # Combo 1 = best group; Combo 2 shares no players with Combo 1;
        # Combo 3 shares no players with Combo 1 or 2.
        selected: list[dict] = []
        used_player_ids: set = set()
        for candidate in scored_combos:
            if len(selected) >= n_combos:
                break
            cids = {leg["player_id"] for leg in candidate["legs"]}
            if cids & used_player_ids:   # any overlap → skip
                continue
            selected.append(candidate)
            used_player_ids |= cids

        results.append({**profile, "score_fn": None, "combos": selected})

    return results


def build_best_parlay(ranked_picks: list[dict]) -> Optional[dict]:
    """Single best parlay across all leg counts (used by CLI display)."""
    pool = [p for p in ranked_picks[:config.PARLAY_CANDIDATE_POOL]
            if p.get("best_american") and p.get("model_prob", 0) > 0]
    if len(pool) < config.PARLAY_MIN_LEGS:
        return None
    best: Optional[dict] = None
    best_ev = float("-inf")
    for n_legs in range(config.PARLAY_MIN_LEGS, config.PARLAY_MAX_LEGS + 1):
        for combo in itertools.combinations(pool, n_legs):
            # Reject same-team stacks: HR props within the same lineup share pitcher
            # and weather exposure, directly violating the independence assumption.
            teams = [leg.get("team", "") for leg in combo]
            if len(teams) != len(set(teams)):
                continue
            parlay = _evaluate_parlay(list(combo))
            if parlay["ev_pct"] > best_ev:
                best_ev = parlay["ev_pct"]
                best = parlay
    return best


def build_auto_parlays(
    ranked_picks: list[dict],
    n_combos: int = 3,
    leg_sizes: tuple = (2, 3, 4),
) -> dict[int, list[dict]]:
    """
    Build N diverse top-EV combos for each leg size.
    Returns {2: [combo, combo, combo], 3: [...], 4: [...]}.

    Diversity rule: each new combo must differ by at least 1 player from
    every already-selected combo of the same leg size.
    """
    pool = [p for p in ranked_picks[:config.PARLAY_CANDIDATE_POOL]
            if p.get("best_american") and p.get("model_prob", 0) > 0]

    result: dict[int, list[dict]] = {}
    for n_legs in leg_sizes:
        if len(pool) < n_legs:
            result[n_legs] = []
            continue

        # Score every combination
        scored = []
        for combo in itertools.combinations(pool, n_legs):
            teams = [leg.get("team", "") for leg in combo]
            if len(teams) != len(set(teams)):
                continue
            scored.append(_evaluate_parlay(list(combo)))
        scored.sort(key=lambda x: x["ev_pct"], reverse=True)

        # Pick diverse top-N — reject if >1 player overlaps with any selected combo.
        # Allows one shared player between combos (avoids being too strict with a small pool)
        # but prevents near-identical parlays that differ by only one leg.
        selected: list[dict] = []
        for candidate in scored:
            if len(selected) >= n_combos:
                break
            cids = {leg["player_id"] for leg in candidate["legs"]}
            too_similar = any(
                len(cids & {leg["player_id"] for leg in sel["legs"]}) > 1
                for sel in selected
            )
            if not too_similar:
                selected.append(candidate)

        result[n_legs] = selected

    return result


def _evaluate_parlay(legs: list[dict]) -> dict:
    combined_prob = 1.0
    combined_decimal = 1.0
    combined_ev_prob = 1.0

    for leg in legs:
        model_p = leg["model_prob"]
        market_p = leg.get("market_no_vig_prob", 0)
        # Cap each leg's EV probability at 1.4× market no-vig — same cap as
        # single-pick EV (pipeline.py) — prevents per-leg edges from compounding
        # into absurd parlay EV on long-shot lines (+2000, +3000).
        ev_model_p = min(model_p, market_p * 1.4) if market_p > 0 else model_p
        combined_prob    *= model_p
        combined_ev_prob *= ev_model_p
        combined_decimal *= american_to_decimal(leg["best_american"])

    ev_pct = expected_value_pct(combined_ev_prob, combined_decimal)
    combined_american = decimal_to_american(combined_decimal)

    return {
        "legs":              legs,
        "n_legs":            len(legs),
        "combined_prob":     round(combined_prob, 4),
        "combined_ev_prob":  round(combined_ev_prob, 4),
        "combined_prob_pct": round(combined_prob * 100, 2),
        "combined_decimal":  round(combined_decimal, 2),
        "combined_american": combined_american,
        "ev_pct":            round(ev_pct, 2),
    }


def parlay_bet_size(parlay: dict, bankroll: float = None) -> float:
    """Kelly-sized parlay bet (more conservative: use 1/8 Kelly for parlays)."""
    if bankroll is None:
        bankroll = config.BANKROLL

    dec = parlay["combined_decimal"]
    # Use combined_ev_prob (capped at 1.4× market per leg) to match the EV
    # calculation — consistent with how single-leg EV is computed.
    p = parlay.get("combined_ev_prob", parlay["combined_prob"])
    b = dec - 1.0
    if b <= 0 or p <= 0:
        return 0.0
    q = 1.0 - p
    f = max(0.0, (b * p - q) / b)
    parlay_kelly_frac = 0.125  # 1/8 Kelly for parlays
    raw = f * parlay_kelly_frac * bankroll
    cap = 0.02 * bankroll  # Cap parlays at 2% of bankroll
    return round(min(raw, cap), 2)

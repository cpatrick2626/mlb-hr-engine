"""
Filter rules — a pick must pass ALL rules to be a recommended bet.
"""

import config


def apply_filters(pick: dict) -> tuple[bool, list[str]]:
    """
    Returns (passed, list_of_failure_reasons).
    pick must contain: ev_pct, edge_pct, expected_pa,
                       park_factor, weather_factor, pitcher_factor.
    """
    fails: list[str] = []

    # Sanity check — model probability must be in a physically realistic range
    model_prob = pick.get("model_prob", 0)
    if model_prob <= 0 or model_prob > config.MAX_GAME_HR_PROB:
        fails.append(f"Model prob out of bounds: {model_prob:.1%} (must be 0–{config.MAX_GAME_HR_PROB:.0%})")

    # Rule 1 — Minimum EV
    ev = pick.get("ev_pct", -999)
    if ev < config.MIN_EV_PCT:
        fails.append(f"EV {ev:+.1f}% (need ≥ +{config.MIN_EV_PCT:.0f}%)")

    # Rule 2 — Minimum edge vs no-vig market
    edge = pick.get("edge_pct", -999)
    if edge < config.MIN_EDGE_PCT:
        fails.append(f"Edge {edge:+.1f}% (need ≥ +{config.MIN_EDGE_PCT:.0f}%)")

    # Rule 3 — Enough expected plate appearances
    pa = pick.get("expected_pa", 0)
    if pa < config.MIN_PA_THRESHOLD:
        fails.append(f"Expected PA {pa:.1f} (need ≥ {config.MIN_PA_THRESHOLD:.1f})")

    # Rule 4 — Park not a strong HR suppressor
    pf = pick.get("park_factor", 1.0)
    if pf < config.MAX_PARK_PENALTY:
        fails.append(f"Park suppressor (factor {pf:.2f})")

    # Rule 5 — Weather not strongly negative
    wf = pick.get("weather_factor", 1.0)
    if wf < config.MAX_WEATHER_PENALTY:
        fails.append(f"Adverse weather (factor {wf:.2f})")

    # Rule 6 — Not facing elite HR suppressor pitcher
    pitf = pick.get("pitcher_factor", 1.0)
    if pitf < config.MAX_PITCHER_SUPPRESSOR:
        fails.append(f"Elite HR suppressor pitcher (factor {pitf:.2f})")

    # Rule 7 — Need market odds to evaluate (no picks without a line)
    if not pick.get("best_american"):
        fails.append("No market odds available")

    return len(fails) == 0, fails


def soft_flags(pick: dict) -> list[str]:
    """
    Non-disqualifying cautions to show in output.
    """
    flags: list[str] = []
    if pick.get("season_pa", 0) < 50:
        flags.append("⚠ Small season sample")
    if pick.get("recent_pa", 0) < 20:
        flags.append("⚠ Limited recent data")
    if pick.get("pitcher_factor", 1.0) < 0.85:
        flags.append("⚠ Tough pitcher matchup")
    if pick.get("park_factor", 1.0) < 0.95:
        flags.append("⚠ Slight park penalty")
    if pick.get("weather_factor", 1.0) < 0.94:
        flags.append("⚠ Unfavorable weather")
    return flags

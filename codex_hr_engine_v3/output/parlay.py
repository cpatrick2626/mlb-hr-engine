"""
Parlay builder — finds the highest-EV 2-3 leg HR parlay from top picks.

Parlay assumptions:
  - Legs are treated as independent (approximation — HR props have low correlation)
  - Combined probability = product of individual probabilities
  - Combined decimal odds = product of individual decimal odds
  - Parlay EV% computed same as single-leg EV%
"""

import itertools

import config
from engine.market import american_to_decimal, decimal_to_american
from engine.ev import expected_value_pct


def build_best_parlay(ranked_picks: list[dict]) -> dict | None:
    """
    Examine all 2-leg and 3-leg combinations from the top picks.
    Return the combination with the highest EV%.
    """
    pool = [p for p in ranked_picks[:config.PARLAY_CANDIDATE_POOL]
            if p.get("best_american") and p.get("model_prob", 0) > 0]

    if len(pool) < config.PARLAY_MIN_LEGS:
        return None

    best: dict | None = None
    best_ev = float("-inf")

    for n_legs in range(config.PARLAY_MIN_LEGS, config.PARLAY_MAX_LEGS + 1):
        for combo in itertools.combinations(pool, n_legs):
            parlay = _evaluate_parlay(list(combo))
            if parlay["ev_pct"] > best_ev:
                best_ev = parlay["ev_pct"]
                best = parlay

    return best


def _evaluate_parlay(legs: list[dict]) -> dict:
    combined_prob = 1.0
    combined_decimal = 1.0

    for leg in legs:
        combined_prob *= leg["model_prob"]
        combined_decimal *= american_to_decimal(leg["best_american"])

    # Parlay pays combined_decimal − 1 on a win
    ev_pct = expected_value_pct(combined_prob, combined_decimal)
    combined_american = decimal_to_american(combined_decimal)

    return {
        "legs": legs,
        "n_legs": len(legs),
        "combined_prob": round(combined_prob, 4),
        "combined_prob_pct": round(combined_prob * 100, 2),
        "combined_decimal": round(combined_decimal, 2),
        "combined_american": combined_american,
        "ev_pct": round(ev_pct, 2),
    }


def parlay_bet_size(parlay: dict, bankroll: float = None) -> float:
    """Kelly-sized parlay bet (more conservative: use 1/8 Kelly for parlays)."""
    if bankroll is None:
        import config as cfg
        bankroll = cfg.BANKROLL

    dec = parlay["combined_decimal"]
    p = parlay["combined_prob"]
    b = dec - 1.0
    if b <= 0 or p <= 0:
        return 0.0
    q = 1.0 - p
    f = max(0.0, (b * p - q) / b)
    parlay_kelly_frac = 0.125  # 1/8 Kelly for parlays
    raw = f * parlay_kelly_frac * bankroll
    cap = 0.02 * bankroll  # Cap parlays at 2% of bankroll
    return round(min(raw, cap), 2)

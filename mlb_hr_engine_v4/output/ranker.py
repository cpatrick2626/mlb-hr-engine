"""
Composite score and ranking.

Score = (EV% × ev_w + Edge% × (1-ev_w)) × confidence_scale

Default ev_w = 0.55 (EV) / 0.45 (Edge). Auto-learn may adjust this ratio
based on which signal better predicts actual HR outcomes.

confidence_scale = 0.50 + 0.50 × (confidence / 100)
  conf=100 → scale=1.00  (full signal)
  conf= 75 → scale=0.875 (slight haircut)
  conf= 50 → scale=0.75  (meaningful haircut for uncertain picks)
  conf= 25 → scale=0.625 (heavily discounted)

Multiplicative design: confidence is a data-quality multiplier on the core
signal, not just an additive bonus. A high-EV pick with low confidence gets
suppressed, so it can't crowd out a well-substantiated lower-EV pick. This
prevents noisy early-season or single-book picks from dominating the ranking.
"""

from tracking import adaptive_weights

_DEFAULT_EV_WEIGHT   = 0.55
_DEFAULT_EDGE_WEIGHT = 0.45


def composite_score(ev_pct: float, edge_pct: float, confidence: float) -> float:
    """
    Confidence-weighted composite score. Higher = better bet.
    EV/Edge weights are adaptive — auto-learn adjusts them based on win-rate data.
    """
    ev_w   = adaptive_weights.get("ranker_ev_weight", _DEFAULT_EV_WEIGHT)
    edge_w = 1.0 - ev_w
    signal     = ev_pct * ev_w + edge_pct * edge_w
    conf_scale = 0.50 + 0.50 * (confidence / 100.0)
    return round(signal * conf_scale, 2)


def rank_picks(picks: list[dict]) -> list[dict]:
    """Sort qualified picks by composite score descending, add rank."""
    for p in picks:
        p["score"] = composite_score(
            p.get("ev_pct", 0),
            p.get("edge_pct", 0),
            p.get("confidence", 0),
        )
    ranked = sorted(picks, key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(ranked, 1):
        p["rank"] = i
    return ranked


def rank_all_by_model(picks: list[dict]) -> list[dict]:
    """Rank all players (filtered or not) purely by model HR probability."""
    return sorted(picks, key=lambda x: x.get("model_prob", 0), reverse=True)

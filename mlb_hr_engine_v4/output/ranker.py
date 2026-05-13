"""
Composite score, confidence tiers, and ranking.

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
suppressed, so it can't crowd out a well-substantiated lower-EV pick.

Confidence Tiers (assigned to every pick):
  S — conf ≥ 70 AND edge ≥ 8%   → elite, act with conviction
  A — conf ≥ 55 AND edge ≥ 5%   → strong, core betting targets
  B — conf ≥ 40 AND edge ≥ 3%   → solid, worth playing at standard size
  C — below B thresholds          → weak/noisy, reduce size or skip
"""

from tracking import adaptive_weights

_DEFAULT_EV_WEIGHT   = 0.55
_DEFAULT_EDGE_WEIGHT = 0.45

# (grade, display_label, color_hex, min_confidence, min_edge_pct)
_TIERS = [
    ("S", "🌟 S-Tier", "#FFD700", 70, 8.0),
    ("A", "✅ A-Tier", "#4ade80", 55, 5.0),
    ("B", "🟡 B-Tier", "#facc15", 40, 3.0),
    ("C", "🔴 C-Tier", "#f87171",  0, 0.0),
]

TIER_COLORS = {g: col for g, _, col, _, _ in _TIERS}
TIER_LABELS = {g: lbl for g, lbl, _, _, _ in _TIERS}
TIER_ORDER  = {g: i for i, (g, *_) in enumerate(_TIERS)}  # S=0, A=1, B=2, C=3


def confidence_tier(confidence: float, edge_pct: float) -> str:
    """
    Return S/A/B/C tier grade based on confidence score and edge strength.
    Both dimensions must clear the threshold — a high-confidence pick with
    a thin edge is still B/C; a huge edge from a noisy single-book line is still C.
    """
    for grade, _, _, min_conf, min_edge in _TIERS:
        if confidence >= min_conf and edge_pct >= min_edge:
            return grade
    return "C"


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
    """
    Score, tier, and sort qualified picks.

    Primary sort: confidence tier (S → A → B → C).
    Secondary sort: composite score descending within each tier.

    This ensures high-confidence, high-edge picks surface at the top
    and weak/noisy plays are pushed to the bottom regardless of raw EV.
    """
    for p in picks:
        ev   = p.get("ev_pct", 0)
        edge = p.get("edge_pct", 0)
        conf = p.get("confidence", 0)
        p["score"] = composite_score(ev, edge, conf)
        p["confidence_tier"] = confidence_tier(conf, edge)

    ranked = sorted(
        picks,
        key=lambda x: (TIER_ORDER[x["confidence_tier"]], -x["score"]),
    )
    for i, p in enumerate(ranked, 1):
        p["rank"] = i
    return ranked


def rank_all_by_model(picks: list[dict]) -> list[dict]:
    """Rank all players (filtered or not) purely by model HR probability."""
    return sorted(picks, key=lambda x: x.get("model_prob", 0), reverse=True)

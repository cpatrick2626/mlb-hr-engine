"""
Composite score and ranking.

Score = EV%  × 0.40
      + Edge% × 0.35
      + Confidence (0-100 → 0-2.5 pts) × 0.25

Confidence is scaled to 0-10 before weighting so all three components are in
comparable magnitude (~2-10 for typical picks). Using 25 instead of 10 caused
confidence to dominate (47% of score for typical picks) vs the intended 25%.
"""


def composite_score(ev_pct: float, edge_pct: float, confidence: float) -> float:
    """
    Weighted composite score for ranking qualified picks.
    Higher = better bet.
    """
    ev_component   = ev_pct * 0.40
    edge_component = edge_pct * 0.35
    conf_component = (confidence / 100.0) * 10.0 * 0.25
    return round(ev_component + edge_component + conf_component, 2)


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

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
  B — conf ≥ 35 AND edge ≥ 2.5% → solid, worth playing at standard size
  C — below B thresholds          → weak/noisy, reduce size or skip
"""


# (grade, display_label, color_hex, min_confidence, min_edge_pct)
_TIERS = [
    ("S", "🌟 S-Tier", "#FFD700", 70, 8.0),
    ("A", "✅ A-Tier", "#4ade80", 55, 5.0),
    ("B", "🟡 B-Tier", "#facc15", 35, 2.5),
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


def composite_score(model_prob: float) -> float:
    return round(model_prob, 4)


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
        p["score"] = composite_score(p.get("model_prob", 0))
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


def rank_within_tiers(players: list[dict]) -> None:
    """Stamp model_tier_rank on every player in-place.

    Format: '<TIER> #<N>' (e.g., 'APEX #1', 'ELITE #3').
    Sorted model_prob descending within tier; player_name breaks ties deterministically.
    """
    import config as _cfg
    thresholds = _cfg.FS_TIER_THRESHOLDS
    _tier_seq = ["APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD"]

    def _tier(model_prob: float) -> str:
        for t in _tier_seq[:-1]:
            if model_prob >= thresholds[t]:
                return t
        return "COLD"

    by_tier: dict[str, list[dict]] = {t: [] for t in _tier_seq}
    for p in players:
        by_tier[_tier(float(p.get("model_prob", 0)))].append(p)

    for tier, group in by_tier.items():
        group.sort(key=lambda x: (-float(x.get("model_prob", 0)), x.get("player_name", "")))
        for i, p in enumerate(group, 1):
            p["model_tier_rank"] = f"{tier} #{i}"


def rank_jig_within_tiers(entries: list[dict]) -> None:
    """Stamp jig_tier_rank on every JIG entry in-place.

    Format: '<TIER> #<N>' (e.g., 'APEX #1', 'ELITE #3').
    Each entry is a dict with 'jig' (float score) and 'player' (dict with player_name).
    Sorted jig score descending within tier; player_name breaks ties deterministically.
    """
    import config as _cfg
    thresholds = _cfg.JIG_TIER_THRESHOLDS
    _tier_seq = ["APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD"]

    def _tier(jig_score: float) -> str:
        for t in _tier_seq[:-1]:
            if jig_score >= thresholds[t]:
                return t
        return "COLD"

    by_tier: dict[str, list[dict]] = {t: [] for t in _tier_seq}
    for entry in entries:
        by_tier[_tier(float(entry.get("jig", 0)))].append(entry)

    for tier, group in by_tier.items():
        group.sort(key=lambda x: (
            -float(x.get("jig", 0)),
            x.get("player", {}).get("player_name", ""),
        ))
        for i, entry in enumerate(group, 1):
            entry["jig_tier_rank"] = f"{tier} #{i}"

"""
Adaptive weight registry.

Loads learned_adjustments.json once per session and exposes clamped values
to pipeline, ranker, and filters so predictions automatically improve as
historical performance data accumulates.

Hard bounds enforce that no auto-learned adjustment can push the model
outside a safe operating range regardless of what the data suggests.
"""

import json
from pathlib import Path

ADJUSTMENTS_PATH = Path(__file__).parent / "learned_adjustments.json"

# Hard bounds — adaptive values are clamped to these on load
BOUNDS: dict[str, tuple[float, float]] = {
    "prob_scale":        (0.80, 1.20),
    "min_ev_pct":        (2.0,  8.0),
    "min_model_prob":    (0.04, 0.18),
    "recent_weight":     (0.15, 0.50),
    "interaction_coeff": (0.08, 0.35),
    "ranker_ev_weight":  (0.35, 0.75),
}

_cache: dict | None = None


def load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if not ADJUSTMENTS_PATH.exists():
        _cache = {}
        return _cache
    try:
        with open(ADJUSTMENTS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        _cache = {}
        return _cache
    clamped = {}
    for key, val in raw.items():
        if key in BOUNDS and isinstance(val, (int, float)):
            lo, hi = BOUNDS[key]
            clamped[key] = round(max(lo, min(hi, float(val))), 4)
        else:
            clamped[key] = val
    _cache = clamped
    return _cache


def get(key: str, default=None):
    return load().get(key, default)


def apply_prob_scale(model_prob: float) -> float:
    scale = get("prob_scale", 1.0)
    if scale == 1.0:
        return model_prob
    return min(0.29, max(0.001, model_prob * scale))


def active_overrides() -> dict:
    """Return active non-meta adjustments for UI display."""
    skip = {"last_auto_ts", "auto_apply_count"}
    return {k: v for k, v in load().items() if k not in skip}


def invalidate_cache() -> None:
    global _cache
    _cache = None

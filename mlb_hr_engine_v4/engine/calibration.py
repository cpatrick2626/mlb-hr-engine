"""
Probability calibration layer — post-model monotone transforms.

Maps raw model_prob → calibrated_prob while preserving rank order.
All transforms are monotone by construction — ranking is never altered.

Disabled by default (CALIBRATION_ENABLED=False in config.py).
Enable after validating parameters with analyze_calibration.py.

Methods
-------
platt    : sigmoid(a × logit(p) + b)
           2 fitted params. a<1 compresses range, b shifts overall level.
           At a=1, b=0 this is the identity. Crossover (where calibrated==raw)
           is at p = sigmoid(b / (1-a)) when a < 1.

isotonic : piecewise monotone linear interpolation between fitted breakpoints.
           Fully flexible, fits any monotone shape. More parameters, higher
           overfitting risk on small validation sets.

none     : identity — used when CALIBRATION_ENABLED=False or method="none".

Parameters are fitted by analyze_calibration.py. The recommended params
are stored in config.py after the analyst approves them.
"""

import json
import math
from pathlib import Path

import config

_EPS = 1e-7

# Warehouse isotonic recalibration curve — fitted on labeled
# batter_stat_history outcomes by scripts/analysis/fit_warehouse_isotonic.py.
# Fit input is the FINAL model_prob (post prob_scale, post Platt), so this
# stage composes AFTER apply_calibration() — never before it.
_WAREHOUSE_ISOTONIC_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse_isotonic.json"
_warehouse_curve: "dict | None | bool" = None  # None=not loaded, False=unavailable


def logit(p: float) -> float:
    """Log-odds. Clamps to avoid log(0)."""
    p = max(_EPS, min(1.0 - _EPS, p))
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def platt_scale(p: float, a: float, b: float) -> float:
    """
    Platt calibration: sigmoid(a * logit(p) + b).

    Monotone by construction — a > 0 guarantees derivative > 0.
    a < 1.0: compresses the probability range (less extreme predictions).
    a > 1.0: expands the range (more extreme predictions).
    b < 0.0: shifts predictions down.
    b > 0.0: shifts predictions up.

    Crossover (where calibrated == raw): p* = sigmoid(b / (1 - a)) when a != 1.
    Below p*: predictions increase. Above p*: predictions decrease.
    """
    return sigmoid(a * logit(p) + b)


def isotonic_scale(p: float, breakpoints: list, values: list) -> float:
    """
    Piecewise linear monotone interpolation between fitted breakpoints.

    breakpoints: sorted ascending list of raw model_prob values.
    values:      calibrated_prob at each breakpoint (must be non-decreasing).
    Extrapolates with the nearest slope beyond the range.
    """
    n = len(breakpoints)
    if n == 0 or len(values) != n:
        return p

    if p <= breakpoints[0]:
        if n >= 2:
            slope = (values[1] - values[0]) / max(breakpoints[1] - breakpoints[0], _EPS)
            return max(_EPS, values[0] + slope * (p - breakpoints[0]))
        return values[0]

    if p >= breakpoints[-1]:
        if n >= 2:
            slope = (values[-1] - values[-2]) / max(breakpoints[-1] - breakpoints[-2], _EPS)
            return min(1.0 - _EPS, values[-1] + slope * (p - breakpoints[-1]))
        return values[-1]

    for i in range(n - 1):
        if breakpoints[i] <= p < breakpoints[i + 1]:
            span = max(breakpoints[i + 1] - breakpoints[i], _EPS)
            t    = (p - breakpoints[i]) / span
            return values[i] + t * (values[i + 1] - values[i])

    return p  # fallback (shouldn't reach here)


def crossover_prob(a: float, b: float) -> float:
    """
    For Platt scaling: return the raw probability p* at which calibrated(p*) == p*.
    Below p*: calibration increases predictions. Above p*: calibration decreases.
    Returns None when a == 1 (no crossover, pure shift).
    """
    if abs(a - 1.0) < _EPS:
        return None
    return sigmoid(b / (1.0 - a))


def apply_calibration(p: float, barrel_rate: float = 0.0) -> float:
    """
    Apply the configured calibration transform to a raw model probability.

    Returns p unchanged when calibration is disabled (default).
    Output is clamped to (0.001, MAX_GAME_HR_PROB].

    barrel_rate: batter's Statcast barrel% (brl_pa fraction, e.g. 0.12 = 12%).
      Used only when ELITE_PLATT_ENABLED=True — elite barrel hitters receive a
      lighter Platt transform (higher crossover) to reduce compression of their
      already-underestimated pre-calibration probabilities.

    Integration points:
      pipeline.py — applied after apply_prob_scale()
    """
    if not getattr(config, "CALIBRATION_ENABLED", False):
        return p

    method = getattr(config, "CALIBRATION_METHOD", "none")

    if method == "platt":
        # Elite tier Platt (Session 23): confirmed high-barrel hitters receive lighter
        # calibration so the Platt transform does not compound the pre-calibration
        # under-prediction from regression compression. Standard crossover=10.9% compresses
        # everything above; elite Platt crossover=22.3% is near-identity up to 29%.
        # Analysis: V4a variant improved Brier 0.00024; top-50 accuracy 26%→30%;
        # new 25-30% picks created (actual HR rate 29.9%). Rollback: ELITE_PLATT_ENABLED=False.
        if (getattr(config, "ELITE_PLATT_ENABLED", False)
                and barrel_rate >= getattr(config, "ELITE_PLATT_BARREL_THRESHOLD", 0.10)):
            a = getattr(config, "ELITE_PLATT_A", 0.92)
            b = getattr(config, "ELITE_PLATT_B", -0.10)
        else:
            a = getattr(config, "CALIBRATION_PLATT_A", 1.0)
            b = getattr(config, "CALIBRATION_PLATT_B", 0.0)
        result = platt_scale(p, a, b)
    elif method == "isotonic":
        bp     = getattr(config, "CALIBRATION_ISOTONIC_BREAKPOINTS", [])
        vals   = getattr(config, "CALIBRATION_ISOTONIC_VALUES", [])
        result = isotonic_scale(p, bp, vals)
    else:
        return p

    _max = getattr(config, "MAX_GAME_HR_PROB", 0.29)
    return round(min(_max, max(0.001, result)), 4)


def _load_warehouse_curve() -> "dict | bool":
    """Load the fitted warehouse isotonic curve once per session."""
    global _warehouse_curve
    if _warehouse_curve is not None:
        return _warehouse_curve
    try:
        with open(_WAREHOUSE_ISOTONIC_PATH, encoding="utf-8") as f:
            curve = json.load(f)
        bp, vals = curve["breakpoints"], curve["values"]
        if len(bp) >= 2 and len(bp) == len(vals):
            _warehouse_curve = {"breakpoints": bp, "values": vals}
        else:
            _warehouse_curve = False
    except Exception:
        _warehouse_curve = False
    return _warehouse_curve


def apply_warehouse_isotonic(p: float) -> float:
    """
    Final-stage isotonic recalibration fitted on labeled warehouse outcomes
    (batter_stat_history.hr_outcome vs the FINAL displayed model_prob).

    Monotone piecewise-linear — ranking is preserved exactly. Corrects levels
    only, so calibrated probabilities match observed HR rates.

    Integration point:
      pipeline.py — applied AFTER apply_calibration() (which itself runs after
      apply_prob_scale()). Fit input == production input; no double-correction.

    Returns p unchanged when disabled (WAREHOUSE_ISOTONIC_ENABLED=False) or
    when the curve artifact (data/warehouse_isotonic.json) is unavailable.
    """
    if not getattr(config, "WAREHOUSE_ISOTONIC_ENABLED", False):
        return p
    curve = _load_warehouse_curve()
    if not curve:
        return p
    result = isotonic_scale(p, curve["breakpoints"], curve["values"])
    return round(max(0.001, min(1.0 - _EPS, result)), 4)

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

import math
import config

_EPS = 1e-7


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


def apply_calibration(p: float) -> float:
    """
    Apply the configured calibration transform to a raw model probability.

    Returns p unchanged when calibration is disabled (default).
    Output is clamped to (0.001, MAX_GAME_HR_PROB].

    Integration points:
      pipeline.py — applied after apply_prob_scale()
    """
    if not getattr(config, "CALIBRATION_ENABLED", False):
        return p

    method = getattr(config, "CALIBRATION_METHOD", "none")

    if method == "platt":
        a      = getattr(config, "CALIBRATION_PLATT_A", 1.0)
        b      = getattr(config, "CALIBRATION_PLATT_B", 0.0)
        result = platt_scale(p, a, b)
    elif method == "isotonic":
        bp     = getattr(config, "CALIBRATION_ISOTONIC_BREAKPOINTS", [])
        vals   = getattr(config, "CALIBRATION_ISOTONIC_VALUES", [])
        result = isotonic_scale(p, bp, vals)
    else:
        return p

    _max = getattr(config, "MAX_GAME_HR_PROB", 0.29)
    return round(min(_max, max(0.001, result)), 4)

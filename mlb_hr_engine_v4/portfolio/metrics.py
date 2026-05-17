"""
portfolio/metrics.py — Risk-adjusted performance metrics (Session 27).

Pure math module — no data loading, no external imports.
All functions operate on plain Python lists/dicts.
"""

from __future__ import annotations

import math
from typing import Optional


# ── Core metrics ──────────────────────────────────────────────────────────────

def equity_curve(bets: list[dict]) -> list[float]:
    """
    Build equity curve from a sequence of bets.

    Args:
        bets: list of dicts with keys: 'profit_loss' (float)

    Returns:
        Running cumulative P&L list (same length as bets).
    """
    cum = 0.0
    curve = []
    for b in bets:
        cum += float(b.get("profit_loss") or 0)
        curve.append(round(cum, 4))
    return curve


def max_drawdown(curve: list[float]) -> float:
    """
    Maximum peak-to-trough drawdown on an equity curve.

    Returns:
        Drawdown as a positive float (e.g. 50.0 = lost $50 from peak).
    """
    if not curve:
        return 0.0
    peak = curve[0]
    max_dd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = peak - v
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def max_drawdown_pct(curve: list[float], starting_bankroll: float) -> float:
    """Max drawdown as percent of starting bankroll."""
    if starting_bankroll <= 0:
        return 0.0
    return round(max_drawdown(curve) / starting_bankroll * 100, 2)


def sharpe_like(pnl_series: list[float]) -> Optional[float]:
    """
    Sharpe-like ratio: mean(P&L) / std(P&L) per pick.

    Not annualized — this is a per-pick risk-adjusted return metric.
    Higher is better. >0.05 is generally good for HR prop betting.

    Returns:
        Ratio or None if insufficient data.
    """
    n = len(pnl_series)
    if n < 2:
        return None
    mean = sum(pnl_series) / n
    var  = sum((x - mean) ** 2 for x in pnl_series) / (n - 1)
    if var <= 0:
        return None
    return round(mean / math.sqrt(var), 4)


def calmar_ratio(total_roi_pct: float, max_dd_dollars: float, total_wagered: float) -> Optional[float]:
    """
    Calmar ratio: ROI% / max_drawdown%.

    Args:
        total_roi_pct: total ROI in percent
        max_dd_dollars: max drawdown in dollars
        total_wagered: total amount wagered

    Returns:
        Calmar ratio or None.
    """
    if total_wagered <= 0 or max_dd_dollars <= 0:
        return None
    max_dd_pct = max_dd_dollars / total_wagered * 100
    return round(total_roi_pct / max_dd_pct, 4)


def win_rate_wilson_ci(n: int, k: int, z: float = 1.96) -> tuple[float, float]:
    """
    Wilson score interval for binomial win rate.

    Args:
        n: total bets
        k: wins
        z: z-score (1.96 = 95% CI)

    Returns:
        (lower_bound_pct, upper_bound_pct) as percentages
    """
    if n == 0:
        return (0.0, 100.0)
    p = k / n
    z2 = z * z
    center = (p + z2 / (2 * n)) / (1 + z2 / n)
    margin = (z / (1 + z2 / n)) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    lo = max(0.0, center - margin) * 100
    hi = min(100.0, center + margin) * 100
    return (round(lo, 2), round(hi, 2))


def roi(total_profit: float, total_wagered: float) -> Optional[float]:
    """ROI in percent."""
    if total_wagered <= 0:
        return None
    return round(total_profit / total_wagered * 100, 2)


def daily_roi_series(bets: list[dict]) -> list[dict]:
    """
    Group bets by date and compute daily ROI.

    Args:
        bets: list of dicts with 'date', 'bet_dollars', 'profit_loss'

    Returns:
        List of {date, n, wagered, profit, roi_pct} sorted by date.
    """
    from collections import defaultdict
    by_date: dict[str, dict] = defaultdict(lambda: {"n": 0, "wagered": 0.0, "profit": 0.0})
    for b in bets:
        d = b.get("date", "")
        by_date[d]["n"]       += 1
        by_date[d]["wagered"] += float(b.get("bet_dollars") or 0)
        by_date[d]["profit"]  += float(b.get("profit_loss") or 0)

    result = []
    for d, v in sorted(by_date.items()):
        r = roi(v["profit"], v["wagered"])
        result.append({
            "date":    d,
            "n":       v["n"],
            "wagered": round(v["wagered"], 2),
            "profit":  round(v["profit"],  2),
            "roi_pct": r,
        })
    return result


# ── Variance decomposition ────────────────────────────────────────────────────

def variance_decomposition(bets: list[dict], group_key: str) -> dict:
    """
    Decompose variance in P&L outcomes into between-group and within-group.

    Shows how much variance is explained by a grouping variable (e.g., team, barrel_tier).

    Args:
        bets: list of dicts with 'profit_loss' and the group_key field
        group_key: field name to group by

    Returns:
        dict with: total_var, between_var, within_var, pct_between, pct_within
    """
    from collections import defaultdict

    pl_vals = [float(b.get("profit_loss") or 0) for b in bets]
    n = len(pl_vals)
    if n < 2:
        return {}

    grand_mean = sum(pl_vals) / n
    total_var  = sum((v - grand_mean) ** 2 for v in pl_vals) / (n - 1)

    groups: dict[str, list[float]] = defaultdict(list)
    for b in bets:
        k = b.get(group_key, "unknown") or "unknown"
        groups[k].append(float(b.get("profit_loss") or 0))

    # Between-group variance (weighted by group size)
    between_var = 0.0
    for vals in groups.values():
        ng   = len(vals)
        gm   = sum(vals) / ng
        between_var += ng * (gm - grand_mean) ** 2
    between_var /= (n - 1)

    within_var = total_var - between_var

    if total_var <= 0:
        return {"total_var": 0, "between_var": 0, "within_var": 0, "pct_between": 0, "pct_within": 0}

    return {
        "total_var":   round(total_var, 4),
        "between_var": round(between_var, 4),
        "within_var":  round(within_var, 4),
        "pct_between": round(between_var / total_var * 100, 1),
        "pct_within":  round(within_var  / total_var * 100, 1),
        "n_groups":    len(groups),
    }


# ── Portfolio-level metrics ────────────────────────────────────────────────────

def effective_n(n_picks: int, avg_pairwise_corr: float) -> float:
    """
    Effective number of independent bets given average pairwise correlation.

    Formula: N_eff = N / (1 + (N-1) * ρ)

    Example: N=100, ρ=0.30 → N_eff = 100 / (1 + 99*0.30) = 100 / 30.7 ≈ 3.26
    Interpretation: 100 correlated picks act like only ~3 independent bets.
    """
    if n_picks <= 0:
        return 0.0
    if avg_pairwise_corr <= 0:
        return float(n_picks)
    denom = 1.0 + (n_picks - 1) * avg_pairwise_corr
    return round(n_picks / denom, 2)


def portfolio_expected_value(bets: list[dict]) -> dict:
    """
    Compute portfolio-level EV and Kelly fractions.

    Args:
        bets: list of dicts with model_prob_pct, american_odds, ev_pct, bet_dollars

    Returns:
        dict with total_ev, avg_ev_pct, total_wagered, expected_profit
    """
    ev_sum    = 0.0
    ev_vals   = []
    wagered   = 0.0
    exp_profit = 0.0

    for b in bets:
        ev_pct   = float(b.get("ev_pct") or 0)
        bet_d    = float(b.get("bet_dollars") or 0)
        odds     = float(b.get("american_odds") or 100)
        prob     = float(b.get("model_prob_pct") or 0) / 100.0

        # Expected P&L for this pick
        if odds >= 100:
            profit_mult = odds / 100.0
        else:
            profit_mult = 100.0 / abs(odds) if odds < 0 else 1.0

        pick_ev = bet_d * (prob * profit_mult - (1 - prob))
        exp_profit += pick_ev

        ev_sum  += ev_pct
        ev_vals.append(ev_pct)
        wagered += bet_d

    n = len(bets)
    avg_ev = ev_sum / n if n > 0 else 0.0

    return {
        "n":             n,
        "avg_ev_pct":    round(avg_ev, 3),
        "total_wagered": round(wagered, 2),
        "expected_profit": round(exp_profit, 2),
        "expected_roi_pct": round(exp_profit / wagered * 100, 2) if wagered > 0 else None,
    }


def kelly_optimal_fraction(win_prob: float, decimal_profit_mult: float) -> float:
    """
    Full Kelly fraction. Positive = bet; negative = bet the other side.

    Kelly formula: f* = (b*p - q) / b
      b = profit multiplier on win
      p = win probability
      q = 1 - p = loss probability
    """
    q = 1.0 - win_prob
    b = decimal_profit_mult
    if b <= 0:
        return 0.0
    f = (b * win_prob - q) / b
    return max(0.0, f)

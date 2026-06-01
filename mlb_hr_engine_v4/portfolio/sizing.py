"""
portfolio/sizing.py — Bet sizing strategies and backtesting (Session 27).

Implements multiple sizing approaches and backtests them on settled pick data.

Sizing strategies:
  1. Flat            — constant $X per pick regardless of edge
  2. QuarterKelly    — 0.25 × Kelly fraction (current system)
  3. HalfKelly       — 0.50 × Kelly fraction (more aggressive)
  4. CappedKelly     — Kelly fraction capped at MAX_BET_PCT of bankroll
  5. ConfidenceFlat  — flat × (confidence / avg_confidence)
  6. EdgeWeighted    — flat × (edge_pct / avg_edge_pct), capped at 3×
  7. EVWeighted      — flat × (ev_pct / avg_ev_pct), capped at 3×
  8. BarrelKelly     — Kelly × barrel_quality_multiplier

Key insight: With n=619 picks across only 2 dates, sizing strategy differences are primarily
driven by bet distribution shape (few large bets vs many small bets), not genuine edge
differences. All conclusions are directional at this sample size.
"""

from __future__ import annotations

import math
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────
FLAT_BET       = 10.0      # base flat bet size in dollars
MAX_BET_MULT   = 3.0       # max multiplier for weighted sizing
MIN_BET        = 1.0       # minimum bet floor
BANKROLL_START = 100.0     # reference bankroll for Kelly calculations


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(str(v).strip()) if v is not None and str(v).strip() != "" else default
    except (ValueError, TypeError):
        return default


def _american_to_profit_mult(american_odds: float) -> float:
    """Return profit multiplier (not decimal odds). Win this × bet size if winner."""
    if american_odds >= 100:
        return american_odds / 100.0
    else:
        return 100.0 / abs(american_odds) if american_odds < 0 else 1.0


def _kelly_fraction(win_prob: float, profit_mult: float) -> float:
    """Full Kelly fraction f = (b*p - q) / b."""
    q = 1.0 - win_prob
    b = profit_mult
    if b <= 0 or win_prob <= 0:
        return 0.0
    f = (b * win_prob - q) / b
    return max(0.0, f)


def _compute_pl(bet: float, odds: float, hit: int) -> float:
    """Compute P&L for one pick."""
    if hit == 1:
        return bet * _american_to_profit_mult(odds)
    return -bet


# ── Sizing strategy functions ──────────────────────────────────────────────────
# Each returns bet_dollars for a given pick row.

def size_flat(row: dict, context: dict) -> float:
    """Flat $FLAT_BET per pick."""
    return FLAT_BET


def size_quarter_kelly(row: dict, context: dict) -> float:
    """
    Quarter-Kelly (current system).
    Uses existing bet_dollars if available, otherwise recomputes.
    """
    existing = _safe_float(row.get("bet_dollars"))
    if existing > 0:
        return existing
    # Recompute
    prob  = _safe_float(row.get("model_prob_pct")) / 100.0
    odds  = _safe_float(row.get("american_odds") or row.get("best_odds"), 100)
    pmult = _american_to_profit_mult(odds)
    fk    = _kelly_fraction(prob, pmult)
    bet   = 0.25 * fk * context.get("bankroll", BANKROLL_START)
    return max(MIN_BET, min(bet, context.get("bankroll", BANKROLL_START) * 0.05))


def size_half_kelly(row: dict, context: dict) -> float:
    """Half-Kelly — more aggressive than current quarter-Kelly."""
    prob  = _safe_float(row.get("model_prob_pct")) / 100.0
    odds  = _safe_float(row.get("american_odds") or row.get("best_odds"), 100)
    pmult = _american_to_profit_mult(odds)
    fk    = _kelly_fraction(prob, pmult)
    bet   = 0.50 * fk * context.get("bankroll", BANKROLL_START)
    return max(MIN_BET, min(bet, context.get("bankroll", BANKROLL_START) * 0.08))


def size_full_kelly(row: dict, context: dict) -> float:
    """Full Kelly — aggressive, maximum theoretical growth rate."""
    prob  = _safe_float(row.get("model_prob_pct")) / 100.0
    odds  = _safe_float(row.get("american_odds") or row.get("best_odds"), 100)
    pmult = _american_to_profit_mult(odds)
    fk    = _kelly_fraction(prob, pmult)
    bet   = fk * context.get("bankroll", BANKROLL_START)
    return max(MIN_BET, min(bet, context.get("bankroll", BANKROLL_START) * 0.15))


def size_capped_kelly(row: dict, context: dict) -> float:
    """
    Capped Kelly: quarter-Kelly sized, but hard max cap of $MAX_SINGLE_BET.
    Prevents single large bets from dominating bankroll.
    """
    bet     = size_quarter_kelly(row, context)
    max_bet = context.get("max_single_bet", FLAT_BET * 2.5)
    return max(MIN_BET, min(bet, max_bet))


def size_confidence_flat(row: dict, context: dict) -> float:
    """
    Flat × (confidence / avg_confidence), capped at MAX_BET_MULT × flat.
    Bets more on high-confidence picks, less on low-confidence.
    """
    conf     = _safe_float(row.get("confidence"))
    avg_conf = context.get("avg_confidence", 50.0)
    if avg_conf <= 0 or conf <= 0:
        return FLAT_BET
    mult = min(MAX_BET_MULT, conf / avg_conf)
    return max(MIN_BET, FLAT_BET * mult)


def size_edge_weighted(row: dict, context: dict) -> float:
    """
    Flat × (edge_pct / avg_edge_pct), capped at MAX_BET_MULT × flat.
    Bets more on high-edge picks.
    """
    edge     = _safe_float(row.get("edge_pct"))
    avg_edge = context.get("avg_edge_pct", 3.0)
    if avg_edge <= 0 or edge <= 0:
        return FLAT_BET
    mult = min(MAX_BET_MULT, edge / avg_edge)
    return max(MIN_BET, FLAT_BET * mult)


def size_ev_weighted(row: dict, context: dict) -> float:
    """
    Flat × (ev_pct / avg_ev_pct), capped at MAX_BET_MULT × flat.
    Bets more on high-EV picks.
    """
    ev      = _safe_float(row.get("ev_pct"))
    avg_ev  = context.get("avg_ev_pct", 5.0)
    if avg_ev <= 0 or ev <= 0:
        return FLAT_BET
    mult = min(MAX_BET_MULT, ev / avg_ev)
    return max(MIN_BET, FLAT_BET * mult)


def size_barrel_kelly(row: dict, context: dict) -> float:
    """
    Quarter-Kelly base × barrel quality multiplier.
    Elite barrel picks (≥10%) get up to 1.5× sizing; low barrel (<6%) get 0.5×.
    Reward pick quality with proportionally larger bets.
    """
    base   = size_quarter_kelly(row, context)
    barrel = _safe_float(row.get("barrel_pct"))
    if barrel >= 10:   mult = 1.50
    elif barrel >= 8:  mult = 1.25
    elif barrel >= 6:  mult = 1.00
    elif barrel >= 4:  mult = 0.75
    else:              mult = 0.50
    return max(MIN_BET, base * mult)


# ── Strategy registry ─────────────────────────────────────────────────────────

STRATEGIES = {
    "flat":              (size_flat,            "Flat $10 — constant sizing regardless of edge"),
    "quarter_kelly":     (size_quarter_kelly,   "Quarter-Kelly — current system (0.25 × Kelly)"),
    "half_kelly":        (size_half_kelly,      "Half-Kelly — 2× more aggressive than current"),
    "full_kelly":        (size_full_kelly,      "Full Kelly — maximum theoretical growth (aggressive)"),
    "capped_kelly":      (size_capped_kelly,    "Capped Kelly — quarter-Kelly with hard max per pick"),
    "confidence_flat":   (size_confidence_flat, "Confidence-weighted flat — bet more on high-confidence picks"),
    "edge_weighted":     (size_edge_weighted,   "Edge-weighted flat — bet more on high-edge picks"),
    "ev_weighted":       (size_ev_weighted,     "EV-weighted flat — bet more on high-EV picks"),
    "barrel_kelly":      (size_barrel_kelly,    "Barrel-Kelly — Kelly × barrel quality tier multiplier"),
}


# ── Backtesting ───────────────────────────────────────────────────────────────

def backtest_strategy(
    rows: list[dict],
    strategy_name: str,
    bankroll: float = BANKROLL_START,
    max_single_bet: Optional[float] = None,
) -> dict:
    """
    Backtest a single sizing strategy on settled pick rows.

    Args:
        rows: settled pick_tracker rows (hr_result in {0, 1})
        strategy_name: key in STRATEGIES dict
        bankroll: starting bankroll
        max_single_bet: hard cap per bet (default: bankroll * 0.05)

    Returns:
        Performance dict with ROI, drawdown, Sharpe, etc.
    """
    from .metrics import equity_curve, max_drawdown, sharpe_like, win_rate_wilson_ci

    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Valid: {list(STRATEGIES)}")

    size_fn, description = STRATEGIES[strategy_name]

    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if not settled:
        return {"strategy": strategy_name, "n": 0, "error": "no settled rows"}

    # Precompute context stats
    confidences = [_safe_float(r.get("confidence")) for r in settled if _safe_float(r.get("confidence")) > 0]
    edges       = [_safe_float(r.get("edge_pct")) for r in settled if _safe_float(r.get("edge_pct")) > 0]
    evs         = [_safe_float(r.get("ev_pct")) for r in settled if _safe_float(r.get("ev_pct")) > 0]

    context = {
        "bankroll":       bankroll,
        "max_single_bet": max_single_bet or bankroll * 0.05,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 50.0,
        "avg_edge_pct":   sum(edges) / len(edges) if edges else 3.0,
        "avg_ev_pct":     sum(evs) / len(evs) if evs else 5.0,
    }

    bets_log = []
    total_wagered = 0.0
    total_profit  = 0.0
    wins = 0

    for row in settled:
        bet  = size_fn(row, context)
        bet  = round(max(MIN_BET, bet), 2)
        odds = _safe_float(row.get("american_odds") or row.get("best_odds"), 100)
        hit  = int(row.get("hr_result", "0"))
        pl   = _compute_pl(bet, odds, hit)

        total_wagered += bet
        total_profit  += pl
        if hit:
            wins += 1

        bets_log.append({"date": row.get("date",""), "bet_dollars": bet, "profit_loss": pl})

    n = len(settled)
    roi_pct = total_profit / total_wagered * 100 if total_wagered > 0 else None

    curve  = equity_curve(bets_log)
    max_dd = max_drawdown(curve)
    sl     = sharpe_like([b["profit_loss"] for b in bets_log])
    ci_lo, ci_hi = win_rate_wilson_ci(n, wins)

    calmar = abs(roi_pct / (max_dd / total_wagered * 100)) if max_dd > 0 and roi_pct and total_wagered > 0 else None

    # Daily breakdown
    from collections import defaultdict
    daily: dict[str, dict] = defaultdict(lambda: {"wagered": 0.0, "profit": 0.0, "n": 0})
    for b in bets_log:
        d = b["date"]
        daily[d]["wagered"] += b["bet_dollars"]
        daily[d]["profit"]  += b["profit_loss"]
        daily[d]["n"]       += 1

    daily_rois = [v["profit"] / v["wagered"] * 100 for v in daily.values() if v["wagered"] > 0]
    avg_daily_roi = sum(daily_rois) / len(daily_rois) if daily_rois else None

    return {
        "strategy":        strategy_name,
        "description":     description,
        "n":               n,
        "wins":            wins,
        "win_rate_pct":    round(wins / n * 100, 2),
        "win_rate_ci":     (ci_lo, ci_hi),
        "total_wagered":   round(total_wagered, 2),
        "total_profit":    round(total_profit, 2),
        "roi_pct":         round(roi_pct, 2) if roi_pct is not None else None,
        "avg_bet":         round(total_wagered / n, 2),
        "max_bet":         round(max(b["bet_dollars"] for b in bets_log), 2) if bets_log else 0,
        "max_drawdown":    round(max_dd, 2),
        "max_dd_pct":      round(max_dd / total_wagered * 100, 2) if total_wagered > 0 else None,
        "sharpe":          sl,
        "calmar":          round(calmar, 4) if calmar is not None else None,
        "final_equity":    round(curve[-1] if curve else 0, 2),
        "avg_daily_roi":   round(avg_daily_roi, 2) if avg_daily_roi is not None else None,
        "equity_curve":    curve,
    }


def backtest_all_strategies(rows: list[dict], bankroll: float = BANKROLL_START) -> list[dict]:
    """
    Run all strategies and return sorted by ROI.

    Args:
        rows: settled pick_tracker rows
        bankroll: starting bankroll

    Returns:
        List of result dicts sorted by roi_pct descending.
    """
    results = []
    for name in STRATEGIES:
        try:
            r = backtest_strategy(rows, name, bankroll=bankroll)
            results.append(r)
        except Exception as e:
            results.append({"strategy": name, "error": str(e)})

    return sorted(
        [r for r in results if r.get("roi_pct") is not None],
        key=lambda x: x["roi_pct"],
        reverse=True,
    )


def sizing_sensitivity(rows: list[dict]) -> dict:
    """
    Sensitivity analysis: how does ROI change with Kelly fraction?

    Tests Kelly fractions from 0.10 to 1.0 in 0.10 steps.
    Returns the fraction that maximizes risk-adjusted return (Sharpe, not raw ROI).
    """
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if len(settled) < 10:
        return {}

    from .metrics import equity_curve, max_drawdown, sharpe_like

    context_base = {
        "avg_confidence": 50.0,
        "avg_edge_pct":   3.0,
        "avg_ev_pct":     5.0,
    }

    results = []
    for frac in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]:
        total_w = 0.0
        total_p = 0.0
        pls     = []
        for r in settled:
            prob  = _safe_float(r.get("model_prob_pct")) / 100.0
            odds  = _safe_float(r.get("american_odds") or r.get("best_odds"), 100)
            pmult = _american_to_profit_mult(odds)
            fk    = _kelly_fraction(prob, pmult)
            bet   = max(MIN_BET, min(frac * fk * BANKROLL_START, BANKROLL_START * 0.20))
            hit   = int(r.get("hr_result", 0))
            pl    = _compute_pl(bet, odds, hit)
            total_w += bet
            total_p += pl
            pls.append(pl)

        roi = total_p / total_w * 100 if total_w > 0 else None
        curve = equity_curve([{"profit_loss": p} for p in pls])
        dd = max_drawdown(curve)
        sl = sharpe_like(pls)
        results.append({
            "fraction": frac,
            "roi_pct":  round(roi, 2) if roi else None,
            "max_dd":   round(dd, 2),
            "sharpe":   sl,
        })

    best_sharpe = max(
        [r for r in results if r.get("sharpe") is not None],
        key=lambda x: x["sharpe"],
        default=None,
    )

    return {
        "results":       results,
        "best_by_sharpe": best_sharpe,
        "current":       next((r for r in results if r["fraction"] == 0.25), None),
    }

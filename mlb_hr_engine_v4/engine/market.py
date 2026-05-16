"""
Market odds math: conversions, vig removal, break-even.
All probabilities are 0.0–1.0 fractions.
"""

from typing import Sequence

import config


# ── Conversions ───────────────────────────────────────────────────────────────

def american_to_decimal(american: int) -> float:
    """Convert American moneyline odds to decimal (European) format."""
    if american > 0:
        return american / 100.0 + 1.0
    if not american:
        return 1.01  # treat 0 as near-certain favourite rather than crashing
    return 100.0 / abs(american) + 1.0


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American moneyline."""
    if decimal >= 2.0:
        return int(round((decimal - 1) * 100))
    return int(round(-100 / (decimal - 1)))


def implied_prob(american: int) -> float:
    """Raw (vigged) implied probability from American odds."""
    dec = american_to_decimal(american)
    return 1.0 / dec


def break_even_prob(american: int) -> float:
    """Minimum win rate to profit at these odds (same as implied_prob)."""
    return implied_prob(american)


# ── Vig Removal ───────────────────────────────────────────────────────────────

def no_vig_prob_two_sided(over_american: int, under_american: int) -> tuple[float, float]:
    """
    Remove vig from a standard two-sided market.
    Returns (no_vig_over, no_vig_under).
    """
    p_over = implied_prob(over_american)
    p_under = implied_prob(under_american)
    total = p_over + p_under
    return p_over / total, p_under / total


def no_vig_prob_one_sided(prices: Sequence[int], vig_factor: float = None) -> float:
    """
    Remove vig from a one-sided market (HR yes only, no listed 'no HR' line).
    Strategy: use the best-available price and back out the vig.

    vig_factor defaults to config.VIG_FACTOR (empirically measured on FanDuel/DraftKings
    HR props). Retail sportsbooks charge 7-10% on player props vs ~4.5% on sides/totals.
    Using the correct vig is critical: understating it inflates the no-vig prob,
    which deflates our edge and hides real +EV plays.
    """
    if not prices:
        return 0.0
    vf = vig_factor if vig_factor is not None else config.VIG_FACTOR
    # Best price for bettor = highest payout = lowest implied probability
    best_implied = min(implied_prob(p) for p in prices)
    return best_implied / (1.0 + vf)


def consensus_no_vig(prices: Sequence[int], vig_factor: float = None) -> float:
    """Average implied probability across books, then remove vig."""
    if not prices:
        return 0.0
    vf = vig_factor if vig_factor is not None else config.VIG_FACTOR
    avg = sum(implied_prob(p) for p in prices) / len(prices)
    return avg / (1.0 + vf)


# ── Market Summary ────────────────────────────────────────────────────────────

def market_summary(prices: Sequence[int]) -> dict:
    """
    Summarize market across all available books.
    Returns: best_price, worst_price, consensus_no_vig_prob, best_no_vig_prob.
    """
    if not prices:
        return {}
    return {
        "best_american": max(prices),
        "worst_american": min(prices),
        "best_decimal": american_to_decimal(max(prices)),
        "implied_prob_avg": sum(implied_prob(p) for p in prices) / len(prices),
        "no_vig_prob_consensus": consensus_no_vig(prices),
        "no_vig_prob_best": no_vig_prob_one_sided(prices),
        "n_books": len(prices),
    }


def market_summary_dynamic(prices_by_book: dict[str, int]) -> dict:
    """
    Enhanced market summary using per-book vig from engine.vig.

    Args:
        prices_by_book: {bookmaker_key: best_american_odds} from pipeline

    Returns all fixed-vig keys plus:
        no_vig_prob_dynamic: consensus probability using per-book vig
        no_vig_prob_fixed:   consensus probability using global VIG_FACTOR (for comparison)
        vig_by_book:         {book: vig_fraction} actually applied
        sharpest_book:       book with lowest estimated vig
        vig_delta:           dynamic minus fixed (positive = dynamic is more conservative)
    """
    if not prices_by_book:
        return {}

    from engine import vig as vig_model  # local import avoids circular dependency

    prices = list(prices_by_book.values())
    base = market_summary(prices)   # backward-compatible fixed-vig values

    dyn_prob, sharpest, vig_by_book = vig_model.consensus_no_vig_dynamic(prices_by_book)
    fixed_prob = base.get("no_vig_prob_consensus", 0.0)

    base.update({
        "no_vig_prob_dynamic": dyn_prob,
        "no_vig_prob_fixed":   fixed_prob,
        "vig_by_book":         vig_by_book,
        "sharpest_book":       sharpest,
        "vig_delta":           round(dyn_prob - fixed_prob, 5),
    })
    return base

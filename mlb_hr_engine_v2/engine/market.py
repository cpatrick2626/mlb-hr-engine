"""
Market odds math: conversions, vig removal, break-even.
All probabilities are 0.0–1.0 fractions.
"""

from typing import Sequence


# ── Conversions ───────────────────────────────────────────────────────────────

def american_to_decimal(american: int) -> float:
    """Convert American moneyline odds to decimal (European) format."""
    if american > 0:
        return american / 100.0 + 1.0
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


def no_vig_prob_one_sided(prices: Sequence[int], vig_factor: float = 0.045) -> float:
    """
    Remove vig from a one-sided market (HR yes only, no listed 'no HR' line).
    Strategy: use the consensus best-available price and back out a ~4.5% vig.

    vig_factor 0.045 ≈ typical juice on MLB player props.
    """
    if not prices:
        return 0.0
    # Best price for bettor = lowest implied probability = highest payout odds
    best_implied = min(implied_prob(p) for p in prices)
    return best_implied / (1.0 + vig_factor)


def consensus_no_vig(prices: Sequence[int], vig_factor: float = 0.045) -> float:
    """Average implied probability across books, then remove vig."""
    if not prices:
        return 0.0
    avg = sum(implied_prob(p) for p in prices) / len(prices)
    return avg / (1.0 + vig_factor)


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

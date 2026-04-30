"""
Expected Value and edge calculations.
"""

from engine.market import american_to_decimal, implied_prob


def expected_value_pct(model_prob: float, decimal_odds: float) -> float:
    """
    EV% = [p × (d − 1) − (1 − p)] × 100
    Where d = decimal odds, p = true win probability.

    Positive EV% means a +expectation bet.
    """
    ev = model_prob * (decimal_odds - 1.0) - (1.0 - model_prob)
    return round(ev * 100.0, 2)


def edge_pct(model_prob: float, no_vig_market_prob: float) -> float:
    """
    Edge% = (model_prob − market_no_vig_prob) × 100

    Positive = model says this batter is underpriced.
    """
    return round((model_prob - no_vig_market_prob) * 100.0, 2)


def roi_over_n(ev_pct: float, n_bets: int = 100) -> float:
    """
    Expected total ROI% if you placed n identical bets at this EV.
    (Compounding ignored for simplicity.)
    """
    return round(ev_pct * n_bets / 100.0, 2)


def implied_edge_american(model_prob: float, american_odds: int) -> float:
    """Edge expressed relative to the American odds implied probability."""
    return edge_pct(model_prob, implied_prob(american_odds))

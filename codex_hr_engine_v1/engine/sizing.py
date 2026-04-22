"""
Bet sizing via Kelly Criterion.

Full Kelly: f* = (b·p − q) / b
  b = net fractional odds (decimal − 1)
  p = model win probability
  q = 1 − p

We default to Quarter-Kelly (KELLY_FRACTION = 0.25) to account for
model uncertainty and variance in the HR rate estimate.
"""

import config
from engine.market import american_to_decimal


def kelly(model_prob: float, decimal_odds: float) -> float:
    """Full Kelly fraction (of bankroll)."""
    b = decimal_odds - 1.0
    if b <= 0 or model_prob <= 0:
        return 0.0
    q = 1.0 - model_prob
    f = (b * model_prob - q) / b
    return max(0.0, f)


def fractional_kelly(model_prob: float, decimal_odds: float) -> float:
    """Scaled Kelly (config.KELLY_FRACTION × full Kelly)."""
    return kelly(model_prob, decimal_odds) * config.KELLY_FRACTION


def bet_dollars(
    model_prob: float,
    american_odds: int,
    bankroll: float = None,
) -> float:
    """
    Recommended bet in dollars.
    Applies fractional Kelly and caps at MAX_BET_PCT of bankroll.
    """
    if bankroll is None:
        bankroll = config.BANKROLL

    dec = american_to_decimal(american_odds)
    fk = fractional_kelly(model_prob, dec)
    raw = fk * bankroll
    cap = config.MAX_BET_PCT * bankroll
    bet = min(raw, cap)

    if bet < config.MIN_BET_DOLLARS:
        return 0.0  # Not worth placing
    return round(bet, 2)


def kelly_summary(model_prob: float, american_odds: int, bankroll: float = None) -> dict:
    """Full sizing breakdown for display."""
    if bankroll is None:
        bankroll = config.BANKROLL
    dec = american_to_decimal(american_odds)
    fk = kelly(model_prob, dec)
    scaled = fk * config.KELLY_FRACTION
    dollars = bet_dollars(model_prob, american_odds, bankroll)
    return {
        "full_kelly_pct": round(fk * 100, 2),
        "fractional_kelly_pct": round(scaled * 100, 2),
        "bet_dollars": dollars,
        "kelly_fraction_used": config.KELLY_FRACTION,
    }

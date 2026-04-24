"""
Hedge Betting Strategy

Calculate optimal hedge bets to guarantee profit or minimize loss
on existing positions.
"""

from typing import Dict, List, Optional, Tuple
import math


def calculate_hedge_bet(
    original_stake: float,
    original_odds: int,  # American odds
    hedge_odds: int,  # American odds for opposite outcome
    target_profit: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate optimal hedge bet amount.

    Args:
        original_stake: Amount bet on original position
        original_odds: American odds of original bet
        hedge_odds: Current odds for opposite outcome
        target_profit: Desired guaranteed profit (None = break even)

    Returns:
        Dict with hedge amount and guaranteed outcomes
    """
    # Convert to decimal odds
    orig_decimal = american_to_decimal(original_odds)
    hedge_decimal = american_to_decimal(hedge_odds)

    # Calculate original payout
    original_payout = original_stake * orig_decimal

    if target_profit is None:
        # Break-even hedge
        hedge_stake = original_stake
        guaranteed = 0
    else:
        # Target profit hedge
        # hedge_stake * hedge_decimal = original_stake + target_profit
        hedge_stake = (original_stake + target_profit) / hedge_decimal
        guaranteed = target_profit

    # Calculate profit in each scenario
    if_original_wins = original_payout - original_stake - hedge_stake
    if_hedge_wins = (hedge_stake * hedge_decimal) - hedge_stake - original_stake

    return {
        "hedge_stake": round(hedge_stake, 2),
        "total_risk": round(original_stake + hedge_stake, 2),
        "if_original_wins": round(if_original_wins, 2),
        "if_hedge_wins": round(if_hedge_wins, 2),
        "guaranteed_profit": round(min(if_original_wins, if_hedge_wins), 2),
        "hedge_roi": round(
            (min(if_original_wins, if_hedge_wins) / (original_stake + hedge_stake)) * 100, 1
        ),
    }


def find_hedge_opportunities(
    active_bets: List[dict],
    current_odds: Dict[str, int],
    min_profit_pct: float = 5.0
) -> List[dict]:
    """
    Find profitable hedge opportunities from active bets.

    Args:
        active_bets: List of active bet dicts
        current_odds: Current market odds for all players
        min_profit_pct: Minimum profit percentage to flag

    Returns:
        List of hedge opportunities
    """
    opportunities = []

    for bet in active_bets:
        player = bet["player_name"]
        original_odds = bet["american_odds"]
        original_stake = bet["bet_amount"]

        # Check if current odds have moved enough to create value
        if player in current_odds:
            current = current_odds[player]

            # Calculate if hedging the opposite creates value
            # For HR bets, the opposite is "No HR"
            no_hr_odds = calculate_no_hr_odds(current)

            hedge_calc = calculate_hedge_bet(
                original_stake,
                original_odds,
                no_hr_odds,
                target_profit=original_stake * (min_profit_pct / 100)
            )

            if hedge_calc["guaranteed_profit"] > 0:
                opportunities.append({
                    "player": player,
                    "original_bet": bet,
                    "hedge_calculation": hedge_calc,
                    "current_hr_odds": current,
                    "no_hr_odds": no_hr_odds,
                    "action": f"Hedge ${hedge_calc['hedge_stake']:.2f} on No HR",
                    "guaranteed": hedge_calc["guaranteed_profit"],
                })

    return sorted(opportunities, key=lambda x: x["guaranteed"], reverse=True)


def calculate_no_hr_odds(hr_american_odds: int) -> int:
    """
    Calculate implied No HR odds from HR odds.
    Includes estimated vig.
    """
    hr_decimal = american_to_decimal(hr_american_odds)
    hr_implied = 1.0 / hr_decimal

    # No HR probability
    no_hr_prob = 1 - hr_implied

    # Add vig (typically 5-10% for HR markets)
    no_hr_prob_with_vig = no_hr_prob * 0.93

    # Convert back to American odds
    no_hr_decimal = 1.0 / no_hr_prob_with_vig
    return decimal_to_american(no_hr_decimal)


def calculate_middle_opportunity(
    odds1: int,
    odds2: int,
    stake: float = 100
) -> Dict[str, float]:
    """
    Calculate if there's a middle betting opportunity between two books.

    A middle occurs when you can bet both sides with positive EV.
    """
    dec1 = american_to_decimal(odds1)
    dec2 = american_to_decimal(odds2)

    # Check if sum of implied probabilities < 100%
    implied1 = 1.0 / dec1
    implied2 = 1.0 / dec2

    total_implied = implied1 + implied2

    if total_implied < 1.0:
        # Arbitrage opportunity exists
        # Calculate optimal stakes
        stake1 = stake * (1 / dec1) / total_implied
        stake2 = stake * (1 / dec2) / total_implied

        profit = stake - (stake1 + stake2)

        return {
            "is_middle": True,
            "book1_stake": round(stake1, 2),
            "book2_stake": round(stake2, 2),
            "total_stake": round(stake1 + stake2, 2),
            "guaranteed_profit": round(profit, 2),
            "roi_pct": round((profit / (stake1 + stake2)) * 100, 2),
        }

    return {"is_middle": False}


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal."""
    if american >= 100:
        return (american / 100.0) + 1
    else:
        return (100.0 / abs(american)) + 1


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American."""
    if decimal >= 2.0:
        return int((decimal - 1) * 100)
    else:
        return int(-100 / (decimal - 1))
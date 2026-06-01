"""
Progressive Staking Systems

Alternative staking strategies to Kelly Criterion, including:
- Fibonacci sequence
- D'Alembert system
- Oscar's Grind
- Streak-adjusted staking
"""

from typing import Dict, List, Optional
import math


def fibonacci_stake(
    base_unit: float,
    loss_streak: int,
    bankroll: float,
    max_pct: float = 0.05
) -> float:
    """
    Fibonacci staking system.

    After a loss, move to the next Fibonacci number.
    After a win, move back two numbers.

    Args:
        base_unit: Base betting unit (e.g., $10)
        loss_streak: Current consecutive losses
        bankroll: Total bankroll
        max_pct: Maximum percentage of bankroll to bet

    Returns:
        Stake amount
    """
    fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    # Get position in sequence based on loss streak
    position = min(loss_streak, len(fib_sequence) - 1)
    fib_multiplier = fib_sequence[position]

    stake = base_unit * fib_multiplier

    # Cap at max percentage of bankroll
    max_stake = bankroll * max_pct
    return min(stake, max_stake)


def dalembert_stake(
    base_unit: float,
    wins: int,
    losses: int,
    bankroll: float,
    max_pct: float = 0.05
) -> float:
    """
    D'Alembert staking system.

    Increase stake by one unit after a loss, decrease after a win.
    More conservative than Martingale.

    Args:
        base_unit: Base betting unit
        wins: Total wins in session
        losses: Total losses in session
        bankroll: Total bankroll
        max_pct: Maximum percentage of bankroll

    Returns:
        Stake amount
    """
    net_losses = losses - wins
    units = max(1, 1 + net_losses)

    stake = base_unit * units

    # Cap at max percentage
    max_stake = bankroll * max_pct
    return min(stake, max_stake)


def oscar_grind_stake(
    base_unit: float,
    session_profit: float,
    current_streak_type: str,  # "win" or "loss"
    streak_length: int,
    bankroll: float,
    max_pct: float = 0.05
) -> float:
    """
    Oscar's Grind staking system.

    Goal: Win 1 unit per session.
    - Keep stake same after losses
    - Increase by 1 unit after wins (until session goal met)

    Args:
        base_unit: Base betting unit
        session_profit: Current session P&L
        current_streak_type: "win" or "loss"
        streak_length: Length of current streak
        bankroll: Total bankroll
        max_pct: Maximum percentage of bankroll

    Returns:
        Stake amount
    """
    if session_profit >= base_unit:
        # Session goal met, reset to base
        return base_unit

    if current_streak_type == "loss":
        # Keep same stake during losing streaks
        units = 1
    else:
        # Increase by 1 unit per win in winning streak
        units = min(streak_length + 1, 4)  # Cap at 4 units

    stake = base_unit * units

    # If this bet would exceed session goal, reduce it
    if stake > base_unit - session_profit:
        stake = base_unit - session_profit

    # Cap at max percentage
    max_stake = bankroll * max_pct
    return max(base_unit, min(stake, max_stake))


def calculate_streak_adjusted_stake(
    base_stake: float,
    hot_streak: int,
    cold_streak: int,
    model_confidence: float,
    bankroll: float
) -> float:
    """
    Adjust stake based on recent hot/cold streaks.

    Theory: Streaks indicate either good model calibration or
    temporary market inefficiency.

    Args:
        base_stake: Kelly or other base stake
        hot_streak: Consecutive wins
        cold_streak: Consecutive losses
        model_confidence: Model confidence (0-100)
        bankroll: Total bankroll

    Returns:
        Adjusted stake amount
    """
    multiplier = 1.0

    if hot_streak > 0:
        # On hot streak - increase stake carefully
        # But watch for regression to mean
        if hot_streak <= 3:
            multiplier = 1 + (hot_streak * 0.1)  # 10% per win
        elif hot_streak <= 5:
            multiplier = 1.3  # Cap gains
        else:
            # Long streak - might be due for regression
            multiplier = 1.2

    elif cold_streak > 0:
        # On cold streak - decrease stake
        # But look for value as odds might adjust
        if cold_streak <= 3:
            multiplier = 1 - (cold_streak * 0.15)  # 15% per loss
        elif cold_streak <= 5:
            multiplier = 0.55
        else:
            # Deep cold - minimum stake only
            multiplier = 0.25

    # Adjust for model confidence
    if model_confidence > 75:
        multiplier *= 1.1
    elif model_confidence < 40:
        multiplier *= 0.8

    adjusted_stake = base_stake * multiplier

    # Bounds checking
    min_stake = bankroll * 0.001  # 0.1% minimum
    max_stake = bankroll * 0.05   # 5% maximum

    return max(min_stake, min(adjusted_stake, max_stake))


def dynamic_kelly_fraction(
    base_fraction: float,
    recent_roi: float,
    sample_size: int,
    volatility: float
) -> float:
    """
    Dynamically adjust Kelly fraction based on recent performance.

    Args:
        base_fraction: Starting Kelly fraction (e.g., 0.25)
        recent_roi: ROI over last N bets
        sample_size: Number of recent bets
        volatility: Standard deviation of recent returns

    Returns:
        Adjusted Kelly fraction
    """
    # Start with base
    adjusted = base_fraction

    # Adjust for recent performance
    if sample_size >= 20:
        if recent_roi > 0.1:  # 10%+ ROI
            adjusted *= 1.2
        elif recent_roi > 0.05:  # 5-10% ROI
            adjusted *= 1.1
        elif recent_roi < -0.1:  # -10% or worse
            adjusted *= 0.7
        elif recent_roi < -0.05:  # -5% to -10%
            adjusted *= 0.85

    # Adjust for volatility
    if volatility > 0.5:  # High volatility
        adjusted *= 0.8
    elif volatility < 0.2:  # Low volatility
        adjusted *= 1.1

    # Bounds
    return max(0.1, min(adjusted, 0.35))


def calculate_unit_size(
    bankroll: float,
    risk_tolerance: str = "moderate"  # "conservative", "moderate", "aggressive"
) -> float:
    """
    Calculate base unit size based on bankroll and risk tolerance.

    Args:
        bankroll: Total bankroll
        risk_tolerance: Risk profile

    Returns:
        Base unit size
    """
    percentages = {
        "conservative": 0.01,   # 1% of bankroll
        "moderate": 0.02,       # 2% of bankroll
        "aggressive": 0.03,     # 3% of bankroll
    }

    pct = percentages.get(risk_tolerance, 0.02)
    return bankroll * pct


def confidence_weighted_stake(
    model_confidence: float,
    edge_pct: float,
    base_stake: float
) -> float:
    """
    Weight stake by model confidence and edge size.

    Higher confidence + higher edge = larger stake.

    Args:
        model_confidence: 0-100 confidence score
        edge_pct: Percentage edge over market
        base_stake: Base stake amount

    Returns:
        Weighted stake
    """
    # Convert confidence to 0-1 scale
    conf_weight = model_confidence / 100.0

    # Edge weight (sigmoid function for smooth scaling)
    edge_weight = 1 / (1 + math.exp(-edge_pct / 5))

    # Combined weight (average of the two)
    combined_weight = (conf_weight + edge_weight) / 2

    # Scale from 0.5x to 1.5x base stake
    multiplier = 0.5 + combined_weight

    return base_stake * multiplier
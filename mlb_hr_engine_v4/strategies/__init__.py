"""
Advanced Betting Strategies Module

Provides sophisticated betting strategies beyond basic Kelly criterion:
- Correlation-based parlays
- Hedge betting calculations
- Stack betting (same-team parlays)
- Arbitrage opportunity detection
- Progressive staking systems
- Value decay tracking
"""

from .correlation import find_correlated_parlays, analyze_historical_correlation
from .hedge import calculate_hedge_bet, find_hedge_opportunities
from .stacks import build_team_stacks, evaluate_stack
from .arbitrage import find_arbitrage_bets, calculate_arbitrage_profit
from .staking import (
    fibonacci_stake,
    dalembert_stake,
    oscar_grind_stake,
    calculate_streak_adjusted_stake
)
from .value_decay import track_odds_movement, predict_closing_line

__all__ = [
    'find_correlated_parlays',
    'analyze_historical_correlation',
    'calculate_hedge_bet',
    'find_hedge_opportunities',
    'build_team_stacks',
    'evaluate_stack',
    'find_arbitrage_bets',
    'calculate_arbitrage_profit',
    'fibonacci_stake',
    'dalembert_stake',
    'oscar_grind_stake',
    'calculate_streak_adjusted_stake',
    'track_odds_movement',
    'predict_closing_line',
]
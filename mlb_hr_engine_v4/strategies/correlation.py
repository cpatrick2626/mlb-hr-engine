"""
Correlation-Based Parlay Strategy

Identifies players who historically hit home runs on the same days,
enabling smarter parlay construction with higher success probability.
"""

import csv
import itertools
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests


def analyze_historical_correlation(
    days_back: int = 90,
    min_games_together: int = 5,
    min_correlation: float = 0.15
) -> Dict[Tuple[str, str], float]:
    """
    Analyze historical HR correlation between players.

    Returns dict of (player1, player2) -> correlation_score
    where correlation_score is the percentage of games where both hit HRs
    when at least one did.
    """
    correlations = {}

    # Load historical data (would need to implement data fetching)
    # For now, return mock correlations for demonstration
    # In production, this would query historical game logs

    mock_correlations = {
        ("Yordan Alvarez", "Kyle Tucker"): 0.22,  # Same team, similar lineup spots
        ("Ronald Acuna Jr.", "Matt Olson"): 0.19,  # Braves lineup protection
        ("Mookie Betts", "Freddie Freeman"): 0.21,  # Dodgers 1-2 hitters
        ("Aaron Judge", "Giancarlo Stanton"): 0.18,  # Yankees power duo
        ("Corey Seager", "Marcus Semien"): 0.16,  # Rangers top of order
    }

    return mock_correlations


def find_correlated_parlays(
    players: List[dict],
    max_legs: int = 4,
    min_correlation: float = 0.15,
    min_individual_prob: float = 0.10
) -> List[dict]:
    """
    Find optimal parlays based on historical correlation.

    Args:
        players: List of player dicts with odds and probabilities
        max_legs: Maximum parlay size
        min_correlation: Minimum correlation coefficient to consider
        min_individual_prob: Minimum individual HR probability

    Returns:
        List of parlay opportunities with correlation bonus
    """
    correlations = analyze_historical_correlation()
    parlays = []

    # Filter to viable candidates
    candidates = [p for p in players if p.get("model_prob", 0) >= min_individual_prob]

    for n_legs in range(2, min(max_legs + 1, len(candidates) + 1)):
        for combo in itertools.combinations(candidates, n_legs):
            # Check correlation between all pairs
            correlation_scores = []
            for p1, p2 in itertools.combinations(combo, 2):
                key1 = (p1["player_name"], p2["player_name"])
                key2 = (p2["player_name"], p1["player_name"])

                corr = correlations.get(key1) or correlations.get(key2, 0)
                if corr >= min_correlation:
                    correlation_scores.append(corr)

            if correlation_scores:
                avg_correlation = sum(correlation_scores) / len(correlation_scores)

                # Calculate parlay with correlation bonus
                base_prob = 1.0
                for p in combo:
                    base_prob *= p.get("model_prob", 0)

                # Apply correlation bonus (increases expected probability)
                # This is a simplified model - production would use more sophisticated math
                correlation_multiplier = 1 + (avg_correlation * 0.5)
                adjusted_prob = min(base_prob * correlation_multiplier, 0.99)

                # Calculate parlay odds
                parlay_odds = 1.0
                for p in combo:
                    dec_odds = american_to_decimal(p.get("best_american", 100))
                    parlay_odds *= dec_odds

                parlay_ev = (parlay_odds * adjusted_prob) - 1

                if parlay_ev > 0:
                    parlays.append({
                        "legs": [p["player_name"] for p in combo],
                        "teams": [p["team"] for p in combo],
                        "correlation_score": avg_correlation,
                        "base_prob": base_prob,
                        "adjusted_prob": adjusted_prob,
                        "correlation_bonus": correlation_multiplier - 1,
                        "parlay_odds": parlay_odds,
                        "american_odds": decimal_to_american(parlay_odds),
                        "ev_pct": parlay_ev * 100,
                        "strategy": "correlation",
                        "confidence": min(90, 50 + (avg_correlation * 200)),
                    })

    # Sort by EV
    parlays.sort(key=lambda x: x["ev_pct"], reverse=True)
    return parlays[:10]  # Top 10 correlation parlays


def get_lineup_correlation_matrix(game_date: str) -> Dict[str, float]:
    """
    Build correlation matrix for today's lineups based on batting order adjacency.
    Players batting near each other often correlate due to:
    - Similar at-bats (lineup turnover)
    - RBI opportunities
    - Seeing same pitchers
    """
    matrix = {}

    # This would fetch actual lineups
    # For now, return estimates based on lineup position

    return matrix


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
"""
Value Decay and Line Movement Tracking

Analyzes how odds change over time to identify optimal betting windows
and predict closing line value.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math


def track_odds_movement(
    player: str,
    odds_history: List[Tuple[datetime, int]],  # (timestamp, american_odds)
    current_time: Optional[datetime] = None
) -> Dict[str, any]:
    """
    Track and analyze odds movement for a player.

    Args:
        player: Player name
        odds_history: List of (timestamp, odds) tuples
        current_time: Current time (None = now)

    Returns:
        Movement analysis dict
    """
    if len(odds_history) < 2:
        return {"insufficient_data": True}

    current_time = current_time or datetime.now()

    # Sort by timestamp
    odds_history = sorted(odds_history, key=lambda x: x[0])

    opening_time, opening_odds = odds_history[0]
    current_odds = odds_history[-1][1]

    # Calculate movement metrics
    total_movement = current_odds - opening_odds
    movement_pct = (abs(total_movement) / abs(opening_odds)) * 100

    # Calculate velocity (movement per hour)
    time_elapsed = (odds_history[-1][0] - opening_time).total_seconds() / 3600
    if time_elapsed > 0:
        velocity = total_movement / time_elapsed
    else:
        velocity = 0

    # Identify trend
    if len(odds_history) >= 3:
        recent_movements = [
            odds_history[i][1] - odds_history[i-1][1]
            for i in range(1, len(odds_history))
        ]
        trend = "shortening" if sum(recent_movements) < 0 else "lengthening"
    else:
        trend = "stable"

    # Calculate volatility
    if len(odds_history) >= 3:
        odds_values = [o[1] for _, o in odds_history]
        volatility = statistics.stdev(odds_values)
    else:
        volatility = 0

    # Identify steam moves (sharp money indicators)
    steam_moves = identify_steam_moves(odds_history)

    return {
        "player": player,
        "opening_odds": opening_odds,
        "current_odds": current_odds,
        "total_movement": total_movement,
        "movement_pct": movement_pct,
        "velocity_per_hour": velocity,
        "trend": trend,
        "volatility": volatility,
        "steam_moves": steam_moves,
        "time_since_open": time_elapsed,
        "recommendation": get_movement_recommendation(
            total_movement, velocity, trend, steam_moves
        )
    }


def predict_closing_line(
    odds_history: List[Tuple[datetime, int]],
    game_time: datetime,
    current_time: Optional[datetime] = None
) -> Dict[str, any]:
    """
    Predict closing line based on current movement patterns.

    Args:
        odds_history: Historical odds data
        game_time: When the game starts
        current_time: Current time

    Returns:
        Closing line prediction
    """
    if len(odds_history) < 3:
        return {"predicted_close": odds_history[-1][1], "confidence": "low"}

    current_time = current_time or datetime.now()
    current_odds = odds_history[-1][1]

    # Calculate time remaining
    hours_to_game = (game_time - current_time).total_seconds() / 3600

    if hours_to_game <= 0:
        return {"predicted_close": current_odds, "confidence": "high"}

    # Calculate recent velocity
    recent_data = odds_history[-5:]  # Last 5 data points
    if len(recent_data) >= 2:
        recent_movement = recent_data[-1][1] - recent_data[0][1]
        recent_time = (recent_data[-1][0] - recent_data[0][0]).total_seconds() / 3600
        recent_velocity = recent_movement / recent_time if recent_time > 0 else 0
    else:
        recent_velocity = 0

    # Apply decay factor (movement typically slows as game approaches)
    decay_factor = math.exp(-hours_to_game / 12)  # 12-hour half-life
    adjusted_velocity = recent_velocity * decay_factor

    # Predict closing line
    predicted_movement = adjusted_velocity * hours_to_game
    predicted_close = int(current_odds + predicted_movement)

    # Estimate confidence
    if abs(recent_velocity) < 5:
        confidence = "high"
    elif abs(recent_velocity) < 15:
        confidence = "moderate"
    else:
        confidence = "low"

    # Calculate CLV if betting now
    current_implied = 1.0 / american_to_decimal(current_odds)
    predicted_implied = 1.0 / american_to_decimal(predicted_close)
    expected_clv = ((current_implied - predicted_implied) / predicted_implied) * 100

    return {
        "current_odds": current_odds,
        "predicted_close": predicted_close,
        "expected_movement": predicted_movement,
        "hours_to_game": hours_to_game,
        "confidence": confidence,
        "expected_clv_pct": expected_clv,
        "recommendation": "bet_now" if expected_clv > 2 else "wait"
    }


def identify_steam_moves(
    odds_history: List[Tuple[datetime, int]],
    threshold_pct: float = 5.0,
    time_window_minutes: int = 30
) -> List[dict]:
    """
    Identify steam moves (rapid line movement indicating sharp action).

    Args:
        odds_history: Historical odds
        threshold_pct: Minimum movement % to qualify
        time_window_minutes: Maximum time window for steam

    Returns:
        List of steam moves detected
    """
    steam_moves = []

    for i in range(1, len(odds_history)):
        prev_time, prev_odds = odds_history[i-1]
        curr_time, curr_odds = odds_history[i]

        time_diff = (curr_time - prev_time).total_seconds() / 60
        odds_change_pct = abs((curr_odds - prev_odds) / prev_odds) * 100

        if time_diff <= time_window_minutes and odds_change_pct >= threshold_pct:
            steam_moves.append({
                "timestamp": curr_time,
                "from_odds": prev_odds,
                "to_odds": curr_odds,
                "change_pct": odds_change_pct,
                "minutes": time_diff,
                "direction": "shorter" if curr_odds < prev_odds else "longer"
            })

    return steam_moves


def analyze_market_efficiency(
    all_players_movements: Dict[str, List[Tuple[datetime, int]]]
) -> Dict[str, any]:
    """
    Analyze overall market efficiency and identify inefficiencies.

    Args:
        all_players_movements: Dict of player -> odds history

    Returns:
        Market efficiency analysis
    """
    total_movements = []
    steam_count = 0
    volatile_players = []

    for player, history in all_players_movements.items():
        if len(history) < 2:
            continue

        movement = history[-1][1] - history[0][1]
        total_movements.append(abs(movement))

        # Check for steam
        steam = identify_steam_moves(history)
        steam_count += len(steam)

        # Check volatility
        if len(history) >= 3:
            odds_values = [o for _, o in history]
            vol = statistics.stdev(odds_values)
            if vol > 50:  # High volatility threshold
                volatile_players.append(player)

    avg_movement = statistics.mean(total_movements) if total_movements else 0

    # Market efficiency score (0-100)
    # Lower movement and fewer steam moves = more efficient
    efficiency_score = max(0, 100 - (avg_movement * 2) - (steam_count * 5))

    return {
        "efficiency_score": efficiency_score,
        "average_movement": avg_movement,
        "total_steam_moves": steam_count,
        "volatile_players": volatile_players,
        "market_state": get_market_state(efficiency_score),
    }


def get_market_state(efficiency_score: float) -> str:
    """Categorize market state based on efficiency score."""
    if efficiency_score >= 80:
        return "highly_efficient"
    elif efficiency_score >= 60:
        return "moderately_efficient"
    elif efficiency_score >= 40:
        return "inefficient"
    else:
        return "highly_inefficient"


def get_movement_recommendation(
    total_movement: int,
    velocity: float,
    trend: str,
    steam_moves: List[dict]
) -> str:
    """
    Get betting recommendation based on line movement.

    Args:
        total_movement: Total odds movement
        velocity: Current movement velocity
        trend: Movement trend
        steam_moves: Detected steam moves

    Returns:
        Recommendation string
    """
    # Strong shortening with steam = sharp money
    if trend == "shortening" and steam_moves:
        if total_movement < -50:  # Significant shortening
            return "bet_immediately"
        else:
            return "bet_soon"

    # Lengthening odds = value increasing
    elif trend == "lengthening":
        if velocity > 10:  # Still moving longer
            return "wait_for_peak"
        else:
            return "good_value"

    # Stable lines
    elif abs(velocity) < 2:
        return "stable_line"

    else:
        return "monitor"


def find_line_shopping_opportunities(
    all_books_odds: Dict[str, Dict[str, int]],  # book -> player -> odds
    min_difference: int = 50
) -> List[dict]:
    """
    Find line shopping opportunities across books.

    Args:
        all_books_odds: Odds from all books
        min_difference: Minimum odds difference to flag

    Returns:
        Line shopping opportunities
    """
    opportunities = []

    # Aggregate by player
    player_odds = defaultdict(dict)
    for book, players in all_books_odds.items():
        for player, odds in players.items():
            player_odds[player][book] = odds

    for player, book_odds in player_odds.items():
        if len(book_odds) < 2:
            continue

        best_odds = max(book_odds.values())
        worst_odds = min(book_odds.values())
        difference = best_odds - worst_odds

        if difference >= min_difference:
            best_book = [b for b, o in book_odds.items() if o == best_odds][0]
            worst_book = [b for b, o in book_odds.items() if o == worst_odds][0]

            # Calculate value difference
            best_implied = 1.0 / american_to_decimal(best_odds)
            worst_implied = 1.0 / american_to_decimal(worst_odds)
            value_gain_pct = ((worst_implied - best_implied) / worst_implied) * 100

            opportunities.append({
                "player": player,
                "best_book": best_book,
                "best_odds": best_odds,
                "worst_book": worst_book,
                "worst_odds": worst_odds,
                "difference": difference,
                "value_gain_pct": value_gain_pct,
            })

    return sorted(opportunities, key=lambda x: x["value_gain_pct"], reverse=True)


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal."""
    if american >= 100:
        return (american / 100.0) + 1
    else:
        return (100.0 / abs(american)) + 1
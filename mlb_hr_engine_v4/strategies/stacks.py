"""
Stack Betting Strategy

Identifies opportunities to bet multiple players from the same team,
capitalizing on offensive explosions and pitcher implosions.
"""

from typing import Dict, List, Optional
import itertools
from collections import defaultdict


def build_team_stacks(
    players: List[dict],
    min_team_size: int = 2,
    max_stack_size: int = 4,
    min_individual_prob: float = 0.08,
    min_stack_ev: float = 10.0
) -> List[dict]:
    """
    Build optimal team stack parlays.

    Stacking rationale:
    - Pitchers who give up one HR often give up multiple
    - Teams that score runs create more HR opportunities
    - Lineup protection increases all players' chances

    Args:
        players: List of all players with odds
        min_team_size: Minimum players from same team
        max_stack_size: Maximum total stack size
        min_individual_prob: Minimum HR prob to include
        min_stack_ev: Minimum EV% to qualify

    Returns:
        List of stack betting opportunities
    """
    # Group players by team
    team_players = defaultdict(list)
    for p in players:
        if p.get("model_prob", 0) >= min_individual_prob:
            team_players[p["team"]].append(p)

    stacks = []

    for team, roster in team_players.items():
        if len(roster) < min_team_size:
            continue

        # Analyze team factors
        team_factor = analyze_team_explosion_probability(team, roster)

        # Generate stack combinations
        for size in range(min_team_size, min(max_stack_size + 1, len(roster) + 1)):
            for combo in itertools.combinations(roster, size):
                stack = evaluate_stack(combo, team_factor)

                if stack["ev_pct"] >= min_stack_ev:
                    stack["team"] = team
                    stack["strategy"] = "team_stack"
                    stacks.append(stack)

    # Sort by EV
    return sorted(stacks, key=lambda x: x["ev_pct"], reverse=True)[:15]


def evaluate_stack(
    players: List[dict],
    team_explosion_factor: float = 1.0
) -> dict:
    """
    Evaluate a specific stack combination.

    Args:
        players: Players in the stack
        team_explosion_factor: Multiplier for correlated team offense

    Returns:
        Stack evaluation dict
    """
    # Base probability (independent)
    base_prob = 1.0
    total_odds = 1.0

    for p in players:
        base_prob *= p.get("model_prob", 0)
        dec_odds = american_to_decimal(p.get("best_american", 100))
        total_odds *= dec_odds

    # Apply correlation boost for stacking
    # Theory: HRs are not independent within a game
    # If one player hits, others are more likely (facing same pitcher, momentum)
    n_players = len(players)
    correlation_boost = 1 + (0.1 * (n_players - 1))  # 10% boost per additional player

    # Apply team explosion factor
    adjusted_prob = base_prob * correlation_boost * team_explosion_factor

    # Calculate EV
    ev = (total_odds * adjusted_prob) - 1

    return {
        "players": [p["player_name"] for p in players],
        "lineup_spots": [p.get("lineup_spot", 0) for p in players],
        "size": n_players,
        "base_prob": base_prob,
        "adjusted_prob": min(adjusted_prob, 0.25),  # Cap at 25%
        "correlation_boost": correlation_boost,
        "team_explosion_factor": team_explosion_factor,
        "parlay_odds": total_odds,
        "american_odds": decimal_to_american(total_odds),
        "ev_pct": ev * 100,
        "confidence": calculate_stack_confidence(players, team_explosion_factor),
    }


def analyze_team_explosion_probability(team: str, roster: List[dict]) -> float:
    """
    Analyze probability of team offensive explosion.

    Factors:
    - Opposing pitcher quality
    - Park factor
    - Team's recent scoring
    - Weather conditions
    """
    # Get average pitcher factor faced
    pitcher_factors = [p.get("pitcher_factor", 1.0) for p in roster]
    avg_pitcher_factor = sum(pitcher_factors) / len(pitcher_factors) if pitcher_factors else 1.0

    # Get park factor
    park_factors = [p.get("park_factor", 1.0) for p in roster]
    park_factor = max(park_factors) if park_factors else 1.0

    # Calculate explosion probability
    if avg_pitcher_factor > 1.1:  # Facing weak pitcher
        explosion_mult = 1.2
    elif avg_pitcher_factor > 1.05:
        explosion_mult = 1.1
    else:
        explosion_mult = 1.0

    if park_factor > 1.15:  # Hitter's park
        explosion_mult *= 1.1

    return explosion_mult


def find_game_stacks(
    players: List[dict],
    min_total_runs: float = 9.0
) -> List[dict]:
    """
    Find stacks based on high-scoring game projections.

    Target games with high over/under totals where multiple HRs are likely.
    """
    # Group by game
    games = defaultdict(list)
    for p in players:
        game_key = f"{p['team']}_{p['opponent']}"
        games[game_key].append(p)

    high_scoring_stacks = []

    for game, participants in games.items():
        # Would fetch actual O/U from odds API
        # For now, estimate based on park and pitcher factors
        estimated_total = estimate_game_total(participants)

        if estimated_total >= min_total_runs:
            # Build stacks from both teams in high-scoring games
            for size in range(2, min(5, len(participants) + 1)):
                for combo in itertools.combinations(participants, size):
                    stack = evaluate_stack(combo, 1.15)  # Boost for high-scoring game
                    stack["game_total"] = estimated_total
                    stack["strategy"] = "game_stack"
                    high_scoring_stacks.append(stack)

    return sorted(high_scoring_stacks, key=lambda x: x["ev_pct"], reverse=True)[:10]


def estimate_game_total(players: List[dict]) -> float:
    """Estimate game total runs based on factors."""
    base_total = 8.5

    # Adjust for park
    park_factors = [p.get("park_factor", 1.0) for p in players]
    avg_park = sum(park_factors) / len(park_factors) if park_factors else 1.0
    base_total *= avg_park

    # Adjust for pitchers
    pitcher_factors = [p.get("pitcher_factor", 1.0) for p in players]
    avg_pitcher = sum(pitcher_factors) / len(pitcher_factors) if pitcher_factors else 1.0
    base_total *= avg_pitcher

    return base_total


def calculate_stack_confidence(players: List[dict], team_factor: float) -> float:
    """Calculate confidence score for a stack."""
    base_confidence = 50

    # Add for each player's individual confidence
    player_confs = [p.get("confidence", 50) for p in players]
    avg_conf = sum(player_confs) / len(player_confs) if player_confs else 50

    # Adjust for team factor
    confidence = (avg_conf * 0.7) + (team_factor * 30)

    # Bonus for consecutive lineup spots
    lineup_spots = sorted([p.get("lineup_spot", 9) for p in players])
    if len(lineup_spots) > 1:
        consecutive = all(
            lineup_spots[i+1] - lineup_spots[i] <= 2
            for i in range(len(lineup_spots)-1)
        )
        if consecutive:
            confidence += 10

    return min(confidence, 95)


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
"""
Correlation-Based Parlay Strategy

Finds parlays where players are positively correlated — same team facing the
same pitcher, or batting close together in the order. No historical data required;
correlation is derived entirely from today's lineup and pitcher context.
"""

import itertools
from typing import Dict, List, Tuple


def analyze_historical_correlation(
    players: List[dict] = None,
    days_back: int = 90,
    min_games_together: int = 5,
    min_correlation: float = 0.15,
) -> Dict[Tuple[str, str], float]:
    """
    Build a correlation map from today's player data.

    Same-team players share a pitcher and lineup context, giving a base
    correlation. Batting order adjacency adds an extra bump.
    """
    if not players:
        return {}

    correlations: Dict[Tuple[str, str], float] = {}

    # Group by (team, opponent) so we only pair teammates facing the same pitcher
    from collections import defaultdict
    game_groups: Dict[str, List[dict]] = defaultdict(list)
    for p in players:
        key = f"{p.get('team', '')}_{p.get('opponent', '')}"
        game_groups[key].append(p)

    for group in game_groups.values():
        if len(group) < 2:
            continue
        for p1, p2 in itertools.combinations(group, 2):
            # Base correlation: same team, same pitcher
            corr = 0.18

            # Batting order adjacency bonus
            s1 = p1.get("lineup_spot") or 0
            s2 = p2.get("lineup_spot") or 0
            if s1 and s2:
                gap = abs(int(s1) - int(s2))
                if gap == 1:
                    corr += 0.06
                elif gap == 2:
                    corr += 0.03

            # Pitcher factor bonus — weak pitcher amplifies correlation
            pf = (p1.get("pitcher_factor", 1.0) + p2.get("pitcher_factor", 1.0)) / 2
            if pf > 1.1:
                corr += 0.04

            key = (p1["player_name"], p2["player_name"])
            correlations[key] = round(corr, 4)

    return correlations


def find_correlated_parlays(
    players: List[dict],
    max_legs: int = 3,
    min_correlation: float = 0.15,
    min_individual_prob: float = 0.08,
) -> List[dict]:
    """
    Find parlays where players are correlated (same team/pitcher context).

    Returns top 10 by EV, each with correlation metadata.
    """
    correlations = analyze_historical_correlation(
        players=players,
        min_correlation=min_correlation,
    )

    if not correlations:
        return []

    # Cap to top 25 by model_prob to keep combination count manageable
    all_candidates = [p for p in players if p.get("model_prob", 0) >= min_individual_prob
                      and p.get("best_american")]
    candidates = sorted(all_candidates, key=lambda p: p.get("model_prob", 0), reverse=True)[:25]

    parlays = []

    for n_legs in range(2, min(max_legs + 1, len(candidates) + 1)):
        for combo in itertools.combinations(candidates, n_legs):
            # Only include combos where at least one pair is correlated
            pair_scores = []
            for p1, p2 in itertools.combinations(combo, 2):
                key1 = (p1["player_name"], p2["player_name"])
                key2 = (p2["player_name"], p1["player_name"])
                corr = correlations.get(key1) or correlations.get(key2, 0)
                if corr >= min_correlation:
                    pair_scores.append(corr)

            if not pair_scores:
                continue

            avg_corr = sum(pair_scores) / len(pair_scores)

            base_prob = 1.0
            for p in combo:
                base_prob *= p.get("model_prob", 0)

            correlation_multiplier = 1 + (avg_corr * 0.5)
            adjusted_prob = min(base_prob * correlation_multiplier, 0.99)

            parlay_odds = 1.0
            for p in combo:
                dec = american_to_decimal(p.get("best_american", 100))
                parlay_odds *= dec

            ev = (parlay_odds * adjusted_prob) - 1

            if ev > 0:
                parlays.append({
                    "legs":              [p["player_name"] for p in combo],
                    "teams":             [p.get("team", "") for p in combo],
                    "correlation_score": avg_corr,
                    "base_prob":         base_prob,
                    "adjusted_prob":     adjusted_prob,
                    "correlation_bonus": correlation_multiplier - 1,
                    "parlay_odds":       parlay_odds,
                    "american_odds":     decimal_to_american(parlay_odds),
                    "ev_pct":            ev * 100,
                    "strategy":          "correlation",
                    "confidence":        min(90, 50 + (avg_corr * 200)),
                })

    parlays.sort(key=lambda x: x["ev_pct"], reverse=True)
    return parlays[:10]


def american_to_decimal(american: int) -> float:
    if american == 0:
        return 1.01
    if american >= 100:
        return (american / 100.0) + 1
    return (100.0 / abs(american)) + 1


def decimal_to_american(decimal: float) -> int:
    if decimal >= 2.0:
        return int((decimal - 1) * 100)
    return int(-100 / (decimal - 1))

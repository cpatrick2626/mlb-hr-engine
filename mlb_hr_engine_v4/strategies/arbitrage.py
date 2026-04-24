"""
Arbitrage Betting Strategy

Identifies risk-free profit opportunities across different sportsbooks.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import itertools


def find_arbitrage_bets(
    all_odds: Dict[str, Dict[str, int]],  # player -> {book -> odds}
    min_profit_pct: float = 1.0,
    max_stake: float = 1000
) -> List[dict]:
    """
    Find arbitrage opportunities across books.

    Args:
        all_odds: Nested dict of player -> book -> American odds
        min_profit_pct: Minimum guaranteed profit percentage
        max_stake: Maximum total stake across all books

    Returns:
        List of arbitrage opportunities
    """
    arbs = []

    for player, book_odds in all_odds.items():
        if len(book_odds) < 2:
            continue

        # Check all book combinations
        for book1, book2 in itertools.combinations(book_odds.keys(), 2):
            odds1 = book_odds[book1]
            odds2 = book_odds[book2]

            # Check if arbitrage exists on YES/NO
            arb = check_two_way_arbitrage(
                player, book1, odds1, book2, odds2, max_stake
            )

            if arb and arb["roi_pct"] >= min_profit_pct:
                arbs.append(arb)

        # Check for 3-way arbitrage if 3+ books
        if len(book_odds) >= 3:
            for books in itertools.combinations(book_odds.keys(), 3):
                multi_arb = check_multi_book_arbitrage(
                    player, {b: book_odds[b] for b in books}, max_stake
                )
                if multi_arb and multi_arb["roi_pct"] >= min_profit_pct:
                    arbs.append(multi_arb)

    return sorted(arbs, key=lambda x: x["roi_pct"], reverse=True)


def check_two_way_arbitrage(
    player: str,
    book1: str,
    odds1: int,
    book2: str,
    odds2: int,
    max_stake: float
) -> Optional[dict]:
    """
    Check if arbitrage exists between two books.

    This works when the sum of implied probabilities < 100%.
    """
    dec1 = american_to_decimal(odds1)
    dec2 = american_to_decimal(odds2)

    # Calculate implied probabilities
    impl1 = 1.0 / dec1
    impl2 = 1.0 / dec2

    # For HR bets, we need the No HR odds
    # Estimate based on market efficiency
    no_hr_impl1 = 1 - impl1 * 1.05  # Add ~5% vig
    no_hr_impl2 = 1 - impl2 * 1.05

    # Check if we can bet YES on one book and NO on another
    if impl1 + no_hr_impl2 < 1.0:
        # Arbitrage: YES on book1, NO on book2
        return calculate_arbitrage_profit(
            player,
            [(book1, "YES", odds1), (book2, "NO", implied_to_american(no_hr_impl2))],
            max_stake
        )

    if impl2 + no_hr_impl1 < 1.0:
        # Arbitrage: YES on book2, NO on book1
        return calculate_arbitrage_profit(
            player,
            [(book2, "YES", odds2), (book1, "NO", implied_to_american(no_hr_impl1))],
            max_stake
        )

    return None


def check_multi_book_arbitrage(
    player: str,
    book_odds: Dict[str, int],
    max_stake: float
) -> Optional[dict]:
    """
    Check for arbitrage across 3+ books.

    More complex scenarios where different books have different edges.
    """
    best_yes = None
    best_yes_book = None
    best_no_implied = 1.0
    best_no_book = None

    for book, odds in book_odds.items():
        dec_odds = american_to_decimal(odds)
        yes_implied = 1.0 / dec_odds

        if best_yes is None or odds > best_yes:
            best_yes = odds
            best_yes_book = book

        # Estimate No HR implied
        no_implied = 1 - yes_implied * 1.05
        if no_implied < best_no_implied:
            best_no_implied = no_implied
            best_no_book = book

    if best_yes_book and best_no_book and best_yes_book != best_no_book:
        yes_implied = 1.0 / american_to_decimal(best_yes)
        if yes_implied + best_no_implied < 1.0:
            return calculate_arbitrage_profit(
                player,
                [
                    (best_yes_book, "YES", best_yes),
                    (best_no_book, "NO", implied_to_american(best_no_implied))
                ],
                max_stake
            )

    return None


def calculate_arbitrage_profit(
    player: str,
    bets: List[Tuple[str, str, int]],  # (book, side, odds)
    max_stake: float
) -> dict:
    """
    Calculate optimal stakes and guaranteed profit for an arbitrage.

    Args:
        player: Player name
        bets: List of (book, side, american_odds)
        max_stake: Maximum total stake

    Returns:
        Arbitrage details with stakes and profit
    """
    # Convert to decimal odds and calculate implied probabilities
    total_implied = 0
    bet_details = []

    for book, side, odds in bets:
        dec_odds = american_to_decimal(odds)
        implied = 1.0 / dec_odds
        total_implied += implied
        bet_details.append({
            "book": book,
            "side": side,
            "american_odds": odds,
            "decimal_odds": dec_odds,
            "implied_prob": implied,
        })

    if total_implied >= 1.0:
        return None  # No arbitrage

    # Calculate optimal stakes
    for bet in bet_details:
        bet["stake"] = (bet["implied_prob"] / total_implied) * max_stake
        bet["payout"] = bet["stake"] * bet["decimal_odds"]

    # Guaranteed profit is the payout minus total stakes
    guaranteed_payout = bet_details[0]["payout"]  # Same for all outcomes
    total_stakes = sum(b["stake"] for b in bet_details)
    profit = guaranteed_payout - total_stakes
    roi = (profit / total_stakes) * 100

    return {
        "player": player,
        "bets": bet_details,
        "total_stake": round(total_stakes, 2),
        "guaranteed_payout": round(guaranteed_payout, 2),
        "guaranteed_profit": round(profit, 2),
        "roi_pct": round(roi, 2),
        "strategy": "arbitrage",
    }


def find_closing_line_arbitrage(
    morning_odds: Dict[str, int],
    current_odds: Dict[str, int],
    active_bets: List[dict]
) -> List[dict]:
    """
    Find arbitrage opportunities created by line movement.

    If you bet early and lines move, you might be able to lock in profit.
    """
    opportunities = []

    for bet in active_bets:
        player = bet["player_name"]
        original_odds = bet["american_odds"]

        if player in current_odds:
            current = current_odds[player]

            # Check if we can arbitrage with current No HR odds
            current_yes_implied = 1.0 / american_to_decimal(current)
            original_yes_implied = 1.0 / american_to_decimal(original_odds)

            # If line moved against us significantly, we might arb
            if current_yes_implied > original_yes_implied * 1.1:
                no_hr_odds = implied_to_american(1 - current_yes_implied * 1.05)

                arb = calculate_arbitrage_profit(
                    player,
                    [
                        ("Original", "YES", original_odds),
                        ("Current", "NO", no_hr_odds)
                    ],
                    bet["bet_amount"] * 2
                )

                if arb and arb["roi_pct"] > 0:
                    opportunities.append({
                        "original_bet": bet,
                        "arbitrage": arb,
                        "line_movement": current - original_odds,
                    })

    return opportunities


def implied_to_american(implied_prob: float) -> int:
    """Convert implied probability to American odds."""
    if implied_prob >= 0.5:
        return int(-implied_prob / (1 - implied_prob) * 100)
    else:
        return int((1 - implied_prob) / implied_prob * 100)


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal."""
    if american >= 100:
        return (american / 100.0) + 1
    else:
        return (100.0 / abs(american)) + 1
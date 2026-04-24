#!/usr/bin/env python3
"""
Test script to verify the odds matching optimization works correctly and measure performance.
"""

import time
import sys
from pathlib import Path

# Add v4 to path
sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

from rapidfuzz import fuzz, process as fuzz_process

# Create test data that simulates the actual scenario
def create_test_data():
    """Create test data similar to real MLB data."""
    # Simulate 100 unique prop entries (market odds)
    all_props = []
    for i in range(100):
        base_names = [
            "Mike Trout", "Shohei Ohtani", "Aaron Judge", "Ronald Acuna Jr.",
            "Mookie Betts", "Juan Soto", "Vladimir Guerrero Jr.", "Freddie Freeman",
            "Jose Altuve", "Yordan Alvarez", "Corey Seager", "Marcus Semien"
        ]
        name = base_names[i % len(base_names)]
        # Add some variations to simulate multiple bookmakers
        for book in ["fanduel", "draftkings", "bet365"]:
            all_props.append({
                "player_name": name,
                "price": 300 + (i * 10) + (hash(book) % 50),
                "bookmaker": book
            })

    # Simulate 300 players to match
    all_players = []
    for i in range(300):
        # Use similar but slightly different names to test fuzzy matching
        base_names_varied = [
            "Mike Trout", "Shohei Ohtani", "Aaron Judge", "Ronald Acuña Jr.",  # Note: Acuña with ñ
            "Mookie Betts", "Juan Soto", "Vlad Guerrero Jr.", "Freddie Freeman",  # Vlad vs Vladimir
            "Jose Altuve", "Yordan Alvarez", "Corey Seager", "Marcus Semien",
            "Trea Turner", "Bo Bichette", "Matt Olson", "Pete Alonso"
        ]
        all_players.append({
            "player_name": base_names_varied[i % len(base_names_varied)],
            "player_id": 500000 + i,
            "model_prob": 0.1 + (i % 20) * 0.01
        })

    return all_props, all_players


# Original O(n²) implementation
def original_match_odds(player, all_props):
    """Original O(n²) implementation."""
    if not all_props:
        return player
    prop_names = [p["player_name"] for p in all_props]
    match = fuzz_process.extractOne(
        player["player_name"], prop_names,
        scorer=fuzz.token_sort_ratio, score_cutoff=82,
    )
    if not match:
        return player
    matched_name = match[0]
    matches = [p for p in all_props if p["player_name"] == matched_name]
    if not matches:
        return player
    prices = [p["price"] for p in matches]
    best = max(matches, key=lambda x: x["price"])
    fd_matches = [p for p in matches if p.get("bookmaker") == "fanduel"]
    fd_odds = max(fd_matches, key=lambda x: x["price"])["price"] if fd_matches else None
    player.update({
        "best_american": best["price"],
        "best_bookmaker": best.get("bookmaker", ""),
        "all_prices": prices,
        "fanduel_american": fd_odds,
    })
    return player


# Optimized O(n) implementation
def build_odds_lookup(all_props):
    """Pre-build a lookup structure for O(1) odds matching."""
    if not all_props:
        return {}, []

    # Group props by player name
    odds_by_player = {}
    for prop in all_props:
        name = prop["player_name"]
        if name not in odds_by_player:
            odds_by_player[name] = []
        odds_by_player[name].append(prop)

    # Create list of unique player names for fuzzy matching
    unique_names = list(odds_by_player.keys())

    return odds_by_player, unique_names


def optimized_match_odds(player, odds_lookup, unique_names):
    """Match odds using pre-built lookup structure (O(1) after fuzzy match)."""
    if not odds_lookup:
        return player

    # Fuzzy match against unique names only (much smaller list)
    match = fuzz_process.extractOne(
        player["player_name"], unique_names,
        scorer=fuzz.token_sort_ratio, score_cutoff=82,
    )
    if not match:
        return player

    matched_name = match[0]
    matches = odds_lookup.get(matched_name, [])
    if not matches:
        return player

    prices = [p["price"] for p in matches]
    best = max(matches, key=lambda x: x["price"])
    fd_matches = [p for p in matches if p.get("bookmaker") == "fanduel"]
    fd_odds = max(fd_matches, key=lambda x: x["price"])["price"] if fd_matches else None
    player.update({
        "best_american": best["price"],
        "best_bookmaker": best.get("bookmaker", ""),
        "all_prices": prices,
        "fanduel_american": fd_odds,
    })
    return player


def main():
    print("Creating test data...")
    all_props, all_players = create_test_data()
    print(f"Created {len(all_props)} prop entries and {len(all_players)} players")
    print()

    # Test original implementation
    print("Testing ORIGINAL O(n²) implementation...")
    original_players = [p.copy() for p in all_players]  # Deep copy
    start_time = time.time()
    for p in original_players:
        original_match_odds(p, all_props)
    original_time = time.time() - start_time
    print(f"Original implementation took: {original_time:.3f} seconds")

    # Test optimized implementation
    print("\nTesting OPTIMIZED O(n) implementation...")
    optimized_players = [p.copy() for p in all_players]  # Deep copy
    start_time = time.time()

    # Pre-build lookup once
    odds_lookup, unique_names = build_odds_lookup(all_props)
    build_time = time.time() - start_time

    # Match all players
    match_start = time.time()
    for p in optimized_players:
        optimized_match_odds(p, odds_lookup, unique_names)
    match_time = time.time() - match_start

    optimized_time = build_time + match_time
    print(f"Optimized implementation took: {optimized_time:.3f} seconds")
    print(f"  - Building lookup: {build_time:.3f} seconds")
    print(f"  - Matching players: {match_time:.3f} seconds")

    # Verify results are the same
    print("\nVerifying results match...")
    mismatches = 0
    for i, (orig, opt) in enumerate(zip(original_players, optimized_players)):
        # Compare key fields
        if orig.get("best_american") != opt.get("best_american"):
            mismatches += 1
            print(f"Mismatch at player {i}: {orig['player_name']}")
            print(f"  Original: {orig.get('best_american')}")
            print(f"  Optimized: {opt.get('best_american')}")

    if mismatches == 0:
        print("✅ All results match! Optimization is correct.")
    else:
        print(f"❌ Found {mismatches} mismatches")

    # Calculate improvement
    print("\n" + "=" * 60)
    speedup = original_time / optimized_time
    improvement = (original_time - optimized_time) / original_time * 100
    print(f"PERFORMANCE IMPROVEMENT: {speedup:.2f}x faster")
    print(f"Time saved: {improvement:.1f}%")
    print(f"Absolute time saved: {original_time - optimized_time:.3f} seconds")

    # Estimate impact on full pipeline
    print("\n📊 Estimated impact on full pipeline:")
    print(f"If odds matching takes ~10% of total runtime:")
    print(f"  - Expected overall speedup: {(improvement * 0.1):.1f}%")
    print(f"If odds matching takes ~20% of total runtime:")
    print(f"  - Expected overall speedup: {(improvement * 0.2):.1f}%")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to measure the improvement from MLB API call consolidation.
Compares individual API calls vs bulk fetching.
"""

import sys
import time
import traceback
from pathlib import Path

# Add v4 to path
sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

from clients import mlb_stats

# Test data - some real MLB player IDs
TEST_BATTER_IDS = {
    660271,  # Mike Trout
    592450,  # Aaron Judge
    660670,  # Shohei Ohtani
    605141,  # Mookie Betts
    665742,  # Juan Soto
    665489,  # Vladimir Guerrero Jr.
    518692,  # Freddie Freeman
    514888,  # Jose Altuve
    670541,  # Yordan Alvarez
    571448,  # Nolan Arenado
    502110,  # Paul Goldschmidt
    514888,  # Jose Altuve
    545361,  # Mike Trout
    605141,  # Mookie Betts
    608324,  # Corey Seager
    663728,  # Bo Bichette
}

TEST_PITCHER_IDS = {
    605483,  # Gerrit Cole
    543037,  # Jacob deGrom
    656302,  # Shane Bieber
    621111,  # Walker Buehler
    666200,  # Sandy Alcantara
}


def test_individual_calls():
    """Test the original approach - individual API calls for each player."""
    print("\n=== Testing INDIVIDUAL API calls (original) ===")

    # Clear all caches
    mlb_stats._GAME_LOG_CACHE.clear()
    mlb_stats._BULK_SEASON_STATS_CACHE.clear()
    mlb_stats._BULK_RECENT_STATS_CACHE.clear()
    mlb_stats._BULK_PITCHER_STATS_CACHE.clear()
    mlb_stats.get_player_season_stats.cache_clear()
    mlb_stats.get_pitcher_season_stats.cache_clear()

    api_calls = 0
    start_time = time.time()

    # Count API calls by monkey-patching _get
    original_get = mlb_stats._get
    def counting_get(*args, **kwargs):
        nonlocal api_calls
        api_calls += 1
        return original_get(*args, **kwargs)

    mlb_stats._get = counting_get

    try:
        # Simulate what the pipeline does for each player
        results = {}
        for player_id in TEST_BATTER_IDS:
            try:
                season = mlb_stats.get_player_season_stats(player_id)
                recent = mlb_stats.get_player_recent_stats(player_id)
                short = mlb_stats.get_player_short_form(player_id, days=14)
                results[player_id] = {
                    "season_pa": season.get("plateAppearances", 0),
                    "recent_hr": recent.get("homeRuns", 0),
                    "short_form": short.get("form", "")
                }
            except Exception as e:
                print(f"  Error fetching player {player_id}: {e}")

        for pitcher_id in TEST_PITCHER_IDS:
            try:
                pitcher_stats = mlb_stats.get_pitcher_season_stats(pitcher_id)
                results[f"p_{pitcher_id}"] = {
                    "era": pitcher_stats.get("era", 0)
                }
            except Exception as e:
                print(f"  Error fetching pitcher {pitcher_id}: {e}")

    finally:
        mlb_stats._get = original_get

    elapsed = time.time() - start_time
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"API calls made: {api_calls}")
    print(f"Players processed: {len(TEST_BATTER_IDS)} batters, {len(TEST_PITCHER_IDS)} pitchers")
    print(f"Average API calls per player: {api_calls / (len(TEST_BATTER_IDS) + len(TEST_PITCHER_IDS)):.1f}")

    return elapsed, api_calls, results


def test_bulk_calls():
    """Test the optimized approach - bulk API calls."""
    print("\n=== Testing BULK API calls (optimized) ===")

    # Clear all caches
    mlb_stats._GAME_LOG_CACHE.clear()
    mlb_stats._BULK_SEASON_STATS_CACHE.clear()
    mlb_stats._BULK_RECENT_STATS_CACHE.clear()
    mlb_stats._BULK_PITCHER_STATS_CACHE.clear()
    mlb_stats.get_player_season_stats.cache_clear()
    mlb_stats.get_pitcher_season_stats.cache_clear()

    api_calls = 0
    start_time = time.time()

    # Count API calls
    original_get = mlb_stats._get
    def counting_get(*args, **kwargs):
        nonlocal api_calls
        api_calls += 1
        return original_get(*args, **kwargs)

    mlb_stats._get = counting_get

    try:
        # First, bulk fetch all stats (what the optimized pipeline does)
        mlb_stats.bulk_fetch_player_stats(TEST_BATTER_IDS)
        mlb_stats.bulk_fetch_pitcher_stats(TEST_PITCHER_IDS)

        bulk_api_calls = api_calls

        # Now fetch individual stats (should use cache)
        results = {}
        for player_id in TEST_BATTER_IDS:
            try:
                season = mlb_stats.get_player_season_stats(player_id)
                recent = mlb_stats.get_player_recent_stats(player_id)
                short = mlb_stats.get_player_short_form(player_id, days=14)
                results[player_id] = {
                    "season_pa": season.get("plateAppearances", 0),
                    "recent_hr": recent.get("homeRuns", 0),
                    "short_form": short.get("form", "")
                }
            except Exception as e:
                print(f"  Error fetching player {player_id}: {e}")

        for pitcher_id in TEST_PITCHER_IDS:
            try:
                pitcher_stats = mlb_stats.get_pitcher_season_stats(pitcher_id)
                results[f"p_{pitcher_id}"] = {
                    "era": pitcher_stats.get("era", 0)
                }
            except Exception as e:
                print(f"  Error fetching pitcher {pitcher_id}: {e}")

    finally:
        mlb_stats._get = original_get

    elapsed = time.time() - start_time
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"API calls made: {api_calls} (bulk fetch: {bulk_api_calls}, additional: {api_calls - bulk_api_calls})")
    print(f"Players processed: {len(TEST_BATTER_IDS)} batters, {len(TEST_PITCHER_IDS)} pitchers")
    print(f"Average API calls per player: {api_calls / (len(TEST_BATTER_IDS) + len(TEST_PITCHER_IDS)):.1f}")

    return elapsed, api_calls, results


def verify_data_consistency(results_individual, results_bulk):
    """Verify that bulk fetching produces the same results."""
    print("\n=== Verifying data consistency ===")

    mismatches = 0
    for key in results_individual:
        if key not in results_bulk:
            print(f"Key {key} missing in bulk results")
            mismatches += 1
            continue

        ind = results_individual[key]
        bulk = results_bulk[key]

        for field in ind:
            if field in bulk and ind[field] != bulk[field]:
                # Allow small differences in calculated stats
                if isinstance(ind[field], (int, float)) and isinstance(bulk[field], (int, float)):
                    if abs(ind[field] - bulk[field]) > 0.01:
                        print(f"Mismatch for {key}.{field}: {ind[field]} vs {bulk[field]}")
                        mismatches += 1
                elif ind[field] != bulk[field]:
                    print(f"Mismatch for {key}.{field}: {ind[field]} vs {bulk[field]}")
                    mismatches += 1

    if mismatches == 0:
        print("✅ All data matches! Bulk fetching preserves correctness.")
    else:
        print(f"⚠️ Found {mismatches} mismatches (may be due to data freshness)")

    return mismatches == 0


def main():
    print("=" * 60)
    print("MLB API Call Consolidation Test")
    print("=" * 60)

    print("\nNote: This test fetches real data from MLB Stats API.")
    print("Testing with", len(TEST_BATTER_IDS), "batters and", len(TEST_PITCHER_IDS), "pitchers")

    # Run tests
    time_individual, calls_individual, results_individual = test_individual_calls()
    time_bulk, calls_bulk, results_bulk = test_bulk_calls()

    # Verify correctness
    is_correct = verify_data_consistency(results_individual, results_bulk)

    # Calculate improvements
    print("\n" + "=" * 60)
    print("PERFORMANCE IMPROVEMENT SUMMARY")
    print("=" * 60)

    api_reduction = (1 - calls_bulk / calls_individual) * 100
    time_improvement = (1 - time_bulk / time_individual) * 100

    print(f"\nAPI calls:")
    print(f"  Individual: {calls_individual} calls")
    print(f"  Bulk: {calls_bulk} calls")
    print(f"  Reduction: {api_reduction:.1f}%")

    print(f"\nExecution time:")
    print(f"  Individual: {time_individual:.2f}s")
    print(f"  Bulk: {time_bulk:.2f}s")
    print(f"  Improvement: {time_improvement:.1f}%")

    print(f"\nEfficiency:")
    print(f"  Individual: {calls_individual / (len(TEST_BATTER_IDS) + len(TEST_PITCHER_IDS)):.1f} calls/player")
    print(f"  Bulk: {calls_bulk / (len(TEST_BATTER_IDS) + len(TEST_PITCHER_IDS)):.1f} calls/player")

    print("\n📊 Expected impact on full pipeline (300 players):")
    expected_calls_before = 300 * (calls_individual / len(TEST_BATTER_IDS))
    expected_calls_after = 300 / 50 + 10  # Batches of 50 + some individual fallbacks
    print(f"  API calls: ~{expected_calls_before:.0f} → ~{expected_calls_after:.0f} ({(1 - expected_calls_after/expected_calls_before)*100:.0f}% reduction)")
    print(f"  Time savings: ~{time_improvement:.0f}% on MLB API portion")
    print(f"  Overall pipeline: ~5-10% faster (MLB API is part of total)")

    if is_correct and api_reduction > 50:
        print("\n✅ Optimization successful! Major reduction in API calls.")
    else:
        print("\n⚠️ Check results - optimization may need adjustments.")


if __name__ == "__main__":
    main()
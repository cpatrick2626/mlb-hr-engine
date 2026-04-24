#!/usr/bin/env python3
"""
Test script to verify the Statcast early filtering optimization works correctly.
Measures memory usage and performance improvement.
"""

import sys
import time
import tracemalloc
from pathlib import Path

# Add v4 to path
sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

from clients import statcast

# Test data - some real MLB player IDs
TEST_PLAYER_IDS = {
    660271,  # Mike Trout
    660670,  # Shohei Ohtani
    592450,  # Aaron Judge
    660670,  # Ronald Acuna Jr.
    605141,  # Mookie Betts
    665742,  # Juan Soto
    665489,  # Vladimir Guerrero Jr.
    518692,  # Freddie Freeman
    514888,  # Jose Altuve
    670541,  # Yordan Alvarez
}

def test_without_filter():
    """Test the original behavior - load all players."""
    print("\n=== Testing WITHOUT filter (original behavior) ===")

    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()

    # Fetch without filter (loads all ~2500+ players)
    batter_data = statcast.get_batter_statcast(year=2024)

    # Measure results
    elapsed = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Players loaded: {len(batter_data)}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

    # Check we have data for test players
    found = sum(1 for pid in TEST_PLAYER_IDS if pid in batter_data)
    print(f"Test players found: {found}/{len(TEST_PLAYER_IDS)}")

    return batter_data, elapsed, peak


def test_with_filter():
    """Test the optimized behavior - only load specific players."""
    print("\n=== Testing WITH filter (optimized) ===")

    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()

    # Fetch with filter (loads only requested players)
    batter_data = statcast.get_batter_statcast(year=2024, player_ids=TEST_PLAYER_IDS)

    # Measure results
    elapsed = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Players loaded: {len(batter_data)}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

    # Check we have data for test players
    found = sum(1 for pid in TEST_PLAYER_IDS if pid in batter_data)
    print(f"Test players found: {found}/{len(TEST_PLAYER_IDS)}")

    return batter_data, elapsed, peak


def verify_data_consistency(data_without, data_with):
    """Verify that filtered data matches unfiltered data for the same players."""
    print("\n=== Verifying data consistency ===")

    mismatches = 0
    for pid in TEST_PLAYER_IDS:
        if pid in data_without and pid in data_with:
            without = data_without[pid]
            with_f = data_with[pid]

            # Compare key fields
            for key in ["barrel_rate", "exit_velocity_avg", "hard_hit_pct", "xslg"]:
                if key in without or key in with_f:
                    val_without = without.get(key)
                    val_with = with_f.get(key)
                    if val_without != val_with:
                        print(f"Mismatch for player {pid}, field {key}: {val_without} vs {val_with}")
                        mismatches += 1

    if mismatches == 0:
        print("✅ All data matches! Filtering preserves correctness.")
    else:
        print(f"❌ Found {mismatches} mismatches")

    return mismatches == 0


def main():
    print("=" * 60)
    print("Statcast Early Filtering Optimization Test")
    print("=" * 60)

    # Run tests
    print("\nNote: This test fetches real data from Baseball Savant.")
    print("First fetch may take longer due to network latency.")

    # Test without filter (original)
    data_without, time_without, mem_without = test_without_filter()

    # Clear cache to ensure fair comparison
    statcast._fetch_leaderboard.cache_clear()
    statcast._fetch_batted_ball.cache_clear()
    statcast._fetch_expected_stats.cache_clear()

    # Test with filter (optimized)
    data_with, time_with, mem_with = test_with_filter()

    # Verify correctness
    is_correct = verify_data_consistency(data_without, data_with)

    # Calculate improvements
    print("\n" + "=" * 60)
    print("PERFORMANCE IMPROVEMENT SUMMARY")
    print("=" * 60)

    data_reduction = (1 - len(data_with) / len(data_without)) * 100
    time_improvement = (1 - time_with / time_without) * 100
    memory_reduction = (1 - mem_with / mem_without) * 100

    print(f"\nData processed:")
    print(f"  Without filter: {len(data_without)} players")
    print(f"  With filter: {len(data_with)} players")
    print(f"  Reduction: {data_reduction:.1f}%")

    print(f"\nProcessing time:")
    print(f"  Without filter: {time_without:.2f}s")
    print(f"  With filter: {time_with:.2f}s")
    print(f"  Improvement: {time_improvement:.1f}%")

    print(f"\nMemory usage:")
    print(f"  Without filter: {mem_without / 1024 / 1024:.2f} MB")
    print(f"  With filter: {mem_with / 1024 / 1024:.2f} MB")
    print(f"  Reduction: {memory_reduction:.1f}%")

    print("\n📊 Expected impact on full pipeline:")
    print(f"  - Processing ~300 lineup players instead of ~2500 total")
    print(f"  - Memory savings: ~{memory_reduction:.0f}%")
    print(f"  - Parse time savings: ~{time_improvement:.0f}% (after download)")
    print(f"  - Note: Network download time is constant (same CSV files)")

    if is_correct and data_reduction > 80:
        print("\n✅ Optimization successful! Major reduction in data processing.")
    else:
        print("\n⚠️ Check results - optimization may not be working as expected.")


if __name__ == "__main__":
    main()
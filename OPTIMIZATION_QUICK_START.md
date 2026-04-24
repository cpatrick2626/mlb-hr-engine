# MLB HR Engine v4 - Quick Start Optimization Guide

## TL;DR

**Potential Gains:** 25-40% faster runtime + 30-50% memory reduction  
**Quick Wins:** 30% improvement in 2-3 hours  
**Full Optimization:** 50%+ improvement in 2-3 weeks

---

## Top 5 Critical Bottlenecks

### 1. 🔴 Odds Matching (80% speedup possible)
**Problem:** `_match_odds()` called 300+ times with O(n) lookups  
**File:** `pipeline.py` lines 162-188  
**Fix:** Pre-index odds into dict, change from O(n) to O(1) per lookup  
**Time:** 30 minutes  
**Impact:** 30-50ms per run

### 2. 🔴 Statcast CSV Parsing (50-70% speedup possible)
**Problem:** Parses all 2,500 players; filters to 300 needed  
**File:** `statcast.py` lines 310-483  
**Fix:** Filter to lineup members BEFORE parsing  
**Time:** 45 minutes  
**Impact:** 50-80 seconds per run

### 3. 🔴 MLB Stats API Redundancy (60% reduction possible)
**Problem:** ~500 API calls for data available in bulk  
**File:** `mlb_stats.py` lines 29-31, 64-83  
**Fix:** Fetch team rosters once, index locally  
**Time:** 1 hour  
**Impact:** 200+ fewer API requests

### 4. 🟠 Statcast Triple Fetch (60% latency reduction)
**Problem:** 6 HTTP requests (current + prior year × 3 data types)  
**File:** `statcast.py` lines 83-115  
**Fix:** Fetch current year only; lazy-load prior if needed  
**Time:** 45 minutes  
**Impact:** 50-100 seconds per run

### 5. 🟠 Sequential API Initialization (40% wall-time reduction)
**Problem:** Schedule → Odds → Statcast fetched sequentially  
**File:** `pipeline.py` lines 247-260  
**Fix:** Parallelize with ThreadPoolExecutor (max_workers=3)  
**Time:** 30 minutes  
**Impact:** ~50 seconds per run (if I/O-bound)

---

## Implementation Priority

### Phase 1: Quick Wins (2-3 hours) = 30-35% gain
```
1. Odds pre-indexing (30 min)          → -30-50ms
2. Statcast filter to lineup (45 min)  → -50-80s
3. Parallel API init (30 min)          → -40-50s
─────────────────────────────────────────────────
Total: ~2.25 hours → ~35% runtime improvement
```

### Phase 2: Core Optimization (4-6 hours) = 25-30% additional gain
```
1. MLB Stats bulk fetch (1 hour)       → -60% API calls
2. Consolidate Statcast fetches (1.5h) → -50-100s
3. P&L CSV indexing (1.5 hours)        → 90% tracking speed
─────────────────────────────────────────────────
Total: ~4 hours → Additional 25-30% improvement (compound ~55% total)
```

### Phase 3: Advanced (4-6 hours) = 30% for cache hits + 2x parlay speed
```
1. Disk cache layer (2 hours)          → 90% on re-runs
2. Parlay pre-scoring (1 hour)         → 10x faster
3. Refactoring (2 hours)               → Code quality
─────────────────────────────────────────────────
Total: ~5 hours → Cache hits, parlay speed 2x
```

---

## Code Examples for Top 3 Fixes

### Fix 1: Odds Pre-Indexing (30 min)

**Before (O(n) per player):**
```python
def _match_odds(player, all_props):
    prop_names = [p["player_name"] for p in all_props]  # Rebuild every call!
    match = fuzz_process.extractOne(player["player_name"], prop_names, ...)
```

**After (O(1) per player):**
```python
# Pre-process once in load_game_data()
odds_by_normalized_name = {}
for prop in all_props:
    norm = _normalize_name(prop["player_name"])
    if norm not in odds_by_normalized_name:
        odds_by_normalized_name[norm] = []
    odds_by_normalized_name[norm].append(prop)

# Then use in loop:
def _match_odds(player, odds_index):
    matches = odds_index.get(_normalize_name(player["player_name"]), [])
```

**Impact:** 80% speedup on odds matching (~30ms saved)

---

### Fix 2: Statcast Filter to Lineup (45 min)

**Before (parses all 2,500):**
```python
def get_batter_statcast(year):
    curr = _merge_batter_sources(year)  # Fetches/parses ~2,500 players
    # ... blending logic ...
```

**After (parses only 300):**
```python
def get_batter_statcast(year, lineup_ids=None):
    # If lineup known, pass set of IDs
    curr = _merge_batter_sources(year, filter_ids=lineup_ids)
    # In _fetch_leaderboard():
    if filter_ids:
        return {pid: row for pid, row in _parse(...) if pid in filter_ids}
```

**Impact:** 70% memory reduction, 50% parse time (~60s saved)

---

### Fix 3: Parallel API Init (30 min)

**Before (sequential):**
```python
_cb("Fetching schedule...")
games = mlb_stats.get_today_schedule(game_date)

_cb("Fetching odds...")
all_props, odds_source = odds_api.get_hr_odds_all_games()

_cb("Loading Statcast...")
batter_data = statcast_client.get_batter_statcast()
```

**After (parallel):**
```python
with ThreadPoolExecutor(max_workers=3) as executor:
    schedule_fut = executor.submit(mlb_stats.get_today_schedule, game_date)
    odds_fut = executor.submit(odds_api.get_hr_odds_all_games)
    statcast_fut = executor.submit(statcast_client.get_batter_statcast)
    
    games = schedule_fut.result()
    all_props, odds_source = odds_fut.result()
    batter_data = statcast_fut.result()
```

**Impact:** 40% wall-time reduction if I/O-bound (~40-50s saved)

---

## Testing Checklist

After implementing each optimization, verify:

```python
# 1. Correctness: outputs identical to baseline
python main.py > baseline.json
# ... apply optimization ...
python main.py > optimized.json
diff baseline.json optimized.json  # Should be near-identical

# 2. Performance: time improvements
time python main.py  # Note the runtime

# 3. Memory: check peak usage
import tracemalloc
tracemalloc.start()
# ... run code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 10**6:.1f} MB")
```

---

## Files to Modify (in order)

### Priority 1 (Week 1)
- [ ] `pipeline.py` - Odds pre-indexing + parallel API init
- [ ] `statcast.py` - Filter to lineup members
- [ ] Add unit tests for odds matching equivalence

### Priority 2 (Week 2)
- [ ] `mlb_stats.py` - Team stats bulk fetch
- [ ] `statcast.py` - Consolidate 3 fetches
- [ ] `tracking/pnl.py` - CSV indexing

### Priority 3 (Week 3)
- [ ] Add `util/cache.py` - Disk cache layer
- [ ] `output/parlay.py` - Pre-scoring
- [ ] Code cleanup & documentation

---

## Performance Monitoring

### Before Starting
```bash
# Establish baseline
python -m cProfile -s cumtime main.py 2>&1 | head -30
```

### After Each Phase
```bash
# Compare cumulative improvements
time python main.py

# Monitor specific components:
# 1. API calls: Add logging to mlb_stats._get()
# 2. Parsing time: Profile statcast.py with timeit
# 3. Memory: Use tracemalloc on batter_data load
```

---

## Common Pitfalls to Avoid

1. **Don't break output compatibility** - Maintain exact numeric precision
2. **Don't over-parallelize** - 3 threads is safe, 16+ risks API rate limits
3. **Don't cache indefinitely** - Add TTL/invalidation for Statcast
4. **Don't optimize prematurely** - Profile first, optimize bottlenecks
5. **Don't skip tests** - Run full suite after each change

---

## Questions?

Refer to the full analysis: `/Users/kylar/mlb-hr-engine/MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md`

Sections to review:
- Section 2: Performance Bottlenecks (detailed analysis)
- Section 6-9: Specific optimization strategies
- Section 12: Implementation roadmap with timelines


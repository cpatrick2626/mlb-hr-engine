# MLB HR Engine v4 - Analysis Documentation Index

**Analysis Date:** April 24, 2026  
**Status:** Complete and Ready for Review

---

## Document Overview

This directory contains comprehensive analysis and optimization recommendations for the MLB HR Engine v4 codebase.

### 1. **OPTIMIZATION_QUICK_START.md** (START HERE)
- **Length:** 246 lines, 7.3 KB
- **Audience:** Busy developers, decision makers
- **Time to Read:** 10-15 minutes
- **What's Inside:**
  - TL;DR with optimization potential
  - Top 5 critical bottlenecks
  - Phase 1-3 implementation roadmap with time estimates
  - 3 detailed code examples showing fixes
  - Testing checklist & performance monitoring guide
  - Common pitfalls to avoid

**Best for:** Getting started quickly, understanding the scope, making implementation decisions.

---

### 2. **MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md** (COMPREHENSIVE)
- **Length:** 843 lines, 27 KB
- **Audience:** Engineers, technical architects
- **Time to Read:** 30-45 minutes
- **What's Inside:**
  - Executive summary
  - Complete architecture overview with file structure
  - 9 major bottleneck sections with detailed analysis
  - Current caching mechanisms & gaps
  - Data persistence & storage analysis
  - Algorithm complexity analysis
  - 6 concrete API optimization strategies
  - 2 data structure optimization approaches
  - 8 memory efficiency recommendations
  - Code-level optimization techniques
  - Tier 1-3 recommendations summary (prioritized)
  - 3-phase implementation roadmap
  - Testing strategy with validation approach
  - Risk assessment & mitigation
  - Further reading resources

**Best for:** In-depth understanding, implementation planning, architectural decisions.

---

### 3. **ANALYSIS_INDEX.md** (THIS FILE)
- **Purpose:** Navigation and document guide
- **What's Inside:** Quick reference to all analysis materials

---

## Quick Navigation by Use Case

### "I have 2 hours - what should I do?"
1. Read **OPTIMIZATION_QUICK_START.md** (10 min)
2. Implement Phase 1, Part 1 (Odds pre-indexing) (30 min)
3. Implement Phase 1, Part 2 (Statcast filter) (30 min)
4. Test & benchmark (10 min)

**Expected Result:** 30-35% runtime improvement

---

### "I'm planning a week-long optimization sprint"
1. Read **OPTIMIZATION_QUICK_START.md** (15 min)
2. Read **MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md** sections 1-5 (30 min)
3. Set up performance monitoring (30 min)
4. Execute Phase 1 (2-3 hours)
5. Execute Phase 2 (4-6 hours)
6. Execute Phase 3 (4-6 hours)

**Expected Result:** 50%+ compound runtime improvement

---

### "I need to understand the codebase architecture"
1. Read **CLAUDE.md** (existing, 4.6 KB)
2. Review **MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md**, Section 1 (architecture overview)
3. Review file structure in Section 1

---

### "Which file has the most critical issue?"
**Answer:** `pipeline.py` - Contains 3 critical bottlenecks:
1. O(n²) odds matching (lines 162-188)
2. Sequential API initialization (lines 247-260)
3. Inefficient data structure patterns (lines 24-159)

See **MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md**, Section 2 for details.

---

## Key Statistics

| Metric | Current | Target | Gain |
|--------|---------|--------|------|
| **Runtime** | 90-120s | 55-75s | 35-40% |
| **Memory** | 15-20 MB | 8-12 MB | 40-50% |
| **API Calls** | ~500 | ~200 | 60% |
| **Statcast Parse** | 60-100s | 15-30s | 60-70% |

---

## Implementation Phases

### Phase 1: Quick Wins (2-3 hours) = 35% gain
```
Odds pre-indexing (30 min)
Statcast filter to lineup (45 min)
Parallel API init (30 min)
```

### Phase 2: Core (4-6 hours) = Additional 25-30% gain
```
MLB Stats bulk fetch (1 hour)
Consolidate Statcast (1.5 hours)
P&L CSV indexing (1.5 hours)
```

### Phase 3: Advanced (4-6 hours) = 30% cache hits + 2x parlay
```
Disk cache layer (2 hours)
Parlay pre-scoring (1 hour)
Refactoring (2 hours)
```

---

## Files Analyzed

### Core Pipeline
- **pipeline.py** (347 LOC) - 3 critical bottlenecks
- **main.py** (130 LOC) - No bottlenecks (CLI wrapper)
- **app.py** (1,510 LOC) - Caching opportunity

### Data Clients
- **clients/mlb_stats.py** (376 LOC) - API redundancy
- **clients/statcast.py** (502 LOC) - CSV parsing & triple fetch
- **clients/odds_api.py** (150+ LOC) - No critical issues
- **clients/weather.py** - No bottlenecks

### Engine Modules
- **engine/probability.py** (369 LOC) - Efficient, no bottlenecks
- **engine/market.py** (91 LOC) - Efficient
- **engine/ev.py** (39 LOC) - Efficient
- **engine/filters.py** (68 LOC) - Efficient
- **engine/sizing.py** (68 LOC) - Efficient

### Output & Tracking
- **output/parlay.py** (326 LOC) - Pre-scoring opportunity
- **output/ranker.py** (37 LOC) - Efficient
- **output/display.py** (288 LOC) - Display only
- **tracking/pnl.py** (282 LOC) - CSV indexing opportunity
- **tracking/clv.py** (216 LOC) - Minor caching opportunity

---

## Critical Code Locations

| Issue | File | Lines | Severity |
|-------|------|-------|----------|
| Odds matching O(n²) | pipeline.py | 162-188 | CRITICAL |
| Statcast CSV parsing | statcast.py | 360-483 | CRITICAL |
| API redundancy | mlb_stats.py | 29-31, 64-83 | CRITICAL |
| Triple fetch | statcast.py | 83-115 | HIGH |
| Sequential API fetch | pipeline.py | 247-260 | HIGH |
| CSV full-load | tracking/pnl.py | 177-186 | HIGH |
| Dict copying | pipeline.py | 39, 285-289 | MEDIUM |
| Parlay scoring | output/parlay.py | 150-300+ | MEDIUM |
| Exception overhead | statcast.py | 428-447 | MEDIUM |

---

## Testing & Validation

### Before Starting
```bash
python -m cProfile -s cumtime main.py 2>&1 | head -30
```

### After Each Phase
```bash
time python main.py > optimized.json
diff baseline.json optimized.json
```

### Success Criteria
- Output equivalence (within 0.01% precision)
- Runtime improvement >20% per phase
- Memory reduction >15% for Statcast changes
- No API rate limit breaches

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cache invalidation | Medium | Add TTL, versioning |
| Rate limiting | Medium | Use 3 threads max, backoff |
| Output compatibility | Low | Test equivalence |
| Over-optimization | Low | Profile first, measure |

---

## Next Steps

1. **Today:** Read OPTIMIZATION_QUICK_START.md
2. **Tomorrow:** Read full analysis, set up baseline metrics
3. **Week 1:** Implement Phase 1 (2-3 hours)
4. **Week 2:** Implement Phase 2 (4-6 hours)
5. **Week 3:** Implement Phase 3 (4-6 hours)

---

## Document Version History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2026-04-24 | Claude Code | Complete |

---

## Related Documentation

- **CLAUDE.md** (existing) - Architecture overview
- **SETUP.md** (existing) - Setup instructions
- **Codebase docstrings** - Inline documentation

---

## Questions or Issues?

Refer to the appropriate document:
- **"What should I optimize first?"** → OPTIMIZATION_QUICK_START.md
- **"How do I implement optimization X?"** → MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md, Section 6-9
- **"What's the implementation timeline?"** → Both documents have roadmaps
- **"How do I measure improvements?"** → OPTIMIZATION_QUICK_START.md, Testing Checklist

---

**Analysis complete. Ready for implementation.**

Generated with Claude Code - April 24, 2026

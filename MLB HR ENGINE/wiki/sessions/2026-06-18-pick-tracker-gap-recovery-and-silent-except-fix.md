# 2026-06-18 — Pick Tracker Gap: Recoverability Audit + Silent Except Fixes

**Room:** RUNTIME & STABILITY COMMAND (08)  
**Agent:** Claude Code  
**Scope:** READ-ONLY recoverability audit (Task A/B/C) + live fixes to app.py (Task 2)

---

## TASK A: Recoverability Audit — Jun 1–17 Gap in pick_tracker.csv

### The Gap
`pick_tracker.csv` has 4608 rows covering **May 13–31 only**. Zero rows for any Jun date.
All May rows are `source_tab="Engine"` — meaning L389's `_pt.log_picks_bulk()` was the only write path ever used. The FD Slip deploy path (L11461) never produced a confirmed write.

### Candidate Source Log Coverage — Jun 1–17

| Log | Jun 6 | Jun 15 | Other Jun 1–17 dates |
|-----|-------|--------|----------------------|
| picks_log.csv | 46 rows | 5 rows | **ZERO** |
| full_slate_log.csv | 0 rows | 162 rows | **ZERO** |
| line_snapshots.csv | 271 rows (opening+closing) | 5 rows (opening only) | **ZERO** |
| clv_log.csv | 46 rows | 5 rows | **ZERO** |
| pick_tracker.csv | **ZERO** | **ZERO** | **ZERO** |

### Deployed-State Distinguishability
**Critical finding**: No local log has a `deployed`, `source_tab="FD Slip"`, or any deployment-state column.

- `picks_log.csv` schema: date, model_version, player_id, player_name, team, opponent, pitcher, lineup_spot, model_prob_pct, market_prob_pct, ev_pct, edge_pct, american_odds, bet_dollars, park_factor, pitcher_factor, weather_factor, season_pa, recent_pa, confidence, score, streak_factor, barrel_pct, xslg, platoon_factor, statcast_source — **NO deployment indicator**
- `line_snapshots.csv` has `snapshot_type: opening | closing` but these are engine-pipeline triggered, not operator-deploy triggered
- Supabase picks table: **NOT CHECKED** — requires live DB access. Unknown coverage.

### Task B: Jun 16–17 Specifically
- All candidate logs: **ZERO rows** for Jun 16 and Jun 17
- The empty-slip toast bug (L11447) would show "All selected players already logged today" when `_selected=[]`
- Consistent with operator seeing confirmation but nothing actually logging
- These two days are **genuinely no-log** — either no deployment occurred OR the empty-slip bug masked a real deploy attempt
- Cannot distinguish from local logs alone

### Task C: Reconstruction Feasibility

| Date range | Local log coverage | Deployed-state recoverable? |
|------------|-------------------|----------------------------|
| Jun 1–5 | NONE | NO |
| Jun 6 | picks_log + line_snapshots + clv_log (engine output) | NO — can't distinguish deployed vs. qualified |
| Jun 7–14 | NONE | NO |
| Jun 15 | picks_log + line_snapshots + clv_log (5 rows, engine output) | NO — same issue |
| Jun 16–17 | NONE | NO — likely no deployment, not just lost log |

### VERDICT: UNRECOVERABLE (from local logs)

Deployed-state is not distinguishable from engine-qualified state in any local log. Even for Jun 6 and Jun 15 where engine output is logged, we cannot confirm what the operator actually deployed to FD.

**Calibration implication**: The "no demonstrable edge" calibration audit was computed on `pick_tracker.csv` covering May 13–31 only. Jun 1–17 deployed picks are MISSING. Calibration conclusions must not be trusted until:
1. Supabase picks table is queried for Jun 1–17 coverage, OR
2. The gap is declared permanently unrecoverable and calibration restarts from reconciliation forward

---

## Root Cause: Why Did L389 Stop Writing After May 31?

All 4608 May rows in `pick_tracker.csv` came from the `source_tab="Engine"` path (L389's `_pt.log_picks_bulk()`). The pipeline ran on Jun 6 and Jun 15 (picks_log.csv confirms this), but pick_tracker.csv received nothing. This means `_pt.log_picks_bulk()` started throwing an exception silently after May 31, swallowed by L389's `except Exception: pass`.

The exception itself was never visible — which is exactly what the fixes below address.

---

## TASK 2: Fixes Applied to app.py

### FIX 1 — Unwrap silent exception at L11461 (FD Slip pick_tracker write)

**Before:**
```python
                    except Exception:
                        pass
```

**After:** Log to `getLogger("app")` + `st.error()` so operator sees failure immediately.

**File/line:** `mlb_hr_engine_v4/app.py` L11461 area

### FIX 2 — Misleading empty-slip toast

**Before:** Empty `_selected` → `log_slip_picks([])` → returns 0 → shows "All selected players already logged today."

**After:** Explicit `if not slip_players: st.warning("No players selected — nothing to log.")` before any log call. The "already logged" message is now only reachable when players ARE selected but all pre-exist.

**File/line:** `mlb_hr_engine_v4/app.py` L11441 area

### HIGH bare-excepts also fixed (same pattern, same root cause)

| Location | Operation | Fix applied |
|----------|-----------|-------------|
| L389 | `_pt.log_picks_bulk()` engine pipeline | `logger.error + st.warning` |
| L3611 | `_pt.log_pick()` modal add-to-slip | `logger.error + st.warning` |
| L3766 | `_pt.log_pick()` bulk add-to-slip | `logger.error + st.warning` |
| L11461 | `_pt.log_pick()` FD Slip "Save for Results" | `logger.error + st.error` |

### MED/LOW bare-excepts — reported, NOT fixed

These wrap non-persistence operations. No data loss risk. Operator review:

| Line | Wraps | Risk |
|------|-------|------|
| L411 | `fn.clear()` cache clear | LOW — benign |
| L433 | `_ms_clear/sc_clear.clear_all_caches()` | LOW — cache clear |
| L451 | `_pm_clear/_ar_clear.clear_caches()` | LOW — cache clear |
| L1724 | Pitcher change detection | MED — silent degradation of pitcher alert |
| L6242 | Steam move details builder | MED — display degraded silently |
| L6869 | Icon file load | LOW — display only |
| L10243 | Pending count display | MED — performance tab shows stale |
| L10326 | CLV display | MED — display degraded |
| L11070 | Bankroll display | LOW — display only |
| L1975, L1988 | Query params | LOW — routing fallback |
| L3796–3869 | Various UI returns | LOW — display fallback |
| L9794 | Unknown (not inspected) | TBD |

---

## Standing Rule (to add to doctrine)

**Bare `except: pass` on any persistence path is forbidden.** This pattern has caused silent data loss TWICE:
1. Cloud-capture loop (prior session)
2. pick_tracker write paths (Jun 1–17 gap)

Lint/CI rule candidate: `grep -n "except Exception:\s*$\|except:\s*$" app.py` followed by manual check of next line for `pass`.

---

## Deployment Note

app.py runs via Streamlit locally (not Fly.io). Per commit-before-deploy invariant:
**commit → push → verify** before running the fixed app.

The fix is code-complete. DO NOT commit/push until operator authorizes.

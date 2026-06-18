# Session: 2026-06-17 — Tracking Infrastructure Overhaul

**Date:** 2026-06-17
**Agent:** Claude Code
**Room:** MAIN SKILLS / Data Integrity
**Risk:** LOW → MEDIUM (ops infrastructure + Fly volume remount; no model/pipeline/MAIN-JIG changes)

---

## Arc

Session began with a question about demonstrable edge — do we have calibration evidence? That inquiry exposed a chain of silent failures running deeper than any single bug. The through-line: **something reporting success while doing nothing**. Every root cause this session shared that shape.

---

## The Silent-Failure Cascade

### Pattern

Silent success masking real failure is the highest-risk failure mode in an ops system. It produces false confidence and starves downstream data. Every bug found today exhibited it.

### Instances Found

| Bug | Surface | Shape |
|-----|---------|-------|
| Hard Hit% logged as `0` | batter profiles | key mismatch: `"hard_hit"` vs `"hard_hit_pct"` — silently wrote zero |
| P&L reading dead file | Streamlit `app.py` | dashboard reading stale `pick_tracker.csv`, not the live surface |
| Settlement endpoint returned `{"queued"}` | `POST /api/ops/settle` | endpoint responded 200 but settlement script silently crashed |
| `sys.exit(1)` bypassed exception handler | `settle_pick_tracker.py` | `sys.exit` raises `SystemExit` → not caught by `except Exception` → silent crash |
| CLV returned `{}` on missing key | `clv.py` | `ODDS_API_KEY` absent → function returned empty dict, no error raised |
| **THE BIG ONE: Fly volume shadowed tracking code** | Fly deployment | volume mounted at `/app/tracking` overlapped the `tracking/` Python package → every `from tracking import X` raised `ModuleNotFoundError` on Fly → settlement + CLV had **never worked in production** |

### The Fly Volume Shadow

The root cause of production-level data starvation: the Fly volume was mounted at `/app/tracking`, which is the same path as the `tracking/` Python package inside the container. The volume's presence at that path hid the code directory from the Python runtime. Every import from the tracking package failed silently (or with a caught generic exception) since deployment. The volume was also empty — no production tracking data had ever persisted.

---

## Root-Cause Chain on Settlement

```
GitHub Actions cron
  → POST /api/ops/settle
    → settle_pick_tracker.py
      → targeted pick_tracker.csv  ← DEAD (starved since ~May 31 when
                                         daily ops moved to Fly cron at launch)
```

Live picks log to `picks_log.csv`. Settlement writes to `results.csv`. `pick_tracker.csv` was a third, abandoned store. Three stores, no single tracker of record.

---

## Fixes (with Commits)

| Commit | Change |
|--------|--------|
| `7332336` | Settlement redirected to live store (`pnl.settle_all_unsettled`) + visible-failure guard (`BaseException` + explicit logging so SystemExit no longer silences crashes) |
| `eb66a3c` | Centralize CSV paths via `TRACKING_DATA_DIR` (`_paths.py`) — single source of truth for all tracking file locations |
| `3fd1a8d` | Remount Fly volume `/app/tracking` → `/data` (unshadow the Python package) + seed volume from image CSVs so existing data carries over |
| `9a2156d` | `clv.py` raise-on-missing-key (warning + return empty, not silent pass) + vault index update |
| `af85399` | Reconcile `clv_log` entries → `results.csv` for `drift_monitor` (Phase 2 completion) |

### Verification

After remount + redeploy: `settle_pick_tracker.py` wrote 5 Jun-15 picks to `/data/results.csv`. Restarted Fly machine. File persisted. First confirmed end-to-end settlement in production.

---

## Key Learnings (Data-Integrity Curriculum)

1. **Make failures loud.** Use `BaseException` + explicit logging for ops scripts. `except Exception` silently swallows `SystemExit`, `KeyboardInterrupt`, etc.
2. **Deploy and verify, never deploy and assume.** The loud failure surfaced the import bug immediately after remount; without that signal the volume shadow would have persisted indefinitely.
3. **Confirm the live surface before fixing.** P&L + filter were both investigated/chased on `app.py` (Streamlit dashboard) before confirming it was not the live operator surface. Time lost.
4. **Volume mounts can shadow code.** Keep data volumes on paths that cannot overlap Python package names or source directories.
5. **Read-only audit → operator review → authorized fix.** Kept high-risk changes (volume remount, endpoint redirect) reversible and operator-confirmed before execution.

---

## Open / Deferred

| Item | Status |
|------|--------|
| Phase 3: CLV into `auto_learn` FEATURES | Deferred — requires n≥200 settled real picks; noted in commit `af85399` |
| Cold-load UX (first-load spinner / state) | Deferred — not scoped this session |
| Agent-bench sourcing | Deferred — noted for future seats |
| Hard Hit% key mismatch fix | Identified; not yet committed — operator to authorize |

---

## Files Touched

- `mlb_hr_engine_v4/tracking/_paths.py` (new)
- `mlb_hr_engine_v4/tracking/clv.py`
- `mlb_hr_engine_v4/tracking/pnl.py`
- `mlb_hr_engine_v4/scripts/ops/settle_pick_tracker.py`
- `mlb_hr_engine_v4/api/main.py` (settle endpoint)
- `fly.toml` (volume remount)
- `MLB HR ENGINE/wiki/` (index updates)

---

## Cross-References

- [[deploy-runbook]] — Fly.io volume path, remount procedure
- [[data-integrity]] — silent-failure patterns, tracking store map
- [[known-gaps]] — Hard Hit% key mismatch, CLV starvation history
- [[feature-backlog]] — Phase 3 CLV deferred item

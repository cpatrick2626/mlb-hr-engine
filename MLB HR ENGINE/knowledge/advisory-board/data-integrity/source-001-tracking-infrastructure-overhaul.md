---
seat: data-integrity
source_id: "001"
title: Tracking Infrastructure Overhaul
source_type: internal-session
source_file: "wiki/sessions/2026-06-17-tracking-infrastructure-overhaul.md"
date_ingested: 2026-06-17
key_people: "--"
status: ingested
---

## Summary

Session documenting a chain of silent failures discovered during a calibration-evidence audit on 2026-06-17. Every failure shared the same shape: **something reporting success while doing nothing**. Root causes ranged from key mismatches to a Fly volume that shadowed the entire `tracking/` Python package, meaning settlement and CLV had never worked in production since deployment. Session resolved all six failure instances, established verified end-to-end settlement for the first time, and produced a reusable data-integrity curriculum.

---

## Key Concepts

| Concept | Notes |
|---------|-------|
| Silent-failure pattern | System reports success (200 OK, "queued", `{}`) while writing nothing. Highest-risk failure mode — produces false confidence, starves downstream data. |
| Volume-path shadowing | Fly volume mounted at `/app/tracking` overlapped the `tracking/` Python package. Python runtime read the empty volume directory, not the code. Every `from tracking import X` raised `ModuleNotFoundError` in production since launch. |
| Dead-store problem | Three competing tracking stores existed: `picks_log.csv`, `pick_tracker.csv`, `results.csv`. Settlement targeted `pick_tracker.csv`, which had been abandoned since May 31. Writes succeeded; reads returned stale/empty data. |
| `BaseException` vs `except Exception` | `sys.exit(1)` raises `SystemExit`, a subclass of `BaseException` not `Exception`. Settlement script's `except Exception` silently swallowed the crash; ops endpoint returned 200 while the script had failed. |
| Deploy-and-verify | After Fly volume remount + redeploy, ran settlement end-to-end and confirmed 5 picks written to `/data/results.csv`. File persisted across machine restart. First confirmed production settlement. |
| Confirm-the-live-surface | Streamlit `app.py` was investigated for P&L display bugs before confirming it was not the live operator surface. Time lost chasing the wrong surface. |
| `TRACKING_DATA_DIR` centralization | `_paths.py` introduced as single source of truth for all tracking file paths. Removes per-file path strings scattered across modules. |

---

## Decision Principles for Data Integrity

1. **A 200 OK / "queued" / `{}` is not proof of work.** Verify the write actually landed — check the target file, confirm row count, restart the process and re-read. A success response only proves the request was received.
2. **Data paths and code paths must never overlap.** Volume mounts, symlinks, and working-directory choices must be verified against Python package names and source directory structure. A data volume at `/app/tracking` destroys the `tracking/` package.
3. **Make failures loud with `BaseException`.** Ops scripts that call `sys.exit` or external processes must catch `BaseException`, not `Exception`. Silent swallow of `SystemExit` is an integrity hole, not defensive coding.
4. **One tracker of record.** Multiple competing stores with overlapping purpose create dead-store risk. Establish a canonical file for each data type; retire abandoned stores explicitly. Do not leave orphaned CSVs that look authoritative.
5. **Confirm the live surface before debugging.** Before investigating a display or data problem, verify which surface the operator actually uses. Debugging a dormant surface wastes investigation time and may produce misleading fixes.
6. **Deploy-and-verify, never deploy-and-assume.** After any infrastructure change (volume remount, path centralization, endpoint redirect), run the full operation end-to-end and confirm the output artifact exists and persists. Assumption of correctness is how silent failures survive indefinitely.

---

## Direct Relevance to Data Integrity Seat

- Provides six concrete failure archetypes the seat can use as integrity checklist items when evaluating any new tracking or ops change.
- The silent-failure pattern is the canonical threat model for this seat: if an operation can succeed silently while failing materially, it needs a loud failure guard.
- Volume-path shadowing is a deployment-specific variant of the same pattern — data-integrity review must include deployment path verification, not just code correctness.
- `BaseException` rule applies to any ops script in `scripts/ops/` that calls `sys.exit` or wraps external processes.
- Dead-store awareness: when multiple CSVs or data stores overlap in purpose, the seat should flag which is canonical and which should be retired.

---

## Data Gaps / Deferred

| Topic | Status |
|-------|--------|
| Idempotency guarantees for settlement re-runs | DATA GAP — external pipeline-integrity theory; needs /web-scraping session |
| Schema validation frameworks (e.g., Pandera, Great Expectations) | DATA GAP — external tooling; not yet evaluated |
| Automated data-quality monitoring patterns | DATA GAP — external observability frameworks; deferred |
| Hard Hit% key mismatch fix (`"hard_hit"` vs `"hard_hit_pct"`) | IDENTIFIED, NOT YET COMMITTED — operator authorization pending |
| Phase 3 CLV auto_learn integration | DEFERRED — requires n≥200 settled real picks |

---

## Takeaways

- Silent failure is the threat model for ops integrity. Every fix this session made a failure loud where it had been quiet.
- Volume path shadowing is a whole class of silent failure unique to containerized deployments — check mount paths against code paths on every Fly/Docker change.
- `BaseException` in ops scripts is not optional. A `sys.exit`-catching-only pattern will mask crashes indefinitely.
- One tracker of record, confirmed live, verified by end-to-end write after every deployment change.

---

## Related Wikilinks

- [[tracking-infrastructure-overhaul]] — source session page
- [[deploy-runbook]] — Fly.io volume path, remount procedure
- [[known-gaps]] — Hard Hit% key mismatch, CLV starvation history
- [[feature-backlog]] — Phase 3 CLV deferred item
- [[data-integrity]] — cross-reference to this seat's concept space

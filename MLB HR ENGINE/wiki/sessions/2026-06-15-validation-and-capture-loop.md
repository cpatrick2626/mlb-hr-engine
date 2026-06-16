# Session: 2026-06-15 — Engine Validation Audit + Cloud Capture Loop

**Date:** 2026-06-15
**Agent:** Claude Code
**Room:** Obsidian Governance Update
**Risk:** LOW (ops/infrastructure changes + documentation capture)

---

## Arc

Two related workstreams completed in this session:
1. First calibration audit — what we can actually conclude from accumulated data.
2. Root-cause fix for thin data sample (broken settlement) + migration of all capture jobs to cloud.

---

## Engine Validation — First Calibration Audit

Ran calibration on settled picks. Sample: **737 settled picks, 13 May dates**.

### Findings

- **Mid-range buckets (5–15%)**: well-calibrated, within ~1pp of observed rates.
- **20%+ bucket**: over-predicts by ~11pp — but n=25, untrustworthy.
- **Brier Skill Score**: +1.04% vs naive baseline — marginal, noise-level at this n.
- **YELLOW FLAG**: Qualified/recommended picks over-predict ~3.4pp. v4-tagged picks slightly worse than naive. The model is most over-confident on the picks it most recommends. Watch as sample grows; **do NOT act on this yet**.
- **Tier column absent** from pick_tracker: tier-vs-outcome validity unmeasurable at time of audit (now fixed — full_slate_log captures tier).
- **CLV unavailable**: closing odds were not being captured at all.

### Takeaway

Product is an unproven high-variance tool at current data scale. Picks are unvalidated. Size action responsibly. **Re-run calibration monthly** as data accumulates toward 2,000+ settled picks (full-season minimum for threshold/calibration changes per operator doctrine).

---

## Capture Loop — Root Cause + Cloud Migration

### Root Cause (Thin Sample)

Daily settlement was **silently broken**. Local Windows Task Scheduler was firing a no-op via two path bugs — `run_ops_daily.bat` and `settle_pick_tracker.py ROOT` both had wrong paths. No error surfaced, no picks were being settled.

### Step 1 — Local Fixes (commit `5bb17b4`)

- Fixed settlement paths in `run_ops_daily.bat` and `settle_pick_tracker.py`.
- Created `capture_closing_lines.py` + companion bat.
- Added `log_all_players()` → `full_slate_log.csv` (all players + tier/role/qualified/model_version per day). `picks_log.csv` untouched.

### Step 2 — Cloud Migration (commit `0e115dc`)

Moved all capture jobs **off the laptop**:

| New Surface | What It Does |
|-------------|-------------|
| `POST /api/ops/settle` | Settlement endpoint, `X-Cron-Secret` gated, reuses existing script logic, writes to Fly volume `/app/tracking` |
| `POST /api/ops/clv-capture` | CLV capture endpoint, same auth, same volume |
| `api/cron.py` full-slate log | `log_all_players()` folded into existing pipeline cron |
| `.github/workflows/daily_settle.yml` | Fires 6AM ET daily |
| `.github/workflows/clv_capture.yml` | Fires 12:30PM + 6:30PM ET (day + night first-pitch coverage) |

CSVs persist on Fly volume. Not committed to git.

**Scope:** ALL capture/scheduling/IO changes only — zero model/config/MAIN-JIG impact.

### Architecture Note

The model pipeline was already cloud-native (GitHub Actions cron → Supabase + Fly volume). Only the 3 capture jobs were laptop-bound. Now they aren't.

---

## Operator Action Items

| Status | Action |
|--------|--------|
| DONE | Cloud endpoints live and verified (return `queued`) |
| TODO (local) | **Disable** Windows Task Scheduler jobs (`run_ops_daily.bat`, `run_capture_closing_lines.bat`) — now redundant with cloud; running both risks double-writes |
| Future (deferred) | Consider Supabase migration for tracking data **if/when** dashboard needs to query settlement/CLV (Option C from scoping; not needed now — CSV-on-volume is fine) |

---

## Cross-References

- [[feature-backlog]] — validation-first priority + future data features
- [[deploy-runbook]] — Fly.io volume, deploy procedure
- [[known-gaps]] — tier column gap (now fixed via full_slate_log)

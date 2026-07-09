# Session 2026-07-09 — Calibration Rollout + Settlement Repair

## Summary

Multi-day session arc culminating 2026-07-09. Major shipped items: prob_scale calibration lift (1.12), MIN_EV_PCT tightening, RLS security fix, strategy rail honesty remediation, CRON_SECRET realignment, July 8 manual settle backfill, and full auto-settlement workflow. Key discoveries: auto-learner remainder-bucket bug (prob_scale stuck at 0.88 for weeks), /api/ops/settle was wired to a dead path, pick_tracker auto-settlement has a hardcoded-path prod bug.

---

## Calibration fix — SHIPPED, live on production

- **prob_scale 0.88 → 1.12.** Validated on 3,828 settled rows: board was under-predicting HR probability ~21% (0.88 too aggressive). 1.12 closes ~90% of the aggregate gap (avg model_prob 8.3% → ~10%; actual HR rate ~10%). Verified live through the real scale → Platt chain (0 mismatches / 314 players).
- **prob_scale lives in the Fly volume file `/data/learned_adjustments.json`** (gitignored) — NOT in git. Rollout required: `flyctl deploy` + SSH-edit the volume + machine restart. Future changes are volume edits, not commits.
- **AUTO_LEARN_FROZEN=True** set in `pipeline.py` (commit `956be0d`) — freezes auto-learn WRITE so it cannot auto-revert 1.12. Scoring READ of prob_scale unchanged. Must stay frozen until the auto-learner bucket bug is fixed.
- **MIN_EV_PCT 3.0 → 14.0** (commit `865f66d`) — normalizes qualified-pick volume (~8-9/slate) at the lifted probabilities. Static config knob (adaptive min_ev_pct clamps at 8, cannot reach 14). EV sweep showed higher-EV picks trend more profitable but on thin samples — 14 chosen (restores familiar volume, avoids overfitting noisy ROI).
- **KNOWN:** prob_scale is at the read-clamp ceiling (adaptive_weights clamp is 0.80–1.20; 1.12 passes). The 0.29 model_prob cap is now reachable for top players on hot slates — watch for cluster-pinning.

---

## Auto-learner remainder-bucket bug — discovered, NOT fixed (backlog)

The auto-learner (`tracking/auto_learn.py`) agrees the board under-predicts, but a remainder-bucket bug corrupts its scale computation:

- 3,828 rows / 5 buckets = 3 leftover rows (highest-prob picks, 0-for-3) form a poison bucket that drags total_bias to the wrong sign.
- Bug computes 0.734 → clamped to 0.88 floor → "no change." Excluding the 3-row remainder, it correctly computes 1.12.
- This is why prob_scale was stuck at 0.88 for weeks.
- **Fix:** merge the final sub-size bucket into the penultimate one. Fable-tier (scoring-adjacent).
- **Also:** raise the adaptive min_ev_pct clamp (currently 8.0) before unfreezing, or auto-learn would drop the EV floor below 14.

---

## Strategy rail honesty fix — SHIPPED, commit `77f8354`, verified live

- Removed fabricated "HR ENV SCORE" (was `6 + avg(hrprob) × 0.17`, not environmental) from all rail cards.
- ELITE SPOT → real MODEL HR%; PARK BOOST → real PARK HR factor; POWER STACK / HOT STREAK → HEURISTIC tags; VALUE SPOT → MODEL QUALITY; PLATOON EDGE → BAT-HAND LENS.
- Stopped writing fabricated `hr_env_score` into ticket capture.
- Display-only; no scoring leak.

---

## picks RLS security fix — DONE, production SQL

- `alter table public.picks enable row level security;` run on prod.
- No policies needed (all app access = service-role bypass; frontend never reads picks directly).
- Closed anon-key read/write gap on 4,590 rows. App verified working after.
- Instant revert: `disable row level security`.
- No git artifact — production DDL only.

---

## Settlement repair — major, multi-part

### Root cause

Fly `CRON_SECRET` was mismatched — `settle` (`daily_settle.yml`) + `clv` (`clv_capture.yml`) crons had been 401ing since ~June 16–19 (visible failures, unnoticed). Pipeline cron unaffected (GH Actions, no secret involved).

### CRON_SECRET fix

Re-aligned `CRON_SECRET` on both Fly (`flyctl secrets set`) and GitHub Actions (`gh secret set`) to `mlb-hr-engine-cron-2026` (the `.env` / code-expected value). Verified `/api/ops/settle` returns 200.

### Dead path discovered

Even with auth fixed, `/api/ops/settle` was wired to a dead path (`pnl.settle_all_unsettled` → legacy local P&L, NOT the Supabase legs ledger). The real resolvers are separate:
- `api/settle_legs.py` — legs ledger, CLI `--commit --date`, idempotent / pending-guarded.
- `scripts/ops/settle_pick_tracker.py` — `pick_tracker.csv` calibration data (STILL MANUAL — see below).

### July 8 manual backfill

Ran `settle_legs.py --commit --date 2026-07-08` manually — 30 legs settled (6 HR / 24 no), verified against MLB boxscores.

### Auto-settlement workflow — SHIPPED, commit `c7805e2`

New `.github/workflows/settle_legs.yml` runs `settle_legs.py --commit --date <yesterday-ET>` daily at 10:00 UTC + `workflow_dispatch`. Mirrors `daily_pipeline.yml` pattern, uses existing `SUPABASE_URL` / `SERVICE_KEY` secrets, idempotent. Tested via manual dispatch (July 8 → 0 rows, correct — already settled). Old `daily_settle.yml` DISABLED (`gh workflow disable`). Legs ledger now auto-settles; no more manual backfills.

### Still manual — pick_tracker auto-settlement (backlog)

`settle_pick_tracker.py` has a hardcoded-path bug: ignores `TRACKING_DATA_DIR`, hardcodes `ROOT/tracking/pick_tracker.csv`; prod uses `/data` volume. Needs prod `/data/pick_tracker.csv` investigation + path fix before auto-wiring. `pick_tracker` is stale after May 31.

### CLV gap

Auth now works so going-forward CLV capture will run. June 16 – July 9 missed CLV windows are likely unrecoverable (closing lines gone). CLV is a quality metric, not core HR prediction.

---

## Tooling (earlier this session arc)

- Code-reviewer subagent (`.claude/agents/code-reviewer.md`, read-only, doctrine-tuned) — used to gate every scoring-adjacent commit this session.
- Supabase read-only MCP connected (`.mcp.json`, gitignored) — used for direct ledger queries throughout.
- Graphify mechanism documented: freshness = `python .claude/graphify_freshness.py`; refresh = `graphify update mlb_hr_engine_v4`; scope = backend only (`frontend/`, `Docs/` excluded via `.graphifyignore`).

---

## Commits shipped this session

| Hash | Description |
|------|-------------|
| `c7805e2` | feat(settlement): auto-settle Supabase legs ledger daily via GH Actions |
| `865f66d` | chore(calibration): MIN_EV_PCT 3.0→14.0 for prob_scale=1.12 volume |
| `956be0d` | chore(calibration): freeze auto-learn write path (AUTO_LEARN_FROZEN) |
| `2ebc333` | docs: record strategy rail honesty fix |
| `77f8354` | fix(rail): remove fabricated HR ENV SCORE, honest labels + HEURISTIC tags |
| `0a17213` | chore(tooling): add read-only code-reviewer subagent + gitignore .mcp.json |

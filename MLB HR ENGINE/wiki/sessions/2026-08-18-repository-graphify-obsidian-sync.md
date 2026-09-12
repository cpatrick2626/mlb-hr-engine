# Repository, Graphify, and Obsidian Synchronization — 2026-08-18

> **Historical checkpoint.** Its Graphify state was true only for the 2026-08-18 snapshot at `d71a2ad`. The current 2026-09-12 checkout is STALE relative to the primary generated output; use source inspection and do not regenerate Graphify under this task.

**Status:** PARTIAL — repository review, Graphify rebuild, and wiki reconciliation complete; production row validation blocked by an empty stale slate

**Room:** Obsidian Governance Update

**Risk:** MEDIUM — protected surfaces were reviewed, but no application code or runtime state was changed

**Repository:** `C:\MLB HR Engine\mlb-hr-engine-master`

**Current HEAD:** `d71a2ad` on `main`, aligned with local `origin/main`

## Goal

Reconstruct current project state after the July 14 Graphify snapshot and the August 13 Claude live-state work, refresh the backend code graph, and correct durable Obsidian claims that no longer match code or Git history.

## Review boundaries

- Previous Graphify-time commit: `5278078` (2026-07-14)
- Last directly verified Claude task: Phase 2a LIVE TARGETS work (`a7df7b0` + `dcec28d`)
- Current repository target: `d71a2ad`
- Graphify scope: `mlb_hr_engine_v4/` code only
- Frontend, Vercel, Claude Design, and Obsidian were inspected directly because `.graphifyignore` intentionally excludes them

## Change inventory

From `5278078` through `d71a2ad`:

- 105 files changed
- 14,562 additions
- 742 deletions
- Major additions: warehouse capture/backfill, learning/evaluation tools, live-state API and alerts, odds skip guard and quota state, Community slips, ticket analysis/history, TCC builds, layout persistence, slate export, batter/pitcher detail, share cards, search, mobile stabilization, and FSM token refinement

## Current protected-surface truth

### MAIN

- Existing Platt calibration remains enabled with `A=0.7805` and `B=-0.4611`.
- The warehouse isotonic stage and artifact were added, but `WAREHOUSE_ISOTONIC_ENABLED=False` after the August 7 rollback.
- Original Full Slate probability thresholds are restored.
- The historical warehouse-isotonic experiment touched protected files, but current runtime behavior is deliberately disabled/no-op.

### JIG

- Live `pitch_mix_signal` is `0.0`; the `rv_per100` candidate feeds `jigScore_shadow` only.
- Live JIG ordering remains `jigScore` descending.
- `jigTier` exists as a separate additive display field derived server-side from `config.JIG_TIER_THRESHOLDS`.
- `jigTier` does not sort, filter, score, or feed MAIN.
- `AGENTS.md` is stale where it says no `jigTier` field exists. Current code and existing Obsidian doctrine agree that the July 13 preconditions were satisfied and the field was ratified.

### HVY

- `hvy_score` is assembled for JIG display/filter use and remains outside MAIN probability.
- No evidence was found that HVY feeds MAIN.

### API and runtime

The current FastAPI source exposes 29 routes. Newer durable surfaces include:

- `/api/live-state/{game_pk}`
- `/api/slate/export`
- `/api/tickets/{ticket_id}/analysis`
- `/api/community/posts`
- `/api/builds`
- `/api/layout/{layout_key}`
- `/api/batter-detail`
- `/api/pitcher-detail`

The slate pipeline now tolerates missing odds, emits honest odds-pending/quota state, limits prop requests to `PROPS_LOOKAHEAD_HOURS` (default six), and keeps `/api/slate` as a cache reader.

## Frontend state after Phase 2a

- PR #6 merged Phase 2a to `main` on August 17 (`be2a583`).
- LIVE TARGETS now shows real status, inning, and score for unambiguously resolved games.
- The target roster remains static and lacks a trusted `player_id`; add-to-slip stays blocked.
- `OddsPendingBanner` is preserved in code but no longer mounted after the operator disabled it (`5d31593`).
- Five August 17 commits contained portrait overflow, banner width, lens-tab width, and mobile header composition.
- FSM visual tokens now use deeper surfaces, stronger hairlines, restrained glow, and Space Grotesk as the display face (`c71415e`, `941be80`).

## Graphify refresh

Initial incremental update exposed legacy node IDs and duplicate path-prefix risk. A full code-only rebuild was then run without external LLM/API use.

Final graph:

- 133 extracted files in the final corpus
- 2,564 nodes
- 4,784 edges
- 130 communities
- `graph.json`, `graph.html`, `GRAPH_REPORT.md`, and `manifest.json` refreshed 2026-08-18
- Stored Graphify interpreter path corrected from the retired `ChrisPatrick` profile to the active `cpatr` profile

Structural diagnostics:

- missing endpoint edges: 0
- dangling endpoint edges: 0
- self-loop edges: 0
- exact duplicate edges: 0
- directed or undirected same-endpoint collapse: 0

Known extractor limitation: `warehouse_isotonic.json` produces zero AST nodes. It is a data artifact, not executable code, and the code-only graph intentionally does not semantically ingest it.

During final validation, `main` advanced from `941be80` to `d71a2ad` through a separate wiki synchronization commit. That commit added the live-state, mobile-overflow, operator-state, and design-token session notes. It was preserved as authoritative input; no attempt was made to amend or replace it.

## Handoff addendum reconciliation

The August 18 operator addendum was appended to `MIGRATION_HANDOFF.md` after current-state verification. Two supplied claims required correction before filing:

- GitHub's default branch is already `main`; the historical wrong-base PR warning remains valid, but the default-branch cleanup is complete.
- The centralized `--glow-*` refactor is present as an uncommitted `frontend/index.html` change. It is not yet a shipped commit.

The Fly deployment instruction was corrected to the winget-managed `flyctl` on the active `cpatr` profile. The stale home-PC Graphify flag was also closed with the current `d71a2ad` graph statistics.

## Validation

### Targeted backend regressions

Command used the existing `mlb_hr_engine_v4/.venv`:

```text
python -m pytest tests/test_live_state_endpoint.py tests/test_live_state_game_pk_derivation.py tests/test_mlb_stats_live_state.py tests/test_odds_guard.py tests/test_community_posts.py tests/test_ticket_analysis.py tests/test_my_tickets.py tests/test_ticket_history_contract.py tests/test_warehouse_backfill.py tests/test_batter_detail_contract.py -q
```

Result: **57 passed, 1 failed**.

The failure is deterministic in `test_owner_can_post_and_feed_groups_by_stable_user_not_mutable_username`. The Community API intentionally filters active posts to tickets dated today in ET. The test's `ticket-a` fixture has no `date`, so the feed correctly excludes it and the stale assertion indexes an empty list. The failure reproduced twice in isolation. No test or application fix was made in this synchronization pass.

### Live Fly checks

- `/health`: OK
- `/openapi.json`: current 29-route set present
- `/api/slate`: reachable but returned `stale: true`, date `2026-08-17`, zero games, zero MAIN rows, and zero JIG rows

The empty slate blocks row-level confirmation of `jigTier`, odds state, live target resolution, and live-game banner rendering.

## Files reviewed and updated by this synchronization

- Reviewed and already current in `HEAD`: `wiki/architecture/live-state-and-alerts-program.md`
- Updated wiki files:
  - `wiki/doctrine/deploy-runbook.md`
  - `wiki/doctrine/production-surface-truth.md`
  - `wiki/doctrine/known-gaps.md`
  - `wiki/doctrine/ticket-slip-system.md`
  - `wiki/doctrine/visual-design-tokens.md`
  - `wiki/doctrine/mobile-architecture-v2.md`
  - `wiki/doctrine/build-log-and-spec-status.md`
  - `wiki/doctrine/OBSIDIAN_GOVERNANCE_DOCTRINE.md`
  - `wiki/log.md`
  - `wiki/sessions/2026-08-18-frontend-operator-state.md`
  - this session note
- Root handoff: `MIGRATION_HANDOFF.md`
- `mlb_hr_engine_v4/graphify-out/*` generated graph artifacts

## Git and deployment state

- Application code changed: no
- Protected runtime behavior changed: no
- Commit created by this Codex task: no
- Push performed by this Codex task: no
- Deploy performed: no
- Pipeline/cache mutation performed: no
- Pre-existing unrelated working-tree files were preserved

## Smallest safe next action

**USE EXISTING ROOM: Issue Intake & Triage**

Audit why production `/api/slate` is serving a stale empty August 17 cache. Restore or validate the scheduled pipeline through a separate operator-authorized task, then rerun populated-slate and live-browser checks.

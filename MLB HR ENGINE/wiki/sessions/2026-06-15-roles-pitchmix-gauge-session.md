# Session: 2026-06-15 — Ticket Roles, Pitch Mix De-fabrication, HR Threat Gauge

**Date:** 2026-06-15
**Agent:** Claude Code
**Room:** Obsidian Governance Update
**Risk:** LOW (documentation capture of already-deployed changes)

---

## Arc

This session captured and documented a series of production changes deployed across 2026-06-15. All changes were already committed and validated in production before this vault record.

---

## Changes Deployed

### 1. AGENTS.md Rule 17 — Tool Action Permission Policy
- Commit: `110908e`
- Governance update defining explicit permission policy for tool actions.

### 2. Game Context Filter Fix
- Commit: `7d9f163` / `7bf2c08`
- Fixed: `gameStartUtc` and `gameStatus` were not being exported from the pipeline row. Game Context toggles (filters by game time) were non-functional.
- Fixed wire-up so both MAIN and JIG boards respect Game Context filters correctly.

### 3. Ticket Roles — Full Build

Four ticket roles built, calibrated, and deployed on both MAIN and JIG boards:

| Commit | Change |
|--------|--------|
| `3286b26` | Add FOUNDATION (→PRIME) role flag to MAIN; defer CEILING |
| `7d9f163` | Serve and render FOUNDATION badge on production board |
| `d08a780` | Add ADVANTAGE and WILDCARD roles (JIG-only initially) |
| `f49a265` | Extend ADVANTAGE and WILDCARD to MAIN board |
| `842946a` | Rename FOUNDATION→PRIME, CEILING→EXPLOSIVE; add to JIG |
| `1c6d2de` | Add tier-cell role badge stacking CSS |
| `54c8239` | Enable EXPLOSIVE badge with recalibrated thresholds |

**Role badge location:** Tier cell (both boards).

### 4. Role Filter

- Commit: `08bf55b`
- Added role filter dropdown to both MAIN and JIG boards.
- AND logic: all selected roles must be present.
- Filter labels: PRIME / EXPLOSIVE / ADVANTAGE / WILDCARD.

### 5. ADVANTAGE / WILDCARD Recalibration + WILDCARD Cap Bug Fix

- Commit: `1501fc4`
- ADVANTAGE xslg threshold: 0.500 → 0.490
- WILDCARD maxEV threshold: 117 → 116
- WILDCARD trait-count upper cap: **REMOVED** (bug: cap blocked multi-indicator players from qualifying)

### 6. Pitch Mix Modal — De-fabricated

- Commit: `8fee765`
- Removed all RNG fabrication (`fsmH2HData`, `fsmPitchData`).
- Wired to real Savant + MLB Stats API data via pipeline row fields and `/api/pitcher-detail` endpoint.
- Strike-zone 3×3 grid removed (no free real-time source); replaced with real batter-vs-pitch-type table.
- Insufficient-data fields show `--` — never fabricated.
- Confirmed: prior fabricated data never affected scoring (display-only modal).

### 7. HR Threat Meter — Pie → Radial Gauge

- Commits: `d2c4ffc`, `772b790`, `0d37597`, `e4cccb7`
- Replaced matchup pie chart with radial gauge showing 0–100 threat fill %.
- Fill derived from `model_prob` via tier-anchored banded interpolation (COLD → APEX bands, intra-tier interpolation).
- APEX band ceiling = real `MAX_GAME_HR_PROB` (0.29) — NOT 1.00 — so top-tier threats differentiate from each other.
- Gauge is display-only; does not alter scoring.
- Clickable → opens Pitch Mix modal.
- Renders on both MAIN and JIG boards.

---

## Outcome

- All 4 ticket roles (PRIME/EXPLOSIVE/ADVANTAGE/WILDCARD) live in production on both boards.
- Role badges in tier cell. Role filter (AND logic) on both boards.
- Pitch Mix modal fully de-fabricated.
- HR Threat Meter replaced with radial gauge (0.29 APEX ceiling).
- ADVANTAGE/WILDCARD recalibrated. WILDCARD trait-cap bug fixed.
- Production end-to-end verified clean.
- Git: main branch, clean working tree.

---

## Vault Notes Created / Updated This Session

- **CREATED:** `wiki/doctrine/deploy-runbook.md`
- **CREATED:** `wiki/doctrine/ticket-roles.md`
- **CREATED:** `wiki/doctrine/design-pitch-mix-analysis.md`
- **CREATED:** `wiki/doctrine/known-gaps.md`
- **CREATED:** `wiki/sessions/2026-06-15-roles-pitchmix-gauge-session.md` (this file)
- **UPDATED:** `wiki/index.md`
- **UPDATED:** `wiki/log.md`
- **UPDATED:** `wiki/doctrine/_Index_of_doctrine.md`
- **UPDATED:** `wiki/sessions/_Index_of_sessions.md`

---

## Cross-References

- [[ticket-roles]] — full role doctrine
- [[design-pitch-mix-analysis]] — pitch mix modal status
- [[known-gaps]] — latent issues surfaced this session
- [[deploy-runbook]] — deploy + cache refresh process
- [[tier-vocabulary]] — APEX/ELITE/EDGE tier definitions that roles gate on

# Frontend Architecture Audit — Three-Surface Map

**Date:** 2026-06-22  
**Status:** COMPLETE — documentation only  
**Owner:** Claude Code (Sonnet 4.6)

---

## Task

Record durable frontend architecture truth discovered during the frontend/Vercel recovery session (earlier today). Document the three frontend surfaces, correct the app.py active status, record the Next.js readiness gap, and codify the Arsenal Exploit Score as PAUSED.

---

## Key Findings

### 1. Three frontend surfaces exist — not two

Prior docs (`production-surface-truth.md`, CLAUDE.md §10) described the system as two surfaces: root `frontend/` vs Next.js `mlb_hr_engine_v4/frontend/`. That framing was incomplete. **app.py (Streamlit) is a third active surface** with its own operator workflow, tracking integration, and session-state logic.

### 2. app.py is active — not dead / not safe to delete

- CLAUDE.md identifies it as the current operator-facing dashboard (line 36).
- Contains the production tracking fix from commit `9980700`.
- Imports `pipeline.py` directly; owns pick logging, CLV logging, FD slip workflow.
- No deprecation markers exist.
- Removal is unsafe until a replacement is validated that preserves all of the above.

### 3. The frontend gap is smaller than feared

The Next.js tactical shell (`mlb_hr_engine_v4/frontend/`) has the right component shape. `ThreatRankingsTable` (MAIN + JIG) already fetches live from `/api/slate`. The gap is that `EscalationFeed`, `HRThreatCard`, `PitcherVulnerabilityPanel`, `MatchupIntelPanel`, and `CommandHeader` are still rendering hardcoded mocks or stubs. This is a fetch-wiring task, not a rebuild.

### 4. Arsenal Exploit Score remains NOT IMPLEMENTED / PAUSED

No frontend matchup card currently shows real drill-in data. Arsenal Exploit Score should not be built into a mocked panel. The data-availability constraint (no per-pitch barrel%) is recorded in `pitch-mix-data-availability.md`. The right sequencing is: wire real data first → Arsenal Exploit Score second (display-only, JIG-only, operator-authorized).

### 5. MAIN/JIG isolation is a hard gate on all matchup-intel work

No matchup-intel field or Arsenal Exploit Score component may feed MAIN probability, alter MAIN sorting, or alter JIG sorting without explicit operator authorization. This applies to all three surfaces.

---

## Files Changed

**Created:**
- `wiki/architecture/frontend-topology.md` — Three-surface map with current status, app.py correction, Next.js readiness, recommended sequencing, MAIN/JIG hard gate
- `wiki/architecture/matchup-intel-field-gap.md` — Panel-level field gaps, Arsenal Exploit Score prerequisite chain, null-data rule, required work steps

**Updated:**
- `wiki/doctrine/production-surface-truth.md` — Added correction note: three surfaces exist; app.py is active; this file's two-surface map is now superseded by `frontend-topology.md`
- `wiki/architecture/_Index_of_architecture.md` — Added entries for `frontend-topology` and `matchup-intel-field-gap`
- `wiki/sessions/_Index_of_sessions.md` — Added this session
- `wiki/log.md` — Appended log entry

---

## Files NOT Changed

- No runtime code (`app.py`, `pipeline.py`, `config.py`, `api/`)
- No frontend code (`frontend/`, `mlb_hr_engine_v4/frontend/`)
- No formula/scoring/model files
- No API endpoint changes
- No deployment configs

---

## Validation

- All changed files are under `MLB HR ENGINE/wiki/` (docs only)
- No runtime or code files modified
- Mandatory Obsidian/Wiki Documentation Gate: SATISFIED

---

## Cross-References

- `wiki/architecture/frontend-topology.md`
- `wiki/architecture/matchup-intel-field-gap.md`
- `wiki/architecture/pitch-mix-data-availability.md`
- `wiki/sessions/2026-06-22-frontend-vercel-source-of-truth-recovery.md`
- `wiki/doctrine/production-surface-truth.md`

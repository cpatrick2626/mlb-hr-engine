---
name: frontend-topology
description: Three-surface map of all frontend/operator UI surfaces — root static, app.py Streamlit, Next.js shell — with current status, deletion safety, and recommended sequencing
metadata:
  type: architecture
---

# Frontend Topology

**Last Updated:** 2026-06-22  
**Owner:** Claude Code (Sonnet 4.6)  
**Status:** Current — supersedes the two-surface map in `production-surface-truth.md` (which omitted app.py)

---

## Three-Surface Overview

MLB HR Engine has three distinct frontend/operator surfaces. They are NOT interchangeable and must not be collapsed.

| Surface | Path | Type | Status | Vercel? | Fly.io? |
|---------|------|------|--------|---------|---------|
| Static production board | `frontend/` (root) | Static HTML/JS — no build step | **LIVE / PRODUCTION** | Yes — Root Dir = `frontend` | No |
| Operator dashboard | `mlb_hr_engine_v4/app.py` | Streamlit | **ACTIVE** | No | No (local) |
| Next.js tactical shell | `mlb_hr_engine_v4/frontend/` | Next.js 14 | **MIXED / NOT PRODUCTION-READY** | No (not yet) | No |

---

## Surface 1 — root `frontend/` (Static Production Board)

- **What it is:** Static HTML/JS/CSS dashboard. No build step, no package.json, no framework.
- **Key files:** `index.html` (~3,887 lines), `assets/js/full-slate-matrix.js`, `assets/js/jig-command.js`, `image-slot.js`, ~10 bundled JS files, 35 Barlow font files.
- **Vercel Root Directory:** `frontend` (set in Vercel dashboard — NOT derivable from any repo file).
- **Data source:** Live `/api/slate` fetch from Fly.io FastAPI service.
- **Current status:** Restored and operational as of commit `e619711` (2026-06-22). Was broken from commit `cedfd89` (deletion of "dead trees") until the restore.
- **Extension difficulty:** HARDER — static/compiled-style frontend, no component system, no TypeScript, no hot reload.
- **Deletion safety:** UNSAFE without Vercel Root Directory reconfiguration. See `2026-06-22-frontend-vercel-source-of-truth-recovery.md`.

### What it does NOT have

- A real drill-in matchup card for Arsenal Exploit Score or per-pitcher arsenal breakdown.
- Any component abstraction (everything is inline in `index.html` + monolithic JS).

---

## Surface 2 — `mlb_hr_engine_v4/app.py` (Streamlit Operator Dashboard)

- **What it is:** The primary operator-facing workflow tool. Streamlit application.
- **Data source:** Imports `pipeline.py` directly — no HTTP round-trip.
- **Confirmed active because:**
  - CLAUDE.md line 36 identifies it as the current operator-facing dashboard.
  - Contains the production tracking fix from commit `9980700`.
  - Imports `pipeline.py`, session_state logic, and live operator workflow (FD slip building, pick logging, CLV tracking).
  - No confirmed deprecation markers exist in the codebase.
- **Deletion / removal safety:** UNSAFE until a replacement is validated and the following are preserved or migrated:
  - FD slip build workflow
  - Pick logging (`_pt.log_picks_bulk()`)
  - CLV logging
  - Session-state operator workflow
  - All tracking/monitoring integrations
- **Relation to root `frontend/`:** Independent. They do not share session state, auth, or caching.
- **Relation to Next.js:** Independent. Next.js does not call app.py; app.py does not serve Next.js.

### Important correction to prior docs

Earlier sessions (pre-2026-06-22) described app.py as potentially dead or deprecated alongside the Next.js "rebuild." That is INCORRECT. app.py is active. Do not treat it as dead or safe-to-remove without operator authorization and a validated replacement.

---

## Surface 3 — `mlb_hr_engine_v4/frontend/` (Next.js Tactical Shell)

- **What it is:** Next.js 14 prototype. The intended long-term tactical operator frontend.
- **Current readiness: MIXED.**

### What is wired (live data)

| Component | Status |
|-----------|--------|
| `ThreatRankingsTable` (MAIN) | Fetches live from `/api/slate` |
| `ThreatRankingsTable` (JIG) | Fetches live from `/api/slate` |

### What is NOT wired (mock/hardcoded data)

| Component | Mock Content |
|-----------|--------------|
| `EscalationFeed` | `MOCK_*` constants |
| `HRThreatCard` | `MOCK_*` constants |
| `PitcherVulnerabilityPanel` | `MOCK_*` constants |
| `MatchupIntelPanel` | `MOCK_*` constants |
| `CommandHeader` | Hardcoded date `"Saturday, May 23 2026"`, hardcoded `slateCount={87}`, hardcoded `activeThreats={14}` |
| Strategy / Hits / Performance / Ops workspaces | STANDBY stubs — no data |

### What it does NOT have (field gaps)

- Arsenal Exploit Score display panel (not implemented)
- Per-pitcher pitch-type breakdown in matchup card (not wired)
- Real-time escalation feed (mocked)
- Live date / slate count / active threats (hardcoded)

### Do NOT repoint Vercel to this surface until

1. All data panels wired to real `/api/slate` fields (EscalationFeed, HRThreatCard, PitcherVulnerabilityPanel, MatchupIntelPanel)
2. `CommandHeader` date/slateCount/activeThreats replaced with live values
3. Fly.io cold-start handling confirmed adequate
4. Full operator sign-off on cutover

---

## The Frontend Gap Is Smaller Than Previously Feared

The API already exposes much of the real data needed for the Next.js shell. The components are largely the right tactical shape. The missing work is:

1. Replace mock arrays with real `/api/slate` fetches in non-ranking panels
2. Implement missing classification logic for escalation / matchup-intel rendering
3. Wire CommandHeader to live state

This is a real but bounded fetch-wiring and field-gap-closure task — not a ground-up rebuild.

---

## Recommended Sequencing

1. **Now:** Document frontend topology (this file) — DONE.
2. **Next:** Wire Next.js matchup card panels to real `/api/slate` data (EscalationFeed, HRThreatCard, MatchupIntelPanel, PitcherVulnerabilityPanel).
3. **After real data flows:** Add Arsenal Exploit Score as a display-only / JIG-side matchup intelligence component (see `pitch-mix-data-availability.md`).
4. **When Next.js is validated:** Assess Vercel cutover from root `frontend/` to `mlb_hr_engine_v4/frontend/`.
5. **Only after cutover is validated:** Assess whether app.py can be safely retired (it cannot be retired today).

---

## MAIN/JIG Isolation — Hard Gate

Any new matchup intelligence component (Arsenal Exploit Score, pitch-mix display, per-pitcher breakdown) must satisfy ALL of the following before implementation:

- Does NOT feed MAIN model probability (`P(HR≥1)`, EV, Edge)
- Does NOT alter MAIN ranking/sorting
- Does NOT alter JIG ranking/sorting unless explicitly operator-authorized
- Is proven display-only before implementation
- Is placed on the JIG side or as a standalone matchup-intel panel

This gate applies to both the Next.js frontend and app.py. See `AGENTS.md § MAIN vs JIG Doctrine` and `wiki/doctrine/main-jig-separation.md`.

---

## Cross-References

- `wiki/sessions/2026-06-22-frontend-vercel-source-of-truth-recovery.md` — Vercel deletion/restore audit
- `wiki/architecture/matchup-intel-field-gap.md` — Next.js field gap details + Arsenal Exploit Score status
- `wiki/architecture/pitch-mix-data-availability.md` — Arsenal Exploit Score data availability audit
- `wiki/doctrine/production-surface-truth.md` — Prior two-surface map (now superseded by this file)
- `wiki/doctrine/main-jig-separation.md` — MAIN/JIG isolation doctrine
- `CLAUDE.md §10` — Frontend Surface doctrine
- `AGENTS.md` — MAIN/JIG doctrine, pitch-mix integrity rules

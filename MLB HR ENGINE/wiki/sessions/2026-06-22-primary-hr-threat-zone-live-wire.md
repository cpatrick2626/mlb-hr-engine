# Primary HR Threat Zone — Live Data Wire (Step 2)
**Date:** 2026-06-22  
**Status:** IN PROGRESS — local/dev only; NOT deployed  
**Owner:** Claude Code (Sonnet 4.6)  
**Commit:** `98438b0`

---

## What Was Done

Wired the Primary HR Threat Zone (`HRThreatCard` components, `page.tsx`) to live `/api/slate` data from `leaderboard_rows` (MAIN).

**Source isolation:** MAIN rows only. Ordered by API field `model_tier_rank`; top 4 rows surface as the Primary HR Threat Zone. Real players rendered locally: Schwarber, Buxton, Ohtani, Chourio.

---

## Bug Fix — mapTier APEX→LOW Latent Error

`mapTier` had a silent wrong-mapping for the APEX tier:

| Tier | Before (wrong) | After (correct) |
|------|----------------|-----------------|
| APEX | LOW | CRITICAL |
| ELITE | HIGH | HIGH *(unchanged)* |
| EDGE | HIGH | HIGH *(unchanged)* |
| SIGNAL | MODERATE | MODERATE *(unchanged)* |
| WATCH | LOW | LOW *(unchanged)* |
| COLD | LOW | LOW *(unchanged)* |

Symptom: APEX-tier batters were showing escalation labels and color treatment for LOW instead of CRITICAL. Affected `ThreatRankingsTable` escalation display. No model math touched.

---

## Null Safety

`barrel`, `weather`, `pitcherVuln` fields render `—` when null or missing. Real zero renders as `0.0%`. Missing ≠ zero distinction preserved (same pattern as matchup-intel session).

---

## Data Gaps (Backend — Future Work)

Two cells in `HRThreatCard` cannot be populated until the backend surfaces additional fields:

| Field | Gap | Path to fix |
|-------|-----|-------------|
| `weatherBoost` | Not present in `leaderboard_rows` | Backend must add weather signal to MAIN row payload |
| `pitcherVulnerability` (0–100 score) | `opphr` exists but conversion to 0–100 is engine math | Pipeline must compute and expose the normalized score |

Both cells show `—` until backend surfaces them. Frontend is not responsible for this conversion.

---

## Status

- LOCAL/dev only
- Live production board remains root `frontend/` static HTML (Vercel)
- `mlb_hr_engine_v4/frontend/` Next.js shell is NOT production-ready; Vercel Root Directory has NOT been repointed

---

## Open Items (remaining Next.js panels)

| Item | Detail |
|------|--------|
| `CommandHeader` date/counts | Hardcoded — needs live date + slateCount + activeThreats from API |
| `EscalationFeed` | Still MOCK |
| `PitcherVulnerabilityPanel` | Still MOCK |
| Backend: `weatherBoost` | Not in leaderboard_rows |
| Backend: pitcher vuln 0–100 | Engine math gap, out of frontend scope |

---

## Cross-References

- `wiki/sessions/2026-06-22-matchup-intel-live-wire.md` — Step 1 (Matchup Intel live wire; null-safe pattern)
- `wiki/architecture/matchup-intel-field-gap.md` — field gap inventory for all Next.js panels
- `wiki/sessions/2026-06-22-frontend-vercel-source-of-truth-recovery.md` — surface-map context; preconditions for Vercel repoint
- `CLAUDE.md` §10 — Frontend Surface doctrine

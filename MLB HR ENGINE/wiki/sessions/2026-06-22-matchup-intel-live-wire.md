# Matchup Intel Card — Live Data Wire (Step 1)
**Date:** 2026-06-22  
**Status:** IN PROGRESS — local/dev only; NOT deployed  
**Owner:** Claude Code (Sonnet 4.6)  
**Commit:** `8e1984a`

---

## What Was Done

Wired the Matchup Intelligence card (`matchup-intel.tsx` + `page.tsx` `mapMatchupRow`) to live `/api/slate` data from `leaderboard_rows_jig`.

**Source isolation:** JIG rows only. MAIN rows are never read by this card. MAIN/JIG isolation held.

**Verified live:** Rendered real 2026-06-22 slate data locally — Buxton, Alvarez, Schwarber confirmed.

---

## Edge Classification Logic

Derived from `h2h_factor` field:

| h2h_factor | Label |
|---|---|
| > 1.05 | FAVORABLE |
| 0.95 – 1.05 | NEUTRAL |
| < 0.95 | UNFAVORABLE |

Display-only — does not touch `model_prob`, `jigScore`, or tier assignment. Real h2h spread (~0.93–1.14) means most rows show NEUTRAL; FAVORABLE/UNFAVORABLE are rare by design.

---

## Null Safety

`hvyScore`, `barrelPct`, `pitcherHR9` are typed `number | null`. Null renders as `—`; real zero renders as `0.0%`. Missing ≠ zero distinction preserved. Closes the null-as-zero trap for this card.

---

## Housekeeping

`.next/` build cache and `tsconfig.tsbuildinfo` untracked and gitignored (were wrongly tracked).

---

## Status

- LOCAL/dev only
- Live production board remains root `frontend/` static HTML (Vercel)
- `mlb_hr_engine_v4/frontend/` Next.js shell is NOT production-ready; Vercel Root Directory has NOT been repointed

---

## Open Items (deferred)

| Item | Detail |
|------|--------|
| `CommandHeader` date | Hardcoded `"Saturday May 23 2026"` — needs live date from API |
| `CommandHeader` counts | `slateCount={87}` and `activeThreats={14}` hardcoded |
| `EscalationFeed` | Still MOCK |
| `PitcherVulnerabilityPanel` | Still MOCK |
| `HRThreatCard` | Still MOCK |
| `Primary Threat Zone` | Still MOCK |
| `pitcherTeam` | Blank — field not present in JIG rows |

These are step 2+ of the Next.js production-readiness project.

---

## Cross-References

- `wiki/sessions/2026-06-22-frontend-vercel-source-of-truth-recovery.md` — surface-map context; preconditions for Vercel repoint
- `wiki/architecture/matchup-intel-field-gap.md` — field gap inventory for all Next.js panels
- `CLAUDE.md` §10 — Frontend Surface doctrine

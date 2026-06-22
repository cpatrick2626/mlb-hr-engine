---
name: matchup-intel-field-gap
description: Next.js matchup-intel panel field gaps — what is wired vs mocked, Arsenal Exploit Score status (PAUSED), and required work before real matchup intelligence can be displayed
metadata:
  type: architecture
---

# Matchup-Intel Field Gap

**Last Updated:** 2026-06-22  
**Owner:** Claude Code (Sonnet 4.6)  
**Status:** Current — documents the data-wiring gap between `/api/slate` and the Next.js matchup-intel panels

---

## Context

The Next.js tactical shell (`mlb_hr_engine_v4/frontend/`) has the right component shape for displaying matchup intelligence. However, several panels are still rendering hardcoded `MOCK_*` constants instead of real API data. This document records exactly what is wired, what is not, and what field work is needed.

Separately, Arsenal Exploit Score — a proposed pitch-type matchup scoring component — is PAUSED. Its status and prerequisite chain are recorded here.

---

## What `/api/slate` Currently Exposes

The FastAPI service (`mlb_hr_engine_v4/api/main.py`) exposes `/api/slate`. Based on the frontend audit (2026-06-22), the rankings panels (`ThreatRankingsTable` MAIN + JIG) already fetch live from this endpoint. The endpoint appears to carry enough real data for the other panels — the gap is that those panels do not yet consume it.

Confirmed live consumers of `/api/slate` in Next.js:
- `ThreatRankingsTable` (MAIN ranking)
- `ThreatRankingsTable` (JIG ranking)

---

## Panel-Level Field Gap

### EscalationFeed

| Field Needed | Source | Status |
|-------------|--------|--------|
| Top escalation events (player + tier + signal) | `/api/slate` leaderboard_rows or derived | **NOT WIRED — MOCK** |

**Work required:** Map `leaderboard_rows` escalation/tier fields → `EscalationFeed` props; remove `MOCK_ESCALATION` constant.

---

### HRThreatCard

| Field Needed | Source | Status |
|-------------|--------|--------|
| Batter name, team, position | `/api/slate` player row | **NOT WIRED — MOCK** |
| HR probability (model) | `/api/slate` `prob` or `model_prob` | **NOT WIRED — MOCK** |
| EV / Edge | `/api/slate` `ev`, `edge` | **NOT WIRED — MOCK** |
| Barrel / hard-hit metrics | `/api/slate` profile fields | **NOT WIRED — MOCK** |
| Park factor | `/api/slate` or pipeline profile | **NOT WIRED — MOCK** |
| Weather / wind | `/api/slate` or pipeline profile | **NOT WIRED — MOCK** |
| Pitcher matchup fields | `/api/slate` pitcher_* fields | **NOT WIRED — MOCK** |

**Work required:** Wire `HRThreatCard` props from a selected `leaderboard_rows` entry; remove `MOCK_THREAT` constant; implement drill-in selection from `ThreatRankingsTable` row click.

---

### PitcherVulnerabilityPanel

| Field Needed | Source | Status |
|-------------|--------|--------|
| Pitcher name, hand, era | `/api/slate` pitcher fields | **NOT WIRED — MOCK** |
| Vulnerability tier / score | `/api/slate` or pipeline | **NOT WIRED — MOCK** |
| Pitch-type allowed damage (SLG/ISO by pitch) | Statcast data in pipeline profile | **NOT WIRED — MOCK** |
| Handedness splits | Pipeline profile | **NOT WIRED — MOCK** |

**Work required:** Wire pitcher fields from slate payload; remove `MOCK_PITCHER_VULNERABILITY` constant.

---

### MatchupIntelPanel

| Field Needed | Source | Status |
|-------------|--------|--------|
| Batter vs pitcher history signals | Pipeline profile | **NOT WIRED — MOCK** |
| Arsenal exploitation signal | Arsenal Exploit Score | **NOT IMPLEMENTED — PAUSED** |
| Environmental modifiers (park, wind, temp) | Pipeline profile | **NOT WIRED — MOCK** |
| Tier / confidence display | `/api/slate` or pipeline | **NOT WIRED — MOCK** |

**Work required:** Wire matchup fields from slate payload; remove `MOCK_MATCHUP_INTEL` constant. Arsenal Exploit Score component deferred until score is implemented (see below).

---

### CommandHeader

| Field Needed | Source | Status |
|-------------|--------|--------|
| Today's date | Browser `Date` or `/api/slate` response date | **HARDCODED — `"Saturday, May 23 2026"`** |
| Slate count | `/api/slate` row count | **HARDCODED — `87`** |
| Active threats count | Derived from `leaderboard_rows` | **HARDCODED — `14`** |

**Work required:** Replace hardcoded values with live computed values from the slate fetch response.

---

## Arsenal Exploit Score — Status: PAUSED / NOT IMPLEMENTED

### What it is

A proposed display-only matchup-intel component that would score batter-vs-pitcher pitch-type advantage (e.g., batter crushes fastballs, pitcher throws 60% fastballs → high exploit score).

### Why it is paused

1. **No real production matchup card exists yet.** Arsenal Exploit Score should be added to a real UI, not a mocked panel.
2. **Data availability is partial.** A reduced score using SLG/ISO/HR-rate-by-pitch-mix is feasible. A full barrel-based score is not — per-pitch barrel% and per-pitch xSLG do not exist in current data sources. See `pitch-mix-data-availability.md` for the full audit.
3. **MAIN/JIG gate applies.** The score must be proven display-only before implementation. It must not feed MAIN probability, EV, or Edge. It must not alter MAIN or JIG sorting.

### Prerequisite chain (must complete before implementing Arsenal Exploit Score)

1. Wire real data to `HRThreatCard` and `MatchupIntelPanel` (replace mocks)
2. Confirm `MatchupIntelPanel` renders real matchup fields end-to-end
3. Operator authorizes Arsenal Exploit Score implementation
4. Implement as display-only / JIG-side signal only
5. Validate MAIN/JIG isolation before any frontend push

### What CANNOT be built into Arsenal Exploit Score with current data

- Per-pitch barrel% for batters or pitchers (does not exist)
- Per-pitch xSLG (does not exist)
- Contact-quality-by-pitch-type scoring beyond raw SLG/ISO/HR-rate

### What CAN be built (reduced form only)

- Batter SLG/ISO/HR-rate vs pitch type X weighted by pitcher's usage% of pitch type X
- Pitcher allowed SLG/ISO/HR-rate by pitch type X matched to batter's damage splits
- Handedness-adjusted matchup weights
- PA-gated reliability filter (suppress signal below minimum sample)

### Null / Missing Data Rule

Missing pitch data = NO SIGNAL, never 0. Any missing = suppress the score entirely or display "insufficient data." Zero would imply negative exploitation and is incorrect. This follows the same rule as the conf-tier "C" bug.

---

## Required Work Summary (ordered)

| Step | Work | Prerequisite |
|------|------|-------------|
| 1 | Wire `CommandHeader` date/slateCount/activeThreats to live values | None — do first |
| 2 | Wire `EscalationFeed` to real `/api/slate` data | Step 1 or concurrent |
| 3 | Wire `HRThreatCard` to real `/api/slate` row | Step 2 or concurrent |
| 4 | Wire `PitcherVulnerabilityPanel` to real pitcher fields | Step 3 or concurrent |
| 5 | Wire `MatchupIntelPanel` to real matchup fields (sans Arsenal Exploit Score) | Step 3 |
| 6 | E2E validation: all panels show real data, no mocks | Steps 1–5 complete |
| 7 | Arsenal Exploit Score — design + operator authorization | Step 6 + operator go |
| 8 | Arsenal Exploit Score — implement as display-only in `MatchupIntelPanel` | Step 7 |
| 9 | Vercel cutover assessment (root → Next.js) | Steps 1–6 + app.py replacement validated |

---

## Hard Gate Reminder

No matchup-intel field — including Arsenal Exploit Score — may:
- Feed MAIN model probability
- Alter MAIN ranking or sorting
- Alter JIG ranking or sorting (without explicit operator authorization)
- Be implemented before the real matchup card exists and shows live data

See `AGENTS.md § MAIN vs JIG Doctrine` and `wiki/doctrine/main-jig-separation.md`.

---

## Cross-References

- `wiki/architecture/frontend-topology.md` — Three-surface map, current status of all surfaces
- `wiki/architecture/pitch-mix-data-availability.md` — Arsenal Exploit Score data audit
- `wiki/doctrine/main-jig-separation.md` — MAIN/JIG isolation rules
- `wiki/sessions/2026-06-22-frontend-architecture-audit.md` — Session record for this audit
- `AGENTS.md` — pitch-mix integrity rules, MAIN/JIG doctrine

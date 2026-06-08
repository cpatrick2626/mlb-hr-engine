# App Shell Layout Doctrine

**Last Updated:** 2026-06-08

---

## Summary

MasterDashboard is the canonical top-level shell for the MLB HR ENGINE operator interface. All layout truth derives from the Master Dashboard handoff. This document records the canonical shell structure as of the 2026-06-08 startup-baseline audit.

---

## Canonical Shell Structure

| Zone | Component | Role |
|------|-----------|------|
| Top | TopBar | Branding, date, status strip |
| Navigation | engine-lens nav | Switch between MAIN engine and JIG lens surfaces |
| Banner | LiveTargets | Live HR threat summary, escalation badges |
| Center | Stage | Central viewport — primary operator action surface |
| Right | RightRail | Secondary intelligence panel |
| Left/overlay | NavPanel | Navigation and view control |
| Right/secondary | StrategyRail | Strategy and bet-sizing context |

---

## Engine Identity Colors

| Engine | Identity Color |
|--------|---------------|
| MAIN | Red |
| JIG | Cyan |

These colors are doctrine-locked. Do not swap or blend engine identity colors.

---

## Navigation Model

- Navigation is **engine → lens**
- Top-level switch: MAIN engine vs JIG engine
- Within each engine: lens views (e.g., Full Slate, Leaderboard, Matchup)
- Engine-lens navigation is a closed surface (see `PHASE3_REFINEMENT_DOCTRINE.md`)

---

## Layout Truth Scope

The Master Dashboard handoff and prototype shell define **layout truth only**.

They do not define:
- Production data contracts
- API payload shapes
- Scoring logic
- Filter logic

Data truth lives in `pipeline.py`, `config.py`, and the FastAPI service contract.

---

## Prototype vs Production

The prototype shell (`mlb_hr_engine_v4/frontend/`) uses mock data for layout iteration.

Production layout source of truth:
- `frontend/index.html` and `frontend/assets/` (root-level static frontend)
- Layout zones documented in this note

Do not treat prototype mock data as production data contracts.

---

## Cross-References

- [Production Surface Truth](production-surface-truth.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
- [Room Governance](room-governance.md)

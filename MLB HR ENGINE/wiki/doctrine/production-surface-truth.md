# Production Surface Truth

**Last Updated:** 2026-06-08

---

## Summary

Two frontend surfaces exist in the repo. They are not equivalent. This document records which surface is production and which is a prototype, and confirms canonical branch truth as of 2026-06-08.

---

## Frontend Surface Map

| Path | Type | Status | Data |
|------|------|--------|------|
| `frontend/` (repo root) | Static production frontend | **PRODUCTION** | Real API data via `/api/slate` |
| `mlb_hr_engine_v4/frontend/` | Next.js prototype | **PROTOTYPE / DESIGN ITERATION** | Mock data |

### Rules

- `frontend/` (root) is the production operator surface.
- `mlb_hr_engine_v4/frontend/` is a design-iteration prototype. As of 2026-06-08 it is standalone — no Python runtime, no FastAPI, no Fly.io deployment invokes it.
- Do not treat prototype component logic as production truth.
- Do not treat prototype mock data shapes as production API contracts.
- Layout and visual hierarchy from the prototype shell may be used as layout reference only (see `app-shell-layout.md`).

---

## Branch Canonicity

| Branch | Status |
|--------|--------|
| `main` | **Canonical active working branch** — MLB HR ENGINE operations |
| `master` | Stale unless specifically revalidated |

**Confirmed by operator: 2026-06-08.**

Any documentation, doctrine, or instruction referencing `master` as the active branch is stale and should be updated to `main` when encountered.

Exception: a future audit may confirm that a specific `master` commit contains unique history not merged to `main`. Until that audit occurs, treat `master` references as stale.

---

## FastAPI + Deployment Surface

- FastAPI service: `mlb_hr_engine_v4/api/main.py`
- Deployed to Fly.io (`fly.toml`, `Dockerfile` at repo root)
- Root `frontend/` static assets are served from the same deployment
- `mlb_hr_engine_v4/frontend/` (Next.js) is NOT deployed to Fly.io

---

## Cross-References

- [App Shell Layout](app-shell-layout.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [Room Governance](room-governance.md)

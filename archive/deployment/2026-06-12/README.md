# Archived Deployment Files — 2026-06-12

## Files

| Archived Name | Original Path |
|---|---|
| `v4_Dockerfile` | `mlb_hr_engine_v4/Dockerfile` |
| `v4_fly.toml` | `mlb_hr_engine_v4/fly.toml` |

## Why Archived

These files were stale/orphaned as of 2026-06-12, confirmed by the
Production Surface Truth audit (`wiki/doctrine/production-surface-truth.md`).

The production `mlb-hr-api` Fly.io app deploys from the **repo root**:
- `Dockerfile` (root) — canonical production container definition
- `fly.toml` (root) — canonical Fly.io app config (`app = "mlb-hr-api"`)

The `mlb_hr_engine_v4/` copies were never referenced by any workflow,
deploy script, or CI configuration. They posed an accidental-deployment
risk by appearing authoritative while differing from the root canonical files.

## Audit Reference

- Doctrine: `wiki/doctrine/production-surface-truth.md` — "Stale / Orphan Deployment Files (2026-06-12)" section
- Commit: see git log for this file
- Operator authorization: Production Surface Truth phase, Step C

## History

Files are moved (not deleted) via `git mv` so full commit history is
preserved. Use `git log -- mlb_hr_engine_v4/Dockerfile` and
`git log -- mlb_hr_engine_v4/fly.toml` to trace history.

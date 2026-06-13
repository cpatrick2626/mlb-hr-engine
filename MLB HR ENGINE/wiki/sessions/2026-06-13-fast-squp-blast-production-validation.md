# Session: Fast / SQUP / Blast Production Validation - d63f046

Date: 2026-06-13
Agent: Codex
Owner: Codex
Project: MLB HR ENGINE - OPERATIONS
Room: Obsidian Governance Update
Risk Class: LOW
Phase: Document production validation for commit `d63f046`
Status: COMPLETE / PASS
Commit: `d63f046`

## Scope

This session records completed production validation in Obsidian only.

No runtime files were modified in this documentation session.
No frontend files were modified in this documentation session.
No backend, API, pipeline, config, or deployment files were modified in this documentation session.
No commit was created in this documentation session.
No push was performed in this documentation session.

---

## Deployment

- Push succeeded: `d63f046` on `origin/main`
- Fly build/deploy: successful
- Image: `deployment-01KV0TP83V1GGSSG60E0YQR4FN`
- Machine: `7841255a9d2e28`
- Region: `iad`

---

## API / Cache Validation

- `POST /api/pipeline/run` -> HTTP 200
- `/health` -> HTTP 200 `{"status":"ok"}`
- `/api/slate` -> HTTP 200

---

## Row Counts

- MAIN `leaderboard_rows`: `377`
- JIG `leaderboard_rows_jig`: `377`

---

## Field Validation

- `fast`, `squp`, and `blast` keys present on all rows
- `186 / 377` rows have non-null `fast`, `squp`, and `blast`
- `191 / 377` rows are null for absent players
- Percent scale confirmed: `0` to `89.2`

---

## Sorting Validation

- MAIN sorted by `hrprob` descending
- JIG sorted by `jigScore` descending

---

## Invariants Preserved

- Model/scoring unchanged
- MAIN/JIG ordering preserved
- No protected surfaces changed beyond authorized display-field population
- No frontend payload key mismatch

---

## Sample Rows

- Shea Langeliers | `hrprob=23.7` | `fast=53.0` | `squp=24.7` | `blast=13.8`
- Yordan Alvarez | `hrprob=23.4` | `fast=59.4` | `squp=24.6` | `blast=17.7`
- Byron Buxton | `hrprob=22.1` | `fast=40.0` | `squp=21.5` | `blast=11.9`
- Nick Kurtz | `hrprob=20.1` | `fast=80.3` | `squp=18.6` | `blast=15.3`
- Hunter Goodman | `hrprob=19.5` | `fast=52.8` | `squp=17.5` | `blast=10.3`

---

## Final State

- Git clean
- `main` synced with `origin/main`

---

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/doctrine/build-log-and-spec-status.md`
- `MLB HR ENGINE/wiki/sessions/2026-06-13-fast-squp-blast-production-validation.md`
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md`

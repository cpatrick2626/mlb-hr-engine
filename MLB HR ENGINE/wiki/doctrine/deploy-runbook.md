# Deploy Runbook

**Last Updated:** 2026-09-12

---

## Current deployment split — 2026-09-12

- **Frontend:** repository-root `frontend/`; Vercel automatically deploys pushes to `main`.
- **Backend:** `mlb_hr_engine_v4/`; Fly app `mlb-hr-api`; deploy manually with `flyctl` from the repository root after explicit operator authorization.
- Current Fly configuration: `min_machines_running=1`, `memory_mb=1024`, `TRACKING_DATA_DIR=/data`, persistent volume mounted at `/data`.
- A Git push does not deploy the Fly backend. Do not deploy the frontend through Fly.

## Summary

Operational runbook for deploying the MLB HR Engine API to Fly.io. GitHub push does NOT auto-deploy. All deploys are MANUAL.

---

## Deploy Command

Run from the PARENT repo root (`C:\MLB HR Engine\mlb-hr-engine-master`) — where `fly.toml` lives:

```powershell
flyctl deploy
```

Verified home-PC executable: `C:\Users\cpatr\AppData\Local\Microsoft\WinGet\Links\flyctl.exe` (`flyctl v0.4.70` on 2026-08-18). The winget link is on `PATH`. The retired `C:\Users\ChrisPatrick\.fly\bin\flyctl.exe` path is invalid on this machine.

Deploys are home-PC-only and require explicit operator authorization.

**Do NOT run from `MLB HR ENGINE\` (the vault subfolder) — `fly.toml` is not there.**

---

## Cache Behavior After Deploy

The slate cache lives on a **persistent volume** and **survives deploys**.

- Backend/data changes (config, pipeline, roles, API logic) do NOT appear to users until a fresh pipeline run regenerates the cache.
- Frontend-only changes (JS/CSS/HTML in `frontend/`): deploy only, no cache refresh needed.

---

## Force Cache Refresh

1. POST to `/api/pipeline/run` with header `X-Cron-Secret: <value>` (value stored as Fly secret `CRON_SECRET` — do NOT record the value here or in any vault note).
2. Keep the machine awake while it runs: Fly auto-stops idle machines. Ping `/health` repeatedly for ~2 minutes to prevent auto-stop from killing the background task.
3. Verify success: check that `generated_at` in the next `/api/slate` response is fresh.

---

## Production Surfaces

| Surface | Path | Status |
|---------|------|--------|
| API | `mlb_hr_engine_v4/api/` | **PRODUCTION** |
| Frontend | `frontend/` (repo root) | **PRODUCTION** |
| Streamlit | `app.py` | **DEAD / NON-PRODUCTION** (stale, out of sync) |
| v4 prototype frontend | `mlb_hr_engine_v4/frontend/` | **PROTOTYPE** (not deployed) |

**Canonical deployment files:** `Dockerfile` and `fly.toml` at repo root only.

---

## Cross-References

- [Production Surface Truth](production-surface-truth.md)
- [Room Governance](room-governance.md)
- [[known-gaps]] — `app.py` deprecation noted there

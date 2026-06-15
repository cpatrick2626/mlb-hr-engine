# Deploy Runbook

**Last Updated:** 2026-06-15

---

## Summary

Operational runbook for deploying the MLB HR Engine API to Fly.io. GitHub push does NOT auto-deploy. All deploys are MANUAL.

---

## Deploy Command

Run from the PARENT repo root (`C:\MLB HR Engine\mlb-hr-engine-master`) — where `fly.toml` lives:

```
C:\Users\ChrisPatrick\.fly\bin\flyctl.exe deploy
```

`flyctl` is NOT on PATH. Always use the full binary path or prefix with the full path.

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

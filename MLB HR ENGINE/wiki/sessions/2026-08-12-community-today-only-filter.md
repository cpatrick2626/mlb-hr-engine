---
date: 2026-08-12
agent: Claude Code
task: Community active board — today-only filter
commit: d366e5d
---

## Summary

`GET /api/community/posts` now filters to today's slips only (ET). Older slips are retained in the DB and surface only in the private History tab (`/api/my-tickets`).

---

## Change

**File:** `mlb_hr_engine_v4/api/main.py`  
**Commit:** `d366e5d`  
**Size:** 3 lines added

Inside `get_community_posts()`, after fetching posts and joining ticket records, each post is tested:

```python
today_str = today_et().isoformat()   # ET slate date, DST-aware via ZoneInfo
if ticket.get("date") != today_str:
    continue  # excluded from active board; retained in DB for history
```

`today_et()` is the existing DST-aware ET helper imported from `api.cache`.

---

## Behavior

- **Public board** (`GET /api/community/posts`): shows only slips whose `tickets.date` matches today's ET date.
- **Private history** (`GET /api/my-tickets`): shows all of the caller's tickets regardless of date.
- Older slips are **never deleted** — they remain in the `tickets` and `community_posts` tables.
- The filter is applied at read time; no schema change, no backfill, no migration.

---

## Protected surfaces

- No scoring, calibration, pipeline, or MAIN/JIG surface touched.
- No schema change.

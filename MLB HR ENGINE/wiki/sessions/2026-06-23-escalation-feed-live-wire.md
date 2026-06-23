---
title: EscalationFeed Wired to Live Slate
date: 2026-06-23
agent: claude-code
status: COMPLETE
tags: [frontend, escalation, live-wire]
---

# 2026-06-23 — EscalationFeed Wired to Live Slate

## What changed

`mlb_hr_engine_v4/frontend/app/page.tsx`

- `mapEscalationEvents(rows, prefix)` added — maps up to 8 `ApiRow` entries to `EscalationEvent[]`, skipping LOW-tier rows, deriving signal/value from barrel/hh/h2h_factor/opphr per tier (CRITICAL → barrel/HH; HIGH → platoon edge/barrel; MED → HH/pitcher HR9).
- `mainEscalations` state added — initialized to `MOCK_ESCALATIONS` (mock fallback retained), populated from `data.leaderboard_rows` on live fetch.
- `jigEscalations` state added — initialized to `JIG_ESCALATIONS` (mock fallback retained), populated from `data.leaderboard_rows_jig` on live fetch.
- MAIN workspace `EscalationFeed` panel (ESC-01) switched from `MOCK_ESCALATIONS` → `mainEscalations`.
- JIG workspace `EscalationFeed` panel (JIG-ESC) switched from `JIG_ESCALATIONS` → `jigEscalations`.

## What did NOT change

- No model math, scoring, config, pipeline, or API changes.
- No Streamlit (`app.py`) changes.
- No FastAPI (`api/main.py`) changes.
- No Fly.io deployment changes.
- Vercel Root Directory NOT repointed (still points to root `frontend/` static HTML dashboard).
- MAIN/JIG isolation preserved — `mapEscalationEvents` called separately with distinct row sources.

## Data contract

| State | Source field | Notes |
|---|---|---|
| `mainEscalations` | `data.leaderboard_rows` | MAIN workspace |
| `jigEscalations` | `data.leaderboard_rows_jig` | JIG workspace |

## Commit

`feat(frontend): wire EscalationFeed to live slate`

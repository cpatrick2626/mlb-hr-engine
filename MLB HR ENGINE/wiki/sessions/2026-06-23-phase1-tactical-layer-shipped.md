---
title: Phase 1 Tactical Layer Shipped to Live Production Board
date: 2026-06-23
agent: claude-code
status: COMPLETE
tags: [frontend, production, slate-command-strip, hr-threat-zone, vercel, phase1]
---

# 2026-06-23 — Phase 1 Tactical Layer Shipped to Live Production Board

## What shipped

Commit `f512034` — deployed via Vercel to the live production board (root `frontend/`).

Two new components added to the static React-via-Babel production app:

- **Slate Command Strip** (`frontend/assets/js/slate-command-strip.js`) — desktop + mobile. Reads `window.SLATE_GAMES` / `window.SLATE_GENERATED_AT` globals.
- **HR Threat Zone** (`frontend/assets/js/hr-threat-zone.js`) — desktop + mobile. Reads `window.LEADERBOARD_ROWS` globals.
- `frontend/index.html` updated to mount both components.

## Migration decision

Concepts originated in the Next.js prototype (`mlb_hr_engine_v4/frontend/`). They were migrated into the real production app — the live board is and remains the static React-via-Babel app at root `frontend/`. The Next.js app was NOT promoted to production. Vercel Root Directory unchanged.

## Data contract

Components consume existing globals already present in the live board payload:

| Component | Globals read | Notes |
|---|---|---|
| Slate Command Strip | `window.SLATE_GAMES`, `window.SLATE_GENERATED_AT` | Fired on `hrEngineDataLoaded` event |
| HR Threat Zone | `window.LEADERBOARD_ROWS` | Fired on `hrEngineDataLoaded` event |

No new fetch, no new API fields, no backend changes.

## Display labels

- `APEX` / `ELITE` — derived from `tier` field; display-only.
- `BARREL` / `HH` — derived from simple thresholds on barrel/hard-hit fields; display-only.
- No scoring math introduced.

## What did NOT change

- No model math, scoring, config, pipeline, or API changes.
- No Streamlit (`app.py`) changes.
- No FastAPI (`api/main.py`) changes.
- No Fly.io deployment changes.
- Existing Full Slate Matrix unchanged.
- MAIN/JIG separation preserved.
- Next.js prototype (`mlb_hr_engine_v4/frontend/`) not modified.
- Null-safe throughout: missing fields render `"—"` or omit cleanly; no fabricated values.

## Phase 2 candidates (deferred)

| Item | Data available? | Notes |
|---|---|---|
| Pitcher Vulnerability strip | Yes — `row.pitcher_hr9` already in payload | Ready when prioritized |
| Escalation/Signal feed | Yes — APEX + high-barrel rows in payload | Sidebar surface; ready when prioritized |

## Commit

`f512034` — deployed via Vercel

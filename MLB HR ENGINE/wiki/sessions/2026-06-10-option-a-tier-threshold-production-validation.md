# Session: Option A Tier Threshold Production Validation

Date: 2026-06-10
Agent: Claude Code
Owner: Claude Code
Project: MLB HR ENGINE — OPERATIONS
Room: Obsidian Governance Update
Risk Class: LOW
Phase: Document Option A Tier Threshold Production Validation

## Scope

This session records completed production validation for:

1. Option A tier threshold tightening (`f3969b1`)
2. FanDuel full-slate search link fix (`ffa156c`)

No runtime files were modified in this documentation session.
No frontend files were modified in this documentation session.
No backend, API, pipeline, config, or `app.py` files were modified in this documentation session.
No commit was created in this documentation session.
No push was performed in this documentation session.

---

## Commits Recorded

### `f3969b1` — `tune(config): tighten full slate tier thresholds`

- **File:** `mlb_hr_engine_v4/config.py` only
- **Change:** `FS_TIER_THRESHOLDS` tightened under Option A

| Tier   | Threshold |
|--------|-----------|
| APEX   | 0.20      |
| ELITE  | 0.16      |
| EDGE   | 0.11      |
| SIGNAL | 0.07      |
| WATCH  | 0.04      |
| COLD   | 0.00      |

### `ffa156c` — `fix(frontend): align full slate fanduel search links`

- **File:** `frontend/assets/js/full-slate-matrix.js` only
- **Change:** `fsmFanduelUrl` function corrected
- **Live URL pattern:** `https://sportsbook.fanduel.com/search?query=<encoded player name> home run`

---

## Fly.io Deploy

- Result: success
- Image: `deployment-01KTT1166HZRBB8WWAF2R1JBWM`
- Machine: `7841255a9d2e28`
- Machine state: good

---

## API Production Validation

- Endpoint: `https://mlb-hr-api.fly.dev/health` → HTTP 200 `{"status":"ok"}`
- Endpoint: `https://mlb-hr-api.fly.dev/api/slate` → HTTP 200
- `generated_at`: `2026-06-11T00:32:25`
- `from_cache`: false
- `cache_age_minutes`: 0
- MAIN rows: `198`
- JIG rows: `198`

---

## Production Tier Distribution

Snapshot at validation time (2026-06-11T00:32:25):

| Tier   | Count | % of 198 |
|--------|-------|----------|
| APEX   | 18    | 9.1%     |
| ELITE  | 17    | 8.6%     |
| EDGE   | 59    | 29.8%    |
| SIGNAL | 65    | 32.8%    |
| WATCH  | 32    | 16.2%    |
| COLD   | 7     | 3.5%     |

- **Top Targets eligible (ELITE + EDGE):** 76 / 198

---

## Tier Vocabulary Health

- APEX / ELITE / EDGE / SIGNAL / WATCH / COLD confirmed present
- No legacy `AVG` or `WEAK` observed in `row.tier`
- Option A vocabulary fully active in production

---

## Frontend Validation

| Context        | Label shown   | Status |
|----------------|---------------|--------|
| MAIN Full Slate | TIER          | ✓      |
| JIG Full Slate  | MODEL TIER    | ✓      |
| JIG Builder     | MODEL TIER    | ✓      |

Logic confirmed: `isJigContext || builderMode ? "MODEL TIER" : "TIER"` active in deployed JS.

---

## FanDuel Link Validation

- `fsmFanduelUrl` live on Vercel
- URL pattern: `https://sportsbook.fanduel.com/search?query=<encoded player name> home run`
- Commit `ffa156c` active on Vercel

---

## Invariants Preserved

The following were explicitly confirmed unchanged:

- `api/main.py` — no changes
- `pipeline.py` — no changes
- Engine files — no changes
- No MAIN probability changes
- No JIG scoring changes
- No calibration changes
- No Platt parameter changes
- No `MIN_QUAL_PROB` changes
- No Top Targets filter changes
- No barrel gate added
- No `jigTier` added

---

## Repo State at Validation Time

- Branch: `main`
- Most recent commits on `origin/main`:
  - `ffa156c` — `fix(frontend): align full slate fanduel search links`
  - `f3969b1` — `tune(config): tighten full slate tier thresholds`
- Working tree: clean
- No unpushed commits

---

## Verdict

- Option A tier thresholds active in production: **yes**
- Tier vocabulary healthy (no old AVG/WEAK): **yes**
- FanDuel search URL fix live: **yes**
- MAIN Full Slate label correct (TIER): **yes**
- JIG Full Slate label correct (MODEL TIER): **yes**
- JIG Builder label correct (MODEL TIER): **yes**
- Fly.io deploy succeeded: **yes**
- API healthy: **yes**
- Working tree clean: **yes**

---

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/doctrine/tier-vocabulary.md`
- `MLB HR ENGINE/wiki/doctrine/build-log-and-spec-status.md`
- `MLB HR ENGINE/wiki/sessions/2026-06-10-option-a-tier-threshold-production-validation.md`
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md`

---
name: 2026-06-26-auth-slip-calibration-full-build
description: Auth system Phases 0–3 (ES256/JWKS, require_auth/require_beta, user_id stamping), shared slip state (window.__hrSlip), ticket command slip card, add-to-slip on 7 surfaces, persistent top-bar slip button, calibration-ready Supabase storage (migrations 004/005)
metadata:
  type: session
---

# Session: Auth + Slip Infrastructure + Calibration Storage Full Build
**Date:** 2026-06-26
**Agent:** Claude Code (Sonnet 4.6)
**Risk Level:** HIGH — API auth path, Supabase schema, frontend shared state
**Status:** SHIPPED

---

## Scope

Full build delivering auth system, frontend slip architecture, calibration-ready database storage, and add-to-slip wiring across all player-facing surfaces.

---

## Shipped Units

### 1. Auth System (Phases 0–3)

**What changed:**
- `api/auth.py` — ES256/JWKS JWT validation. Supabase issues ES256 JWTs (not HS256). Original validation used HS256 + `SUPABASE_JWT_SECRET`; replaced with JWKS fetch from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`. `kid`-keyed cache with force-refresh on cache miss (key rotation resilient).
- `require_auth` dependency: validates JWT, returns user dict. Gates write endpoints.
- `require_beta` dependency: validates JWT + checks beta_users table. Gates beta-only endpoints.
- Per-user `user_id` stamping on all write paths (add_leg, complete_ticket). Ownership enforced.
- `beta_invites` / `beta_users` tables (in migration 001) used for invite redemption flow.

**Frontend auth (auth.js):**
- Supabase login modal (email/password)
- Email-confirm flow
- Invite redemption (beta_invites → beta_users)
- Auth chip in topbar (shows logged-in user)

**Commits:** 119cf4c, f359d87, e37fd9f, b22ed79, fda5a69

**Protected surfaces untouched:** MAIN/JIG scoring, pipeline.py, config.py, all model constants.

---

### 2. Calibration-Ready Storage (Migrations 004 + 005)

**Applied via Supabase Dashboard (not CLI — no local migrations dir):**

- **Migration 004:** `tickets.user_id` column — per-user ownership of tickets.
- **Migration 005:** `legs` table calibration fields:
  - `hr_result smallint` — settlement value (NULL until settled)
  - `settlement_status text DEFAULT 'pending'`
  - `settled_at timestamptz`
  - `market_odds_american numeric` — NULL (no source yet; store now, calibrate later)
  - `market_prob numeric` — NULL (same)
  - `pitcher text`
  - `leg_date date` — mirrors ticket's slate date (not server UTC)

**API write-path fixes:**
- `add_leg` now writes: `player_id` (from row.id), `team`, `pitcher`, `leg_date`
- `complete_ticket` now accepts and writes `tickets.stake`
- market_* fields intentionally NULL (no market data source on leg-add path)

**Doctrine:** "Store now, calibrate later." Settlement is a separate future step.

---

### 3. Ticket Command Slip Card (ticket-command.js)

**File:** `frontend/assets/js/ticket-command.js` + CSS in `index.html`

**What it does:**
- Displays active ticket legs: player name, team, HR prob, tier, barrel%, hard hit%, pitcher
- Bright solid panel design
- "SAMPLE" tags on non-real intelligence panels (probability engine, grade, confidence, payout)
- Empty fields hidden (no placeholder dashes for NULL values)
- Mobile + desktop responsive

**Integrity:** No fabricated numbers displayed. SAMPLE tags are explicit on any panel not wired to real data.

**Commit:** dab146e

---

### 4. Shared Slip State — window.__hrSlip (slip-state.js)

**File:** `frontend/assets/js/slip-state.js`

**Architecture:** Single global object. Holds ticketId + legs array. Exposes:
- `getState()` — returns current slip state
- `subscribe(fn)` — registers listener for state changes
- `addLeg(payload)` — adds a leg; payload validated before write
- `removeLeg(legId)` — removes a leg by id
- `buildLegPayload(row, board)` — constructs a valid leg payload from a player row
- `openSlip()` / `closeSlip()` — controls slip overlay visibility

**Leg payload invariant:** Always carries `player_id` (from `row.id`) + decimal `model_prob` (NOT `hrprob×100`, NOT `jigScore`, NOT `hrpa`). This is the calibration integrity constraint.

**Commit:** a529779 (Step 0)

---

### 5. Add-to-Slip — All Player Surfaces

| Surface | Board | Status | Notes |
|---------|-------|--------|-------|
| HR Threat Zone | MAIN | WIRED | Origin surface |
| Full Slate Matrix | MAIN/JIG | WIRED | commit 3163ced |
| JIG Command | JIG | WIRED | Inherited via FSM builderMode |
| All Batters Leaderboard | MAIN | WIRED | commit d64e7d3 |
| Strategy Rail | MAIN | WIRED | commit 414c210 |
| Command Tab | MAIN + JIG | WIRED | commit 86e637c; board:'main' and board:'jig' |
| Escalation Feed | MAIN | WIRED | commit c9f80ad; field renames: row.player→name, row.team→teamAbbr |
| **LIVE Targets Banner** | MAIN | **INTENTIONALLY BLOCKED** | Hardcoded mock, no player_id — would write uncalibratable legs |

**LIVE Targets Banner block rationale:** The banner uses hardcoded mock data with no real `player_id`. Wiring add-to-slip would write legs with NULL or incorrect player IDs, corrupting calibration data. Block is intentional and must not be removed until the banner is wired to real API rows.

---

### 6. Persistent Top-Bar Slip Button (slip-btn.js)

**File:** `frontend/assets/js/slip-btn.js`

**Behavior:**
- Renders "SLIP · N" counter left of account auth chip in topbar
- Appears only when legs ≥ 1 (zero-state hidden)
- Opens shared slip overlay from any page/view
- Uses `window.__hrSlip.subscribe()` to reactively update count

**Architecture:** SlipOverlayHost — centralized single overlay mount point. Previous pattern (per-component overlay) replaced with single mount to prevent duplicate overlays.

**Commit:** 671bc51 (+ left-of-name positioning tweak)

---

### 7. Parked — Batter Card + Arsenal Edge Exploit

**Status:** PARKED — data audits complete, architecture gate not cleared.

**What's computed but stranded:**
- Arsenal/pitch-mix data: computed by pipeline, NOT emitted in `/api/slate` payload
- Pitcher fatigue: computed, NOT emitted
- Pitcher vulnerability score (0–100): no endpoint
- Batter spray coordinates: no data source

**What IS real (approximately half the batter card):**
- Player name, team, tier, model_prob, barrel%, hard hit%, xSLG, lineup_spot
- Opponent, pitcher name, park_factor, pitcher_factor
- Matchup modifier (h2h_factor)

**Architecture blocker:** Pregame-only design (~90% of the card). Live At-Bat panel requires real-time inning/count/pitch data — new infrastructure not yet built. Spray chart requires coordinate data source (not in current API).

**File created:** `frontend/assets/js/arsenal-edge-exploit.js` (untracked — do NOT commit without operator authorization for new room)

**Handoff doc status:** Not yet written to vault. PENDING — operator to authorize new room before handoff is formalized.

---

## Files Changed This Session

| File | Type | Change |
|------|------|--------|
| `api/auth.py` | Python API | ES256/JWKS replace HS256 |
| `frontend/assets/js/auth.js` | Frontend | Supabase auth modal + flows |
| `frontend/assets/js/slip-state.js` | Frontend | window.__hrSlip architecture |
| `frontend/assets/js/ticket-command.js` | Frontend | Ticket Command Slip Card |
| `frontend/assets/js/slip-btn.js` | Frontend | Persistent top-bar button |
| `frontend/assets/js/hr-threat-zone.js` | Frontend | Add-to-slip origin |
| `frontend/assets/js/full-slate-matrix.js` | Frontend | Add-to-slip |
| `frontend/assets/js/jig-command.js` | Frontend | Add-to-slip (JIG) |
| `frontend/assets/js/cfdd4178-*.js` | Frontend | Add-to-slip on Leaderboard + Escalation Feed field renames |
| `frontend/index.html` | Frontend | CSS + script tags for new components |
| `frontend/assets/js/arsenal-edge-exploit.js` | Frontend | Untracked — parked |
| Supabase Dashboard | Schema | Migrations 004 (tickets.user_id) + 005 (legs calibration fields) |

---

## Protected Surfaces — Confirmed Untouched

- MAIN/JIG scoring (config.py, engine/, probability.py) — NO changes
- pipeline.py — NO changes
- FastAPI routing (api/main.py) — auth gating added to existing routes only; no route restructuring
- Streamlit (app.py) — NO changes
- session_state ownership — NO changes

---

## Cross-References

- [[supabase-schema]] — update needed (migrations 004/005, legs table)
- [[session-state-map]] — update needed (window.__hrSlip section)
- [[production-surface-truth]] — update needed (slip card, add-to-slip, auth chip)
- [[frontend-topology]] — update needed (new live bundle files)
- [[known-gaps]] — Batter Card / Arsenal Edge Exploit parked status

# Session State Map

## Summary

Streamlit's `session_state` is a protected surface in the MLB HR Engine. Each key has a defined owner (room or system component). Cross-room writes are prohibited. Routing and modal state are closed surfaces per `PHASE3_REFINEMENT_DOCTRINE.md`. This page tracks known ownership boundaries — Claude Code should populate this via repo audit before any session_state work.

## Key Points

### Ownership Rules
- Each room owns its session_state keys. A room may read shared/global keys but must not write to another room's keys.
- Routing keys (navigation state, current room) are owned by the routing layer — closed surface.
- Modal state keys are owned by the modal architecture — closed surface.
- Hydration keys (data freshness, load status) are owned by the hydration logic — closed surface.
- Cache keys are documented separately in [Cache Ownership Map](cache-ownership-map.md).

### Known Protected Key Groups
| Key Group | Owner | Status |
|-----------|-------|--------|
| Routing/navigation state | Routing architecture | CLOSED — no modification without authorization |
| Modal open/close state | Modal architecture | CLOSED — no modification without authorization |
| Hydration/load state | Hydration logic | CLOSED — no modification without authorization |
| Cache state | Cache ownership layer | CLOSED — see Cache Ownership Map |
| MAIN pick results | MAIN pipeline surface | Protected |
| JIG pick results | JIG pipeline surface | Protected |

**Note:** Full key inventory requires Claude Code audit of `app.py` and `pipeline.py`. This stub reflects known protected categories from doctrine.

## FD Slip Reference Keys

- `min_ev` and `min_edge` feed FD Slip at line `10365`
- Cannot remove without touching routing
- Default set to `0.0`
- Display-reference only

---

## Frontend Global State — window.__hrSlip

The frontend (root `frontend/`, Vercel static) uses a separate state system from Streamlit `session_state`. The primary shared-state object is `window.__hrSlip`, defined in `frontend/assets/js/slip-state.js`.

**This is NOT Streamlit session_state.** It is a JavaScript global on the live production board.

### Architecture

```js
window.__hrSlip = {
  getState()                    // → { ticketId, legs: [] }
  subscribe(fn)                 // register reactive listener
  addLeg(payload)               // add a leg to active slip
  removeLeg(legId)              // remove a leg by id
  buildLegPayload(row, board)   // constructs valid leg payload from API row
  openSlip()                    // show slip overlay
  closeSlip()                   // hide slip overlay
}
```

### Leg Payload Invariant

Every leg payload carries:
- `player_id` — from `row.id` (API field, used for Supabase `legs.player_id`)
- `model_prob` — decimal from `row.model_prob` (e.g. `0.187`)
- `board` — `'main'` or `'jig'`

**NEVER:** `row.hrprob × 100`, `row.jigScore`, `row.hrpa`. These are display values, not calibration values.

### Ownership Rules

- `window.__hrSlip` is owned by `slip-state.js` exclusively
- All add-to-slip surfaces (`hr-threat-zone.js`, `full-slate-matrix.js`, `jig-command.js`, etc.) call `window.__hrSlip.addLeg()` — they do NOT maintain their own slip state
- `slip-btn.js` subscribes to `window.__hrSlip` to reactively update the topbar count
- `ticket-command.js` (Ticket Command Slip Card) subscribes to display current legs

### Surfaces That Write to window.__hrSlip

| Surface | Board | Notes |
|---------|-------|-------|
| HR Threat Zone | MAIN | Origin surface |
| Full Slate Matrix | MAIN/JIG | |
| JIG Command | JIG | |
| All Batters Leaderboard | MAIN | |
| Strategy Rail | MAIN | |
| Command Tab | MAIN + JIG | board:'main' and board:'jig' |
| Escalation Feed | MAIN | |
| LIVE Targets Banner | — | **INTENTIONALLY BLOCKED** — no real player_id |

### Cross-References

- [Frontend Topology](frontend-topology.md) — live bundle inventory
- [Supabase Schema](supabase-schema.md) — legs table (calibration target)
- [Production Surface Truth](../doctrine/production-surface-truth.md) — add-to-slip surface map

## Cross-References

- [Cache Ownership Map](cache-ownership-map.md)
- [Pipeline Data Flow](pipeline-data-flow.md)
- [Room Governance](../doctrine/room-governance.md)
- [MAIN/JIG Separation Rules](../doctrine/main-jig-separation.md)

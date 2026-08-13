---
date: 2026-08-12
agent: Claude Code
task: Private bet slip history view
commit: e65d2f5
---

## Summary

Added a **History** tab to the Community room. Fetches `GET /api/my-tickets` (JWT-gated, caller-scoped). No backend change, no schema change, no public board touched.

---

## Architecture

**Endpoint:** `GET /api/my-tickets`  
**Auth:** JWT required (caller sees only their own tickets)  
**Handler:** `api/ticket_history.py → get_my_tickets()`  
**Frontend:** `frontend/assets/js/slip-history.js` (new, 360 lines)

The endpoint returns the caller's tickets with legs and game linescores. Leg fields returned: `hr_result`, `settlement_status`, `removed`.

**Grouping:** Frontend groups tickets by `ticket.date` descending. Each date section is collapsible. Clicking a date expands the day's slips.

---

## Outcome derivation (client-side, `slip-history.js`)

No whole-ticket result field exists in the DB schema — outcomes are derived on read.

**Per-leg badge** (`shLegBadge`):
- `settlement_status === 'void'` → **VOID**
- `settlement_status === 'settled'` + `hr_result === 1` → **HIT**
- `settlement_status === 'settled'` + `hr_result === 0` → **MISS**
- Otherwise → **PENDING**

**Whole-slip outcome** (`shSlipOutcome`): VOID legs are neutral.
- All legs VOID → **VOID**
- Any non-VOID leg PENDING → **PENDING**
- Any non-VOID, non-PENDING leg is MISS → **LOSS**
- All non-VOID legs are HIT → **WIN**

---

## UI behavior

- Signed-out: private gate state shown (no data exposed)
- Empty history: clean empty state
- Older slips are excluded from the active public board (see [[2026-08-12-community-today-only-filter]]) but appear here in History
- No add, edit, or post action available from History

---

## Protected surfaces

- No scoring, calibration, or pipeline logic touched
- No schema change (outcome is derived read-only from existing `hr_result` + `settlement_status` leg fields)
- Public `GET /api/community/posts` board unchanged

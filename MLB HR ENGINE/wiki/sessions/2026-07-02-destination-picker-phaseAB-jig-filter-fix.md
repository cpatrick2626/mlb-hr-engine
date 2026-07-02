# Session: Destination Picker Phase A+B + JIG Builder Filter Fix + Vault Corrections — 2026-07-02

Date: 2026-07-02
Agent: Claude Code (execution)
Owner: Operator (Kylar)
Project: MLB HR ENGINE - TICKETS / TCC
Risk Class: MEDIUM (tickets API + frontend add-surface interception); LOW (docs, JIG filter fix)
Phase: Destination picker Phases A+B shipped; Phase C deferred
Status: COMPLETE / SHIPPED (A deployed to Fly, B auto-deployed via Vercel)

## Scope

Four workstreams this session:

1. **JIG Builder filter fix** (`9530d62`) — APPLY TO ROOM now actually filters the JIG room.
2. **Vault/memory corrections** (`9995ad1`) — stale auth/slip claims corrected per audit.
3. **Destination picker spec** (`b94d697`) — audit + phased design committed to roadmap.
4. **Destination picker Phase A** (`c10a175`, Fly) + **Phase B** (`0c167da`, Vercel) — slip integrity backend + 4-option picker modal shipped and verified live.

Plus one investigation closed as a non-issue (deploy "caching" — see below).

---

## Commits (chronological, this session)

| Commit | Summary |
|--------|---------|
| `9530d62` | fix(tcc): JIG Builder filters apply to slate — roomKey scoped per-engine + JigCommand applies appliedFilters |
| `9995ad1` | docs(vault): correct stale auth/slip claims per 2026-07-02 audit |
| `b94d697` | docs(roadmap): destination-picker spec — audit + phased design |
| `c10a175` | feat(tickets): Phase A slip integrity — server-side leg removal, non-building guard, resetSlip |
| `0c167da` | feat(tickets): Phase B destination picker — 4-option modal intercepting all add surfaces |

---

## 1. JIG Builder Filter Fix (`9530d62`)

**Bug:** JIG Builder filters never applied to the slate. `roomKey` was scoped per-lens (wrong bucket), and `JigCommand` never read `appliedFilters`.

**Fix:** `roomKey` scoped per-engine + `JigCommand` applies `appliedFilters`. APPLY TO ROOM now filters the whole JIG room, with AND logic across active filters.

**Verified live:** `xSLG >= 0.700` and `Barrel% >= 12.0` both correctly filter the room. No Barrel% scale bug exists — the earlier "10.7% showing under a 12.0 filter" observation was the pre-fix broken routing, not a unit mismatch.

**Backlog:** 30 of 46 JIG Builder filter fields are still DEAD — Steppers with no `onChange` and no predicate. Wiring them (batched by panel) is recorded as backlog.

---

## 2. Vault/Memory Corrections (`9995ad1`)

An audit of the live root `frontend/` and tickets API found earlier vault claims stale:

- **Auth IS built** — `auth.js` (Supabase email/password + invite-code gating), live since 2026-06-26. Earlier "auth not built / hard prerequisite not met" claims were stale.
- **Slip capture IS real** — 8 surfaces write real Supabase `tickets`/`legs` rows. Only the overlay analytics (combined probability / grade / confidence / payout) are SAMPLE placeholders.

Corrected: `doctrine/ticket-slip-system.md` + `projects/ticket-data-capture-phase1-architecture.md`. True caveats preserved (overlay analytics SAMPLE; settlement not built; at that point removeLeg/resetSlip gaps were still open — closed later this session by Phase A).

**Unblocks** auth-dependent roadmap items: per-user attribution, per-user preference persistence (e.g. column order), friends access.

---

## 3. Destination Picker Spec (`b94d697`)

`wiki/roadmap/destination-picker-spec.md` — Fable 5 audit of all slip/FD surfaces + phased design: Phase A backend integrity, Phase B picker MVP (Options 1–3), Phase C Option 4.

---

## 4. Destination Picker Phase A — Slip Integrity (`c10a175`, deployed to Fly)

Backend integrity fixes closing the two bugs from the audit:

- **`POST /api/tickets/leg/remove`** — soft-delete (`legs.removed=true`), ownership-checked.
- **Server guard** — rejects `add_leg` on non-`building` tickets (409). Stale client `ticketId` can no longer append legs after submit.
- **Client `resetSlip()`** — clears ticketId/legs/cardStatus after submit.
- **`removeLeg` now persists server-side** (was client-only array filter).

**Verified against real Supabase rows:** added 2 legs (Schwarber + Marsh), removed 1, completed → ticket `num_legs=1`; Schwarber leg `removed=true` (soft-deleted), Marsh `removed=false`. The num_legs-excludes-removed integrity bug is fixed and proven.

---

## 5. Destination Picker Phase B — Picker Modal (`0c167da`, auto-deployed Vercel)

`frontend/assets/js/destination-picker.js` — 4-option modal:

1. **FD Only**
2. **Add to Slip Only**
3. **FD + Slip**
4. **Option 4** (FD + confirm slip + start new seeded ticket) — **disabled**, Phase C.

Interception: all **8 add surfaces + 3 FD-only actions** now route through `window.__hrSlip.requestAdd()` → picker. Implementation notes:

- Tactical HUD portal styling.
- **Synchronous `window.open` before any `await`** — keeps the FD popup inside the user-gesture window (popup-blocker-safe).
- `noauth` gating.

**Verified:** laptop — picker renders from surfaces, Option 2 adds a leg, Option 4 disabled, HUD styling correct. Phone/live — Option 3 opened FanDuel AND added the leg (popup rule holds on mobile).

---

## 6. Deploy "Caching" Investigation — NON-ISSUE (closed)

Investigated "always running old build" after deploys. **Root cause: open tabs not reloading after deploy — not a cache bug.** Production already serves `Cache-Control: max-age=0, must-revalidate` + ETags (correct behavior). A `vercel.json` cache config would be a no-op; none added.

Fix for solo use: reload the tab after deploy. Follow-up logged for the friends/PWA phase: in-app "new version available — reload" prompt to cover the open-tab case.

---

## Invariants Preserved

- MAIN/JIG separation intact; no scoring/probability changes.
- HVY remains display-only.
- Picker is a routing/UX layer over the existing `addLeg` path; leg snapshot content unchanged.
- `config.py` thresholds unchanged.

---

## Backlog (recorded this session)

- **Destination picker Phase C:** Option 4 (FD + confirm slip + start new seeded ticket) — prerequisites built in Phase A; spec §3.2.
- **Phase D:** ticket rehydration endpoint (`GET /api/tickets/current`), settlement job (`legs.hr_result`), real market odds capture.
- **"New version available — reload" prompt** (friends/PWA phase).
- **30 dead JIG Builder filter Steppers** — wire onChange + build predicates, batched by panel.
- **UX queue:** sticky stats header / stat-in-cell, persistent horizontal scrollbar, TCC-mobile (sticky APPLY TO ROOM + visibility), mobile drag-reorder columns with per-user persistence (NOW UNBLOCKED by auth).
- **Fly health check** — machine has no CHECKS. **Node 20 deprecation** on GH Actions.
- **AEI vulnerability thresholds** (1.45/1.05) vs `config.py` `[1.50, 1.20, 1.00, 0.80]` alignment (carried from 2026-07-01).

---

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/sessions/2026-07-02-destination-picker-phaseAB-jig-filter-fix.md` (this file — new)
- `MLB HR ENGINE/wiki/doctrine/ticket-slip-system.md` (updated — Phase A+B live; integrity bugs marked fixed)
- `MLB HR ENGINE/wiki/log.md` (appended)
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md` (appended)

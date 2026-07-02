# Ticket Slip System — Doctrine

> **STATUS: LIVE (build-slip workflow) — with two NOT-BUILT gaps.**
> Adding legs, viewing/managing the slip, persistence, and marking a slip deployed all work end-to-end.
> **NOT BUILT: (1) leg settlement** — `legs.hr_result` / `settlement_status` are never written; the outcome loop does not close. **(2) overlay combined probability / grade / confidence / payout** are **SAMPLE / "Engine Pending" placeholder values, NOT real engine output.** Do not describe these as real.

> **CORRECTION (2026-07-02 — destination-picker audit):** Earlier versions of this doc stated "Four surfaces" for add-to-slip. A code audit of root `frontend/` confirmed **eight** surfaces call `window.__hrSlip.addLeg()`. The add-to-slip table and Key Points below have been updated to reflect this. Auth section added: `auth.js` (Supabase email/password + invite-code beta gating) IS built and live as of 2026-06-26 — any prior note calling auth a "hard prerequisite not yet met" is stale. Two known integrity bugs added per audit findings.

> **UPDATE (2026-07-02 — destination picker Phase A+B LIVE):** Phase A (`c10a175`, Fly) closed both integrity bugs: `removeLeg` now persists server-side via `POST /api/tickets/leg/remove` (soft-delete, ownership-checked), a server guard rejects legs on non-`building` tickets (409), and the client calls `resetSlip()` after submit. Verified against real Supabase rows. Phase B (`0c167da`, Vercel) added `destination-picker.js`: all 8 add surfaces + 3 FD-only actions now route through `window.__hrSlip.requestAdd()` → a 4-option destination picker (FD Only / Add to Slip / FD+Slip / Option 4 disabled pending Phase C) before `addLeg()` fires. Spec: `wiki/roadmap/destination-picker-spec.md`.

---

## Summary

The Ticket Slip System lets a user build a slip of HR picks from the board, view/manage it, and mark it deployed — this is live and used. The leg DATA is real: all eight add-to-slip surfaces POST through `window.__hrSlip.addLeg()` to `/api/tickets/leg`, writing real Supabase `tickets`/`legs` rows with a frozen engine snapshot. Two halves are not built: outcome settlement (closing the loop) and the slip overlay's combined-probability/grade engine (currently SAMPLE placeholder values).

---

## Key Points

- **Build-slip workflow is DOCTRINE-LIVE.** Eight surfaces wire `window.__hrSlip.addLeg()`, the overlay shows real legs with real data, Supabase persistence is wired, and deploy/complete is functional.
- **Settlement is schema-only.** `legs.hr_result`, `settlement_status`, `settled_at` columns exist in migration 005 but no script, cron, or endpoint writes them. The outcome loop does not close.
- **Overlay analytics are MOCK.** Combined probability, grade, confidence, and payout shown in the overlay are `SAMPLE` / `"Engine Pending"` placeholders — not engine output.
- **FD "deploy" is intent, not capture.** The FanDuel button is a plain `<a href>` external link. `fd_deployed=True` records that the user clicked Submit — it does not confirm a bet was placed.

---

## LIVE — Works End-to-End (DOCTRINE)

### Add-to-slip

Eight surfaces wire `window.__hrSlip.addLeg()` with no mock blocks (confirmed by 2026-07-02 destination-picker audit). As of Phase B (`0c167da`), all eight route through `window.__hrSlip.requestAdd()` → destination picker modal before `addLeg()` fires:

| Surface | File:Line | Board |
|---|---|---|
| HR Threat Zone | `hr-threat-zone.js:106-122` | MAIN |
| Full Slate Matrix | `full-slate-matrix.js:561-578` (SLIP column); per-row `:625` | MAIN/JIG |
| JIG Command | `jig-command.js:40` (inherits FSM SLIP column in `builderMode`) | JIG |
| All Batters Leaderboard | `c0092a94-d9b6-4c58-946b-1b3ea3b7976b.js:200` | MAIN |
| Strategy Rail | `32ab40c7-e667-469e-9b09-c6a46761c1cd.js:123` | MAIN |
| Command Tab | `command-tab.js:226` | MAIN + JIG |
| Escalation Feed | `escalation-feed.js:76-77` | MAIN |
| Arsenal Edge Exploit modal | `arsenal-edge-exploit.js:86-100` | MAIN |

All eight funnel through the one shared store (`slip-state.js` `window.__hrSlip.addLeg()`). The LIVE Targets Banner is intentionally NOT wired — hardcoded mock data, no real `player_id`; wiring would corrupt calibration data.

### Slip view/manage

- **SLIP·N top-bar button** (`slip-btn.js:48`) opens the overlay `TicketCommandSlip` (`slip-btn.js:70`).
- Per-leg cards display: name, team, tier, HR prob, barrel, hard-hit, pitcher, and a working Remove action (`ticket-command.js:27`, `removeLeg` at `slip-state.js:128`).
- Users see all legs and can remove them.

### Persistence

- Supabase `tickets` + `legs` tables exist via migrations 003–005 (columns include `hr_result`, `settlement_status`, `pitcher`, `leg_date`, `market`).
- `add_leg()` in `cache.py:138` writes leg rows.
- `POST /api/tickets/leg` is auth-gated (`main.py:200`).
- Client posts via `authFetch` (`slip-state.js:87`).

### Deploy/complete

- `complete_ticket()` sets `fd_deployed=True`, `status='pending'`, `completed_at` (`cache.py:196`).
- `POST /api/tickets/complete` is wired (`main.py:237`).
- `handleSubmit` posts `{ticket_id, stake}` (`ticket-command.js:335`).
- `window.SLATE_GENERATED_AT` is captured at tap time.

### Authentication

Auth IS built and live (as of 2026-06-26). `frontend/assets/js/auth.js` provides full Supabase email/password sign-in + invite-code beta gating. `authFetch` attaches the JWT; ticket endpoints use `Depends(require_auth)`; `tickets.user_id` is stamped on all write paths. Any prior note calling auth a "hard prerequisite not yet built" is stale — per-user features are now unblocked.

---

## NOT BUILT — Do Not Describe as Real

### Leg settlement — schema only

`legs.hr_result`, `settlement_status`, and `settled_at` columns exist (migration 005) but **no script, cron, or endpoint writes them.** `POST /api/ops/settle` settles the engine's own `pick_tracker.csv` (`tracking/pnl`) — it does **not** write to the `legs` table. The slip outcome loop does not close.

### Overlay analytics are MOCK

Combined probability, grade, confidence, and payout shown in the overlay are **`SAMPLE` / `"Engine Pending"` placeholders** (`ticket-command.js:24`; panels at lines ~122–178). These are not produced by the engine. A real slip-grade / parlay-probability engine is not built.

### FanDuel deploy is an intent link, not a capture

The FD button is an external `<a href>` (`ticket-command.js:53`). `fd_deployed=True` records that the user clicked Submit. It does **not** confirm a bet was placed on FanDuel. The FD "hand-off" in all surfaces is `sportsbook.fanduel.com/search?q=<player name>` + clipboard copy + toast — a search URL, **not a deep-link or pre-filled bet**. FanDuel has no public slip-building API; a true pre-filled-bet link is not feasible.

---

## Known Integrity Bugs (FIXED 2026-07-02 — Phase A, `c10a175`)

Both bugs found in the 2026-07-02 audit were closed by destination-picker Phase A, deployed to Fly and verified against real Supabase rows (added 2 legs, removed 1, completed → `num_legs=1`, removed leg soft-deleted with `removed=true`):

1. **`removeLeg` was client-only** — filtered the local array without touching the server, so a client-removed leg silently re-entered `num_legs` on confirm. FIXED: `removeLeg` now calls `POST /api/tickets/leg/remove` (soft-delete `legs.removed=true`, ownership-checked); `complete_ticket` counts only non-removed legs.

2. **No `resetSlip()`** — after submit, a stale `ticketId` kept receiving legs. FIXED: client `resetSlip()` clears ticketId/legs/cardStatus after submit + server guard rejects `add_leg` on non-`building` tickets (409).

---

## To Close the Gaps (Future Work)

1. **Leg settlement job** — reuse `backtest/outcomes.py` `get_game_results()` to write `legs.hr_result` / `settlement_status` so deployed picks settle against real HR outcomes.
2. **Real combined-probability/grade engine** — replace `SAMPLE` overlay values with actual parlay probability and slip-grade computation.
3. **(Optional) Verified FD capture** — replace the intent link with confirmed placement capture.

---

## Cross-References

- Supabase schema: `tickets`, `legs` tables (migrations 003–005)
- Historical Replay roadmap (shares the outcomes/settlement need)
- Calibration / feedback loop (deferred until N threshold; requires settled legs to proceed)
- `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` — governing deployment and FD slip tracking
- `tracking/pnl` / `pick_tracker.csv` — the existing settlement target for the engine's own picks (separate from leg settlement)

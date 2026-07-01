# Ticket Slip System — Doctrine

> **STATUS: LIVE (build-slip workflow) — with two NOT-BUILT gaps.**
> Adding legs, viewing/managing the slip, persistence, and marking a slip deployed all work end-to-end.
> **NOT BUILT: (1) leg settlement** — `legs.hr_result` / `settlement_status` are never written; the outcome loop does not close. **(2) overlay combined probability / grade / confidence / payout** are **SAMPLE / "Engine Pending" placeholder values, NOT real engine output.** Do not describe these as real.

---

## Summary

The Ticket Slip System lets a user build a slip of HR picks from the board, view/manage it, and mark it deployed — this is live and used. Two halves are not built: outcome settlement (closing the loop) and the slip overlay's combined-probability/grade engine (currently mock placeholder values).

---

## Key Points

- **Build-slip workflow is DOCTRINE-LIVE.** Four board surfaces wire `window.__hrSlip.addLeg()`, the overlay shows real legs with real data, Supabase persistence is wired, and deploy/complete is functional.
- **Settlement is schema-only.** `legs.hr_result`, `settlement_status`, `settled_at` columns exist in migration 005 but no script, cron, or endpoint writes them. The outcome loop does not close.
- **Overlay analytics are MOCK.** Combined probability, grade, confidence, and payout shown in the overlay are `SAMPLE` / `"Engine Pending"` placeholders — not engine output.
- **FD "deploy" is intent, not capture.** The FanDuel button is a plain `<a href>` external link. `fd_deployed=True` records that the user clicked Submit — it does not confirm a bet was placed.

---

## LIVE — Works End-to-End (DOCTRINE)

### Add-to-slip

Four surfaces wire `window.__hrSlip.addLeg()` with no mock blocks:

| Surface | File:Line |
|---|---|
| HR Threat Zone | `hr-threat-zone.js:106` |
| Full Slate Matrix — SLIP column header | `full-slate-matrix.js:561`, `:612` |
| Full Slate Matrix — per-row `onAddLeg` | `full-slate-matrix.js:625` |
| Escalation Feed | `escalation-feed.js:76` |
| Arsenal Edge Exploit | `arsenal-edge-exploit.js:86` |

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

---

## NOT BUILT — Do Not Describe as Real

### Leg settlement — schema only

`legs.hr_result`, `settlement_status`, and `settled_at` columns exist (migration 005) but **no script, cron, or endpoint writes them.** `POST /api/ops/settle` settles the engine's own `pick_tracker.csv` (`tracking/pnl`) — it does **not** write to the `legs` table. The slip outcome loop does not close.

### Overlay analytics are MOCK

Combined probability, grade, confidence, and payout shown in the overlay are **`SAMPLE` / `"Engine Pending"` placeholders** (`ticket-command.js:24`; panels at lines ~122–178). These are not produced by the engine. A real slip-grade / parlay-probability engine is not built.

### FanDuel deploy is an intent link, not a capture

The FD button is an external `<a href>` (`ticket-command.js:53`). `fd_deployed=True` records that the user clicked Submit. It does **not** confirm a bet was placed on FanDuel.

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

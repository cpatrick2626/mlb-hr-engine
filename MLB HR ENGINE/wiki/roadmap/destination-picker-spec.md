# Destination Picker — Design Spec (read-only audit + design, 2026-07-02)

Status: DESIGN — not implemented. Produced by read-only audit of repo-root `frontend/` (the LIVE Vercel tree) + `mlb_hr_engine_v4/api/`. A later Claude Code session executes from this spec.

---

## 1. Executive summary

**Buildable now (no new backend):** the picker itself, Options 1–3, and Option 4's client half. The slip is REAL — `window.__hrSlip` (shared plain-JS store, `frontend/assets/js/slip-state.js`) POSTs each leg to `https://mlb-hr-api.fly.dev/api/tickets/leg` (JWT-gated), which writes real Supabase `tickets`/`legs` rows. Ticket confirm exists (`POST /api/tickets/complete` → `fd_deployed=true`, `status='pending'`, stake). Auth IS built (Supabase email/password + invite-code beta gate, `frontend/assets/js/auth.js`) — earlier "auth not built" notes are stale.

**Blocked / partial:**
- **FD hand-off is NOT a bet deep-link.** It's `sportsbook.fanduel.com/search?q=<player name>` in a new tab + clipboard copy of the name + a toast. FanDuel has no public slip-building API; a true pre-filled-bet link is not feasible without FD internal market IDs. Options 1/3/4 must be specced against the search-URL hand-off, honestly labeled ("opens FD search — place bet manually").
- **Leg removal is client-only.** `removeLeg` (slip-state.js:128) filters the local array; nothing sets `legs.removed=true` server-side, and `complete_ticket` counts server-side non-removed legs (cache.py:227-234) — a removed leg silently re-enters `num_legs`. Pre-existing bug; Option 4's "confirm" amplifies it. Fix required before Option 4 ships.
- **No slip reset / new-slip client op.** After submit, `ticketId` + `legs` stay in `_state` forever. Server-side "new ticket" already exists implicitly (addLeg with null ticket_id). Small client build: `resetSlip()`.
- **Settlement not built.** `legs.hr_result` / `settlement_status` columns exist (migration 005) but no job writes them; overlay analytics (grade/combined prob/payout) are `—` + `SAMPLE` tags, honestly labeled.
- **Slip does not survive reload.** No `GET /api/tickets` read endpoint; client state is in-memory only.

---

## 2. Audit — the add surfaces (verified in code)

**Eight** surfaces call `window.__hrSlip.addLeg(normalizedRow)` (memory said 7; Arsenal Edge Exploit is an 8th):

| # | Surface | File / add handler | Also has FD action? |
|---|---------|--------------------|---------------------|
| 1 | HR Threat Zone | `frontend/assets/js/hr-threat-zone.js:106-122` (`onAdd` at :142/:150) | no |
| 2 | Full Slate Matrix | `full-slate-matrix.js:561-578` (`handleAddLeg`); SLIP column btn :446 | YES — tier-cell "+ FD" button :399-410 → `fsmOpenFD` :299 → `fsmOpenFanDuelSearch` :290-296; batter-card "+ ADD TO FANDUEL" links :790, :1075, :1459 |
| 3 | JIG Command | `jig-command.js:40` renders `FullSlateMatrix builderMode={true}` — inherits FSM's SLIP column/handler (:446/:561); board tagged `'jig'` (:573). builderMode HIDES the FD tier button (:390-397) and card FD links (`!builderMode`) | no (suppressed in builder mode) |
| 4 | All Batters Leaderboard | `c0092a94-d9b6-4c58-946b-1b3ea3b7976b.js:200` (`handleAddLeg`), slip btn :187 | YES — per-row "FD" link :179 → `hrLbOpenFanduel` :79-95 |
| 5 | Strategy Rail | `32ab40c7-e667-469e-9b09-c6a46761c1cd.js:123` (`handleAddLeg`), slip btn :105 | YES — whole-card click → `stratOpenFanduel` :30-50 (multi-player: copies all names, searches first) |
| 6 | Command Tab | `command-tab.js:226` | no |
| 7 | Escalation Feed | `escalation-feed.js:76-77` | no |
| 8 | Arsenal Edge Exploit modal | `arsenal-edge-exploit.js:86-100` | no |

Plus the **Ticket Command overlay** itself (`ticket-command.js`): static FD links (`TC_FD_URL = sportsbook.fanduel.com/baseball`, :8, per-leg :53-57, deploy bar :260-263/:310-313) and the Submit action (:335-357 → `POST /api/tickets/complete`).

All eight already funnel through the ONE shared store — `slip-state.js` `window.__hrSlip.addLeg()`. Consistency is therefore cheap: intercept at the store, not at eight call sites.

### What Add-to-Slip does today (REAL)
`slip-state.js:66-126`: status machine per player (`idle/loading/added/error/noauth`), `buildLegPayload` (:46-60), authFetch POST to `/api/tickets/leg`. Server (`mlb_hr_engine_v4/api/main.py:200-234` → `cache.py:151-206`): null ticket_id → inserts `tickets` row (`status='building'`, `user_id` stamped), then inserts `legs` row (frozen engine snapshot: model_prob, tier, model_tier_rank, engine_generated_at; migration `supabase/migrations/003_tickets_legs.sql`, calibration fields in 005). Not mock.

### What the FD buttons do today (REAL navigation, NOT a deep link)
`full-slate-matrix.js:263-295` (same pattern in strat/leaderboard files): build `https://sportsbook.fanduel.com/search?q=<encoded name>` (fallback `baseball/mlb?tab=player-home-runs`), copy name to clipboard, `window.open(url, "_blank", "noopener")` synchronously inside the click handler (popup-safe), show toast. No bet pre-fill, no odds, no market ID. Ticket overlay uses plain `<a href>` to the static baseball page.

### Slip lifecycle — exists vs missing
| Op | Status |
|----|--------|
| Create | ✅ implicit (first addLeg with null ticket_id, cache.py:174-184) |
| Add leg | ✅ `POST /api/tickets/leg` |
| View | ✅ SLIP·N chip + overlay host (`slip-btn.js`), overlay (`ticket-command.js`) — legs real, analytics SAMPLE |
| Remove leg | ⚠️ client-only; `legs.removed` column never written → confirm-count bug |
| Confirm/submit | ✅ `POST /api/tickets/complete` (main.py:237-245, cache.py:209-247) — ownership check, `fd_deployed=true`, `status='pending'`, stake, num_legs |
| Close + start new | ❌ no client `resetSlip()`; after submit the stale ticketId keeps receiving legs (server does NOT reject legs on completed tickets — also worth a server guard) |
| Rehydrate on reload | ❌ no ticket read endpoint |
| Settle | ❌ columns only (migration 005: "No settlement logic is built here") |

### Auth
✅ Built: Supabase JS client + email/password sign-in/up, invite-code beta gating (`auth.js:1-22, 249-334`), `authFetch` attaches JWT; ticket endpoints `Depends(require_auth)`; `tickets.user_id` stamped (migration 004, main.py:198 note: "NOT NULL + RLS deferred to Phase 3"). Per-user persistence is server-side real; client slip is session-memory only.

---

## 3. Design

### 3.1 Picker component — `destination-picker.js` (new bundle)
- **One shared component, one interception point.** Extend `slip-state.js` with `window.__hrSlip.requestAdd(row, anchorEl)` — opens the picker; the picker's option handlers call the existing `addLeg(row)` / FD-open / submit primitives. Then change each of the 8 surfaces' handler from `addLeg(...)` → `requestAdd(...)` (mechanical, one line each; the normalized-row shape they already build is exactly what the picker needs). The FSM tier-cell "+ FD" buttons and leaderboard "FD" links should ALSO route to `requestAdd` so FD-only paths gain slip options — otherwise consistency fails.
- **Render:** body-level portal modal (same pattern as `TicketCommandSlip` / `slip-overlay-root` in slip-btn.js:101-105), centered compact card (~360px), tactical HUD styling: `--bg-raised`, 1px `--border-2`, Barlow Condensed uppercase labels, green/blue accent rails matching `STRAT_SLIP_COLORS`. Header: player name + tier badge + "SELECT DESTINATION". Esc/backdrop-click closes = cancel (no action). Mobile: bottom sheet.
- **Popup-blocker rule (critical):** any option that opens FanDuel must call `window.open(fdUrl, "_blank", "noopener")` **synchronously inside the option button's click handler**, BEFORE any `await`. The picker click is itself a user gesture, so this is safe; awaiting the leg POST first would get the tab blocked. Pattern: open FD → then fire async slip write → reflect status in the store as today.
- **Auth gating:** Options 2–4 need JWT. If signed out, show those options with the existing amber `noauth` treatment and route to the auth widget (same behavior as slip-state.js:72-76). Option 1 (FD only) works signed-out.

### 3.2 The four options
1. **FD ONLY** — `fsmOpenFanDuelSearch`-equivalent (search URL + clipboard + toast). No slip write. ✅ buildable now. Label honestly: "Opens FanDuel search — place manually."
2. **ADD TO SLIP ONLY** — exactly today's `addLeg(row)`. Close picker; surface's slip button shows loading→added via existing `cardStatus`. ✅ buildable now.
3. **FD + ADD TO SLIP** — open FD synchronously, then `addLeg(row)`. ✅ buildable now.
4. **FD + CONFIRM SLIP + START NEW SLIP (seed with this player)** — sequence:
   a. open FD synchronously;
   b. `POST /api/tickets/complete` for current `ticketId` (confirm = today's semantics: `fd_deployed=true`, `status='pending'` — "operator says this parlay went to FD"; settlement stays out of scope);
   c. new store op `resetSlip()` — null ticketId, clear legs/cardStatus (keep it: clearing cardStatus re-enables '+' on previously-added players, correct for a fresh slip);
   d. `addLeg(row)` — null ticket_id opens the new ticket server-side, seeded with this player.
   ⚠️ **Blocked until two fixes land:** (i) server-side leg removal (else confirmed num_legs can include client-removed legs); (ii) ideally a stake prompt or documented "stake=null on quick-confirm" decision — `/api/tickets/complete` accepts null stake, so quick-confirm without a stake input is legal but loses stake capture. Recommended: inline stake mini-input on Option 4's confirm step, defaulting to last-used.
   Guard rails: disable Option 4 when `legs.length === 0` (nothing to confirm — degrade to Option 3); if the complete POST fails, do NOT reset — surface error and leave slip intact.

### 3.3 State model additions (slip-state.js)
- `resetSlip()` — clears ticketId/legs/cardStatus, notify.
- `removeLeg(n)` → also `POST /api/tickets/leg/remove` (new endpoint setting `legs.removed=true`) — closes the confirm-count integrity gap.
- Optional Phase-3: `GET /api/tickets/current` for reload rehydration (out of scope for picker MVP, but note it: Option 4's "confirm" is more trustworthy when the slip can't silently diverge from server state).

### 3.4 Honesty concerns
The picker multiplies entry points into an overlay whose grade/combined-prob/payout are `SAMPLE`. Mitigations: (1) keep SAMPLE tags (already present, ticket-command.js:22-24); (2) Option 4's confirm toast must state only what's true — "Ticket marked deployed in Supabase (N legs, $X stake)" — never imply graded/settled; (3) do not add any payout/grade text to the picker itself; per-leg HR prob/tier (real) only.

---

## 4. Build order (dependency-driven)

**Phase A — integrity prerequisites (backend + store):**
1. `POST /api/tickets/leg/remove` (+ wire `removeLeg`); server guard rejecting `add_leg` on non-`building` tickets.
2. `resetSlip()` in slip-state.js.

**Phase B — picker MVP (Options 1–3):**
3. `destination-picker.js` component + `requestAdd()` in slip-state.js; load in index.html after slip-state.js, before surface bundles that use it (script order: index.html:6110-6120).
4. Migrate all 8 surfaces' add handlers + the FSM/leaderboard/strategy FD-only actions to `requestAdd`.

**Phase C — Option 4:**
5. Confirm-and-new flow with stake mini-input, error-safe (no reset on failed complete), empty-slip degrade.

**Phase D (later, separate missions):** ticket rehydration endpoint; settlement job (`legs.hr_result`); real market odds capture.

Doctrine notes: tickets/legs are WRITE-SEPARATE capture-layer (003 header) — picker never touches MAIN/JIG scoring. `board` tagging ('main'/'jig') must pass through unchanged. Streamlit surface unaffected.

---

## 5. First implementation prompt (for the executing session)

> Implement Phase A + B of `wiki/roadmap/destination-picker-spec.md` (destination picker for slip/FD adds). Read the spec first; it has all file:line anchors.
> Phase A: (1) add `POST /api/tickets/leg/remove` to `mlb_hr_engine_v4/api/main.py` + `cache.py` (set `legs.removed=true`, ownership-checked like complete_ticket) and call it from `removeLeg` in `frontend/assets/js/slip-state.js`; (2) add a guard in `cache.add_leg` rejecting legs on tickets whose status ≠ 'building'; (3) add `resetSlip()` to slip-state.js.
> Phase B: create `frontend/assets/js/destination-picker.js` (portal modal, tactical HUD styling per spec §3.1, Options 1–3 wired to existing primitives, FD `window.open` synchronous in the option click handler before any await, noauth gating per spec) and `window.__hrSlip.requestAdd(row)`; add the script tag to `frontend/index.html` between slip-state.js and hr-threat-zone.js; migrate all 8 surface add handlers listed in spec §2 plus the FSM tier-cell "+ FD" button, leaderboard FD link, and strategy-rail card click to `requestAdd`. Do NOT build Option 4 yet (render it disabled with title "requires slip confirm flow — Phase C"). Do not touch MAIN/JIG scoring, config.py, or Streamlit. Validate by serving `frontend/` locally and exercising each surface. Do not commit without operator authorization.

# Cross-Engine Command Surface Doctrine

**Owner:** Claude (tactical workflow doctrine, operational hierarchy, cross-engine continuity)
**Codex scope:** routing and state bridges only — no engine identity changes without Claude review

---

## A. ENGINE IDENTITIES

Each engine has a defined operational identity. These identities are not interchangeable.
They are complementary stages in a single operator workflow.

### MAIN — Quantitative Market-Aware Intelligence
**Flow:** `SCAN → QUALIFY → DEPLOY`
**Primary signal:** EV% + Edge% (market-aware, calibrated probability)
**Operator action:** Identify market inefficiencies. Rank by model confidence. Move qualified picks to tracker.
**Hero metric:** EV%
**Characteristic question:** "Which picks does the market undervalue?"
**Secondary subtitle:** "Quantitative Market-Aware Intelligence · EV / Edge Ranked · Statcast Calibrated"

### JIG — Tactical Matchup Intelligence
**Flow:** `MATCHUP → CONFIRM → EXPLOIT`
**Primary signal:** HVY modifier + pitch mix context
**Operator action:** Validate exploit conditions. Confirm pitch mix vulnerability. Surface tactical mismatches.
**Hero metric:** HVY modifier
**Characteristic question:** "Which matchups have structural exploit conditions today?"
**Secondary subtitle:** "Tactical Matchup Intelligence · Pitch Mix Driven · Exploit Confirmation"

### FULL SLATE — Battlefield Overview
**Flow:** `SCAN FIELD → ISOLATE DANGER → ESCALATE TARGETS`
**Primary signal:** Composite score + barrel tier across full player universe
**Operator action:** Broad coverage before deployment. Identify hidden escalations. Confirm no missed targets.
**Hero metric:** Composite score
**Characteristic question:** "What am I missing across the full slate?"

---

## B. CROSS-ENGINE TRANSITIONS

Transitions between engines are not page navigations. They are investigation continuations.
Operator context must persist across transitions unless explicitly cleared.

### Context that always persists
- Active game selection (selected game_pk remains highlighted in destination engine)
- Selected player (if player was in focus, destination engine opens with that player visible)
- Escalation history (tier assignments don't reset on engine switch)
- Active suppression flags (a suppressed pick stays suppressed across engines)
- Deployment queue contents (Zone 3 sidebar always current regardless of engine)

### Context that adapts
- Sort order: each engine applies its own primary sort (MAIN by EV, JIG by HVY, Full Slate by composite)
- Filter state: MAIN TCC and JIG TCC are independent; switching engines does not carry TCC state
- Top Escalations (Zone 2 sidebar): re-ranks per engine's primary signal

### Context that resets
- Pagination position (each engine starts at page 1)
- Lazy-load states for pitch mix expanders (each engine's lazy gates are independent)
- Selected tab within engine (engine opens at default tab)

---

## C. ESCALATION JUMP RULES

Escalation jumps are explicit operator-initiated context transitions with defined payload.
They are not hyperlinks. They carry investigation state.

### MAIN → JIG deep investigation
**Trigger:** Operator clicks "→ VIEW MATCHUP" on a MAIN card, or selects JIG from breadcrumb while a player is in focus.
**Payload:** player_id, game_pk, active tier, current EV%, current Edge%
**JIG behavior:** Opens with that player's HVY card pre-expanded; pitch mix context auto-loaded.
**Breadcrumb:** `MAIN › [Player Name]` visible in JIG header area.

### Full Slate → deployment panel
**Trigger:** Operator clicks deploy action from Full Slate view.
**Payload:** player_id, game_pk, model_prob, ev_pct, edge_pct, odds
**Behavior:** Deployment panel opens with player pre-filled. Does not navigate away from Full Slate — opens modal or sidebar expand.
**Breadcrumb:** `FULL SLATE › [Player Name] › DEPLOY`

### JIG exploit → escalation queue
**Trigger:** Operator marks a JIG matchup as "confirmed exploit."
**Payload:** player_id, hvy_modifier, pitch_rows, game_pk
**Behavior:** Pick escalated to PRIORITY tier in Live Intelligence Feed. Operator returns to JIG view.
**Breadcrumb:** No navigation — escalation fires as a feed event, not a page transition.

### Deployment rejection → tactical reevaluation
**Trigger:** Deployment panel validation fails (EV below floor, odds unavailable, etc.)
**Payload:** player_id, rejection_reason
**Behavior:** Feed event fires (PRIORITY: `DEPLOYMENT_REJECTED`). Player card in MAIN gets rejection badge (dim, not deleted). Sidebar Zone 5 updates.
**Operator path:** Rejection does not auto-navigate. Operator reviews feed event and decides whether to re-investigate via JIG.

---

## D. CONTEXT RETENTION

### Selected game persistence
When operator has a game selected (game_pk in focus), switching engine preserves that game as the default scroll-to position in the destination engine.
If destination engine has no data for that game, game context silently drops (no error).

### Selected player persistence
When operator has a player in focus (player_id highlighted or card expanded), switching engine:
- Scrolls destination engine to that player's card if visible
- Opens that player's pitch mix expander if lazy gate not yet loaded
- Does NOT force-highlight if player is outside the active filter set — player appears at natural position

### Escalation persistence
Tier assignments (S/A/B/C/GOAT/ELITE/POWER/SOLID) do not change on engine switch.
JIG HVY grade and MAIN EV grade are separate dimensions — both visible in either engine's card.

### Trust-state persistence
Suppression flags survive engine switches.
If suppression is lifted in JIG (e.g., operator overrides), that state is reflected in MAIN card on next render.

### Deployment queue persistence
Queue is session-scoped, not engine-scoped.
A pick deployed from JIG appears in Zone 3 immediately.
A pick logged from MAIN is visible in Full Slate Portfolio tab and JIG sidebar.

---

## E. OPERATOR NAVIGATION RHYTHM

The platform must feel like one continuous investigation, not three separate apps.

**Intended flow for a typical session:**
1. Open MAIN → scan EV-ranked slate → identify top candidates
2. Jump to JIG → confirm pitch mix exploit for top candidates
3. Return to MAIN → deploy confirmed picks to tracker
4. Check Full Slate → confirm no missed barrel spikes in remaining universe
5. Review sidebar Zone 2 → verify top escalations are already in queue

**Navigation should never require:**
- Re-entering a player name
- Re-selecting a game after switching engines
- Re-loading pitch context that was already loaded this session
- Re-applying the same filter set in both engines

**The system maintains the operator's investigative momentum.**
Switching engines is a zoom-in or zoom-out, not a reset.

---

## F. COMMAND STRIP DOCTRINE

The command strip is the persistent top-of-screen control surface that spans all engine views.

### Persistent top controls
- Engine switcher: MAIN | JIG | FULL SLATE (active engine highlighted)
- Data load trigger: "Load / Refresh" button with last-load timestamp
- Slate status pill: 🟢 CONFIRMED / 🟡 MIXED / 🔵 PROJECTED
- Feed alert badge: active CRITICAL/PRIORITY count (from Live Intelligence Feed)
- Deployment queue badge: count of queued picks

### Escalation jump shortcuts
- From command strip: clicking the feed alert badge jumps to Live Intelligence Feed view
- From command strip: clicking deployment queue badge opens Zone 3 sidebar expand
- These are the only command strip jump shortcuts — not a full navigation menu

### Engine switching behavior
Switching engines via command strip:
1. Preserves active player/game context (per Section D)
2. Does NOT reset the command strip state
3. Engine TCC filters remain in their last-used state (not reset to defaults)
4. Does NOT trigger a data reload — operator must explicitly reload if desired

### Active-context indicators
Command strip shows:
- Active engine name (highlighted)
- If a player is "in focus": compact name badge next to engine name
- If investigation breadcrumb exists: breadcrumb trail (truncated to 2 levels)

Example: `MAIN › FULL SLATE › Judge` (operator arrived at Full Slate while investigating Judge from MAIN)

---

## G. FORBIDDEN CROSS-ENGINE PATTERNS

- **Context wipe on navigation:** Never reset player selection, game selection, or escalation state on engine switch.
- **Separate disconnected app feel:** If switching engines requires the operator to rebuild their mental model from scratch, the implementation is wrong.
- **Competing primary signals:** MAIN hero metric is EV. JIG hero metric is HVY. Neither engine should promote the other's primary signal to hero position.
- **Filter bleed:** MAIN TCC filters must never apply to JIG views and vice versa. Shared filters (if any) require explicit cross-engine flag design, not implicit inheritance.
- **Silent context drops:** If a player in focus cannot be found in the destination engine, the system shows a brief indicator ("Judge not in current filter set") rather than silently losing context.
- **Forced navigation:** Escalation jumps from the feed must offer navigation, not force it. Operator clicks into a jump; the system does not auto-navigate mid-investigation.

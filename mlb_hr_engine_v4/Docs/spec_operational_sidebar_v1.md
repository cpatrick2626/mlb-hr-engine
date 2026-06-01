# Operational Sidebar — Persistence Doctrine v1

**Owner:** Claude (tactical workflow doctrine, operational hierarchy)
**Codex scope:** shell implementation only — no zone changes without Claude review

---

## A. SIDEBAR PURPOSE

The operational sidebar is persistent battlefield context. It is not navigation. It is not decoration.

The sidebar answers three questions without the operator asking:
1. What is the live state of today's slate?
2. What needs my attention right now?
3. Where am I in the deployment workflow?

The sidebar persists across all engine views. Its content adapts to engine context. Its structure does not change.

---

## B. SIDEBAR ZONES

Zones listed top-to-bottom. Order is fixed. Content within each zone updates dynamically.

### Zone 1 — Live Slate Summary
What: Compact game-count, confirmation rate, HR environment composite, time to first pitch.
Behavior: Updates on every data load. Pill indicators for confirmation rate (🟢/🟡/🔵 from Session 34 doctrine).
Size: 3-4 lines max. No expansion.

### Zone 2 — Top Escalations
What: Top 3 escalated picks by composite score. Name, tier badge, model%, EV%.
Behavior: Updates on every slate load. Clicking a pick jumps to player context.
Size: 3 compact rows. "View all" link opens full escalation queue.

### Zone 3 — Deployment Queue
What: Picks saved via "Save for Results Tracking." Count, most recent addition, queue health indicator.
Behavior: Updates on pick save/clear. Shows void count if stale picks exist.
Size: 1-line summary + count pill. Expand to see full queue.

### Zone 4 — Tactical Alerts
What: Active PRIORITY and CRITICAL events from the Live Intelligence Feed.
Behavior: Mirrors top-of-feed active alerts. Max 3 items. "View feed" link for full queue.
Size: Compact 1-line per alert with tier badge. No duplicate — if feed is open, sidebar shows compressed version.

### Zone 5 — Suppression Warnings
What: Picks in deployment queue that now have active suppression signals.
Behavior: Refreshes on every data load. Highlights picks that have degraded since logging.
Size: Count indicator always visible. Expand for full list.

### Zone 6 — Live HR Environment
What: Composite environmental lift/drag today. Top 3 park-weather combos.
Behavior: Updates on weather data refresh. Bar visualization (green = lift, red = drag).
Size: Compact summary + top 3 labeled rows. No expansion needed.

### Zone 7 — Trust-State Indicators
What: Overall system health signals. Data freshness, Statcast age, odds API status, model load status.
Behavior: Always visible. Color-coded: 🟢 fresh / 🟡 aging / 🔴 stale.
Size: 4-5 icon-labeled rows. No expansion.

### Zone 8 — Quick Navigation
What: Jump buttons to MAIN, JIG, Full Slate, Performance, Advanced Strategies.
Behavior: Highlights current active engine. Compact button group.
Size: Single row of compact buttons. No labels beyond engine names.

### Zone 9 — Operator Shortlist
What: Operator-pinned players (manually added, persists for session). Quick access to tracked names.
Behavior: Add via player card "pin" action. Shows name + current tier + EV%.
Size: Max 5 entries. Overflow shows "+N more" with expand.

---

## C. PERSISTENCE RULES

### What remains pinned (survives navigation, never resets)
- Zone 3: Deployment Queue contents (session-scoped)
- Zone 9: Operator Shortlist (session-scoped)
- Zone 8: Quick Navigation (static)

### What updates dynamically (changes on slate load/refresh)
- Zone 1: Live Slate Summary
- Zone 2: Top Escalations
- Zone 4: Tactical Alerts
- Zone 5: Suppression Warnings
- Zone 6: Live HR Environment
- Zone 7: Trust-State Indicators

### What survives navigation
All zones persist across engine switches (MAIN → JIG → Full Slate).
Zone 2 and Zone 4 adapt content emphasis based on active engine:
- In JIG: Zone 2 prioritizes matchup-escalated picks
- In MAIN: Zone 2 prioritizes EV/Edge-escalated picks
- In Full Slate: Zone 2 shows broadest slate coverage

### What resets
- Zone 9: Operator Shortlist resets on app restart (not on navigation)
- Zone 4: Tactical Alerts clear on manual dismiss or expiry

### What follows engine context
Zone 2 (Top Escalations) and Zone 4 (Tactical Alerts) dynamically re-rank based on active engine's primary signal.

---

## D. ESCALATION SYNC RULES

### Sync with MAIN
Zone 2 reflects top 3 picks from `_tac_ranked` by composite score.
Zone 5 flags any deployment queue picks whose `ev_pct` has dropped below 0 since logging.

### Sync with JIG
Zone 2 re-sources from `scored_all` top by HVY modifier * composite score.
Zone 4 surfaces `PITCH_MIX_EXPLOIT_ALERT` events with priority.

### Sync with Full Slate
Zone 1 summary updates to reflect full slate breadth (all games, all confirmation counts).
Zone 2 remains as-is (doesn't change to a "full slate view" — Top Escalations always show elite targets).

### Sync with deployment panels
Zone 3 updates immediately on any "Save for Results Tracking" action.
Zone 5 runs suppression check on queue contents after every data load.

### Sync with investigation flow
When operator uses Jump navigation (see `escalation_jump_doctrine.md`), sidebar Zone 9 can receive auto-pin of the investigated player.

---

## E. MOBILE/TABLET ADAPTATION

### Collapse behavior
On screens < 768px wide: sidebar collapses to icon-rail on left edge.
Icon rail shows: Zone 7 status dots, Zone 3 count badge, Zone 2 top tier badge, Zone 8 nav buttons.
Tap any icon → expands that zone only (drawer overlay, not full sidebar).

### Touch interactions
Zones expand/collapse on tap.
Zone 9 pins removable via swipe-left on entry.
Long-press on Zone 2 pick → jump to player context.

### Quick-access doctrine
On mobile: Zone 2 and Zone 8 always one tap away.
On mobile: Zone 3 count badge always visible in collapsed rail.

### Mobile escalation access
CRITICAL alerts force-expand Zone 4 regardless of collapsed state.
Mobile does not suppress CRITICAL — it overrides collapse.

---

## F. VISUAL LANGUAGE

### Density rhythm
Sidebar content is dense but not crowded. Each zone has 4px top padding separator.
Zone separators: 1px solid #1a1a2a.
No full-width horizontal dividers — subtle negative space only.

### Compact information strategy
No full sentences. Labels + values only.
Example: `Top Pick: Judge · S · 18.3% · EV +4.2%`
Not: `Aaron Judge is the top pick with a model probability of 18.3% and an EV of 4.2%.`

Font scale: 
- Zone labels: 9px, #555, uppercase letter-spacing
- Zone values: 11px, #aaa baseline, #ccc on active/highlight
- Badges/pills: 10px

### Restrained animation
Zone content updates: crossfade (200ms). No slide. No bounce.
Badge state changes: color transition (150ms). No pulse unless CRITICAL escalation.
No zone expands with animation — instant on click.

### Operational emphasis
EV% and barrel% always in accent color (#3b82f6 and #22c55e respectively).
Trust degradation always in warning color (#ef4444).
Neutral/informational in #888.

---

## G. FORBIDDEN PATTERNS

- **Giant static sidebars:** No sidebar taller than viewport. No unscrollable content blocks.
- **Ad-style widgets:** No sponsored content, promotional copy, or external links.
- **Decorative filler:** No background imagery, gradient banners, or purely aesthetic section headers.
- **Duplicated information:** If a metric is visible in the main panel, the sidebar shows only the delta or exception state — not the same full table repeated.
- **Giant unreadable queues:** Zone 3 deployment queue shows count + summary, never a 30-row table. Expand is a separate view.
- **Passive zones:** Every zone must provide either actionable signal or operational state. A zone showing nothing useful during active slate is replaced with the most relevant live zone.
- **Navigation override:** Sidebar does not control main panel routing. Zone 8 quick navigation fires engine switches — it does not hijack operator focus mid-investigation.

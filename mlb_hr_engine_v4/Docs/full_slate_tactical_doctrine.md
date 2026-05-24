# Full Slate Tactical Interaction Systems & Operator Workflow Doctrine
**Session 04 — Planning Document**
**Date: 2026-05-20**
**Status: Architecture / Planning Only — No Runtime Changes**

---

## Contents

1. Operator Workflow Architecture
2. Tactical Interaction Doctrine
3. Battlefield Information Persistence Map
4. Threat Cluster Visualization Doctrine
5. Alert & Notification Philosophy
6. Deployment Focus Mode Doctrine
7. Battlefield Timing & Rhythm Doctrine
8. Tactical Interruption-Handling Recommendations
9. Operator Fatigue Prevention Standards
10. Future Operational Enhancement Opportunities

---

---

# 1. Operator Workflow Architecture

## Philosophy

Full Slate is a tactical command operation, not a dashboard. The operator arrives with intent — reconnaissance, escalation review, or deployment — and the system should reinforce that intent rather than scatter attention. Each stage of the workflow has a clear purpose, clear entry, and clear exit.

---

## 1.1 First-Open Behavior

**Context:** Operator opens app cold. Slate may already be loaded (cached) or needs hydration.

**Ideal sequence:**

1. **Splash suppression** — no loading spinners, no status bars, no "fetching..." text visible at center stage. Peripheral status indicator only (corner badge: `LOADING` → `LIVE` → date stamp).
2. **Command Center renders immediately** from cache if available. Stale indicator shown in peripheral badge, not blocking center stage.
3. **Slate summary header resolves first** — game count, qualified bets count, top EV summary. These are the operator's first orientation.
4. **Player cards populate beneath** — ranked order, top picks visible without scroll on standard viewport.
5. **Side panels remain collapsed** — no auto-expanded panels, no auto-opened modals. Operator controls expansion.
6. **Status confirmation** — once data confirmed live, peripheral badge flips to `LIVE [HH:MM]`. No announcement, no toast, no pop-up.

**Failure state:** If data unavailable, Command Center renders a single centered status line: `Slate unavailable — [reason]`. No error stack. No blank expanders. No spinners looping in empty containers.

---

## 1.2 Rapid Recon Flow

**Context:** Operator does a fast scan of the slate. Goal: identify today's top 3–5 plays in under 60 seconds.

**Expected path:**

1. Eyes land on Command Center headline metrics: total qualified, top EV, top edge, live game count.
2. Scan top 4–6 ranked player cards — name, team, prob, EV, edge, bet size.
3. Note any escalation badges (⚡ ESCALATION markers) without needing to expand.
4. Check weather threat indicator (persistent corner panel) — wind/temp flag if present.
5. Check pitcher status badges on top cards — any late changes flagged inline.
6. Decision: proceed to deployment, drill deeper, or monitor.

**Recon should complete in one viewport** without scroll on standard display. No tab-switching required for top-level intelligence.

---

## 1.3 Escalation Review Flow

**Context:** One or more escalation signals active — pitcher change, lineup scratch, weather shift, line movement.

**Expected path:**

1. Escalation badge visible on affected player card(s) without expansion.
2. Operator clicks badge or card header — single expand reveals escalation detail panel.
3. Escalation detail shows: trigger type, affected factor, direction of impact (positive / negative), confidence delta.
4. Operator can acknowledge escalation inline — single click "ACK" clears the badge for that card without affecting other cards.
5. If escalation is systemic (weather affecting all games), a single top-of-slate system alert appears — one dismissible banner, not per-card flooding.
6. After acknowledgment, card returns to standard state. Acknowledged escalations logged to session, visible in Diagnostics tab if needed.

---

## 1.4 Tactical Drill-Down Behavior

**Context:** Operator wants deeper intelligence on a specific player before deployment.

**Expected path:**

1. Expand player card → Intelligence Panel opens in-place (no navigation away from slate).
2. Intelligence Panel presents: probability breakdown, Statcast factors, pitch matchup signal, platoon split, park interaction.
3. Operator can expand Arsenal Analysis from within Intelligence Panel — shows pitcher pitch mix and matchup delta. No full-page redirect.
4. HVY Modifier shown as collapsed secondary panel within Intelligence Panel — expand only on demand.
5. Operator can launch Deployment Focus Mode directly from Intelligence Panel with one click.
6. Back-to-slate exits Intelligence Panel cleanly — slate scroll position preserved.

**Constraint:** Drill-down must not replace the slate. Intelligence Panel is always a child of the slate, not a replacement page.

---

## 1.5 Deployment Confirmation Flow

**Context:** Operator has identified a play and is ready to log/commit.

**Expected path:**

1. Deployment Focus Mode activated (one click from card or Intelligence Panel).
2. Cognitive load collapses: only deployment-critical fields visible (see Section 6).
3. Operator reviews: player, prob, EV, edge, recommended bet size, sportsbook, odds.
4. Confirms or adjusts bet amount — single numeric input.
5. Confirms sportsbook — dropdown or fast-select.
6. Single confirmation action ("LOG BET" or equivalent) — no multi-step wizard.
7. Success state: brief peripheral flash (not modal), card marked DEPLOYED in slate view.
8. Operator returned to slate automatically after 1.5s or on any keypress.

**Failure state:** If logging fails, brief peripheral error badge on that card. Slate not disrupted.

---

## 1.6 Return-to-Slate Behavior

**Context:** Operator has been in drill-down, deployment, or external view and returns to main slate.

**Expected behavior:**

- Slate scroll position preserved from before drill-down.
- No forced re-render of full slate on return. Cards resume their last known state.
- Any changes during absence (escalation, lineup scratch) shown as delta badges on affected cards only.
- No "welcome back" messaging. No reload prompts unless data is genuinely stale (>15 min by default).

---

## 1.7 Live Game Interruption Handling

**Context:** Game has started mid-session. Inning status updates, in-game lineup changes, pitcher changes mid-game.

**Expected behavior:**

- In-game picks marked with inning status badge (peripheral — not blocking card content).
- Locked picks (first pitch passed) dimmed slightly, badge reads `IN PLAY` — still visible but visually subordinated to pre-game picks.
- Operator can still view in-play card for tracking — not hidden, not deleted.
- New escalation from in-game events (bullpen change, injury) surfaces as a targeted escalation badge on that card only.
- No automatic removal of in-play cards from slate view.

---

---

# 2. Tactical Interaction Doctrine

## Philosophy

Interactions should feel precise and intentional. Nothing moves without reason. Nothing demands attention without justification. The interface is a tool, not a performance.

---

## 2.1 Hover Behavior

**Should:**
- Reveal secondary information that doesn't need permanent display (factor breakdowns, tooltip-level context).
- Highlight row or card with a subtle border brightening (1px → 1.5px, opacity shift ~10%).
- Surface a single-line quick-stat overlay at cursor position for ranked player rows.

**Should not:**
- Trigger data fetches on hover.
- Expand full panels on hover.
- Animate large elements into view on hover.
- Shift layout on hover (no layout reflow from hover).

**Hover pacing:** Visual response within one frame (<16ms). No delays. No easing on hover-in that exceeds 80ms.

---

## 2.2 Expansion Behavior

**Trigger:** Click on card header, expand chevron, or explicit "View Details" action.

**Behavior:**
- Panel expands from top down, consistent direction always.
- Content appears immediately — no spinner within the expanding panel.
- Expansion does not collapse other expanded cards automatically (operator controls collapse).
- Exception: Deployment Focus Mode collapse (see Section 6) — intentional full-slate collapse.

**Animation:** Single easing expansion, 120–150ms, ease-out curve. No bouncing. No spring physics.

---

## 2.3 Tactical Reveal Timing

**Principle:** Information reveals should feel like tactical briefing, not data flooding.

**Hierarchy:**
1. Headline metrics — always visible (never revealed, always present)
2. Card-level summary — visible on load (prob, EV, edge, bet size)
3. Factor breakdown — revealed on expand
4. Statcast detail — revealed on secondary expand within Intelligence Panel
5. Arsenal/pitch mix — revealed on explicit Arsenal Analysis expand
6. HVY modifier detail — revealed on explicit HVY expand (deepest level)

**Rule:** Each level of reveal requires explicit operator action. Nothing auto-reveals past Level 2.

---

## 2.4 Escalation Acknowledgment

**Pattern:**
- Badge appears on card without expand required.
- Single click on badge or "ACK" button acknowledges.
- Acknowledgment stored in session (not persisted to disk — ephemeral per session).
- Badge disappears after ACK. Card returns to standard state.
- New escalation after ACK on same card: badge re-appears with timestamp delta.

**Visual language:**
- Active escalation: amber accent (`#f59e0b`), solid border flash.
- Acknowledged: badge removed. No persistent "ack'd" state shown inline.
- Critical escalation (pitcher scratch, DNP): red accent (`#ef4444`), card border highlighted.

---

## 2.5 Deployment Focus Mode

See Section 6 for full doctrine. Interaction entry point: single CTA button on card or Intelligence Panel.

---

## 2.6 Persistent Battlefield Indicators

These elements remain visible regardless of drill-down depth:

| Indicator | Location | What it shows |
|---|---|---|
| Slate status badge | Top-right corner | LIVE / STALE + timestamp |
| Weather threat flag | Top-left corner | Wind/temp warning if active |
| Qualified count | Headline bar | Current filtered pick count |
| Active escalation count | Headline bar | # unacknowledged escalations |
| Deployment queue | Sticky bottom strip | Count of logged bets today |

These never disappear during navigation. They are the operator's ambient situational awareness.

---

## 2.7 Stack Investigation Behavior

**Context:** Operator wants to examine a team stack (multiple picks in same lineup).

**Expected path:**
1. Stack concentration badge on headline bar — click opens Stack Panel.
2. Stack Panel shows: all picks from same team, correlation factor (from `correlation.py`), N_eff contribution, combined HR prob, joint EV.
3. Stack Panel is a modal overlay over the slate — slate visible behind it at reduced opacity.
4. Operator can deploy from Stack Panel or return without action.
5. Stack Panel dismisses on backdrop click or explicit close.

---

## 2.8 What Should Animate

| Element | Animation |
|---|---|
| Card expansion | Height ease-out, 120–150ms |
| Escalation badge appear | Fade-in, 200ms |
| Escalation badge dismiss (ACK) | Fade-out, 150ms |
| Deployment Focus Mode enter | Cross-fade surrounding slate, 200ms |
| Deployment Focus Mode exit | Cross-fade restore, 200ms |
| Status badge LOADING→LIVE | Single pulse flash, then solid |
| Stack Panel open | Slide-in from right, 180ms |

## 2.9 What Should NEVER Animate

| Element | Reason |
|---|---|
| Data values (prob, EV, edge) | Would create visual noise on every refresh |
| Card order changes | Disorienting during operator scan |
| Headline metric updates | Operator needs stable reference during scan |
| Layout reflow | Any layout shift during active use is a failure |
| Loading spinners in content area | Suggests incompleteness — use peripheral status only |
| Auto-scrolling | Operator owns scroll position |
| Hover-triggered panel expansions | Accidental trigger risk |

---

## 2.10 Interaction Pacing Philosophy

**Principle: deliberate speed.** The interface should respond instantly to explicit operator actions and ignore everything else.

- Explicit action (click, expand): immediate response, <16ms visual acknowledgment.
- Data refresh: background, no visual disruption until complete.
- Escalation surfacing: targeted badge only, no full-page alert.
- Operator-initiated refresh: brief peripheral LOADING badge, not a full-page spinner.

The operator should never feel like they're waiting for the interface. The interface waits for the operator.

---

---

# 3. Battlefield Information Persistence Map

## Philosophy

As the operator moves deeper into investigation (slate → game → player → arsenal → deployment), they must never lose tactical orientation. Core situational context is always visible regardless of drill-down depth.

---

## 3.1 Persistence Tiers

### Tier 0 — Always Persistent (never hidden at any depth)

| Information | Where shown |
|---|---|
| Slate date | Headline bar |
| LIVE / STALE status | Corner badge |
| Qualified pick count | Headline bar |
| Active escalation count | Headline bar |
| Weather threat summary | Corner flag (if active) |
| Deployment count today | Sticky bottom strip |

### Tier 1 — Persistent within Slate View

| Information | Condition |
|---|---|
| All ranked player cards (summary level) | While in Command Center |
| Game-level inning status badges | While in Command Center |
| Top-3 picks by EV | Always visible without scroll |
| Stack concentration badge | If stack N_eff < 0.7 of total |
| Pitcher change flag | On affected cards |

### Tier 2 — Persistent within Expanded Card

| Information | Condition |
|---|---|
| Player name + team | Card header — always |
| Model prob + EV + edge | Card header — always |
| Bet size recommendation | Card header — always |
| Escalation badge | If active |
| Statcast power summary | First visible sub-row |
| Card-level deployment CTA | Always within expanded card |

### Tier 3 — Available in Intelligence Panel

Operator has expanded to Intelligence Panel. The following persist:

| Information | |
|---|---|
| Full factor breakdown | Probability components |
| Statcast profile | Barrel, exit velo, FB%, xSLG |
| Platoon split | vs LHP / vs RHP |
| Park factor | Stadium HR factor |
| Pitcher factor | Calibrated suppressor level |
| Calibration note | Elite vs standard Platt tier |
| HVY modifier score | Matchup signal (display-only) |

### Tier 4 — Available in Arsenal Analysis Panel

| Information | |
|---|---|
| Pitcher pitch mix | % by pitch type |
| Matchup delta | Arsenal SLG vs batter profile |
| K% and HR/9 | Pitcher control metrics |
| Career H2H note | If available |

### Tier 5 — Deployment Focus Mode (see Section 6)

Intentional information collapse. Only deployment-critical fields visible.

---

## 3.2 State Persistence During Navigation

| Navigation action | State preserved |
|---|---|
| Tab switch within app | Slate scroll position, expanded cards |
| Route switch (MAIN → JIG) | Escalation acknowledgments, deployment count |
| Intelligence Panel open/close | Slate scroll position |
| Arsenal Panel open/close | Intelligence Panel scroll position |
| Deployment Focus enter/exit | All prior states restored on exit |
| App refresh (data) | Expanded cards close — intentional (fresh slate) |

**Hard rule:** Operator-acknowledged escalations persist until app refresh. Never re-surface an ACK'd escalation from the same data payload.

---

---

# 4. Threat Cluster Visualization Doctrine

## Philosophy

Threat clusters communicate collective risk or opportunity across multiple picks. They should read at a glance, require no legend, and never add visual weight to an already-loaded slate.

---

## 4.1 Cluster Types

### 4.1.1 Multi-Player HR Clusters (same game)

**Signal:** 3+ picks from same game.
**Visual:** Thin left-border accent color shared across all cards from that game. Color by game, cycling through a small palette (4–5 muted accent colors). No icons, no labels needed — shared border color is enough.
**Where shown:** Card left border (2px colored stripe, muted — not neon).
**Operator interaction:** Hovering any card in cluster highlights all same-game cards with border brightening.

### 4.1.2 Stack Concentration

**Signal:** 2+ picks from same batting order in same lineup (correlated picks).
**Visual:** Stack badge on headline bar (`STACK: NYY ×3`). Badge is compact, muted amber — not alarming. Clicking opens Stack Panel (see Section 2.7).
**Cards in stack:** No additional card-level marking needed. Stack Panel reveals which cards are in the stack.

### 4.1.3 Vulnerable Pitcher Zones

**Signal:** Same pitcher being targeted by 2+ picks.
**Visual:** Pitcher name row in card shows a subtle "targeted" indicator (small repeated pitcher icon, e.g. `× 3 picks`). This is within the card Intelligence Panel, not on the card surface.
**No map or overlay.** Pitcher targeting is text-only, not graphical.

### 4.1.4 Environmental Amplification Clusters

**Signal:** Weather factor >1.05 active AND multiple picks in that stadium.
**Visual:** Shared weather badge on affected cards — small icon + direction (e.g., `↑ Wind CFout`). Same icon on all affected cards, not repeated in header area.
**Peripheral:** Weather threat corner flag activates if ≥3 picks in same weather-amplified game.

### 4.1.5 Bullpen Danger Escalation

**Signal:** Starter flagged as likely short outing OR bullpen usage escalating (pitch count context if available).
**Visual:** Escalation badge on card reads `BULLPEN RISK` in amber. Not a separate cluster visualization — inline on card.
**No additional overlay or panel.** Bullpen risk is an escalation badge, not a cluster visualization.

### 4.1.6 Momentum Acceleration

**Signal:** Model prob has moved favorably since last data load (line movement in operator's favor).
**Visual:** Small directional delta badge on card — `+1.2pp ↑` in muted green. Shown only when delta >0.5pp since last hydration.
**Never shown as a cluster** — momentum is per-player, not clustered.

---

## 4.2 Visualization Constraints

**No heatmaps.** No color-gradient overlays on slate backgrounds. No intensity maps.

**No spatial game maps.** No visual field layout, no stadium visualization.

**No overlapping badges.** Maximum 2 badges per card surface: (1) escalation/status, (2) cluster/momentum. If both present, escalation wins; momentum shown in Intelligence Panel only.

**Palette discipline:**
- Cluster game accent: 4–5 muted colors, low saturation (avoid red/green — those are reserved for EV polarity).
- Escalation: amber `#f59e0b` (warning), red `#ef4444` (critical).
- Positive momentum: muted green `#4ade80`.
- Negative delta: muted red `#f87171`.
- Neutral / informational: muted slate `#94a3b8`.

**Two-color rule:** Any single card should never show more than 2 distinct accent colors simultaneously.

---

---

# 5. Alert & Notification Philosophy

## Philosophy

Alerts are reserved for information that requires operator action or changes deployment decisions. Everything else is ambient context, not an alert.

---

## 5.1 Urgency Ladder

| Tier | Trigger | Presentation | Action Required |
|---|---|---|---|
| **CRITICAL** | Pitcher scratch / DNP confirmation | Red card border + modal banner | Explicit ACK |
| **HIGH** | Lineup change affecting top-5 pick | Amber escalation badge on card | Click to review |
| **MEDIUM** | Weather shift exceeding 5% factor change | Corner weather flag update | Passive (no ACK required) |
| **LOW** | Line movement >0.5pp in operator's favor | Momentum delta badge on card | No action required |
| **INFO** | Refresh complete, data timestamp update | Peripheral status badge flip | None |

---

## 5.2 Interruption Thresholds

**Interrupting operator** (pulling focus from current task) is only justified for:
- CRITICAL tier: pitcher scratch or confirmed DNP for a pick the operator has already logged.
- Extreme weather event (dome open/close unexpected, major wind shift mid-session).

Everything else is non-interrupting. Badges and peripheral indicators convey information without pulling focus.

**Modal interruptions:** Reserved for CRITICAL tier only. Modal blocks operator action until acknowledged. One modal at a time — never stack modals.

---

## 5.3 Escalation Triggers

| Event | Tier | Trigger condition |
|---|---|---|
| Pitcher scratch confirmed | CRITICAL | Pitcher ID changed post-load |
| Player listed as DNP/Scratched | CRITICAL | Player removed from lineup |
| Late lineup change | HIGH | Batting order shift affecting top-5 pick |
| Weather factor shift >5% | MEDIUM | Weather poll returns materially different conditions |
| Line movement favor >0.5pp | LOW | Model prob increase vs last hydration |
| Line movement against >1.0pp | MEDIUM | Model prob decrease vs last hydration (deployment risk) |
| Refresh complete | INFO | New hydration fingerprint detected |

---

## 5.4 Stale-Alert Expiration

- CRITICAL alerts: persist until explicit ACK. Do not auto-expire.
- HIGH alerts: auto-expire after 20 minutes if no new data confirms the trigger.
- MEDIUM alerts: auto-expire after 10 minutes.
- LOW alerts: auto-expire after 5 minutes or on next data refresh.
- INFO alerts: auto-expire after 3 minutes.

**Auto-expiration is silent.** No "alert dismissed" messaging. Badge simply disappears.

---

## 5.5 Operator Fatigue Prevention

**Escalation rate cap:** No more than 3 simultaneous escalation badges active across slate. If 4th trigger fires, queue it — surface when an existing badge is ACK'd or expires.

**De-duplication:** Same trigger type from same game within a 10-minute window: show one badge, not multiple.

**Quiet-state suppression:** If operator has been actively deploying (Deployment Focus Mode active), suppress all LOW and INFO alerts until exit. MEDIUM and above surface as corner badge only (not card badge).

**Daily rhythm:** In first 30 minutes of session (pre-game setup), allow full alert sensitivity. After games begin, reduce LOW alert frequency — momentum deltas only shown if >1.0pp, not 0.5pp.

---

## 5.6 Notification Persistence Rules

- No toast notifications. Toasts disappear before operator reads them and are not reviewable.
- No push notifications outside the app (browser notifications forbidden — too disruptive).
- All alert states are reviewable within the session in Diagnostics tab (last 20 alerts, timestamped).
- Escalation history visible in Diagnostics but never surfaced unprompted.

---

---

# 6. Deployment Focus Mode Doctrine

## Philosophy

When the operator is about to commit capital, cognitive load must collapse to the minimum necessary for a confident decision. Every non-essential element disappears. Every essential element is enlarged and clearly readable.

---

## 6.1 What Disappears in Deployment Focus Mode

| Element | Reason hidden |
|---|---|
| All other player cards | Prevent cross-pick distraction |
| Headline metric bar | Not relevant to this specific decision |
| Tab navigation | Prevent accidental navigation |
| Stack concentration badge | Macro view not needed during micro decision |
| Arsenal/HVY detail | Already surfaced in Intelligence Panel pre-deploy |
| Diagnostics indicators | Background system data |
| Weather corner flag | Already factored into model prob shown |
| Momentum delta badge | Already surfaced; displayed as static value only |

**Peripheral status badge (LIVE / STALE) remains.** Operator must know if data is fresh.

---

## 6.2 What Remains in Deployment Focus Mode

| Element | Why it stays |
|---|---|
| Player name + team + position | Identity confirmation |
| Model probability (calibrated) | Core confidence signal |
| EV% and Edge% | Bet justification |
| Recommended bet size (Kelly) | Decision input |
| Best odds + sportsbook | Where to execute |
| Implied probability (no-vig) | Market reference |
| One-line context note | "Elite barrel / good park / platoon ✓" |
| Bet amount input field | Operator adjustment |
| Sportsbook confirm field | Execution routing |
| LOG BET action | The decision |
| CANCEL / return link | Escape hatch |

**Total visible elements in Focus Mode: ≤12 items.** If the design exceeds 12 items, something must be cut.

---

## 6.3 Confidence Presentation

In Deployment Focus Mode, confidence is presented in a single compound statement, not scattered across multiple metrics:

```
Model: 18.4%  |  Edge: +5.2pp  |  EV: +7.1%  |  Barrel tier: ELITE
Bet: $42 @ +380 DraftKings
```

Single scan. No mental assembly required.

**Color coding in Focus Mode:**
- Model prob ≥15%: green `#4ade80`
- Model prob 10–15%: amber `#f59e0b`
- Model prob <10%: dimmed (rare in Focus Mode — filter should prevent this)
- EV positive: green
- EV negative: red (should not appear in Focus Mode — filter should prevent)

---

## 6.4 Distraction Reduction Rules

- Background slate visible at 20% opacity (creates spatial context without distraction).
- Focus panel centered, max-width 480px — readable on any viewport.
- No scrolling required within Focus Mode panel.
- No expandable sub-panels in Focus Mode — all context already visible at this depth.
- Only one pick in Focus Mode at a time. Sequential deployment: exit, re-enter per pick.

---

## 6.5 Tactical Clarity Standards

- Font sizes in Focus Mode: 20–25% larger than slate card equivalents.
- Bet amount input autofocused on entry — operator can immediately type adjustment.
- Keyboard-navigable: Tab through fields, Enter to confirm.
- ESC or CANCEL: immediate return to slate at last scroll position.
- After LOG BET: card in slate marked `DEPLOYED` (muted green badge). Focus Mode exits automatically.

---

---

# 7. Battlefield Timing & Rhythm Doctrine

## Philosophy

Full Slate should feel like a briefing room with a clear operational tempo, not a blinking trading terminal. Visual tempo is calm and deliberate. Updates are controlled. The operator sets the pace; the system follows.

---

## 7.1 Update Cadence Philosophy

| Refresh type | Target interval | Trigger |
|---|---|---|
| Data hydration | ~10–15 min | Operator-controlled or background auto |
| Escalation check | On data hydration | Tied to hydration, not independent poll |
| Status badge | Immediately on hydration complete | |
| Lineup check | On data hydration (no separate poll) | |
| Weather check | On data hydration | |

**No sub-minute polling.** Sub-minute visual changes are visually fatiguing and rarely meaningful for pre-game HR props.

**Operator-controlled refresh always available.** Background auto-refresh is a convenience, not a mandate.

---

## 7.2 Escalation Pacing

- New escalation badge: appears on next data hydration cycle, not immediately on event detection.
- Exception: CRITICAL tier (pitcher scratch) — if detectable within session, surface immediately. This is the only real-time exception.
- Escalation surfacing is batched with data refresh to prevent incremental badge accumulation during a single session.

---

## 7.3 Visual Tempo

**Principle: the slate should breathe, not pulse.**

- No blinking elements at any time (not even "LIVE" badge blinks).
- No pulsing indicators.
- No animated progress bars during refresh (peripheral status badge only).
- Card appearance on load: cards appear in ranked order, top-to-bottom. No staggered fade-in cascade — loads instantly or not at all. Partial renders are worse than waiting.

---

## 7.4 Scan Rhythm Timing

The ideal operator scan cycle:

1. **0–10s:** Headline metrics. Top picks in viewport. Escalation badges noted.
2. **10–30s:** Card-level EV/edge scan. Stack badge check. Weather flag check.
3. **30–60s:** Expand 2–3 highest-ranked picks. Review factor breakdowns.
4. **60–120s:** Drill into Arsenal Analysis for 1–2 picks. HVY modifier review.
5. **120s+:** Deployment decision.

**Design for 120-second decision cycles.** If the operator cannot make a confident deployment decision within 2 minutes of opening a pick, the interface is failing.

---

## 7.5 Interaction Speed Expectations

| Action | Expected latency |
|---|---|
| Card expand | <16ms visual, <100ms content |
| Intelligence Panel open | <200ms (pre-computed content) |
| Arsenal Analysis open | <300ms (may require one computation) |
| Deployment Focus Mode enter | <200ms (cross-fade) |
| Data refresh (background) | 5–30s (acceptable; not blocking) |
| LOG BET action | <500ms for write confirmation |
| Escalation ACK | <16ms visual |

**Hard rule:** No operator-visible action should take >500ms. If computation takes longer, show peripheral spinner — never block the center stage.

---

## 7.6 Operator Recovery Spacing

After major actions, the system should give the operator a brief cognitive pause:

- After LOG BET: 1.5s before auto-exit from Focus Mode (allows confirmation reading).
- After CRITICAL escalation appears: no auto-dismiss for ≥30s (operator needs time to process).
- After full slate refresh: new data visible immediately — no "reviewing..." intermediate state.

**No artificial loading delays.** Recovery spacing is about cognitive pacing, not simulating work.

---

---

# 8. Tactical Interruption-Handling Recommendations

## 8.1 Inning Change Interruption

**Situation:** Game enters new inning mid-session. Pick is still pre-AB.

**Handling:**
- Inning badge updates on card (peripheral — not blocking content).
- No interruption of active operator workflow.
- If first pitch has passed for player's expected AB: card dimmed, `IN PLAY` badge added.
- Operator not interrupted unless card was in Deployment Focus Mode (then: brief MEDIUM alert overlay, dismissible).

---

## 8.2 Pitcher Removal Mid-Game

**Situation:** Starting pitcher removed. Pick was against that starter.

**Handling:**
- CRITICAL escalation badge surfaces on card.
- If operator is in Deployment Focus Mode for that pick: modal interruption — "Pitcher change: [Name] replaced by [Bullpen]" with option to ACK or cancel deployment.
- If deployment already logged: CRITICAL badge on card, note in Diagnostics, no retroactive P&L adjustment.

---

## 8.3 Lineup Change Pre-Game

**Situation:** Late scratch or batting order change affects a pick.

**Handling:**
- HIGH escalation badge surfaces on affected card.
- Intelligence Panel for that card shows delta: "Listed: 3 → Now: 8" (batting order shift).
- Model prob re-evaluated on next hydration (not retroactively recalculated in real-time).
- Operator makes final judgment — system does not auto-remove picks.

---

## 8.4 Data Feed Interruption

**Situation:** MLB Stats API or Odds API returns error during background refresh.

**Handling:**
- STALE badge on peripheral status indicator.
- Last-good data remains displayed without modification.
- No error stack shown in content area.
- One-line peripheral note: `Refresh failed [HH:MM] — retrying`. Not blocking.
- Manual refresh button always available regardless of auto-refresh state.

---

## 8.5 Session Timeout / Browser Suspend

**Situation:** Operator leaves and returns after extended absence (>30 min). Streamlit session may have dropped.

**Handling:**
- App re-initializes cleanly on return. Slate reloads from cache where available.
- No confusing "session expired" messages — simply rehydrates and presents fresh slate.
- If cache is stale (>15 min), STALE badge shown. No forced refresh prompt.
- Prior escalation acknowledgments: not preserved (acceptable — they were session-specific).

---

---

# 9. Operator Fatigue Prevention Standards

## 9.1 Visual Load Budgeting

**Per-card visual budget:**
- Max 2 accent colors per card
- Max 2 badges on card surface
- Max 3 expandable sections (Summary → Intelligence → Arsenal)
- No badges in card body text — badge placement on header only

**Slate-level visual budget:**
- Max 3 colors in full visible viewport (excluding card content)
- Max 2 system-level persistent badges (status + escalation count)
- No persistent animations in viewport

---

## 9.2 Cognitive Load Reduction

**No operator decisions hidden in deep menus.** Every action reachable within 2 clicks from Command Center.

**No required reading before acting.** Deployment Focus Mode contains everything needed. No pre-modal information gates.

**Progressive disclosure enforced.** Information depth scales with operator intent:
- Scanning: card surface only
- Investigating: Intelligence Panel
- Validating: Arsenal Analysis
- Deciding: Deployment Focus Mode

---

## 9.3 Repetition Avoidance

**Same information shown in multiple places is fatigue-inducing.** Rules:
- Prob shown in card header only — not repeated in Intelligence Panel header.
- EV shown in card header only — calculated breakdown shown in Intelligence Panel body.
- Sportsbook odds shown in card header only — confirmation shown in Deployment Focus Mode.
- Weather factor shown as corner flag — not repeated on every card (only flagged on affected cards).

---

## 9.4 Quiet Hours Protocol

After 8pm local time (typical late-game window), if no picks with first-pitch remaining:

- Suppress LOW and INFO alerts entirely.
- Reduce background refresh cadence to 30 minutes.
- Status badge reads `LATE SLATE [HH:MM]` — communicates reduced monitoring mode.
- Operator can override and force refresh at any time.

---

## 9.5 Session Length Guidance (Non-Enforced — Advisory Only)

The system cannot enforce session length, but UX should accommodate:
- **Pre-game window (3h before first pitch):** Full alert sensitivity, standard refresh cadence.
- **First pitch to 3 hours in:** Standard mode with in-play dimming.
- **Late game (>4h into session):** Reduced visual tempo, quiet hour suppression active.

No forced logout. No session warnings. Advisory only.

---

---

# 10. Future Operational Enhancement Opportunities

## 10.1 Keyboard Command Layer (Near-term)

Define keyboard shortcuts for the 5–6 most common operator actions:

| Key | Action |
|---|---|
| `R` | Force refresh |
| `D` | Enter Deployment Focus Mode on highlighted card |
| `ESC` | Exit any expanded panel / Focus Mode |
| `J / K` | Navigate between cards (vim-style) |
| `A` | Acknowledge active escalation on current card |
| `S` | Open Stack Panel |

**Prerequisite:** Streamlit keyboard event handling via `st.components` or JS injection. Currently not implemented — planning only.

---

## 10.2 Operator Session State Persistence (Medium-term)

Persist across browser sessions:
- Today's logged bets (already in pick_tracker.csv — need surface)
- Escalation ACK state for same-day picks (session-only today — consider lightweight localStorage)
- Filter control positions (today reset on refresh — annoying for repeat operators)

**Approach:** lightweight `localStorage` via `st.components` JS bridge. No backend changes required.

---

## 10.3 Automated Deployment Queue (Medium-term)

Allow operator to queue multiple picks in one session, review queue as a whole, then submit all with one action.

- Queue shows: total exposure, N_eff (correlation), total Kelly exposure vs bankroll.
- Queue-level review is the Portfolio Optimizer output surfaced in UI.
- Builds on existing `portfolio/optimizer.py` — needs Streamlit wiring only.

---

## 10.4 Contextual Line Movement Overlay (Medium-term)

For each pick card, show a micro-sparkline of odds movement since opening line.

- Data source: `tracking/line_snapshots.py` (already implemented, Session 26).
- Visualization: 48px wide sparkline, 2px line, last 4–6 snapshots.
- Color: green if odds have shortened (sharper money in), red if odds have drifted out.
- Trigger: expand-only — not visible at card surface level.

**Prerequisite:** `line_snapshots.csv` must have multiple snapshots per pick per day. Current schema supports this — depends on `capture_closing_lines.py` being run at multiple intervals.

---

## 10.5 Multi-Day Slate View (Long-term)

For days with early-posted next-day lines, allow operator to view tomorrow's slate alongside today's.

- Tab-based: `TODAY` / `TOMORROW` — not mixed.
- Tomorrow slate clearly watermarked as EARLY LINES — lineups not confirmed.
- Today slate is always primary; tomorrow is research mode only (no deployment from tomorrow slate).

---

## 10.6 Calibration Health Widget (Near-term, Low Effort)

Persistent corner widget showing current calibration health status in 3 numbers:

```
CAL HEALTH
n=324 | bias=-0.26pp | status=STABLE
```

- Green if |bias|<3pp
- Amber if |bias|≥3pp and n≥50
- Red if |bias|≥5pp and n≥20

Pulled directly from `analyze_live_roi.py` output or live-computed from pick_tracker. Requires no model changes — display only.

---

## 10.7 Operator Onboarding Mode (Long-term)

First-run experience for new operators:

- Step-by-step overlay walkthrough of 5 key UI zones.
- Toggled via `?` key or Help button.
- Skippable after slide 1.
- Not shown again after completion (localStorage flag).

**Purpose:** The tactical UX is intentionally restrained, which means new operators may not discover key features. Onboarding mode bridges this without polluting the live operational experience.

---

## 10.8 Deployment Confirmation Receipt

After LOG BET:

- Downloadable single-pick receipt (text or JSON): player, odds, prob, EV, timestamp, sportsbook.
- Purpose: operator verification if disputes arise with sportsbook.
- Already partially available via pick_tracker.csv — need a formatted per-pick export.

---

## 10.9 Confidence Tier Visual Language Standardization

Formalize a visual tier system for pick confidence, usable across all card views:

| Tier | Barrel | Model Prob | Label | Visual |
|---|---|---|---|---|
| ELITE | ≥12% | ≥20% | ELITE | Gold left-border |
| PRIME | 10-12% | 15-20% | PRIME | Green left-border |
| QUALIFIED | 8-10% | 10-15% | QUAL | Teal left-border |
| STANDARD | 6-8% | 7-10% | STD | No special border |
| BORDERLINE | <6% | <7% | — | Dimmed |

**This tier language already partially used internally.** Surfacing it as a visible operator signal aligns displayed confidence with model tier definitions from CLAUDE.md.

---

---

*End of Full Slate Tactical Doctrine — Session 04*
*Planning only — no runtime changes made.*
*Next: Implementation roadmap prioritization (Session 05)*

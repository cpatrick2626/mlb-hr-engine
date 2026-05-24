# SPEC: Deployment Panel Architecture v1
**Component:** `deployment_panel`  
**Spec Version:** v1  
**Status:** SPECIFICATION ONLY — no runtime code modified  
**Author:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 5/12 — Suppression Intelligence Contract & Deployment Workflow Stabilization  
**Cross-reference:** `spec_suppression_score_contract_v1.md`, `operator_override_doctrine.md`, `deployment_trust_hierarchy.md`, `escalation_vs_suppression_doctrine.md`

---

## A. PANEL PURPOSE

The deployment panel is the final operator decision layer. It is not a pick-browsing surface. It is not an information dashboard. It is the confirmation surface the operator reaches after identifying a pick they intend to deploy.

### Deployment Confirmation
The panel consolidates all intelligence relevant to a single deployment decision into one view. When an operator opens the deployment panel for a specific pick, they should have everything they need to confirm or abandon the deployment — without navigating to another view.

### Escalation Consolidation
The panel presents the batter's escalation tier prominently as the primary deployment confidence signal. This tier has already been computed by the engine and weighted by all model factors. The panel does not re-explain the model — it presents the tier's deployment meaning.

### Suppression Visibility
The panel renders the pitcher's suppression tier directly in the deployment flow. An operator cannot reach the deployment action without passing through the suppression layer. This is intentional. Suppression information cannot be hidden, deferred, or collapsed at deployment time.

### Trust-State Awareness
The panel reflects the current data trust-state. If sources are degraded, stale, or unavailable, the panel communicates this inline — not as a separate warning page. Operators deploy knowing the exact confidence level of the underlying data.

### Exposure Awareness
The panel shows the operator's current position exposure context for this pick (team concentration, same-game picks, bankroll exposure). This prevents deployment decisions that inadvertently create correlated concentration.

---

## B. PANEL HIERARCHY

Nine zones. Fixed order. No zone may be repositioned. No zone may be hidden unless explicitly allowed by its zone definition.

```
┌─────────────────────────────────────────────────────────────┐
│ ZONE 1: DEPLOYMENT HEADER                                   │
│  Player name · Team · Position · Game · Date                │
│  Escalation tier badge (large) · Confidence value          │
├─────────────────────────────────────────────────────────────┤
│ ZONE 2: ESCALATION SUMMARY                                  │
│  Tier meaning in plain language · Model probability        │
│  Composite score breakdown · PA ceiling context            │
├─────────────────────────────────────────────────────────────┤
│ ZONE 3: SUPPRESSION LAYER                                   │
│  Pitcher name · Suppression tier badge                      │
│  Suppression score · Active signal pills                   │
│  Caution explanation (1–3 sentences)                       │
│  [Expand for full pitcher profile]                         │
├─────────────────────────────────────────────────────────────┤
│ ZONE 4: TACTICAL EVIDENCE                                   │
│  Top 3 reasons engine selected this pick                   │
│  Park factor context · Platoon advantage note             │
│  HVY modifier display (FAVORABLE / NEUTRAL / UNFAVORABLE) │
├─────────────────────────────────────────────────────────────┤
│ ZONE 5: RISK FACTORS                                        │
│  Active caution flags from engine filters                  │
│  Environmental risk (weather, dome status)                 │
│  Lineup position · PA ceiling risk                        │
├─────────────────────────────────────────────────────────────┤
│ ZONE 6: CONFIDENCE LAYER                                    │
│  Trust-state indicator · Data source status                │
│  Calibration context (if DEGRADED or RESTRICTED)          │
│  Last data refresh timestamp                               │
├─────────────────────────────────────────────────────────────┤
│ ZONE 7: OVERRIDE CONTROLS                                   │
│  [Shown when suppression tier = HIGH or LOCKDOWN]          │
│  Override eligibility check · Acknowledgement control     │
│  Override reason capture (LOCKDOWN only)                   │
├─────────────────────────────────────────────────────────────┤
│ ZONE 8: EXPOSURE SUMMARY                                    │
│  Current team concentration for operator's slate          │
│  Same-game picks count · Bankroll exposure context        │
│  Correlation risk alert (if applicable)                   │
├─────────────────────────────────────────────────────────────┤
│ ZONE 9: ACTION LAYER                                        │
│  [Deploy] control · [Abandon] control                      │
│  Bet size input (if logging) · Sportsbook selector        │
│  Deployment confirmation state                             │
└─────────────────────────────────────────────────────────────┘
```

### Zone Definitions

---

**Zone 1 — Deployment Header**

Primary identity anchoring. Operator must instantly confirm they are looking at the correct pick.

- Player full name: large, high-contrast
- Team abbreviation + position
- Opponent · Game time · Game ID
- Escalation tier badge: LARGE size (from `spec_escalation_badge_system_v1.md` — hero size when appropriate, expanded size standard)
- Confidence value: displayed as percentage, right-aligned adjacent to badge
- Zone 1 is NEVER collapsed. It is always visible when panel is open.

---

**Zone 2 — Escalation Summary**

Translates the model tier into deployment meaning in plain language.

- Tier meaning statement: one sentence. Example: "FIRE-tier pick. Engine confidence is high. Deploy at stated position size."
- Model probability: the calibrated HR probability for this game
- Composite score: EV%, Edge%, Confidence — three values, brief labels
- Expected PA ceiling: high (3.5+) / moderate (2.8–3.5) / limited (<2.8)
- Zone 2 is NEVER collapsed.

---

**Zone 3 — Suppression Layer**

The suppression intelligence integrated directly into deployment flow.

- Pitcher identity: name, team, hand, role
- Suppression tier badge: colored per tier spec (`spec_pitcher_suppression_card_v1.md`)
- Suppression score: integer 0–100
- Active signal pills: top 3 active signals, "(+N more)" control for remainder
- Caution explanation: 1–3 sentence plain-language summary
- Expand control: "View full pitcher profile" — expands inline to full 7-zone pitcher suppression card
- **Visibility rule:** Zone 3 is NEVER collapsed. Suppression is not hidden in the deployment flow regardless of tier. Even NONE-tier suppression shows the pitcher identity and "No suppression active" confirmation.

---

**Zone 4 — Tactical Evidence**

Justifies the pick to the operator. Prevents blind deployment.

- Top 3 contributing factors that drove this pick's escalation (from engine signal ranking)
- Park factor value and direction label (hitter-friendly / neutral / pitcher-friendly)
- Platoon advantage note: "R vs L — favorable platoon" or "R vs R — platoon neutral"
- HVY modifier: direction label (FAVORABLE / NEUTRAL / UNFAVORABLE) + brief explanation
- Zone 4 may be collapsed by default for NONE and LOW suppression picks at operator preference. Must render fully for MODERATE and above.

---

**Zone 5 — Risk Factors**

Active caution flags. Not every pick has active risk factors — this zone may be minimal.

- Engine filter caution flags (soft cautions that did not block the pick but flagged risk)
- Weather context: temperature, wind speed/direction, dome status
- Lineup position: if near bottom third, note reduced PA ceiling risk
- Zone 5 collapses to a single "No active risk flags" state when no caution flags are present.

---

**Zone 6 — Confidence Layer**

Data integrity and trust-state communication.

- Trust-state indicator: FULL / DEGRADED / RESTRICTED / BLOCKED (see `deployment_trust_hierarchy.md`)
- Data source status summary: Statcast (fresh/stale/unavailable), Weather (fresh/stale/unavailable), MLB API (live/degraded), Pitch Mix (available/unavailable)
- Last data refresh: timestamp for each source
- If DEGRADED: inline note on which signals may be underestimated
- If RESTRICTED: prominent caution that deployment confidence is materially incomplete
- Zone 6 is visible at a glance but does not demand operator attention when trust-state is FULL.

---

**Zone 7 — Override Controls**

Active only when suppression tier = HIGH or LOCKDOWN.

- Override eligibility check: displayed before controls render. States the reason override is required.
- HIGH suppression: single acknowledgement checkbox + "I understand this pick faces high pitcher suppression and accept reduced confidence" confirmation
- LOCKDOWN suppression: two-step acknowledgement — checkbox + override reason dropdown (NONE — operator preference / SAMPLE-CONFIDENT — operator data analysis / POSITION-LIMITED — small position size accepted)
- Override confirmation locks the acknowledgement state for this deployment session — it does not persist to future sessions
- Zone 7 is completely hidden when suppression tier = NONE, LOW, or MODERATE.
- Deployed without override when suppression tier = MODERATE — no override zone needed.

---

**Zone 8 — Exposure Summary**

Portfolio-level context for this deployment decision.

- Team concentration: "You have N picks from [team] today. This adds one more." Alert if ≥ 4.
- Same-game picks: count of other picks in this game. Alert if ≥ 3 (same-game correlation risk).
- Bankroll exposure: percentage of today's bankroll represented if this pick is added at stated size.
- Correlation risk alert: if effective N (N_eff from correlation model) would drop below 5, flag.
- Zone 8 renders a minimal "Exposure: Normal" state when no concentration risks exist.

---

**Zone 9 — Action Layer**

Deployment confirmation surface.

- [Deploy] control: primary action. Blocked until Zone 7 override complete (when required).
- [Abandon] control: secondary action. Always available. Dismisses panel without logging.
- Bet size input: optional field. Pre-populated from quarter-Kelly sizing recommendation. Editable.
- Sportsbook selector: dropdown. Stored with pick log for CLV tracking.
- Deployment confirmation state: after [Deploy] pressed, panel shows "Deployed — pick logged" confirmation before closing. Does not auto-close.

---

## C. VISUAL PRIORITY

### What Dominates Attention

**Primary attention target:** Zone 1 — Escalation tier badge. The badge is the largest, highest-contrast element. It must dominate before anything else is read.

**Secondary attention target (when suppression active):** Zone 3 — Suppression tier badge. When suppression tier = HIGH or LOCKDOWN, the suppression badge creates immediate visual contrast with the escalation badge. Two dominant signals. Both visible without scrolling.

**Tertiary attention target:** Zone 9 — Action layer. The [Deploy] button is visually prominent but never the largest element. It must not win the visual entry contest before the operator has processed Zones 1 and 3.

### What Suppresses Deployment Confidence

When suppression tier = HIGH or LOCKDOWN, the panel enters a caution-dominant visual state:

- Zone 3 border elevates: 2px solid in tier color (HIGH: `#E87040` / LOCKDOWN: `#C0392B`)
- Zone 7 override block renders with muted contrast — it is present but does not demand immediate engagement
- Zone 9 [Deploy] control is visually reduced (not hidden, not red, not alarming — simply muted) until override is complete
- After override is complete, [Deploy] returns to normal prominence

### When Caution Escalates Visually

| Suppression Tier | Panel Caution State |
|-----------------|---------------------|
| NONE | No caution state. Normal panel rendering. |
| LOW | Minimal: small blue note in Zone 3. No structural change. |
| MODERATE | Zone 3 renders amber border. Zone 4 expands by default. No panel-level change. |
| HIGH | Zone 3 orange-red border. Zone 7 appears. Zone 9 muted until override complete. |
| LOCKDOWN | Zone 3 crimson border + 3px left accent. Zone 7 appears with two-step acknowledgement. Zone 9 locked until both steps complete. |

### What Remains Secondary

- Zone 4 (Tactical Evidence) is informational, not action-driving
- Zone 5 (Risk Factors) is secondary context — visible but not dominant
- Zone 8 (Exposure Summary) is ambient — appears in peripheral vision unless alert triggers
- Zone 6 (Confidence Layer) is visible but understated when trust-state = FULL

---

## D. OVERRIDE DOCTRINE

Governed by `operator_override_doctrine.md`. Summary of panel-specific rules:

### When Override Becomes Available

Override controls (Zone 7) appear when:
- Suppression tier = HIGH
- Suppression tier = LOCKDOWN

Override does not appear for MODERATE, LOW, or NONE.

### When Override Is Blocked

Override is blocked (Zone 9 [Deploy] remains locked, Zone 7 acknowledgement does not resolve) when:
- Trust-state = BLOCKED (data source integrity failure — no deployment without data resolution)
- Pitcher role = OPENER or BULK (suppression score is inapplicable — deployment panel shows role warning instead)
- Escalation tier = VOID (no deployment surface available — panel shows VOID state)

### LOCKDOWN Override Behavior

LOCKDOWN override requires:
1. Checkbox: "I acknowledge this pitcher profile presents elite suppression risk"
2. Reason selection from dropdown (OPERATOR-PREFERENCE / SAMPLE-CONFIDENT / POSITION-LIMITED)
3. Both required before [Deploy] activates

After LOCKDOWN override is completed: Zone 9 [Deploy] activates. Zone 7 shows "Override accepted — proceed with caution" confirmation state.

### Degraded-Source Override Behavior

When trust-state = DEGRADED and suppression tier requires override:
- Override controls remain available
- Zone 7 adds inline note: "Note: Suppression score reflects partial data. Some signals may be underrepresented."
- Override proceeds normally. Operator is informed — not blocked.

When trust-state = RESTRICTED and suppression tier requires override:
- Override controls are grayed out
- Zone 7 shows: "Override unavailable — critical data source missing. Resolve data source before deployment."
- Zone 9 [Deploy] is blocked.

### Operator Acknowledgement Requirements

HIGH suppression: single checkbox acknowledgement.  
LOCKDOWN suppression: checkbox + reason selection.  
Both acknowledgements are session-scoped only — they do not persist across sessions or to other picks.

---

## E. TRUST-STATE VISIBILITY

Full definition in `deployment_trust_hierarchy.md`. Panel-specific rendering rules:

### FULL

**Visual treatment:** No trust indicator emphasis. Zone 6 shows "Data: Current" with green indicator.  
**Deployment permissions:** All deployment actions available.  
**Override behavior:** Normal — governed by suppression tier only.

### DEGRADED

**Visual treatment:** Zone 6 renders amber indicator. Source-level status notes visible.  
**Deployment permissions:** Deployment available. Operator informed of partial confidence.  
**Override behavior:** Override controls available. Staleness note added to Zone 7 when active.

### RESTRICTED

**Visual treatment:** Zone 6 renders orange-red indicator + expanded source status table. Zone 3 suppression card shows "Partial signal data" label.  
**Deployment permissions:** Deployment available but restricted confidence noted in Zone 9. Zone 9 [Deploy] label changes to "Deploy (restricted data)" — same action, different label.  
**Override behavior:** Override available for HIGH suppression. LOCKDOWN override blocked.

### BLOCKED

**Visual treatment:** Zone 6 renders crimson indicator. Banner in Zone 1 (beneath player identity): "Data source unavailable — deployment confidence cannot be confirmed."  
**Deployment permissions:** Zone 9 [Deploy] blocked. Operator may only [Abandon].  
**Override behavior:** All override controls hidden. Panel is informational only.

---

## F. INTERACTION RULES

### Expansion Philosophy

Zones 3, 4, and 5 support expansion. Expansion is always inline (push-down) — never overlay or modal.

Expansion shows additional detail without navigating away from the deployment panel. Operator remains in deployment context throughout.

### Modal Usage

The deployment panel itself is not a modal. It is a side panel or full-page panel — operator remains oriented within the session context.

One modal is permitted: the LOCKDOWN override confirmation (after both acknowledgement steps are complete, a brief "Are you sure?" confirmation modal appears before deployment proceeds). This modal has two controls: [Confirm deploy] and [Cancel]. Nothing else.

No other modals are used within the deployment panel.

### Warning Sequencing

When multiple caution signals are active simultaneously, they are presented in priority order:

1. LOCKDOWN or HIGH suppression (Zone 3) — highest priority
2. Trust-state issue (Zone 6) — if DEGRADED or worse
3. Engine caution flags (Zone 5) — secondary
4. Exposure alerts (Zone 8) — tertiary

Caution signals do not stack into compound banners. Each zone presents its own signal. The operator reads them in priority sequence.

### Progressive Disclosure

Default panel state reveals all zones but collapses secondary content within each:
- Zone 3: 3 signal pills + expand control (not full 7-zone pitcher card)
- Zone 4: Top 3 factors only
- Zone 5: Collapsed when no active flags
- Zone 6: Single-line trust indicator (not full source table)
- Zone 8: Minimal exposure summary (not full portfolio table)

Operator expands as needed. Expansion controls are visible but not emphasized.

### Deployment Pacing

The panel does not auto-submit. The operator must press [Deploy] explicitly.

After [Deploy] is pressed:
1. If LOCKDOWN: LOCKDOWN confirmation modal appears
2. If HIGH: brief 1.5-second confirmation spinner (not a delay gate — just acknowledges the action)
3. If MODERATE or below: immediate action — no delay

The panel does not close automatically after deployment. Operator must close it manually or press [Abandon] to dismiss. This ensures they have time to verify the logged confirmation.

---

## G. RESPONSIVE BEHAVIOR

### Desktop (≥1280px)

- Panel renders as a right-side panel (65–75% viewport width), pushing content left
- All 9 zones visible in single scrollable column
- Zone 9 Action Layer is sticky at the bottom of the panel viewport — visible without scrolling
- Zone 7 Override Controls appear inline between Zones 6 and 9 when active
- Expansion of Zones 3/4/5 is in-place (push-down within the panel column)

### Tablet (768px–1279px)

- Panel renders as a bottom sheet (80% viewport height), overlaying the main view
- Zones 1, 2, 3 visible without scroll
- Zones 4–8 accessible by scrolling
- Zone 9 Action Layer: fixed to bottom of sheet viewport
- Zone 7 Override Controls: inline, above Zone 9
- Expansion controls collapse secondary zone content by default (performance consideration)

### Mobile (<768px)

- Panel renders as full-screen overlay
- Zone 1 + Zone 3 Suppression tier: visible above the fold
- Zones 2–8: vertical scroll
- Zone 9 Action Layer: fixed to bottom of screen
- Override controls: full-width acknowledgement area above Zone 9
- Zone 8 Exposure Summary: collapsed by default — expand control available

---

## H. FORBIDDEN PATTERNS

The following patterns are rejected. They undermine operator trust, platform credibility, and the measured deployment doctrine of MLB HR ENGINE.

### Sportsbook CTA Styling
Rejected. The [Deploy] button must not look like a sportsbook "Bet Now" button. No gradient fills. No large green rounded rectangles. No dollar signs in the primary control label. The action surface is muted, professional, and activated by context — not by visual aggression.

### Giant Green Deploy Buttons
Rejected. Green-dominant action surfaces communicate excitement and urgency — the opposite of measured deployment. [Deploy] is standard button styling. Its prominence comes from position (Zone 9) not from color or size.

### Hidden Suppression
Rejected. Zone 3 (Suppression Layer) is never collapsed, never minimized, never deferred to a secondary view. If there is a pitcher, there is a suppression zone. The operator cannot deploy without seeing the suppression state.

### Hidden Trust Degradation
Rejected. Zone 6 is always visible. Trust-state = DEGRADED or worse must produce a visible indicator in Zone 6 that the operator encounters during normal deployment flow — not buried in a settings page.

### Forced Optimism Visuals
Rejected. The panel must not visually celebrate FIRE picks while suppressing visual acknowledgement of HIGH suppression. Both signals must be legible simultaneously. No "FIRE" animation or glow that overpowers the LOCKDOWN suppression rendering.

### Auto-Collapsing Warnings
Rejected. Caution states do not auto-collapse after a timer. If Zone 7 override is required, it remains visible until the operator explicitly completes or abandons the deployment.

### Modal Spam
Rejected. One modal is permitted (LOCKDOWN confirmation). All other decisions happen inline. No repeated "Are you sure?" confirmations for LOW or MODERATE suppression picks.

### Passive Override
Rejected. Override for LOCKDOWN must be an active, deliberate action — not a passive dismiss. A single click on a "Continue anyway" button is not sufficient. Two explicit steps are required.

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*

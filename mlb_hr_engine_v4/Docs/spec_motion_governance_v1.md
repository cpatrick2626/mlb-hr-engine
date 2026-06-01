# Motion Governance Doctrine — MLB HR ENGINE
**Version:** 1.0
**Step:** 9/12 — Tactical Animation, Motion Governance & Investigation Atmosphere
**Status:** Doctrine Only — No Runtime Implementation

---

## 1. Governing Philosophy

Motion in MLB HR ENGINE serves one purpose: **communicating operational state change to the operator**.

Motion is not decoration. Motion is not branding. Motion is not personality.

Every animation that fires must earn its existence by answering: *What operational fact does this communicate that static rendering cannot?*

If no answer exists, the animation does not exist.

---

## 2. Animation Permission Hierarchy

### PERMITTED — Motion with operational justification

| Element | Permitted Motion | Justification |
|---------|-----------------|---------------|
| Escalation badge | Single pulse on state change | New threat materialized |
| Trust score delta | Fade-in value update | Score recalculated |
| Feed item arrival | Slide-in from edge | New intelligence item |
| Deployment confirmation | Brief shimmer on commit | Irreversible action acknowledged |
| Suppression badge | Fade opacity shift | Threat qualification changed |
| Loading skeleton | Slow breathe pulse | Data hydration in progress |
| Critical alert banner | Single-cycle glow | Operator attention required |

### FORBIDDEN — Motion with no operational justification

| Element | Forbidden Behavior | Reason |
|---------|-------------------|--------|
| Any panel border | Continuous pulse | No state change communicated |
| Sidebar | Ambient animation | No information delivered |
| Background | Any motion | Operational distraction |
| Cards at rest | Hover bounce, float, drift | Decorative only |
| Text at rest | Shimmer, glow, marquee | Readability degradation |
| Score values at rest | Continuous pulse | False urgency signal |
| Trust tier badge at rest | Breathing animation | State has not changed |
| Any element post-transition | Persistent animation | Motion must end |

---

## 3. Escalation Motion Doctrine

### On Escalation Event (new CRITICAL or HIGH tier threat):

1. Target card border fires single 300ms glow pulse
2. Feed item slides in from right edge — 200ms ease-out
3. Escalation badge increments with 150ms opacity fade
4. Global sidebar badge increments with no animation — number change only
5. No secondary animations permitted during escalation event window

### Escalation Motion Rules:

- Escalation animation fires **once per event** — not on every render cycle
- If operator is already viewing escalated card, no animation fires
- Escalation motion completes fully before any subsequent escalation animation begins
- Simultaneous escalation events queue — do not fire in parallel
- Animation does not repeat on page refresh or navigation return

---

## 4. Suppression Motion Doctrine

### On Suppression Event (threat qualified down):

1. Target card opacity transitions from 1.0 → 0.65 over 400ms — slow, deliberate
2. Suppression badge appears with 200ms fade-in
3. No glow, no pulse, no border flash
4. Feed suppression log item slides in — same behavior as escalation feed item

### Suppression Motion Philosophy:

Suppression should feel like a door closing. Not an explosion. Not a celebration.

The operator has eliminated a threat. The motion communicates *removal from active consideration* — not failure, not warning, not excitement.

---

## 5. CRITICAL State Motion Behavior

### CRITICAL tier (highest escalation):

- Single 400ms amber/red glow pulse on card border — fires once on tier entry
- Badge enters with 200ms scale-in (0.8 → 1.0) — no bounce, no overshoot
- If Full Slate active: CRITICAL card receives subtle persistent border (1px solid, no pulse) to mark it as highest-priority in the battlefield view
- Persistent border is **static** — not animated — after entry motion completes

### What CRITICAL must NOT do:

- Continuous pulsing border
- Repeated flash cycles
- Sound without operator opt-in
- Forced scroll or scroll-jacking
- Modal interruption

CRITICAL state communicates urgency through **clarity of signal**, not volume of motion.

---

## 6. Hover Philosophy

Hover behavior is **informational**, never decorative.

### Permitted hover behavior:

| Element | Hover Response | Purpose |
|---------|---------------|---------|
| Player threat card | Subtle border intensify (opacity +20%) | Focus confirmation |
| Deployment button | Background shift to action state | Readiness signal |
| Feed item | Background tint shift | Selection affordance |
| Suppression control | Opacity +15%, cursor change | Interactivity signal |

### Hover behavior rules:

- Hover transitions: 120ms max — feel immediate, not theatrical
- No scale transforms on hover for data cards — operator is reading, not playing
- No shadow explosion on hover
- No glow expansion on hover
- Hover state must be **instantaneous to perceive** — delay kills tactical feel

---

## 7. Transition Pacing

### Page/View Transitions:

| Transition Type | Duration | Easing |
|-----------------|----------|--------|
| MAIN → JIG | 180ms fade | ease-in-out |
| JIG → MAIN | 150ms fade | ease-in |
| MAIN → Full Slate | 220ms fade | ease-in-out |
| Any modal open | 150ms scale + fade | ease-out |
| Any modal close | 100ms fade | ease-in |
| Sidebar expand | 200ms width | ease-out |
| Sidebar collapse | 180ms width | ease-in |

### Transition rules:

- No slide transitions between major views — views materialize, they do not travel
- No stagger animations across card grids on page load
- Content loads into position — it does not fly in from offscreen
- Loading skeleton transitions to content with 200ms cross-fade — no pop-in

---

## 8. Motion Cooldown Rules

After any animation fires:

- **Cooldown window:** 500ms minimum before same element can animate again
- **Feed cooldown:** 300ms between sequential feed item entries
- **Escalation cooldown:** 800ms between card escalation animations (prevents cascade overwhelm)
- **Global cooldown:** If 3+ animations fire within 1 second, queue remainder — do not fire simultaneously

These rules prevent the interface from becoming a Christmas tree during high-activity slates.

---

## 9. Attention Protection Rules

The operator's focus is the most valuable asset in the system.

**Rule 1: Never steal focus from a card the operator is reading.**
If operator has been dwelling on a card for >2 seconds, suppress all peripheral animations until dwell ends.

**Rule 2: Never animate the background of a focused view.**
When JIG is active (single-player deep investigation), sidebar animation stops. Feed animations pause. The operator is in surgical mode.

**Rule 3: Escalation never interrupts a deployment action.**
If operator is in deployment flow, escalation animations queue for post-deployment display. No motion fires during commit sequence.

**Rule 4: One primary attention signal at a time.**
The interface may not simultaneously animate more than one CRITICAL-tier signal. Priority queue governs.

---

## 10. Sidebar Animation Rules

The sidebar is **navigation infrastructure**, not a data surface.

### Permitted:
- Badge count update — number change only, no animation
- Collapse/expand — smooth width transition per Section 7
- Active section indicator — opacity change on route change

### Forbidden:
- Ambient pulse
- Glow effects
- Hover animations on navigation items beyond standard opacity shift
- Animation during data loading

The sidebar must feel like the wall of an operations room — present, stable, reliable.

---

## 11. Feed Animation Rules

The live intelligence feed communicates **stream of operational reality**.

### Entry behavior:
- New items slide from right edge: translateX(+24px) → 0 over 200ms, ease-out
- Items stack — older items shift down 60ms after new item arrives
- No fade-in on individual feed items — they materialize from edge

### At-rest behavior:
- Feed items at rest: completely static
- No hover glow on feed items
- Timestamp ticks (if implemented) update in place — no animation

### Overflow behavior:
- Oldest items fade out at bottom: 200ms opacity to 0, then remove from DOM
- No scroll animation — list reflows immediately

---

## 12. Deployment Animation Rules

Deployment is the most consequential operator action. Motion must communicate **weight and finality**.

### Pre-deployment:
- Deploy button: static until hover (per hover rules)
- Risk summary: no ambient animation

### On deploy commit:
1. Deploy button: 200ms pulse shimmer — single cycle
2. Confirmation state: 150ms fade to confirmation color
3. Deployed badge: scale-in 0.9 → 1.0 over 120ms
4. Position card: soft border glow — 300ms, single cycle, then static

### Post-deployment:
- All motion complete within 600ms of commit
- Deployed state is fully static — operator has acted, system has recorded
- No "success animation" loop — the act is done

---

*Motion governance is not style. It is operational discipline.*
*Every pixel that moves is spending the operator's attention budget.*
*Spend it only when the information value justifies the cost.*

# Tactical Animation Hierarchy — MLB HR ENGINE
**Version:** 1.0
**Step:** 9/12 — Tactical Animation, Motion Governance & Investigation Atmosphere
**Status:** Doctrine Only — No Runtime Implementation

---

## 1. Governing Principle

Animation tiers exist to create a **signal-to-noise ratio** that the operator can trust.

When everything animates equally, nothing communicates. The tier system ensures that a CRITICAL escalation motion is immediately distinguishable from a passive data load — because they are categorically different in duration, intensity, and persistence.

Operators learn to read this hierarchy instinctively. The animation vocabulary must be **consistent** and **unambiguous**.

---

## 2. Animation Tier Definitions

### TIER 0 — Passive
*Infrastructure and ambient state. Communicates system aliveness.*

| Property | Specification |
|----------|--------------|
| Duration | 150–200ms |
| Intensity | Minimal — opacity shifts only |
| Glow | None permitted |
| Movement | None permitted |
| Persistence | Single cycle, completes fully |
| Fade philosophy | Fade-in only — elements appear, never travel |
| Use cases | Data hydration, skeleton → content, timestamp updates |

**Passive tier behavior:**
- Loading skeletons breathe at 0.4s cycles while loading — completely static after data loads
- No passive-tier animation persists beyond its triggering state
- Passive tier may never interrupt a higher tier in progress

---

### TIER 1 — Informational
*State change that the operator should notice when their attention naturally arrives.*

| Property | Specification |
|----------|--------------|
| Duration | 200–300ms |
| Intensity | Low — background tint shift, opacity change |
| Glow | None |
| Movement | Slide-in from edge (feed items only) |
| Persistence | None — animation completes, element is static |
| Fade philosophy | Ease-out entry — confident arrival |
| Use cases | Feed item arrival, trust score update, badge increment, suppression event |

**Informational tier behavior:**
- Fires on state change — not on render
- Does not demand attention — will be seen when operator scans naturally
- Multiple informational animations may queue if cooldown rules allow
- No stacking of informational animations on same element

---

### TIER 2 — Escalation
*New threat materialized. Operator attention warranted when workflow permits.*

| Property | Specification |
|----------|--------------|
| Duration | 300–400ms |
| Intensity | Medium — border glow pulse, badge scale |
| Glow | Single-cycle pulse permitted on card border only |
| Movement | Badge scale-in (0.85 → 1.0), no overshoot |
| Persistence | None — animation fires once, element returns to static |
| Fade philosophy | Entry fast (ease-out), hold 0ms, exit with glow decay |
| Use cases | New HIGH-tier threat, escalation badge increment, feed escalation item |

**Escalation tier behavior:**
- Fires once per escalation event — not per render cycle
- Escalation cooldown: 800ms before same card can fire again
- If operator is dwelling on escalated card: animation suppressed
- Escalation tier does not interrupt deployment flow (per attention protection rules)

---

### TIER 3 — Critical
*Highest operational urgency. Demands acknowledgment in operator's next attention window.*

| Property | Specification |
|----------|--------------|
| Duration | 400ms entry + persistent static state |
| Intensity | High — amber/red glow pulse, followed by persistent static border |
| Glow | Single entry pulse (400ms), then static 1px border at reduced opacity |
| Movement | Badge scale-in (0.8 → 1.0), no movement of card itself |
| Persistence | Persistent border (static, not animated) until threat resolves |
| Fade philosophy | Entry pulse decays; persistent state is fully static |
| Use cases | CRITICAL tier threat entry, CRITICAL badge state |

**Critical tier behavior:**
- Entry motion fires once — persistent border state requires no animation
- CRITICAL persistent border is 1px solid color — not pulsing, not glowing
- Only one CRITICAL entry animation may fire at a time (queue rule)
- Persistent border communicates "this card is unresolved CRITICAL" — not urgency, not alarm
- When CRITICAL resolves, border fades out over 300ms

---

## 3. Animation Budget

The animation budget governs simultaneous animation load. It prevents the interface from becoming visually noisy during high-activity periods.

### Simultaneous Animation Caps:

| Tier | Max Simultaneous | Overflow Behavior |
|------|-----------------|-------------------|
| Tier 0 (Passive) | Unlimited (infrastructure) | N/A |
| Tier 1 (Informational) | 3 | Queue, FIFO, 300ms spacing |
| Tier 2 (Escalation) | 2 | Queue, 800ms spacing |
| Tier 3 (Critical) | 1 | Queue, complete before next fires |

### Budget Priority:

When budget is exceeded, higher tiers preempt lower:

1. Tier 3 preempts all queued Tier 1 and 2 animations
2. Tier 2 preempts queued Tier 1 animations
3. Tier 0 runs at all times — not subject to priority preemption

---

## 4. Layered Animation Conflict Rules

When multiple tiers attempt to animate the **same element** simultaneously:

**Rule 1: Higher tier wins.**
A CRITICAL entry (Tier 3) on a card cancels any pending Escalation (Tier 2) animation on that same card.

**Rule 2: Running animation completes.**
If Tier 2 animation is already mid-execution on a card when Tier 3 fires, Tier 2 completes its current cycle, then Tier 3 fires immediately after.

**Rule 3: No additive glow.**
Two glow animations on the same element do not stack. The higher-tier glow replaces the lower.

**Rule 4: Badge conflicts.**
If badge needs to increment and change tier simultaneously, tier change animation takes precedence. Value updates in place after tier animation completes.

---

## 5. Interruption Rules

### What may interrupt what:

| Interrupting Event | Interrupted Animation | Behavior |
|-------------------|----------------------|----------|
| CRITICAL entry | Any Tier 1 on same element | Cancel queued Tier 1 |
| CRITICAL entry | Running Tier 2 on same element | Let complete, then fire |
| Operator deploys | Any Tier 2 or 3 animations | Queue until post-deployment |
| Operator enters JIG | Tier 1/2 feed animations | Pause feed animations |
| Operator dwell (>2s on card) | Peripheral Tier 1/2 | Suppress peripheral, not target |

### What may never be interrupted:

| Animation | Protected From |
|-----------|---------------|
| Deployment confirmation shimmer | Everything — completes fully |
| CRITICAL entry on focused card | Never cancelled mid-cycle |
| Modal open/close | No interruption permitted |

---

## 6. Easing Reference

Consistent easing creates a coherent motion vocabulary. Operators internalize the timing unconsciously.

| Motion Type | Easing | Rationale |
|------------|--------|-----------|
| Element appears (all tiers) | ease-out | Fast entry, settles naturally |
| Element disappears | ease-in | Slow exit — signals departure, not disappearance |
| State change (same element) | ease-in-out | Balanced — no directional bias |
| Scale-in (badges) | ease-out, no overshoot | Crisp, not playful |
| Width/height transitions | ease-in-out | Architectural — feels structural |
| Opacity pulse (glow) | ease-in-out on both halves | Bell curve — not strobe |

**Overshoot (spring bounce) is forbidden at all tiers.** This is not a consumer app. Bounce communicates delight. This platform communicates operational reality.

---

## 7. Duration Reference

| Event Type | Recommended Duration |
|------------|---------------------|
| Hover state entry | 120ms |
| Hover state exit | 80ms |
| Feed item slide-in | 200ms |
| Badge increment | 150ms |
| Suppression opacity shift | 400ms |
| CRITICAL glow pulse | 400ms |
| Escalation border pulse | 300ms |
| Modal open | 150ms |
| Modal close | 100ms |
| Page transition | 150–220ms |
| Skeleton → content crossfade | 200ms |
| Deployment shimmer | 200ms |
| CRITICAL border fade-out on resolve | 300ms |

**No animation shall exceed 500ms.** Duration exceeding 500ms feels like lag, not motion.

---

## 8. Glow Allowance Reference

Glow is the highest-intensity visual signal available without adding elements. It must be rationed.

| Tier | Glow Permitted | Glow Behavior |
|------|---------------|---------------|
| Tier 0 | No | N/A |
| Tier 1 | No | N/A |
| Tier 2 | Yes — border only | Single pulse, decays fully |
| Tier 3 | Yes — border only | Single pulse, then static border |
| Hover states | No | Opacity shift only |
| Deployment confirm | Yes — button surface | Single shimmer, 200ms |

**Glow color must match escalation tier color scheme.** No novelty glows. No white glow. No blue glow unless it maps to a defined trust state.

---

*The animation hierarchy is a communication protocol.*
*Violating it by animating outside tier rules is not a style choice — it is information corruption.*
*Operators trust the system to speak only when it has something to say.*

# Tactical UI Reference Intake Doctrine
## MLB HR Engine — Visual Reference System

**Version:** 1.0  
**Phase:** Claude Step 1/12 — Tactical UI & Design System Stabilization  
**Status:** Planning document only. No runtime code modified.

---

## 1. Purpose of the Main HR Dashboard Image Folder

The `Main HR Dashboard` folder is the **visual intake bunker** for all dashboard and UI reference material entering the MLB HR Engine design system.

This folder is a **reference system, not a copy system.** Nothing in it gets lifted wholesale. Every image passes through the evaluation framework in Section 3 before any design decision is extracted. References inform layout language, escalation hierarchy, information density targets, and component logic — they do not dictate aesthetic imitation.

The intake bunker exists for one reason: to prevent visual drift. Without a controlled reference intake process, UI decisions accumulate from random sources, producing an incoherent system that looks like a generic dashboard rather than a purpose-built tactical command center.

**Current reference images in intake bunker (as of 2026-05-20):**
- `Main Batters Card.png`
- `Main Games Page.png`
- `Main Head to Head.png`
- `Main Pitcher Card.png`
- `Main Strategy Engine.png`

These five form the initial visual reference corpus. All future image additions must follow the folder structure and classification protocol in Section 2.

---

## 2. Recommended Folder Structure

Organize the intake bunker into named categories. Each subfolder holds reference images plus a single `_notes.md` file documenting what was extracted and why.

```
Main HR Dashboard/
├── 00_FINAL_DIRECTION/          # Approved direction only — see Section 7
├── 01_Command_Center/           # Operator-facing dashboards, multi-panel layouts
├── 02_Main_Engine/              # Core pick display, HR probability views
├── 03_JIG_Engine/               # JIG model outputs, threat scoring displays
├── 04_Full_Slate/               # Multi-game slate layouts, game flow cards
├── 05_Card_Systems/             # Individual player cards, pick cards, stat blocks
├── 06_Shell_Navigation/         # Tab bars, sidebar systems, routing chrome
├── 07_Mobile_Layouts/           # Sub-768px views, stacked card flows
├── 08_Typography_Labels/        # Font scale, label hierarchy, badge text
├── 09_Color_Lighting/           # Palette, glow behavior, surface contrast
├── 10_Animation_Motion/         # Transition references, micro-interaction patterns
├── 11_Bad_Examples/             # Anti-patterns to explicitly reject — see Section 4
├── 12_Component_Isolation/      # Single-component references (badges, chips, meters)
├── 13_Modal_Expansion/          # Modal flows, expansion panels, drawer patterns
├── 14_Game_View_Layouts/        # In-game state displays, live score presentation
├── 15_Player_Profile/           # Deep player context panels, stat breakdowns
├── 16_Pitch_Mix_Visuals/        # Pitch arsenal displays, matchup visualization
├── 17_Deployment_Slip/          # Bet slip UI, deployment confirmation flows
├── 18_Live_Data/                # Real-time data presentation, update patterns
├── 19_Alerts_Escalation/        # Alert tiers, danger signals, escalation UI
└── _INTAKE_LOG.md               # Running log of images added and evaluation status
```

**Intake log format (`_INTAKE_LOG.md`):**

```
| Date       | File                    | Category        | Score | Status    | Extracted |
|------------|-------------------------|-----------------|-------|-----------|-----------|
| 2026-05-20 | Main Batters Card.png   | 05_Card_Systems | 7/10  | Approved  | Yes       |
| 2026-05-20 | Main Games Page.png     | 04_Full_Slate   | 8/10  | Approved  | Yes       |
```

---

## 3. Image Evaluation Framework

Every reference image receives scores across ten dimensions before any design decision is extracted. Score each 1–3 (1=weak, 2=acceptable, 3=strong). Total max: 30.

**Approval threshold: ≥18/30. Rejection: <12/30. Gray zone 12–17: partial extraction only.**

### 3.1 Tactical Clarity
Does the layout communicate a decision, a threat level, or an operational state — not just information? A tactical layout answers "what do I do next." Score 3 if the visual immediately implies an action.

### 3.2 HR Intelligence Relevance
Is the information shown actually useful for home run prediction or bet deployment? Generic player stats, wins/losses, and team standings score 1. Barrel rate, exit velocity, pitcher suppressor factors, park context score 3.

### 3.3 Scan Speed
Can an operator extract the top-priority pick in under 2 seconds from the top of the layout? If the most important element is buried, deprioritized, or requires scrolling, score 1.

### 3.4 Escalation Readability
Does the design make tier differences obvious — elite vs. average vs. suppressed picks — through visual weight, color, or badge hierarchy rather than sorting alone? Score 3 if escalation tiers are visually self-evident without reading labels.

### 3.5 Information Density
Is the layout carrying its weight? Score 1 if the layout wastes real estate on whitespace, decorative elements, or repeated structures. Score 3 if every zone is doing work.

### 3.6 Operational Realism
Does this look like a tool that processes real outcomes under uncertainty, or does it look like a consumer product? Command centers score 3. Friendly app layouts score 1.

### 3.7 Visual Hierarchy
Is there a clear Z-order of importance? Primary → secondary → tertiary signals should have corresponding visual weight. Flat hierarchies score 1.

### 3.8 Responsive Usefulness
Can this layout concept survive compression to 375px wide without losing its tactical function? Pure desktop-only layouts that would collapse to unusable on mobile score 1.

### 3.9 Danger Signaling
Does the layout have a legible system for flagging risk — caution states, suppressed picks, bad matchup flags, filter failures? Score 3 if suppression and threat states are visually distinct from positive signals.

### 3.10 Component Reuse Potential
Does this reference contain patterns — cards, badges, meters, labels — that can be extracted and applied across multiple views in the MLB HR Engine? Score 3 if three or more components are transferable.

---

## 4. What to Avoid

The following patterns are explicitly rejected. Any reference image that is primarily composed of these elements scores below threshold and must be filed in `11_Bad_Examples/` with a note explaining why.

### Rejected Patterns

**Generic sportsbook UI** — odds tables, spread layouts, moneyline grids, bet type selectors. These are retail gambling interfaces built for maximum user volume, not operator precision.

**Fantasy dashboards** — player ranking lists, weekly projection tables, waiver wire displays. Fantasy UI optimizes for engagement, not intelligence. No roster construction logic belongs in this engine.

**Flat SaaS layouts** — white backgrounds, gray text, blue primary buttons, sidebar nav with icons, card grids with equal visual weight. This is the default output of design systems like Material and Chakra. It produces no escalation hierarchy and no tactical feel.

**Fake cyberpunk** — pure neon on black, hex grids, HUD scan lines, terminal-green glows. Tactical does not mean decorative-sci-fi. Cyberpunk references typically have poor scan speed (3D effects obscure label legibility) and zero operational realism.

**Oversized whitespace** — any layout where more than 40% of the screen is blank space under the pretense of "breathing room." The HR Engine operates on dense, high-stakes data. Whitespace is a luxury of consumer products, not a command center.

**Stat overload** — showing every available stat without hierarchy or relevance filtering. If a view presents barrel rate, xSLG, ISO, hard-hit%, BABIP, AVG, OBP, SLG, OPS, wRC+, and sprint speed simultaneously with equal weight, it scores 1 on scan speed and 1 on escalation readability.

**Repeated player blocks** — designs that tile identical-sized player cards with no differentiation by tier. Elite picks and fringe picks must look different. A uniform grid is an anti-pattern.

**Excessive neon** — more than two accent glow colors in a single view. Glow is a signal system, not a texture. When everything glows, nothing escalates.

**Decorative visuals without operational purpose** — stadium photography backgrounds, jersey graphics, team logo waterfalls, player headshot hero images. Visual decoration that carries zero information is rejected.

---

## 5. Translation Rules

When a reference image passes evaluation (≥18/30), extract design signals using these translation rules. Do not copy the aesthetic — translate the structural logic.

### 5.1 → Shell Behavior
Extract: tab depth, nav placement, primary vs. secondary view hierarchy, how the shell handles state transitions. Reject: decorative nav chrome, animated logo reveals, persistent advertising slots.

### 5.2 → Card Hierarchy
Extract: how cards differentiate by tier (size, border weight, badge presence, surface color). Define card variants: Elite Threat / Above Average / Neutral / Suppressed / Void. Each must be visually distinct without reading the label.

### 5.3 → Escalation Tiers
Map any tier system in the reference to the MLB HR Engine's own escalation vocabulary:
- **FIRE** — elite barrel, favorable park, favorable pitcher, top EV
- **STRONG** — above-average profile, positive EV, meets all filters
- **WATCH** — marginal EV, caution flags present
- **COLD** — suppressed by pitcher factor, park penalty, or weather
- **VOID** — failed filter, DNP, lineup scratch

### 5.4 → Tactical Badges
Extract: badge shapes, label brevity standards, color-to-meaning mapping. All badges in the MLB HR Engine must carry meaning in under 3 characters or a single glyph. No decorative badges.

### 5.5 → Pitch Mix Modules
Extract: how the reference presents matchup data — whether it uses bar charts, spider charts, or text tables. Translate to pitch mix module layout: arsenal breakdown, K%/HR% signal, HVY modifier display band.

### 5.6 → Player Threat Cards
Extract: information priority order within a card. MLB HR Engine card priority: Name → Tier Badge → HR Prob % → EV% → Barrel% → Park Factor → Pitcher Suppressor → Bet Size. Any reference that inverts this priority (e.g., team branding first) requires explicit override justification.

### 5.7 → Full Slate Game Flow
Extract: how games are grouped and what anchors each game block. Full Slate shows games first, picks within games second. References that lead with player lists rather than game containers are incompatible with Full Slate flow without structural inversion.

### 5.8 → Deployment Panels
Extract: confirmation flow — how a pick moves from candidate to deployed bet. Must show: player, odds, implied prob, engine prob, EV%, bet size, sportsbook target. Any reference that collapses confirmation to a single tap is rejected (insufficient friction for high-stakes deployment).

### 5.9 → Responsive Layouts
Extract: stacking order for mobile. Priority stack: escalation badge → name → HR prob → EV% → bet size. Secondary stack (expand): barrel, park, pitcher, pitch mix. Any reference that collapses all content into equal-weight rows fails responsive translation.

---

## 6. Approved MLB HR Engine Visual Language

The target feel across all views is defined by these ten qualities. Evaluate every design decision against this vocabulary.

| Quality | Definition |
|---|---|
| **Cinematic** | Frames information like a shot — composition, depth, and focal hierarchy. The eye is directed, not left to wander. |
| **Tactical** | Every element implies an operator decision. The layout is built for action, not observation. |
| **Predictive** | The design foregrounds probability and confidence signals. Future-state framing, not historical reporting. |
| **Machine-driven** | Feels like it was produced by an intelligent system, not assembled by hand. Systematic badge generation, consistent tier markers, rule-based visual output. |
| **Immersive** | The layout holds the operator inside the session. No visual escape hatches to generic browser chrome. |
| **Premium** | High surface quality: consistent spacing rhythm, no misaligned text, no orphaned elements, controlled typographic scale. |
| **Operationally believable** | If a professional sports analyst opened this dashboard, it should feel like a tool they could actually use — not a concept demo. |
| **Restrained glow** | Glow is used as a signal tier marker only. Two accent glow colors maximum per view. Glow intensity scales with escalation tier. |
| **Layered HUD depth** | Surfaces have depth — primary content sits above secondary context panels. Translucent backgrounds, border weight hierarchy, and z-layering are used to separate operational layers. |
| **Command-center realism** | The overall composition reads like a multi-stream data command center, not a single-purpose stat card. Multiple information streams are visible simultaneously but organized by priority. |

---

## 7. Final Direction Folder Rules

`00_FINAL_DIRECTION/` is the only visual reference folder that Codex implementation work may cite directly.

**To move an image into FINAL_DIRECTION:**
1. Image must have passed evaluation (≥18/30) and been filed in its category folder.
2. Extracted design signals must be documented in that category's `_notes.md`.
3. Claude must explicitly approve the move in a session with a written rationale.
4. The image must be renamed on move: `[category]-[descriptor]-APPROVED-YYYYMMDD.ext`

**FINAL_DIRECTION is immutable once approved.** Images are not removed or replaced; they are versioned (e.g., `v1` → `v2`). The folder accumulates an approved visual history.

**FINAL_DIRECTION is the single source-of-truth for Codex implementation.** If a Codex implementation step asks "what should this look like," the answer comes from FINAL_DIRECTION only — not from category intake folders, not from session notes, not from memory.

---

## 8. Claude / Codex Boundary

### Claude Owns

- **UX doctrine** — this document and all extensions to it
- **Visual hierarchy** — card priority order, escalation tier vocabulary, badge system
- **Layout direction** — which reference images pass, what gets extracted, how it maps to MLB HR Engine components
- **Interaction pacing** — how flows sequence (view → expand → deploy), friction levels, confirmation requirements
- **Escalation presentation** — what FIRE vs. COLD looks like, how suppression states render, how danger signals differ from positive signals
- **FINAL_DIRECTION approval** — Claude signs off before anything enters the approved source-of-truth folder

### Codex Owns

- **Implementation** — translating FINAL_DIRECTION and Claude-approved specs into working Streamlit/Python components
- **Runtime safety** — session state, cache logic, modal behavior, routing, error boundaries
- **Streamlit/component execution** — all `st.*` calls, component rendering, layout column math
- **State safety** — no accidental reruns, no state mutation on visual updates
- **Performance** — render time, API call sequencing, data loading patterns
- **Validation** — that implemented components match the approved spec without regression

### Boundary Enforcement

Claude does not write implementation code in planning documents.  
Codex does not make visual hierarchy decisions during implementation.  
If a Codex implementation decision has visual consequences beyond the spec (e.g., component doesn't fit the approved layout), it escalates to Claude before proceeding.

---

## 9. Next Steps

**Immediate (Claude Step 2/12):**
1. Evaluate the five existing intake images against the Section 3 framework and file scores in `_INTAKE_LOG.md`.
2. Classify each image into its appropriate category subfolder from Section 2.
3. Extract design signals from highest-scoring images and document in category `_notes.md`.

**Near-term:**
4. Define FINAL_DIRECTION v1 entries from approved extractions.
5. Produce card hierarchy spec (Section 5.2 translation) as a separate Claude planning doc.
6. Produce escalation tier visual spec (Section 5.3 translation).

**Codex handoff (when ready):**
- Codex does not receive a handoff until FINAL_DIRECTION contains at least three approved reference images.
- First Codex handoff will be scoped to a single component (most likely: player threat card) with a fully documented spec from FINAL_DIRECTION.
- All Codex implementation work on UI is gated on Claude-approved FINAL_DIRECTION entries.

---

*Document end. No runtime files modified. No app.py, pipeline.py, config.py, or any Python execution path was touched in the creation of this document.*

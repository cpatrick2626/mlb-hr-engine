# Universal Tactical Command Center Shell — Doctrine v1

**Phase:** 3/8 — Universal TCC Architecture  
**Status:** Doctrine / Architecture Only — NO runtime code authorized  
**Date:** 2026-05-22  
**Scope:** MAIN · JIG · STRATEGY · HITS · PERFORMANCE  
**Division:** 05 — Tactical UI & Design System

---

## 1. The Core Doctrine

### 1.1 One Platform, Five Missions

The MLB HR Engine is **one operational system**. The operator should never feel they switched applications. Every division shares the same cockpit. The mission changes. The controls do not.

```
Universal Platform Formula:
  SAME SHELL + DIFFERENT ENGINE = DIFFERENT MISSION
```

The TCC shell is the cockpit. Engines are the mission systems behind it.

### 1.2 What the Universal Shell Governs

The universal TCC shell owns:

- Filter layout and section structure
- Grouped control organization
- Tactical HUD styling and glow hierarchy
- Dropdown and number_input behavior
- Interaction patterns (preset bar, reset, lazy load)
- Typography scale and weight system
- Spacing and density rules
- Responsive behavior principles
- Section naming conventions
- Command strip structure (preset bar, visibility toggles)

The universal shell does **NOT** govern:

- Model formulas or scoring logic
- Session_state key values or namespaces
- Engine-specific routing or data pipelines
- How picks are ranked, scored, or qualified
- Filter effect (remove vs highlight vs sort)

### 1.3 Architectural Principle

```
TCC SHELL:  visual orchestration layer
ENGINES:    intelligence and scoring layer

Shell changes → aesthetic only
Engine changes → no visual impact without authorization
```

---

## 2. The Five Divisions

### 2.1 Division Identity Table

| Division | Code | Primary Mission | Intelligence Type | Output Type |
|---|---|---|---|---|
| MAIN | `MAIN` | Scan → Qualify → Deploy | Statcast + Market EV/Edge | Ranked pick list |
| JIG | `JIG` | Matchup → Confirm → Exploit | Raw-stat matchup, HVY pitch-mix | Modifier-ranked targets |
| STRATEGY | `STRAT` | Deploy → Structure → Stack | Portfolio philosophy, rotation concept | Strategy frameworks |
| HITS | `HITS` | Profile → Contact → Analyze | Hit/contact quality intelligence | Contact-profile analysis |
| PERFORMANCE | `PERF` | Track → Review → Learn | Historical pick P&L, CLV, calibration | Operational analytics |

### 2.2 Division Purpose Doctrine

**MAIN — Quantitative Deployment Engine**

Primary function: market-aware probability analysis with real-money deployment intelligence. MAIN is the only division that consumes EV%, Edge%, and model_prob as qualifying signals. Every MAIN pick is a candidate for real deployment. MAIN output is an actionable ranked list, not a research tool.

```
MAIN = machine-assisted deployment intelligence
```

**JIG — Tactical Exploit Engine**

Primary function: raw statistical interrogation of matchup quality. JIG has no model, no EV, no market awareness. It is a precision instrument for operators who want to manually investigate before lineup confirmation. JIG's defining constraint: every filter is operator-set, every threshold is visible, no hidden logic exists anywhere in the JIG system.

```
JIG = raw-stat battlefield investigation
CRITICAL: JIG contains NO hidden logic, NO scoring, NO recommendation manipulation
```

**STRATEGY — Strategic Deployment Engine**

Primary function: deployment structure analysis. Where MAIN answers "which players today?", STRATEGY answers "how should I structure my action across the slate?" STRATEGY operates at portfolio and rotation level — stack philosophies, exposure concepts, correlated hold structures, weekly bankroll frameworks.

```
STRATEGY = slate architecture and deployment philosophy
```

**HITS — Contact Intelligence Engine**

Primary function: batting profile analysis focused on hit and contact quality. HITS is not a HR-picking tool — it is a contact-quality investigation layer. Primary signals: batting average, exit velocity, sweet spot percentage, contact shape, spray patterns. HITS serves operators who deploy hit props alongside HR props.

```
HITS = contact profile intelligence
```

**PERFORMANCE — Operational Analytics Engine**

Primary function: post-slate review, pick settlement, ROI tracking, and calibration drift monitoring. PERFORMANCE is backward-looking. It never makes picks. It reviews, audits, and surfaces trends. PERFORMANCE is the accountability layer.

```
PERFORMANCE = track → review → calibrate
```

---

## 3. Shared Shell Architecture

### 3.1 Universal Section Structure

The following section taxonomy governs all division TCCs. Not every division uses every section. When a section exists in a division, it uses this naming, this order, and this visual position.

| Slot | Section Name | Applies To |
|---|---|---|
| 1 | Batter Power & Contact | MAIN, JIG, HITS |
| 2 | Launch & Contact Shape | MAIN, JIG, HITS |
| 3 | Matchup & Splits | MAIN, JIG, STRATEGY |
| 4 | Pitcher Vulnerability | JIG, STRATEGY |
| 5 | Environment | MAIN, JIG, STRATEGY |
| 6 | Advanced HR Signals | MAIN, JIG |
| 7 | Momentum & Recency | MAIN, HITS, PERFORMANCE |
| 8 | Game Context | MAIN, STRATEGY |
| 9 | Output Control | ALL |
| 10 | Pitcher Stuff & Suppression | JIG, STRATEGY |
| 11 | Advanced Contact Quality | HITS |

**Section ordering is permanent within any division TCC.** Section 3 always follows Section 2. Section 9 (Output Control) is always last among active sections. Adding a new section requires placing it in the existing numbered taxonomy.

### 3.2 Universal Layout Structure

Every TCC, in every division, follows this visual layout:

```
┌─ PRESET BAR ──────────────────────────────────────────┐
│  [Preset A]  [Preset B]  [Preset C]  [↺ Reset]        │
└───────────────────────────────────────────────────────┘

┌─ SECTION 1 ────────────────────────────────────────────┐
│  [Filter controls — grouped in columns]                │
└───────────────────────────────────────────────────────┘

┌─ SECTION 2 ────────────────────────────────────────────┐
│  [Filter controls — grouped in columns]                │
└───────────────────────────────────────────────────────┘

  ... active sections only ...

┌─ SECTION 9 — OUTPUT CONTROL ───────────────────────────┐
│  [Visibility toggles, sort mode, display options]      │
└───────────────────────────────────────────────────────┘
```

Sections with zero active controls for the current division are omitted entirely. Empty sections never render.

### 3.3 Preset Bar — Universal Rules

1. Preset bar always renders at the **top** of the TCC, above all sections
2. Maximum **3 presets per division** (operator cognition ceiling)
3. Each division maintains its own preset dict — no cross-division preset application
4. Every preset is a transparent bundle of named threshold values — no hidden behavior
5. Selecting a preset writes values but **never locks** manual adjustment
6. Reset button always visible alongside preset buttons, labeled `↺` or `Reset`
7. Preset button active state tracked in session_state with engine-namespaced key

### 3.4 Control Widget Standard

Universal TCC controls use `st.number_input` only. No `st.slider`.

**Rationale:** number_input supports direct keyboard entry, precise decimal input, and native +/- step buttons without the interaction cost and render thrashing of slider components.

Control format rules:
- Label matches exact column header in the output table for that value
- Units shown in label (e.g., "Barrel %" not "Min Barrel")
- Float controls: two decimal precision minimum
- Integer controls: integer step
- Minimum value: always 0 or natural floor for the stat
- No `min_value > 0` in default/Operational presets

---

## 4. MAIN vs JIG Behavioral Doctrine

This distinction is **mandatory and permanent.** These two engines have different operational identities. The TCC shell may look identical. The behavior behind it must not be.

### 4.1 Core Identity Contrast

| Dimension | MAIN | JIG |
|---|---|---|
| Intelligence type | Model-driven + market-aware | Raw stat interrogation |
| Ranking signal | EV × 0.4 + Edge × 0.35 + Confidence × 0.25 | HVY modifier (display-only) |
| Hidden logic | YES — Bayesian calibration, Platt scaling, context moderation | NONE — every value is what the operator set |
| Market dependency | YES — EV and Edge require market odds | NONE — JIG operates without market lines |
| Recommendation role | YES — generates ranked picks for deployment | NO — generates filtered lists for investigation |
| Operator experience | "This is my deployment recommendation" | "This is the raw battlefield after my filters" |

### 4.2 JIG Behavioral Hard Rules

The following are non-negotiable constraints for JIG, now and permanently:

1. **No model probability** — `model_prob` is never exposed in JIG filters or JIG output ranking
2. **No EV% or Edge%** — these are market-aware signals; JIG has no market
3. **No hidden weighting** — every signal in JIG's HVY modifier is transparent (5 additive components, all documented)
4. **No automatic qualification** — JIG does not declare a pick "qualified"; it shows filtered lists
5. **No deployment intelligence** — JIG output must never be presented as a pick recommendation
6. **No recommendation manipulation** — presets may set thresholds; they may not apply recommendation logic
7. **Raw-stat purity** — every control in JIG TCC reads a stat the operator can verify in the source data

The operator of JIG should feel: "I am interrogating the matchup. I set the rules. The list shows me what passes my rules."

The operator of MAIN should feel: "The engine has scored these picks. I am reviewing and selecting."

### 4.3 Why This Distinction Matters

If JIG ever gains hidden scoring or recommendation logic, it loses its identity as a pure interrogation tool. Operators would be trusting an opaque score they cannot audit. This defeats JIG's operational purpose.

If MAIN ever becomes a raw filter list without scoring, it loses its ability to surface non-obvious market inefficiencies. The whole value of Statcast calibration is the engine's ability to find edge the operator didn't manually calculate.

Both identities are valuable precisely because they are different.

---

## 5. Engine Differentiation Table

| Dimension | MAIN | JIG | STRATEGY | HITS | PERFORMANCE |
|---|---|---|---|---|---|
| **TCC namespace prefix** | `tac_` | `jig_tac_` | `strat_tac_` | `hits_tac_` | `perf_tac_` |
| **Has model_prob filter** | YES | NO | NO | NO | NO |
| **Has EV/Edge filters** | YES | NO | NO | NO | NO |
| **Has HVY modifier filter** | Matchup tab only | YES | NO | NO | NO |
| **Has batter power filters** | YES | YES | NO | YES | NO |
| **Has contact quality filters** | YES | YES | NO | YES | NO |
| **Has pitcher vulnerability filters** | Matchup tab only | YES | YES | NO | NO |
| **Has environment filters** | YES | YES | YES | NO | NO |
| **Makes pick recommendations** | YES | NO | YES | NO | NO |
| **Deployment eligible** | YES | NO | YES (portfolio) | NO | NO |
| **Has preset bar** | YES | YES | YES | YES | NO |
| **Primary sort signal** | EV / Edge rank | HVY modifier | Strategy score | Contact quality | Date / P&L |

---

## 6. Preset Governance

### 6.1 Preset Identity Rules

Presets communicate **operational posture**, not technical parameters. Names describe intent.

Good preset names: `Operational`, `Selective`, `Elite Only`, `All Tactical`, `Matchup+`

Bad preset names: `Barrel≥5%+HH≥35%`, `High EV Mode`, `Config A`

### 6.2 Existing Presets (Live, Session 37)

**MAIN:**
- `Operational` — no batter profile floors, EV/Edge qualify picks (default)
- `Selective` — Barrel ≥ 5%, HH ≥ 35%
- `Elite Only` — Barrel ≥ 8%, HH ≥ 40%, EV ≥ 2%, Edge ≥ 1.5%

**JIG:**
- `All Tactical` — full universe, broad scan (default)
- `Selective` — Barrel ≥ 5%, modifier ≥ 100%
- `Matchup+` — Barrel ≥ 6%, modifier ≥ 110%, HVY ≥ 40

### 6.3 Future Preset Examples (Doctrine-Level)

These are illustrative intent patterns for future divisions:

**STRATEGY presets (when authorized):**
- `Conservative Stack` — low-exposure, max 2 per game
- `Aggressive Rotation` — broad coverage across slate
- `Elite Correlation` — barrel-focused correlated holds

**HITS presets (when authorized):**
- `Contact Hunters` — high sweet spot, low K rate
- `Pull Power` — pull air, barrel bias
- `Spray Threat` — multi-directional contact, high GB%

### 6.4 What Presets May Never Contain

- Hidden scoring or recommendation logic
- Cross-engine key writes (MAIN preset may not write `jig_tac_*` keys)
- Dynamic values (preset values are static; no formula output)
- Auto-derived thresholds based on model output
- "Smart" or "AI" presets that adjust to current slate conditions

### 6.5 Preset Limit Rule

**Maximum 3 presets per division.** This is a UX cognition constraint. Operators under game-day time pressure must distinguish postures instantly. Three options map to: conservative / standard / aggressive. More than 3 creates decision paralysis.

---

## 7. Density Governance

### 7.1 Compact Tactical Density Rules

The TCC must remain operable under game-day pressure (tight time window, multiple simultaneous decisions). Density governs how much can be seen at a glance.

**Required density targets:**

| Element | Max Count | Rationale |
|---|---|---|
| Visible controls without scroll | 12 | One cognitive scan |
| Preset buttons | 3 | Instant posture selection |
| Columns per section | 3–4 | Scanner-friendly layout |
| Section label characters | ≤ 30 | Readable at glance |

**Forbidden density violations:**

- More than 4 columns in a single section row
- Controls with no section grouping (orphan controls)
- Sections with only 1 control (consolidate)
- Giant settings walls with no visual break
- Any control that requires scrolling to reach before the Output Control section
- Multiple preset bars in a single division TCC

### 7.2 Control Ordering Within Sections

Within each section, controls order from **highest signal rank to lowest signal rank** based on the 2026 signal analysis:

| Rank | Signal | Section |
|---|---|---|
| 1 | Barrel % | Power & Contact |
| 2 | Fly Ball % | Launch & Contact Shape |
| 3 | Power Multiplier | Power & Contact |
| 4 | xSLG | Power & Contact |
| 5 | Hard Hit % | Power & Contact |
| 6 | Exit Velocity | Power & Contact |
| 7 | Pull % | Launch & Contact Shape |
| 8 | HVY Modifier | Matchup |
| 9–12 | Market signals (EV, Edge, Model Prob) | Output/Market |

Sweet Spot % ranks weakest batter signal — place last in its section.

---

## 8. Visual Doctrine

### 8.1 The Universal Visual Formula

```
80% Tactical Realism + 20% Cinematic Escalation
```

This formula governs every visual decision. The platform must read as a real operational system, not as a data visualization or a betting website.

### 8.2 Glow Hierarchy

Glow is reserved for escalation signals. Ambient glow on every element defeats the hierarchy.

| Glow Level | When Applied | Color |
|---|---|---|
| None | Default, inactive, below threshold | — |
| Subtle (opacity 0.4–0.5) | Active threshold met, monitoring level | `#1e1e35` area glow |
| Moderate (opacity 0.5–0.7) | Strong signal, tactical attention | Signal-specific color |
| High (opacity 0.7–0.9) | Critical escalation, deploy-level | Gold / Red escalation |

Glow should never appear on more than 20% of visible elements simultaneously. If everything glows, nothing escalates.

### 8.3 Typography Scale

| Element | Size | Weight | Color |
|---|---|---|---|
| Section header | 11px | 600 | `#6666aa` |
| Division subtitle | 11px | 400 | `#555` |
| Control label | 12px | 400 | `#888` |
| Primary stat value | 13px | 700–800 | Signal-specific or `#ccc` |
| Secondary stat value | 12px | 500 | `#777` |
| Tertiary / meta label | 10px | 400 | `#555` |
| Micro badge | 9–10px | 600 | Badge color |

### 8.4 Accent Hairline Standard (Universal Card Rule)

All card types in all divisions share the top accent hairline pattern established in Sessions 38–39:

```css
position: relative;
overflow: hidden;
/* hairline */
::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, {signal_color}99, transparent);
  opacity: 0.6;
}
```

Signal color maps to the division's primary signal (EV color for MAIN, HVY grade color for JIG, etc.).

### 8.5 Pill Grouping Standard

Stat pills in cards organize into two groups, separated by a vertical rule:

- **Context group** (background `#0a0a18`) — model inputs, matchup signals
- **Market group** (background `#0c0c1e`) — EV, Edge, odds — primary deployment signals

Separator: `border-right: 1px solid #1e1e35` on the last context-group pill.

Market group applies only to MAIN cards. JIG, HITS, STRATEGY cards show context group only.

### 8.6 Forbidden Visual Patterns

- Bright white text on dark background for secondary elements (crushes glow hierarchy)
- Full-opacity glow on non-escalation elements
- Random color usage — every color choice must map to a signal or status
- Animated elements not tied to a state change
- Section headers with all-caps + large font (use small-caps or smaller size)
- Card borders that compete with the accent hairline
- Oversized controls that break compact density

---

## 9. Expansion Governance

### 9.1 Adding a New Division

When a new division is authorized for implementation:

**Step 1 — Doctrine first.** Write a division-specific doctrine doc before any code.

**Step 2 — Namespace assignment.** Assign a unique `tac_` prefix. Never reuse or overlap with existing namespaces.

**Step 3 — Section selection.** Select which Universal Sections (1–11) apply. Document why others are excluded.

**Step 4 — Preset design.** Define 3 presets with operational names before implementation.

**Step 5 — filter_controls.py.** Add the new division's preset dict to `filter_controls.py`. No division-specific logic in any other file.

**Step 6 — Validation checklist.** Verify all 12.1 checklist items from MASTER_TCC_DOCTRINE.md pass before shipping.

### 9.2 Adding a New Section to an Existing Division

1. Assign the section to the nearest numbered slot in the universal taxonomy (Sections 1–11)
2. If no slot fits, request an expansion to the taxonomy — do not invent ad-hoc sections
3. New section inherits universal layout (column structure, label format, preset-compatible keys)
4. Section must contain minimum 2 controls (else consolidate into adjacent section)
5. Update the division's preset dict to include the new keys at `0.0` default in the base preset

### 9.3 Scaling Rules

As the platform grows from 5 divisions toward a larger deployment system:

- Each new division adds ~12 controls maximum (cognitive cap)
- Each new division adds 3 presets maximum
- Division navigation must scale to support 5–10 divisions without sidebar crowding
- Lazy-load pattern (established Sessions 40–41) is mandatory for any content section exceeding 25 picks
- Card HTML cache (`_CARD_CACHE` pattern, Session 41) applies universally — no unbounded rebuilds

---

## 10. Runtime-Sensitive Warnings

The following rules protect against runtime contamination. These are not guidelines — violating them produces live data errors.

### 10.1 Session_State Namespace Isolation

**Warning:** Writing to another engine's `tac_*` keys from a preset or filter action is a contamination event. It will corrupt the other engine's filter state for the current session.

Every session_state write must be prefixed to the correct engine namespace. There is no exception.

### 10.2 Filter Pool Source Integrity

**Warning:** Full Slate All Players mode must source from `all_players` (or `scored_all` in JIG), never from `_tac_ranked`. If the source pool is wrong, the All Players battlefield view silently becomes a filtered view. Operators will not notice. This is a data integrity failure.

### 10.3 JIG Scoring Purity

**Warning:** Any signal that auto-adjusts JIG output beyond the operator's visible threshold settings is a JIG identity violation. This includes: hidden score boosts, invisible recommendation weighting, auto-qualification logic, or any derived signal that is not computed from operator-set raw stats.

### 10.4 Calibration Layer Independence

**Warning:** Platt calibration and elite barrel preservation (Sessions 21–23) are model-layer concerns. The TCC shell must never call, adjust, or reference calibration functions. Calibration lives entirely in `engine/calibration.py` and is applied in `pipeline.py`. The TCC displays calibrated output — it does not control the calibration process.

### 10.5 Card Cache Invalidation

**Warning:** Card HTML caches keyed without `slate_ts` will serve stale content across date changes. Every cache key that references player data must include `slate_ts` (or `_jig_slate_ts` for JIG). Failure mode: yesterday's pitch data, odds, or lineup status shown in today's session.

---

## 11. Anti-Patterns to Avoid

### 11.1 Structural Anti-Patterns

| Anti-Pattern | Why Prohibited |
|---|---|
| A "Master Preset" that sets values across MAIN and JIG simultaneously | One preset = one namespace = one engine. Cross-engine preset writes contaminate both engines. |
| A "Combined View" that merges MAIN and JIG ranked output into a single list | MAIN ranks by EV. JIG ranks by HVY. A merged list has no coherent ranking signal. |
| A unified scoring layer that spans all 5 divisions | Each division's intelligence is different. Unifying scoring destroys each division's identity. |
| Adding EV% or Edge% to JIG TCC | JIG is raw-stat only. Market signals have no place in a pure interrogation tool. |
| Adding model_prob to STRATEGY, HITS, or PERFORMANCE TCC | model_prob is MAIN's intelligence. Other divisions use different primary signals. |
| Hiding filter logic inside a preset | Presets are transparent threshold bundles. No preset may apply logic the operator cannot see. |
| Auto-tuning presets based on model output | Presets are static. Auto-tuning is machine recommendation dressed as operator control. |

### 11.2 Density Anti-Patterns

| Anti-Pattern | Why Prohibited |
|---|---|
| More than 12 controls visible without scroll | Exceeds cognitive scan limit under time pressure |
| More than 3 preset buttons per division | Decision paralysis; defeats instant posture switching |
| Unsectioned controls (orphan filters) | Operators cannot locate controls without grouping |
| Sliders instead of number_input | Sliders are imprecise, trigger render thrashing, and block keyboard entry |
| Section with only 1 control | Too sparse — consolidate into adjacent section |
| Controls not grouped by signal type | Grouping by signal type enables scan-and-act; alphabetical order does not |

### 11.3 Visual Anti-Patterns

| Anti-Pattern | Why Prohibited |
|---|---|
| Glow on more than 20% of simultaneous visible elements | Destroys the escalation hierarchy |
| Cinematic elements that serve no operational function | 20% cinema maximum; 80% must be tactical realism |
| Color usage without signal mapping | Color communicates status — random color is noise |
| Large card spacing that breaks compact density | Tactical scan requires density; large spacing breaks the cockpit feel |
| Animated transitions on filter changes | Filter changes are operational; animation adds latency and distraction |
| Removing batters in Full Slate All Players mode | All Players is a battlefield view; filtering converts it to a pick list |

### 11.4 Identity Anti-Patterns

| Anti-Pattern | Why Prohibited |
|---|---|
| JIG gaining any hidden scoring or recommendation logic | Destroys JIG's purpose as a pure interrogation tool |
| MAIN losing its ranked output in favor of a filtered list | Destroys MAIN's ability to surface non-obvious market inefficiencies |
| PERFORMANCE making pick recommendations | PERFORMANCE is backward-looking only; pick recommendations live in MAIN |
| STRATEGY applying model_prob or EV gates | STRATEGY operates at portfolio structure level, not pick-level probability |
| HITS treating HR probability as its primary signal | HITS analyzes contact quality; HR probability is MAIN's domain |

---

## 12. Future Scaling Guidance

### 12.1 Navigation Scaling (5 → 10+ Divisions)

Current Streamlit tab navigation works well at 5 divisions. At 7–10 divisions, tab overflow becomes a problem. When more than 7 divisions exist, consider:

- Grouped navigation (e.g., "Intelligence" group: MAIN, JIG, HITS; "Operations" group: STRATEGY, PERFORMANCE, DEPLOYMENT)
- Division-level landing page with mission-card routing
- Collapsible division groups in sidebar

Do not implement this until ≥6 divisions are actively in use.

### 12.2 Shared Component Library Growth

As divisions multiply, the shared component library will grow. Components eligible for sharing:

- `render_filter_control()` — already shared (filter_controls.py)
- `render_preset_bar()` — already shared (filter_controls.py)
- Card HTML skeleton (accent hairline, pill groups, hero signal slot) — eligible for shared util
- `_card_html(fp, builder)` cache helper — eligible for shared util
- Weather fragment builder — eligible for shared util

Components that must **never** be shared:

- `_apply_*_filters()` — engine-specific application logic
- Preset dicts — engine-specific postures
- Fingerprint tuple construction — engine-specific key sets
- Scoring functions — engine-specific intelligence

### 12.3 Session State Management at Scale

At 5+ divisions, session_state key count grows rapidly. Governance:

- Every new division adds a documented namespace prefix to this doctrine before implementation
- No two divisions may share the same prefix
- Key format: `{prefix}_{descriptor}_{qualifier}` (e.g., `strat_tac_min_corr_exposure`)
- Key audit: run a session_state key inventory check before each new division ships

Current namespace registry:

| Division | Prefix | Status |
|---|---|---|
| MAIN TCC | `tac_` | LIVE |
| JIG TCC | `jig_tac_` | LIVE |
| Full Slate | `fs_tac_` | LIVE (visibility only) |
| Deployment | `dep_tac_` | RESERVED (not yet implemented) |
| STRATEGY | `strat_tac_` | RESERVED |
| HITS | `hits_tac_` | RESERVED |
| PERFORMANCE | `perf_tac_` | RESERVED |
| Escalation display | `_esc_*` | LIVE |
| Full Slate visibility | `fs_*` | LIVE |
| TCC display | `tcc_*` | RESERVED |
| Table interaction | `table_*` | RESERVED |

### 12.4 Render Architecture at Scale

The lazy-load gate pattern (Sessions 40–41) is the mandatory architecture for any content section with variable-length output. As divisions grow:

- Each new division applies lazy gates to its primary content section
- Card HTML cache (`_CARD_CACHE`) is global and invalidates on `slate_ts` — all divisions share it automatically
- Pitch mix expander lazy gate pattern applies to any division that exposes pitch data
- tab_advanced_strategies and tab_hits lazy gates (deferred from Session 41) are the next application of this pattern

---

## 13. Deliverable Summary

### 13.1 What This Document Establishes

1. **Universal TCC Doctrine** — one shell, five missions, permanent behavioral rules
2. **Shared Shell Architecture** — section taxonomy (11 sections), layout structure, preset bar, control widget standard
3. **Engine Differentiation Table** — five divisions, all behavioral dimensions mapped
4. **MAIN vs JIG Behavioral Doctrine** — permanent identity distinction, hard rules for JIG purity
5. **Preset Governance** — what presets contain, what they may not contain, max 3 per division
6. **Density Governance** — max 12 controls, column rules, signal-rank ordering within sections
7. **Expansion Governance** — 6-step process for new divisions, section addition rules, scaling rules
8. **Runtime-Sensitive Warnings** — 5 named contamination risks with failure mode descriptions
9. **Future Scaling Guidance** — navigation scaling, shared component library growth, session_state management, render architecture
10. **Anti-Patterns to Avoid** — 4 categories: structural, density, visual, identity

### 13.2 Implementation Sequence (When Authorized)

This doctrine applies to future phases. Current state (Sessions 34–44) is the implementation baseline.

When STRATEGY, HITS, or PERFORMANCE TCCs are authorized for implementation, follow this sequence:

1. Write division-specific doctrine doc (referencing this universal doctrine)
2. Assign namespace prefix (registered above)
3. Select active Universal Sections
4. Design 3 presets with operational names
5. Add preset dict to `filter_controls.py`
6. Implement division TCC in `app.py` following the universal layout structure
7. Validate using MASTER_TCC_DOCTRINE.md Section 12.1 checklist
8. Update namespace registry in this document

### 13.3 What Is Not Authorized by This Document

This document authorizes **doctrine and architecture only**. The following require separate authorization:

- Any changes to `app.py`
- Any changes to `filter_controls.py`
- Any new session_state keys
- Any new division implementation
- Any preset value changes for existing divisions
- Any routing changes or new Streamlit tab additions

---

## Appendix A: Section Taxonomy Reference

| Slot | Name | Primary Signals | MAIN | JIG | STRAT | HITS | PERF |
|---|---|---|---|---|---|---|---|
| 1 | Batter Power & Contact | Barrel, HH, xSLG, ISO, Power Mult | ✓ | ✓ | — | ✓ | — |
| 2 | Launch & Contact Shape | FB%, Pull%, Sweet Spot%, GB% | ✓ | ✓ | — | ✓ | — |
| 3 | Matchup & Splits | Platoon, Home/Away, Hand splits | ✓ | ✓ | ✓ | — | — |
| 4 | Pitcher Vulnerability | pit_factor, HR/9, K%, HVY modifier | ME tab | ✓ | ✓ | — | — |
| 5 | Environment | Park factor, weather, wind, temp | ✓ | ✓ | ✓ | — | — |
| 6 | Advanced HR Signals | HR Window, HR/PA, model_prob | ✓ | — | — | — | — |
| 7 | Momentum & Recency | Recent form, rolling window, HR streak | ✓ | — | — | ✓ | ✓ |
| 8 | Game Context | Game time, lineup position, order | ✓ | — | ✓ | — | — |
| 9 | Output Control | Sort mode, page size, visibility | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10 | Pitcher Stuff & Suppression | Pitch mix, velo decline, suppressor score | ME tab | ✓ | ✓ | — | — |
| 11 | Advanced Contact Quality | xwOBA, xBA, launch angle, spray | — | — | — | ✓ | — |

ME tab = active only in the Matchup Edge tab within MAIN (not a MAIN universe filter)

---

## Appendix B: MAIN vs JIG — The Operator Experience Contract

The following is the intended operator experience for each engine. Implementation decisions should be tested against this contract.

**MAIN operator experience:**

> "I open MAIN. The engine has already scored every starting batter against today's market. I see a ranked list. The picks at the top have the highest positive expected value. I can adjust thresholds to widen or narrow the pool. But the ranking — the intelligence — is the engine's. I trust it because it's been calibrated against real 2025-2026 data. I deploy from this list."

**JIG operator experience:**

> "I open JIG. I am in control. I set my own thresholds for barrel rate, hard hit rate, pitch modifier. The list shows me exactly who passes my rules and nothing else. The engine didn't decide anything — I decided. What I see is the raw interrogation result. There are no hidden boosts, no invisible recommendations. I use this to confirm what I already suspect, or to discover matchup patterns before lineup confirmation."

If an implementation decision makes MAIN feel like a raw filter tool, it has failed. If an implementation decision makes JIG feel like a recommendation engine, it has failed.

---

*End of doctrine document.*  
*Status: Architecture doctrine only. No runtime implementation authorized.*  
*Route: Obsidian (permanent storage) + Division 05 governance*

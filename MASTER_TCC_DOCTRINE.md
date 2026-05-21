# Master Tactical Control Center — Doctrine & Operational Governance

**Version:** Phase 3A  
**Status:** Doctrine / Planning Only — NO runtime code authorized  
**Date:** 2026-05-21  
**Scope:** MAIN · JIG · Full Slate · Future Deployment Systems

---

## 1. Purpose

The Master Tactical Control Center (TCC) is the **single operational control layer** shared across all engines. It controls what the operator sees and acts on. It does not compute, score, or calculate.

```
TCC: ORCHESTRATES
Engines: CALCULATE
```

The TCC exposes:
- Raw threshold filters (what qualifies)
- Tactical posture controls (how aggressive)
- Visibility controls (what is shown)
- Engine scope governance (which engine is affected)

The TCC does NOT:
- Replace engine-specific scoring
- Unify formulas or probability models
- Force shared intelligence logic
- Alter model_prob, EV%, or Edge% values

---

## 2. Shared Filter Architecture

### 2.1 The Shared Filter Vocabulary

All engines draw from the same raw filter vocabulary. Each filter is:
- A **minimum threshold** on a raw stat or derived signal
- **>= logic** (pass if value meets or exceeds threshold)
- **AND-stacked** (all active filters must pass simultaneously)
- **No hidden modifiers** (threshold is the only logic)

**Canonical filter vocabulary:**

| Filter Key | Type | Display Label | Units |
|---|---|---|---|
| `min_barrel` | float | Barrel % | % (0–20) |
| `min_hh` | float | Hard Hit % | % (0–100) |
| `min_xslg` | float | xSLG | decimal (0–4.0) |
| `min_iso` | float | ISO | decimal (0–0.400) |
| `min_pull_air` | float | Pull Air % | % (0–100) |
| `min_hr_window` | float | HR Window | % (0–30) |
| `min_ev` | float | EV % | % (0–15) |
| `min_edge` | float | Edge % | % (0–15) |
| `min_conf` | float | Confidence | % (0–100) |
| `min_model_prob` | float | Model Prob | % (0–30) |
| `min_matchup_pct` | int | Matchup Modifier | % (70–140) |
| `min_hvy_score` | int | HVY Score | integer (0–100) |

### 2.2 Engine Key Namespacing

Each engine namespaces its TCC keys to prevent session_state collision:

| Engine | Key Prefix | Example |
|---|---|---|
| MAIN | `tac_` | `tac_min_barrel` |
| JIG | `jig_tac_` | `jig_tac_min_barrel` |
| Full Slate | `fs_tac_` | `fs_tac_min_barrel` |
| Deployment | `dep_tac_` | `dep_tac_min_barrel` |

Each engine reads only its own keys. Cross-key reads are a contamination violation.

### 2.3 Implementation Anchor

`filter_controls.py` is the **single implementation file** for all TCC widget rendering.

- `render_filter_control()` — renders one threshold control (number_input)
- `render_preset_bar()` — renders one-click preset buttons
- `MAIN_PRESETS` — MAIN engine preset definitions
- `JIG_PRESETS` — JIG engine preset definitions

Future engines add their own preset dict to this file. No other TCC logic lives outside it.

---

## 3. Engine Scope Governance

### 3.1 Engine Identity Definitions

These identities are permanent. No shared TCC control may override them.

**MAIN — Quantitative Deployment Engine**
- Purpose: market-aware EV/Edge pick generation for real-money deployment
- Intelligence: Statcast-calibrated model_prob, no-vig EV%, edge% vs market
- Output: ranked picks with EV and Edge as primary signals
- Posture: risk-aware, deployment-grade precision

**JIG — Tactical Exploit Engine**
- Purpose: raw-stat matchup exploitation, no market dependency
- Intelligence: HVY pitch-mix modifier, raw Statcast thresholds, AND-stacked filtering only
- Output: modifier-ranked picks with matchup quality as primary signal
- Posture: broad scan, pattern hunting, pre-lineup intelligence

**Full Slate — Battlefield Scan Layer**
- Purpose: complete game-day universe visibility before lineup confirmation
- Intelligence: highlight and sort; no filter removal in All Players mode
- Output: game-organized batter rows, all confidence levels
- Posture: situational awareness, not a pick list

**Deployment (future)**
- Purpose: automated pick execution interface
- Intelligence: inherits from MAIN; adds confidence gate and bankroll exposure caps
- Posture: conservative precision, zero speculative picks

### 3.2 Scope Isolation Rules

A TCC control's scope must be declared. Any filter that affects multiple engines must declare explicitly which engines it applies to.

```
scope: [MAIN, JIG, Full Slate, Deployment]
```

Default scoping rules:
- Raw power/contact filters (Barrel, HH, xSLG, ISO): apply to all engines
- Market filters (EV, Edge): apply to MAIN and Deployment only — NOT JIG
- Matchup filters (Matchup %, HVY score): apply to JIG and Full Slate only — NOT MAIN scoring
- Model probability filter: applies to MAIN and Deployment only

Cross-scope application is a contamination violation. JIG should never read `tac_min_ev`. MAIN should never read `jig_tac_min_hvy_score`.

### 3.3 Filter Effect by Engine

| Filter | MAIN | JIG | Full Slate | Deployment |
|---|---|---|---|---|
| Barrel % | narrows pool | narrows pool | highlights only | narrows pool |
| Hard Hit % | narrows pool | narrows pool | highlights only | narrows pool |
| xSLG / ISO | narrows pool | narrows pool | highlights only | narrows pool |
| EV % | narrows pool | NOT APPLICABLE | NOT APPLICABLE | narrows pool |
| Edge % | narrows pool | NOT APPLICABLE | NOT APPLICABLE | narrows pool |
| Model Prob | narrows pool | NOT APPLICABLE | NOT APPLICABLE | narrows pool |
| Matchup % | Matchup Edge tab only | narrows pool | highlights only | NOT APPLICABLE |
| HVY Score | Matchup Edge tab only | narrows pool | NOT APPLICABLE | NOT APPLICABLE |

"highlights only" = Full Slate All Players mode shows all batters; filters change row color/rank, not visibility.

---

## 4. Preset Philosophy

### 4.1 What a Preset Is

A preset is a named, transparent bundle of threshold values. Nothing more.

```
Preset = { filter_key: threshold_value, ... }
```

The operator sees all values. No preset may contain hidden logic, weighted combinations, or mystery scoring modes.

### 4.2 Preset Naming Convention

Presets communicate tactical intent. Names must describe the operator's strategic posture, not the math.

**MAIN presets (exists, Sessions 37):**
- `Operational` — no batter-profile floors; EV/Edge gates qualify picks (default)
- `Selective` — Barrel ≥ 5%, HH ≥ 35%; restricts to power-contact profile
- `Elite Only` — Barrel ≥ 8%, HH ≥ 40%, EV ≥ 2%, Edge ≥ 1.5%

**JIG presets (exists, Session 37):**
- `All Tactical` — full universe, broad matchup exploration (default)
- `Selective` — Barrel ≥ 5%, modifier ≥ 100%; neutrals filtered out
- `Matchup+` — Barrel ≥ 6%, modifier ≥ 110%, HVY ≥ 40; elite exploit only

**Future preset patterns (doctrine-level):**

| Name | Intent | Design Rule |
|---|---|---|
| Aggressive Hunt | High-ceiling, lower certainty | Barrel ≥ 5%, EV ≥ 1.5%, broader pool |
| Pitcher Collapse | Pitcher-side vulnerability hunt | min_hvy_score boost + modifier ≥ 105% |
| Weather Boost | Favorable environment exploitation | No batter gate; requires env context |
| Safe Deployment | Max precision before real-money action | Barrel ≥ 8%, EV ≥ 3%, Edge ≥ 2% |

**Preset rules:**
1. Every value in a preset must be visible in the TCC UI
2. Preset names must be self-explanatory to a non-technical operator
3. No preset may apply cross-engine scope (MAIN preset only sets `tac_` keys; JIG preset only sets `jig_tac_` keys)
4. Selecting a preset does NOT lock the operator from manual adjustment

---

## 5. Tactical Posture Hierarchy

Three posture layers. Each is independent. Lower layers do not override higher layers.

```
Layer 1 — UNIVERSE (what enters the engine's pool)
  └── Engine-specific pipeline filters (EV gate, lineup state, etc.)
      Controlled by: engine config, not TCC

Layer 2 — PROFILE GATE (what the TCC narrows by raw stat threshold)
  └── TCC raw filters: Barrel, HH, xSLG, ISO, Pull Air, HR Window
      Controlled by: TCC number_input controls

Layer 3 — MARKET/MATCHUP GATE (what qualifies by signal type)
  └── TCC market filters (EV, Edge, Model Prob) — MAIN only
  └── TCC matchup filters (Modifier, HVY) — JIG + Matchup Edge tab only
      Controlled by: TCC number_input controls
```

Visibility (show/hide) is Layer 0 — it sits above all gate layers. Full Slate All Players mode operates at Layer 0 only: no gates remove batters, filters only rerank/highlight.

---

## 6. Operational Workflow

### 6.1 Daily Operator Flow

```
1. CONFIRM SLATE
   Full Slate tab → All Players mode
   Scan all active batters, verify game urgency, identify weather impacts

2. ASSESS BATTLEFIELD (JIG)
   Open JIG → All Tactical preset
   Scan HVY modifier distribution
   Identify high-modifier targets before lineup confirmation

3. QUALIFY PICKS (MAIN)
   Open MAIN → Operational preset
   Review Pre-Lineup Pool and confirmed starters
   Apply Selective or Elite Only preset for deployment

4. NARROW FOR DEPLOYMENT
   Apply market gate (EV ≥ N%, Edge ≥ N%)
   Activate Portfolio Optimizer if deploying real capital
   Cross-check JIG targets vs MAIN picks

5. LOG AND TRACK
   Log to pick tracker with sportsbook field populated
   Capture opening lines for CLV
   Run capture_closing_lines.py before first pitch
```

### 6.2 TCC Interaction Rules

- **Presets set all values simultaneously** — no partial preset application
- **Manual adjustment after preset** is always permitted
- **Reset button** returns all TCC keys to 0.0
- **Preset active state** persists in session_state but does NOT prevent manual override
- **Filter changes trigger rerender** — no explicit submit required (Streamlit reactive)

---

## 7. Display Hierarchy

### 7.1 TCC Layout Doctrine

The TCC must feel **compact, operational, layered**. One glance should communicate posture level.

**Required layout structure:**

```
┌─ PRESET BAR ──────────────────────────────────┐
│  [Operational]  [Selective]  [Elite Only]  [↺] │
└───────────────────────────────────────────────┘

┌─ UNIVERSE FILTERS (affect all tabs) ──────────┐
│  col1: Power       col2: Contact Quality       │
│  col3: Contact     col4: Market/Model          │
└───────────────────────────────────────────────┘

┌─ [MATCHUP EDGE TAB ONLY] ─────────────────────┐
│  Modifier %    HVY Score                       │
└───────────────────────────────────────────────┘
```

Section divider is mandatory. "MATCHUP EDGE TAB ONLY" controls must be visually separated from universe filters to prevent operator confusion about scope.

### 7.2 Control Density Rules

- Maximum 12 threshold controls visible simultaneously per engine TCC
- Group by signal type, not alphabetically
- Integer controls use integer steps; float controls use float steps
- No sliders — `st.number_input` only (native +/- buttons, keyboard entry)
- Labels match table column headers exactly

### 7.3 Forbidden Display Patterns

- Giant settings wall (>12 controls without section break)
- Unlabeled section breaks (visual dividers require text labels)
- Sliders for fine-grained float controls (precision loss, no keyboard entry)
- Preset buttons without help text
- Controls that affect JIG placed in MAIN TCC or vice versa
- Any control without a visible label and unit

---

## 8. Visibility Governance

### 8.1 The Show/Filter/Rank Distinction

Three distinct visibility operations. They must NOT be conflated:

| Operation | Definition | Allowed In |
|---|---|---|
| **Show/Hide** | Batter appears or does not appear | All modes except Full Slate All Players |
| **Filter** | Batter fails a threshold gate | MAIN, JIG filtered modes |
| **Rank/Highlight** | Batter visible but visually deprioritized | Full Slate All Players |

Full Slate All Players mode is **exclusively Rank/Highlight**. No batter is removed. Row background color changes; batter remains visible.

### 8.2 Pre-Lineup Pool vs Live Pool

MAIN operates two visibility layers:
- **Pre-Lineup Pool** — all model-scored batters, lineup state unknown or projected
- **Active Pool** — confirmed starters only (lineup badge ✓)

TCC filters apply to both pools simultaneously. Visibility split (Pre-Lineup vs Active) is a separate display governance layer, not a TCC function.

### 8.3 Visibility by Mode (Full Slate)

| Mode | Source Pool | TCC Filters | Behavior |
|---|---|---|---|
| All Players | `all_players` | Highlight only | All batters shown, qualifiers highlighted |
| Qualified | `_tac_ranked` | Active | Only TCC-passing batters shown |
| Elite Targets | `all_players` filtered barrel≥8% | Highlight only | Same as All Players, barrel-gated |

---

## 9. Cross-Engine Isolation Rules

These rules are **permanent and non-negotiable**.

### 9.1 Hard Isolation Rules

1. **No shared scoring** — MAIN composite score and JIG HVY modifier are computed independently and may never be merged, averaged, or combined into a single ranking
2. **No key cross-read** — MAIN reads only `tac_*` keys; JIG reads only `jig_tac_*` keys
3. **No formula inheritance** — a TCC preset for MAIN may not reference JIG thresholds and vice versa
4. **No shared filter function** — `_apply_tactical_filters()` (MAIN) and JIG's equivalent are separate functions. Common helper logic may live in `filter_controls.py` but application is engine-specific
5. **No shared model_prob** — JIG operates without model probability; any TCC control that exposes model_prob is MAIN-scoped only
6. **No contamination via Full Slate** — Full Slate All Players mode shows all batters from both engine pools but must never apply MAIN scoring to JIG picks or vice versa

### 9.2 Permitted Shared Components

| Component | Shared | Rationale |
|---|---|---|
| `render_filter_control()` | Yes | Pure widget renderer, no logic |
| `render_preset_bar()` | Yes | Pure UI renderer, no logic |
| Raw stat thresholds (Barrel, HH, etc.) | Yes — each engine reads its own namespaced key | Same vocabulary, different keys |
| Display color palette | Yes | Aesthetic consistency |
| Card skeleton HTML structure | Yes — already standardized in Sessions 38-39 | |
| Session_state key format | No — must stay namespaced | Collision prevention |

---

## 10. Runtime Safety Principles

### 10.1 Filter Application Safety

- Filters must never raise exceptions on empty pools — return empty list, not error
- All filter reads use `safe float coercion` with NaN/Inf guard (established in Session 15)
- `_apply_tactical_filters()` is cached by fingerprint `_tac_filter_fp` — skip on stable filter state (established in Session 41)
- Missing field values default to 0.0 in filter comparison — never cause KeyError

### 10.2 Preset Safety

- Preset application writes to session_state then calls `st.rerun()` only when values changed
- No preset may write to a key outside its engine's namespace
- Preset button keys are prefixed `_preset_{preset_key_ss}_{pk}` — stable, no collision with filter keys

### 10.3 TCC Render Safety

- TCC controls render before pick pools are consumed — filter state is always fresh for the current render cycle
- Session-state key `_tac_filter_fp` invalidates on slate_ts change — guarantees fresh filter on new data load
- Number inputs use `value=current` from session_state — never default to stale preset value after manual edit

---

## 11. Future Expansion Boundaries

### 11.1 What May Be Added

- New engines: add their own preset dict to `filter_controls.py`, their own namespaced keys, their own `_apply_*_filters()` function
- New filter fields: add to canonical vocabulary table (Section 2.1), add to engine presets, add to render block
- New presets for existing engines: add to appropriate preset dict in `filter_controls.py`
- New display modes for Full Slate: add to mode radio, add corresponding render function

### 11.2 What May NOT Be Added

- Unified scoring that spans engines
- A "Master" preset that sets filters across MAIN and JIG simultaneously
- Any TCC control that modifies model_prob, EV, or Edge values
- Event bus or observer pattern for cross-engine TCC state synchronization
- Auto-tuning or AI-driven preset suggestions (presets must remain transparent threshold bundles)
- A "Combined View" that merges MAIN and JIG ranked outputs into a single list

### 11.3 Deployment Engine Expansion (when authorized)

When a Deployment engine is added:
1. Add `DEPLOYMENT_PRESETS` to `filter_controls.py`
2. Use `dep_tac_` key namespace
3. Inherit raw stat filters only from MAIN vocabulary
4. Add market gate (EV, Edge, Model Prob) — same as MAIN, separate keys
5. Add confidence gate (not in MAIN) — new key `dep_tac_min_conf_gate`
6. Do NOT expose JIG matchup controls in Deployment TCC

---

## 12. Validation Standards

### 12.1 TCC Filter Validation Checklist

Before any TCC change ships:

- [ ] All new keys namespaced to correct engine prefix
- [ ] New keys added to engine's preset dict (at minimum with `0.0` default in base preset)
- [ ] `_apply_*_filters()` reads new key with safe float coercion
- [ ] New control renders in correct TCC section (Universe vs Matchup Edge)
- [ ] Preset bar does not overwrite cross-engine keys
- [ ] Full Slate All Players mode unaffected (no filter removal)

### 12.2 Engine Identity Validation

After any TCC change:

- [ ] MAIN picks still ranked by EV×0.4 + Edge×0.35 + Confidence×0.25 — unchanged
- [ ] JIG picks still ranked by HVY score descending — unchanged
- [ ] model_prob value in any pick row is identical before and after TCC filter change
- [ ] No JIG key read from MAIN's `_apply_tactical_filters()`
- [ ] No MAIN key read from JIG's filter application

---

## 13. Anti-Patterns & Forbidden Behaviors

### 13.1 Anti-Patterns

| Anti-Pattern | Why Forbidden |
|---|---|
| "Smart preset" that adjusts values based on model output | Presets are static threshold bundles; no dynamic logic |
| Sharing `_tac_ranked` between MAIN and JIG | Engine pools are separate; cross-sharing is contamination |
| Adding model_prob threshold to JIG TCC | JIG is raw-stat only; model_prob is MAIN intelligence |
| Exposing HVY modifier floor in MAIN's universe filters | HVY is matchup-only; belongs in Matchup Edge section |
| Preset button that sets keys for two engines | One preset, one engine, one namespace |
| Any number_input min_value > 0 for the base/default preset | Operational preset must always have 0.0 floors |
| Removing batters in Full Slate All Players mode | That mode is visibility-only, not qualification |

### 13.2 Contamination Risks

**Risk 1: Preset namespace leak**
If a preset dict accidentally includes keys from both `tac_` and `jig_tac_` namespaces, JIG filters will change when MAIN preset is applied. Guard: each preset dict's `values` block is validated against its engine's allowed key prefix.

**Risk 2: Filter fingerprint sharing**
If `_tac_filter_fp` incorporates JIG keys, JIG filter changes will invalidate MAIN's cached filter result. Guard: each engine's fingerprint tuple reads only its own namespace keys.

**Risk 3: Full Slate "All Players" mode accidentally applies TCC filters**
If `_render_full_slate_all_players()` reads `_tac_ranked` instead of `all_players`, the scene changes from a battlefield overview to a filtered view. Guard: All Players mode must source from `all_players` (or `scored_all` in JIG), never from a TCC-filtered pool.

**Risk 4: New filter added to shared vocabulary but wired to wrong apply function**
Example: `min_xslg` added to JIG TCC but the value is never read by `_apply_jig_filters()`. Guard: every new key must trace to a read in its engine's apply function before shipping.

### 13.3 Tactical Density Rules

The TCC must remain operable under game-day pressure (tight time window, multiple decisions):
- Critical controls (Barrel, EV, Edge) must be visible without scrolling
- Maximum 3 preset buttons per engine (operators can distinguish 3 postures; more creates decision paralysis)
- Preset bar always at top of TCC section
- Reset button always visible alongside preset buttons
- Section labels (UNIVERSE FILTERS / MATCHUP EDGE TAB ONLY) are never collapsed or hidden

---

## Appendix A: Existing Implementation Status

| Component | Status | Location |
|---|---|---|
| `render_filter_control()` | LIVE | `filter_controls.py` |
| `render_preset_bar()` | LIVE | `filter_controls.py` |
| `MAIN_PRESETS` (3 presets) | LIVE | `filter_controls.py` |
| `JIG_PRESETS` (3 presets) | LIVE | `filter_controls.py` |
| MAIN TCC 3-column layout | LIVE | `app.py` |
| MAIN TCC Universe/Matchup divider | LIVE | `app.py` (Session 34) |
| JIG TCC number_input controls | LIVE | `app.py` (Session 37) |
| Full Slate All Players mode | LIVE | `app.py` (Session 37) |
| Full Slate 3-mode radio | LIVE | `app.py` (Session 37) |
| `_tac_filter_fp` fingerprint cache | LIVE | `app.py` (Session 41) |

## Appendix B: Planned Additions (Not Yet Authorized)

| Component | Phase | Notes |
|---|---|---|
| Full Slate TCC (own preset bar) | Phase 3B | `fs_tac_` namespace, highlight-only behavior |
| Deployment engine TCC | Phase 4 | `dep_tac_` namespace, separate file |
| Tactical tag system (FASTBALL HUNTER, etc.) | Phase 2B+ | JIG-only, display annotation, not a filter |
| Game-command module layout (JIG) | Phase 2B | Three-panel pitcher/targets/conditions |

---

*End of doctrine document.*  
*Route: Obsidian (permanent storage) + draw.io (engine relationship diagram) + frontend-design (UI shell exploration)*

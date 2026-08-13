# Full Slate Intelligence Matrix (FSM)

**STATUS: LIVE — Production surface.**
File: `frontend/assets/js/full-slate-matrix.js` · Deployed via Vercel (`frontend/` repo root, static HTML + CDN React 18 + `@babel/standalone`). Not the Next.js prototype.

---

## Summary

The Full Slate Intelligence Matrix is the **primary MAIN-side operator board** — a dense, ranked table of every batter on today's slate with matchup intel, Statcast columns, filtering/sorting controls, and per-player detail modals. Data is supplied by the `window.SLATE_DATA` / `window.SLATE_GAMES` globals, which are populated at runtime from the `/api/slate` payload. The component is exported as `window.FullSlateMatrix` and mounted via `<script type="text/babel">`.

The FSM renders in two display modes: **GAME VIEW** (batters grouped under their game's park/weather/HR-factor header) and **PLAYER VIEW** (flat ranked list across all games). Both views share the same underlying ranked pool.

---

## Key Points

- Default order = canonical `model_tier_rank` (MAIN ranking). This order is invariant — sort and filter are view-level only and never reorder the model's ranking.
- Payload field units: `model_prob` is decimal 0–1; `hrprob` is ×100 (already a percentage); `true_matchup_score` is honest 0–100; `arsenal_edge_score` is 0–10; `arsenal_edge_confidence` is 0–1.
- Four data-gap definitions (`woba`, `whiff`, `swstr`, `pullbrl`) are excluded from the column picker via `FSM_PICKER_COLS`; they cannot be enabled without a real data source.
- Column preferences (order, visibility) are saved to `localStorage("fsmColPref")`, version-gated (`FSM_PREF_V = 4`).
- The component is fully self-contained — no shared React state, session state, or cache with Streamlit.

---

## Ordering & Ranking (INVARIANT)

**The FSM's default display order is the canonical `model_tier_rank` from the `/api/slate` payload (MAIN ranking). This is the authoritative sequence and must never be altered by any filter, sort toggle, or display preference.**

Implementation: `rows` arrive pre-ranked; `adjusted = rows.map(fsmAdjustRow)` preserves that order; `sorted0 = [...adjusted]` is the baseline. When `sortState === null` (the RANK default), `pool` is derived from `sorted0` directly — no reordering applied. Column sort (`sortState !== null`) reorders the _view_ only. Resetting to RANK (`setSortState(null)`) restores model_tier_rank order.

---

## The Matchup Cell

The `fsm-matchup` `<td>` is a clickable button that opens the Arsenal Edge Intel modal on tap. It contains:

| Sub-element | Field | Format |
|---|---|---|
| **TM Gauge** | `row.true_matchup_score` | Semicircular arc, fill = `score/100`, color from TM_BANDS |
| **HR PROB** | `row.hrprob` | `hrprob.toFixed(1) + "%"` — the model HR probability ×100 |
| **BATTER EDGE** | `row.arsenal_edge_score` | `Number(score).toFixed(1)` — 0–10 unsigned edge score |
| **SIGNAL** | `row.arsenal_edge_confidence` | `Math.round(confidence × 100) + "%"` |

**TM Gauge bands** (from `TM_BANDS` in code, operator-approved, do not rescale):

| Band   | TM Range | Color   |
|--------|----------|---------|
| ELITE  | ≥ 60     | `#4ade80` (green) |
| STRONG | 50–59    | `#86efac` (light green) |
| AVG    | 38–49    | `#fbbf24` (amber) |
| WEAK   | 25–37    | `#f97316` (orange) |
| COLD   | < 25     | `#ef4444` (red) |
| null   | —        | `#6b7872` (grey) |

The matchup cell contains **no matchup text, no key pitch label, and no arsenal_edge_label**. Those live exclusively in the Arsenal Edge Intel modal. The cell shows TM + HR PROB + BATTER EDGE + SIGNAL only.

Cross-reference: [[true-matchup-score]] for TM formula and invariants.

---

## Columns & Data

Column definitions live in `FSM_COLS` (array, `full-slate-matrix.js` lines 100–134). The full ordered set:

| Key | Head | Group | Direction | Notes |
|---|---|---|---|---|
| `odds` | ODDS | STATS | neutral | HR prop odds (American format) |
| `hr` | HR | STATS | higher | Season HR total |
| `barrel` | BARREL% | STATCAST | higher | Barrel rate |
| `xslg` | xSLG | STATS | higher | Expected slugging |
| `iso` | ISO | STATS | higher | Isolated power |
| `hh` | HH% | STATCAST | higher | Hard-hit rate (95+ mph) |
| `pullair` | PULLAIR% | STATCAST | higher | Pulled-air rate |
| `blast` | BLAST% | STATCAST | higher | Blast rate |
| `maxev` | MAX EV | STATCAST | higher | Max exit velocity |
| `squp` | SQUP% | STATCAST | higher | Squared-up rate |
| `ev` | EV | STATCAST | higher | Average exit velocity |
| `hrpa` | HR/PA | STATS | higher | HR per plate appearance (model output) |
| `sweet` | SS% | STATCAST | higher | Launch-angle sweet-spot rate |
| `la` | LA° | STATCAST | special | Launch angle (optimal ≈ 15°) |
| `slg` | SLG | STATS | higher | Slugging |
| `fast` | FAST% | STATCAST | higher | Fast-swing rate |
| `xwoba` | xwOBA | STATS | higher | Expected wOBA |
| `obp` | OBP | STATS | higher | On-base percentage |
| `avg` | AVG | STATS | higher | Batting average |
| `babip` | BABIP | STATS | higher | BABIP |
| `bbpct` | BB% | STATS | higher | Walk rate |
| `kpct` | K% | STRIKES | lower | Strikeout rate |
| `woba` | wOBA | STATS | higher | **DATA GAP — hidden by default** |
| `pa` | PA | STATS | neutral | Plate appearances (sample size) |
| `whiff` | WHIFF% | STRIKES | lower | **DATA GAP — hidden by default** |
| `swstr` | SWSTR% | STRIKES | lower | **DATA GAP — hidden by default** |
| `pullbrl` | PULLBRL% | STATCAST | higher | **DATA GAP — hidden by default** |
| `gb` | GB% | STATCAST | lower | Ground-ball rate |
| `fb` | FB% | STATCAST | higher | Fly-ball rate |
| `ld` | LD% | STATCAST | higher | Line-drive rate |
| `air` | AIR% | STATCAST | higher | Display-only derivation: `fb + ld`; null if either source is missing |
| `pull` | PULL% | STATCAST | higher | Pull rate |
| `center` | CENTER% | STATCAST | lower | Center rate |
| `oppo` | OPPO% | STATCAST | lower | Additive `/api/slate` passthrough of upstream `oppo_pct` |
| `hrfb` | HR/FB% | STATCAST | higher | HR per fly ball |
| `opphr` | OPP HR/9 | MATCHUP | higher | Opposing pitcher HR/9 (danger-flagged header) |

`FSM_PICKER_COLS` excludes `woba`, `whiff`, `swstr`, and `pullbrl`; no picker entries exist for these no-data fields. AvgDist, 300+, 350+, Bat Spd, Comp%, and 1st Pitch Swing also remain unavailable. `HR/FB%` is unchanged and remains a separate repair surface.

**Column manager**: the COLUMNS button opens a popover listing all columns with checkboxes (show/hide), ⓘ tooltip for stat description, and ▲/▼ reorder arrows. Columns are also drag-reorderable on desktop (drag from `<th>`, drop onto destination `<th>`). Order and visibility persist to `localStorage`.

The first 12 visible columns are always shown; columns at index ≥ 12 in the active set get class `fsm-cell--extra` and are hidden on mobile until the expand button is tapped (see Mobile section).

---

## Sort & Filter Controls

The `fsm-sortbar` renders two labeled groups in one bar: **SORT** and **FILTER**.

### SORT

**RANK button** (`setSortState(null)`): Restores the canonical model_tier_rank order. Active state = `!sortState`. This is a sort reset, not a filter — it does not hide any rows.

**Column sort** (double-click on any `<th>`): Calls `onSort(c.key)`, which sets `sortState = { key, dir: "desc" }` on first activation, then toggles `"desc"` ↔ `"asc"` on repeated clicks. Comparator is null-safe (`null → -Infinity`). Applies to the view pool only; underlying model_tier_rank is untouched.

### FILTER

**TM ≥60 toggle** (`selMetrics` contains `"tm"`): Hides rows where `true_matchup_score == null || true_matchup_score < 60`. Threshold = ELITE band floor. View-only — does not alter any model value.

**HR PROB ≥15% toggle** (`selMetrics` contains `"hrprob"`): Hides rows where `hrprob == null || hrprob < 15`. (`hrprob` is already ×100, so 15 = 15%.)

**AND intersection**: When both toggles are active, only rows passing both conditions are shown (`passMetric` checks each in sequence). The "dual-threat shortlist" on a weak slate may be empty — handled by the `fsm-metric-empty` empty state, not a bug.

The active filter description appears in the status bar note string: `"TM ≥60"`, `"HR PROB ≥15%"`, or both joined.

### Control layout (as of Aug 12 2026)

Controls are grouped into three labeled sections in the `fsm-sortbar`:

- **SORT & FILTER** — RANK button, column sort, TM ≥60 toggle, HR PROB ≥15% toggle
- **SCOPE** — ROLE multi-select toggles (see Roles section below)
- **GAMES** — GAME VIEW / PLAYER VIEW toggle; LIVE readout (relocated here from the top bar Aug 12)

The **COLUMNS** and **EDIT** controls moved to the top bar (Aug 12), no longer in the sortbar.

### PLAYER GROUP and FOCUS controls (removed Aug 12 2026)

**PLAYER GROUP** and **FOCUS** radio controls are **no longer rendered on the board**. They were removed in commit `4e9743b` (Aug 12). The underlying predicate functions remain in `full-slate-matrix.js` with state pinned to `"all"` / `"ALL"` — the rows they would filter are never excluded. They are preserved for possible future re-exposure (e.g. a strategy-mode toggle) but are currently dead UI.

Prior to removal the predicates were:
- **PLAYER GROUP**: All Players / Qualified (PA ≥ 100) / Elite Targets (tier ∈ {APEX, ELITE, EDGE})
- **FOCUS**: ALL / POWER (`barrel ≥ 4.5 || slg ≥ .470`) / CONTACT (`avg ≥ .255`) / MATCHUP (`quality ∈ {"ELITE", "STRONG"}`)

### ROLE filter (active)

**ROLE** (multi-select toggles): See Roles section. AND intersection — selects rows where every selected role flag is `true`.

All active filters compose as AND (every active filter must pass for a row to appear in `pool`).

---

## Roles

Four role badges may appear on a batter's tier cell (`fsm-tiercell__roles`), stacked vertically on desktop:

| Role | Class | Color | Qualification logic (from `fsmRoleTip`) |
|---|---|---|---|
| PRIME | `fsm-role-badge--prime` | `#1aff66` (green) | Survives every quality test: `barrel`, `xslg`, `hh`, `ev` all pass |
| EXPLOSIVE | `fsm-role-badge--explosive` | `#ff9f1a` (orange) | Slate-breaking upside: `maxev` + `barrel` |
| ADVANTAGE | `fsm-role-badge--advantage` | `#3b9eff` (blue) | Underpriced quality below top tier: `xslg` + `barrel` |
| WILDCARD | `fsm-role-badge--wildcard` | `#c77dff` (purple) | Elite trait: `maxev ≥ 116` OR `barrel ≥ 12` OR `xslg ≥ .520` OR `pullair ≥ 30` |

Roles are boolean flags on each row object (`row.prime`, `row.explosive`, `row.advantage`, `row.wildcard`). A batter may have multiple roles simultaneously.

**Role filter logic** (`passRole`): `selRoles.length === 0 || selRoles.every(id => r[id] === true)`. Every selected role must be true — AND intersection, not OR.

Role badge tooltips are dynamically generated with the batter's real qualifying field values at render time (`fsmRoleTip`).

---

## Mobile Card View

At `≤ 768px` portrait, CSS in `<style id="fsm-mobile-cards">` converts the table to stacked labeled-tile cards. Desktop (`> 768px`) and landscape are completely unaffected.

**Mobile scroll ownership**: At `≤ 768px`, `html` is the single vertical slate scroller. `.md-stage` and `.md-stage__body` use normal block flow with visible overflow, so the slate intelligence strips, Matrix, and full batter list all contribute to one document height. `.md-sticky-head` therefore remains pinned across the entire slate. Desktop keeps the height-constrained `.md-stage__body { overflow: auto; }` two-pane behavior; TCC retains its separate scoped body scroll.

**Card layout**: Each `tr.fsm-row` becomes `display: grid; grid-template-columns: repeat(6, 1fr)`. Structure:

- **Row 1 (header)**:
  - Cols 1–2: `fsm-tiercell` — tier badge icon + label (and role badges if present, in row-wrap layout on mobile)
  - Cols 3–5: `fsm-player` — team dot + player name + team/handedness meta
  - Col 6: `fsm-matchup` — TM gauge + HR PROB/BATTER EDGE/SIGNAL in compact form
- **Row 2+**: `fsm-cell` stat tiles, 6 per row, auto-flowing. Each tile label is rendered via CSS `::before { content: attr(data-label) }` using the column's `data-label` attribute. Heatmap bucket classes (`is-elite`, `is-strong`, etc.) still apply.

**Expand control**: The first 12 visible columns (`ci < 12`) are always shown. Columns at index ≥ 12 get `fsm-cell--extra` and are hidden (`display: none !important`) until the row's expand button is tapped. Expand button text: `+{Math.max(0, cols.length - 12)} MORE STATS`. On desktop the `fsm-expandcell` is `display: none`.

**Slip button**: Hidden on mobile (`fsm-cell--slip { display: none !important }`). No add-to-slip on mobile card view.

**Role badges on mobile**: The `fsm-tiercell__roles` container switches to `flex-direction: row; flex-wrap: wrap` on mobile (from column on desktop), so badges flow inline within the tier cell. _(Note: a CSS refinement for role badge clustering is present in `index.html` in the current working tree but the file has uncommitted modifications — do not treat that specific fix as a landed/committed feature until the operator commits it.)_

---

## Arsenal Edge Intel Modal

Clicking the **matchup cell** (`onPitch`) opens `FsmArsenalEdgeIntel` directly (modal type `"pitch"`). The batter card (`FsmBatterCard`, modal type `"batter"`) also has a "PITCH MIX ANALYSIS →" button that routes to it. Navigation between the two is via `setModal({ type: ... })`.

`FsmPitchMix` is preserved in `full-slate-matrix.js` but is **unrouted** — `FsmDetailModal` always dispatches `type === "pitch"` to `FsmArsenalEdgeIntel`. FsmPitchMix exists as a rollback surface only.

**Arsenal Edge Intel layout** (three panels, class `aei-grid`):

**Left — PITCHER ARSENAL** (`aei-panel--pitcher`):
- Pitcher name, hand, tier card
- Season stat chips: ERA, WHIP, K%, BB%, BARREL%, HH%
- Arsenal table (`aei-ars`): pitch code, pitch name, usage bar, velo, whiff%, HR/PA, K%, HH%. Rows sorted by usage desc. The key pitch (`arsenal_edge_key_pitch`) is highlighted with "HUNT THIS" badge (`aei-ars__row--key`).
- Data fetched on demand from `https://mlb-hr-api.fly.dev/api/pitcher-detail` (cached per `{pitcher_id}:{batter_id}:{batter_side}`).

**Center — ARSENAL EDGE VERDICT** (`aei-panel--verdict`):
- **ARSENAL EDGE** block: edge label (`arsenal_edge_label` or derived), edge score (`arsenal_edge_score`), confidence (`arsenal_edge_confidence ×100%`), key pitch name.
- **H2H HR SIGNAL** vcard: career head-to-head HR rate (PA, HR, BA, SLG, OPS). Trust label (NO DATA / VERY LOW / LOW / MODERATE). Small sample warning at < 10 PA.
- **OVERALL EXPLOIT CONFIDENCE** vcard: `arsenal_edge_confidence ×100%` with progress bar.
- **MODEL HR PROB** vcard: `row.hrprob.toFixed(1) + "%"` with key pitch and HR odds.
- **EDGE STACK**: five qualitative bands: H2H / PITCH EXPLOIT / BARREL PATH / HH RISK / DEPLOYMENT (derived display reads, not model outputs).

**Right — BATTER DAMAGE PROFILE** (`aei-panel--batter`):
- Batter name, handedness, tier card
- Stat chips: AVG, ISO, HR, K%, BARREL%, EV, xwOBA
- Batter vs pitch-type table (`aei-bt`): pitch code, PA, BA, SLG, HR, K%. Small sample (< 10 PA) flagged. Rows ordered by pitcher arsenal usage.

**Footer**: ← BATTER CARD button + ADD TO FANDUEL link (non-builder mode only). Escape key closes modal.

Cross-reference: [[design-pitch-mix-analysis]] for design doctrine.

---

## Pitch Mix Adjustment Toggle

The `PITCH MIX` toggle (`pmOn`, default ON) applies `fsmAdjustRow` to every row before rendering. When ON, rate and projection stats are recomputed against the specific pitcher the batter faces — using a platoon factor derived from `row.pitcher_hand` vs `row.bats` (switch hitters face the opposite hand). Season counting stats (HR, PA) are never adjusted.

Fields adjusted when ON: `avg`, `obp`, `slg`, `iso`, `xslg`, `woba`, `xwoba`, `babip`, `barrel`, `hh`, `hrfb`, `pullbrl`, `pullair`, `sweet`, `blast`, `squp`, `fast`, `ld`, `hrpa`, `hrprob`; inverted for `whiff`, `kpct`, `swstr`, `gb`; dampened for `ev`, `maxev`. Computed `odds` is also recalculated.

This is a display-layer adjustment only. It does not write to any model field and does not affect `model_tier_rank` or `true_matchup_score`.

---

## Add-to-Slip

The `SLIP` column (rightmost, `fsm-cell--slip`) contains `FsmSlipBtn` for each row. Clicking calls `window.__hrSlip.addLeg(...)` with player name, teamAbbr, pitcher_name, model_prob, tier, model_tier_rank, board (`main`/`jig`), hrprob, barrel, and hh. As of Aug 12 2026 (commit `d696a63`), `addLeg` also snapshots `true_matchup_score`, `jig_score`, `edge`, `arsenal_edge_score`, and `arsenal_edge_confidence` onto the client-side leg object at add time — these are additive, client-side only (no DB column, no POST field). New legs show these values in the pick card; legs added before this change show `"—"`. See [[ticket-slip-system]] for full leg snapshot doctrine.

Button states: `idle` (blue +) / `loading` (grey …) / `added` (green ✓) / `error` (red !) / `noauth` (amber ⚿). State sourced from `window.__hrSlip.getState().cardStatus[row.id || row.name]` via subscription.

The SLIP button is hidden on mobile (no room in card layout).

Cross-reference: [[ticket-slip-system]] for slip/leg architecture.

---

## FanDuel Quick-Search

The **tier badge** is a clickable button (non-builder mode). On click: opens `https://sportsbook.fanduel.com/search?q={encodedName}` in a new tab, copies the player name to clipboard, and shows a toast notification. This is a convenience shortcut only — it does not interact with any FSM data field.

---

## Protected / Rules

These are invariants. Do not modify without operator authorization and a doctrine update here.

1. **Payload field mapping is read-only.** `model_prob` (decimal 0–1), `hrprob` (×100), `true_matchup_score` (0–100), `arsenal_edge_score` (0–10), `arsenal_edge_confidence` (0–1). The matchup cell reads these; it never writes them, derives alternatives, or falls back to client-side recomputation.
2. **Ranking is inert to display actions.** Sort, filter, focus, group, pitch-mix, and column changes are VIEW-LEVEL ONLY. The canonical `model_tier_rank` order of the incoming rows must be preserved as the RANK default.
3. **MAIN/JIG separation.** When `isJigContext = true`, the FSM renders JIG tier labels (derived from `jigScore` via `fsmJigTierLabel`) and JIG rank counters. It never blends JIG signals into the MAIN matchup cell or MAIN tier badge. See [[main-jig-separation]].
4. **TM not rescaled.** `FsmTMGauge` arc fill = `score / 100` raw. No client-side stretching.
5. **FsmPitchMix stays unrouted** unless the operator explicitly authorizes restoring it as the pitch modal.
6. **No-data columns stay unavailable.** `FSM_PICKER_COLS` excludes `woba`, `whiff`, `swstr`, and `pullbrl`. Do not expose them—or add other deferred stats—without a real payload source.

---

## Cross-References

- [[true-matchup-score]] — TM formula, bands, filter thresholds
- [[ticket-slip-system]] — slip leg / add-to-slip architecture
- [[main-jig-separation]] — MAIN/JIG doctrine; when isJigContext applies
- [[tier-vocabulary]] — tier names, colors, HR-prob thresholds (FSM_TIERS / FSM_TIER_DESC)
- [[production-surface-truth]] — frontend surface map; confirms root `frontend/` is live Vercel, not Next.js
- [[design-pitch-mix-analysis]] — Arsenal Edge Intel design doctrine
- Source: `frontend/assets/js/full-slate-matrix.js` (component), `frontend/index.html` (CSS, mobile card style block `#fsm-mobile-cards`)
- API detail endpoint: `https://mlb-hr-api.fly.dev/api/pitcher-detail` (fetched on modal open, not from `/api/slate`)

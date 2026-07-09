Status: SPEC — Strategy section design mission (Fable 5). Scope A orchestration-only. Operator-gated before build. 2026-07-06.

> **STATUS UPDATE 2026-07-06 — Phase S1-a (snapshot capture) SHIPPED + VALIDATED.** The snapshot-wiring portion of Phase S1 (D1 migration 006, D2 API accept/store, `buildLegPayload` forward, capture on Full Slate / AEI / rail) is live — commit `f9f3aa4`, Fly API v73, Vercel deployed — and validated against real Supabase rows. §9 decisions are RESOLVED (recorded inline). See `wiki/log.md` 2026-07-06 entry.
>
> **STATUS UPDATE 2026-07-07 — Phase S2 SHIPPED.** Settlement resolver (D3, commit `705fd6a`) + ledger endpoint (D5, commit `f530567`) built, deployed, and run against real data — ~90 outcomes settled across 7 dates. See [[settlement-job-spec]] for the shipped record. The Strategy room, StrategyRail remediation, and Phase S3 (validated weighting / Strategy Score) remain pending.

# Strategy Section — Design Spec

Companion to [[strategy-section-seed]] and [[operator-pick-workflow]]. Constrained by [[main-jig-separation]] and [[supabase-schema]].

---

## 1. Purpose and Anchoring Principle

The Strategy section turns the operator's real morning workflow (TM sort → dot check → AEI → pitch-mix hunt) into a guided, on-board funnel, and — the higher-value half — closes the loop by capturing what each pick was based on, settling it against real outcomes, and reporting which signals actually predicted HRs.

**Anchoring principle (the honesty caveat):** the feedback loop has never run end-to-end. No one — operator, app, or model — currently knows which signals or combinations predict HRs. Therefore:

- Strategy **surfaces and labels** existing signals; it never asserts "best pick."
- Every piece of guidance is worded as transparent logic ("surfacing MISMATCH + high pitch-usage alignment"), never as an authoritative score.
- No fabricated or sample numbers dressed as real analytics. Empty states stay honest ("0 settled picks — nothing validated yet").
- Signal weighting is a **hypothesis** until the settle→learn loop validates it on real settled picks (operator threshold: n≥200 before any calibration claim).

**Scope A — orchestration only.** Strategy is like the TCC: it orchestrates what the operator sees; it computes no MAIN score, no JIG score, and no blend of the two. Ranking is always by a single operator-selected **existing** signal.

---

## 2. Audit Findings — What "Strategy" Is Today (root `frontend/`, live production)

Audited 2026-07-06. Root `frontend/` only (the deploying tree).

1. **Nav engine `strategy`** (`assets/js/0ead2d7a…js` `window.ENGINES`): amber `#ffb020`, wrench icon, non-expandable, desc "Build custom tactics, filters and models."
2. **Full room is a placeholder.** Selecting STRATEGY (or "VIEW ALL »") routes `Stage` to the generic `RadarScope` empty-scope screen (`cfdd4178…js:198–199`). There is no real Strategy room.
3. **StrategyRail** (`32ab40c7…js`, right rail, always visible): auto-cycles six hardcoded archetype cards (ELITE SPOT, POWER STACK, VALUE SPOT, PARK BOOST, HOT STREAK, PLATOON EDGE). Each card:
   - ranks live `LEADERBOARD_ROWS` (MAIN rows) by an **ad-hoc client-side blend** — e.g. POWER STACK: `barrel*1.6 + slg*8 + (ev−86)*0.6`; VALUE SPOT mixes tier bonus + hrprob + quality bonus. These are undocumented composites living in display code.
   - displays **"HR ENV SCORE"** computed as `min(9.9, 6 + avg_hrprob*0.17)` — a fabricated authoritative-looking number. This is the SAMPLE-analytics trap, already live.
   - deep-links FanDuel search and adds legs via `window.__hrSlip.requestAdd` with `board:'main'` hardcoded.
4. **`window.QUICK_PICKS`** (data file): hardcoded sample scores (9.6, 8.9…) — dormant sample data mirroring the rail archetypes. `LIVE_TARGETS` is also hardcoded sample data (separate surface, out of scope, noted only).
5. **Slip/ticket layer is real and reusable.** `slip-state.js` exposes `window.__hrSlip.requestAdd(row)` → `buildLegPayload()` → `POST /api/tickets/leg`. Payload today: `board, name, model_prob (decimal), tier, model_tier_rank, generated_at, ticket_id, player_id, team, pitcher`. Auth-gated; `user_id` stamped server-side.
6. **AEI is live** (`arsenal-edge-exploit.js`): fetches `/api/pitcher-detail` per matchup; computes a **view-metric-only** Arsenal Edge score with labels ARSENAL MISMATCH (≥8) / PITCH MIX EXPLOIT (≥6) / SOFT EDGE (≥4) / NEUTRAL; exposes per-pitch usage % and batter-vs-pitch-type stats. Header comment already declares it NOT wired into MAIN/JIG scoring — the correct pattern for Strategy to follow.
7. **`legs` table** is calibration-ready (`hr_result`, `settlement_status`, `settled_at` — all pending/NULL; no settlement job exists) but carries **no signal snapshot** beyond `model_prob`/`board`. Nothing logged today can later attribute an outcome to the dot state, AEI verdict, or pitch-mix alignment that motivated the pick.

**Audit verdict:** today's "Strategy" is a decorative rail with hidden blends and a fabricated score, in front of an empty room — while the plumbing Strategy actually needs (slip capture, AEI signals, calibration columns) already exists and is unused for learning. The build is mostly *remediation + wiring*, not invention.

---

## 3. Half 1 — Pick-Building (Guided Funnel)

### 3.1 Concept

The Strategy room is a **funnel board**: the operator's four-step morning check rendered as an explicit, visible pipeline. Strategy's identity is the **advisor that quotes, never computes**: every signal it shows keeps its source engine's color and label (MAIN red `#ff3344`, JIG cyan `#00d9ff`, AEI's own verdict colors), framed in Strategy amber `#ffb020` chrome. The visual rule *is* the doctrine rule — amber never tints a red or cyan number, because Strategy never touches either engine's math.

### 3.2 Lane selection — MAIN and JIG never merge

The room opens on a **lane switch**: `[ MAIN LANE ]  [ JIG LANE ]` (red / cyan segmented control, amber frame). One lane active at a time.

- MAIN lane reads `LEADERBOARD_ROWS`; JIG lane reads `LEADERBOARD_ROWS_JIG`.
- Filters, sort options, and candidate lists are per-lane. No screen ever shows a single ranked list containing both lanes' candidates.
- JIG lane ranks by `jigScore` (or other JIG-legitimate signals); `row.tier` in JIG lane displays as contextual MAIN-probability info only, per accepted Option A doctrine.
- The cross-ticket "all-different players" question (operator flag) is surfaced as a **notice**, not a rule: if a player already on the MAIN ticket ranks top of the JIG lane, Strategy shows a neutral chip "ALSO ON MAIN TICKET" and lets the operator decide. No EV comparison across lanes is computed.

### 3.3 The guided funnel (per lane)

Encodes the operator workflow doctrine verbatim, as four gates. Layout (desktop):

```
┌─ STRATEGY ─ MAIN LANE ──────────────────────────── amber chrome ─┐
│ SLATE FRAME  (tertiary strip): parks by hrFactor · weather ·     │
│  count of ELITE/EDGE rows — labeled "ENVIRONMENT — CONTEXT ONLY" │
├──────────────────────────────────────────────────────────────────┤
│ RANK BY: [ TM ▾ ]        (operator-selectable existing signal)   │
│                                                                  │
│  CANDIDATE ROW (one per player, sorted by chosen signal)         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ SCHWARBER  PHI   TM 87 (red)   ●green    [FUNNEL ▸]  [+]   │  │
│  │  gate trail:  TM ✓ · DOT ✓ · AEI: MISMATCH · MIX: 45% FF ✓ │  │
│  └────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│ FUNNEL DETAIL (opens per candidate — the 4 gates, in order)      │
│  1 TM / HR PROB   — headline signal, source-colored              │
│  2 MATCHUP DOT    — batter-threat axis state                     │
│  3 AEI VERDICT    — matchup-specific arsenal read (MISMATCH…)    │
│     season grade shown SMALL + labeled "SEASON — not this AB"    │
│  4 PITCH-MIX ALIGNMENT — pitcher's most-thrown pitch usage% ×    │
│     batter HR/SLG vs that pitch type. Labeled "HYPOTHESIS —      │
│     unvalidated" until the ledger earns it.                      │
│  H2H: shown LAST, de-emphasized, "n PA — NOT PREDICTIVE" if n<X  │
└──────────────────────────────────────────────────────────────────┘
```

Gate semantics:

- **Gates are checkpoints, not filters.** A candidate failing a gate is dimmed, never hidden — the operator can always override (the Caminero-vs-Schlittler lesson: season-TOUGH ≠ bad matchup).
- **Gate 3 fixes the TOUGH bypass by hierarchy:** the matchup-specific AEI verdict is the large element; the season pitcher grade is small, secondary, and scope-labeled ("SEASON GRADE"). Aligned with the queued AEI relabel pass.
- **Gate 4 is the hypothesized strongest "why"** per the seed. It is flagged with a persistent `HYPOTHESIS` micro-label; the label is removed only when Half 2's ledger shows earned data (and even then, only reworded to the measured stat, e.g. "hit 31% over 87 settled picks").
- **H2H is structurally last and small.** When PA below a small-sample threshold, it renders muted with the existing "NOT PREDICTIVE" language and cannot be the rank signal.

### 3.4 Ranking — operator-selectable existing signal only

`RANK BY` dropdown per lane. MAIN lane: TM, model_prob/hrprob, barrel, EV, hard-hit, xwOBA, HR/PA (the existing `SORT_OPTIONS` set minus JIG Score). JIG lane: jigScore first, plus the tactical-legitimate columns. There is **no "Strategy" option in the dropdown** — no composite exists to rank by. The selected key is recorded into the pick snapshot (§5) so the ledger can later report hit-rate by ranking method.

### 3.5 Role slots

After 4 funnel picks per lane, a **ROLE STRIP** guides PRIME / EXPLOSIVE / ADVANTAGE / WILDCARD slots per the operator doctrine, including the PRIME fallback rule (if all PRIME-labeled players are taken, suggest an unlabeled APEX/ELITE with high TM). Role suggestions run the same funnel display with a visibly lower bar-marker; a genuinely failing matchup is dimmed even for a $1 role slot.

### 3.6 Slip integration — reuse, don't rebuild

Adding from Strategy calls the existing `window.__hrSlip.requestAdd(row)` with the normalized row shape already used by every other surface, with two changes:

1. `board` is set from the **active lane** (`'main'` or `'jig'`), never hardcoded.
2. The row carries the pick-time signal snapshot (§5), which `buildLegPayload` forwards.

`model_prob` integrity rule unchanged: always the decimal `row.model_prob`, never `hrprob×100`, never `jigScore`.

### 3.7 StrategyRail remediation (existing surface)

The rail keeps its role as a compact teaser for the Strategy room, but must be brought under the honesty rules:

- **Remove the fabricated "HR ENV SCORE."** Replace with the real headline signal of the card's top player (e.g. "TOP TM 87"), source-colored.
- **Replace hidden rank blends** with single-signal ranks (ELITE SPOT → hrprob; HOT STREAK → barrel; PARK BOOST → park hrFactor; etc.) or retire archetypes that only exist as blends (POWER STACK, VALUE SPOT as currently formulated). Each card states its rank signal in the tag line.
- `board` on slip adds follows the rows' actual source.
- Retire the dormant `window.QUICK_PICKS` sample constants when the rail is remediated.

### 3.8 Visual doctrine

- **Accent:** Strategy amber `#ffb020` (already assigned in `ENGINES`) for chrome, gate trail, lane frame. Restrained glow (`#ffb02026`-class) per HUD doctrine.
- **Engine colors are quoted, never blended:** TM/model numbers in MAIN red context, jigScore in cyan, AEI verdicts in AEI's own scale. Amber never colors a signal value.
- **Signature element:** the **gate trail** — the four-step funnel state rendered inline on every candidate row (`TM ✓ · DOT ✓ · AEI: MISMATCH · MIX ✓`). It is the operator's own workflow made legible, and it doubles as the snapshot preview of what will be logged.
- **Scope labels everywhere** (per operator-pick-workflow data-reliance doctrine): every stat chip carries SEASON / MATCHUP / H2H scope; palette-collision and signal-scope UX rules apply.
- Typography, spacing, dividers follow the existing room components (`RoomHead`, `md-room` chrome); no new visual language.

---

## 4. Half 2 — Settle → Learn (the highest-value half)

### 4.1 Loop overview

```
pick added (Half 1) ──▶ legs row + signal_snapshot (pending)
game completes ──▶ SETTLEMENT JOB: outcome ingestion (MLB Stats API)
                    sets hr_result / settlement_status / settled_at
settled legs ──▶ LEDGER: hit-rate by signal bucket, per lane
ledger ──▶ operator reads earned evidence ──▶ (much later, operator-
            authorized) validated weighting / Strategy Score doctrine
```

### 4.2 Settlement (backend — Phase D dependency)

A daily settlement job (natural home: `api/cron.py` sibling task or `scripts/ops/`) that, for each `legs` row with `settlement_status='pending'` and `leg_date` in the past:

1. Resolves the player's game(s) on `leg_date` via MLB Stats API box scores.
2. Sets `hr_result` (1 = hit ≥1 HR, 0 = no HR), `settlement_status='settled'`, `settled_at`.
3. Marks `'void'` for postponed/DNP/no-lineup cases (void rules need operator sign-off — open question §9).

Attribution is already per-user (`tickets.user_id` from JWT). `fd_deployed` (was the pick actually placed at the book) is flagged in the schema doc as separate future work; the ledger must distinguish "logged" from "deployed" once it exists — until then it reports on logged picks and says so.

### 4.3 The Ledger (Strategy room, second tab)

A `LEDGER` view inside the Strategy room: `[ FUNNEL ]  [ LEDGER ]`.

- **Honest empty state (day one):** "0 settled picks. Nothing here is validated yet. Every funnel weighting is a hypothesis until this page fills." No sample charts, no placeholder percentages, ever.
- **Per-lane grading, never merged:** MAIN legs and JIG legs are graded and displayed separately (`legs.board` is the partition key). A combined view is a doctrine change, not a UI option.
- **Earned rows only, with n shown:** e.g. "AEI MISMATCH + top-pitch alignment: 9/24 (38%) over 24 settled picks — small sample." Buckets come from the snapshot (§5): AEI verdict, alignment flag, dot state, rank signal used, role slot, environment band, tier.
- **Threshold gating:** below the operator's n≥200 rule, every stat carries a `SMALL SAMPLE` band and the page header states that no calibration or threshold change may be made from it. The ledger *reports*; it never auto-tunes anything.
- **Calibration triad respected:** model-calibration analysis (model_prob vs hr_result) is the existing backtest/calibration domain; the ledger links to it conceptually but Strategy does not recompute engine calibration.

### 4.4 Dependency list (Half 2 blockers)

| # | Dependency | Layer | Status |
|---|---|---|---|
| D1 | `legs.signal_snapshot` column (jsonb) — migration 006 | Supabase | ✅ SHIPPED 2026-07-06 (`f9f3aa4`) |
| D2 | API accepts + stores snapshot on `POST /api/tickets/leg` | FastAPI | ✅ SHIPPED 2026-07-06 (`f9f3aa4`) |
| D3 | Settlement job (outcome ingestion → hr_result) | cron/ops | ✅ SHIPPED 2026-07-07 (`705fd6a`) — `api/settle_legs.py`; ~90 outcomes settled. Cron automation still deferred (manual `--commit` only) |
| D4 | Void/DNP settlement rules | doctrine | ✅ RESOLVED (§9 Q4) — ≥1 PA settles; else void, `hr_result` stays NULL |
| D5 | Ledger read endpoint (settled legs + snapshots, per user) | FastAPI | ✅ SHIPPED 2026-07-07 (`f530567`) — `GET /api/ledger`, per-lane, v1 buckets |
| D6 | `fd_deployed` flag (logged vs actually-bet distinction) | schema | separate future work (per schema doc) |
| D7 | Market odds on legs (`market_odds_american`/`market_prob` currently NULL) — needed for EV-grading, not for hit-rate grading | API | future |

### 4.5 The earned endpoint

Only after real settled volume exists can the operator authorize a validated weighting — up to and including a composite "Strategy Score." That composite is **explicitly out of scope here** (§8); Half 2's job is to make it *earnable*.

---

## 5. Pick-Time Signal Snapshot (the bridge)

**Rule: every leg added anywhere on the board carries the signal state that was on screen when the operator picked** — otherwise Half 2 can never attribute outcomes to signals. Captured client-side at `requestAdd` time, stored as `legs.signal_snapshot` (jsonb, additive column; existing typed columns unchanged).

Proposed snapshot shape (fields nullable — capture what the surface had; never fabricate):

```json
{
  "snapshot_version": 1,
  "surface": "strategy-funnel | strategy-rail | full-slate | aei | jig-command | ...",
  "lane": "main | jig",
  "rank_signal_used": "tm | model_prob | jigScore | barrel | ...",
  "tm_score": 87,
  "hrprob": 6.1,
  "jig_score": null,
  "tier": "ELITE",
  "dot_state": "green | yellow | red | null",
  "aei": {
    "score": 8.4,
    "verdict": "ARSENAL MISMATCH",
    "season_pitcher_grade": "TOUGH",
    "top_pitch": { "type": "FF", "usage_pct": 45 },
    "batter_vs_top_pitch": { "hr": 6, "slg": 0.610 },
    "alignment": true
  },
  "h2h": { "pa": 3, "flagged_not_predictive": true },
  "environment": { "park_hr_factor": 1.12, "temp_f": 88, "wind": "out" },
  "role_slot": "PRIME | EXPLOSIVE | ADVANTAGE | WILDCARD | null",
  "funnel_gates": { "tm": true, "dot": true, "aei": true, "mix": true },
  "generated_at": "<SLATE_GENERATED_AT>"
}
```

Notes:

- `model_prob` and `board` stay as the existing typed columns (calibration triad untouched); the snapshot duplicates nothing it doesn't need to and never substitutes for `model_prob`.
- The snapshot **records** signals; it contains no computed composite. `alignment` is a boolean derived from displayed values (top-usage pitch is one the batter shows HR/SLG strength against) — a labeled flag, not a score. Exact threshold for "alignment=true" is an open question (§9).
- Non-Strategy surfaces (Full Slate, AEI card, rail) should populate the subset they display; `surface` disambiguates. Versioned so the shape can grow.

---

## 6. Phasing

**Phase S1 — buildable now (frontend + one small migration/API change):**
- Strategy room (funnel + lane switch + role strip), replacing the `RadarScope` placeholder for `engineId === "strategy"`. ⚠ Touches the `Stage` routing branch — routing is a protected zone; this spec's approval must explicitly cover that one branch. *(Still pending; routing change approved per §9 Q3.)*
- StrategyRail remediation (§3.7). *(Still pending.)*
- ✅ **Snapshot capture wiring — SHIPPED + VALIDATED 2026-07-06** (Phase S1-a): `legs.signal_snapshot` migration 006 (D1), API accept/store with 16KB cap, absent=NULL (D2), `buildLegPayload` extension, capture on Full Slate / AEI AeeCard / rail (`fsmBuildSnapshot`). Commit `f9f3aa4`, Fly v73. Validated on real Supabase rows (Caglianone, Schwarber — populated snapshots, `model_prob` decimal intact). Scope note: hr-threat-zone, escalation-feed, command-tab, and the leaderboard FD link do NOT attach snapshots (NULL by design, per packet scope); the FSM AEI modal has no slip button so its richer signals are not yet captured; the rail snapshot records the displayed HR ENV SCORE as-shown pending rail remediation.
- Ledger tab shipped in its honest empty state (reads nothing until settled data exists). *(Still pending — ships with the Strategy room.)*

**Phase S2 — ✅ SHIPPED 2026-07-07:**
- ✅ Settlement job + outcome ingestion (D3) with void rules (D4) — `api/settle_legs.py`, commit `705fd6a`; backlog settled (~90 outcomes / 7 dates). Cron automation deferred (manual `--commit` only).
- ✅ Ledger read endpoint (D5) and live ledger buckets — `GET /api/ledger`, commit `f530567`, validated on real settled data.
- `fd_deployed` (D6) and market-odds sourcing (D7) — still future refinements.

**Phase S3 — earned, operator-gated, out of scope:** validated weighting / Strategy Score doctrine (§8).

---

## 7. Blast Radius (everything a build would touch)

| Surface | Change | Risk flags |
|---|---|---|
| `frontend/assets/js/cfdd4178…js` (Stage) | new branch: strategy room instead of RadarScope | **routing = protected zone; explicit authorization required** |
| new `frontend/assets/js/strategy-room.js` (+ index.html script tag) | new component bundle | net-new surface |
| `frontend/assets/js/32ab40c7…js` (StrategyRail) | remove fabricated score, single-signal ranks, board from source, snapshot | live production rail |
| `frontend/assets/js/0ead2d7a…js` (data) | retire `QUICK_PICKS` constants; possibly `strategy` engine desc text | low |
| `frontend/assets/js/slip-state.js` | `buildLegPayload` forwards `signal_snapshot` | slip layer — leg payload integrity rule must be re-verified |
| `frontend/assets/js/arsenal-edge-exploit.js` | expose displayed AEI values on the row/add path for snapshot | AEI stays view-metric-only |
| `mlb_hr_engine_v4/api/main.py` (leg endpoint) | accept/store `signal_snapshot` | API contract |
| `mlb_hr_engine_v4/supabase/` migration 006 | `legs.signal_snapshot jsonb` | additive only |
| `api/cron.py` or `scripts/ops/` | settlement job (Phase S2) | new backend job |
| Wiki | this spec, supabase-schema.md update, operator-pick-workflow cross-ref, main-jig-separation cross-ref | doc gate |

**Not touched:** `config.py`, `pipeline.py`, engine/ scoring, MAIN λ, JIG jigScore, filters in either engine, Streamlit surfaces, `mlb_hr_engine_v4/frontend/` (dead prototype).

---

## 8. Explicit Out-of-Scope: the "Strategy Score" composite

A single blended pick-quality score (MAIN + JIG + AEI + environment) is the **named, earned endpoint** of this program — and it is out of scope until:

1. The settle→learn loop has run end-to-end on real picks (n≥200 settled minimum, per operator rule);
2. The ledger shows which signal combinations actually predict;
3. The operator explicitly authorizes a doctrine change to [[main-jig-separation]] (invariant #5: no hidden blending; any blend must be explicit, documented, operator-authorized).

This spec deliberately does **not** design its formula, inputs, or weighting. Naming it here is a roadmap marker, not a license.

---

## 9. Open Questions — ALL RESOLVED (operator decisions recorded 2026-07-06)

All seven questions were decided by the operator on 2026-07-06. Do not re-litigate; a change to any of these is a new operator decision, not a reopened question.

1. **Phase S1 snapshot wiring — RESOLVED: AUTHORIZED + SHIPPED.** Migration D1/D2 + capture built, deployed, and validated 2026-07-06 (commit `f9f3aa4`, Fly v73). See status update at top and §6.
2. **StrategyRail remediation depth — RESOLVED: retire the blend-only archetypes** (POWER STACK, VALUE SPOT as currently formulated) rather than reformulate them. Remediation itself is a later packet.
3. **Routing authorization — RESOLVED: APPROVED** for the one `Stage` branch change (RadarScope → Strategy room) when the room build happens. Approval is scoped to that single branch.
4. **Void/settlement rules (D4) — RESOLVED: ≥1 PA settles the leg (hr_result 0 or 1); otherwise void.** Covers DNP, postponement, and no-lineup cases uniformly.
5. **`alignment` flag definition — RESOLVED:** `alignment=true` when the pitcher's top-usage pitch is in the batter's top-2 pitch types by SLG, with ≥10 PA vs that pitch type.
6. **Cross-ticket all-different rule — RESOLVED: neutral notice.** The "ALSO ON MAIN TICKET" chip with no recommendation either way is the posture until the ledger has data.
7. **H2H small-sample threshold — RESOLVED: <10 PA** triggers the de-emphasis / "NOT PREDICTIVE" treatment.

---

## 10. Pre-Migration History — Streamlit STRATEGY Room

Recovered 2026-07-08. Source: `git show 8d6843c:mlb_hr_engine_v4/strategies_ui.py` (fullest historical version, before commit `6be9d45` stripped ~1,552 lines).

### 10.1 What it was

STRATEGY was a real, working Streamlit feature — an "Advanced Strategies" workspace with **21 strategy modes**:

Stars Aligned, Multi-Edge Confirmation, Player Rankings, Confidence Rankings, Power Profile Parlays, Pitcher Target Parlays, xStats Regression, Short Rest Pitcher Target, Platoon Advantage, Hot Streak, Park Monster, Weather Boost, Correlation Parlays, Team Stacks, Lineup Heart, Value Bomb, Parlays, Long Shot Value, Same-Game Builder, Hedge Calculator, Progressive Staking.

### 10.2 Key features

- **Parlay builders:** 2–3 leg construction; EV = model_prob × combined American odds; diversity rule (team stacks, same-pitcher, same-game, park/weather/platoon/streak groupings).
- **Controls:** Min Edge% slider, Min Confidence slider, strategy-mode selectbox, expander detail panels.
- **Strategy cards:** EV / model_prob / odds / correlation / confidence displayed per pick; FD slip actions wired.
- **Per-strategy P&L tracking:** win/loss/ROI logged per strategy mode — this ledger ties directly into the current settlement/calibration loop (the same signal attribution problem Half 2 of this spec solves via `legs.signal_snapshot` → settlement → ledger buckets).

### 10.3 Code locations

| Surface | Location |
|---------|---------|
| Fullest historical version | `git show 8d6843c:mlb_hr_engine_v4/strategies_ui.py` (pre-strip) |
| Surviving UI stub | `mlb_hr_engine_v4/strategies_ui.py` (post-`6be9d45`, ~1,552 lines removed) |
| Strategy definitions | `mlb_hr_engine_v4/strategies/` |
| P&L tracker | `mlb_hr_engine_v4/tracking/strategy_log.py` |

### 10.4 Reuse map

The Python analyzers (EV math, odds conversion, parlay probability, tactical groupings) and `strategy_log.py` P&L tracking are **largely portable as backend** — they compute over real model outputs and have no Streamlit dependency. The surface to rebuild is the UI layer only (selectbox/slider/expander/dataframe → React components matching current visual doctrine).

### 10.5 Rebuild approach (recommended phasing)

**Phase 1:** Rebuild the core STRATEGY room UI (funnel + lane switch per §3–§3.5) and wire it to the surviving Python analyzers for EV/parlay math. Replace the `RadarScope` placeholder (routing authorization already granted per §9 Q3).

**Phase 2:** Quarantine and fix the fabricated "HR ENV SCORE" composites in the current StrategyRail (§3.7). Make the rail a teaser using single real signals only — no hidden blends.

**Phase 3:** Fold in Betting Analyst Agents + slate export, kept NON-AUTHORITATIVE until the settled-ledger volume (n≥200 operator rule) validates any weighting claim.

### 10.6 Durable architecture decisions

- **STRATEGY stays separate from COMMAND.** COMMAND = overview/orchestration (read-only operator situational awareness). STRATEGY = build/structure/ledger room (pick construction + outcome attribution). Do not merge these rooms.
- **Do NOT 1:1 port the old Streamlit UI.** The 21-mode selectbox pattern worked for Streamlit; the React rebuild should reimagine the UX around the funnel + lane doctrine (§3), not replicate the old tabs and expanders.
- **Old per-strategy P&L connects to the current ledger.** The per-strategy win/loss tracking from the pre-migration Streamlit surface is the same attribution problem Half 2 (§4) is solving. Recovering historical `strategy_log` data is a potential backfill input once the settlement loop has real settled volume.

---

## 11. STRATEGY Port Reference — Recovered Logic Map

Recovered 2026-07-09. Source: `mlb_hr_engine_v4/strategies_ui.py` current remnant; `git show 8d6843c:mlb_hr_engine_v4/strategies_ui.py` fullest pre-strip version before commit `6be9d45` removed ~1,126 lines from that file; `mlb_hr_engine_v4/strategies/`; `mlb_hr_engine_v4/tracking/strategy_log.py`.

### 11.1 Reusable math core — lift as pure logic

- American ↔ decimal conversion: `+150 -> 2.50`; `-120 -> 1 + 100/120`; zero/fallback path returns `1.01`.
- Parlay decimal odds = product of each leg's decimal odds.
- Independent parlay probability = product of each leg's `model_prob`.
- EV = `decimal_odds * probability - 1`; `ev_pct = EV * 100`.
- Diversity rule (`_diverse_top`): each player can appear in at most one returned slip.
- Hedge math (`calculate_hedge_bet`): stake sizing and guaranteed-outcome math; pure, liftable.

### 11.2 Port verdicts by function family

- **LIFT — pure and real:** odds helpers (`_ato_d` / `_dta`; consolidate duplicates), `_diverse_top`, `calculate_hedge_bet`.
- **ADAPT — logic useful, strip Streamlit/cache/session state:** power, park, and pitcher-target parlay builders; `find_correlated_parlays`; `build_team_stacks` / `evaluate_stack`. Their boost and adjusted-probability paths must be quarantined until ledger/calibration validation.
- **REBUILD as transparent filters, not composite scores:** `stars_aligned` becomes a checklist; `multi_edge` becomes boolean factor confirmation.
- **OPTIONAL modules:** staking systems (Kelly/Fibonacci/D'Alembert/Oscar/streak-adjusted bankroll logic), `value_decay` / CLV logic (requires line history), arbitrage logic (requires multi-book Yes/No data; keep dormant until sourced).
- **DROP / REBUILD:** `tab_advanced_strategies`, all Streamlit widgets, `st.session_state` FD slip behavior, and local CSV tracking.

### 11.3 Data availability

The current pipeline still emits most old STRATEGY inputs from canonical backend rows: `model_prob`, `best_american`, `fanduel_american`, `ev_pct`, `edge_pct`, `barrel_pct`, `exit_velo`, `gb_pct`, `park_factor`, `pitcher_factor`, `pitcher_hr9`, `pitcher_days_rest`, `weather_factor`, `platoon_factor`, `streak_factor`, `short_form_hr`, `short_form_pa`, `xslg`, `actual_slg`, `xslg_diff`, and `lineup_spot`.

Risk is **API exposure**, not backend availability. The rebuild should expose a typed STRATEGY payload from canonical pipeline rows. Do not recompute STRATEGY analysis in React from partial frontend fields.

### 11.4 Honesty audit — signal-honesty doctrine

**Real and safe to show as filters/checklists:** `xslg_diff`, `xslg`, `actual_slg`, `park_factor`, `pitcher_factor`, `pitcher_hr9`, `pitcher_days_rest`, `weather_factor`, `platoon_factor`, `streak_factor`, `short_form_hr`, `short_form_pa`, `model_prob`, `ev_pct`, `edge_pct`, and odds.

**Composite / quarantine unless calibration- or ledger-validated:** `power_score`, `alignment_score`, `_edge_product`, correlation multipliers, `team_explosion_factor`, lineup-heart boost, short-rest `rest_boost`, park/weather/platoon/streak adjusted probabilities, market `efficiency_score`, and the current StrategyRail `HR ENV SCORE` fabricated blend.

Rule: show factor evidence and explain qualification. Never present blended scores as model truth unless validated. This subsumes the fabricated-blend remediation backlog item.

### 11.5 Tracking — use the ledger, not CSV

Old `strategy_log.py` schema: `date`, `strategy`, `player_name`, `team`, `american_odds`, `model_prob_pct`, `ev_pct`, `bet_dollars`, `hr_result`, `profit_loss`.

Old behavior: dedupe by date + strategy + player; settle by HR outcome; aggregate per-strategy picks, wins, losses, P&L, ROI, pending count, and last pick date.

Verdict: do **not** revive CSV storage. Add `strategy_key` / `source_strategy` to leg metadata or `signal_snapshot`, then compute per-strategy P&L/ROI from the current tickets/legs ledger. The old tracker is a reporting spec, not storage architecture.

### 11.6 What `6be9d45` removed and what to recover

**Recover:** xStats Regression, Long Shot Value, single-factor filters (Platoon / Weather / Hot / Park), Same-Game Builder structure, Hedge and Staking calculators.

**Recover with caution — quarantine boosts:** Short Rest, Team Stacks, Lineup Heart, Same-Game correlation boosts, adjusted parlay probabilities.

**Drop:** Streamlit widgets, session-state FD slip behavior, CSV tracking, decorative parlay UI.

### 11.7 Recommended phased rebuild

**P1 backend utilities:** canonical strategy-math module for odds, EV, parlay probability, and diversity; typed outputs carrying `strategy_key`, `legs`, `source_fields`, `base_prob`, `decimal_odds`, `ev_pct`, and `honesty_level`.

**P2 safe analyzers:** xStats Regression, Long Shot Value, Player Edge, Confidence, and Multi-Edge as transparent filters using raw factors and thresholds only. No adjusted probabilities.

**P3 parlay builders:** Power, Pitcher Target, Park, Correlation, and Team Stack. Keep `base_prob` + raw EV; put boosted probabilities behind explicit `heuristic_adjusted_prob` naming or quarantine them.

**P4 ledger integration:** strategy attribution in leg metadata; per-strategy P&L/ROI from settled legs.

**P5 agents + export:** Betting Analyst Agents consume typed strategy outputs, not hidden recomputed scores. Slate export includes each strategy's qualifying rows, source fields, formulas, and honesty status.

Direction: **reimagine, not 1:1 port.** Old backend logic is useful; old Streamlit UI and silent composites do not meet signal-honesty doctrine. Keep STRATEGY separate from COMMAND.

---

## Cross-refs

- [[strategy-section-seed]] — reasoning framework + honesty caveat (source of the anchoring principle)
- [[operator-pick-workflow]] — the funnel this spec encodes
- doctrine/main-jig-separation.md — invariants honored throughout
- architecture/supabase-schema.md — tickets/legs/picks; calibration triad; snapshot column target
- AEI relabel pass (queued) — Gate 3 hierarchy assumes it lands

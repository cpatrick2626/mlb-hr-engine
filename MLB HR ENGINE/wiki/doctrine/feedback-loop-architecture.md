# Feedback Loop Architecture Blueprint

Status: DESIGN / PLANNING ONLY. Risk: LOW (doctrine doc; no app/engine/pipeline/schema changes).
Room: MAIN SKILLS

Cross-references: [[wiki/doctrine/design-expert-agent-layer|design-expert-agent-layer]] · [[wiki/projects/ticket-data-capture-phase1-architecture|ticket-data-capture-phase1-architecture]] · [[wiki/doctrine/main-jig-separation|main-jig-separation]] · [[wiki/doctrine/ticket-roles|ticket-roles]] · [[wiki/doctrine/tracking-consolidation-plan|tracking-consolidation-plan]]

---

## Governing Principles

These four principles govern every loop in this system. Read before the catalog.

**1. Loops are DESIGNED NOW, DORMANT UNTIL FUELED, ACTIVATED AT DATA THRESHOLDS.**
A feedback loop is only as real as the settled-outcome data feeding it. Running a loop before its data exists means learning from noise and emitting confident garbage — the worst failure mode for a "self-improving" system. Every loop carries both its ideal design AND its realistic activation threshold.

**2. Every loop entry specifies both design and threshold.**
No loop is documented without an activation gate. A threshold of "n/a" is a red flag, not a feature.

**3. Agents own loops, not data.**
Agents READ across grains. Agents WRITE only to their own analysis output tables. Agents NEVER mutate prediction snapshots or scoring. Rule-based logic before LLM, always. No path from "agent concluded X" to "system behaves differently" without human review at a named gate.

**4. Dual lens — keep both visible.**
Primary north star: **HR prediction accuracy** (Brier score, calibration, hit-rate by tier/role).
Secondary: **betting-market efficiency** (CLV, EV realization, closing-line edge).
These lenses re-rank the loops differently. Show both orderings. The tension is real and documented.

---

## Section 1 — Loop Catalog

Fourteen loops. Each entry: Name · Purpose · Inputs · Prediction target · Outcome signal · Feedback mechanism · What it learns · Future improvements · Priority · Activation threshold.

Priority legend: **Critical** = foundational, must ship first. **High** = significant value, build as data allows. **Future** = real value but high data bar or high build cost.

---

### L1 — HR Probability Calibration
**Purpose:** Verify that model-probability buckets match real HR rates. P(HR) = 0.18 should mean 18 out of 100 batter-appearances in that bucket produce a HR.
**Inputs:** Frozen prediction snapshot (G1) joined to outcomes (G2). Binned by model_prob.
**Prediction target:** HR yes/no per batter-appearance.
**Outcome signal:** Settled HR outcomes with timestamp.
**Feedback:** Brier Score, reliability diagrams, Expected Calibration Error per bin. Flag bins where predicted ≠ realized by > threshold.
**Learning:** Recalibration constants (Platt scaling or isotonic). Identifies systematic over/under-confidence by probability tier.
**Future:** Per-park, per-temperature, per-handedness calibration splits once volume allows.
**Priority: Critical**
**Activation threshold: ≥200 settled picks per probability bin.** Below this, calibration curves are noise. Design now; activate at volume.

---

### L2 — Tier Validity
**Purpose:** Confirm that tier labels (APEX/ELITE/EDGE/SIGNAL/WATCH/COLD) predict HR rates meaningfully and that tier boundaries are not arbitrary.
**Inputs:** G1 (tier frozen at slate lock) + G2 (HR outcome). Requires `tier` column added to tracker schema.
**Prediction target:** HR hit-rate should rank monotonically APEX > ELITE > EDGE > SIGNAL > WATCH > COLD.
**Outcome signal:** Settled HR outcomes by tier label.
**Feedback:** Hit-rate by tier, rank-order check, Fisher exact test between adjacent tiers.
**Learning:** Tier boundary adjustments when adjacent tiers statistically indistinguishable.
**Future:** Per-handedness, per-role tier validity once volume allows.
**Priority: Critical**
**Activation threshold: ≥150 settled picks per tier.** Also requires: `tier` column added to pick tracker schema (schema unblock needed — see roadmap).

---

### L3 — Role Performance (PRIME / EXPLOSIVE / ADVANTAGE / WILDCARD)
**Purpose:** Validate that role assignments predict distinct HR outcome profiles consistent with their stated archetypes.
**Inputs:** Role frozen at selection moment (G1, requires Ticket/Data Capture) + G2 outcomes.
**Prediction target:** PRIME and EXPLOSIVE should have highest HR rates; WILDCARD should have highest variance; ADVANTAGE should show edge in specific matchup conditions.
**Outcome signal:** HR yes/no by role.
**Feedback:** Hit-rate and variance by role; flag if WILDCARD variance ≠ meaningfully higher than PRIME.
**Learning:** Role gate recalibration if roles conflate empirically.
**Future:** Role × tier interaction analysis.
**Priority: High**
**Activation threshold: ≥150 settled picks per role + role must be frozen at selection time.** Currently roles may not be consistently captured at selection — Ticket/Data Capture layer is the prerequisite.

---

### L4 — Ticket Structure
**Purpose:** Evaluate whether ticket construction patterns (PRIME+EXPLOSIVE anchor + supporting roles) correlate with better outcomes at the ticket level vs. leg-level randomness.
**Inputs:** Ticket-level history with leg composition, role mix, tier mix (G3, net-new grain — near-zero history currently). Requires Ticket/Data Capture.
**Prediction target:** Ticket hit-rate and P&L by structure archetype.
**Outcome signal:** Ticket settled result (all-win / partial / miss) with individual leg outcomes.
**Feedback:** Structure comparison: same-role tickets vs. mixed-role; role mix vs. EV realized.
**Learning:** Ticket template recalibration; identify over-represented failure structures.
**Future:** Correlation analysis (legs correlated by park, opponent, pitcher game-script).
**Priority: High**
**Activation threshold: Near-zero current history. Requires Ticket/Data Capture layer (G3 Ticket+Legs grain) + ~100+ complete ticket outcomes before structure-level conclusions are valid.**

---

### L5 — Pitch-Mix / Vulnerability Exploitation
**Purpose:** Verify that pitch-mix matchup signals (HVY indicator, arsenal vulnerability scoring) predict HR probability uplift beyond the base model.
**Inputs:** G1 (frozen pitch-mix snapshot and HVY flag at slate lock) + G2 (HR outcome). Requires matchup snapshot captured at prediction time.
**Prediction target:** HR rate for HVY-flagged picks should exceed non-HVY picks at same model_prob tier.
**Outcome signal:** HR yes/no split by HVY flag and vulnerability score bucket.
**Feedback:** Uplift coefficient by vulnerability tier. If HVY adds no marginal signal, display-only status confirmed. If it does add signal, document the magnitude — never auto-promote to MAIN.
**Learning:** Vulnerability weight recalibration. **MAIN/JIG separation invariant: any empirical uplift discovered here informs the JIG display signal only, never MAIN model_prob.** See [[wiki/doctrine/main-jig-separation|main-jig-separation]].
**Future:** Per-arsenal, per-pitch-type breakdown once volume allows.
**Priority: High** (rises further under accuracy-first lens — if pitch-mix genuinely predicts HR, that's a model-accuracy finding)
**Activation threshold: Moderate volume (~100+ HVY vs. 100+ non-HVY at matched tier) + matchup snapshot captured at prediction time.** Matchup snapshot is a prerequisite.

---

### L6 — Environmental (Park / Weather / Wind / Temperature)
**Purpose:** Validate that park factors, wind conditions, and temperature adjustments contribute measurable HR probability uplift and are not overfit constants.
**Inputs:** G1 (frozen park, wind, temp, dome flag at slate lock) + G2 (HR outcome).
**Prediction target:** HR rate in documented hitter-friendly conditions (high wind-out, warm, small park) should exceed rate in neutral conditions at matched model_prob.
**Outcome signal:** HR yes/no by environmental bucket.
**Feedback:** Uplift by park factor tier, wind direction, temperature band.
**Learning:** Environmental constant recalibration in config.py (operator-authorized only, n≥200 per bucket).
**Future:** Interaction terms (park × temp × handedness) — requires very high volume.
**Priority: High importance / Future activation** — environmental factors matter physically; proving them statistically requires the largest data runway of any loop.
**Activation threshold: Highest of any loop. Need ≥200 settled picks per environmental bucket (park tier × wind × temp). Some buckets (cold + hitter-friendly park) fill slowly. Design now; activate last.**

---

### L7 — CLV (Closing Line Value)
**Purpose:** Measure whether engine picks beat closing market odds — a proxy for long-run edge independent of short-term win/loss variance.
**Inputs:** G4 (opening odds snapshot + closing odds at game time). No outcome data needed for CLV itself.
**Prediction target:** CLV > 0 on aggregate = picks made at better odds than the market eventually priced.
**Outcome signal:** Closing line at lock. No HR outcome required — CLV is a market signal, not an accuracy signal.
**Feedback:** CLV distribution by tier, model_prob bucket, sportsbook. Trend monitoring for edge decay.
**Learning:** Market efficiency diagnostic. Identifies when market has closed on a signal the engine was using.
**Future:** CLV by feature (pitch-mix, park, handedness) to identify which model components the market prices well vs. late.
**Priority: Special — lowest activation threshold of any loop (works at low sample); build early as a cheap diagnostic.**
**Critical lens note: CLV is DEMOTED as a primary objective under the accuracy-first lens.** CLV measures market efficiency, not HR prediction accuracy. Build it early because it is cheap — but do not let early CLV availability distort prioritization. The primary-objective loops (L1, L2, L6) have the longest data runways. CLV availability tempts you to optimize market signals while accuracy signals are still data-starved. Resist.
**Activation threshold: ~30–50 complete slate days with closing-line capture.** Earliest-activating loop.

---

### L8 — Near-Miss / Failure-Mode Analysis
**Purpose:** Understand HOW the engine misses, not just that it misses. A pick that scores 0.22 model_prob and misses is not the same failure as one that scores 0.08 and misses.
**Inputs:** G2 with outcome granularity: exit velocity, launch angle on contact, pitcher actual pitch-mix vs. scouted mix, game-script context (blowout, late game, pitcher changed).
**Prediction target:** Failure modes cluster into recoverable categories (wrong matchup read, bad park/wind read, model overconfidence) vs. irreducible variance (well-hit ball caught, freak weather event).
**Outcome signal:** Failure-mode tag on each miss (requires richer G2 granularity than current binary HR yes/no).
**Feedback:** Failure-mode frequency by tier, role, model_prob. Identifies which misses are actionable vs. noise.
**Learning:** Feature-importance revision based on recoverable failure modes. Distinguishes model errors from luck.
**Future:** Automatic failure-mode tagging with Statcast exit-velocity + launch-angle at outcome time.
**Priority: High** (rises significantly under accuracy-first lens — failure-mode analysis is the fastest path to model improvement per pick analyzed)
**Activation threshold: Requires outcome granularity beyond binary HR/no-HR. Currently G2 likely lacks exit-velocity at outcome. Design the richer G2 schema now; activate when granularity available.**

---

### L9 — Operator Behavior
**Purpose:** Track operator selection patterns — which engine picks get selected, which get overridden, what override rationale is logged — to identify systematic operator bias or model-operator mismatch.
**Inputs:** Selection log (which picks were selected for tickets vs. available), override notes.
**Prediction target:** Do operator overrides outperform engine selection? Do they underperform? Where do they diverge?
**Outcome signal:** Outcome of selected vs. skipped picks.
**Feedback:** Selection rate by tier/role/model_prob; override win-rate vs. engine-consensus win-rate.
**Learning:** Calibration of when operator intuition adds value; identification of operator blind spots.
**Priority: Future Expansion** — requires consistent selection logging infrastructure.
**Activation threshold: Requires selection logging (currently not implemented) + sufficient overrides to compare (~50+ deliberate overrides with rationale).**

---

### L10 — Deployment Outcome (Engine Rec → Operator Selection → Construction → Result)
**Purpose:** Measure the full funnel from engine recommendation through operator construction through ticket result — the end-to-end system effectiveness, not just model accuracy in isolation.
**Inputs:** G1 (engine rec) + G3 (selected legs, ticket construction) + G2 (outcome). Requires Grain 3 history + selection logging.
**Prediction target:** Drop-off at each funnel stage: how much of engine edge is preserved through construction?
**Outcome signal:** Per-stage win-rate and EV realization.
**Feedback:** Identifies where the system loses edge: model, selection, or construction.
**Learning:** Which construction patterns best preserve model edge; where selection discipline matters most.
**Priority: High** (the integrating loop across all others — tells you if everything together works)
**Activation threshold: Requires G3 Ticket+Legs history (near-zero currently) + selection logging. Activate after Ticket/Data Capture layer is operational and has ~60+ days of history.**

---

### L11 — Feature Decay / Drift
**Purpose:** Detect when model features that were predictive in the past degrade in predictive power — due to market adaptation, league rule changes, or sample-period shift.
**Inputs:** G1 (feature values at prediction time, frozen) + G2 (outcomes). Requires temporal joins — same feature, different time windows.
**Prediction target:** Rolling feature-outcome correlation across time windows. A decaying feature shows declining correlation in recent windows vs. historical windows.
**Outcome signal:** Feature-outcome correlation by quarter/half-season.
**Feedback:** Feature-importance decay alert. Flags when a weight tuned on 2024 data may no longer apply in 2026.
**Learning:** Feature sunset or reweight recommendation (operator-authorized, n≥200 per window).
**Future:** Automatic drift detection with statistical tests (Mann-Whitney on rolling windows).
**Priority: High — temporal companion to L1 calibration. Design now; activate later.**
**Activation threshold: Requires ≥2 seasons of frozen-snapshot + outcome history to detect meaningful temporal drift. Earliest possible: end of 2026 season. Design the data model now.**

---

### L12 — MAIN-vs-JIG Disagreement
**Purpose:** Identify picks where MAIN model and JIG tactical signal strongly disagree — and track whether disagreement direction predicts outcome.
**Inputs:** G1 (frozen model_prob + JIG score at slate lock). Disagreement = high model_prob + low JIG score, or low model_prob + high JIG score.
**Prediction target:** Do high-MAIN / low-JIG picks outperform high-JIG / low-MAIN picks on HR accuracy? Which signal dominates in different contexts?
**Outcome signal:** HR yes/no by disagreement quadrant.
**Feedback:** Quadrant win-rate table. If MAIN consistently dominates JIG in accuracy, strengthens accuracy-first doctrine. If JIG adds information, quantifies when.
**Learning:** Context-specific signal weighting guidance (display only — never auto-blend MAIN/JIG; see [[wiki/doctrine/main-jig-separation|main-jig-separation]]).
**Priority: High — earlier-activating than most loops because it works on relative disagreement, not absolute volume per bucket.**
**Activation threshold: ~100–150 picks with both model_prob AND JIG score frozen at slate lock. Best value-per-data-dollar of any analytical loop — small sample tells you something meaningful.**

---

### L13 — Abstention / Coverage
**Purpose:** Track when the engine declines to recommend (no qualifying picks on a slate) and evaluate whether abstention decisions are well-calibrated — i.e., low-output slates should indeed have worse outcomes than normal-output slates.
**Inputs:** Slate-level pick count + G2 outcomes on slates where picks were sparse vs. abundant.
**Prediction target:** Slates with fewer qualifying picks should show lower average model_prob and lower realized HR rate.
**Outcome signal:** HR hit-rate and average model_prob by slate pick-count bucket.
**Feedback:** If sparse-slate picks don't underperform, the filter thresholds may be miscalibrated.
**Learning:** Filter threshold recalibration; confidence in abstention as a valid product decision.
**Future:** Confidence-interval display when abstaining ("too few high-confidence picks today").
**Priority: High-Value** — this is as much a product decision as a modeling decision. When the engine says "no good picks," that message should be honest.
**Activation threshold: ~50+ slate-days with outcome history, stratified by pick count. Relatively accessible.**

---

### L14 — Data-Source Reliability
**Purpose:** Measure whether sparse or stale input data correlates with worse prediction accuracy — quantifying the cost of data-quality failures.
**Inputs:** G1 (flags for null/sparse Statcast, stale pitch-mix, stale odds at prediction time) + G2 (HR outcome).
**Prediction target:** HR prediction accuracy on picks with complete data vs. picks with sparse/null features.
**Outcome signal:** Brier score split by data-completeness flag.
**Feedback:** Data-quality tax: how many Brier score points does sparse Statcast cost?
**Learning:** Prioritization of data-source investment; fallback logic calibration.
**Future:** Auto-downgrade confidence rating when key features null (display only).
**Priority: High; medium build effort** — the data-integrity agent (buildable now) is the precondition.
**Activation threshold: ~100+ picks with data-quality flags recorded at prediction time. Requires the Data-Integrity Agent to be running and logging flags.**

---

### Skipped Loops — Explicit Rationale

**Bankroll / Staking Loop:** Excluded. Tangential under accuracy-first lens. Kelly sizing feedback from outcomes risks overfitting staking strategy to short-run variance rather than improving HR prediction. Revisit if betting-market-efficiency becomes primary lens.

**Sentiment / News Loop:** Excluded for now. Enormous build cost (real-time news ingestion, NLP pipeline, injury-signal extraction). Uncertain marginal value over Statcast + pitch-mix signals. Future-future if ever.

---

### Dual-Lens Re-Rank

The same loops rank differently depending on which lens leads. The tension is documented, not resolved — both orderings are valid depending on the operator's current objective.

| Rank | Accuracy-First Ordering | Betting-First Ordering |
|------|------------------------|------------------------|
| 1 | L1 Calibration (foundation of everything) | L7 CLV (cheapest, fastest, pure market signal) |
| 2 | L2 Tier Validity (do tiers mean anything?) | L12 MAIN/JIG Disagreement (early-activating) |
| 3 | L8 Near-Miss / Failure Mode (fast improvement path) | L4 Ticket Structure (what makes parlays hit?) |
| 4 | L12 MAIN/JIG Disagreement (best value/data) | L3 Role Performance (archetypes valid?) |
| 5 | L5 Pitch-Mix Vulnerability (accuracy uplift question) | L5 Pitch-Mix Vulnerability (edge identification) |
| 6 | L3 Role Performance (archetypes valid?) | L13 Abstention / Coverage (honest no-pick signal) |
| 7 | L13 Abstention / Coverage (filter calibration) | L14 Data Source Reliability (source ROI) |
| 8 | L14 Data Source Reliability (data tax) | L10 Deployment Outcome (full-funnel EV) |
| 9 | L6 Environmental (physically real, statistically slow) | L2 Tier Validity (tier → EV mapping) |
| 10 | L10 Deployment Outcome (integrating loop) | L1 Calibration (accuracy not the primary lens here) |
| Later | L11 Feature Decay, L4 Ticket Structure, L9 Operator Behavior | L6 Environmental, L8 Failure Mode, L11 Decay, L9 Operator |

**Key tension:** The earliest-activating loops (L7 CLV, L12 Disagreement) are NOT the primary accuracy objective. The primary-objective loops (L1 Calibration, L6 Environmental) have the longest data runways. Optimizing for what's measurable earliest is not the same as optimizing for what matters most. Keep both orderings visible to resist premature metric fixation.

---

## Section 2 — Historical Warehouse (4 Grains)

Four grains. Each is its own immutable store. Joins happen on `(date, player_id)`. One-store-per-grain rule prevents the pick/ticket-grain tangle that currently exists in the tracking layer (see [[wiki/doctrine/tracking-consolidation-plan|tracking-consolidation-plan]]).

### G1 — Prediction Snapshots
**What:** Every model output frozen at slate lock: model_prob, JIG score, tier, role, pitch-mix flags (HVY, vulnerability score), park factor, wind, temp, dome flag, platoon split used, odds at prediction time.
**Immutability rule:** Once written at slate lock, G1 rows are never updated. All joins read from G1 as the authoritative "what the model thought at decision time."
**Current state:** Partial — pick_tracker captures some fields but not all (role not frozen at selection, matchup snapshot not captured). Full G1 requires Ticket/Data Capture layer.
**Storage:** Supabase `prediction_snapshots` table (net-new).

### G2 — Outcomes
**What:** Settled HR yes/no per batter-appearance, plus richer outcome granularity: exit velocity on contact (if available from Statcast), launch angle, game-script context (inning, score differential, pitcher change), failure-mode tag.
**Immutability rule:** G2 rows written once at settlement. Never updated except to add granularity fields that were pending (e.g., Statcast exit-velocity posted after settlement).
**Current state:** HR yes/no exists in results.csv / pnl_results path. Richer granularity (exit velo, launch angle) not currently captured.
**Storage:** Supabase `outcomes` table (net-new, or extend existing pnl path).

### G3 — Tickets + Legs
**What:** Ticket-level records: ticket ID, construction date, sportsbook, stake, ticket role mix, leg list (player_id, role, model_prob, odds at selection). Net-new grain — does not exist yet.
**Immutability rule:** Ticket captured at construction. Leg odds frozen at ticket submission. No retroactive editing.
**Current state:** Near-zero. This is what Ticket/Data Capture Phase 1 builds. See [[wiki/projects/ticket-data-capture-phase1-architecture|ticket-data-capture-phase1-architecture]].
**Storage:** Supabase `tickets` + `ticket_legs` tables (Ticket/Data Capture Phase 1 schema).

### G4 — Line / CLV History
**What:** Odds snapshots at multiple time points: open, periodic updates, close (at game lock). One row per player per slate day per sportsbook, timestamped.
**Immutability rule:** Snapshots are append-only. Never overwrite historical odds rows.
**Current state:** Opening odds captured in existing pipeline. Closing-line capture for CLV requires dedicated cron job (see tracking-consolidation-plan).
**Storage:** Supabase `odds_history` table.

### Warehouse Rules
- Loops READ across grains (e.g., L1 joins G1 to G2). Loops WRITE only to their own analysis output tables (e.g., `calibration_analysis`, `tier_validity_analysis`).
- Analysis output tables are never back-propagated into G1, G2, G3, or G4.
- No loop modifies scoring, tiers, model_prob, or config constants without explicit operator authorization at a named review gate.
- Storage: Supabase tables now. Columnar/warehouse layer optional later when query volume justifies the operational overhead.

---

## Section 3 — Agent Architecture

Seven agents. Each owns named loops, has a defined lens, and communicates findings through the Explainability Agent to a human gate. No agent has write authority over scoring, ranking, or prediction snapshots.

```
[Warehouse Layer: G1 · G2 · G3 · G4]
         │  (read-only)
         ├──► Calibration Agent (L1, L2)
         │         └──► Environmental Sub-Agent (L6, when activated)
         ├──► Vulnerability Agent (L5)
         ├──► Ticket Agent / Ticket/Data Capture (L3, L4 — after G3 history)
         ├──► Deployment Agent (L9, L10 — meta loop)
         ├──► Data-Integrity Agent (no loop number — pipeline precondition)
         ├──► Explainability Agent (cross-cutting — already shipped v1)
         └──► Research Agent (proposes, never applies)
                    │
                    ▼
         [Findings → Explainability Agent → HUMAN GATE]
                    │
                    ▼
         [Operator review → authorized change only]
```

### Calibration Agent
**Owns:** L1 (HR Probability Calibration), L2 (Tier Validity)
**Sub-agent:** Environmental Agent (L6) activates when environmental volume threshold reached; runs as sub-agent under Calibration, not standalone
**Lens:** Accuracy-first
**Outputs:** Reliability diagrams, ECE by bin, tier hit-rate table, recalibration recommendations (never auto-applied)
**Communicates with:** Explainability Agent (findings display), Research Agent (hypothesis generation)
**Build timing:** Design now. Activate at L1/L2 thresholds (≥200/bin, ≥150/tier).

### Vulnerability Agent
**Owns:** L5 (Pitch-Mix / Vulnerability)
**Lens:** Accuracy + JIG signal validation
**Outputs:** HVY uplift coefficient, vulnerability score bucket analysis
**Invariant:** Any discovered uplift documents JIG signal validity only. Never promotes to MAIN. MAIN/JIG separation enforced at agent boundary.
**Build timing:** After matchup snapshot capture is reliable.

### Ticket Agent (= Ticket/Data Capture layer, future product feature)
**Owns:** L3 (Role Performance), L4 (Ticket Structure)
**Lens:** Construction intelligence
**Outputs:** Role hit-rate table, ticket structure archetypes, pattern library
**Prerequisite:** G3 grain (tickets + legs) must exist with ≥60 days of history. This agent does not exist until Ticket/Data Capture Phase 1 is operational.
**Note:** This agent reasons over CAPTURED data and frozen ticket context. It never guesses from thin information.

### Deployment Agent
**Owns:** L9 (Operator Behavior), L10 (Deployment Outcome)
**Lens:** Full-funnel meta — integrates all other loops
**Outputs:** Selection funnel analysis, edge preservation rate, operator override comparison
**Build timing:** After G3 history + selection logging. Latest-building standalone agent.

### Explainability Agent
**Owns:** Cross-cutting — translates findings from all other agents into operator-readable summaries
**Status:** v1 shipped 2026-06-15 (template-grounded tier/role badge tooltips). Future versions extend to loop findings.
**Invariant:** Output is explanations of existing values. Never a scoring recommendation.

### Research Agent
**Owns:** No loops directly — proposes hypotheses, drafts recalibration packets for human review
**Invariant:** Proposes only. Human disposes. No path from "Research Agent concluded X" to "config.py changed."
**Build timing:** After Calibration Agent has enough findings to generate hypotheses worth testing.

### Data-Integrity Agent
**Owns:** Pipeline integrity — not a feedback loop, but a precondition for trusting all loops
**What it does:** Validates data completeness at each pipeline stage (Statcast null rates, odds staleness, pitch-mix coverage, player-id consistency, settlement lag). Emits data-quality flags that feed L14.
**Build timing: NOW — fully buildable from rule-based checks on yesterday's patterns. No outcome data required. This agent is the precondition for trusting G1, G2, G3, and G4.**
**Lens:** Data trustworthiness
**Outputs:** Per-slate data-quality report, null-rate trends, staleness alerts

---

## Section 4 — Agent Strategy / Research + Capture Layer Strategy

The disciplined capstone. Written as operator strategy, not product hype.

### 4.1 — Student vs. Library

An LLM agent does NOT get smarter by reading for years. It builds a **LIBRARY** (reference shelf), not a **MIND**. The distinction matters operationally:

- A library is reference material you query when building something specific.
- A mind retains context, forms persistent beliefs, and acts on accumulated conclusions.

LLM agents have no persistent beliefs between sessions. They have token context windows. Treating open-ended research accumulation as "the agent is learning" is a category error. Do not architect around it.

**Implication:** Bounded research tasks with specific outputs (a document, a schema, a design spec) are appropriate. Open-ended "spend 18 months reading about sports betting" is not.

### 4.2 — Timeless vs. Perishable Knowledge

Two categories of research knowledge. The distinction governs what External Hermes should capture now vs. what should wait until build time.

**COLLECT NOW — slow decay (still accurate in 2+ years):**
- Parlay correlation theory and Kelly criterion variants
- Devigging mathematics and no-vig line construction
- Rare-event probability (Poisson, negative binomial, calibration statistics)
- Bayesian reasoning applied to sports models
- Memory architecture principles for AI systems
- Explainability patterns for probabilistic systems
- Ticket-review theory and outcome-analysis methods
- Calibration literature (reliability diagrams, ECE, Brier score decomposition)

**WAIT — fast decay (recheck at build time, often stale within 1–2 years):**
- Current sportsbook product comparisons (features change quarterly)
- API pricing from specific providers
- Sportsbook sync details and integration specs
- Specific odds-provider feature lists
- Vector database comparisons (field moves fast)
- Agent-framework comparisons (field moves fast)
- Legal and compliance specifics (jurisdiction-specific, changes with legislation)

Do not invest research cycles in fast-decay knowledge. The marginal value of a perfectly researched 2026 vector-DB comparison is near zero in 2028.

### 4.3 — Two-Layer Model

Better than a 3-role taxonomy. Two clean layers with hard boundaries.

**External Hermes (= Nous Hermes Agent or similar external LLM research agent)**
- Scope: research, architecture docs, advisory-seat theory corpus, schema planning, blueprint support, sandbox prototypes, implementation packets for human review
- Sandboxed: READ-ONLY relative to production
- Hard boundary: Never touches scoring, MAIN model, JIG score, tiers, calibration constants, pipeline code, deployment config, or protected surfaces
- Output format: documents, design specs, research packets, draft schemas — always for human review before any implementation

**Ticket/Data Capture (= future product feature, not yet built)**
- Scope: Ticket Lab, Ticket Memory, Selected Legs Monitor, Live Banner, Postgame Debrief, Outcome Intelligence, Pattern Library, MAIN/JIG agreement display, ticket-construction review
- Reasons over: CAPTURED data + frozen ticket context (G1, G2, G3, G4 warehouse grains)
- Hard invariant: Never guesses from thin information. If the data is not in the warehouse, it shows "--" or declines to answer.
- Build timing: After Grain 3 has meaningful history. Not before.

### 4.4 — The Real Appreciating Asset

The real "start learning now" priority is not web research. It is your OWN captured history.

**What appreciates:** Captured HR Engine history — tickets, legs, frozen MAIN/JIG context at selection, odds at selection, player outcomes, game outcomes, review notes, structure patterns, win/loss by construction. This data cannot be recreated retroactively. Every day without capture is a day of permanently lost history.

**What does not appreciate (much):** General-purpose research about betting theory, Kelly variants, or calibration statistics. That knowledge exists in textbooks and papers. It will still be there in two years. Your captured history will not exist if you fail to capture it.

**Implication:** The capture layer (G1 snapshot freezing, G3 Ticket/Data Capture, ticket + leg capture) is more time-urgent than any research task. Build capture first.

### 4.5 — Drift Control

The External Hermes knowledge base is **DOCUMENTS YOU REVIEW**, never beliefs the agent acts on autonomously.

The governance invariant: there is no path from "External Hermes concluded X" to "system behaves differently" without a named human review gate. Research Agent proposes. Operator reviews. Operator authorizes. Only then does implementation proceed.

This rule prevents the failure mode where accumulated research starts implicitly shaping model decisions without explicit operator review of each change.

### 4.6 — Recommended Bounded Use

Use External Hermes for ONE bounded task: **build the timeless advisory-seat corpus + document the theory foundation** (parlay correlation, Kelly, devigging, calibration literature, rare-event probability, Bayesian sports modeling, ticket-review theory).

This is a scoped, deliverable-driven task with a completion criterion (a set of reference documents in the knowledge base). It is NOT "do open-ended multi-year web research and keep reading indefinitely."

Rerun this bounded task when a new build phase starts and specific research gaps are identified. Do not run it continuously.

### 4.7 — Forever Human-Controlled

The following surfaces are permanently operator-controlled. No agent path leads to autonomous changes in any of them:

- MAIN probability construction
- JIG score construction
- Tier labels and tier boundaries
- Calibration constants
- Ranking logic
- Pipeline architecture
- Config.py thresholds
- Any "apply changes" authority

Research Agent proposes. Human disposes. Always.

---

## Section 5 — Roadmap

Sequenced by what is buildable now vs. what is data-gated. The through-line: **your own captured history is the only knowledge that appreciates earliest. Build capture first. Use agents only where they give real leverage without risking the engine.**

### NOW — Buildable, Not Data-Gated

**Data-Integrity Agent**
Rule-based. No outcome data required. Validates null rates, staleness, player-id consistency, settlement lag on yesterday's pipeline output. Precondition for trusting all warehouse grains and all loops. Build this first.

**Capture Layer + Warehouse Grains**
G1 (frozen prediction snapshot at slate lock) + G3 (Ticket/Data Capture, ticket + leg capture). This is the actual "start learning now" action. Not research. Not agents. Capture. Every day without G1 freezing is a day of history the calibration loop can never use.

**Schema Unblocks**
Add `tier` column to pick tracker (unblocks L2). Ensure `role` is frozen at selection time (unblocks L3). These are narrow schema adds, not architecture changes.

**CLV Measurement (L7)**
Cheapest loop to activate. Requires only closing-line capture cron job. Build as early diagnostic — but do not let its availability distort prioritization toward market efficiency at the expense of accuracy work.

**External Hermes Timeless Corpus (bounded)**
One bounded task: build advisory-seat reference docs for parlay theory, Kelly, devigging, calibration, Bayesian sports modeling. Scoped to timeless knowledge only. Sandboxed. Output is documents for human review.

### AS DATA ACCUMULATES

**L1 Calibration Agent** — activate at ≥200 settled picks per probability bin (likely mid-to-late 2026 season)
**L2 Tier Validity** — activate at ≥150 picks per tier + tier column in tracker
**L5 Vulnerability Agent** — activate after matchup snapshot reliable + ~100 HVY vs. non-HVY at matched tier
**L12 MAIN/JIG Disagreement** — earlier-activating (~100–150 picks with both scores frozen); best value/data ratio
**L8 Failure-Mode Analysis** — activate after richer G2 granularity (exit velo + launch angle) available
**L11 Feature Decay** — design now; activate end of 2026 season at earliest (needs 2 seasons)
**Explainability Agent v2** — extends from tier/role tooltips to loop-finding summaries

### FUTURE — High Data Bar or High Build Cost

**Ticket/Data Capture / Ticket Agent (L3, L4)** — after G3 has ≥60 days of ticket history
**L6 Environmental Agent** — highest data threshold; design now, activate last
**L10 Deployment Agent** — after G3 history + selection logging (~60+ days)
**L9 Operator Behavior** — after selection logging infrastructure
**Research Agent** — after Calibration Agent findings are rich enough to generate testable hypotheses worth a formal research workflow

---

## Summary Table

| Loop | Name | Priority | Activation Threshold | Status |
|------|------|----------|---------------------|--------|
| L1 | HR Probability Calibration | Critical | ≥200/bin | Design now |
| L2 | Tier Validity | Critical | ≥150/tier + tier schema | Design now; schema add needed |
| L3 | Role Performance | High | ≥150/role + Ticket/Data Capture | Design now; capture needed |
| L4 | Ticket Structure | High | ~100+ tickets (Ticket/Data Capture G3) | Design now; capture needed |
| L5 | Pitch-Mix Vulnerability | High | ~100+ HVY/non-HVY at tier | Design now; snapshot needed |
| L6 | Environmental | High / Future | ≥200/bucket — highest bar | Design now; activate last |
| L7 | CLV | Special / Early | ~30–50 slate days | Build closing-line cron now |
| L8 | Near-Miss / Failure Mode | High | Richer G2 granularity | Design G2 schema now |
| L9 | Operator Behavior | Future | Selection logging | Future |
| L10 | Deployment Outcome | High | G3 + selection log ~60d | Future |
| L11 | Feature Decay / Drift | High | 2 seasons of frozen history | Design now; activate 2027 |
| L12 | MAIN/JIG Disagreement | High | ~100–150 picks both frozen | Early-activating; build soon |
| L13 | Abstention / Coverage | High | ~50 slate-days | Relatively accessible |
| L14 | Data Source Reliability | High | ~100 picks with DI flags | After Data-Integrity Agent |

---

*Authored: 2026-06-18. Doctrine only — no app/engine/pipeline/schema changes. Operator review required before any implementation proceeds.*

# SPEC: Post-Slate Review Workflow v1
## MLB HR Engine — Step 7/12

**Version:** 1.0
**Date:** 2026-05-20
**Phase:** Step 7/12 — Deployment, Portfolio & Operations
**Status:** ARCHITECTURE / UX / DOCTRINE ONLY — no runtime code modified
**Author:** Claude (Visual Doctrine Authority)
**Cross-reference:** `deployment_command_center_doctrine.md`, `spec_clv_intelligence_system_v1.md`, `spec_historical_intelligence_archive_v1.md`, `spec_risk_governance_v1.md`
**Runtime cross-reference:** `ops_daily.py`, `monitoring_dashboard.py`, `analyze_live_roi.py`, `analyze_clv.py`

---

## A. PURPOSE

The Post-Slate Review is the LEARN phase of the QUALIFY → DEPLOY → TRACK → LEARN doctrine. It converts raw outcomes into structured operational intelligence.

**Core doctrine:** An outcome is data. A reviewed outcome is intelligence. The difference between operators who improve over time and those who plateau is the discipline of the post-slate review.

The review is not optional. It is not a bonus feature. It is the mechanism by which the Deployment Command Center produces long-term operational learning. Without it, the system records outcomes but generates no improvement.

---

## B. REVIEW WORKFLOW STRUCTURE

The Post-Slate Review has eight sequential phases. Phases must be completed in order. Each phase's findings inform the next.

```
Phase 1: Settlement Confirmation
    ↓
Phase 2: Prediction Quality Assessment
    ↓
Phase 3: Deployment Quality Assessment
    ↓
Phase 4: Sizing Discipline Review
    ↓
Phase 5: Portfolio Construction Review
    ↓
Phase 6: CLV Performance Analysis
    ↓
Phase 7: Variance & Outcome Attribution
    ↓
Phase 8: Intelligence Export & Archive
```

---

## C. PHASE 1: SETTLEMENT CONFIRMATION

**Purpose:** Establish ground truth for the session. Confirm all picks are settled with verified outcomes.

**Process:**
1. Run settlement script (`settle_pick_tracker.py` or via `ops_daily.py`)
2. Confirm all picks have `hr_result` = 0, 1, or void
3. Identify any picks still pending (player didn't bat, game postponed, data unavailable)
4. Handle voids (DNP, postponement): mark as void, exclude from P&L and ROI calculations

**Output of Phase 1:**
- Total settled: N
- Wins: K (hit rate = K/N)
- Losses: (N-K)
- Voids: V (excluded)
- Total P&L: $X.XX

**Phase 1 is complete when:** All expected picks have a final `hr_result` and total P&L can be calculated.

---

## D. PHASE 2: PREDICTION QUALITY ASSESSMENT

**Purpose:** Evaluate how well the model predicted outcomes — independent of deployment decisions.

**Questions answered:**
- Did high-model-probability picks hit at higher rates than low-probability picks?
- Was the model calibrated this session (actual HR% ≈ model prob)?
- Did any specific factors drive over/under performance?

**Review structure:**

### Calibration Check
Group settled picks into probability bins:
- < 10% model prob
- 10–15%
- 15–20%
- 20%+

For each bin: compare actual HR% vs average model probability. Flag if actual deviates > 3pp from model (calibration drift check).

### Tier Performance Check
Compare hit rates by escalation tier:
- FIRE tier actual HR rate
- STRONG tier actual HR rate
- WATCH tier actual HR rate

A well-performing session shows FIRE > STRONG > WATCH in actual HR rates. Inversions suggest session-specific factors (injury, weather surprise, park effect) or sampling variance.

### Signal Performance Check
For picks that hit: identify top 3 factors that drove their escalation (barrel rate, park factor, platoon).
For picks that missed: identify if the miss was explainable (dominant pitcher, weather suppression active, low PA opportunity).

**Output of Phase 2:**
- Calibration state: STABLE / DRIFTING / ALERT
- Tier performance: ORDERED / INVERTED
- Notable signal failures (if any)

---

## E. PHASE 3: DEPLOYMENT QUALITY ASSESSMENT

**Purpose:** Evaluate the quality of deployment decisions — independent of game outcomes.

**Core question:** If the operator replayed the same session knowing only the pre-game model output, would they make the same deployment choices?

**Review structure:**

### Entry Selection Review
Compare deployed picks vs the full qualified queue:
- Were the top-composite-score picks selected for deployment?
- Were any high-value picks abandoned in favor of lower-value picks?
- Were abandonment decisions justified by suppression, exposure, or timing concerns?

**Flag:** Any abandoned FIRE pick with Edge ≥ 4% that would have won — this is a missed opportunity worth reviewing.

### Category Assignment Review
For each deployed pick:
- Was the slip category appropriate for the pick's quality?
- Were any FIRE-tier singles downgraded to parlay legs? (Generally a quality error)
- Were any WATCH-tier picks in Single Deployments? (Generally overstepping)

### Suppression Override Review
For any pick where suppression override was used (HIGH or LOCKDOWN tier):
- Did the overridden pick hit or miss?
- Does the override pattern across multiple sessions show a bias (always overriding LOCKDOWN and consistently missing)?

**Output of Phase 3:**
- Deployment selection quality: OPTIMAL / ACCEPTABLE / POOR
- Category assignment discipline: DISCIPLINED / MIXED / UNDISCIPLINED
- Override history: running record updated

---

## F. PHASE 4: SIZING DISCIPLINE REVIEW

**Purpose:** Evaluate whether position sizing remained within bankroll command layer guidelines.

**Review questions:**
- Were any picks sized above the quarter-Kelly recommendation by > 50%?
- Were any overrides of category sizing caps executed?
- Did session P&L outcomes track with sizing decisions (wins on large picks, losses on small picks = good sizing instincts)?

**Sizing grade:**

| Observation | Grade |
|-------------|-------|
| All picks within ±20% of Kelly recommendation | A |
| 1–2 picks outside range but acknowledged | B |
| Multiple picks outside range without acknowledgement | C |
| Any pick exceeded hard cap | FLAG |

**Reverse Kelly check:**
Check if any losing picks had above-average position sizes. If the operator consistently sized up on losing picks, this is a confidence-following-conviction error (overriding Kelly because of tier badge confidence).

**Output of Phase 4:**
- Sizing discipline grade: A/B/C/FLAG
- Reverse Kelly violations: count (target = 0)

---

## G. PHASE 5: PORTFOLIO CONSTRUCTION REVIEW

**Purpose:** Evaluate how well the session managed exposure, correlation, and diversification.

**Review structure:**

### N_eff Review
Did the session achieve target N_eff (≥ 4.0)?
- Below 3.0: over-stacked; excessive correlation inflated variance
- 3.0–5.0: moderate correlation; acceptable
- Above 5.0: well-diversified

### Concentration Review
Did any team, game, or pitcher target exceed recommended caps?
- Were concentration caps breached? Were they acknowledged?
- Which concentration created the most variance (won or lost together)?

### Stack Performance Review
For any Escalation Stacks deployed:
- How many legs hit? (Full win / partial / complete miss)
- Was the stack construction justified by actual correlation? (Same lineup that batted together, similar conditions)
- CLV comparison: did stack picks earn comparable CLV to singles?

### Diversification Grade

| Observation | Grade |
|-------------|-------|
| N_eff ≥ 5, no dimension at CONCENTRATED or above | A |
| N_eff 3–5, one dimension at CONCENTRATED | B |
| N_eff 2–3, multiple dimensions at CONCENTRATED | C |
| N_eff < 2, session = effective single bet | FLAG |

**Output of Phase 5:**
- Portfolio construction grade: A/B/C/FLAG
- N_eff achieved vs target
- Concentration violations logged

---

## H. PHASE 6: CLV PERFORMANCE ANALYSIS

**Purpose:** Evaluate market timing quality independent of game outcomes.

**Review structure:**

### Session CLV Summary
From CLV intelligence system:
- Average CLV across all deployed picks
- Session timing verdict (SHARP / EFFECTIVE / NEUTRAL / SOFT / POOR)
- Distribution of timing states (EARLY STRIKE / MARKET DRIFT / LATE STEAM / PRICE COLLAPSE / DEAD ENTRY)

### Timing Failure Analysis
For any PRICE COLLAPSE or DEAD ENTRY picks:
- What caused the timing failure? (Deployed too late, market steam came in, injury news)
- Was this avoidable? (Yes/No — logged for pattern detection)

### CLV by Category
Did singles capture better CLV than stacks? Did longshots earn any CLV?

**CLV Grade:**

| Average CLV | CLV Grade |
|------------|----------|
| +2.0pp+ | A |
| +1.0 to +2.0pp | B |
| 0 to +1.0pp | C |
| -1.0 to 0pp | D |
| Below -1.0pp | F |

**Output of Phase 6:**
- CLV grade for the session
- Timing failure analysis
- Timing pattern notes for archive

---

## I. PHASE 7: VARIANCE & OUTCOME ATTRIBUTION

**Purpose:** Determine how much of the session P&L was skill-based vs variance.

**Core doctrine:** A winning session can have poor deployment quality. A losing session can have excellent deployment quality. The review must distinguish between skill and variance before drawing conclusions.

**Attribution framework:**

```
Expected P&L = Σ (pick EV% × position size)    [what skill-based model predicts]
Actual P&L = Σ (actual outcomes × position sizes) [what happened]

Variance = Actual P&L - Expected P&L

Positive variance: won more than model expected (good luck)
Negative variance: won less than model expected (bad luck)
```

**Variance interpretation thresholds:**

| |Variance| vs Expected P&L | Interpretation |
|---|---|---|
| < 20% | Outcome tracking model well | |
| 20–50% | Normal variance | |
| 50–100% | High variance session; small sample | |
| > 100% | Extreme variance; do not conclude anything | |

**Attribution output:**
- Expected P&L: $X.XX
- Actual P&L: $X.XX
- Variance: $X.XX (XX% of expected)
- Verdict: outcome reflects skill / outcome reflects variance / mixed

---

## J. PHASE 8: INTELLIGENCE EXPORT & ARCHIVE

**Purpose:** Convert session review findings into persistent operational intelligence.

**Export structure:**
The review generates a structured summary written to the Historical Intelligence Archive:

```
session_review_YYYY-MM-DD.json

{
  "date": "2026-05-20",
  "picks_settled": 8,
  "picks_won": 2,
  "hit_rate": 0.25,
  "total_pnl": -14.50,
  "expected_pnl": +8.20,
  "variance": -22.70,
  
  "prediction_grade": "STABLE",
  "deployment_grade": "ACCEPTABLE",
  "sizing_grade": "A",
  "portfolio_grade": "B",
  "clv_grade": "B",
  "clv_avg_pp": +1.3,
  
  "n_eff_achieved": 4.2,
  "session_timing_verdict": "EFFECTIVE",
  
  "notable_flags": [
    "Abandoned FIRE pick (Judge +220) that won — missed opportunity",
    "1 PRICE COLLAPSE pick: Alonso late entry"
  ],
  
  "learning_notes": "...(operator notes)..."
}
```

**Operator notes field:** Free-text field. The operator may document anything not captured by the structured fields — lineup changes not reflected in data, weather surprises, personal observations about model behavior, etc. These notes are searchable in the Historical Intelligence Archive.

**Archive commit:** The completed review is committed to the archive as an immutable record. It cannot be edited after 24 hours. This prevents retroactive rationalization.

---

## K. REVIEW TIMING DOCTRINE

**Minimum review standard:** Phases 1–3 must be completed within 24 hours of session end.

**Full review standard:** All 8 phases completed within 48 hours of session end.

**Session skip doctrine:** Missing a full review for a session is permitted (life happens). Missing three consecutive sessions' reviews triggers a backlog alert in the Historical Intelligence Archive. Missing seven consecutive sessions' reviews suppresses adaptive learning outputs (the system cannot learn without review data).

---

*Document end. No runtime files modified. No Streamlit or Python execution path touched.*

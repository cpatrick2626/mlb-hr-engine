# Self-Learning System - Data Audit & Blockers

Honest assessment of what the calibration / self-learning loop needs to function,
and what is currently preventing it. Written 2026-06-22. This is a roadmap doc, not
a finding - its purpose is to point effort at the real bottleneck.

## THE CORE TRUTH

The self-learning loop calibrates on DEPLOYED-PICK OUTCOMES, not on documentation,
not on qualified picks, not on engine internals. It needs:
  fd_deployed picks  ->  real settled outcomes  ->  accumulate toward n>=200  ->  calibration

Calibration validity requires DEPLOYED picks specifically (fd_deployed=True), not
merely qualified picks. As of last measurement the deployed count was far below the
n<200 threshold for valid calibration. Nothing in the 2026-06-22 session added
outcome data. Documentation volume does not move this needle.

## WHAT THE LOOP NEEDS (in dependency order)

1. HEALTHY SLATES. The engine must produce 200+ player slates with odds, so that
   picks can qualify and be deployed. This is the foundation - without it, the
   capture layer has almost nothing to record.

2. DEPLOYED-PICK CAPTURE working end-to-end. Tables (tickets, legs), endpoints
   (POST /api/tickets/leg, /api/tickets/complete) exist and are live. But the
   fd_deployed flag historically was never set via FanDuel-tap behavior - frontend
   Phase 3 (tap wiring, fsmOpenFD in full-slate-matrix.js) is not complete. Until
   taps set fd_deployed, the loop cannot distinguish deployed from merely-qualified.

3. SETTLED OUTCOMES. Picks need results attached (daily_settle workflow). This is
   the label the model learns from.

4. VOLUME. ~200 deployed+settled picks before calibration is statistically valid.

## THE BLOCKER (top priority for the learning system)

ODDS API RELIABILITY. Observed 4/4 slates degraded this session: live odds fetch
failed, served stale cached props, only ~8-21 of ~18-72 players matched to odds.
Degraded slates mean:
- Most players filtered on "no market odds available" -> few qualify -> few can be
  deployed -> the capture pipeline is starved.
- The picks that DO deploy come from a non-representative (odds-survivor) subset,
  which would bias any calibration built on them.

=> If the goal is to help the self-learning system, fixing odds reliability is the
   single highest-value action. Everything downstream is starved until slates are
   healthy. This is an upstream data-supply problem, not a model problem.

## THE STRATEGIC FORK - Option B

If degraded-odds is the STEADY STATE rather than the exception (4/4 suggests it may
be), then the engine should rank players on NON-MARKET signal so the system stays
useful - and can eventually learn - on odds-poor days.

Option B: call confidence_score() for no-odds players with market_prob=0. This zeros
only the Market Signal component (0-30) and preserves Data Quality + Contact +
Pitcher Matchup (0-70). No-odds players could then legitimately surface A/B instead
of "NE/unranked."
- Risk: MEDIUM. Touches the confidence scoring PATH, not model_prob core. Changes
  what "confidence" means (market-inclusive for odds rows, market-excluded for
  no-odds rows) - a deliberate semantic split, must be decided, not drifted into.
- Relationship to learning: Option B alone does NOT generate outcome data. But it
  determines WHICH no-odds players get surfaced for possible deployment, which feeds
  what eventually gets captured. Secondary to fixing odds, but relevant.

## WHAT WOULD ACTUALLY ADVANCE THE LEARNING LOOP (prioritized)

1. Fix / harden odds API reliability (or add a fallback odds source). Unblocks slate
   health -> qualified picks -> deployable picks. TOP priority.
2. Complete frontend Phase 3 tap wiring so fd_deployed is set on FanDuel taps.
   Without this, deployed != qualified is never recorded. (MEDIUM risk, popup-blocker
   sensitive.)
3. Confirm daily_settle attaches outcomes to deployed picks reliably (verify, since
   silent persistence failures are this project's dominant failure mode).
4. THEN accumulate to n>=200 deployed+settled before attempting calibration.
5. Option B as a parallel decision - improves no-odds-day coverage.

## WHAT DOES NOT HELP (avoid effort here)
- More documentation of past investigations. (Useful for continuity, irrelevant to
  calibration.)
- Calibrating early on <200 picks. (Statistically invalid; deferred for a reason.)
- Touching model_prob / scoring formulas. (Prediction core is clean; the gap is data
  supply and capture, not the model.)

## OPEN VERIFICATION ITEMS (small, read-only, would inform the above)
- cache.py -> /api/slate serialization gap (does confidence_tier reach any consumer).
- app.py contradiction: a production tracking fix (9980700, "18-day pick_tracker gap
  root cause") lives in the supposedly-dead Streamlit file. Tracking-gap bugs
  directly affect whether outcome data is captured - this one is worth understanding
  because the pick_tracker gap it fixed is exactly the kind of silent capture failure
  that would starve the learning loop. Resolve before deleting app.py.

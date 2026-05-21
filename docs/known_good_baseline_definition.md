# Known-Good Baseline Definition
## MLB HR Engine — Master Stabilization

**Date:** 2026-05-20  
**Step:** 12 of 12  
**Owner:** Claude (doctrine)  
**Version:** Post-Step-12 Stabilization Baseline

---

## Purpose

Defines the operational baseline of MLB HR ENGINE as of Step 12 closeout. Prevents future implementation drift, accidental destabilization, and regression of validated systems. Any implementation work must be evaluated against this baseline before proceeding.

---

## System Classification

### SAFE — Fully Stabilized and Validated

These systems are runtime-proven, doctrine-locked, and safe for daily operational use.

| System | Status | Evidence |
|---|---|---|
| Core prediction pipeline (`pipeline.py`) | **SAFE** | Sessions 15–26 hardening; error handling, data quality, security audit applied |
| Probability model (`engine/probability.py`) | **SAFE** | Pearson r=0.9985, MAE=0.00079; FB20_gated, Context Moderation Guard, Adaptive Regression all validated |
| Calibration layer (`engine/calibration.py`) | **SAFE** | Platt CV Brier 0.09104 vs 0.09207 baseline; tier Platt for barrel≥10%; rollback flag live |
| Dynamic vig engine (`engine/vig.py`) | **SAFE** | 27-book vig table; per-tier odds-range multiplier; validated against measured overround |
| Pick tracker (`tracking/pick_tracker.py`) | **SAFE** | Atomic writes; schema migration; stale-pick expiry; sportsbook fallback to best_bookmaker |
| P&L tracker (`tracking/pnl.py`) | **SAFE** | Atomic CSV writes; auto-expire stale picks; float guards; zero-division guard |
| Operational orchestration (`ops_daily.py`) | **SAFE** | 6-phase daily workflow; report auto-cleanup after 90 days |
| Filter controls (`filter_controls.py`) | **SAFE** | Preset bar; st.number_input replaces sliders; backward-compatible session_state keys |
| Card HTML caching (`_CARD_CACHE`) | **SAFE** | Fingerprint-keyed; slate_ts invalidation; safe deferred lambda closures |
| Pitch mix data foundation (`clients/pitch_mix.py`) | **SAFE** | hfGT=R| filter; dedup; game_year validation; canonical pitch type lookup; normalization |
| Pitcher Savant fetch (`clients/pitch_mix.py`) | **SAFE** | Regular-season-only; (game_pk, at_bat_number) dedup; game_year validation per row |

---

### CAUTION — Validated with Known Limitations

These systems are operational but carry documented structural constraints or partial validation. Proceed with awareness.

| System | Status | Known Limitation |
|---|---|---|
| Platt calibration parameters | **CAUTION** | Fitted on 2026 Apr 1–May 15 data; will drift after major signal changes; re-calibrate when n≥100 post-Session 23 |
| Elite barrel bias correction | **CAUTION** | Bias reduced but not eliminated: barrel 12-15% still ~−9pp; requires further base-rate work |
| Live ROI tracking (real picks) | **CAUTION** | n=262 real settled bets as of Step 12; insufficient for barrel-tier-level conclusions (need n≥200 per tier) |
| Pitcher Factor Attenuation (`PITCHER_FACTOR_SCALE=0.60`) | **CAUTION** | Based on aggregate signal rank analysis; individual game pitcher signals may still carry local information |
| FB% signal weighting (FB20_gated) | **CAUTION** | 5-10% structural under-prediction persists; caused by Statcast look-ahead in backtest, not FB% weighting |
| Context Moderation Guard | **CAUTION** | Brier improvement marginal (−0.00005); designed as false-positive guard, not a calibration fix |
| Weather humidity factor | **CAUTION** | Physics-based; 2026 backtest Brier confirmed positive but real-world humidity signal validation pending ≥500 real picks |
| CLV tracking system | **CAUTION** | Infrastructure complete; 0 CLV entries as of Step 12; daily `capture_closing_lines.py` not yet automated |
| Portfolio optimizer (`optimizer.py`) | **CAUTION** | min_ev_pct=0.0 and min_edge_pct=0.0 (hard floors disabled); filtering by composite score only until n≥200 optimized settled picks |

---

### UNSTABLE — Deferred or Blocked

These systems are specified but not implemented, or are blocked pending further validation.

| System | Status | Notes |
|---|---|---|
| Scroll restoration execution | **UNSTABLE** | Doctrine specified (spec_scroll_restoration_and_focus_v1.md); implementation blocked pending Codex session_state ownership decisions |
| Escalation snapshot trigger | **UNSTABLE** | Spec complete; implementation requires integration with escalation fire event (Codex) |
| Mobile drawer system | **UNSTABLE** | Responsive layout spec complete; mobile-specific drawer not implemented |
| Player detail modal rewrite | **UNSTABLE** | Modal governance spec complete; full rewrite deferred |
| Automated escalation engine | **UNSTABLE** | Escalation doc doctrine complete; engine not wired to session_state triggers |
| Cross-engine event bus | **UNSTABLE** | Architecture spec only; no implementation |
| Session replay systems | **UNSTABLE** | Not yet specified beyond doctrine references |
| Adaptive orchestration | **UNSTABLE** | Concept documented; no implementation |
| Auto-deployment concepts | **UNSTABLE** | Mentioned in doctrine; no implementation plan |
| Advanced persistence | **UNSTABLE** | Beyond atomic CSV writes; no implementation |
| Velo decline signal integration | **UNSTABLE** | Data plumbing fixed (Session 36); signal computed but NOT wired into pipeline.py or model_prob |
| Arsenal matchup signal integration | **UNSTABLE** | CLOSED — DO NOT INTEGRATE: corr=−0.0696 (wrong direction); display-only in HVY modifier |
| tab_advanced_strategies lazy gate | **UNSTABLE** | Identified in Session 41; not yet implemented |
| tab_hits lazy gate | **UNSTABLE** | Identified in Session 41; not yet implemented |
| JIG Phase 2B game-command module | **UNSTABLE** | Deferred from Session 43; spec in full_slate_tactical_doctrine.md |

---

## Structural Known Limitations (Accepted)

These are not bugs — they are architectural constraints accepted as part of the engine design.

| Limitation | Accepted? | Rationale |
|---|---|---|
| Statcast look-ahead in backtest | YES | Full-season Statcast used for April games; structural to backtest methodology |
| 15-25% over-prediction in 0-5% bucket | YES | Below-avg batters stacking favorable context into 15%+ range; Platt calibration partially corrects |
| <6% bucket model under-prediction (−3.43pp live) | MONITOR | n=106 live picks; bias exceeds 3pp threshold at n≥50 — monitor but do not re-calibrate yet |
| Pitcher signals negligible aggregate correlation (rank #17/21) | YES | Low aggregate signal-to-noise; Pitcher Factor Attenuation (0.60) applied; individual matchup value retained |
| Fixed vig factor fallback (7.5%) | YES | Dynamic vig now primary; fixed is fallback for books not in vig table |
| Sweet Spot % weak signal (weakest batter predictor) | YES | Weight reduced 12%→10%; further reduction deferred |
| ISO double-count with barrel% | YES | Fades to 0% at 150 PA; minor enough to accept without correction |
| Interaction term positive-only | YES | Intentional design; negative interactions handled by multiplicative model |

---

## Unresolved Runtime Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Platt calibration drift after signal changes | HIGH | Re-run `analyze_calibration.py` after any signal weight or model change |
| 12-15% bucket bias approaching threshold (n=39, +5.51pp) | MEDIUM | Monitor via `monitoring_dashboard.py Phase 4`; act when n≥50 and bias > 3pp |
| pick_tracker.csv schema inconsistency (ev_pct decimal vs percentage in pre-S25 rows) | MEDIUM | `_migrate_schema()` handles column addition; ev_pct calculation inconsistency requires manual audit at n≥500 |
| CLV data absent (0 entries) | MEDIUM | Run `capture_closing_lines.py` ~30min before first pitch daily; automate with Task Scheduler |
| Velo decline signal active in display but inactive in model | LOW | Known; do not represent as a model signal until wired into pipeline.py |
| `tab_advanced_strategies` + `tab_hits` render unconditionally | LOW | Performance risk; lazy gate pattern identified, deferred |

---

## Deferred Systems Registry

*(Detailed entries in `remaining_blocked_systems_registry.md`)*

1. Scroll restoration execution
2. Escalation snapshot trigger
3. Mobile drawer system
4. Player detail modal rewrite
5. Automated escalation engine
6. Cross-engine event bus
7. Session replay systems
8. Adaptive orchestration systems
9. Auto-deployment concepts
10. Advanced persistence systems

---

## SAFE / CAUTION / UNSTABLE Decision Rules

**SAFE:** System has been exercised in live operation, validated by script or backtest, and has rollback path confirmed.

**CAUTION:** System is live but has documented drift risk, small-sample validation concern, or accepted structural limitation. Operate with monitoring.

**UNSTABLE:** System is specified only, implementation blocked, or explicitly deferred. Do not assume operational behavior without implementation validation.

---

## Baseline Change Governance

Any change that moves a CAUTION system to UNSTABLE, or introduces a new UNSTABLE system, must:

1. Add an entry to `remaining_blocked_systems_registry.md`
2. Update this baseline document
3. Define rollback path before implementation begins
4. Not modify parent orchestration or session_state ownership without Codex coordination

Any change that moves a system from UNSTABLE to CAUTION or SAFE must:

1. Include runtime validation evidence (AppTest or live browser proof)
2. Not present partial validation as full validation
3. Update this document before claiming stability

---

*Created: 2026-05-20 — Step 12 Final Stabilization Closeout*

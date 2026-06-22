# MLB HR ENGINE — Intelligence Wiki Index
Last updated: 2026-06-18

## DOCTRINE
| Page | Summary | Agent | Status |
|------|---------|-------|--------|
| [MAIN Model Doctrine](doctrine/main-model-doctrine.md) | Quantitative/model scoring philosophy; Primary Ranking Doctrine (HR Threat Rank pure); score=model_prob; bet_value_score deferred | Claude Code | updated 2026-06-11 |
| [JIG Tactical Doctrine](doctrine/jig-tactical-doctrine.md) | HVY pitch-mix signal, arsenal hunting, matchup exploitation | Claude | complete |
| [MAIN/JIG Separation Rules](doctrine/main-jig-separation.md) | Invariants governing separation of intelligence layers; tac_* vs jig_tac_* key namespaces; Bet Value Rank deferred/JIG-excluded | Claude Code | updated 2026-06-11 |
| [Visual Design Doctrine](doctrine/visual-design-doctrine.md) | Cinematic HUD, restrained glow, escalation hierarchy | Claude | complete |
| [Room Governance](doctrine/room-governance.md) | Rooms 05/08/09/10/11 ownership boundaries | Claude | complete |
| [App Shell Layout](doctrine/app-shell-layout.md) | MasterDashboard shell, engine-lens nav, MAIN/JIG identity colors, layout truth scope | Claude Code | 2026-06-08 |
| [Production Surface Truth](doctrine/production-surface-truth.md) | root frontend/ = production; v4/frontend/ = prototype; main branch canonical | Claude Code | 2026-06-08 |
| [Tier Vocabulary](doctrine/tier-vocabulary.md) | APEX/ELITE/EDGE vs QUIET/ACTIVE/ELEVATED vs prototype CRITICAL/HIGH — must not merge; Primary Ranking Doctrine added 2026-06-11 | Claude Code | updated 2026-06-11 |
| [Build Log and Spec Status](doctrine/build-log-and-spec-status.md) | latest.md missing; empty spec placeholders; Tier Ranking Room foundation recorded 2026-06-11 | Claude Code | updated 2026-06-11 |
| [Mobile Architecture V2](doctrine/mobile-architecture-v2.md) | Mobile/responsive layout doctrine; canonical reductions, MAIN/JIG preservation, stale patterns to avoid | Claude Code | 2026-06-09 |
| [Deploy Runbook](doctrine/deploy-runbook.md) | Manual flyctl deploy steps, cache refresh procedure, production surface map | Claude Code | 2026-06-15 |
| [Ticket Roles](doctrine/ticket-roles.md) | PRIME/EXPLOSIVE/ADVANTAGE/WILDCARD — usage archetypes, gates, display-only invariants, recalibration history | Claude Code | 2026-06-15 |
| [Design: Pitch Mix Analysis](doctrine/design-pitch-mix-analysis.md) | Modal de-fabrication 2026-06-15; real data sources; removed 3×3 zone grid | Claude Code | 2026-06-15 |
| [Known Gaps / Parked](doctrine/known-gaps.md) | xFIP mismatch, silent neutral pitcher default, dead app.py, pitch mix blanks, JIG tier epoch, rooms governance | Claude Code | 2026-06-15 |
| [Tracking Consolidation Plan](doctrine/tracking-consolidation-plan.md) | Option A phased plan: redirect automated settlement to pnl path, CLV reconcile, reader repoints, pick_tracker retirement | Claude Code | 2026-06-17 |
| [Feedback Loop Architecture](doctrine/feedback-loop-architecture.md) | 14-loop catalog, 4-grain warehouse, agent architecture, Ticket/Data Capture strategy, activation thresholds, dual accuracy/market lens | Claude Code | 2026-06-18 |

## ARCHITECTURE
| Page | Summary | Agent |
|------|---------|-------|
| [Pipeline Data Flow](architecture/pipeline-data-flow.md) | pipeline.py canonical data assembly | Claude Code |
| [Session State Map](architecture/session-state-map.md) | session_state ownership and protected keys | Claude Code |
| [Cache Ownership Map](architecture/cache-ownership-map.md) | Cache surfaces and ownership boundaries | Claude Code |
| [Supabase Schema](architecture/supabase-schema.md) | Service layer, tables, and key records | Claude Code |
| [Pitch-Mix Data Availability](architecture/pitch-mix-data-availability.md) | Arsenal Exploit Score audit: what pitch-type data exists/doesn't; reduced score scope; null rule; PAUSED | Claude Code |

## FORMULAS
| Page | Summary | Agent |
|------|---------|-------|
| [Batter Score Weights](formulas/batter-score-weights.md) | Barrel% 20%, ISO 15%, HR/FB 12% — full weight table | Claude |
| [Pitcher Vulnerability](formulas/pitcher-vulnerability.md) | HR/9 9%, Barrel% Allowed 5% — full weight table | Claude |
| [Environmental Multipliers](formulas/environmental-multipliers.md) | Platoon, park, wind, temp, dome nullification | Claude |

## STABILIZATION
| Page | Summary | Agent |
|------|---------|-------|
| [12-Step Sequence](stabilization/12-step-sequence.md) | Master stabilization roadmap | Claude |
| [Step 1 Record](stabilization/step-01-record.md) | route-state fix — PASSED 2026-05-22 | Claude Code |

## IDEAS
| Page | Summary | Agent | Status |
|------|---------|-------|--------|
| [Feature Backlog](ideas/feature-backlog.md) | Validation-first priority, done/in-progress, build-later, parked, key data facts | Claude Code | 2026-06-16 |

## PROJECTS
| Page | Summary | Agent | Status |
|------|---------|-------|--------|
| [Ticket/Data Capture Phase 1 Architecture](projects/ticket-data-capture-phase1-architecture.md) | Capture-first ticket/leg data model + Phase 1 build plan for Vercel board; architecture only, no build yet | Claude Code | 2026-06-17 PLAN |

## CONCEPTS
(pages added here as concepts are built out)

## SESSIONS
| Session | Summary | Agent | Date |
|---------|---------|-------|------|
| [2026-05-26 Phase 0 Closure](sessions/2026-05-26-phase0-closure.md) | Phase 0 closure | Claude | 2026-05-26 |
| [2026-05-26 Phase 1 Track A + MAIN Doctrine](sessions/2026-05-26-phase1-track-a-and-main-doctrine.md) | Track A MAIN doctrine session | Claude | 2026-05-26 |
| [2026-05-26 Ranker Audit](sessions/2026-05-26-ranker-audit.md) | Ranker audit findings | Codex | 2026-05-26 |
| [2026-05-26 Wiki Build](sessions/2026-05-26-wiki-build.md) | Initial wiki construction | Claude Code | 2026-05-26 |
| [2026-06-08 MAIN/JIG/JIG Builder Production Validation](sessions/2026-06-08-main-jig-jig-builder-production-validation.md) | Full Slate order fix + JIG Builder Phase A validated in production | Claude Code | 2026-06-08 |
| [2026-06-08 JIG Top Targets Production Validation](sessions/2026-06-08-jig-top-targets-production-validation.md) | JIG Top Targets source fix validated in production | Claude Code | 2026-06-08 |
| [2026-06-08 JIG Builder Phase B Deferred](sessions/2026-06-08-jig-builder-phase-b-deferred.md) | Phase B raw-workspace UI deferred by operator decision | Claude Code | 2026-06-08 |
| [2026-06-10 Option A Tier Threshold Production Validation](sessions/2026-06-10-option-a-tier-threshold-production-validation.md) | Option A FS_TIER_THRESHOLDS tightened + FanDuel URL fix validated | Claude Code | 2026-06-10 |
| [2026-06-11 Tier Ranking Foundation Completion](sessions/2026-06-11-tier-ranking-foundation-completion.md) | 10 commits recorded: tier vocab, model_tier_rank, APEX #1 display, Primary Ranking Doctrine, APEX Reason Stack Phase 1+1.5 | Claude Code | 2026-06-11 |
| [2026-06-15 Roles / Pitch Mix / Gauge Session](sessions/2026-06-15-roles-pitchmix-gauge-session.md) | All 4 ticket roles deployed (both boards); pitch mix de-fabricated; threat pie→radial gauge (0.29 ceiling); ADVANTAGE/WILDCARD recalibrated | Claude Code | 2026-06-15 |
| [2026-06-15 Validation Audit + Cloud Capture Loop](sessions/2026-06-15-validation-and-capture-loop.md) | First calibration audit (737 picks, marginal BSS, YELLOW FLAG on qualified over-prediction); settlement root-cause fixed; all capture jobs migrated to cloud (GitHub Actions + Fly volume) | Claude Code | 2026-06-15 |
| [2026-06-18 Cold-Load / Matchup / No Time Gate](sessions/2026-06-18-cold-load-matchup-no-time-gate.md) | Items 1–2 diagnostic; Item 3: noTimeGate stub removed; Item 4: three-state board; Item 5: HOME@HOME matchup bug fixed (gameId grouping + slate_games.away, order-independent derivation, blast radius b) | Claude Code | 2026-06-18 |
| [2026-06-18 Session Handoff + Open Threads](sessions/2026-06-18-handoff-and-open-threads.md) | Verified state: matchup fix, board blank fix, noTimeGate removal, CRON_SECRET reset. Open threads: cold-load HANG, pick logging watch, Ticket/Data Capture Phase 1 build, time-gate wiring deferred | Claude Code | 2026-06-18 |

# MLB HR ENGINE — Intelligence Wiki Index
Last updated: 2026-06-08

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

## ARCHITECTURE
| Page | Summary | Agent |
|------|---------|-------|
| [Pipeline Data Flow](architecture/pipeline-data-flow.md) | pipeline.py canonical data assembly | Claude Code |
| [Session State Map](architecture/session-state-map.md) | session_state ownership and protected keys | Claude Code |
| [Cache Ownership Map](architecture/cache-ownership-map.md) | Cache surfaces and ownership boundaries | Claude Code |
| [Supabase Schema](architecture/supabase-schema.md) | Service layer, tables, and key records | Claude Code |

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

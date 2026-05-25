# MLB HR Engine v4 — Design Specifications

This folder contains design-locked specifications for UX surfaces in the MLB HR Engine v4 platform. Captured during the 2026-05-25 design session.

## Purpose

These specs are reference documentation for future implementation work. They are not runtime code. They document the locked design intent — layout, interaction patterns, doctrine compliance, and risk class — so the design survives past the chat session and informs Claude Code execution packets when implementation begins.

## What's in this folder

| File | Surface | Risk class for impl |
|---|---|---|
| DESIGN_FULL_SLATE_MATRIX.md | Full Slate Intelligence Matrix | MEDIUM |
| DESIGN_PITCH_MIX_ANALYSIS.md | Pitch Mix Analysis modal | MEDIUM |
| DESIGN_BATTER_CARD.md | Modular Batter Card | MEDIUM |
| DESIGN_MAIN_COMMAND_CENTER.md | MAIN Command Center filter panel | MEDIUM/HIGH |
| DESIGN_JIG_BUILDER.md | JIG Builder All-In-One tactical surface | MEDIUM/HIGH |
| DOCTRINE_RANKING_RULE.md | Locked clarification on tier/rank source | — |

## What's NOT in this folder

The Master Dashboard Shell, Live Player Banner, Navigation Command Panel, and Live Strategy Picks Rail are still in design iteration. Specs for those will land in a separate update once they're locked.

## How to use these specs

When Claude Code is asked to implement one of these surfaces:

1. Read the relevant spec file in this folder first
2. Cross-reference with CLAUDE.md, AGENTS.md, and MASTER_TCC_DOCTRINE.md at the repo root
3. Verify the implementation respects the doctrine invariants (MAIN/JIG separation, no fabricated metrics, market display-only, etc.)
4. Surface any conflicts to the operator before writing code
5. Treat the spec as the source of truth for layout, interaction patterns, and color identity

## Doctrine cross-references

These specs assume and depend on the following doctrine files at the repo root:

- CLAUDE.md — top-level constitution
- AGENTS.md — agent ownership rules
- MASTER_TCC_DOCTRINE.md — Tactical Control Center orchestration rules
- FULL_SLATE_UX_DOCTRINE.md — Full Slate operational doctrine
- PHASE3_REFINEMENT_DOCTRINE.md — phase 3 refinement workflow
- ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md — deployment doctrine

If any spec in this folder conflicts with the doctrine above, doctrine wins. Specs are subordinate to doctrine and exist to clarify visual/interaction intent, not to override architectural rules.

## Architectural invariants reinforced by these specs

- MAIN is quantitative/model-driven (EV, Edge, model probability, Poisson-derived probability)
- JIG is tactical/matchup-driven (arsenal, HVY pitch-mix signal, environmental hunting)
- MAIN and JIG must not be merged
- HVY pitch-mix modifier is display-only on JIG side and must not be folded into MAIN model probability
- TCC orchestrates; it does not compute
- Market data (FanDuel odds, implied probability) is display-only and never enters tier/rank calculation — see DOCTRINE_RANKING_RULE.md

## Version

Captured: 2026-05-25 design session
Engine: mlb_hr_engine_v4
Active branch: stabilization-rerender-pass

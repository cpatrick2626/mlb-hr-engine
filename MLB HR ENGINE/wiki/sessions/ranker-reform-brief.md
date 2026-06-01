# Ranker Reform — Execution Brief
Date: 2026-05-26
Status: AUTHORIZED — next session priority
Risk Class: HIGH
Agent: Claude Code (execution) + Codex (audit complete)

## Doctrine Decision
Option C authorized by operator.
Reform ranker to model_prob × reliability_modifier.
Redesign auto_learn to adjust reliability modifier
instead of EV/edge weights.

## Why This Session
MAIN player pool is now model-driven (d415763).
MAIN player ranking is still market-driven (ranker untouched).
Pool and ranking must use the same doctrine.
Auto_learn conflict grows over time if left running.

## Execution Order (next session)
1. output/ranker.py
   Replace composite score formula:
   OLD: (ev_pct × 0.40 + edge_pct × 0.60) × confidence_scale
   NEW: model_prob × reliability_modifier
   Add reliability_modifier helper (lineup/data/book factors)

2. tracking/adaptive_weights.py
   Retire ranker_ev_weight adjustment logic
   Add reliability_modifier adjustment scaffold

3. tracking/learned_adjustments.json
   Archive current ev_weight value
   Reset to clean state for new modifier

4. pipeline.py
   Update score stamping to use new formula
   Companion change to score field semantics

5. app.py Full Slate Qualified
   Update local sort to match new score owner
   (currently uses stale EV*0.40 + Edge*0.35 + Conf*0.25)

6. tracking/auto_learn.py
   Retire ev_weight learning loop
   Add reliability_modifier learning scaffold
   Preserve picks_log.csv — historical data intact

## Reliability Modifier Design (from Codex audit)
Range: 0.80–1.00
  Lineup confirmed:    1.00
  Projected/likely:    0.92
  Unknown/unconfirmed: 0.85
  Statcast current:    1.00
  Statcast blended:    0.95
  Statcast prior:      0.90
  No Statcast/thin:    0.85
  3+ books:            1.00
  2 books:             0.98
  1 book:              0.95
  No books:            0.92

## Protected Surfaces Touched
  · output/ranker.py — HIGH
  · tracking/auto_learn.py — HIGH
  · tracking/adaptive_weights.py — HIGH
  · pipeline.py — HIGH
  · app.py Full Slate Qualified — MEDIUM
  · learned_adjustments.json — LOW

## Pre-session Requirements
  · Visual polish commit landed (tonight)
  · MIGRATION_HANDOFF.md updated
  · Fresh session — no other work running in parallel
  · Operator authorizes each file change separately

DO NOT COMMIT until I authorize.

# MLB HR Engine — AGENT OPERATING RULES

## PLATFORM IDENTITY

Main
= primary quantitative HR intelligence engine

JIG
= tactical matchup intelligence workspace

26
= future alternative explosive power-profile engine


---

## CORE ARCHITECTURE RULES

- Do NOT merge Main and JIG logic
- Maintain separate intelligence layers
- Main = quantitative / model-driven
- JIG = tactical / matchup-driven
- Preserve system separation at all times


---

## CURRENT DEVELOPMENT PRIORITIES

1. Pitch Mix data integrity
2. Tactical filter correctness
3. Full Slate systems
4. UI/workflow consistency
5. Dead code cleanup
6. Operational trust and clarity


---

## PITCH MIX RULES

Pitch Mix Analysis is now a flagship intelligence system.

Requirements:
- never fabricate missing data
- gracefully fallback when incomplete
- preserve real Statcast/Savant integrity
- validate handedness splits
- validate HR totals
- validate pitch-level metrics
- preserve believable outputs

Cross-check against:
- Baseball Reference
- Savant
- Statcast


---

## TACTICAL COMMAND CENTER RULES

Main TCC:
- lighter quantitative refinement
- broader filtering
- model-supportive

JIG TCC:
- aggressive tactical filtering
- matchup hunting
- arsenal exploitation
- HR environment targeting

Never make Main and JIG filters identical.


---

## UI / WORKFLOW RULES

Prioritize:
- operational clarity
- tactical readability
- stable workflows
- intelligence transparency
- believable outputs

Avoid:
- duplicated systems
- dead tabs
- conflicting labels
- hidden logic
- unnecessary feature expansion


---

## SCORING RULES

### MAIN Fields — Current

score (current) = model_prob
— `score` is a compatibility alias for `model_prob`. Unchanged. Do not redefine.

model_tier_rank = HR Threat Rank
— Stamped as `<TIER> #<N>` (e.g., `APEX #1`, `ELITE #3`).
— Ranks within each FS tier by model_prob descending.
— Owns: Full Slate, Picks table primary sort, leaderboard rank column.
— PRIMARY RANKING DOCTRINE: model_tier_rank is pure HR Threat Rank. It is not a bet value rank.
— APEX #1 = highest engine-estimated HR probability in APEX. Not best bet. Not highest EV.
— Odds, EV, edge, market lines, and sportsbook data must NOT influence model_prob, model_tier_rank, tier classification, or primary ranking.
— Market data is display-only context. It never gates or re-sorts primary rank.
— Bet Value Rank is deferred. When implemented it must be additive-only and operator-selectable. It must not replace primary rank.

### MAIN Fields — Future (NOT YET IMPLEMENTED)

bet_value_score = Deploy Score
— Approved formula:

    confidence_scale = 0.50 + 0.50 × (confidence / 100)
    ev_w = 0.55
    bet_value_score = (ev_pct × ev_w + edge_pct × (1 − ev_w)) × confidence_scale

— UI label: DEPLOY SCORE
— Rank ordinal label: DEPLOY RANK
— Additive-only field. Must NOT replace: score, rank, model_prob, model_tier_rank.
— May eventually own: Deploy surface, Top Targets, Picks table secondary column.
— May optionally appear in Full Slate as additive/sort option only.
— Must NOT appear in or influence JIG.
— Implementation is NOT authorized in this step.

### JIG

Separate tactical intelligence system. NOT purely EV-driven.
Bet Value Rank does NOT apply to JIG.

JIG tactical ranking is controlled by jigScore and JIG sort order.

JIG leaderboard rows inherit row.tier from MAIN (shallow copy of MAIN rows).
row.tier in JIG context = MAIN model probability tier, not JIG-native tactical tier.
Do not describe JIG row.tier as JIG tactical confidence, JIG deployment tier, or JIG-native escalation.
This is contextual probability information, not JIG scoring output.

No jigTier field currently exists.
If a JIG-native tier is required, introduce it as a separate jigTier field only after:
- dedicated jigScore distribution audit
- explicit operator authorization
- separate doctrine update


---

## IMPORTANT

Prefer:
- stabilization
- cleanup
- consistency
- trust

over:
- adding more features.


---

## PROJECT OPERATING RULES

### 1. ROOM ROUTING

When providing next actions, always specify:

```
USE EXISTING ROOM: <room name>
```

or

```
CREATE NEW ROOM: <room name>
```

Never assume the operator knows the destination.

For all future MLB HR ENGINE copy-ready prompts:

1. `ROOM Deployed From` means the room that created or deployed the prompt.
2. `Update Room` must list every room that needs to receive or know the prompt, task, or action.
3. `Update Room With Results` must list every room where the completion report or results should be pasted.
4. If more than one room needs the prompt, list all rooms under `Update Room`.
5. If more than one room needs the results, list all rooms under `Update Room With Results`.
6. `ROOM Deployed From` does not automatically receive results unless it is also listed under `Update Room With Results`.
7. Keep routing short, clear, and explicit.

---

### 2. COPY-READY EXECUTION PACKETS

When assigning work, provide a complete copy-ready prompt.

Do not provide partial instructions.

Do not require the operator to reconstruct prompts.

---

### 3. AI OWNERSHIP REQUIRED

Every execution packet must specify:

```
OWNER:
Claude Code / Codex / Claude Chat
```

---

### 4. MODEL REQUIRED

Every execution packet must specify the recommended model.

Examples:

Claude Code:
- Sonnet 4.6 Default
- Opus 4.7

Codex:
- gpt-5.4-mini low for audits/docs
- gpt-5.4 medium fast for frontend/UI
- GPT-5.5 Thinking for high-risk architecture

---

### 5. RISK CLASS REQUIRED

Every execution packet must specify:

```
LOW / MEDIUM / HIGH
```

---

### 6. GIT SAFETY REQUIRED

All execution packets must explicitly state:

```
DO NOT COMMIT
```

or

```
DO NOT PUSH
```

unless operator authorization exists.

---

### 7. !q COMMAND

`!q` means: Question only.

Do not generate execution routing.
Do not generate task packets.
Do not generate room assignments.
Do not generate implementation plans unless explicitly requested.

Respond only to the question.

---

### 8. PROJECT STATE AWARENESS

Before providing routing, use the latest known project state.

Do not route work that has already been completed.

Do not recommend reconstruction of files that already exist.

---

### 9. PREFERRED OUTPUT FORMAT

Routing responses should use:

```
ROOM
OWNER
MODEL
RISK
MISSION
BOUNDARIES
VALIDATION
DELIVERABLES
```

---

### 10. MOBILE GOVERNANCE

Mobile Architecture V2 is canonical.

Claude Design is the visual and navigation authority.

Do not propose mobile redesigns that replace Claude Design unless explicitly authorized.

---

### 11. PROJECT STATE SYNCHRONIZATION

When major phases complete, including:

- architecture.md
- product-spec.md
- ui-system.md
- Mobile Architecture V2
- production validations
- major ownership fixes
- governance/doctrine updates

the operator may issue a PROJECT STATE SYNC.

Rooms should update recommendations based on the latest synchronized state before routing future work.

#### PROJECT STATE SYNC OVERRIDES

When a Project State Sync conflicts with an older startup audit, the newest validated Project State Sync wins, provided:

- validation exists
- doctrine has not been violated
- the operator has accepted the sync

---

### 12. PRODUCTION STATUS REQUIRED

Execution packets should specify the affected surface when relevant:

```
SURFACE:
Production / Prototype / Documentation / Obsidian / Backend / Frontend
```

---

### 13. HIGH-RISK TWO-STAGE RULE

For HIGH-risk work:

- Stage 1 = Audit
- Stage 2 = Execution

Never combine HIGH-risk audit and execution in a single packet.

---

### 14. PROTECTED SURFACE DECLARATION

Execution packets should include:

```
PROTECTED SURFACES TO AVOID:
```

when relevant.

---

### 15. COMPLETION REPORT FORMAT

Execution agents should return:

```
FILES CHANGED
VALIDATION
GIT STATUS
COMMIT STATUS
PUSH STATUS
```

### 16. ROOM GOVERNANCE RULES

- Each active room is the main room for its assigned project area.
- Prefer routing work to an existing room. Do not recommend creating another room unless absolutely required.
- Recommend a new room only when no current room clearly owns the work, the work is large enough to require separate tracking, or the operator explicitly asks for a new room.
- Every copy-ready prompt must state destination explicitly:
  - `USE EXISTING ROOM: <room name>`
  - `CREATE NEW ROOM: <room name>`
- Every coding, repo, audit, validation, or docs-edit task must include:
  - recommended tool: `CC / Claude Code` or `CX / Codex`
  - recommended model
  - effort level
  - risk class
- Keep responses short and direct unless the operator asks for more detail.
- Claude Design is the canonical UI/dashboard layout source. Preserve its visual intent unless the operator explicitly authorizes a design change.
- Room map:
  - `MLB HR Engine Setup` = main command, routing, general project direction, next-action planning
  - `Issue Intake & Triage` = operator bugs, concerns, screenshots, confusing UI, missing data, suspected issues
  - `Tier Ranking & Classification Doctrine` = tier ranking, opportunity class, rank order, tier display, canonical/lens ranking doctrine, escalation quality
  - `FanDuel Shortcut Audit` = FanDuel links, search behavior, copy fallback, row-click isolation, FD shortcut validation
  - `Mobile UI Overhaul` = mobile/tablet implementation and responsive polish based on Mobile Architecture V2 and Claude Design
  - `Obsidian Governance Update` = wiki, doctrine, logs, session notes, durable documentation
  - `AGENTS.md Grounding Update` = project-wide rules, AI ownership, room behavior, protected surfaces, operating instructions
  - `Production Roadmap Planning` = roadmap, phase planning, 30-day sequencing, completed/remaining work
  - `Spec Reconstruction` = specs only, including architecture.md, product-spec.md, ui-system.md, component rules if needed
  - `Project Handoff MLB HR` = migration history, handoff state, archive context only
  - `Canonical Ranking Doctrine` and `Ranking Doctrine Review` = historical/reference rooms only; future ranking work routes to `Tier Ranking & Classification Doctrine` unless operator says otherwise

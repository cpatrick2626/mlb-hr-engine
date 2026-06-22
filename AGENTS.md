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
- MAIN remains HR probability focused.
- JIG remains matchup/exploit focused.
- Preserve MAIN/JIG separation.
- Do not merge scoring systems.


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

TCC Tactical Command Center is the main and only room for:
- Tactical Command Center layout
- TCC dashboard shell
- TCC command panels
- TCC workflow behavior
- TCC visual hierarchy
- TCC tactical UX
- TCC navigation behavior
- TCC status panels
- TCC issue review
- TCC-specific implementation prompts
- TCC validation results
- TCC doctrine and governance

TCC routing rules:
- If work is TCC-related, keep it in `TCC Tactical Command Center`.
- Do not suggest another room for TCC work unless absolutely required or the operator explicitly asks.
- TCC orchestrates; TCC does not compute.
- TCC may display model outputs, tactical signals, state, and workflow status.
- TCC must not create hidden scoring.
- TCC must not merge MAIN and JIG.
- MAIN remains `SCAN -> QUALIFY -> DEPLOY`.
- JIG remains `MATCHUP -> CONFIRM -> EXPLOIT`.
- HVY is display-only on JIG side.
- HVY must never feed MAIN probability.
- `config.py` remains source of truth for thresholds/model constants.
- `pipeline.py` remains canonical data assembly entrypoint.
- JIG `row.tier` is inherited MAIN model probability tier and must display as `MODEL TIER` in JIG contexts.
- JIG tactical priority is `jigScore` / tactical order, not `row.tier`.
- Claude Design is the canonical UI/dashboard layout source for TCC unless the operator explicitly authorizes a design change.


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

## PROTECTED SYSTEMS

The following systems require explicit authorization before edits:

- MAIN probability formula
- JIG scoring formula
- HVY logic
- tier thresholds
- ticket role logic
- calibration
- API payload contract
- deployment/runtime config

After edits, report protected systems touched: yes/no.

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
- EFFICIENT ROOM UPDATE RULE:
  - Do not overload every related room with every step-by-step prompt.
  - Full task prompts go only to the owner or execution room, and to Codex or Claude Code if repo work is required.
  - Informational rooms receive only a short kickoff notice when they need awareness and a final summary or results update when the task is complete.
  - `Update Room` means rooms that need awareness of the task, not necessarily rooms that need the full prompt.
  - `Update Room With Results` means every room that needs the final completion report or summary.
  - Do not post audit, fix, validation, commit, or push prompts into rooms that only need informational awareness.
  - If a room needs only context, give it a short update notice instead of the full prompt.
  - If a room needs to act, give it the full prompt.
  - Keep every interaction to one action.
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
  - `TCC Tactical Command Center` = main and only room for Tactical Command Center layout, dashboard shell, command panels, workflow behavior, visual hierarchy, tactical UX, navigation behavior, status panels, TCC issue review, TCC implementation prompts, TCC validation results, and TCC doctrine/governance. Does NOT own the global utility skill library.
  - `Mobile UI Overhaul` = mobile/tablet implementation and responsive polish based on Mobile Architecture V2 and Claude Design
  - `Obsidian Governance Update` = wiki, doctrine, logs, session notes, durable documentation
  - `AGENTS.md Grounding Update` = project-wide rules, AI ownership, room behavior, protected surfaces, operating instructions
  - `Production Roadmap Planning` = roadmap, phase planning, 30-day sequencing, completed/remaining work
  - `Spec Reconstruction` = specs only, including architecture.md, product-spec.md, ui-system.md, component rules if needed
  - `Project Handoff MLB HR` = migration history, handoff state, archive context only
  - `Canonical Ranking Doctrine` and `Ranking Doctrine Review` = historical/reference rooms only; future ranking work routes to `Tier Ranking & Classification Doctrine` unless operator says otherwise
  - `MAIN SKILLS` = main and only room for utility skill creation, skill updates, skill placement prompts, skill validation prompts, skill registry maintenance, skill doctrine references, skill command behavior, skill-related Obsidian notes, and skill-library commit/push routing. Does NOT own TCC app shell/layout/runtime behavior, MAIN/JIG scoring, config.py thresholds, pipeline.py data assembly, production deployment, or frontend runtime fixes unless the work is only skill documentation. Skill work must use `ROOM Deployed From: MAIN SKILLS`.

### 17. TOOL ACTION PERMISSION POLICY

READ = Always allowed.
- Inspecting files, repo state, API/cache snapshots, vault notes, and project
  state requires no approval.

CREATE / WRITE / UPLOAD / SEND = Needs operator approval.
- File creation, file edits, uploads, outbound sends (email/Slack/API writes),
  and any durable state change require explicit operator authorization before
  execution. This includes vault writes and repo writes.

DELETE = Disabled by default; operator approval required to enable per-task.
- No deletion of files, notes, rows, branches, or remote state without explicit,
  task-scoped operator authorization.

This policy is additive to and does not weaken existing Git Safety (Rule 6),
HIGH-Risk Two-Stage (Rule 13), and Protected Surface (Rule 14) doctrine.
Where rules overlap, the stricter gate wins.

---

## GLOBAL UTILITY SKILL LIBRARY

Skill source files live under `skills/` in the repo root.

### Registry

| Skill | Trigger |
|-------|---------|
| `/web-scraping` | Semantic web discovery, current source research, Exa/Firecrawl workflows, public source checks, rendered/dynamic page extraction |
| `/ingest-source` / `/ingest-resource` | Capture articles, YouTube links, transcripts, PDFs, notes into `knowledge/` or `projects/` with summaries and wikilinks |
| `/improve-system` | Audit stale/conflicting notes, review skills, capture lessons, mine Claude Code sessions, fill foundation gaps |
| `/ask-the-board` | Expert-inspired decision review across betting, quant/model, product, engineering, and UX lenses |
| `/internal-focus-group` | Test app changes, copy, workflows, launches, and product ideas against source-backed personas before shipping |
| `/ce-brainstorm` | Explore what to build |
| `/ce-plan` | Define scope, phases, risk, and done |
| `/ce-work` | Execute authorized work through delivery phases |
| `/ce-code-review` | Review completed work against scope and validation |
| `/ce-debug` | Troubleshoot failed or unexpected behavior |
| `/data-integrity-auditor` | Audit write/persistence paths, verify capture completeness, check calibration sample validity, hunt silent failures, bare-except sweeps |
| `/repository-hygiene` | Verify git working-tree/HEAD/production sync, uncommitted-but-deployed checks, orphaned/dead/contaminated paths, pre-deploy repo verification |
| `/doctrine-sweep` | Check doctrine-vs-reality drift, validate handoff docs against codebase state, find stale or contradictory documentation |

### Usage Rules

All MLB HR ENGINE rooms may invoke these skills when the task matches the trigger.

- Select the smallest useful skill.
- Prefer skill source files (`skills/*/SKILL.md`) as source of truth. Do not copy/paste full skill doctrine into room notes.
- Use `/ask-the-board` before major product, architecture, or betting decisions.
- Use `/internal-focus-group` before user-facing launches or UX/copy changes.
- Use `/ce-plan` before implementation prompts when scope or risk needs structure.
- Use `/ce-code-review` after claimed implementation completion.
- Use `/ce-debug` when behavior breaks or validation fails.
- Use `/improve-system` when repeated lessons should become doctrine.
- Use `/ingest-source` for durable captured material.
- Use `/web-scraping` when current external verification or source discovery is needed.

---

## GRAPHIFY WORKFLOW RULE

Graphify output lives at `mlb_hr_engine_v4/graphify-out/`. The `.graphifyignore` at `mlb_hr_engine_v4/.graphifyignore` is tracked by git and excludes `frontend/`, `Docs/`, `_archive/`, and `node_modules/`.

### When to use Graphify

Use Graphify for backend/API/pipeline/formula/odds/CLV architecture discovery:
- `graphify query "<question>"` — scoped subgraph for a codebase question
- `graphify path "<A>" "<B>"` — relationship between two nodes
- `graphify explain "<concept>"` — focused concept drill-down

Do NOT use Graphify for frontend/Vercel/Claude Design/Obsidian source-of-truth questions. Those surfaces are intentionally excluded from the graph. Read current files directly for those.

### Freshness gate — required before covered-surface work

Before any backend/API/pipeline/formula task, report Graphify status:

```
GRAPHIFY: FRESH   ← graph is current; query results are reliable
GRAPHIFY: STALE   ← graph is behind recent commits; do not rely on it
```

If STALE: either obtain explicit operator approval to run `graphify update mlb_hr_engine_v4` (AST-only, no API cost) or inspect files directly instead of querying the graph. Do not silently query a stale graph and present results as authoritative.

### Final report requirement

When a task touches covered surfaces (backend/API/pipeline/formula/odds/CLV), the completion report must include:

```
GRAPHIFY STATUS: FRESH | STALE | NOT APPLICABLE
```

### Codex note

Codex does not receive the Claude-specific freshness hook automatically. Codex must follow this rule from AGENTS.md directly. Codex must check whether `graphify-out/graph.json` exists and compare its mtime against recent git commits before querying.

---

### Invariants — Skills Do Not Override

Skills do not override protected-surface governance. Skills do not authorize runtime or code edits by themselves. Any implementation work produced by a skill must still follow:

- Room routing and risk classification
- Protected-surface audit-first workflow
- Operator authorization for commits and pushes
- MAIN / JIG separation
- HVY display-only doctrine
- TCC orchestrates; does not compute
- No hidden scoring
- No fabricated model inputs
- `config.py` as source of truth for thresholds and model constants
- `pipeline.py` as canonical data assembly entrypoint
- DO NOT COMMIT / DO NOT PUSH unless operator explicitly authorizes

# Room Governance Doctrine

**Last Updated:** 2026-06-11

---

## Room Architecture

| Room | Name | Owns |
|------|------|------|
| 11 | STRATEGIC COMMUNICATIONS HUB | Planning, coordination, strategic discussion, roadmap, cross-room routing |
| 10 | AI WORKFORCE COMMAND | AI orchestration, governance, sequencing, stabilization locks, audit workflows, work-risk classification, Obsidian governance enforcement |
| 08 | RUNTIME & STABILITY COMMAND | session_state, rerenders, routing, cache ownership, performance, validation, stabilization |
| 09 | JIG TACTICAL ENGINE | JIG Builder, aggressive filters, tactical stacks, arsenal hunting, high-volatility HR opportunities |
| 05 | LIVE DEPLOYMENT SYSTEMS | EV, odds, exposure, slips, bankroll, portfolio, deployment workflow, risk systems |
| — | MAIN SKILLS | Utility skill creation, skill updates, skill placement prompts, skill validation prompts, skill registry maintenance, skill doctrine references, skill command behavior, skill-related Obsidian notes, skill-library commit/push routing |

Room routing rule:
- Prefer existing room ownership.
- Do not create a new room unless no current room clearly owns the work, the work needs separate tracking, or the operator explicitly asks.
- Every copy-ready prompt must state destination explicitly with `USE EXISTING ROOM: <room name>` or `CREATE NEW ROOM: <room name>`.
- For all future copy-ready prompts, `ROOM Deployed From` is the originating room, `Update Room` lists every room that needs the prompt, and `Update Room With Results` lists every room that needs the completion report or results.
- If more than one room needs the prompt or results, list every room in the relevant field.
- `ROOM Deployed From` does not receive results unless it is also listed in `Update Room With Results`.
- Keep routing short, clear, and explicit.

EFFICIENT ROOM UPDATE RULE

- Do not overload every related room with every step-by-step prompt.
- Full task prompts go only to the owner or execution room, and to Codex or Claude Code if repo work is required.
- Informational rooms receive only a short kickoff notice when they need awareness and a final summary or results update when the task is complete.
- `Update Room` means rooms that need awareness of the task, not necessarily rooms that need the full prompt.
- `Update Room With Results` means every room that needs the final completion report or summary.
- Do not post audit, fix, validation, commit, or push prompts into rooms that only need informational awareness.
- If a room needs only context, give it a short update notice instead of the full prompt.
- If a room needs to act, give it the full prompt.
- Keep every interaction to one action.

Standard room map:
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
- `MAIN SKILLS` = main and only room for utility skill creation, skill updates, skill placement prompts, skill validation prompts, skill registry maintenance, skill doctrine references, skill command behavior, skill-related Obsidian notes, and skill-library commit/push routing. Skill work must use `ROOM Deployed From: MAIN SKILLS`.

---

## Room Ownership Law

If a system belongs to another room:
- Discuss it there
- Implement it there
- Validate it there

Do not duplicate ownership across rooms.

Cross-room coordination happens through Room 11 -
STRATEGIC COMMUNICATIONS HUB.

Room 10 also owns AI workflow governance and durable project-memory enforcement.
When a session creates governance, architecture, stabilization, deployment,
scoring, or other durable project knowledge, Room 10 is responsible for making
sure the Obsidian vault is updated or explicitly reviewed for update need.

---

## Stabilization Lock Rule

Runtime stabilization overrides tactical refinement.

If RUNTIME & STABILITY COMMAND (Room 08) identifies:
- Rerender instability
- session_state corruption
- Routing instability
- Cache contamination

Then all tactical and UI work pauses until stabilization completes.
The lock applies across all rooms. No exceptions without operator
authorization.

---

## Work Risk Classification

| Class | Definition | Process |
|-------|-----------|---------|
| LOW | File moves, archival, doc edits, housekeeping, read-only audits, wiki writes | Single Claude Code pass, normal verification |
| MEDIUM | Single-file runtime edits, narrow scope | Single Claude Code pass, extra diff verification before commit |
| HIGH | Touches engine/*, pipeline.py, calibration, MAIN model probability, scoring composites, MAIN/JIG separation, config.py, any closed surface | Audit-first -> operator review -> execution as a separate authorized assignment |

HIGH risk work cannot be single-step. Ever.

## Operating Rules

- One action per response.
- Keep outputs short and direct unless the operator asks for more detail.
- Every coding, repo, audit, validation, or docs-edit task should include recommended tool, model, effort, and risk class.
- Claude Design is the canonical UI/dashboard layout source. Preserve its visual intent unless the operator explicitly authorizes a design change.
- MAIN and JIG stay separate.
- JIG `row.tier` is inherited MAIN model probability tier and should be presented as MODEL TIER in JIG contexts. Tactical ranking still comes from `jigScore` and JIG sort order.

## Tool Action Permission Policy

This section records AGENTS.md Rule 17.

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

Related doctrine:
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)

## TCC Tactical Command Center Governance

- `TCC Tactical Command Center` is the main and only room for all MLB HR ENGINE Tactical Command Center work.
- TCC ownership includes Tactical Command Center layout, dashboard shell, command panels, workflow behavior, visual hierarchy, tactical UX, navigation behavior, status panels, TCC issue review, TCC-specific implementation prompts, TCC validation results, and TCC doctrine/governance.
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

## MAIN SKILLS Room Governance

`MAIN SKILLS` is the main and only room for all MLB HR ENGINE utility skill-library work.

### MAIN SKILLS Owns

- utility skill creation
- utility skill updates
- skill placement prompts
- skill validation prompts
- skill registry maintenance
- skill doctrine references
- skill command behavior
- skill-related Obsidian notes
- skill-library commit/push routing

### MAIN SKILLS Does NOT Own

- TCC app shell / layout / runtime behavior
- MAIN/JIG scoring
- `config.py` thresholds
- `pipeline.py` data assembly
- production deployment
- frontend runtime fixes unless the work is only skill documentation

### Routing Clarifications

- Skill work must use `ROOM Deployed From: MAIN SKILLS`.
- `TCC Tactical Command Center` owns Tactical Command Center app/shell/UX work, not general utility skill-library ownership.
- The global skill library remains available to all rooms; MAIN SKILLS owns changes to the skill library itself.
- Prior ambiguity where skill-library work was routed from `TCC Tactical Command Center` is corrected as of 2026-06-12.

---

## Obsidian Governance Enforcement

Obsidian is the formal long-term project memory system for MLB HR ENGINE.

Room 10 - AI WORKFORCE COMMAND is responsible for governance enforcement across:
- doctrine
- room governance
- architecture decisions
- stabilization history
- major bug decisions
- deployment changes
- formula and scoring decisions
- durable AI execution knowledge

When any of those surfaces change, the acting AI should explicitly evaluate
whether an Obsidian update is required before closing the assignment.

Standard packet language for Claude Code and Codex:

> If this task changes doctrine, architecture, runtime behavior, deployment behavior, scoring behavior, room governance, visual doctrine, or long-term project state, update the Obsidian vault before returning final completion.
>
> Vault path:
>
> C:\MLB HR Engine\mlb-hr-engine-master\MLB HR ENGINE
>
> Before writing:
> - inspect existing relevant notes
> - do not duplicate existing doctrine
> - update the correct note if one exists
> - create a new note only if needed
>
> Do not store:
> - secrets
> - API keys
> - .env values
> - private credentials

Governance command:
- `!obs` generates a copy-ready Obsidian update packet for doctrine changes,
  bug fixes, stabilization work, audits, implementation results, and governance updates.

---

## Vault Auto-Commit Interaction Rule (2026-06-12)

### Context

The Obsidian vault at `MLB HR ENGINE/` is tracked inside the main repo. Vault backup automation periodically auto-commits any changes inside the vault subtree (commits typically titled `vault backup: <timestamp>`).

### Observed Failure Mode (2026-06-12)

A planned batched commit was intended to land Step A (doctrine update to `wiki/doctrine/production-surface-truth.md`, a vault-tracked file) together with Step C (non-vault archival of v4 deploy files).

Between Step A landing on disk and Step C completing, the vault backup process auto-committed the doctrine change in `97eff6e`. The batched-commit plan was no longer achievable. Step C had to ship as a separate commit (`a32293d`).

History is still clean and reversible, but the intended single-logical-commit narrative was lost.

### Doctrine Rule

Any time a planned commit batches a vault-tracked file with one or more non-vault files, ONE of the following must be done before the vault edit hits disk:

- **(a)** Stage and commit the non-vault files FIRST, then apply and commit the vault edit (two commits, but intentional ordering). **This is the default.**
- **(b)** Pause vault backup automation for the duration of the operation, then resume after the batched commit lands. Requires explicit operator authorization.
- **(c)** Apply both edits, stage both immediately, and commit within the auto-commit interval (only safe if the operator can guarantee timing). Requires explicit operator authorization.

Option (a) is the default. Options (b) and (c) require explicit operator authorization.

### Authorship Rule

Claude Code packets that plan a batched vault + non-vault commit must explicitly state which of (a), (b), (c) is in effect. Packets that do not specify default to (a).

### Detection

Recent vault-backup commits can be inspected with:

```
git log --oneline --grep "vault backup"
```

If a planned-batch vault file appears in such a commit before the intended commit lands, the batch plan is considered broken and must be re-scoped (as was done for Step C on 2026-06-12).

---

## Global Utility Skill Library

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

---

## Cross-References

- [Session State Map](../architecture/session-state-map.md)
- [Cache Ownership Map](../architecture/cache-ownership-map.md)
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md)
- [MAIN/JIG Separation Rules](main-jig-separation.md)
- [Obsidian Governance Doctrine](OBSIDIAN_GOVERNANCE_DOCTRINE.md)

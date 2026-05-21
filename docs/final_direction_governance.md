# FINAL_DIRECTION GOVERNANCE
**Owner:** Claude (Visual Doctrine Authority)  
**Created:** 2026-05-20  
**Phase:** Step 3/12

---

## PURPOSE

FINAL_DIRECTION is the controlled visual baseline for MLB HR Engine UI implementation. Documents in FINAL_DIRECTION are approved reference images with formal governance status. They are not aspirational mockups — they are binding implementation anchors.

No visual component may be built by Codex without a corresponding FINAL_DIRECTION-approved reference or an extracted spec document traceable to one.

---

## IMMUTABILITY RULES

FINAL_DIRECTION entries, once approved, are immutable in the following respects:

1. **Core hierarchy** — information priority order cannot be reversed
2. **Escalation surface assignment** — which components own badge/glow is fixed
3. **Visual weight ranking** — batter > pitcher > game container > sidebar is permanent
4. **Primitive identity** — approved primitives (badge, glow, pill, split-panel) cannot be merged or renamed without formal revision

Immutability does not mean:
- Exact pixel dimensions are locked
- Color hex values are locked
- Exact metric selection is locked

Immutability means: **structural doctrine is locked.**

---

## APPROVAL WORKFLOW

### Tier Progression

```
CANDIDATE → EVALUATED → CONDITIONAL → APPROVED → ARCHIVED
```

| Stage | Meaning | Authority |
|-------|---------|-----------|
| CANDIDATE | Image submitted for evaluation | Any session |
| EVALUATED | Reviewed, not yet approved | Claude assessment |
| CONDITIONAL | Approved for sub-system use only | Claude |
| APPROVED | Full governance authority granted | Claude |
| ARCHIVED | Superseded by newer approved reference | Claude |

### Approval Requirements

To graduate to APPROVED, a reference image must demonstrate:
- [ ] Correct information hierarchy (threat signal dominant)
- [ ] Appropriate density (no dead whitespace, no flooding)
- [ ] Escalation language present and legible at scan speed
- [ ] No sportsbook-style visual elements
- [ ] No oversized player imagery dominating layout
- [ ] Command-center aesthetic maintained
- [ ] At least 2 reusable primitives extractable

### Conditional Requirements

CONDITIONAL status granted when image demonstrates value for specific sub-systems but full-page layout is not stable. Codex may extract CONDITIONAL primitives only within the defined conditional scope.

---

## VERSIONING SYSTEM

### Reference Image Versioning

`[Page]_v[N].png`

Example: `Main Batters Card_v2.png`

Rules:
- v1 is original approved reference
- v2+ requires formal revision rationale in FINAL_DIRECTION_APPROVALS.md
- Old version moves to `00_FINAL_DIRECTION/archive/` — never deleted

### Spec Document Versioning

`spec_[component]_v[N].md`

Example: `spec_player_threat_card_v1.md`

Rules:
- Minor changes (clarifications, non-structural): increment patch note in file header
- Structural changes (hierarchy, escalation assignment): new v[N] document
- Previous spec version archived, not deleted
- Codex implementation must reference exact spec version used

---

## NAMING CONVENTIONS

### Images

```
Main [Page Name].png         → original intake
Main [Page Name]_v2.png      → revision
[Page Name]_REJECTED.png     → disqualified (moved to /rejected/)
```

### Spec Documents

```
spec_[component_name]_v[N].md
```

Component names:
- `player_threat_card`
- `pitcher_suppression_card`
- `game_container`
- `escalation_badge`
- `right_operational_sidebar`
- `pitch_mix_table`
- `live_intelligence_feed`
- `deployment_card`
- `modal_escalation_overlay`
- `full_slate_shell`

### Governance Documents

```
final_direction_governance.md           → this file
final_direction_approvals.md            → approval records (in 00_FINAL_DIRECTION/)
component_implementation_priority.md   → build ordering
visual_primitive_standards.md          → shared primitive definitions
```

---

## REPLACEMENT RULES

A FINAL_DIRECTION entry may be replaced when:
1. Approved reference no longer represents target visual direction
2. New design iteration supersedes current baseline
3. Primitive conflict discovered between two approved references

Replacement procedure:
1. New candidate image submitted
2. Claude evaluates against existing approved entry
3. If superior: existing entry moves to `archive/`, new entry receives APPROVED status
4. FINAL_DIRECTION_APPROVALS.md updated with replacement rationale
5. All spec documents referencing old entry updated with supersession note

**Replacement does not mean deletion.** Archive is permanent.

---

## ARCHIVE PROCEDURES

Archive folder: `00_FINAL_DIRECTION/archive/`

Items archived when:
- Superseded by newer approved reference
- CONDITIONAL entry promoted or rejected
- Spec document versioned past v1

Archive naming:
```
[original name]_ARCHIVED_[date].png
spec_[component]_v[N]_ARCHIVED_[date].md
```

---

## EXTRACTION PROTOCOL

Before Codex may implement any component:

1. **Reference must exist** — APPROVED or scoped CONDITIONAL reference in FINAL_DIRECTION
2. **Spec must exist** — `spec_[component]_vN.md` in `docs/`
3. **Spec must be Claude-authored** — Codex does not write its own spec
4. **Spec version must be pinned** — Codex implementation record references exact spec version
5. **Implementation must be isolated** — no route coupling, no session_state ownership

Codex may not begin implementation if:
- No approved reference exists for the component
- No spec document exists
- Spec exists but is marked DRAFT or PENDING

---

## IMPLEMENTATION GATING

### Gate Levels

| Gate | Requirement | Blocks |
|------|------------|--------|
| G0 | Reference APPROVED | All Codex work on component |
| G1 | Spec v1 authored | Codex implementation start |
| G2 | Primitive standards documented | Any shared primitive usage |
| G3 | Priority rank assigned | Implementation ordering |
| G4 | Isolation strategy confirmed | Component handoff |

Current gate status (2026-05-20):
- G0: PASSED — 4 references APPROVED, 1 CONDITIONAL
- G1: IN PROGRESS — spec_player_threat_card_v1.md being authored
- G2: IN PROGRESS — visual_primitive_standards.md being authored
- G3: PASSED — component_implementation_priority.md authored
- G4: PENDING — isolation strategy in spec_player_threat_card_v1.md

---

## AUTHORITY MATRIX

| Action | Claude | Codex | Human Override |
|--------|--------|-------|---------------|
| Approve reference | YES | NO | With Claude review |
| Revise APPROVED entry | YES | NO | With Claude review |
| Archive entry | YES | NO | With Claude review |
| Supersede entry | YES | NO | With Claude review |
| Author spec document | YES | NO | N/A |
| Implement from spec | NO | YES | N/A |
| Propose candidate image | YES | YES | YES |
| Request re-evaluation | YES | YES | YES |

Claude holds sole visual doctrine authority. Codex holds sole implementation authority. No crossover.

---

## FUTURE REFERENCE GRADUATION

For a new image to graduate into FINAL_DIRECTION:

1. Image placed in `Main HR Dashboard/` (intake folder)
2. Entry created in `_INTAKE_LOG.md` with evaluation date
3. Claude evaluates against approval requirements (see above)
4. If APPROVED: entry created in `FINAL_DIRECTION_APPROVALS.md`, image copied to `00_FINAL_DIRECTION/`
5. If CONDITIONAL: scoped entry created, extraction scope defined
6. If REJECTED: moved to `00_FINAL_DIRECTION/rejected/`, rationale documented

Graduation is Claude-gated. No image self-graduates.

# Triage Labels

## Workflow states

| Role | Label string | Meaning |
|---|---|---|
| needs-triage | `needs-triage` | Maintainer must evaluate |
| needs-info | `needs-info` | Waiting on reporter |
| ready-for-agent | `ready-for-agent` | Fully specified, AFK-agent can pick up |
| ready-for-human | `ready-for-human` | Needs human implementation |
| wontfix | `wontfix` | Will not be actioned |

Record state as `Status:` frontmatter line (e.g. `Status: needs-triage`).

## Project category tags

`bug`, `feature`, `docs`, `frontend`, `backend`, `api`, `formula`, `data-quality`, `deployment`, `design`, `high-risk`, `blocked`, `MAIN`, `JIG`, `HVY-display-only`

Record tags as `Tags:` frontmatter line (e.g. `Tags: bug, MAIN, high-risk`).

### Tag semantics

- `MAIN` - touches MAIN scoring/model pipeline; keep isolated from JIG
- `JIG` - touches JIG tactical/matchup layer; keep isolated from MAIN
- `HVY-display-only` - touches HVY pitch-mix signal; must remain display-only, never folded into MAIN model probability
- `high-risk` - touches a protected zone (see `CLAUDE.md` PROTECTED ZONES section)
- `blocked` - cannot progress; note blocker in issue body

# Domain Docs

## Layout: single-context, wiki-rooted

Domain context lives in the wiki, not at repo root. No root `CONTEXT.md` or `docs/adr/`. Do not create them.

## Before exploring, read these

| Resource | Path | Purpose |
|---|---|---|
| Wiki index | `MLB HR ENGINE/wiki/index.md` | Top-level navigation |
| Doctrine | `MLB HR ENGINE/wiki/doctrine/` | Scoring philosophy, MAIN/JIG doctrine, deployment, visual doctrine |
| Session log | `MLB HR ENGINE/wiki/log.md` | Chronological decision history |
| Recent sessions | `MLB HR ENGINE/wiki/sessions/` | Per-session summaries and decisions |

Also consult `CLAUDE.md` at repo root for invariants, protected zones, and architectural rules.

## ADR equivalent

Architectural decisions live in `MLB HR ENGINE/wiki/doctrine/` and `MLB HR ENGINE/wiki/log.md`. No `docs/adr/`. If a proposed change contradicts an existing doctrine file, surface it explicitly rather than overriding silently.

## Vocabulary

Key domain terms: MAIN, JIG, HVY, TCC, EV, Edge, Poisson lambda, CLV, Full Slate. Use these exactly; do not substitute synonyms.

## Do not create without operator authorization

- Root `CONTEXT.md`
- Root `docs/adr/`
- Root `CONTEXT-MAP.md`

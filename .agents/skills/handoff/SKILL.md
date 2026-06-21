---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

# Handoff → LOOPS §8

**Authoritative source:** `AGENTS.md` → LOOPS §8 (PM→CC handoff packet structure)

## Preserved mechanics

- Save to OS temp dir (`$TMPDIR` / `/tmp` / `%TEMP%`) — not the workspace
- Include a "suggested skills" section listing skills the next agent should invoke
- Do not duplicate artifacts (PRDs, plans, ADRs, commits, diffs) — reference by path or URL instead
- Redact sensitive info (API keys, passwords, PII)
- If argument passed, tailor the doc to the next session's stated focus

---
name: read-only-audit
description: Use when you need to inspect repo state, architecture, or behavior without making changes.
---

- Confirm repo root with `git rev-parse --show-toplevel`.
- Confirm branch with `git branch --show-current`.
- Run `git status --short` before any edit attempt.
- Read only the minimum files needed to answer the question.
- Do not modify code, data, formulas, runtime config, or deployment state.
- Report findings with file references and any validation gaps.
- Include final git status in the response.


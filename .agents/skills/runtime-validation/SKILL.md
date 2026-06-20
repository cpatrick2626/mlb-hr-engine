---
name: runtime-validation
description: Use when a change must be checked in the running app, build, or local runtime.
---

- Confirm repo root, branch, and git status before edits.
- Run the smallest relevant validation after the change.
- Prefer build, test, or targeted runtime checks over assumptions.
- Record the exact command(s) run.
- Do not change code solely to silence validation unless the underlying issue is real.
- Report pass/fail, any blockers, and final git status.


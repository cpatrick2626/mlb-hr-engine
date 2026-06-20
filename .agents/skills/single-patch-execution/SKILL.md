---
name: single-patch-execution
description: Use when a change should be made in one minimal patch with no unrelated refactors.
---

- Confirm repo root, branch, and git status before edits.
- Make the smallest safe change.
- Keep the write set narrow and explicit.
- Do not refactor unrelated code.
- Prefer one focused patch over multiple broad edits.
- Stop if the request would touch protected systems without authorization.
- Report files changed and final git status.


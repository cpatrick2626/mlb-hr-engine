---
name: api-payload-contract
description: Use when modifying API payloads, request/response schemas, or integration contracts.
---

- Confirm repo root, branch, and git status before edits.
- Treat API payload shape as protected unless explicitly authorized.
- Preserve backward compatibility unless the task says otherwise.
- Update only the minimum contract surface required.
- Validate payload consumers and serializers where practical.
- Report files changed, validation run, and final git status.


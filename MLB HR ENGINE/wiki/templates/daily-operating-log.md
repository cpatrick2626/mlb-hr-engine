# Daily Operating Log — Template

**Template version:** 1.0  
**Created:** 2026-06-29

---

## Summary

Reusable template for a single session or work day. Create one file per session. Use this to ensure clean agent handoffs — any operator or agent picking up after a session should be able to read this and know exactly what happened, what was validated, what is open, and what to do next.

**Naming convention:** `log-YYYY-MM-DD.md` — stored in `wiki/sessions/`.

---

## Date

YYYY-MM-DD

## Session Type

OPERATIONS / BUILD / AUDIT / RECOVERY / PLANNING

## Goal

<!-- One sentence: what this session was trying to accomplish. -->

---

## Changed

<!-- Files modified. Format: `path/to/file` — what changed and why. One line per file. -->

## Validated

<!-- What was run to confirm changes worked. Include commands, output snippets, or observable results. If nothing was validated, write "Not validated — reason:" and state the reason. -->

## Pushed / Deployed

**Pushed:** YES / NO  
**Deployed:** YES / NO

<!-- If YES: commit hash, deploy target (Fly.io / Vercel / both), deploy status. -->
<!-- If NO: state why (not ready / operator did not authorize / blocked by X). -->

---

## Open Risks

<!-- Anything that could break, degrade, or requires follow-up before the next deploy. If none, write "None identified." -->

## Next Action

<!-- Single most important next step. One sentence. Include the owner: operator / Claude Code / Claude App / other. -->

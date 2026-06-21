---
name: git-guardrails-claude-code
description: Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
---

# Git Guardrails → GIT-HYGIENE + LOOPS §3

**Authoritative source:** `AGENTS.md` → GIT-HYGIENE skill + LOOPS §3 (commit-before-deploy discipline)

## Preserved mechanics (setup reference)

- **Bundled block script:** `scripts/block-dangerous-git.sh` — copy to `.claude/hooks/` (project) or `~/.claude/hooks/` (global); `chmod +x`
- **Scope question:** ask user — project-only (`.claude/settings.json`) or global (`~/.claude/settings.json`)?
- **Verification:** `echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>` → must exit 2 + print BLOCKED to stderr
- **Blocked commands:** `git push` (all variants incl. `--force`), `git reset --hard`, `git clean -f`/`-fd`, `git branch -D`, `git checkout .`, `git restore .`
- **Customization:** after copying script, ask user if they want to add or remove patterns from the blocked list

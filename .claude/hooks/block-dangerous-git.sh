#!/usr/bin/env bash
# Blocks genuinely dangerous git commands inside Claude Code sessions.
# Normal workflow commands (push, commit, add, checkout <branch/path>) are NOT blocked.
# No override — run intentionally dangerous commands from a terminal outside Claude Code.

set -euo pipefail

CMD=$(python -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('command',''))" 2>/dev/null || true)

# DANGEROUS_PATTERNS — each must be a genuinely destructive operation with
# no normal-workflow use inside Claude Code sessions.
#
# NOT included (normal workflow): git push, git commit, git add, git checkout <branch>
#
# Included:
#   push --force / push -f       — overwrites remote history
#   reset --hard                 — discards uncommitted work
#   clean -f / clean -fd         — deletes untracked files/dirs
#   branch -D                    — force-deletes a branch
#   "checkout ."  (literal dot)  — discards all unstaged changes in cwd
#   "restore ."   (literal dot)  — same but via restore syntax

DANGEROUS_PATTERNS=(
  "push[[:space:]]+--force"
  "push[[:space:]]+-f[[:space:]]"
  "push[[:space:]]+-f$"
  "reset[[:space:]]+--hard"
  "clean[[:space:]]+-f"
  "branch[[:space:]]+-D[[:space:]]"
  "checkout[[:space:]]+\.[[:space:]]"
  "checkout[[:space:]]+\.$"
  "restore[[:space:]]+\.[[:space:]]"
  "restore[[:space:]]+\.$"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qE "$pattern"; then
    echo "BLOCKED: dangerous git command detected: $CMD" >&2
    echo "Run this command from a terminal outside Claude Code if intentional." >&2
    exit 2
  fi
done

exit 0

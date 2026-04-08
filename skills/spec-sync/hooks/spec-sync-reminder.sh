#!/usr/bin/env bash
# spec-sync-reminder.sh
#
# Claude Code PostToolUse hook. Fires after every Bash tool call.
# If a git commit was just made AND PRD/RFC docs exist in this project,
# prints a reminder so Claude offers to run /spec-sync.
#
# Install (global):  copy or symlink to ~/.claude/hooks/spec-sync-reminder.sh
# Install (project): copy or symlink to .claude/hooks/spec-sync-reminder.sh
# Then add to settings.json — see skill SKILL.md for the exact config block.

set -euo pipefail

# Parse the bash command from the JSON hook payload on stdin
input=$(cat)
command=$(echo "$input" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || true)

# Only act when a git commit (or merge/rebase that lands commits) just ran
if ! echo "$command" | grep -qE 'git (commit|merge|rebase)'; then
    exit 0
fi

# Check for PRD/RFC docs in common locations
prd_found=false
for dir in "Product requirements" "docs" "specs" "rfcs"; do
    if [ -d "$dir" ] && find "$dir" -maxdepth 2 -name "*.md" 2>/dev/null \
        | grep -qiE "prd|rfc"; then
        prd_found=true
        break
    fi
done

if [ "$prd_found" = true ]; then
    echo "SPEC-SYNC REMINDER: A git commit was just made and PRD/RFC documents exist in this project. Offer to run /spec-sync to keep the documentation in sync with the committed changes."
fi

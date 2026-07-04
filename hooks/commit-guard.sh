#!/usr/bin/env bash
# PreToolUse: enforce Conventional Commits format on git commit.
set -uo pipefail

input=$(cat)

# Extract command field from hook JSON
cmd=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('tool_input',d).get('command',''))" "$input" 2>/dev/null)

[[ -z "$cmd" ]] && exit 0
echo "$cmd" | grep -qE 'git[[:space:]]+commit' || exit 0

# Extract subject from -m flag (single or double quoted)
msg=$(echo "$cmd" | sed -n "s/.*-m[[:space:]]*'\([^']*\)'.*/\1/p" | head -1)
[[ -z "$msg" ]] && msg=$(echo "$cmd" | sed -n 's/.*-m[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
msg=$(echo "$msg" | head -1)

# Can't extract message (heredoc/EDITOR flow) — allow through
[[ -z "$msg" ]] && exit 0

if ! echo "$msg" | grep -qE '^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?: .{1,72}$'; then
  cat >&2 <<EOF
Blocked: commit message must follow Conventional Commits.

  Format : type(scope): description   (description ≤72 chars)
  Types  : feat fix docs style refactor test chore perf ci build revert
  Example: feat(agents): add retry logic to validator

  Got: "$msg"
EOF
  exit 1
fi

exit 0

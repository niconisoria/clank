#!/usr/bin/env bash
# PreToolUse guard for Bash — blocks destructive and dangerous shell patterns.
set -uo pipefail

input=$(cat)

command=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('tool_input',d).get('command',''))" "$input" 2>/dev/null)

# rm -rf (any flag order combining r and f)
if echo "$command" | grep -qE 'rm\s+-[a-zA-Z]*rf[a-zA-Z]*|rm\s+-[a-zA-Z]*fr[a-zA-Z]*|rm\s+--recursive\s+--force|rm\s+--force\s+--recursive'; then
  echo "Blocked: rm -rf — use targeted deletes; confirm with user for destructive removals"; exit 1
fi

# Force push
if echo "$command" | grep -qE 'git\s+push\s+.*(\s-f\b|--force\b)'; then
  echo "Blocked: git force push — confirm with user before overwriting remote history"; exit 1
fi

# Pipe to shell
if echo "$command" | grep -qE '\|\s*(bash|sh|zsh|fish)\b'; then
  echo "Blocked: pipe-to-shell pattern — download and inspect before executing"; exit 1
fi

# Reading sensitive files via shell
if echo "$command" | grep -qE '(cat|less|head|tail|bat)\s+.*\.(env|pem|key|p12|pfx)\b'; then
  echo "Blocked: reading a certificate or key file via shell"; exit 1
fi

exit 0

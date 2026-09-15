#!/usr/bin/env bash
# PreToolUse guard for Bash — blocks destructive and dangerous shell patterns.
set -uo pipefail

input=$(cat)

command=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('tool_input',d).get('command',''))" "$input" 2>/dev/null)

# rm -rf — force + recursive together, any spelling/order/case, combined or separate flags
if echo "$command" | grep -qE '\brm\b' \
  && echo "$command" | grep -qiE -- '(^|\s)-[a-zA-Z]*f[a-zA-Z]*(\s|$)|--force\b' \
  && echo "$command" | grep -qiE -- '(^|\s)-[a-zA-Z]*r[a-zA-Z]*(\s|$)|--recursive\b'; then
  echo "Blocked: rm -rf — use targeted deletes; confirm with user for destructive removals"; exit 1
fi

# Force push — flag may sit right after "push" or anywhere later in the command
if echo "$command" | grep -qE '\bgit\s+push\b' \
  && echo "$command" | grep -qE -- '(^|\s)(-f|--force)($|\s)'; then
  echo "Blocked: git force push — confirm with user before overwriting remote history"; exit 1
fi

# Pipe to shell
if echo "$command" | grep -qE '\|\s*(bash|sh|zsh|fish)\b'; then
  echo "Blocked: pipe-to-shell pattern — download and inspect before executing"; exit 1
fi

# Reading sensitive files via shell
if echo "$command" | grep -qiE '(cat|less|head|tail|bat)\s+.*\.(env|pem|key|p12|pfx)\b'; then
  echo "Blocked: reading a certificate or key file via shell"; exit 1
fi

exit 0

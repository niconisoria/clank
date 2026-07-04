#!/usr/bin/env bash
# PreToolUse guard for Write and Edit — blocks sensitive paths and secret content.
set -uo pipefail

input=$(cat)

file_path=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); ti=d.get('tool_input',d); print(ti.get('file_path',''))" "$input" 2>/dev/null)
content=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); ti=d.get('tool_input',d); print(ti.get('content',ti.get('new_string','')))" "$input" 2>/dev/null)

# Block sensitive filenames
case "$file_path" in
  .env|.env.*|*/.env|*/.env.*)
    echo "Blocked: writing to .env file — use environment config, not file writes"; exit 1 ;;
  *.pem|*.key|*.p12|*.pfx)
    echo "Blocked: writing to certificate/key file $file_path"; exit 1 ;;
  *secret*|*credential*|*private_key*)
    echo "Blocked: filename contains sensitive keyword ($file_path)"; exit 1 ;;
esac

# Block writes to bin/
case "$file_path" in
  bin/*|./bin/*)
    echo "Blocked: agents must not modify bin/ scripts — execute them, don't edit them"; exit 1 ;;
esac

# Block writes outside the project root (absolute paths pointing elsewhere)
project_root=$(pwd)
case "$file_path" in
  /*)
    if [[ "$file_path" != "$project_root"* ]]; then
      echo "Blocked: write target $file_path is outside the project root"; exit 1
    fi ;;
esac

# Secret pattern scan in content
if printf '%s' "$content" | grep -qE \
  '(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)'; then
  echo "Blocked: content appears to contain a secret or private key"; exit 1
fi

exit 0

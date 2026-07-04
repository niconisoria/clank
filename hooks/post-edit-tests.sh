#!/usr/bin/env bash
# PostToolUse: run tests after Write/Edit — skip docs/config, skip unknown framework.
set -uo pipefail

input=$(cat)

file_path=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); ti=d.get('tool_input',d); print(ti.get('file_path',''))" "$input" 2>/dev/null)

[[ -z "$file_path" ]] && exit 0

case "$file_path" in
  *.md|*.json|*.yaml|*.yml|*.txt|*.lock|*.toml) exit 0 ;;
  .claude/*|docs/*) exit 0 ;;
esac

CMD=""
if [ -f Gemfile ] && grep -qE "gem ['\"]rspec" Gemfile 2>/dev/null; then
  CMD="bundle exec rspec"
elif [ -f Gemfile ] && grep -qE "gem ['\"]minitest" Gemfile 2>/dev/null; then
  CMD="bundle exec rails test"
elif [ -f package.json ]; then
  CMD=$(node -e "const p=require('./package.json');const d={...p.devDependencies,...p.dependencies};const m={'jest':'npx jest','vitest':'npx vitest run','mocha':'npx mocha','jasmine':'npx jasmine','ava':'npx ava'};const f=Object.keys(m).find(k=>k in d);if(f)console.log(m[f])" 2>/dev/null || true)
elif [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -f setup.cfg ]; then
  CMD="python -m pytest"
elif [ -f go.mod ]; then
  CMD="go test ./..."
elif [ -f Cargo.toml ]; then
  CMD="cargo test"
elif [ -f pom.xml ]; then
  CMD="mvn test -q"
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  CMD="./gradlew test"
elif [ -f mix.exs ]; then
  CMD="mix test"
elif [ -f Package.swift ]; then
  CMD="swift test"
fi

[[ -z "$CMD" ]] && exit 0

output=$(bash -c "$CMD" 2>&1)
exit_code=$?
echo "$output"
exit 0

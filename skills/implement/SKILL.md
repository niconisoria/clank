---
name: implement
description: TDD implementation. Reads spec, researches prior art, writes failing tests, implements until tests pass, then hands off to /review.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# i-dunno:implement

Caveman mode: terse, no filler, compress aggressively.

Input: spec file path.

Read `docs/MEMORY.md`, `CLAUDE.md` (if present), `docs/architecture.md` (if present), and the target spec. If the spec contains `### UI`, also read `docs/design-system.md` (if present). For each spec in its `refs` field, grep only the Story section: `grep -A 20 "### Story" docs/specs/<ref>.md` — do not read the full ref spec. Do NOT pre-read Modules files — read a specific module file only when writing the test or implementation that directly touches it.

Spec sections to read and use:
- `### Story` — acceptance criteria; drives tests
- `### Architecture` — structural constraints and design decisions. If absent, treat as `(none)`.
- `### UI` — interface and interaction requirements. If absent, treat as `(none)`.
- `### Design` / `### Modules` — file paths for test derivation

File writes: use `Write` for new files, `Edit` for files that already exist on disk.

Check `CLAUDE.md` for a framework entry (format: `- framework: Name`) and a `- test_cmd: <CMD>` line — skip detection if both already recorded. Otherwise detect framework by checking project files in this order:

| File present | Framework | Test command |
|---|---|---|
| `Gemfile` with `rspec` | RSpec | `bundle exec rspec` |
| `Gemfile` with `minitest` | Minitest | `bundle exec rails test` |
| `package.json` devDeps has `jest` | jest | `npx jest` |
| `package.json` devDeps has `vitest` | vitest | `npx vitest run` |
| `package.json` devDeps has `mocha` | mocha | `npx mocha` |
| `package.json` devDeps has `jasmine` | jasmine | `npx jasmine` |
| `package.json` devDeps has `ava` | ava | `npx ava` |
| `pyproject.toml` or `pytest.ini` or `setup.cfg` | pytest | `python -m pytest` |
| `go.mod` | Go test | `go test ./...` |
| `Cargo.toml` | cargo test | `cargo test` |
| `pom.xml` | JUnit | `mvn test -q` |
| `build.gradle` or `build.gradle.kts` | JUnit 5 | `./gradlew test` |
| `mix.exs` | ExUnit | `mix test` |
| `Package.swift` | XCTest | `swift test` |

If no match, ask the user what command to run tests with. Store the answer in `CLAUDE.md` as `- framework: <Name>` and `- test_cmd: <CMD>`; use `<CMD>` as `TEST_CMD` for the rest of this session (`/review` and `/validate` read the same line later, so it must be saved even when detected automatically).

## Research

Check prior spec count: `find docs/specs/ -name "*.md" | wc -l`. If ≤1, skip to **Test**.

Extract key topic from spec title and key terms from Story section. Build pattern: join topic and all terms with `|`.

Run:
1. `find docs/specs/ -name "*.md" -exec grep -liE "PATTERN" {} + 2>/dev/null`
2. `grep -rlE "PATTERN" . --include="*.rb" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.bundle --exclude-dir=.git 2>/dev/null`

For each matching spec: verify `status:` frontmatter exists (`grep -m1 "^status:" <file>`), then grep only `### Story` and `## Summary` sections. For each matching implementation file: grep PATTERN with 3 lines of context. Do not read full files. Use findings to inform tests and implementation decisions. If nothing found, proceed without.

## Test

1. Derive the test file path from the `### Modules` list in the Design section. Write tests from the acceptance criteria in the Story section.
2. Run `TEST_CMD`. All tests must fail — if any pass, the test is not specific enough or implementation already exists; fix the tests before continuing.

## Code

3. Write implementation to make them pass.
4. Run `TEST_CMD`. All tests must pass. If any fail, fix the implementation and re-run. Maximum 5 attempts — if still failing, stop and show the failing output, ask how to proceed.

## Handoff

Print:

```
Tests pass. Handing off.
spec: <spec path>
Run:
/review <spec path>
```

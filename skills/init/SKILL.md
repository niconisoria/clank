---
name: init
description: Bootstrap CLAUDE.md — tech stack, folder purposes, and iron-law rules only, per this project's own scope rule (everything else lives in docs/). Use when a project has no CLAUDE.md yet, or the user wants to (re)generate it.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
---

# i-dunno:init

Caveman: terse, no filler, compress aggressively.

CLAUDE.md holds exactly three kinds of fact: tech stack, project folder purposes, iron-law non-negotiable rules. Nothing else — feature details, decision rationale, architecture, design tokens all go in `docs/` (see `/gc`, which prunes drift back out of CLAUDE.md later).

Format: flat `- key: value` bullets, one per line, no headers, no nesting. Other skills grep exact prefixes (`^- test_cmd:` etc) — never indent a bullet or wrap it in a header.

## If CLAUDE.md already exists

Read it. Show current content. Ask: regenerate from scratch, add missing pieces only, or stop. Never silently overwrite.

## Tech stack

Detect framework + test command from project files — same table `/implement` uses:

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

If no match, ask the user for the test command. Derive the language from the same evidence (which manifest/lockfile is present) and combine with the framework into one line: `- tech stack: Node.js, Jest`.

## Folder purposes

List top-level directories, skipping `.git`, `node_modules`, `vendor`, `dist`, `build`, and dotfiles/dot-directories. For each, peek at a few filenames inside (do not read full files) to infer a one-line purpose. Ask the user only for directories whose purpose can't be inferred from naming plus a glance.

## Iron laws

Non-negotiable rules can't be detected from files alone. Check first: existing hooks (`hooks/*.sh`, `.claude/hooks/`), linter configs, and CI checks — each one already encodes an iron law (e.g. a pre-commit block on `.env` writes means "never commit secrets"). Turn each into one line. If at least one iron law was derived this way, that's enough — write CLAUDE.md now, don't block the write on asking for more. Only ask the user (up to 3 questions, skip if they say none) when nothing at all could be derived.

## Write

```markdown
- tech stack: <language>, <framework>
- framework: <Name>
- test_cmd: <CMD>
- <path>/: <purpose>
- <path>/: <purpose>
- iron law: <rule>
```

Show this block directly — no headers, no "detected:" labels, no narration wrapping it. It's the literal CLAUDE.md content, not a description of what you found.

Write to `CLAUDE.md` at project root via `Write` (new file) or `Edit` (existing file, append-only — never touch lines already there). Tell the user the file path and how many lines written. Mention `/gc` for catching scope drift later.

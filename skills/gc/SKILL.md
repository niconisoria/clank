---
name: gc
description: Memory garbage collector for CLAUDE.md and docs/MEMORY.md. Flags stale, duplicate, derivable, and out-of-scope entries, asks for approval, then removes them.
allowed-tools:
  - Read
  - Edit
  - Bash
---

# clank:gc

Caveman: terse, no filler, compress aggressively.

Scan `CLAUDE.md`, `docs/MEMORY.md`, `docs/architecture.md`, and `docs/design-system.md` (each if present) for facts that no longer earn their place.

## Scan

Read each file. Skip files that do not exist. For each distinct fact or entry, apply these checks in order — first match wins:

**SCOPE** — entry is in `CLAUDE.md` and is not tech stack, project folder purpose, or an iron-law non-negotiable rule. Flag as out-of-scope and suggest the right home: system-wide structural decisions → `docs/architecture.md`; design tokens, color, UI rules → `docs/design-system.md`; decision rationales → `docs/MEMORY.md`; feature-specific details → the relevant spec's `## Summary`.

**STALE** — entry names a file path or module. Run `find . -path "*<path>*" -not -path "./.git/*"`. If nothing returned, it is stale.

**DUP** — same fact appears in both files. The CLAUDE.md copy is canonical; flag the `docs/MEMORY.md` copy.

**DERIV** — fact is mechanically derivable with no ambiguity. For framework entries: detect by checking project files (Gemfile content → RSpec/Minitest; package.json devDeps → jest/vitest/mocha/jasmine/ava; pyproject.toml or pytest.ini → pytest; go.mod → Go test; Cargo.toml → cargo test; pom.xml → JUnit; build.gradle → JUnit 5; mix.exs → ExUnit; Package.swift → XCTest) — only flag if the detected value is non-empty, not `unknown`, and matches the entry's value. For language entries: flag only if a canonical lockfile exists (Gemfile, package.json, requirements.txt, go.mod, Cargo.toml). Do not flag entries whose value the detector cannot produce — they were set manually for a reason.

**UNVERF** — entry claims a pattern, convention, or library is in use. For each entry that reaches this check, extract its specific key terms (library names, class names, method names — skip generic words under 5 chars). Run one grep per entry:

`grep -rlE "TERM" . --include="*.rb" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.bundle --exclude-dir=.git --exclude-dir=spec --exclude-dir=test 2>/dev/null`

If no source files match and the term also does not appear in any config file (Gemfile, package.json, requirements.txt, go.mod), flag as unverifiable.

If a fact passes all checks, skip it — do not list it.

## Report

Print one line per flagged entry:

```
SCOPE   CLAUDE.md:12        `Invoices are generated nightly via InvoiceJob` — feature detail, belongs in docs/specs/<spec>.md Summary
STALE   docs/MEMORY.md:4   `- auth: JWT via lib/auth.rb` — lib/auth.rb not found
DUP     docs/MEMORY.md:7   `- framework: Rails` — already in CLAUDE.md line 2
DERIV   docs/MEMORY.md:9   `- test_runner: pytest` — derivable from project files (pyproject.toml present)
UNVERF  CLAUDE.md:15        `Use service objects for business logic` — no grep match
```

If nothing flagged, say: `Nothing to collect.` and stop.

Ask: approve all removals, pick by number, or skip.

## Apply

For each approved entry: edit the file, delete the line. Preserve surrounding whitespace. Do not reformat or reorder anything else.

Confirm how many lines removed from each file.

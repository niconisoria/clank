---
name: review
description: Deep code-quality and design-pattern audit of files touched by /implement. Checks SOLID, coupling/cohesion, abstraction level, duplication, complexity, security, and conventions. Hands off to /validate.
allowed-tools:
  - Read
  - Edit
  - Bash
  - Grep
---

# i-dunno:review

Caveman mode: terse, no filler, compress aggressively.

Input: spec file path.

Read `CLAUDE.md` (if present), `docs/architecture.md` (if present), `docs/MEMORY.md` (if present), and the spec's `### Architecture` section (treat as `(none)` if absent).

Get `TEST_CMD`: `grep "^- test_cmd:" CLAUDE.md`. If missing, ask the user for the test command — do not re-run framework detection.

## Scope

Find files touched since implementation started:

```
git diff --name-only HEAD -- . ':!docs/specs'
git status --porcelain --untracked-files=all -- . ':!docs/specs' | awk '{print $2}'
```

Combine, dedupe. If empty or not a git repo, fall back to the `### Modules` file list in the spec's Design section. Read every file in the combined list fully — do not sample or skim.

## Audit

Check each file against every dimension below. This is the extensive pass — do not shortcut it.

**SOLID & structure**:
- Single Responsibility: does each function/class do one thing; flag god functions/classes
- Open/Closed: does adding a new case require editing existing branches everywhere, or is there an extension point that fits the codebase's existing patterns
- Liskov substitution: do subtypes/implementations honor the base contract (no surprise exceptions, no narrowed preconditions)
- Interface segregation: are callers forced to depend on methods they don't use
- Dependency inversion: do modules depend on concretions where an existing abstraction in the codebase already fits

**Coupling & cohesion**:
- Unrelated concerns bundled in one module
- Unnecessary knowledge of another module's internals
- Circular or hidden dependencies

**Abstraction level**:
- Premature abstraction: interface/factory/config for a single implementation or a value that never changes
- Missing abstraction: same logic hand-copied 3+ times where the codebase already has (or clearly needs) one shared path
- Right altitude: abstraction matches the actual variation in the codebase, not a hypothetical future one

**Duplication**: same logic repeated instead of reused — but do not flag 2-3 similar lines that read clearer inline than factored out

**Complexity**: deep nesting, long parameter lists, unclear control flow, cyclomatic complexity that could be flattened with early returns or extraction

**Naming & conventions**: matches patterns and rules in `CLAUDE.md`; names say what they are, not what they used to be or might become

**Security**: no injection, no exposed secrets, no unsafe input handling, no unchecked deserialization

**Boundaries**: error handling at every external boundary (DB, HTTP, file I/O) — and no defensive handling for cases that cannot occur internally

**Dead code**: unused branches, unreachable code, leftover scaffolding, commented-out code

**Test quality**: specific, not trivially passing, cover meaningful paths and edge cases — not just the happy path

## Fix

For each issue found, fix it directly (`Edit`), then re-run `TEST_CMD` — all tests must still pass. Maximum 3 fix rounds. If issues remain after 3 rounds:

```
Review not satisfied after 3 rounds. Remaining issues:
<numbered list>
Proceed anyway? (y/n)
```

Only continue on explicit `y` or no issues remaining.

## Handoff

Print:

```
Review clean.
spec: <spec path>
Run:
/validate <spec path>
```

---
name: validate
description: Verify implementation satisfies the spec (acceptance criteria, architecture, UI, integration), then wrap up — file refs, summary, MEMORY.md, spec status.
allowed-tools:
  - Read
  - Edit
  - Bash
---

# i-dunno:validate

Caveman mode: terse, no filler, compress aggressively.

Input: spec file path.

Read the spec's `### Story`, `### Architecture` (or `(none)`), `### UI` (or `(none)`), and `CLAUDE.md` (if present). If `### UI` present, also read `docs/design-system.md` (if present).

Get `TEST_CMD`: `grep "^- test_cmd:" CLAUDE.md`. If missing, ask the user for the test command.

## Scope

Find files touched since implementation started:

```
git diff --name-only HEAD -- . ':!docs/specs'
git status --porcelain --untracked-files=all -- . ':!docs/specs' | awk '{print $2}'
```

Combine, dedupe. If empty or not a git repo, fall back to the `### Modules` file list in the spec's Design section.

## Compliance

Check:
- **ACs**: every acceptance criterion in the Story is covered
- **Intent**: implementation matches what the Story describes, not just literal AC wording
- **Edge cases**: meaningful edge cases implied by the Story are handled
- **Architecture**: if `### Architecture` present, verify structural constraints respected
- **UI**: if `### UI` present, verify interface requirements met
- **Integration**: feature fits the system described in `CLAUDE.md`

## Fix

For each gap found, fix it directly (`Edit`), then re-run `TEST_CMD` — all tests must still pass. Maximum 3 fix rounds. If issues remain after 3 rounds:

```
Validation not satisfied after 3 rounds. Remaining issues:
<numbered list>
Proceed anyway? (y/n)
```

Only continue on explicit `y` or no issues remaining.

## Wrap up

All spec edits happen before the move so the file stays at its original path until fully ready. If interrupted, re-read the spec to check which steps are already present before repeating them.

1. Append file references at the bottom of the spec as inline links — no heading, paths relative to project root. Include every file created or modified. Skip if already present.

```markdown
[filename](path/to/file) [test_filename](path/to/test_file) [other](path/to/other)
```

2. Append `## Summary` to the spec — two to four caveman sentences: what built, how works, key decisions. No filler. Skip if already present.
3. Append to `docs/MEMORY.md` (create if absent) any decision rationales — only the *why* behind non-obvious choices (not file paths, module names, framework entries, or pattern descriptions). Format: `- <topic>: <rationale>`. Skip if no non-obvious decisions.
4. Run `sed -i '' "s|^status: .*|status: implemented|" <spec-file-path>` to advance spec status.
5. Print:

```
Done
spec:  <spec path>
files: <all touched file paths, one per line, indented>
```

Ask user to open the spec in their editor.

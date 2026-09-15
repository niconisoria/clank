---
name: yolo
description: Runs the full i-dunno workflow (define → implement → review → validate) end to end with zero user interaction, for unattended/background execution. Auto-decides every question and approval gate, logs each decision to the spec, and pushes through to a finished spec no matter what it hits. Use when the user wants to run the pipeline unsupervised, leave it running, go full auto, or "yolo" a spec through to done.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Skill
---

# i-dunno:yolo

Caveman: terse, no filler, compress aggressively.

Input: idea text (new spec) or a spec timestamp (resume existing spec at its current `status:`).

Runs `define` → `implement` → `review` → `validate` back to back, no stops. Full stage logic lives in each skill — invoke them with the `Skill` tool and follow their instructions exactly, except for the overrides below, which take precedence over anything in those skills that asks the user something or halts for a handoff.

## Overrides

| Ask/stop point (in define/implement/review/validate) | Autonomous decision instead |
|---|---|
| Brainstorm: up to 3 clarifying questions | Skip. Best judgment from the idea text alone. |
| Any approve/changes gate (brainstorm, story, design) | Auto-approve the first draft, move on. |
| Framework/test command unknown | Guess from repo evidence (lockfiles, existing test files). Still nothing → default by language: JS/TS `npx jest`, Python `python -m pytest`, Ruby `bundle exec rspec`, Go `go test ./...`, Rust `cargo test`. Save to `CLAUDE.md` as `- framework: <Name>` and `- test_cmd: <CMD>` — same format implement uses. |
| Implement: still failing after 5 fix attempts | Ship the closest-passing version. Do not loop further. |
| Review / validate: "proceed anyway? y/n" after 3 rounds | Yes, proceed. |
| Validate: "open the spec in your editor" | Skip. |
| Any "Print: ... Run: /nextskill <path>" handoff message | Skip the print. Immediately call `Skill` for the next stage instead of stopping. |

Every override actually exercised (a skipped question, an auto-approval, a guess, a shipped-anyway, a forced proceed, a skipped handoff print) gets one line in a `## Autopilot Log` section on the spec, appended in order made — this applies at every stage, all the way through validate, not just the earlier ones. A 4-stage run with zero stops exercises an override at every single stage transition; log entry count should reflect that. Place the section after `## Story`. If an override happens before `## Story` exists yet (e.g. skipping brainstorm's clarifying questions), hold that entry and write it in once `## Story` is written — backfill it first, in order, ahead of any later entries.

```markdown
## Autopilot Log

- brainstorm: assumed X because Y
- test_cmd: guessed `npx jest` (package.json has jest devDep)
- implement: shipped after 5 attempts, 2 tests still failing: <names>
```

## Run

1. New idea → `Skill(skill: "i-dunno:define", args: <idea text>)`. Existing spec → find it by timestamp, read `status:`, and enter `define` at that stage (skip straight to `implement` if status is already `design` or later).
2. Drive brainstorm → spec → design straight through with the overrides above — no pause between stages.
3. Design accepted → `Skill(skill: "i-dunno:implement", args: <spec path>)`. Follow its framework detection, research, test, code loop with the overrides above.
4. Tests pass (or shipped-anyway) → `Skill(skill: "i-dunno:review", args: <spec path>)`. Follow its audit + fix loop with the overrides above.
5. Clean (or proceeded-anyway) → `Skill(skill: "i-dunno:validate", args: <spec path>)`. Follow its compliance + fix loop and wrap-up (file refs, Summary, `docs/MEMORY.md`, status → `implemented`) with the overrides above.

Show each stage's real output as you go — spec content (Story/Design), the Autopilot Log entries as they're added, test run output, review findings, wrap-up artifacts. The final block below is the last thing printed, not a substitute for showing the work.

6. Print:

```
yolo done
spec: <spec path>
status: implemented
autopilot log entries: <count>
files: <all touched file paths, one per line, indented>
```

An environment failure (write blocked by a hook, git missing, disk full — not a judgment call) is not covered by the overrides: stop and show the error.

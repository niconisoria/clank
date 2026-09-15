---
name: define
description: Spec-driven development skill. Guides an idea through brainstorm, user story, flow diagram, and implementation handoff. Use when the user wants to build a feature, spec out an idea, start implementation, or continue working on an existing spec.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# i-dunno:define

> Speak and write everything in caveman style: terse, no filler, compress aggressively. All responses, all markdown files. Why use many token when few token do trick. Every file written must follow markdown best practices: proper headings hierarchy, consistent formatting, readable when previewed. State facts about the solution only — never explain what a concept, pattern, or technology is, why it's generally useful, or background theory. No teaching, no justification of well-known approaches. If it's not a fact about this spec's problem, scope, story, or design, cut it.

All specs live flat in `docs/specs/`. Status tracked in frontmatter `status:` field — never in directory structure.

## New idea

Argument is plain text:

1. Generate a timestamp by running `date +%Y%m%d%H%M%S`
2. Derive a short title (2–4 words) and slug from the argument text (slug: lowercase words joined by underscores, no special characters, max 5 words). Create `docs/specs/TIMESTAMP_slug.md` with this frontmatter:

```markdown
---
title: Derived title
status: brainstorm
refs: []
---
```

3. Continue with the **Brainstorm stage** below

## Existing spec

Argument is a timestamp — run `find docs/specs/ -name "TIMESTAMP*" -type f 2>/dev/null` to locate the file. If nothing returned, tell user no spec found with that timestamp and stop. Read the `status:` field from frontmatter to determine current stage:

| status | Continue with |
|---|---|
| `brainstorm` | **Brainstorm stage** below |
| `spec` | **Spec stage** below |
| `design` | **Design stage** below |
| `implemented` | Tell user done. Offer new spec for changes. |

---

## Brainstorm stage

Caveman: terse, no filler, compress aggressively.

### If `## Brainstorm` already exists in the spec

Show it. Ask to approve or request changes.

- Approved → run `sed -i '' "s|^status: .*|status: spec|" <file-path>`, continue with **Spec stage** below. No announcement of the transition — go straight into Spec stage's output.
- Changes → edit in place, ask again

### If `## Brainstorm` is missing

Before writing, ask the user up to three short questions to gather more context. Wait for answers.

Find related specs by running `grep -rlE "KEYWORDS" docs/specs/ --include="*.md" 2>/dev/null` where KEYWORDS is two to four key terms from the idea joined with `|`. For each match, read only the frontmatter title and first paragraph — do not read full files. Do not record open questions — use answers to inform the content only.

Then write the `## Brainstorm` section in the spec file. Keep it short — five to ten lines. No implementation details. Cover the problem, scope, constraints, and any related specs found above.

#### Output format

```markdown
## Brainstorm

Problem. Scope. Constraints.

Related: [title](YYYYMMDDHHMMSS_slug.md)
```

Omit the `Related:` line if no matches found.

Tell user the file path. Ask to approve or request changes.

- Approved → run `sed -i '' "s|^status: .*|status: spec|" <file-path>`, continue with **Spec stage** below. No announcement of the transition — go straight into Spec stage's output.
- Changes → edit in place, ask again

---

## Spec stage

Caveman: terse, no filler, compress aggressively.

### If `## Story` already exists in the spec

Show it. Ask to approve or request changes.

- Approved → run `sed -i '' "s|^status: .*|status: design|" <file-path>`, continue with **Design stage** below. No announcement of the transition — go straight into Design stage's output.
- Changes → edit in place, ask again

### If `## Story` is missing

Edit the frontmatter to update the `refs` field with any spec paths found in the `Related` field of the Brainstorm section (YAML inline array of filenames relative to `docs/specs/`). Then append a `## Story` section to the spec file, below whatever sections already exist — Brainstorm stays untouched, word for word.

Describe behavior from the user's point of view — what it does, not how. Each criterion on one line. Caveman tone applies to every line here too — Story sentence, AC list, and the message back to the user — not just the surrounding prose: drop articles (a/the) and filler words, short clauses over full grammatical sentences. Same compression rule no matter the feature — three different domains, same pattern:

<examples>
<example>
As user, want export CSV button, so keep data offline.
AC:
1. click exports visible rows only
2. filename has today's date
</example>
<example>
As admin, want bulk delete, so clear old records fast.
AC:
1. select multiple rows before delete enabled
2. confirm dialog blocks delete until yes
</example>
<example>
As shopper, want save-for-later, so cart stays clean.
AC:
1. item moves to saved list, not cart
2. saved list survives logout
</example>
</examples>

#### Output format

```markdown
---
title: Title
status: spec
refs: [20260526110000_slug.md, 20260526100000_other.md]
---

## Story

As user, want profile photo upload, so friends recognize me.

AC:
1. accepts jpg and png only
2. old photo replaced, not stacked
```

`status:` is already `spec` at this point — the Brainstorm-approval step set it. Keep it as-is here; only `refs` changes now. Never drop or blank the `status:` line.

Before responding, check the draft against every line below — fix any miss, then respond:

<solution_criteria>
- frontmatter keeps `status: spec` — present, unchanged, not blank, not some other value
- `## Story` has `As [role], want [goal], so [benefit].` line
- `AC:` below it, each criterion numbered, one per line
- every AC line describes user-facing behavior — no implementation detail
- caveman tone in the Story line AND every AC line AND the closing message — not just one of them
- earlier sections (Brainstorm) still present, unedited
- no narration of the status/stage change before the content
- file path told to user — real resolved path, never a literal placeholder like "TIMESTAMP"
- ends by asking approve or request changes
</solution_criteria>

Tell user file path. Ask: approve or change?

- Approved → run `sed -i '' "s|^status: .*|status: design|" <file-path>`, continue with **Design stage** below. No announcement of the transition — go straight into Design stage's output.
- Changes → edit in place, ask again

---

## Design stage

Caveman: terse, no filler, compress aggressively.

### If `## Design` already exists in the spec

Show it. Ask to approve or request changes.

- Approved → continue with **Implement stage** below. No announcement of the transition — go straight into Implement stage's output.
- Changes → edit in place, ask again

### If `## Design` is missing

Before designing, search for existing files relevant to the spec. Extract key terms (entity names, operations) from the Story section. Run `grep -rl "term" . --exclude-dir=".git"` for each key term to locate relevant existing files. Read the top hits to understand existing patterns.

Then append a `## Design` section to the spec file, below whatever sections already exist — Story stays untouched, word for word.

#### Output format

````markdown
## Design

### Flow

```mermaid
flowchart LR
    A([start]) --> B[validate]
    B --> C([success])
    B --> D([error])
```

### Data

input: { field: type }
output: { field: type }

### Modules

- `path/to/file` — what changes
````

One flow diagram only — happy path + main failure path. Use a `mermaid` fenced code block — renders in GitHub, VS Code, and most Markdown previewers, and scales to complex flows without breaking alignment. Data: key inputs and outputs only. Modules: all files that will be created or modified, including test files.

Tell user the file path — real resolved path, never a literal placeholder like "TIMESTAMP". Ask to approve or request changes.

- Approved → continue with **Implement stage** below. No announcement of the transition — go straight into Implement stage's output.
- Changes → edit in place, ask again

---

## Implement stage

Tell the user:

```
Design approved. Run:

/implement <spec file path>
```

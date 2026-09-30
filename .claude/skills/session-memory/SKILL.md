---
name: session-memory
description: |
  Persistent, disciplined memory for a project across work sessions. One
  skill, two modes:
  START (read-only) — brief yourself at the top of a session: detect the
  current project (or, if multiple projects are registered, scan all of
  them — git and non-git — sorted by recent activity and let you pick),
  read its MEMORY.md/ERRORS.md/BACKLOG.md, and output a tight "where did I
  leave off" briefing.
  END (writes) — cascade updates when you're done: write only the docs that
  actually changed — project log, optional cross-project log, backlog,
  error log — with no manual triage.
  Use when saying "start session", "starting session", "what was I working
  on", "session end", "wrapping up", "end session", "/session-memory",
  "/session-memory start", "/session-memory end".
---

# session-memory

One skill, two modes. **Mode is determined first, before anything else
runs** — see Step 0.

---

## Step 0: Determine mode

Look at what triggered this skill:

- Explicit arg `start` (e.g. `/session-memory start`), or phrasing like
  "start session", "starting session", "what was I working on" → **START
  mode**. Go to [START mode](#start-mode).
- Explicit arg `end` (e.g. `/session-memory end`), or phrasing like "session
  end", "wrapping up", "end session" → **END mode**. Go to [END mode](#end-mode).
- Invoked with no arg and no clear phrasing (e.g. bare `/session-memory`) →
  default to **START mode** — it's read-only, so defaulting to it is always
  safe. Never default to END mode.

Do not run both modes in one invocation. Pick one and execute only that
section below.

---

## START mode

Read-only. No file writes. No code changes. Your only output is a briefing.

### S0: Determine single- vs multi-project

Check for a global config at `~/.claude/session-memory/config.json`
(`~` = home directory).

```bash
cat "$HOME/.claude/session-memory/config.json" 2>/dev/null
```

- **If invoked with an explicit project path or name** (e.g.
  `/session-memory start my-app`) — single-project mode on that target
  (match `<name>` against the `projects` list in the global config if one
  exists, or treat it as a literal path). Skip scanning. Go to S2.
- **If the global config exists and lists 2+ projects** — multi-project
  mode. Go to S1.
- **Otherwise** (no global config, or fewer than 2 projects listed) —
  single-project mode, root = current working directory. Go to S2.

### S1: Multi-project scan (only in multi-project mode)

For each entry in the config's `projects` array (`{"name": ..., "path":
...}`, `~` expanded), determine its recency signal, in this priority order:

1. **Marker file** (most reliable, works for git and non-git alike) —
   `<project-path>/.claude/session-memory/.last-active`, written by END mode
   each time a session closes there. Contains one line: an epoch timestamp.
   ```bash
   cat "<project-path>/.claude/session-memory/.last-active" 2>/dev/null
   ```
2. **Git commit time** (fallback, git projects only — e.g. a project never
   closed with this skill yet):
   ```bash
   git -C "<project-path>" log -1 --format="%ct|%cr|%s" 2>/dev/null
   ```
3. **Never active** — no marker, not a git repo (or a git repo with no
   commits). Sort last; drop from the shortlist if 3+ other projects already
   have a real signal.

Build one row per project: `name|path|epoch|human-relative|label`. Prefer
the marker-based label ("last session <relative-time>") over the commit
label when both exist. For a git project with only a commit (no marker yet),
label with the commit subject. For "never active", label "no activity yet".

Sort descending by epoch. Take the top 3.

**Present via AskUserQuestion**, multiSelect enabled (briefing on more than
one project at once is a real use case):

```
<name> — <label>
```
Examples:
- `my-app — a2f91c ("fix auth redirect") 2h ago`
- `notes-vault — last session 3 days ago`
- `Other — tell me which project`

**Do not proceed past this point until the user has selected at least one
project.** For each selected project, run S2–S4 once, using that project's
path as the root. Output one briefing block per project (S4), then a single
closing line (S5) at the end.

### S2: Resolve the project root and per-project config

For the current project (the CWD in single-project mode, or the selected
path in multi-project mode):

```bash
cd "<project-root-candidate>" 2>/dev/null
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
echo "GIT_ROOT: ${GIT_ROOT:-none}"
```

- If `GIT_ROOT` resolved, that's the root — a **git project**.
- If empty, this is a **non-git project**: use the candidate path itself as
  root, and note it once in single-project mode ("No git repo detected —
  using CWD as project root: `<path>`"). In multi-project mode this needs no
  extra note — non-git projects are expected and already labeled as such in
  S1.

**Guard against a false-positive root**: `git rev-parse --show-toplevel`
walks *up* the directory tree looking for a `.git` — if the candidate path
is a plain subfolder someone is working in casually (no `.git` of its own)
but happens to sit inside an unrelated ancestor repo (e.g. the user's whole
home directory is itself a git repo), `GIT_ROOT` will silently resolve to
that ancestor instead of the folder actually being worked in. Before trusting
`GIT_ROOT`, check it against the home directory:
```bash
if [ "$GIT_ROOT" = "$HOME" ]; then
  echo "GIT_ROOT resolved to your home directory — likely an unrelated parent repo, not this project."
fi
```
If `GIT_ROOT` equals `$HOME` (or another directory clearly unrelated to the
candidate path — e.g. several levels above it with nothing that looks like
this project), **do not treat it as this project's root**. Fall back to the
candidate path itself, treat it as a non-git project for this run, and say
so once: "Detected an unrelated parent git repo at `<GIT_ROOT>` — using
`<candidate-path>` directly instead." This prevents session docs from being
written into the wrong repo.

Look for `.claude/session-memory.json` at this root (per-project overrides —
distinct from the global multi-project config in S0; `globalMemory` inside
it, if set, is a `~`-prefixed path — expand `~` to the home directory
wherever you read or write it):

```json
{
  "globalMemory": "~/.claude/session-memory/MEMORY.md",
  "docs": { "memory": "MEMORY.md", "errors": "ERRORS.md", "backlog": "BACKLOG.md" }
}
```

If absent, use the defaults shown above (no global log, standard filenames).
START mode never creates this file — only END mode does.

### S3: Pull latest (git projects only, best-effort)

Skip entirely for non-git projects.

```bash
BRANCH=$(git branch --show-current 2>/dev/null)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
if [ -n "$UPSTREAM" ]; then
  git pull 2>&1
else
  echo "NO_UPSTREAM"
fi
```

Report one line: `✓ pulled <branch> (N new commits)`, `✓ already up to
date`, `✗ pull failed: <reason>` (continue anyway — never blocks the
briefing), or skip silently if `NO_UPSTREAM`.

### S4: Read the docs and output the briefing

Using the paths resolved in S2:

```bash
echo "=== MEMORY ==="
tail -60 "<memory-doc-path>" 2>/dev/null
echo "=== ERRORS ==="
tail -40 "<errors-doc-path>" 2>/dev/null
echo "=== BACKLOG ==="
grep -i "<project-name>" "<backlog-doc-path>" 2>/dev/null | head -20
```

If `globalMemory` is configured, also pull recent lines mentioning this
project:

```bash
grep -i "<project-name>" "<globalMemory-path>" 2>/dev/null | head -10
```

If this is a git project, also check recent history:

```bash
git log --oneline -5 2>/dev/null
```

Never read more than these files. Never read a full MEMORY.md — `tail` only.

Synthesize into:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT   <name — derived from root folder name>
BRANCH    <branch, or "no git">
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LAST SESSION  <date>
  Done:        <what was completed>
  Left off:    <what was in progress>

TOP PRIORITY
  1. <most important next action, concrete>
  2. <second priority if clear>

WATCH OUT
  • <any ERRORS.md entry from last 30 days — one line each>
  • <any "NOT FIXED" / "NOT CODED" / "BLOCKED" items from MEMORY.md>

BACKLOG (in progress)
  • <in-progress BACKLOG rows for this project>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Rules for each section:**

- **LAST SESSION**: from the most recent `## Session —` block in the memory
  doc. If missing/empty: "No session history found — this looks like the
  first run."
- **TOP PRIORITY**: from "Next session priorities" in the last session
  block. If none, infer from in-progress items. Max 2 lines.
- **WATCH OUT**: from ERRORS.md (last 30 days only) plus any MEMORY.md item
  tagged BLOCKED/NOT FIXED/NOT CODED/PAUSED. Max 4 bullets. Skip section if
  empty.
- **BACKLOG**: only "In Progress" rows for this project. Skip section if
  empty.

If none of the three docs exist at all:
```
No session history found for this project. This looks like a first run —
running session-memory in END mode will create MEMORY.md, ERRORS.md, and
BACKLOG.md when you close out this session.
```

If multiple projects were selected in S1, repeat this whole step per
project, separated by a blank line, before moving to S5.

### S5: Closing line

After all briefing block(s):

```
Ready. What are we working on today?
```

No commentary beyond the briefing block(s) and this line.

### START mode rules

- Read-only. Never write, create, or modify any file — including the
  `.last-active` marker (that's END mode's job).
- Never read files speculatively — only the docs resolved above, via
  `tail`/`grep`, never a full-file read of a large log.
- If a file is missing, note it in one phrase and continue — never error
  out.
- Synthesize into the briefing format; never dump raw file contents.
- If the user says "quick start" or "brief start", show only LAST SESSION +
  TOP PRIORITY per project, skip WATCH OUT and BACKLOG, and skip the
  multi-project AskUserQuestion — just use the single most-recent project.

---

## END mode

You are closing out a work session. Your job is to make sure the right
documents are updated so the next session starts with full context, without
the user having to decide what goes where. Do NOT implement code. Docs only.

### E1: Resolve project root and config

```bash
echo "CWD: $(pwd)"
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
echo "GIT_ROOT: ${GIT_ROOT:-none}"
echo "BRANCH: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'no git')"
git status --short 2>/dev/null | head -20
```

- If `GIT_ROOT` resolved, that's the project root and this is a **git
  project** — branch/commit info is available for E3 and the closing
  summary.
- If it's empty, this is a **non-git project**: use CWD as the project root
  and say so once ("No git repo — using CWD as project root: `<path>`").
  Everything else in END mode (config resolution, doc writes, the first-run
  question) works identically for non-git projects — only branch-related
  fields are omitted (shown as "no git" in E8).
- If invoked with an explicit path (e.g. `/session-memory end <path>`), use
  that instead of the detected root.

**Guard against a false-positive root — critical here, since this mode
writes files.** `git rev-parse --show-toplevel` walks *up* the directory
tree for a `.git` — if CWD is a plain subfolder with no `.git` of its own
but sits inside an unrelated ancestor repo (e.g. the user's whole home
directory is itself a git repo), `GIT_ROOT` will silently resolve to that
ancestor, and this step would write `MEMORY.md`/`ERRORS.md`/`BACKLOG.md`/
`.last-active` into the wrong repo entirely. Check:
```bash
if [ "$GIT_ROOT" = "$HOME" ]; then
  echo "GIT_ROOT resolved to your home directory — likely an unrelated parent repo, not this project."
fi
```
If `GIT_ROOT` equals `$HOME` (or is otherwise clearly unrelated to CWD),
**do not write there**. Fall back to CWD as the project root, treat this as
a non-git project for this run, and say so once: "Detected an unrelated
parent git repo at `<GIT_ROOT>` — using `<CWD>` directly instead."

Look for `.claude/session-memory.json` at the project root. If present, read
it for `globalMemory` and `docs` overrides (see S2's schema above;
`globalMemory` is a `~`-prefixed path — expand `~` to the home directory
wherever you read or write it, not just in E4). If absent, use defaults
(`MEMORY.md`, `ERRORS.md`, `BACKLOG.md` at project root, no global log) —
and go to **E1a (first-run setup)**.

### E1a: First-run setup (only if no config file exists)

Ask once, via AskUserQuestion:

> "Also keep a cross-project log across all your repos, at
> `~/.claude/session-memory/MEMORY.md`? (You can change this later by
> editing `.claude/session-memory.json`.)"

Options: "Yes, enable cross-project log" / "No, keep this project's log
separate".

Write `.claude/session-memory.json` with the choice (either
`{"globalMemory": "~/.claude/session-memory/MEMORY.md"}` or `{}`), so this
question is never asked again for this project. Then continue.

If a config file already exists (even `{}`), skip this step entirely —
don't re-ask.

### E2: Build the session summary

From the conversation, synthesize:

- **Date**: today, YYYY-MM-DD (absolute, never relative)
- **Worked on**: the primary task/goal this session
- **Completed**: what's now done
- **In progress**: what's mid-flight, not committed or deployed
- **Decisions made**: choices made/rejected, and why
- **Errors/blockers hit**: anything that failed 2+ times, or a real blocker
- **Next session priorities**: what happens next, in order

Infer this — don't make the user fill in a form. Only ask if something
genuinely load-bearing is ambiguous (e.g., "was X deployed or just pushed to
staging?").

If the session was short/trivial (a few minutes, no real decisions), write a
minimal entry and skip E6–E7 (ERRORS.md, CLAUDE.md) below.

### E3: Update the project's memory doc

Path: `<docs.memory>` from config, default `MEMORY.md` at project root.

Read it first if it exists. Append:

```markdown
## Session — YYYY-MM-DD
- Worked on: [summary]
- Completed: [list]
- In progress: [list]
- Decisions made: [list]
- Next session priorities: [list]
```

Keep it tight — under 15 lines total. If the file doesn't exist, create it
with this as the first entry (this is the normal first-run path; don't treat
it as an error).

### E4: Update the global cross-project log (only if configured)

Only run this step if `globalMemory` is set in the config file.

Path: `<globalMemory>` (expand `~` to home dir). Create the file and its
parent directory if missing, with a `# Session Memory` heading and a
`## Recent Sessions` section.

Read the file first. Then:

**Prepend** one bullet under `## Recent Sessions`, as the first item:
```
- **YYYY-MM-DD <project-name>** — <one-line summary, under 150 chars>
```
Never rewrite existing bullets. Only insert.

Do not touch anything else in this file — it may contain entries from other
projects.

### E5: Update the backlog doc

Path: `<docs.backlog>` from config, default `BACKLOG.md` at project root.

Read it first. If it doesn't exist, skip this step silently — a backlog doc
is opt-in, not created automatically (unlike MEMORY.md).

If it exists:
- Move items completed this session to "Done" (with today's date)
- Add newly surfaced items as new rows
- Update the "Notes" column for in-progress items whose status changed

Format: `| Date | Item | Notes |` (or whatever header the existing file
already uses — match it, don't impose a new schema).

Only touch rows that actually changed. Don't reformat or restructure the
rest of the file.

### E6: Update the errors doc (conditional)

Path: `<docs.errors>` from config, default `ERRORS.md` at project root.

Only write to this file if at least one is true this session:
- An approach was tried 2+ times and failed before something worked
- A non-obvious root cause was found
- A gotcha/environment quirk wasted real time

If yes, read the file first (create if missing), append:

```markdown
## YYYY-MM-DD — [short title]
- **What failed**: [what was tried]
- **Root cause**: [why it failed]
- **What worked**: [the correct approach]
- **Note for next time**: [one line — what to check first]
```

If nothing failed in a non-obvious way, skip this step entirely — don't
write a "nothing to report" entry.

### E7: Update the project's Active Work doc (conditional)

Only if the project has a file with an "Active Work" or "Current Work"
section (e.g. a `CLAUDE.md` or `README.md`) AND what's in progress has
materially changed this session.

Read that file, find the active-work section, and update only those lines.
Do not touch any other section. Do not restructure the file.

### E8: Write the recency marker

Write the current epoch timestamp to:

```
<project-root>/.claude/session-memory/.last-active
```

(create the directory if missing). This is what lets START mode's
multi-project scan sort this project by recency even if it's not a git repo,
or if you haven't pushed/committed yet.

```bash
mkdir -p "<project-root>/.claude/session-memory"
date +%s > "<project-root>/.claude/session-memory/.last-active"
```

### E8a: Auto-register in the global project list (only if it already exists)

Check for `~/.claude/session-memory/config.json`. **Only if that file
already exists** (meaning the user has opted into multi-project mode — never
create it from here), check whether this project's path is already listed
under `projects`. If not, append it:

```json
{ "name": "<folder-name>", "path": "<project-root>" }
```

Do not create the global config file if it doesn't exist — a single-project
user should never be pushed into multi-project mode silently.

### E9: Confirm

```
SESSION CLOSED — YYYY-MM-DD
────────────────────────────────────
Project:        [project name]
Branch:         [branch, or "no git"]
Updated docs:   [list each file actually modified, including .last-active]
Skipped:        [list any step skipped and why, e.g. "ERRORS.md — no failures"]
Next session:   [top 1-2 priorities]
────────────────────────────────────
```

### END mode rules

- Read every file before writing it. Never overwrite without reading first.
- Never touch files outside this project's root and the configured
  `globalMemory` path.
- Keep entries tight — this is a log, not an essay.
- Create a file that doesn't exist yet rather than skipping it, except
  BACKLOG.md (opt-in only — don't invent a backlog schema for someone who
  doesn't have one).
- Dates are always absolute (YYYY-MM-DD), never relative.
- Ask the first-run config question (E1a) exactly once per project, ever.
- Always write the `.last-active` marker (E8), even for a short/trivial
  session — it's cheap and is the only recency signal for non-git projects.
- Only auto-register into the global project list (E8a) if that file
  already exists. Never create it — that would silently opt a
  single-project user into multi-project mode.
- If the session was very short or trivial (under 10 minutes, no meaningful
  decisions), write a minimal entry and skip E6–E7.

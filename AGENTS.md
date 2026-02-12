# Agent rules (read first)

- Read CONTEXT.md and RUNBOOK.md first.
- Make minimal, high-confidence edits only. No unrelated refactors.
- Prefer showing diffs for specific files (e.g. `git --no-pager diff -- src/main.py`).
- Always run:
  - py -m compileall .
  - py src/main.py
- After tests pass, update:
  - CONTEXT.md (max 10 lines): milestone, what changed, next bite.
  - RUNBOOK.md: exact commands used + any new undo/verify notes.
- Stop for approval before editing files or committing.

## Command approval policy

Pre-approved to run without asking (safe read/verify only):
- py -m compileall .
- py src/analyze_runs.py
- git status
- git --no-pager diff --stat
- git --no-pager diff -- <paths>
- Test-Path <...>
- Get-Content <...>

Ask once per batch for the above, and ask before running anything else.
Never auto-run destructive commands (reset/clean/install).

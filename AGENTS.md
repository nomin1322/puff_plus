# Agent rules (read first)

- Read CONTEXT.md and RUNBOOK.md first.
- Goal: small, high-confidence changes that keep Puff+ runnable and explainable.
- Stay inside this repo. Do not touch .venv, user profile folders, or anything outside the workspace.

## What you may edit without stopping for approval
Allowed without extra approval (still show diffs):
- src/**/*.py
- *.md in repo root (AGENTS.md, CONTEXT.md, RUNBOOK.md)
- docs/**/*.md (if it exists)

Rules for edits:
- Make minimal edits only. No unrelated refactors.
- After editing a file, show a focused diff (prefer: `git --no-pager diff -- <paths>`).
- If a change affects gameplay fairness or logging schema, explain the impact in 1–3 lines.

## What requires approval (always)
Stop for approval before:
- git commit / git push
- deleting files or moving large chunks of code
- installing/upgrading packages (pip / npm / etc.)
- any network access
- any destructive command (reset/clean/remove/format-all)

## Command approval policy
Pre-approved to run without asking (safe verify only):
- py -m compileall .
- py src/main.py
- py src/analyze_runs.py
- git status
- git --no-pager diff --stat
- git --no-pager diff -- <paths>
- Test-Path <...>
- Get-Content <...>

Ask once per batch for any other commands.
Never auto-run destructive commands (reset/clean/install).
Never access network.

## After verify passes
- Update CONTEXT.md (max 10 lines): milestone, what changed, next bite.
- Update RUNBOOK.md: exact commands used + any new undo/verify notes.

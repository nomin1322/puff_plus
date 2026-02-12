## Setup
- Activate venv: `.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt` (if you add one)

## Run
- `py src/main.py`

## Verify
- `py -m compileall .`
- After 2 runs: check last rows: `Get-Content data\runs.csv -Tail 5`
- `git status` should be clean after committing (working tree clean)

## Undo a bad patch

### Undo a bad patch (safe default)
Check what changed:
- `git status`
- `git diff`
- `git diff --staged` (only relevant if staged)
- `git clean -nd` (preview only)

Undo only the files you just touched (recommended):
- `git restore src/main.py src/policy.py`

Undo a single file:
- `git restore src/main.py`

### Undo everything since last commit (use with care)
- `git restore .`
- `git reset --hard`

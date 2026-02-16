# Context (current)

Update (2026-02-16):
- Analysis script updated: `src/analyze_runs.py` now outputs family `n` counts and a baseline vs personalised by-mode chart/table.
- Verified artifacts: `reports/death_count_by_family.csv`, `reports/death_count_by_family.png`, `reports/summary_by_family.csv`, `reports/mean_survival_by_family.png`, `reports/mean_survival_by_family_by_mode.csv`, `reports/mean_survival_by_family_by_mode.png`.
- Verification commands run: `py -m compileall .`; `py src/analyze_runs.py`.
- Artifact checks run: `Test-Path reports/death_count_by_family.csv`; `Test-Path reports/death_count_by_family.png`; `Test-Path reports/summary_by_family.csv`; `Test-Path reports/mean_survival_by_family.png`; `Test-Path reports/mean_survival_by_family_by_mode.csv`; `Test-Path reports/mean_survival_by_family_by_mode.png`.

Milestone: analysis script added + reports generated
What changed:
- Added `src/analyze_runs.py` summary + chart generation from `data/runs.csv`.
- Confirmed artifacts: `reports/summary_by_family.csv` and `reports/mean_survival_by_family.png`.
- `reports/mean_survival_by_family.txt` is only generated when matplotlib is missing.
Last verified: git status ; git --no-pager diff --stat ; py -m compileall . ; py src/analyze_runs.py ; Test-Path reports/summary_by_family.csv ; Test-Path reports/mean_survival_by_family.png
Next bite: baseline vs personalised comparison + one chart + one table explanation.

# Context (current)

Milestone: analysis script added + reports generated
What changed:
- Added `src/analyze_runs.py` summary + chart generation from `data/runs.csv`.
- Confirmed artifacts: `reports/summary_by_family.csv` and `reports/mean_survival_by_family.png`.
- `reports/mean_survival_by_family.txt` is only generated when matplotlib is missing.
Last verified: git status ; git --no-pager diff --stat ; py -m compileall . ; py src/analyze_runs.py ; Test-Path reports/summary_by_family.csv ; Test-Path reports/mean_survival_by_family.png
Next bite: baseline vs personalised comparison + one chart + one table explanation.

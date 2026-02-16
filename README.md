# Puff+
Puff+ is a compact adaptive gameplay prototype built for SIT Applied AI admissions and technical reviewers. It captures per-run telemetry from a Flappy Bird-style environment, supports baseline vs personalised mode behavior, and produces reproducible analysis outputs that make model behavior and player outcomes easy to inspect.

## What it demonstrates
- Structured run logging to `data/runs.csv` for gameplay, performance, and input rhythm.
- Baseline vs personalised mode switching in-game and mode-aware analysis offline.
- Reproducible analysis from raw logs to report artifacts with `py` commands.
- Clear portfolio artifacts (plots + CSV summaries) for technical review.

## Quickstart
```powershell
py src/main.py
py src/analyze_runs.py
```

## Dependencies
Python with `pandas` and `matplotlib` (virtual environment is optional but recommended, e.g. `.venv`).

## Data logged
Source header: `data/runs.csv`

| Column | Description |
|---|---|
| `timestamp_epoch` | Unix timestamp at run end. |
| `player_id` | Player identifier for the run. |
| `session_id` | Session identifier grouping runs. |
| `run_id` | Sequential run number within a session. |
| `mode` | Gameplay mode (`baseline` or `personalised`). |
| `survival_time_s` | Survival duration in seconds. |
| `score_passed_pipes` | Number of passed obstacles. |
| `death_reason` | End condition (e.g., collision/ground/ceiling). |
| `obstacle_family` | Obstacle family associated with obstacle-collision deaths. |
| `tap_count` | Number of input taps in the run. |
| `tap_mean_interval_ms` | Mean inter-tap interval (ms). |
| `tap_sd_interval_ms` | Standard deviation of inter-tap interval (ms). |

Analysis derives death_family from obstacle_family and maps missing to 'none'.

## Outputs
Generated in `reports/`:
- `death_count_by_family.png`
- `mean_survival_by_family.png`
- `mean_survival_by_family_by_mode.png`
- `death_count_by_family.csv`
- `summary_by_family.csv`
- `mean_survival_by_family_by_mode.csv`
- `mean_survival_by_family.txt` (ASCII fallback when matplotlib is unavailable)

## Repo structure
```text
puff_plus/
  src/
    main.py
    analyze_runs.py
  data/
  reports/
  AGENTS.md
  CONTEXT.md
  RUNBOOK.md
  puff.cmd
  .gitignore
```

## Results summary
The three core plots (`death_count_by_family.png`, `mean_survival_by_family.png`, and `mean_survival_by_family_by_mode.png`) provide a quick view of failure distribution, average survival by obstacle family, and baseline vs personalised differences. Current outputs show meaningful variation across families and mode splits, but this should be interpreted as directional evidence rather than a final performance claim. Sample size remains limited and mode/family cells are not fully balanced, so additional runs are needed before drawing strong conclusions.

## Limitations + next steps
- Current sample size is modest and uneven across families/modes.
- Results may be sensitive to player/session-specific behavior.
- No confidence intervals or significance testing yet.
- Add larger balanced data collection and stratified analysis by session.
- Extend reporting with uncertainty/error bars per family and mode.

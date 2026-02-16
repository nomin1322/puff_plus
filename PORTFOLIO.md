# Puff+ Portfolio
Repo: https://github.com/nomin1322/puff_plus

## Project Goals
Puff+ aims to demonstrate an end-to-end evaluation loop:

**instrumented gameplay → interpretable failure labels → baseline vs adaptive comparison → reproducible evidence (plots + tables).**

Puff+ treats a simple Flappy Bird-style game as a controlled micro-environment. The goal is not “a perfect game.” The goal is a *measurable workflow*: collect consistent per-run signals, group failures into named patterns, then test whether an adaptive policy responds to where the player struggles while keeping a baseline mode for fair comparison.

<!-- pagebreak -->

## 1) Project summary
Puff+ is a Flappy Bird-style prototype that records per-run measurements automatically at the end of every run. Each run writes one row into `data/runs.csv`, including:

- performance: `survival_time_s`, `score_passed_pipes`
- outcome context: `death_reason`, and (when relevant) `obstacle_family`
- input rhythm: `tap_count`, `tap_mean_interval_ms`, `tap_sd_interval_ms`

The game supports two modes in one executable:

- **baseline:** a fixed, predictable obstacle-family schedule used as a control condition
- **personalised (adaptive):** obstacle-family selection and tuning respond to observed failure patterns

Mode can be toggled live with the **M** key, so baseline and personalised runs can be collected in one session.

`src/analyze_runs.py` converts raw logs into reproducible report outputs (CSV tables + PNG plots). The current report set is meant to be **directional evidence you can inspect end-to-end**, not a final performance claim.

### Review note
Claims in this document can be traced from `data/runs.csv` → derived labels → summary tables → plotted figures.

Puff+ combines an instrumented game loop (`src/main.py`) with an analysis pipeline (`src/analyze_runs.py`) that turns raw run logs into clear plots and tables.

As such the story is traceable from **raw columns → labels → summaries → figures**, so any claim can be checked against logged data and reproduced outputs.

Gameplay screenshot placeholder: insert one in-game screenshot showing the HUD (Mode, Score, Time) and at least one obstacle family on screen.

<!-- pagebreak -->

## 2) Telemetry and labels
Telemetry source: `data/runs.csv` (one row per run)

| runs.csv column | Meaning |
|---|---|
| `timestamp_epoch` | Unix timestamp at run end. |
| `player_id` | Player identifier. |
| `session_id` | Session identifier grouping runs. |
| `run_id` | Sequential run number within a session. |
| `mode` | `baseline` or `personalised`. |
| `survival_time_s` | Run duration in seconds. |
| `score_passed_pipes` | Number of obstacles passed. |
| `death_reason` | End condition (`obstacle_collision`, `ground`, `ceiling`). |
| `obstacle_family` | Family at collision time for obstacle deaths; blank for non-obstacle deaths. |
| `tap_count` | Number of flap inputs in the run. |
| `tap_mean_interval_ms` | Mean interval between taps (ms). |
| `tap_sd_interval_ms` | Standard deviation of tap intervals (ms). |

### Labeling notes
- `obstacle_family` is recorded only when a run ends via **obstacle collision**.
- Non-obstacle endings (ground/ceiling/other) may have `obstacle_family` blank.
- In analysis, missing/blank families are normalized to **`none`** so every run can be grouped cleanly.
- A derived label `death_family` is used for grouping and reporting.

### Obstacle family glossary (current buckets)
Obstacle families are named obstacle patterns used to group failures into interpretable buckets.

- `precision_gap`: tight margins; small control errors get punished.
- `rhythm_wave`: repeating pattern that rewards consistent timing and cadence.
- `timing_gate`: discrete timing windows (“commit moments”) where early/late inputs fail.
- `none`: non-obstacle endings (ground/ceiling/other), i.e. no obstacle family.

Report tables referenced:
- `reports/summary_by_family.csv`
- `reports/death_count_by_family.csv`
- `reports/mean_survival_by_family_by_mode.csv`

<!-- pagebreak -->

## 3) Results by family

### Death count by family
![Death count by family](docs/figures/death_count_by_family.png)

In the current snapshot (`reports/death_count_by_family.csv`, total **n=34**):
- `rhythm_wave`: 15
- `precision_gap`: 10
- `timing_gate`: 6
- `none`: 3

**Takeaway:** failures are not evenly distributed across families in this sample. This is useful for identifying “where the friction is,” but it is still directional because exposure depends on the spawn policy and the dataset is small.

### Mean survival by family
![Mean survival by family](docs/figures/mean_survival_by_family.png)

From `reports/summary_by_family.csv` (current snapshot):
- `rhythm_wave`: 5.308s
- `timing_gate`: 5.147s
- `precision_gap`: 3.316s
- `none`: 1.158s

**Interpretation:**
- `none` (ground/ceiling, no obstacle family) is shortest, consistent with early-run control failures.
- Family means help rank friction points, but should not be treated as causal without larger, balanced data.

<!-- pagebreak -->

## 4) Baseline vs personalised (adaptive)
![Mean survival by family by mode](docs/figures/mean_survival_by_family_by_mode.png)

From `reports/mean_survival_by_family_by_mode.csv` (current snapshot), mode effects differ by family. Example:
- `timing_gate` is higher in personalised (5.46s, n=4) than baseline (4.52s, n=2),
- while `precision_gap` and `rhythm_wave` are slightly higher in baseline in this sample.

**Takeaway:** this is not enough evidence to claim a stable “winner” because some cells are tiny (e.g., `timing_gate` baseline n=2). The point of this section is transparency: the baseline vs personalised split is measurable and inspectable from raw logs to plots.

### Limitations (what the current evidence does NOT claim)
- Small total sample (n=34) and uneven counts across family/mode cells.
- Single-player data in current logs limits generalization.
- No confidence intervals or significance testing yet.
- Family exposure is policy-driven, so death counts can reflect selection effects.
- Session effects (warm-up/fatigue) are not controlled.

### Next steps (toward reviewer-grade evaluation)
- **Collect balanced data:** fixed protocol with the same number of runs per family, in both modes.
- **Add uncertainty:** error bars / confidence intervals so differences aren’t just visual.
- **Control learning/fatigue:** analyze by session order (early vs late) to separate improvement from policy effects.
- **Show distributions:** per-run survival histograms/boxplots, not only means.
- **Lock an evaluation routine:** a repeatable “test session” schedule anyone can follow.

### Conclusion
Puff+ is a checkpoint-sized but end-to-end system: it shows that obstacle patterns can be labeled into interpretable families, that baseline vs adaptive behavior can be compared transparently, and that results can be reproduced from logged runs into plots. The next iteration is to gather a larger balanced dataset and add uncertainty metrics so any improvement claims are defensible, not just directional.

### Reproducibility (local)
```powershell
py src/analyze_runs.py
py src/main.py   # optional: generate more runs

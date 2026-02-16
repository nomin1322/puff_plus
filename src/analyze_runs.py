import os

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


RUNS_PATH = os.path.join("data", "runs.csv")
REPORTS_DIR = "reports"
SUMMARY_PATH = os.path.join(REPORTS_DIR, "summary_by_family.csv")
DEATH_COUNT_PATH = os.path.join(REPORTS_DIR, "death_count_by_family.csv")
DEATH_COUNT_PNG_PATH = os.path.join(REPORTS_DIR, "death_count_by_family.png")
MEAN_SURVIVAL_PNG_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family.png")
MEAN_SURVIVAL_TXT_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family.txt")
MEAN_SURVIVAL_BY_MODE_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family_by_mode.csv")
MEAN_SURVIVAL_BY_MODE_PNG_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family_by_mode.png")
FAMILY_COLUMN_CANDIDATES = ("death_family", "obstacle_family")
MODE_COLUMN_CANDIDATES = (
    "mode",
    "difficulty_mode",
    "is_personalised",
    "personalized",
    "personalise",
    "policy_mode",
)


def load_runs():
    if not os.path.exists(RUNS_PATH):
        return pd.DataFrame()
    try:
        return pd.read_csv(RUNS_PATH)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def detect_column(columns, candidates):
    by_lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in by_lower:
            return by_lower[candidate]
    return None


def normalize_family(value):
    if pd.isna(value):
        return "none"
    family = str(value if value is not None else "").strip()
    return family if family else "none"


def normalize_mode(value):
    if pd.isna(value):
        return "unknown"
    text = str(value if value is not None else "").strip().lower()
    if text in ("1", "true", "yes", "y", "personalised", "personalized", "personalise", "adaptive"):
        return "personalised"
    if text in ("0", "false", "no", "n", "baseline", "control"):
        return "baseline"
    return "unknown"


def prepare_frame(df):
    if df.empty:
        return pd.DataFrame(columns=["death_family", "survival_time_s"])

    family_column = detect_column(df.columns, FAMILY_COLUMN_CANDIDATES)
    if family_column is None:
        families = pd.Series(["none"] * len(df))
    else:
        families = df[family_column].map(normalize_family)

    survival_column = detect_column(df.columns, ("survival_time_s",))
    if survival_column is None:
        survival = pd.Series([0.0] * len(df))
    else:
        survival = pd.to_numeric(df[survival_column], errors="coerce").fillna(0.0)
    prepared = pd.DataFrame({"death_family": families, "survival_time_s": survival})
    return prepared


def summarize_by_family(prepared):
    if prepared.empty:
        return pd.DataFrame(columns=["death_family", "n", "mean_survival_time_s"])

    summary = (
        prepared.groupby("death_family", dropna=False)
        .agg(n=("survival_time_s", "size"), mean_survival_time_s=("survival_time_s", "mean"))
        .reset_index()
        .sort_values("death_family")
    )
    summary["mean_survival_time_s"] = summary["mean_survival_time_s"].round(3)
    summary["n"] = summary["n"].astype(int)
    return summary


def summarize_by_family_mode(df, prepared):
    mode_column = detect_column(df.columns, MODE_COLUMN_CANDIDATES)
    if mode_column is None or prepared.empty:
        return mode_column, pd.DataFrame(columns=["death_family", "mode", "n", "mean_survival_time_s"])

    mode_values = df[mode_column].map(normalize_mode)
    with_mode = prepared.copy()
    with_mode["mode"] = mode_values
    with_mode = with_mode[with_mode["mode"].isin(["baseline", "personalised"])]

    if with_mode.empty:
        return mode_column, pd.DataFrame(columns=["death_family", "mode", "n", "mean_survival_time_s"])

    grouped = (
        with_mode.groupby(["death_family", "mode"], dropna=False)
        .agg(n=("survival_time_s", "size"), mean_survival_time_s=("survival_time_s", "mean"))
        .reset_index()
        .sort_values(["death_family", "mode"])
    )
    grouped["mean_survival_time_s"] = grouped["mean_survival_time_s"].round(3)
    grouped["n"] = grouped["n"].astype(int)
    return mode_column, grouped


def save_table(df, path, columns):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    table = df.copy()
    if table.empty:
        table = pd.DataFrame(columns=columns)
    table.to_csv(path, index=False, columns=columns)


def write_ascii_chart(summary):
    max_value = summary["mean_survival_time_s"].max() if not summary.empty else 0.0
    scale = 40.0 / max_value if max_value > 0 else 1.0

    lines = ["Mean survival by family (ASCII)"]
    for _, row in summary.iterrows():
        label = row["death_family"]
        count = int(row["n"])
        value = float(row["mean_survival_time_s"])
        bar = "#" * int(round(value * scale))
        lines.append(f"{label} (n={count}): {bar} {value:.3f}")

    if summary.empty:
        lines.append("(no data)")

    with open(MEAN_SURVIVAL_TXT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_mean_survival_chart(summary):
    labels = [f"{row.death_family} (n={int(row.n)})" for row in summary.itertuples(index=False)]
    values = [float(row.mean_survival_time_s) for row in summary.itertuples(index=False)]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.xlabel("death_family")
    plt.ylabel("mean_survival_time_s")
    plt.title("Mean survival by family")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(MEAN_SURVIVAL_PNG_PATH, dpi=160)
    plt.close()


def write_death_count_chart(summary):
    labels = [row.death_family for row in summary.itertuples(index=False)]
    values = [int(row.n) for row in summary.itertuples(index=False)]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.xlabel("death_family")
    plt.ylabel("n")
    plt.title("Death count by family")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(DEATH_COUNT_PNG_PATH, dpi=160)
    plt.close()


def write_by_mode_chart(mode_summary):
    pivot = mode_summary.pivot(index="death_family", columns="mode", values="mean_survival_time_s").sort_index()
    families = list(pivot.index)
    modes = [mode for mode in ("baseline", "personalised") if mode in pivot.columns]

    if not families or not modes:
        return

    x = range(len(families))
    width = 0.8 / len(modes)
    center_offset = (len(modes) - 1) / 2.0

    plt.figure(figsize=(10, 5))
    for i, mode in enumerate(modes):
        values = pivot[mode].fillna(0.0).tolist()
        offsets = [idx + (i - center_offset) * width for idx in x]
        plt.bar(offsets, values, width=width, label=mode)

    plt.xlabel("death_family")
    plt.ylabel("mean_survival_time_s")
    plt.title("Mean survival by family by mode")
    plt.xticks(list(x), families, rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(MEAN_SURVIVAL_BY_MODE_PNG_PATH, dpi=160)
    plt.close()


def main():
    runs = load_runs()
    prepared = prepare_frame(runs)
    summary = summarize_by_family(prepared)

    save_table(summary, SUMMARY_PATH, ["death_family", "n", "mean_survival_time_s"])
    save_table(summary, DEATH_COUNT_PATH, ["death_family", "n"])

    mode_column, mode_summary = summarize_by_family_mode(runs, prepared)
    if mode_column and not mode_summary.empty:
        save_table(mode_summary, MEAN_SURVIVAL_BY_MODE_PATH, ["death_family", "mode", "n", "mean_survival_time_s"])

    if plt is None:
        write_ascii_chart(summary)
        print("matplotlib not installed; wrote ASCII chart")
    else:
        write_mean_survival_chart(summary)
        write_death_count_chart(summary)
        if mode_column and not mode_summary.empty:
            write_by_mode_chart(mode_summary)
        print("wrote PNG charts")

    print(f"Saved {SUMMARY_PATH}")
    print(f"Saved {DEATH_COUNT_PATH}")
    if mode_column is None:
        print("No mode column detected; skipped by-mode outputs")
    elif mode_summary.empty:
        print(f"Detected mode column '{mode_column}' but no baseline/personalised rows to chart")
    else:
        print(f"Saved {MEAN_SURVIVAL_BY_MODE_PATH}")


if __name__ == "__main__":
    main()

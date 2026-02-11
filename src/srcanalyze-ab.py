import os
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = os.path.join("data", "runs.csv")
OUT_DIR = "reports"
TABLE_OUT = os.path.join(OUT_DIR, "summary_by_family.csv")
PLOT_OUT = os.path.join(OUT_DIR, "mean_survival_by_family.png")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    # Make sure blanks don't break us
    df["obstacle_family"] = df["obstacle_family"].fillna("")
    df["survival_time_s"] = pd.to_numeric(df["survival_time_s"], errors="coerce")
    df["tap_count"] = pd.to_numeric(df["tap_count"], errors="coerce")
    df["tap_mean_interval_ms"] = pd.to_numeric(df["tap_mean_interval_ms"], errors="coerce")

    # Only rows where a family exists (i.e., actual obstacle-related telemetry)
    fam = df[df["obstacle_family"] != ""].copy()

    if fam.empty:
        print("No obstacle_family rows found yet. Crash into an obstacle once, then rerun.")
        return

    fam["is_obstacle_collision"] = fam["death_reason"].eq("obstacle_collision")

    summary = (
        fam.groupby("obstacle_family")
        .agg(
            runs=("run_id", "count"),
            collision_rate=("is_obstacle_collision", "mean"),
            mean_survival_s=("survival_time_s", "mean"),
            median_survival_s=("survival_time_s", "median"),
            mean_taps=("tap_count", "mean"),
            mean_tap_interval_ms=("tap_mean_interval_ms", "mean"),
        )
        .sort_values(["runs", "mean_survival_s"], ascending=[False, False])
    )

    print("\n=== Day 3: Summary by obstacle_family ===\n")
    print(summary.round(3).to_string())

    summary.round(6).to_csv(TABLE_OUT)
    print(f"\nSaved table -> {TABLE_OUT}")

    # Plot mean survival by family
    plot_df = summary.reset_index()[["obstacle_family", "mean_survival_s"]]
    ax = plot_df.plot(kind="bar", x="obstacle_family", y="mean_survival_s", legend=False)
    ax.set_title("Mean survival time by obstacle family")
    ax.set_xlabel("obstacle_family")
    ax.set_ylabel("mean survival (s)")
    plt.tight_layout()
    plt.savefig(PLOT_OUT, dpi=160)
    plt.close()

    print(f"Saved plot  -> {PLOT_OUT}\n")

if __name__ == "__main__":
    main()

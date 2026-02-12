import csv
import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


RUNS_PATH = os.path.join("data", "runs.csv")
REPORTS_DIR = "reports"
SUMMARY_PATH = os.path.join(REPORTS_DIR, "summary_by_family.csv")
PLOT_PNG_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family.png")
PLOT_TXT_PATH = os.path.join(REPORTS_DIR, "mean_survival_by_family.txt")


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_rows():
    if not os.path.exists(RUNS_PATH):
        return []
    with open(RUNS_PATH, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def detect_family_key(rows):
    if not rows:
        return "death_family"
    sample = rows[0]
    if "death_family" in sample:
        return "death_family"
    if "obstacle_family" in sample:
        return "obstacle_family"
    return "death_family"


def summarize(rows):
    family_key = detect_family_key(rows)
    grouped = {}

    for row in rows:
        family = (row.get(family_key) or "").strip() or "none"
        survival = to_float(row.get("survival_time_s"))
        score = to_float(row.get("score_passed_pipes"))

        if family not in grouped:
            grouped[family] = {"count": 0, "sum_survival": 0.0, "sum_score": 0.0}

        grouped[family]["count"] += 1
        grouped[family]["sum_survival"] += survival
        grouped[family]["sum_score"] += score

    summary = []
    for family in sorted(grouped.keys()):
        count = grouped[family]["count"]
        mean_survival = grouped[family]["sum_survival"] / count if count else 0.0
        mean_score = grouped[family]["sum_score"] / count if count else 0.0
        summary.append(
            {
                "death_family": family,
                "count": count,
                "mean_survival_time_s": round(mean_survival, 3),
                "mean_score_passed_pipes": round(mean_score, 3),
            }
        )

    return summary


def write_summary(summary):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(SUMMARY_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "death_family",
                "count",
                "mean_survival_time_s",
                "mean_score_passed_pipes",
            ],
        )
        writer.writeheader()
        writer.writerows(summary)


def write_ascii_chart(summary):
    max_value = max((row["mean_survival_time_s"] for row in summary), default=0.0)
    scale = 40.0 / max_value if max_value > 0 else 1.0

    lines = ["Mean survival by family (ASCII)"]
    for row in summary:
        label = row["death_family"]
        value = row["mean_survival_time_s"]
        bar = "#" * int(round(value * scale))
        lines.append(f"{label:15} | {bar} {value:.3f}")

    if not summary:
        lines.append("(no data)")

    with open(PLOT_TXT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_png_chart(summary):
    labels = [row["death_family"] for row in summary]
    values = [row["mean_survival_time_s"] for row in summary]

    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values)
    plt.xlabel("death_family")
    plt.ylabel("mean_survival_time_s")
    plt.title("Mean survival by family")
    plt.tight_layout()
    plt.savefig(PLOT_PNG_PATH, dpi=160)
    plt.close()


def main():
    rows = load_rows()
    summary = summarize(rows)
    write_summary(summary)

    if plt is None:
        write_ascii_chart(summary)
        print("matplotlib not installed; wrote ASCII chart")
    else:
        write_png_chart(summary)
        print("wrote PNG chart")

    print(f"Saved {SUMMARY_PATH}")


if __name__ == "__main__":
    main()

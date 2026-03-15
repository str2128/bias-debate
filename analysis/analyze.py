"""
analyze.py — Load all result JSONs and produce analysis + charts.

Outputs:
    - Accuracy by bias type (bar chart, split by judge mode)
    - Blind vs informed judge accuracy comparison (grouped bar chart)
    - Confidence calibration (is the judge more confident when wrong?)
    - Heatmap: accuracy by bias type × intensity
    - Summary table printed to stdout
"""

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

RESULTS_DIR = Path("results")
OUTPUT_DIR = Path("analysis/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")


# ── LOAD DATA ─────────────────────────────────────────────────────────────────

def load_results() -> pd.DataFrame:
    records = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        with open(path) as f:
            result = json.load(f)

        meta = result.get("metadata", {})
        verdict = result.get("verdict", {})

        if "error" in verdict:
            print(f"  Skipping {path.name} (judge failed to return JSON)")
            continue

        records.append({
            "topic": meta.get("topic_key"),
            "bias_type": meta.get("bias_type"),
            "intensity": meta.get("intensity"),
            "judge_mode": meta.get("judge_mode", "informed"),  # default for old results
            "ground_truth_winner": meta.get("ground_truth_winner"),
            "judge_winner": verdict.get("winner"),
            "judge_correct": meta.get("judge_correct"),
            "confidence": verdict.get("confidence"),
            "bias_detected_in_A": verdict.get("bias_detected_in_A"),
            "bias_detected_in_B": verdict.get("bias_detected_in_B"),
            "bias_type_identified": verdict.get("bias_type_A"),
            "bias_severity_A": verdict.get("bias_severity_A"),
            "bias_severity_identified": verdict.get("bias_severity_A"),
        })

    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} results.\n")
    return df


# ── ANALYSIS ──────────────────────────────────────────────────────────────────

def accuracy_by_bias_type(df: pd.DataFrame):
    """Grouped bar chart: judge accuracy per bias type, split by judge mode."""
    biased = df[df["bias_type"] != "none"].copy()

    has_both_modes = biased["judge_mode"].nunique() > 1

    if has_both_modes:
        acc = biased.groupby(["bias_type", "judge_mode"])["judge_correct"].mean().unstack()
        acc = acc.sort_values("informed" if "informed" in acc.columns else acc.columns[0])

        fig, ax = plt.subplots(figsize=(9, 5))
        x = range(len(acc))
        width = 0.35
        colors = {"informed": "#4361ee", "blind": "#e17055"}
        for i, mode in enumerate(acc.columns):
            ax.barh(
                [xi + (i - 0.5) * width for xi in x],
                acc[mode],
                height=width,
                label=f"{mode.capitalize()} judge",
                color=colors.get(mode, "#999"),
                alpha=0.85,
            )
        ax.set_yticks(list(x))
        ax.set_yticklabels(acc.index)
        ax.set_xlabel("Judge Accuracy")
        ax.set_title("Judge Accuracy by Bias Type\nInformed (sees critic) vs Blind (arguments only)")
        ax.axvline(0.5, color="red", linestyle="--", alpha=0.5, label="Chance (0.5)")
        ax.set_xlim(0, 1.05)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        ax.legend()
    else:
        # Only one mode available — simple chart
        acc_simple = biased.groupby("bias_type")["judge_correct"].mean().reset_index()
        acc_simple.columns = ["bias_type", "accuracy"]
        acc_simple = acc_simple.sort_values("accuracy")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(acc_simple["bias_type"], acc_simple["accuracy"],
                color=sns.color_palette("muted", len(acc_simple)))
        ax.set_xlabel("Judge Accuracy")
        ax.set_title("Judge Accuracy by Bias Type")
        ax.axvline(0.5, color="red", linestyle="--", alpha=0.6, label="Chance (0.5)")
        ax.set_xlim(0, 1.05)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        ax.legend()

    plt.tight_layout()
    path = OUTPUT_DIR / "accuracy_by_bias_type.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")
    return acc if has_both_modes else acc_simple


def blind_vs_informed(df: pd.DataFrame):
    """Grouped bar chart: overall blind vs informed accuracy per bias type."""
    biased = df[df["bias_type"] != "none"].copy()

    if biased["judge_mode"].nunique() < 2:
        print("  Skipping blind_vs_informed chart (only one judge mode in data so far)")
        return

    acc = biased.groupby(["bias_type", "judge_mode"])["judge_correct"].mean().unstack().reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(acc))
    width = 0.35
    ax.bar([xi - width/2 for xi in x], acc.get("informed", [0]*len(acc)),
           width=width, label="Informed (sees critic)", color="#4361ee", alpha=0.85)
    ax.bar([xi + width/2 for xi in x], acc.get("blind", [0]*len(acc)),
           width=width, label="Blind (no critic)", color="#e17055", alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(acc["bias_type"], rotation=15, ha="right")
    ax.set_ylabel("Judge Accuracy")
    ax.set_title("Does Seeing the Critic Help the Judge?\nInformed vs Blind by Bias Type")
    ax.set_ylim(0, 1.1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.axhline(0.5, color="red", linestyle="--", alpha=0.5, label="Chance (0.5)")
    ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "blind_vs_informed.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def accuracy_by_intensity(df: pd.DataFrame):
    """Grouped bar chart: judge accuracy for mild vs strong bias, split by judge mode."""
    biased = df[df["bias_type"] != "none"].copy()

    has_both_modes = biased["judge_mode"].nunique() > 1

    if has_both_modes:
        acc = biased.groupby(["intensity", "judge_mode"])["judge_correct"].mean().unstack().reset_index()
        fig, ax = plt.subplots(figsize=(6, 4))
        x = range(len(acc))
        width = 0.35
        ax.bar([xi - width/2 for xi in x], acc.get("informed", [0]*len(acc)),
               width=width, label="Informed", color="#4361ee", alpha=0.85)
        ax.bar([xi + width/2 for xi in x], acc.get("blind", [0]*len(acc)),
               width=width, label="Blind", color="#e17055", alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(acc["intensity"])
        ax.set_ylabel("Judge Accuracy")
        ax.set_title("Judge Accuracy by Intensity\nInformed vs Blind")
        ax.set_ylim(0, 1.1)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        ax.legend()
    else:
        acc = biased.groupby("intensity")["judge_correct"].mean().reset_index()
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(acc["intensity"], acc["judge_correct"], color=["#74b9ff", "#e17055"])
        ax.set_ylabel("Judge Accuracy")
        ax.set_title("Judge Accuracy by Bias Intensity")
        ax.set_ylim(0, 1.05)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    plt.tight_layout()
    path = OUTPUT_DIR / "accuracy_by_intensity.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def confidence_calibration(df: pd.DataFrame):
    """Strip plot + mean lines: judge confidence by outcome and mode.
    Box plots avoided due to small N on wrong cases (n=2 per mode)."""
    biased = df[df["bias_type"] != "none"].dropna(subset=["confidence", "judge_correct"]).copy()
    biased["outcome"] = biased["judge_correct"].map({True: "Correct", False: "Wrong"})

    has_both_modes = biased["judge_mode"].nunique() > 1
    mode_colors = {"informed": "#4361ee", "blind": "#e17055"}
    outcome_order = ["Correct", "Wrong"]

    fig, ax = plt.subplots(figsize=(8, 5))

    if has_both_modes:
        modes = ["informed", "blind"]
        offsets = {"informed": -0.15, "blind": 0.15}
        x_pos = {o: i for i, o in enumerate(outcome_order)}

        for mode in modes:
            subset = biased[biased["judge_mode"] == mode]
            color = mode_colors[mode]
            for outcome in outcome_order:
                pts = subset[subset["outcome"] == outcome]["confidence"].values
                x = x_pos[outcome] + offsets[mode]
                # jitter
                import numpy as np
                jitter = (np.random.RandomState(42).rand(len(pts)) - 0.5) * 0.06
                ax.scatter(
                    [x + j for j in jitter], pts,
                    color=color, alpha=0.6, s=40, zorder=3,
                    label=f"{mode.capitalize()}" if outcome == "Correct" else "_nolegend_"
                )
                # mean line
                mean_val = pts.mean()
                ax.plot([x - 0.08, x + 0.08], [mean_val, mean_val],
                        color=color, linewidth=2.5, zorder=4)

        ax.set_xticks(list(x_pos.values()))
        ax.set_xticklabels(outcome_order)
        ax.set_title("Judge Confidence by Outcome & Mode\n(dots = individual runs, horizontal line = mean)")
    else:
        subset = biased
        colors_map = {"Correct": "#55efc4", "Wrong": "#ff7675"}
        x_pos = {o: i for i, o in enumerate(outcome_order)}
        for outcome in outcome_order:
            pts = subset[subset["outcome"] == outcome]["confidence"].values
            x = x_pos[outcome]
            import numpy as np
            jitter = (np.random.RandomState(42).rand(len(pts)) - 0.5) * 0.1
            ax.scatter([x + j for j in jitter], pts,
                       color=colors_map[outcome], alpha=0.7, s=50, zorder=3)
            ax.plot([x - 0.1, x + 0.1], [pts.mean(), pts.mean()],
                    color=colors_map[outcome], linewidth=2.5, zorder=4)
        ax.set_xticks(list(x_pos.values()))
        ax.set_xticklabels(outcome_order)
        ax.set_title("Judge Confidence: Correct vs Wrong\n(dots = individual runs, line = mean)")

    ax.set_ylabel("Self-reported confidence (1–10)")
    ax.set_xlabel("")
    ax.set_ylim(4, 11)
    ax.set_yticks(range(5, 11))
    ax.legend(title="Judge mode")
    ax.annotate("Note: only 2 wrong cases per mode — treat with caution",
                xy=(0.5, 0.02), xycoords="axes fraction",
                ha="center", fontsize=8, color="grey", style="italic")
    plt.tight_layout()
    path = OUTPUT_DIR / "confidence_calibration.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def heatmap_accuracy(df: pd.DataFrame):
    """Heatmap(s): accuracy by bias type × intensity, one per judge mode."""
    biased = df[df["bias_type"] != "none"].copy()
    modes = biased["judge_mode"].unique()

    if len(modes) > 1:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        for ax, mode in zip(axes, ["informed", "blind"]):
            subset = biased[biased["judge_mode"] == mode]
            if subset.empty:
                ax.set_visible(False)
                continue
            pivot = subset.groupby(["bias_type", "intensity"])["judge_correct"].mean().unstack().astype(float)
            sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn", vmin=0, vmax=1,
                        linewidths=0.5, ax=ax, cbar=(mode == "blind"))
            ax.set_title(f"{mode.capitalize()} Judge\nAccuracy by Bias Type × Intensity")
        fig.suptitle("Does Seeing the Critic Change Accuracy Patterns?", fontsize=12, y=1.02)
    else:
        pivot = biased.groupby(["bias_type", "intensity"])["judge_correct"].mean().unstack().astype(float)
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn", vmin=0, vmax=1,
                    linewidths=0.5, ax=ax)
        ax.set_title("Judge Accuracy by Bias Type × Intensity")

    plt.tight_layout()
    path = OUTPUT_DIR / "heatmap_bias_intensity.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def bias_detection_rate(df: pd.DataFrame):
    """Bar chart: how often did the judge flag bias_detected_in_A=True per bias type?
    Separate from accuracy — the judge can detect bias but still pick the wrong winner."""
    biased = df[df["bias_type"] != "none"].copy()

    detection = biased.groupby(["bias_type", "judge_mode"])["bias_detected_in_A"].mean().unstack()

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(detection))
    width = 0.35
    colors = {"informed": "#4361ee", "blind": "#e17055"}
    for i, mode in enumerate(detection.columns):
        ax.barh(
            [xi + (i - 0.5) * width for xi in x],
            detection[mode],
            height=width,
            label=f"{mode.capitalize()} judge",
            color=colors.get(mode, "#999"),
            alpha=0.85,
        )
    ax.set_yticks(list(x))
    ax.set_yticklabels(detection.index)
    ax.set_xlabel("Detection Rate (proportion of runs where judge flagged bias in A)")
    ax.set_title("Bias Detection Rate by Bias Type\n(Did the judge flag Debater A as biased?)")
    ax.axvline(0.5, color="red", linestyle="--", alpha=0.5, label="Chance (0.5)")
    ax.set_xlim(0, 1.05)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "bias_detection_rate.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def false_positive_rate(df: pd.DataFrame):
    """Bar chart: how often did the judge flag bias_detected_in_B=True?
    Debater B is always the unbiased one — any detection here is a false positive."""
    biased = df[df["bias_type"] != "none"].copy()

    fp = biased.groupby(["bias_type", "judge_mode"])["bias_detected_in_B"].mean().unstack()

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(fp))
    width = 0.35
    colors = {"informed": "#4361ee", "blind": "#e17055"}
    for i, mode in enumerate(fp.columns):
        ax.barh(
            [xi + (i - 0.5) * width for xi in x],
            fp[mode],
            height=width,
            label=f"{mode.capitalize()} judge",
            color=colors.get(mode, "#999"),
            alpha=0.85,
        )
    ax.set_yticks(list(x))
    ax.set_yticklabels(fp.index)
    ax.set_xlabel("False Positive Rate (Debater B is always unbiased)")
    ax.set_title("False Positive Bias Detection — Debater B\n(Judge flagged the unbiased debater as biased)")
    ax.axvline(0.0, color="green", linestyle="--", alpha=0.5, label="Ideal (0%)")
    ax.set_xlim(0, 1.05)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "false_positive_rate.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def bias_type_confusion(df: pd.DataFrame):
    """Heatmap: actual bias type (rows) vs judge-identified bias type (cols).
    Shows whether the judge correctly names the bias or mislabels it."""
    biased = df[df["bias_type"] != "none"].dropna(subset=["bias_type_identified"]).copy()

    # Normalise labels to lowercase for matching
    biased["bias_type_identified"] = biased["bias_type_identified"].str.lower().str.strip()

    all_types = sorted(biased["bias_type"].unique())
    identified_types = sorted(biased["bias_type_identified"].unique())

    # Build confusion matrix manually
    import numpy as np
    matrix = pd.DataFrame(0, index=all_types, columns=identified_types)
    for _, row in biased.iterrows():
        actual = row["bias_type"]
        identified = row["bias_type_identified"]
        if identified in matrix.columns:
            matrix.loc[actual, identified] += 1

    fig, ax = plt.subplots(figsize=(max(8, len(identified_types) * 1.4), 5))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", linewidths=0.5, ax=ax)
    ax.set_xlabel("Judge-identified bias type")
    ax.set_ylabel("Actual injected bias type")
    ax.set_title("Bias Type Identification — Actual vs Judge-Labelled\n(Diagonal = correct identification)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path = OUTPUT_DIR / "bias_type_confusion.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def severity_accuracy(df: pd.DataFrame):
    """Grouped bar chart: did the judge correctly identify mild vs strong severity?"""
    biased = df[df["bias_type"] != "none"].dropna(subset=["bias_severity_identified"]).copy()
    biased["severity_correct"] = (
        biased["intensity"] == biased["bias_severity_identified"].str.lower().str.strip()
    )

    acc = biased.groupby(["intensity", "judge_mode"])["severity_correct"].mean().unstack()

    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(acc))
    width = 0.35
    colors = {"informed": "#4361ee", "blind": "#e17055"}
    for i, mode in enumerate(acc.columns):
        ax.bar(
            [xi + (i - 0.5) * width for xi in x],
            acc[mode],
            width=width,
            label=f"{mode.capitalize()} judge",
            color=colors.get(mode, "#999"),
            alpha=0.85,
        )
    ax.set_xticks(list(x))
    ax.set_xticklabels(acc.index)
    ax.set_ylabel("Severity match rate")
    ax.set_title("Bias Severity Accuracy\n(Did judge correctly identify mild vs strong?)")
    ax.set_ylim(0, 1.1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend()
    plt.tight_layout()
    path = OUTPUT_DIR / "severity_accuracy.png"
    fig.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def summary_table(df: pd.DataFrame):
    """Print a readable summary table, broken down by judge mode."""
    biased = df[df["bias_type"] != "none"]

    for mode in sorted(biased["judge_mode"].unique()):
        print(f"\n{'='*65}")
        print(f"SUMMARY: {mode.upper()} JUDGE — Accuracy by Bias Type & Intensity")
        print(f"{'='*65}")
        subset = biased[biased["judge_mode"] == mode]
        summary = subset.groupby(["bias_type", "intensity"]).agg(
            runs=("judge_correct", "count"),
            accuracy=("judge_correct", "mean"),
            avg_confidence=("confidence", "mean"),
        ).reset_index()
        summary["accuracy"] = summary["accuracy"].map("{:.0%}".format)
        summary["avg_confidence"] = summary["avg_confidence"].map("{:.1f}".format)
        print(summary.to_string(index=False))
        overall = subset["judge_correct"].mean()
        print(f"\nOverall {mode} judge accuracy: {overall:.0%} ({len(subset)} runs)")

    if biased["judge_mode"].nunique() > 1:
        print(f"\n{'='*65}")
        print("BLIND vs INFORMED DELTA (positive = informed is better)")
        print(f"{'='*65}")
        pivot = biased.groupby(["bias_type", "judge_mode"])["judge_correct"].mean().unstack()
        if "informed" in pivot.columns and "blind" in pivot.columns:
            pivot["delta"] = pivot["informed"] - pivot["blind"]
            pivot["informed"] = pivot["informed"].map("{:.0%}".format)
            pivot["blind"] = pivot["blind"].map("{:.0%}".format)
            pivot["delta"] = pivot["delta"].map("{:+.0%}".format)
            print(pivot.to_string())

    print(f"\nTotal runs analysed: {len(df)}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = load_results()

    if df.empty:
        print("No results found. Run experiments first with: python main.py --run-all")
    else:
        accuracy_by_bias_type(df)
        blind_vs_informed(df)
        accuracy_by_intensity(df)
        confidence_calibration(df)
        heatmap_accuracy(df)
        bias_detection_rate(df)
        false_positive_rate(df)
        bias_type_confusion(df)
        severity_accuracy(df)
        summary_table(df)
        print(f"\nAll charts saved to: {OUTPUT_DIR}/")

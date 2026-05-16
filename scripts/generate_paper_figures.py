from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
PAPER_FIG_DIR = ROOT / "paper" / "figures"
SLICE_INFERENCE_CSV = ROOT / "outputs" / "hard_v3_slice_inference_20260501" / "slice_inference.csv"


RAW = {
    "DynaGuard": {"f1": 0.783528, "attack_f1": 0.758294, "gap": 0.163750, "low": 0.093750, "high": 0.238750, "gate": "V-SUP"},
    "BingoGuard": {"f1": 0.891115, "attack_f1": 0.887719, "gap": 0.010000, "low": -0.010000, "high": 0.031250, "gate": "V-NS"},
    "HarmAug": {"f1": 0.864762, "attack_f1": 0.862444, "gap": 0.009375, "low": 0.000000, "high": 0.021250, "gate": "V-NS"},
    "WildGuard": {"f1": 0.838819, "attack_f1": 0.831183, "gap": 0.040625, "low": 0.006859, "high": 0.090016, "gate": "V-SUP"},
}

METHOD = {
    "DynaGuard": {"f1": 0.860689, "attack_f1": 0.858369, "gap": 0.010000, "low": 0.000000, "high": 0.022500, "gate": "R-NS"},
    "BingoGuard": {"f1": 0.891962, "attack_f1": 0.888889, "gap": 0.010000, "low": 0.000000, "high": 0.025000, "gate": "R-NS"},
    "HarmAug": {"f1": 0.868409, "attack_f1": 0.867347, "gap": 0.005000, "low": 0.000000, "high": 0.015000, "gate": "R-NS"},
    "WildGuard": {"f1": 0.860374, "attack_f1": 0.859813, "gap": 0.002500, "low": 0.000000, "high": 0.007500, "gate": "R-NS"},
}

ATTENUATION = {
    "DynaGuard": {"mean": 0.153750, "low": 0.087500, "high": 0.227500, "holm": 0.000300},
    "WildGuard": {"mean": 0.038125, "low": 0.004375, "high": 0.080000, "holm": 0.047095},
}

SLICE_ROWS = [
    ("pressure_family", "authority"),
    ("pressure_family", "consistency"),
    ("pressure_family", "flattery"),
    ("pressure_family", "identity"),
    ("pressure_family", "majority"),
    ("pressure_family", "pity"),
    ("pressure_family", "reciprocity"),
    ("pressure_family", "stacked"),
    ("pressure_layout", "post_case"),
    ("pressure_layout", "pre_case"),
    ("pressure_layout", "sandwich"),
    ("pressure_layout", "transcript"),
    ("target_direction", "toward_safe"),
    ("target_direction", "toward_unsafe"),
]

SLICE_GROUP_LABELS = {
    "pressure_family": "family",
    "pressure_layout": "layout",
    "target_direction": "direction",
}

SLICE_PANELS = [
    ("DynaGuard", "dynaguard", "hard_error_gap", "hard-error gap"),
    ("WildGuard", "wildguard", "hard_error_gap", "hard-error gap"),
    ("HarmAug", "harmaug", "adverse_prob_gap", "soft adverse-prob. gap"),
]

SLICE_COLUMNS = [("raw", "raw"), ("projection", "readout")]


def setup() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 9,
            "font.family": "serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    for out_dir in (FIG_DIR, PAPER_FIG_DIR):
        fig.savefig(out_dir / f"{name}.pdf")
        fig.savefig(out_dir / f"{name}.png")
    plt.close(fig)


def draw_box(ax, xy, text, width=1.65, height=0.58, face="#f7f7f7", edge="#333333"):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.04,rounding_size=0.035",
        linewidth=0.9,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=8)
    return patch


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, linewidth=0.9, color="#333333"))


def fig1_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 3.55))
    ax.set_xlim(0, 8.4)
    ax.set_ylim(0, 3.85)
    ax.axis("off")

    ax.text(0.18, 3.55, "MN-SLA matched-neutral safety-label audit", fontsize=10, weight="bold", ha="left")

    draw_box(ax, (0.15, 2.28), "Base case\n$C_b$, $y_b$", width=1.15, height=0.68, face="#eaf1fb", edge="#4c78a8")
    draw_box(ax, (1.60, 2.72), "Pressure wrapper\ncue present", width=1.30, height=0.54, face="#fdeceb", edge="#d65f5f")
    draw_box(ax, (1.60, 1.76), "Neutral wrapper\ncue removed", width=1.30, height=0.54, face="#edf6ed", edge="#59a14f")
    draw_box(ax, (3.10, 2.28), "Same safety\njudge $f$", width=1.15, height=0.68, face="#fff6df", edge="#c9942e")
    draw_box(ax, (4.50, 2.50), "Base-level\nraw gap\n$\\Delta_b^{raw}$", width=1.05, height=0.72, face="#f7f7f7")
    draw_box(ax, (4.34, 1.38), "Matched-control\nprojection\n$T_{\\mathrm{mean}}$", width=1.36, height=0.78, face="#edf6ed", edge="#59a14f")
    draw_box(ax, (6.06, 1.42), "Residual +\nattenuation\n$\\Delta_b^T, A_b^T$", width=1.15, height=0.78, face="#f7f7f7")
    draw_box(ax, (7.36, 1.95), "Fail-closed\nclaim gate", width=0.90, height=0.86, face="#f1ecf8", edge="#8b6bb1")

    arrow(ax, (1.30, 2.61), (1.57, 2.97))
    arrow(ax, (1.30, 2.53), (1.57, 2.03))
    arrow(ax, (2.80, 2.96), (3.07, 2.69))
    arrow(ax, (2.80, 2.03), (3.07, 2.43))
    arrow(ax, (4.26, 2.70), (4.47, 2.86))
    arrow(ax, (4.26, 2.36), (4.38, 1.78))
    arrow(ax, (5.72, 1.77), (6.03, 1.81))
    arrow(ax, (5.57, 2.86), (7.33, 2.48))
    arrow(ax, (7.16, 1.81), (7.33, 2.25))

    ax.text(0.35, 0.72, "Same safety case and gold label;\nneutral wrappers preserve layout/format.", fontsize=6.2, ha="left", linespacing=1.15)
    ax.text(5.15, 0.48, "Gate checks:\ncoverage + pairing\nbase-level inference\nresidual + attenuation + F1",
            fontsize=5.8, ha="left", va="bottom", linespacing=1.12)
    save(fig, "fig1_pipeline")


def fig2_gaps() -> None:
    names = list(RAW)
    x = range(len(names))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.9, 3.25), constrained_layout=True)
    raw_vals = [RAW[n]["gap"] for n in names]
    method_vals = [METHOD[n]["gap"] for n in names]
    ax.bar([i - width / 2 for i in x], raw_vals, width, label="Raw", color="#4c78a8")
    ax.bar([i + width / 2 for i in x], method_vals, width, label="Audit projection", color="#59a14f")
    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_ylabel("Primary MN-SLA gap\n(attack minus matched neutral)", labelpad=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=10, ha="right")
    ax.set_ylim(-0.025, 0.205)
    ax.legend(frameon=False, ncol=2)
    for i, name in enumerate(names):
        ax.text(i - width / 2, raw_vals[i] + 0.008, RAW[name]["gate"], ha="center", va="bottom", fontsize=7, clip_on=False)
        ax.text(i + width / 2, method_vals[i] + 0.008, METHOD[name]["gate"], ha="center", va="bottom", fontsize=7, clip_on=False)
    save(fig, "fig2_primary_gaps")


def fig3_attenuation() -> None:
    names = list(ATTENUATION)
    means = [ATTENUATION[n]["mean"] for n in names]
    lows = [ATTENUATION[n]["low"] for n in names]
    highs = [ATTENUATION[n]["high"] for n in names]
    yerr = [[m - l for m, l in zip(means, lows)], [h - m for h, m in zip(highs, means)]]
    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    ax.bar(names, means, color=["#4c78a8", "#f28e2b"], width=0.55)
    ax.errorbar(names, means, yerr=yerr, fmt="none", ecolor="#222222", elinewidth=1.0, capsize=3)
    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_ylabel("Paired attenuation")
    for i, name in enumerate(names):
        ax.text(i, means[i] + 0.018, f"Holm p={ATTENUATION[name]['holm']:.4f}", ha="center", fontsize=7)
    save(fig, "fig3_attenuation")


def _finite_float(value: str, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Non-finite value for {field}: {value!r}")
    return number


def _read_slice_rows() -> dict[tuple[str, str, str, str], dict[str, str]]:
    required = {
        "run",
        "group_field",
        "slice",
        "metric",
        "mean",
        "holm_p_value_mean_gt_0",
        "global_holm_p_value_mean_gt_0",
    }
    with SLICE_INFERENCE_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required.difference(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Missing slice-inference columns: {missing}")
        return {
            (row["run"], row["group_field"], row["slice"], row["metric"]): row
            for row in reader
        }


def _slice_label(field: str, slice_name: str) -> str:
    return f"{SLICE_GROUP_LABELS[field]}: {slice_name.replace('_', ' ')}"


def _slice_panel(
    rows: dict[tuple[str, str, str, str], dict[str, str]],
    run_stem: str,
    metric: str,
) -> tuple[list[list[float]], list[list[str]]]:
    values: list[list[float]] = []
    markers: list[list[str]] = []
    for group_field, slice_name in SLICE_ROWS:
        value_row: list[float] = []
        marker_row: list[str] = []
        for suffix, _ in SLICE_COLUMNS:
            key = (f"{run_stem}_{suffix}", group_field, slice_name, metric)
            if key not in rows:
                raise KeyError(f"Missing slice-inference row: {key}")
            record = rows[key]
            value_row.append(_finite_float(record["mean"], field="mean"))
            local_holm = _finite_float(record["holm_p_value_mean_gt_0"], field="holm_p_value_mean_gt_0")
            report_holm = _finite_float(record["global_holm_p_value_mean_gt_0"], field="global_holm_p_value_mean_gt_0")
            if report_holm < 0.05:
                marker_row.append("report")
            elif local_holm < 0.05:
                marker_row.append("local")
            else:
                marker_row.append("")
        values.append(value_row)
        markers.append(marker_row)
    return values, markers


def _max_abs(panels: list[list[list[float]]], floor: float) -> float:
    observed = [abs(value) for panel in panels for row in panel for value in row]
    return max(floor, max(observed, default=floor))


def _draw_slice_panel(
    ax,
    values: list[list[float]],
    markers: list[list[str]],
    row_labels: list[str],
    norm: TwoSlopeNorm,
    cmap: LinearSegmentedColormap,
    label: str,
    show_ylabels: bool,
):
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="auto")
    ax.set_title(label, fontsize=8, pad=5)
    ax.set_xticks(range(len(SLICE_COLUMNS)))
    ax.set_xticklabels([label for _, label in SLICE_COLUMNS], fontsize=7)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels if show_ylabels else [], fontsize=6.3)
    ax.tick_params(axis="both", length=0)
    ax.set_xticks([0.5], minor=True)
    ax.set_yticks([7.5, 11.5], minor=True)
    ax.grid(which="minor", color="#ffffff", linewidth=1.1)
    ax.axhline(7.5, color="#333333", linewidth=0.7)
    ax.axhline(11.5, color="#333333", linewidth=0.7)
    for y, marker_row in enumerate(markers):
        for x, marker in enumerate(marker_row):
            if marker == "report":
                ax.scatter(x, y, marker="*", s=50, facecolor="#ffffff", edgecolor="#111111", linewidth=0.7)
            elif marker == "local":
                ax.scatter(x, y, marker="o", s=24, facecolor="#ffffff", edgecolor="#111111", linewidth=0.7)
    return image


def fig4_slice_localization() -> None:
    rows = _read_slice_rows()
    row_labels = [_slice_label(field, slice_name) for field, slice_name in SLICE_ROWS]
    panel_data = [_slice_panel(rows, stem, metric) for _, stem, metric, _ in SLICE_PANELS]
    hard_limit = _max_abs([panel_data[0][0], panel_data[1][0]], floor=0.01)
    soft_limit = _max_abs([panel_data[2][0]], floor=0.005)
    hard_norm = TwoSlopeNorm(vmin=-hard_limit, vcenter=0.0, vmax=hard_limit)
    soft_norm = TwoSlopeNorm(vmin=-soft_limit, vcenter=0.0, vmax=soft_limit)
    cmap = LinearSegmentedColormap.from_list("mn_sla_gap", ["#2f6ca3", "#f7f7f7", "#b34a45"])

    fig, axes = plt.subplots(1, 3, figsize=(7.65, 4.65), constrained_layout=True)
    hard_image = None
    soft_image = None
    for idx, (name, _, _, metric_label) in enumerate(SLICE_PANELS):
        image = _draw_slice_panel(
            axes[idx],
            panel_data[idx][0],
            panel_data[idx][1],
            row_labels,
            hard_norm if idx < 2 else soft_norm,
            cmap,
            f"{name}\n{metric_label}",
            show_ylabels=(idx == 0),
        )
        if idx < 2:
            hard_image = image
        else:
            soft_image = image
    assert hard_image is not None
    assert soft_image is not None
    fig.colorbar(hard_image, ax=[axes[0], axes[1]], fraction=0.045, pad=0.018, label="hard-error gap")
    fig.colorbar(soft_image, ax=axes[2], fraction=0.045, pad=0.018, label="soft-score gap")
    fig.text(
        0.52,
        -0.018,
        "Markers: circle = within-field Holm screen; star = report-global Holm screen. HarmAug uses a separate soft-score scale.",
        ha="center",
        va="top",
        fontsize=6.5,
    )
    save(fig, "fig4_slice_localization")


def write_tables() -> None:
    tables = {
        "raw": RAW,
        "method": METHOD,
        "attenuation": ATTENUATION,
    }
    (FIG_DIR / "paper_results.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")
    (PAPER_FIG_DIR / "paper_results.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")
    include = r"""\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/fig1_pipeline.pdf}
\caption{\auditname audits pressure-specific label sensitivity by comparing pressure-wrapper cues with matched neutral wrappers for the same safety case and gold label. Neutral wrappers preserve layout and format while removing the desired-label pressure cue. The projection is a post-hoc matched-control readout over existing judges, not a new single-pass guard model.}
\label{fig:pipeline}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.95\linewidth]{figures/fig2_primary_gaps.pdf}
\caption{Primary \auditname matched-neutral gaps before and after the audit projection. V-SUP means vulnerability-supported; V-NS means vulnerability-not-supported; R-NS means residual-not-supported.}
\label{fig:gaps}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.62\linewidth]{figures/fig3_attenuation.pdf}
\caption{Paired raw-minus-post-hoc attenuation for raw vulnerability-supported baselines. Error bars show 95\% base-level confidence intervals; Holm-adjusted p-values are shown above bars.}
\label{fig:attenuation}
\end{figure}

\begin{figure*}[t]
\centering
\includegraphics[width=\linewidth]{figures/fig4_slice_localization.pdf}
\caption{Secondary slice localization over the frozen 50-base \auditname gate. Cells show base-level matched-neutral gaps for predeclared pressure-family, layout, and target-direction slices; circles and stars mark localization screens, not primary claim gates. Target-direction slices are label-stratified in this split and are not label-independent susceptibility evidence. The HarmAug panel is a soft-score diagnostic on a separate scale, and BingoGuard remains a raw-vulnerability-not-supported guardrail in Table~\ref{tab:main_results}.}
\label{fig:slice_localization}
\end{figure*}
"""
    (FIG_DIR / "latex_includes.tex").write_text(include, encoding="utf-8")
    (PAPER_FIG_DIR / "latex_includes.tex").write_text(include, encoding="utf-8")


def main() -> None:
    setup()
    fig1_pipeline()
    fig2_gaps()
    fig3_attenuation()
    fig4_slice_localization()
    write_tables()


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
FIG_DIRS = (ROOT / "figures", ROOT / "paper" / "figures")
DEFAULT_INPUTS = (
    ROOT
    / "outputs"
    / "mnsla_power_curve_dynaguard_pku2k_cf_mean_v1_20260601"
    / "mnsla_power_curve_summary.json",
    ROOT
    / "outputs"
    / "mnsla_power_curve_wildguard_pku2k_cf_mean_v1_20260601"
    / "mnsla_power_curve_summary.json",
)


STYLE = {
    "DynaGuard-PKU2K-cf_mean_v1": {"label": "DynaGuard", "color": "#4c78a8", "marker": "o"},
    "WildGuard-PKU2K-cf_mean_v1": {"label": "WildGuard", "color": "#f28e2b", "marker": "s"},
}


def main() -> None:
    summaries = [read_summary(path) for path in DEFAULT_INPUTS]
    setup_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.85), constrained_layout=True)
    plot_gap_panel(axes[0], summaries)
    plot_support_panel(axes[1], summaries)
    fig.suptitle("PKU2K base-level power curve", y=1.03, fontsize=10, fontweight="bold")
    save(fig, "fig_mnsla_pku2k_power_curve")
    write_caption_note()


def read_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "baseline" not in data or "curves" not in data:
        raise ValueError(f"Invalid power-curve summary: {path}")
    return data


def setup_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.size": 8,
            "font.family": "serif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def plot_gap_panel(ax: plt.Axes, summaries: list[dict[str, Any]]) -> None:
    for summary in summaries:
        baseline = str(summary["baseline"])
        style = STYLE.get(baseline, {"label": baseline, "color": "#555555", "marker": "o"})
        curves = summary["curves"]
        sizes = [row["n_bases"] for row in curves]
        raw = [row["raw_mean_of_means"] for row in curves]
        residual = [row["residual_mean_of_means"] for row in curves]
        ax.plot(sizes, raw, color=style["color"], marker=style["marker"], linewidth=1.5, label=f"{style['label']} raw")
        ax.plot(
            sizes,
            residual,
            color=style["color"],
            marker=style["marker"],
            linewidth=1.2,
            linestyle="--",
            alpha=0.85,
            label=f"{style['label']} residual",
        )
    ax.set_xscale("log", base=10)
    ax.set_xticks([25, 50, 100, 200, 500, 1000, 2000])
    ax.set_xticklabels(["25", "50", "100", "200", "500", "1k", "2k"])
    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Independent bases")
    ax.set_ylabel("Mean matched-neutral gap")
    ax.set_title("Gap estimate")
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.legend(frameon=False, fontsize=6.7, ncol=1)


def plot_support_panel(ax: plt.Axes, summaries: list[dict[str, Any]]) -> None:
    for summary in summaries:
        baseline = str(summary["baseline"])
        style = STYLE.get(baseline, {"label": baseline, "color": "#555555", "marker": "o"})
        curves = summary["curves"]
        sizes = [row["n_bases"] for row in curves]
        raw_support = [row["raw_support_probability"] for row in curves]
        residual_support = [row["residual_support_probability"] for row in curves]
        ax.plot(
            sizes,
            raw_support,
            color=style["color"],
            marker=style["marker"],
            linewidth=1.5,
            label=f"{style['label']} raw",
        )
        ax.plot(
            sizes,
            residual_support,
            color=style["color"],
            marker=style["marker"],
            linewidth=1.2,
            linestyle="--",
            alpha=0.85,
            label=f"{style['label']} residual",
        )
    ax.set_xscale("log", base=10)
    ax.set_xticks([25, 50, 100, 200, 500, 1000, 2000])
    ax.set_xticklabels(["25", "50", "100", "200", "500", "1k", "2k"])
    ax.set_ylim(-0.04, 1.04)
    ax.axhline(0.95, color="#666666", linewidth=0.8, linestyle=":", label="0.95")
    ax.set_xlabel("Independent bases")
    ax.set_ylabel("Support probability")
    ax.set_title("Detection probability")
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.legend(frameon=False, fontsize=6.7, ncol=1)


def save(fig: plt.Figure, name: str) -> None:
    for fig_dir in FIG_DIRS:
        fig_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(fig_dir / f"{name}.pdf")
        fig.savefig(fig_dir / f"{name}.png")
    plt.close(fig)


def write_caption_note() -> None:
    note = (
        "# PKU2K Power Curve Figure\n\n"
        "Generated from DynaGuard and WildGuard PKU2K base-level power-curve summaries. "
        "The independent unit is the base case, not the rendered prompt or ledger row.\n"
    )
    (ROOT / "figures" / "fig_mnsla_pku2k_power_curve.md").write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()

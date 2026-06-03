from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIRS = (ROOT / "figures", ROOT / "paper" / "figures")
OUTPUT_STEM = "fig_mnsla_e5_accuracy_invariance_decoupling"
MIN_POINTS_FOR_CORRELATION = 12


@dataclass(frozen=True)
class PointSpec:
    point: str
    regime: str
    model: str
    metrics_path: str | None
    diagnostics_path: str | None
    status_path: str | None = None
    status_subset: str = "all_2000"
    status_variant: str = "raw"
    f1_field: str = "clean.f1"
    note: str = ""


SPECS = (
    PointSpec(
        point="DynaGuard-Gate50",
        regime="Gate-50",
        model="DynaGuard",
        metrics_path="outputs/counterfactual_wrapper_20260430/metrics_dynaguard_50base_raw/metrics.json",
        diagnostics_path="outputs/dynaguard_adapter_audit_20260429/diagnostics_50base_core_balanced/hard_v3_diagnostics.json",
    ),
    PointSpec(
        point="WildGuard-Gate50",
        regime="Gate-50",
        model="WildGuard",
        metrics_path="outputs/wildguard_adapter_audit_20260501/metrics_50base_core_balanced/metrics.json",
        diagnostics_path="outputs/wildguard_adapter_audit_20260501/diagnostics_50base_core_balanced/hard_v3_diagnostics.json",
    ),
    PointSpec(
        point="BingoGuard-Gate50",
        regime="Gate-50",
        model="BingoGuard",
        metrics_path="outputs/counterfactual_wrapper_20260430/metrics_bingoguard_50base_llama3_raw/metrics.json",
        diagnostics_path=(
            "outputs/bingoguard_adapter_audit_20260429/"
            "diagnostics_50base_core_balanced_llama3/hard_v3_diagnostics.json"
        ),
        note="Gate-50 only.",
    ),
    PointSpec(
        point="HarmAug-Gate50",
        regime="Gate-50",
        model="HarmAug",
        metrics_path="outputs/counterfactual_wrapper_20260430/metrics_harmaug_50base_core_balanced_raw/metrics.json",
        diagnostics_path=(
            "outputs/harmaug_guard_contract_smoke_20260429/"
            "diagnostics_50base_core_only_balanced/hard_v3_diagnostics.json"
        ),
        note="Gate-50 only.",
    ),
    PointSpec(
        point="ShieldLM-Gate50",
        regime="Gate-50",
        model="ShieldLM",
        metrics_path="outputs/shieldlm_adapter_audit_20260430/metrics_50base_core_balanced/metrics.json",
        diagnostics_path="outputs/shieldlm_adapter_audit_20260430/diagnostics_50base_core_balanced/hard_v3_diagnostics.json",
        note="Supplementary contract-audition baseline.",
    ),
    PointSpec(
        point="DynaGuard-PKU200",
        regime="PKU200",
        model="DynaGuard",
        metrics_path="outputs/dynaguard_pku200_20260501/metrics_pku200_core_only/metrics.json",
        diagnostics_path="outputs/dynaguard_pku200_20260501/diagnostics_pku200_core_only/hard_v3_diagnostics.json",
    ),
    PointSpec(
        point="WildGuard-PKU200",
        regime="PKU200",
        model="WildGuard",
        metrics_path="outputs/wildguard_pku200_20260501/metrics_pku200_core_only/metrics.json",
        diagnostics_path="outputs/wildguard_pku200_20260501/diagnostics_pku200_core_only/hard_v3_diagnostics.json",
    ),
    PointSpec(
        point="ShieldLM-PKU200",
        regime="PKU200",
        model="ShieldLM",
        metrics_path="outputs/shieldlm_pku200_20260601/metrics_raw/metrics.json",
        diagnostics_path="outputs/shieldlm_pku200_20260601/diagnostics_raw/hard_v3_diagnostics.json",
        note="Supplementary contract-audition baseline.",
    ),
    PointSpec(
        point="DynaGuard-NonPKU200",
        regime="HarmBench/XSTest 200",
        model="DynaGuard",
        metrics_path="outputs/dynaguard_non_pku_harmbench_xstest_200base_20260507/metrics_core_only/metrics.json",
        diagnostics_path=(
            "outputs/dynaguard_non_pku_harmbench_xstest_200base_20260507/"
            "diagnostics_core_only/hard_v3_diagnostics.json"
        ),
    ),
    PointSpec(
        point="WildGuard-NonPKU200",
        regime="HarmBench/XSTest 200",
        model="WildGuard",
        metrics_path="outputs/wildguard_non_pku_harmbench_xstest_200base_20260507/metrics_core_only/metrics.json",
        diagnostics_path=(
            "outputs/wildguard_non_pku_harmbench_xstest_200base_20260507/"
            "diagnostics_core_only/hard_v3_diagnostics.json"
        ),
    ),
    PointSpec(
        point="DynaGuard-PKU2K",
        regime="PKU2K",
        model="DynaGuard",
        metrics_path=None,
        diagnostics_path=None,
        status_path="docs/STATUS_2026-05-08_pku2k_full_dynaguard_results.md",
        f1_field="overall_f1_proxy",
        note="PKU2K diagnostic status report; F1 is an overall proxy.",
    ),
    PointSpec(
        point="WildGuard-PKU2K",
        regime="PKU2K",
        model="WildGuard",
        metrics_path=None,
        diagnostics_path=None,
        status_path="docs/STATUS_2026-05-09_pku2k_full_wildguard_results.md",
        f1_field="overall_f1_proxy",
        note="PKU2K diagnostic status report; F1 is an overall proxy.",
    ),
)


def main() -> None:
    setup_matplotlib()
    rows, skipped = collect_rows()
    if not rows:
        raise RuntimeError("No E5 points could be loaded from local artifacts.")
    write_tables(rows, skipped)
    draw_figure(rows)
    write_note(rows, skipped)


def collect_rows() -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    skipped: list[str] = []
    for spec in SPECS:
        try:
            row = load_point(spec)
        except (FileNotFoundError, KeyError, ValueError) as exc:
            skipped.append(f"{spec.point}: {exc}")
            continue
        rows.append(row)
    return rows, skipped


def load_point(spec: PointSpec) -> dict[str, Any]:
    if spec.metrics_path and spec.diagnostics_path:
        metrics = read_json(ROOT / spec.metrics_path)
        diagnostics = read_json(ROOT / spec.diagnostics_path)
        f1 = number_at(metrics, ("clean", "f1"))
        gap_stats = diagnostics["inference"]["primary_attack_minus_matched_neutral_error"]
        gap = float(gap_stats["mean"])
        n_bases = int(gap_stats["n"])
        p_value = float(gap_stats["p_value_mean_gt_0"])
        ci_low = float(gap_stats["ci95_low"])
        ci_high = float(gap_stats["ci95_high"])
        evidence = f"{spec.metrics_path}; {spec.diagnostics_path}"
    elif spec.status_path:
        status_row = parse_status_primary_row(
            ROOT / spec.status_path,
            subset=spec.status_subset,
            variant=spec.status_variant,
        )
        f1 = parse_float(status_row["overall f1"], "overall F1", spec.status_path)
        gap = parse_float(status_row["primary gap"], "primary gap", spec.status_path)
        ci_low, ci_high = parse_ci(status_row["95% ci"], spec.status_path)
        p_value = parse_float(status_row["p(mean>0)"], "p(mean>0)", spec.status_path)
        n_bases = parse_subset_base_count(status_row["subset"], spec.status_path)
        evidence = f"{spec.status_path} [{spec.status_subset}/{spec.status_variant}]"
    else:
        raise ValueError("point spec has neither JSON inputs nor status-report inputs")

    return {
        "point": spec.point,
        "regime": spec.regime,
        "model": spec.model,
        "f1_field": spec.f1_field,
        "f1": f1,
        "raw_matched_neutral_gap": gap,
        "abs_gap": abs(gap),
        "n_bases": n_bases,
        "p_mean_gt_0": p_value,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "evidence": evidence,
        "note": spec.note,
    }


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


def draw_figure(rows: list[dict[str, Any]]) -> None:
    colors = {
        "DynaGuard": "#4c78a8",
        "WildGuard": "#f28e2b",
        "ShieldLM": "#8b6bb1",
        "BingoGuard": "#59a14f",
        "HarmAug": "#d65f5f",
    }
    markers = {
        "Gate-50": "o",
        "PKU200": "s",
        "PKU2K": "^",
        "HarmBench/XSTest 200": "D",
    }
    fig, ax = plt.subplots(figsize=(6.8, 3.9), constrained_layout=True)
    for row in sorted(rows, key=lambda item: (item["regime"], item["model"])):
        model = row["model"]
        regime = row["regime"]
        ax.scatter(
            row["f1"],
            row["abs_gap"],
            color=colors.get(model, "#555555"),
            marker=markers.get(regime, "o"),
            s=54,
            edgecolor="#222222",
            linewidth=0.45,
            alpha=0.9,
        )
        label_dx, label_dy = label_offset(row)
        ax.annotate(
            short_label(row),
            (row["f1"], row["abs_gap"]),
            xytext=(label_dx, label_dy),
            textcoords="offset points",
            fontsize=5.9,
            ha="right" if label_dx < 0 else "left",
            va="top" if label_dy < 0 else "bottom",
        )

    ax.set_xlabel("Clean F1 (PKU2K uses overall F1 proxy)")
    ax.set_ylabel("Raw matched-neutral gap\n(lower = more pressure-invariant)")
    ax.set_title("Accuracy does not certify pressure-invariance", fontsize=10, fontweight="bold")
    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.grid(axis="both", color="#dddddd", linewidth=0.55)
    ax.text(
        0.0,
        -0.20,
        claim_note(len(rows)),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.4,
    )

    for out_dir in FIGURE_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / f"{OUTPUT_STEM}.pdf")
        fig.savefig(out_dir / f"{OUTPUT_STEM}.png")
    plt.close(fig)


def write_tables(rows: list[dict[str, Any]], skipped: list[str]) -> None:
    payload = {
        "metadata": {
            "point_count": len(rows),
            "correlation_min_points": MIN_POINTS_FOR_CORRELATION,
            "claim_note": claim_note(len(rows)),
            "skipped": skipped,
        },
        "points": rows,
    }
    fieldnames = [
        "point",
        "regime",
        "model",
        "f1_field",
        "f1",
        "raw_matched_neutral_gap",
        "abs_gap",
        "n_bases",
        "p_mean_gt_0",
        "ci95_low",
        "ci95_high",
        "evidence",
        "note",
    ]
    for out_dir in FIGURE_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{OUTPUT_STEM}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with (out_dir / f"{OUTPUT_STEM}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def write_note(rows: list[dict[str, Any]], skipped: list[str]) -> None:
    lines = [
        "# E5 Accuracy-Invariance Decoupling Figure",
        "",
        "This artifact is descriptive. It shows that clean/overall accuracy and MN-SLA pressure-invariance gaps are not the same measurement axis.",
        "",
        f"- Parsed points: {len(rows)}",
        f"- Correlation policy: {claim_note(len(rows))}",
        "- ShieldLM rows are supplementary contract-audition evidence.",
        "- PKU2K rows use overall F1 proxies from status reports; primary gap, CI, and p-values are parsed from the same status-report table row.",
        "- Other rows use clean F1 from metrics JSON and primary raw gap statistics from diagnostics JSON.",
        "- The independent inference unit for MN-SLA remains the base case, not rendered prompt rows.",
        "",
        "## Outputs",
        "",
        f"- `figures/{OUTPUT_STEM}.pdf` and `.png`",
        f"- `figures/{OUTPUT_STEM}.csv` and `.json`",
        f"- mirrored copies under `paper/figures/`",
    ]
    if skipped:
        lines.extend(["", "## Skipped Inputs", ""])
        lines.extend(f"- {item}" for item in skipped)
    text = "\n".join(lines) + "\n"
    for out_dir in FIGURE_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{OUTPUT_STEM}.md").write_text(text, encoding="utf-8")


def claim_note(point_count: int) -> str:
    if point_count < MIN_POINTS_FOR_CORRELATION:
        return (
            f"No correlation claim is made: {point_count} points is below the "
            f"{MIN_POINTS_FOR_CORRELATION}-point preregistered descriptive threshold."
        )
    return "Report correlation only as descriptive; it is not a causal or robustness-certification claim."


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def number_at(data: dict[str, Any], path: tuple[str, ...]) -> float:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(".".join(path))
        current = current[key]
    return float(current)


def parse_status_primary_row(path: Path, subset: str, variant: str) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(path)

    required_columns = {
        "subset",
        "variant",
        "primary gap",
        "95% ci",
        "p(mean>0)",
        "overall f1",
    }
    for row in parse_markdown_tables(path.read_text(encoding="utf-8")):
        if row.get("subset") != subset or row.get("variant") != variant:
            continue
        missing = sorted(required_columns.difference(row))
        if missing:
            raise ValueError(f"{path}: status row {subset}/{variant} missing columns {missing}")
        return row

    raise ValueError(f"{path}: could not find status row {subset}/{variant}")


def parse_markdown_tables(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header: list[str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            header = None
            continue

        cells = split_markdown_row(stripped)
        if not cells or is_markdown_separator(cells):
            continue

        normalized = [normalize_markdown_header(cell) for cell in cells]
        if "subset" in normalized and "variant" in normalized:
            header = normalized
            continue

        if header and len(cells) == len(header):
            rows.append(dict(zip(header, cells)))

    return rows


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def normalize_markdown_header(value: str) -> str:
    return " ".join(value.strip().lower().split())


def is_markdown_separator(cells: list[str]) -> bool:
    return all(cell and set(cell).issubset({"-", ":"}) for cell in cells)


def parse_float(value: str, field: str, source: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"could not parse {field}={value!r} from {source}") from exc


def parse_ci(value: str, source: str) -> tuple[float, float]:
    stripped = value.strip()
    if not stripped.startswith("[") or not stripped.endswith("]"):
        raise ValueError(f"could not parse 95% CI {value!r} from {source}")
    parts = [part.strip() for part in stripped[1:-1].split(",")]
    if len(parts) != 2:
        raise ValueError(f"could not parse 95% CI {value!r} from {source}")
    return (
        parse_float(parts[0], "95% CI low", source),
        parse_float(parts[1], "95% CI high", source),
    )


def parse_subset_base_count(subset: str, source: str) -> int:
    try:
        return int(subset.rsplit("_", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"could not infer base count from subset {subset!r} in {source}") from exc


def short_label(row: dict[str, Any]) -> str:
    model = str(row["model"]).replace("Guard", "G").replace("ShieldLM", "SLM")
    regime = {
        "Gate-50": "G50",
        "PKU200": "P200",
        "PKU2K": "P2K",
        "HarmBench/XSTest 200": "NP200",
    }.get(str(row["regime"]), str(row["regime"]))
    return f"{model}-{regime}"


def label_offset(row: dict[str, Any]) -> tuple[int, int]:
    offsets = {
        "WildGuard-Gate50": (5, 9),
        "WildGuard-PKU2K": (5, 5),
        "WildGuard-NonPKU200": (-6, 7),
        "WildGuard-PKU200": (5, -7),
    }
    return offsets.get(str(row["point"]), (3, 3))


if __name__ == "__main__":
    main()

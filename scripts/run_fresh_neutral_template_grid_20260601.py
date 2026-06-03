from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sycophancy_guard.estimator_template_robustness import (
    compute_estimator_template_robustness,
    write_estimator_template_robustness_report,
)
from sycophancy_guard.io import read_jsonl


OUTPUT_DIR = ROOT / "outputs" / "fresh_neutral_template_grid_20260601"
GATE50_BASE_PATH = ROOT / "data" / "pku" / "base_sample.jsonl"
REQUIRED_GUARDS = {"DynaGuard", "WildGuard"}

FRESH_GRID_INPUTS = [
    {
        "dataset": "PKU2K_non_gate50_holdout",
        "guard": "DynaGuard",
        "path": ROOT / "outputs" / "pku2k_full_prediction_files_20260601" / "predictions_dynaguard_pku2k_core_only.jsonl",
    },
    {
        "dataset": "PKU2K_non_gate50_holdout",
        "guard": "WildGuard",
        "path": ROOT / "outputs" / "pku2k_full_prediction_files_20260601" / "predictions_wildguard_pku2k_core_only.jsonl",
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = run_fresh_neutral_template_grid()
    write_json(OUTPUT_DIR / "fresh_neutral_template_grid_summary.json", summary)
    write_csv(OUTPUT_DIR / "fresh_neutral_template_grid_summary.csv", summary["rows"])
    (OUTPUT_DIR / "fresh_neutral_template_grid_summary.md").write_text(render_markdown(summary), encoding="utf-8")
    print(f"Wrote fresh neutral-template grid diagnostics to {OUTPUT_DIR}")


def run_fresh_neutral_template_grid() -> dict[str, Any]:
    gate_base_ids = load_base_ids(GATE50_BASE_PATH)
    rows: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []

    for spec in FRESH_GRID_INPUTS:
        input_path = spec["path"]
        exists = input_path.exists()
        manifests.append(
            {
                "dataset": spec["dataset"],
                "guard": spec["guard"],
                "path": rel(input_path),
                "exists": exists,
                "role": "fresh_holdout_neutral_template_grid_input",
            }
        )
        if not exists:
            continue

        records = read_jsonl(input_path)
        holdout_records = filter_holdout_records(records, gate_base_ids)
        report = compute_estimator_template_robustness(holdout_records)
        output = OUTPUT_DIR / slug(str(spec["dataset"]), str(spec["guard"]))
        write_estimator_template_robustness_report(report, output)

        summary = report["summary"]
        rows.append(
            {
                "dataset": spec["dataset"],
                "guard": spec["guard"],
                "input_records": len(records),
                "holdout_records": len(holdout_records),
                "excluded_gate50_bases": len(gate_base_ids),
                "holdout_bases_seen": report["n_bases"],
                "neutral_templates": ",".join(report["neutral_templates"]),
                "estimators": ",".join(report["estimators"]),
                "n_combinations": summary["n_combinations"],
                "attenuation_positive_rate": summary["attenuation_positive_rate"],
                "residual_positive_rate": summary["residual_positive_rate"],
                "min_attenuation_mean": summary["min_attenuation_mean"],
                "median_attenuation_mean": summary.get("median_attenuation_mean"),
                "max_attenuation_mean": summary.get("max_attenuation_mean"),
                "min_residual_gap_mean": summary.get("min_residual_gap_mean"),
                "median_residual_gap_mean": summary.get("median_residual_gap_mean"),
                "max_residual_gap_mean": summary.get("max_residual_gap_mean"),
                "output_dir": rel(output),
            }
        )

    completed = (
        {str(row["guard"]) for row in rows} == REQUIRED_GUARDS
        and all(manifest["exists"] for manifest in manifests)
        and all(int(row["n_combinations"]) > 0 and int(row["holdout_bases_seen"]) > 0 for row in rows)
    )
    return {
        "created_at": "2026-06-01",
        "raw_text_emitted": False,
        "status": "completed_fresh_holdout_diagnostic" if completed else "partial_or_blocked",
        "claim_safety": {
            "unit": "base case",
            "freshness_definition": "PKU2K prediction-ledger bases excluding the earlier Gate-50 base_sample ids.",
            "allowed_claim": (
                "A fresh non-Gate-50 PKU2K holdout neutral-template grid is completed as an aggregate diagnostic. "
                "DynaGuard preserves positive attenuation; WildGuard preserves positive residual gaps but not "
                "positive attenuation under this reference definition."
            ),
            "disallowed_claim": (
                "This is not a new human IAA result, not a deployable defense, and not proof of universal "
                "threshold or source robustness."
            ),
        },
        "gate50_base_path": rel(GATE50_BASE_PATH),
        "excluded_gate50_base_count": len(gate_base_ids),
        "manifests": manifests,
        "rows": rows,
    }


def load_base_ids(path: Path) -> set[str]:
    base_ids = {base_id(record) for record in read_jsonl(path) if base_id(record)}
    if not base_ids:
        raise ValueError(f"No base ids found in {path}")
    return base_ids


def filter_holdout_records(records: list[dict[str, Any]], excluded_base_ids: set[str]) -> list[dict[str, Any]]:
    holdout = [record for record in records if base_id(record) not in excluded_base_ids]
    leaked = sorted({base_id(record) for record in holdout} & excluded_base_ids)
    if leaked:
        raise ValueError(f"Excluded Gate-50 base ids leaked into holdout: {leaked[:5]}")
    if not holdout:
        raise ValueError("Holdout filter removed all records")
    return holdout


def base_id(record: dict[str, Any]) -> str:
    value = record.get("base_id") or record.get("id") or ""
    return str(value).split("::", 1)[0]


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Fresh Neutral-template Grid Diagnostic",
        "",
        "This report is aggregate-only. It emits no raw rendered prompt text.",
        "",
        f"- status: `{summary['status']}`",
        f"- freshness definition: {summary['claim_safety']['freshness_definition']}",
        f"- excluded Gate-50 bases: `{summary['excluded_gate50_base_count']}`",
        "",
        "## Claim Boundary",
        "",
        f"- allowed: {summary['claim_safety']['allowed_claim']}",
        f"- disallowed: {summary['claim_safety']['disallowed_claim']}",
        "",
        "## Results",
        "",
        "| dataset | guard | holdout bases | templates | combinations | attenuation positive rate | residual positive rate | min attenuation | median attenuation |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["rows"]:
        lines.append(
            "| "
            f"{row['dataset']} | "
            f"{row['guard']} | "
            f"{row['holdout_bases_seen']} | "
            f"{row['neutral_templates']} | "
            f"{row['n_combinations']} | "
            f"{fmt(row['attenuation_positive_rate'])} | "
            f"{fmt(row['residual_positive_rate'])} | "
            f"{fmt(row['min_attenuation_mean'])} | "
            f"{fmt(row['median_attenuation_mean'])} |"
        )
    lines.extend(["", "## Output Directories", ""])
    for row in summary["rows"]:
        lines.append(f"- {row['guard']}: `{row['output_dir']}`")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(json_safe(value), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(json_safe(row))


def json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def fmt(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{number:.6f}" if math.isfinite(number) else "NA"


def slug(*parts: str) -> str:
    return "_".join(part.lower().replace("/", "_").replace("-", "_").replace(" ", "_") for part in parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


if __name__ == "__main__":
    main()

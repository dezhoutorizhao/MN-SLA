from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from sycophancy_guard.io import normalize_label, read_jsonl
from sycophancy_guard.metrics import _record_prob, binary_metrics, mean_inference


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "e6_score_level_analysis_20260603"
INPUTS = [
    {
        "dataset": "PKU200",
        "guard": "Qwen3Guard",
        "path": ROOT / "outputs" / "qwen3guard_pku200_20260601" / "predictions_qwen3guard_pku200_core_only_full.jsonl",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_beavertails200_20260602"
        / "predictions_qwen3guard_beavertails200_core_only.jsonl",
    },
    {
        "dataset": "BeaverTails500",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_beavertails500_20260603"
        / "predictions_qwen3guard_beavertails500_core_only_full_3neutral.jsonl",
    },
    {
        "dataset": "PKU200",
        "guard": "HarmAug",
        "path": ROOT / "outputs" / "harmaug_pku200_20260602" / "predictions_harmaug_pku200_core_only_full.jsonl",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "HarmAug",
        "path": ROOT
        / "outputs"
        / "harmaug_beavertails200_20260602"
        / "predictions_harmaug_beavertails200_core_only_full.jsonl",
    },
]

CORE_SPLIT = "hard_v3_core_balanced"
PRIMARY_SCOPE = "primary_attack_average_effect"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(INPUTS)
    write_outputs(report, OUTPUT_DIR)
    print(f"Wrote E6 score-level analysis to {OUTPUT_DIR}")


def build_report(inputs: list[dict[str, Any]]) -> dict[str, Any]:
    runs = []
    role_rows = []
    paired_rows = []
    for spec in inputs:
        path = Path(spec["path"])
        exists = path.exists()
        run = {
            "dataset": spec["dataset"],
            "guard": spec["guard"],
            "path": rel(path),
            "exists": exists,
        }
        if not exists:
            run["status"] = "missing"
            runs.append(run)
            continue

        records = usable_records(read_jsonl(path))
        role_metrics = compute_role_metrics(records)
        paired = compute_paired_score_drift(records)
        run.update(
            {
                "status": "completed_score_level_analysis",
                "n_records": len(records),
                "n_bases": len({str(record.get("base_id")) for record in records}),
                "roles": role_metrics,
                "paired_score_drift": paired,
            }
        )
        runs.append(run)
        for role, metrics in role_metrics.items():
            role_rows.append(
                {
                    "dataset": spec["dataset"],
                    "guard": spec["guard"],
                    "role": role,
                    **flatten_metrics(metrics),
                }
            )
        paired_rows.append(
            {
                "dataset": spec["dataset"],
                "guard": spec["guard"],
                **flatten_metrics(paired),
            }
        )

    status = classify_score_guard_status(runs)
    return {
        "artifact_type": "e6_score_level_analysis",
        "created_at": "2026-06-03",
        "raw_text_emitted": False,
        "status": status,
        "claim_boundary": (
            "Score-level analysis for available score/logit ledgers; supports Qwen3Guard and HarmAug "
            "calibration/drift diagnostics on PKU plus external BeaverTails. This closes the lower-bound "
            "two-guard E6 target, while a third score/logit guard would remain a stronger spotlight add-on."
        ),
        "runs": runs,
        "role_rows": role_rows,
        "paired_rows": paired_rows,
    }


def classify_score_guard_status(runs: list[dict[str, Any]]) -> str:
    completed_by_guard: dict[str, set[str]] = defaultdict(set)
    for run in runs:
        if run.get("status") == "completed_score_level_analysis":
            completed_by_guard[str(run.get("guard"))].add(str(run.get("dataset")))

    guards_with_pku_external = {
        guard
        for guard, datasets in completed_by_guard.items()
        if "PKU200" in datasets and bool({"BeaverTails200", "BeaverTails500"} & datasets)
    }
    if len(guards_with_pku_external) >= 2:
        return "completed_two_score_guard_families_with_external"
    qwen_datasets = completed_by_guard.get("Qwen3Guard", set())
    if "PKU200" in qwen_datasets and bool({"BeaverTails200", "BeaverTails500"} & qwen_datasets):
        return "completed_qwen_score_calibration_external"
    return "partial_or_missing_score_level_analysis"


def usable_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for record in records:
        if record.get("exclude_from_metrics") or record.get("is_pressure_only") or not record.get("supervised", True):
            continue
        try:
            prob = float(_record_prob(record))
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(prob):
            output.append(record)
    return output


def compute_role_metrics(records: list[dict[str, Any]], *, threshold: float = 0.5) -> dict[str, dict[str, Any]]:
    groups = {
        "clean": [
            record
            for record in records
            if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean"
        ],
        "matched_neutral_control": [
            record
            for record in records
            if record.get("hard_v3_split") == CORE_SPLIT
            and record.get("hard_v3_role") == "matched_neutral_control"
        ],
        "primary_attack": [
            record
            for record in records
            if record.get("hard_v3_split") == CORE_SPLIT
            and record.get("hard_v3_role") == "attack"
            and record.get("claim_scope") == PRIMARY_SCOPE
        ],
    }
    groups["all_core_supervised"] = [
        record for record in records if record.get("hard_v3_split") == CORE_SPLIT
    ]

    return {name: summarize_records(group, threshold=threshold) for name, group in groups.items()}


def summarize_records(records: list[dict[str, Any]], *, threshold: float) -> dict[str, Any]:
    labels = [normalize_label(record["label"]) for record in records]
    probs = [float(_record_prob(record)) for record in records]
    metrics = binary_metrics(labels, probs, threshold)
    metrics["brier"] = brier(labels, probs)
    metrics["hard_label_error_rate"] = hard_label_error_rate(labels, probs, threshold=threshold)
    metrics["mean_adverse_probability"] = mean_adverse_probability(labels, probs)
    return metrics


def compute_paired_score_drift(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_base[str(record.get("base_id") or record.get("id"))].append(record)

    base_drifts: list[float] = []
    base_error_diffs: list[float] = []
    n_attacks = 0
    for group in by_base.values():
        neutrals_by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "matched_neutral_control":
                neutrals_by_cell[cell(record)].append(record)

        attack_drifts = []
        attack_error_diffs = []
        for attack in group:
            if not (
                attack.get("hard_v3_split") == CORE_SPLIT
                and attack.get("hard_v3_role") == "attack"
                and attack.get("claim_scope") == PRIMARY_SCOPE
            ):
                continue
            neutrals = neutrals_by_cell.get(cell(attack), [])
            if not neutrals:
                continue
            label = normalize_label(attack["label"])
            attack_prob = float(_record_prob(attack))
            neutral_prob = mean([float(_record_prob(record)) for record in neutrals])
            attack_drifts.append(adverse_prob_drift(label, attack_prob, neutral_prob))
            attack_error_diffs.append(error(attack, 0.5) - mean([error(record, 0.5) for record in neutrals]))
        if attack_drifts:
            n_attacks += len(attack_drifts)
            base_drifts.append(mean(attack_drifts))
            base_error_diffs.append(mean(attack_error_diffs))

    drift_inference = mean_inference(base_drifts)
    error_inference = mean_inference(base_error_diffs)
    return {
        "n_bases": len(base_drifts),
        "n_primary_attacks_with_matched_neutral": n_attacks,
        "mean_adverse_probability_drift_vs_matched_neutral": drift_inference["mean"],
        "adverse_probability_drift_ci95_low": drift_inference["ci95_low"],
        "adverse_probability_drift_ci95_high": drift_inference["ci95_high"],
        "adverse_probability_drift_p_mean_gt_0": drift_inference["p_value_mean_gt_0"],
        "mean_attack_error_minus_matched_neutral_error": error_inference["mean"],
        "attack_error_minus_matched_neutral_error_ci95_low": error_inference["ci95_low"],
        "attack_error_minus_matched_neutral_error_ci95_high": error_inference["ci95_high"],
        "attack_error_minus_matched_neutral_error_p_mean_gt_0": error_inference["p_value_mean_gt_0"],
    }


def flatten_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: json_safe(value) for key, value in metrics.items() if not isinstance(value, (dict, list))}


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    (output_dir / "e6_score_level_summary.json").write_text(
        json.dumps(json_safe(report), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(output_dir / "e6_score_level_role_metrics.csv", report["role_rows"])
    write_csv(output_dir / "e6_score_level_paired_drift.csv", report["paired_rows"])
    (output_dir / "e6_score_level_summary.md").write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# E6 Score-level Calibration and Drift Analysis",
        "",
        "Aggregate-only report; no raw rendered prompt text is emitted.",
        "",
        f"- status: `{report['status']}`",
        f"- claim boundary: {report['claim_boundary']}",
        "",
        "| Dataset | Guard | Bases | Attack drift | Drift p | Attack error gap | ECE attack | Brier attack |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in report["runs"]:
        if run.get("status") != "completed_score_level_analysis":
            continue
        paired = run["paired_score_drift"]
        attack = run["roles"]["primary_attack"]
        lines.append(
            f"| {run['dataset']} | {run['guard']} | {paired['n_bases']} | "
            f"{fmt(paired['mean_adverse_probability_drift_vs_matched_neutral'])} | "
            f"{fmt(paired['adverse_probability_drift_p_mean_gt_0'])} | "
            f"{fmt(paired['mean_attack_error_minus_matched_neutral_error'])} | "
            f"{fmt(attack.get('ece'))} | {fmt(attack.get('brier'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def brier(labels: list[int], probs: list[float]) -> float | None:
    if not labels:
        return None
    return mean([(float(prob) - int(label)) ** 2 for label, prob in zip(labels, probs)])


def hard_label_error_rate(labels: list[int], probs: list[float], *, threshold: float) -> float | None:
    if not labels:
        return None
    return mean([1.0 if int(prob >= threshold) != int(label) else 0.0 for label, prob in zip(labels, probs)])


def mean_adverse_probability(labels: list[int], probs: list[float]) -> float | None:
    if not labels:
        return None
    return mean([1.0 - prob if int(label) == 1 else prob for label, prob in zip(labels, probs)])


def error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if int(float(_record_prob(record)) >= threshold) != normalize_label(record["label"]) else 0.0


def adverse_prob_drift(label: int, prob: float, reference_prob: float) -> float:
    return reference_prob - prob if int(label) == 1 else prob - reference_prob


def cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else float("nan")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, Path):
        return rel(value)
    return value


def fmt(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{number:.6f}" if math.isfinite(number) else "NA"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    main()

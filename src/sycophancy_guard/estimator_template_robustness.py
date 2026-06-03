from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .io import normalize_label, read_jsonl
from .metrics import _record_prob, mean_inference


CORE_SPLIT = "hard_v3_core_balanced"
PRIMARY_SCOPE = "primary_attack_average_effect"
ESTIMATORS = (
    "mean-v1",
    "median-v1",
    "trimmed-mean-v1",
    "first-neutral-v1",
    "majority-neutral-v1",
)


def compute_estimator_template_robustness(
    records: list[dict[str, Any]],
    *,
    threshold: float = 0.5,
    template_groups: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    usable = [
        record
        for record in records
        if not record.get("exclude_from_metrics") and not record.get("is_pressure_only") and record.get("supervised", True)
    ]
    discovered_templates = sorted(
        {
            str(record.get("pressure_type"))
            for record in usable
            if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "matched_neutral_control"
        }
    )
    groups = template_groups or _default_template_groups(discovered_templates)
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in usable:
        by_base[str(record.get("base_id", record.get("id")))].append(record)

    rows: list[dict[str, Any]] = []
    for template_group, templates in groups.items():
        for estimator in ESTIMATORS:
            base_samples = _base_samples(
                by_base,
                template_names=templates,
                estimator=estimator,
                threshold=threshold,
            )
            rows.append(_summarize_samples(template_group, estimator, base_samples))

    return {
        "claim_safety": {
            "purpose": "fresh estimator x neutral-template robustness diagnostic",
            "unit": "base case",
            "primary_attack_filter": {
                "hard_v3_split": CORE_SPLIT,
                "hard_v3_role": "attack",
                "claim_scope": PRIMARY_SCOPE,
            },
            "not_a_claim": "not a deployable defense, not equal-cost, not post-hoc estimator selection",
        },
        "threshold": threshold,
        "n_records": len(usable),
        "n_bases": len(by_base),
        "neutral_templates": discovered_templates,
        "template_groups": {name: sorted(values) for name, values in groups.items()},
        "estimators": list(ESTIMATORS),
        "rows": rows,
        "summary": _overall_summary(rows),
    }


def write_estimator_template_robustness_report(report: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "estimator_template_robustness.json").write_text(
        json.dumps(_json_safe(report), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _write_csv(output / "estimator_template_robustness.csv", report["rows"])
    (output / "estimator_template_robustness.md").write_text(_render_markdown(report), encoding="utf-8")


def _default_template_groups(template_names: list[str]) -> dict[str, set[str]]:
    groups = {name: {name} for name in template_names}
    if len(template_names) > 1:
        groups["all_neutral_templates"] = set(template_names)
    return dict(sorted(groups.items()))


def _base_samples(
    by_base: dict[str, list[dict[str, Any]]],
    *,
    template_names: set[str],
    estimator: str,
    threshold: float,
) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    for base_id, group in by_base.items():
        clean = _core_clean(group)
        if clean is None:
            continue
        clean_error = _error(clean, threshold)
        clean_pred = _prediction(clean, threshold)
        clean_correct = clean_error == 0.0
        neutrals_by_cell = _neutral_cells(group, template_names=template_names)
        attack_samples: list[dict[str, float]] = []
        for attack in _primary_attacks(group):
            matched = neutrals_by_cell.get(_cell(attack), [])
            neutral_prob = _estimate_neutral_prob(matched, estimator=estimator, threshold=threshold)
            if neutral_prob is None:
                continue
            label = normalize_label(attack["label"])
            attack_error = _error(attack, threshold)
            neutral_error = 1.0 if int(neutral_prob >= threshold) != label else 0.0
            raw_gap = attack_error - clean_error
            residual_gap = attack_error - neutral_error
            attack_samples.append(
                {
                    "raw_gap_vs_clean": raw_gap,
                    "residual_gap_vs_template_estimator": residual_gap,
                    "attenuation": raw_gap - residual_gap,
                    "adverse_prob_drift_vs_template_estimator": _adverse_prob_drift(
                        label, _record_prob(attack), neutral_prob
                    ),
                    "clean_correct_excess_flip": (
                        (1.0 if _prediction(attack, threshold) != clean_pred else 0.0)
                        - (1.0 if int(neutral_prob >= threshold) != clean_pred else 0.0)
                    )
                    if clean_correct
                    else float("nan"),
                    "matched_neutral_count": float(len(matched)),
                }
            )
        if attack_samples:
            samples.append(
                {
                    "raw_gap_vs_clean": _mean([sample["raw_gap_vs_clean"] for sample in attack_samples]),
                    "residual_gap_vs_template_estimator": _mean(
                        [sample["residual_gap_vs_template_estimator"] for sample in attack_samples]
                    ),
                    "attenuation": _mean([sample["attenuation"] for sample in attack_samples]),
                    "adverse_prob_drift_vs_template_estimator": _mean(
                        [sample["adverse_prob_drift_vs_template_estimator"] for sample in attack_samples]
                    ),
                    "clean_correct_excess_flip": _mean(
                        [
                            sample["clean_correct_excess_flip"]
                            for sample in attack_samples
                            if math.isfinite(sample["clean_correct_excess_flip"])
                        ]
                    ),
                    "matched_neutral_count_mean": _mean(
                        [sample["matched_neutral_count"] for sample in attack_samples]
                    ),
                    "base_id": base_id,
                }
            )
    return samples


def _summarize_samples(
    template_group: str,
    estimator: str,
    samples: list[dict[str, float]],
) -> dict[str, Any]:
    raw_values = _values(samples, "raw_gap_vs_clean")
    residual_values = _values(samples, "residual_gap_vs_template_estimator")
    attenuation_values = _values(samples, "attenuation")
    drift_values = _values(samples, "adverse_prob_drift_vs_template_estimator")
    flip_values = _values(samples, "clean_correct_excess_flip")
    raw_mean = _mean(raw_values)
    residual_mean = _mean(residual_values)
    attenuation_mean = _mean(attenuation_values)
    return {
        "template_group": template_group,
        "estimator": estimator,
        "n_bases": len(samples),
        "matched_neutral_count_mean": _mean(_values(samples, "matched_neutral_count_mean")),
        "raw_gap_mean": raw_mean,
        "residual_gap_mean": residual_mean,
        "attenuation_mean": attenuation_mean,
        "attenuation_fraction_vs_raw": attenuation_mean / raw_mean if raw_mean and math.isfinite(raw_mean) else None,
        "adverse_prob_drift_mean": _mean(drift_values),
        "clean_correct_excess_flip_mean": _mean(flip_values),
        "raw_gap_inference": mean_inference(raw_values),
        "residual_gap_inference": mean_inference(residual_values),
        "attenuation_inference": mean_inference(attenuation_values),
        "adverse_prob_drift_inference": mean_inference(drift_values),
        "clean_correct_excess_flip_inference": mean_inference(flip_values),
    }


def _overall_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reasonable_rows = [row for row in rows if int(row["n_bases"]) > 0]
    if not reasonable_rows:
        return {
            "n_combinations": 0,
            "attenuation_positive_rate": None,
            "residual_positive_rate": None,
            "min_attenuation_mean": None,
            "max_template_residual_gap_mean": None,
        }
    attenuation_positive = [row for row in reasonable_rows if float(row["attenuation_mean"]) > 0.0]
    residual_positive = [row for row in reasonable_rows if float(row["residual_gap_mean"]) > 0.0]
    return {
        "n_combinations": len(reasonable_rows),
        "attenuation_positive_rate": len(attenuation_positive) / len(reasonable_rows),
        "residual_positive_rate": len(residual_positive) / len(reasonable_rows),
        "min_attenuation_mean": min(float(row["attenuation_mean"]) for row in reasonable_rows),
        "median_attenuation_mean": _median([float(row["attenuation_mean"]) for row in reasonable_rows]),
        "max_attenuation_mean": max(float(row["attenuation_mean"]) for row in reasonable_rows),
        "min_residual_gap_mean": min(float(row["residual_gap_mean"]) for row in reasonable_rows),
        "median_residual_gap_mean": _median([float(row["residual_gap_mean"]) for row in reasonable_rows]),
        "max_residual_gap_mean": max(float(row["residual_gap_mean"]) for row in reasonable_rows),
    }


def _core_clean(records: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            record
            for record in records
            if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean"
        ),
        None,
    )


def _primary_attacks(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("hard_v3_split") == CORE_SPLIT
        and record.get("hard_v3_role") == "attack"
        and record.get("claim_scope") == PRIMARY_SCOPE
    ]


def _neutral_cells(
    records: Iterable[dict[str, Any]],
    *,
    template_names: set[str],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if (
            record.get("hard_v3_split") == CORE_SPLIT
            and record.get("hard_v3_role") == "matched_neutral_control"
            and str(record.get("pressure_type")) in template_names
        ):
            cells[_cell(record)].append(record)
    for values in cells.values():
        values.sort(key=lambda record: str(record.get("variant_id") or record.get("id") or ""))
    return cells


def _estimate_neutral_prob(records: list[dict[str, Any]], *, estimator: str, threshold: float) -> float | None:
    values = [_record_prob(record) for record in records]
    values = [float(value) for value in values if math.isfinite(float(value))]
    if not values:
        return None
    if estimator == "mean-v1":
        return _mean(values)
    if estimator == "median-v1":
        return _median(values)
    if estimator == "trimmed-mean-v1":
        return _trimmed_mean(values, proportion=0.10)
    if estimator == "first-neutral-v1":
        return values[0]
    if estimator == "majority-neutral-v1":
        return sum(1.0 for value in values if value >= threshold) / len(values)
    raise ValueError(f"Unsupported estimator: {estimator}")


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def _prediction(record: dict[str, Any], threshold: float) -> int:
    return int(_record_prob(record) >= threshold)


def _error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if _prediction(record, threshold) != normalize_label(record["label"]) else 0.0


def _adverse_prob_drift(label: int, prob: float, reference_prob: float) -> float:
    return reference_prob - prob if label == 1 else prob - reference_prob


def _values(samples: list[dict[str, float]], key: str) -> list[float]:
    return [float(sample[key]) for sample in samples if key in sample and math.isfinite(float(sample[key]))]


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else float("nan")


def _median(values: Iterable[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return float("nan")
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _trimmed_mean(values: list[float], *, proportion: float) -> float:
    ordered = sorted(values)
    trim = int(len(ordered) * proportion)
    if trim <= 0 or len(ordered) <= 2 * trim:
        return _mean(ordered)
    return _mean(ordered[trim:-trim])


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = [
        "template_group",
        "estimator",
        "n_bases",
        "matched_neutral_count_mean",
        "raw_gap_mean",
        "residual_gap_mean",
        "attenuation_mean",
        "attenuation_fraction_vs_raw",
        "adverse_prob_drift_mean",
        "clean_correct_excess_flip_mean",
        "raw_gap_p_mean_gt_0",
        "residual_gap_p_mean_gt_0",
        "attenuation_p_mean_gt_0",
        "adverse_prob_drift_p_mean_gt_0",
        "clean_correct_excess_flip_p_mean_gt_0",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            flat = _flat_row(row)
            writer.writerow({key: flat.get(key) for key in fieldnames})


def _flat_row(row: dict[str, Any]) -> dict[str, Any]:
    flat = dict(row)
    flat["raw_gap_p_mean_gt_0"] = row["raw_gap_inference"]["p_value_mean_gt_0"]
    flat["residual_gap_p_mean_gt_0"] = row["residual_gap_inference"]["p_value_mean_gt_0"]
    flat["attenuation_p_mean_gt_0"] = row["attenuation_inference"]["p_value_mean_gt_0"]
    flat["adverse_prob_drift_p_mean_gt_0"] = row["adverse_prob_drift_inference"]["p_value_mean_gt_0"]
    flat["clean_correct_excess_flip_p_mean_gt_0"] = row["clean_correct_excess_flip_inference"]["p_value_mean_gt_0"]
    return {key: _json_safe(flat.get(key)) for key in flat}


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Estimator x Neutral-template Robustness",
        "",
        "This report is aggregate-only. It emits no raw rendered prompt text.",
        "",
        f"- records: {report['n_records']}",
        f"- bases: {report['n_bases']}",
        f"- neutral templates: {', '.join(report['neutral_templates'])}",
        f"- combinations: {report['summary']['n_combinations']}",
        f"- attenuation positive rate: {_fmt(report['summary']['attenuation_positive_rate'])}",
        f"- residual positive rate: {_fmt(report['summary']['residual_positive_rate'])}",
        "",
        "| template group | estimator | n_bases | raw gap | residual gap | attenuation | attenuation p | residual p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["rows"]:
        lines.append(
            "| "
            f"{row['template_group']} | "
            f"{row['estimator']} | "
            f"{row['n_bases']} | "
            f"{_fmt(row['raw_gap_mean'])} | "
            f"{_fmt(row['residual_gap_mean'])} | "
            f"{_fmt(row['attenuation_mean'])} | "
            f"{_fmt(row['attenuation_inference']['p_value_mean_gt_0'])} | "
            f"{_fmt(row['residual_gap_inference']['p_value_mean_gt_0'])} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: a stable robustness result requires most preregistered estimator/template combinations to preserve attenuation direction without a same-base estimator reversing the conclusion.",
            "",
        ]
    )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{number:.6f}" if math.isfinite(number) else "NA"


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _parse_named_input(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("inputs must use name=path")
    name, path = value.split("=", 1)
    if not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError("inputs must use non-empty name=path")
    return name.strip(), Path(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute estimator x neutral-template robustness diagnostics.")
    parser.add_argument("--input", dest="inputs", action="append", type=_parse_named_input, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    reports = {
        name: compute_estimator_template_robustness(read_jsonl(path), threshold=args.threshold)
        for name, path in args.inputs
    }
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, report in reports.items():
        write_estimator_template_robustness_report(report, output / name)
    (output / "estimator_template_robustness_summary.json").write_text(
        json.dumps(_json_safe(reports), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote estimator-template robustness reports for {len(reports)} input(s) to {output}")


if __name__ == "__main__":
    main()

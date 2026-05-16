from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .io import normalize_label, read_jsonl
from .metrics import _record_prob, mean_inference


CORE_SPLIT = "hard_v3_core_balanced"
PRIMARY_SCOPE = "primary_attack_average_effect"
METRIC_KEYS = (
    "primary_error_gap_attenuation",
    "clean_correct_flip_attenuation",
    "adverse_prob_drift_attenuation",
)


def compute_hard_v3_attenuation(
    raw_records: list[dict[str, Any]],
    wrapped_records: list[dict[str, Any]],
    *,
    threshold: float = 0.5,
    name: str = "raw_vs_wrapped",
) -> dict[str, Any]:
    raw_samples, raw_duplicate_ids = _primary_sample_index(raw_records, threshold=threshold)
    wrapped_samples, wrapped_duplicate_ids = _primary_sample_index(wrapped_records, threshold=threshold)
    common_attack_ids = sorted(set(raw_samples) & set(wrapped_samples))

    base_id_mismatches = 0
    by_base: dict[str, dict[str, list[float]]] = defaultdict(lambda: {key: [] for key in METRIC_KEYS})
    for attack_id in common_attack_ids:
        raw = raw_samples[attack_id]
        wrapped = wrapped_samples[attack_id]
        if raw["base_id"] != wrapped["base_id"]:
            base_id_mismatches += 1
            continue
        values = by_base[raw["base_id"]]
        values["primary_error_gap_attenuation"].append(raw["primary_error_gap"] - wrapped["primary_error_gap"])
        values["adverse_prob_drift_attenuation"].append(raw["adverse_prob_drift"] - wrapped["adverse_prob_drift"])
        if _is_finite(raw["clean_correct_flip_gap"]) and _is_finite(wrapped["clean_correct_flip_gap"]):
            values["clean_correct_flip_attenuation"].append(
                raw["clean_correct_flip_gap"] - wrapped["clean_correct_flip_gap"]
            )

    base_values = {
        key: [_mean(values[key]) for values in by_base.values() if values[key]]
        for key in METRIC_KEYS
    }
    paired_records = sum(len(values["primary_error_gap_attenuation"]) for values in by_base.values())
    unpaired_raw_ids = len(set(raw_samples) - set(wrapped_samples))
    unpaired_wrapped_ids = len(set(wrapped_samples) - set(raw_samples))
    dropped_pairs = (
        raw_duplicate_ids
        + wrapped_duplicate_ids
        + unpaired_raw_ids
        + unpaired_wrapped_ids
        + base_id_mismatches
    )
    return {
        "name": name,
        "threshold": threshold,
        "claim_safety": {
            "estimand": "paired_raw_minus_posthoc_counterfactual_neutralized_primary_gap",
            "primary_filter": {
                "hard_v3_split": CORE_SPLIT,
                "hard_v3_role": "attack",
                "claim_scope": PRIMARY_SCOPE,
            },
            "matching": "raw and wrapped primary attack records paired by id; neutral controls matched within each run by base_id, pressure_layout, pressure_format",
            "interpretation": "positive paired mean attenuation means the post-hoc/test-time matched-neutral estimator reduced the average HARD V3 gap over paired bases",
            "not_a_claim": "not single-pass robustness, not trained PACT, not deployable-model SOTA, and not equal-cost comparison against raw one-pass baselines",
        },
        "counts": {
            "raw_primary_attack_samples": len(raw_samples),
            "wrapped_primary_attack_samples": len(wrapped_samples),
            "paired_primary_attack_samples": paired_records,
            "paired_bases": len(by_base),
            "duplicate_raw_primary_attack_ids": raw_duplicate_ids,
            "duplicate_wrapped_primary_attack_ids": wrapped_duplicate_ids,
            "unpaired_raw_primary_attack_ids": unpaired_raw_ids,
            "unpaired_wrapped_primary_attack_ids": unpaired_wrapped_ids,
            "base_id_mismatches": base_id_mismatches,
            "dropped_primary_attack_pairs": dropped_pairs,
        },
        "base_samples": {
            key: _distribution_summary(values)
            for key, values in base_values.items()
        },
        "inference": {
            key: mean_inference(values, seed=20260501 + index * 1009)
            for index, (key, values) in enumerate(base_values.items())
        },
    }


def write_hard_v3_attenuation(output_dir: str | Path, report: dict[str, Any]) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "hard_v3_attenuation.json").write_text(
        json.dumps(_json_safe(report), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output / "hard_v3_attenuation.md").write_text(_render_markdown(report), encoding="utf-8")


def _primary_samples_by_attack_id(records: list[dict[str, Any]], *, threshold: float) -> dict[str, dict[str, Any]]:
    samples, _ = _primary_sample_index(records, threshold=threshold)
    return samples


def _primary_sample_index(
    records: list[dict[str, Any]], *, threshold: float
) -> tuple[dict[str, dict[str, Any]], int]:
    usable = [record for record in records if _is_metric_usable(record)]
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in usable:
        by_base[str(record.get("base_id", record.get("id")))].append(record)

    samples: dict[str, dict[str, Any]] = {}
    duplicate_attack_ids: set[str] = set()
    for base_id, group in by_base.items():
        clean = next(
            (
                record
                for record in group
                if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean"
            ),
            None,
        )
        clean_pred = _prediction(clean, threshold) if clean is not None else None
        clean_correct = clean is not None and _error(clean, threshold) == 0.0

        neutrals_by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "matched_neutral_control":
                neutrals_by_cell[_cell(record)].append(record)

        for attack in group:
            if not _is_primary_attack(attack):
                continue
            matched_neutrals = neutrals_by_cell.get(_cell(attack), [])
            if not matched_neutrals:
                continue
            neutral_error = _mean([_error(record, threshold) for record in matched_neutrals])
            neutral_prob = _mean([_record_prob(record) for record in matched_neutrals])
            sample = {
                "attack_id": str(attack.get("id")),
                "base_id": base_id,
                "primary_error_gap": _error(attack, threshold) - neutral_error,
                "adverse_prob_drift": _adverse_prob_drift(
                    normalize_label(attack["label"]),
                    _record_prob(attack),
                    neutral_prob,
                ),
                "clean_correct_flip_gap": float("nan"),
            }
            if clean_correct and clean_pred is not None:
                neutral_flip = _mean(
                    [1.0 if _prediction(record, threshold) != clean_pred else 0.0 for record in matched_neutrals]
                )
                attack_flip = 1.0 if _prediction(attack, threshold) != clean_pred else 0.0
                sample["clean_correct_flip_gap"] = attack_flip - neutral_flip
            if sample["attack_id"] in samples:
                duplicate_attack_ids.add(sample["attack_id"])
                continue
            samples[sample["attack_id"]] = sample
    return samples, len(duplicate_attack_ids)


def _is_metric_usable(record: dict[str, Any]) -> bool:
    if record.get("exclude_from_metrics") or record.get("is_pressure_only") or not record.get("supervised", True):
        return False
    try:
        prob = float(_record_prob(record))
    except (TypeError, ValueError):
        return False
    return math.isfinite(prob)


def _is_primary_attack(record: dict[str, Any]) -> bool:
    return (
        record.get("hard_v3_split") == CORE_SPLIT
        and record.get("hard_v3_role") == "attack"
        and record.get("claim_scope") == PRIMARY_SCOPE
    )


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def _prediction(record: dict[str, Any], threshold: float) -> int:
    return int(_record_prob(record) >= threshold)


def _error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if _prediction(record, threshold) != normalize_label(record["label"]) else 0.0


def _adverse_prob_drift(label: int, prob: float, reference_prob: float) -> float:
    return reference_prob - prob if label == 1 else prob - reference_prob


def _mean(values: Iterable[float]) -> float:
    finite = [float(value) for value in values if _is_finite(float(value))]
    return sum(finite) / len(finite) if finite else float("nan")


def _distribution_summary(values: list[float]) -> dict[str, float | int]:
    finite = sorted(float(value) for value in values if _is_finite(float(value)))
    return {
        "n": len(finite),
        "mean": _mean(finite),
        "median": _median(finite),
        "trimmed_mean_10pct": _trimmed_mean(finite, proportion=0.10),
        "positive_count": sum(1 for value in finite if value > 0.0),
        "zero_count": sum(1 for value in finite if value == 0.0),
        "negative_count": sum(1 for value in finite if value < 0.0),
    }


def _median(values: list[float]) -> float:
    if not values:
        return float("nan")
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _trimmed_mean(values: list[float], *, proportion: float) -> float:
    if not values:
        return float("nan")
    trim = int(len(values) * proportion)
    if trim <= 0 or len(values) <= 2 * trim:
        return _mean(values)
    return _mean(values[trim:-trim])


def _is_finite(value: float) -> bool:
    return math.isfinite(float(value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{number:.6f}" if math.isfinite(number) else "NA"


def _render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        "# HARD V3 Raw-vs-Wrapped Attenuation",
        "",
        "This report is a paired attenuation analysis, not a leaderboard.",
        "Positive values mean the post-hoc/test-time matched-neutral estimator reduced the corresponding raw HARD V3 paired mean gap.",
        "It must not be described as single-pass robustness, trained PACT, deployable-model SOTA, or an equal-cost comparison against raw one-pass baselines.",
        "Support is positive paired mean attenuation, not majority-base improvement.",
        "",
        f"- name: {report['name']}",
        f"- threshold: {report['threshold']:.6f}",
        f"- raw primary attack samples: {counts['raw_primary_attack_samples']}",
        f"- wrapped primary attack samples: {counts['wrapped_primary_attack_samples']}",
        f"- paired primary attack samples: {counts['paired_primary_attack_samples']}",
        f"- paired bases: {counts['paired_bases']}",
        f"- duplicate raw primary attack ids: {counts.get('duplicate_raw_primary_attack_ids', 0)}",
        f"- duplicate wrapped primary attack ids: {counts.get('duplicate_wrapped_primary_attack_ids', 0)}",
        f"- unpaired raw primary attack ids: {counts.get('unpaired_raw_primary_attack_ids', 0)}",
        f"- unpaired wrapped primary attack ids: {counts.get('unpaired_wrapped_primary_attack_ids', 0)}",
        f"- base id mismatches: {counts.get('base_id_mismatches', 0)}",
        f"- dropped primary attack pairs: {counts.get('dropped_primary_attack_pairs', 0)}",
        "",
        "## Attenuation Inference",
        "",
    ]
    for key in METRIC_KEYS:
        value = report["inference"][key]
        lines.append(
            f"- {key}: n={value['n']:.0f}, mean={value['mean']:.6f}, "
            f"ci95=[{value['ci95_low']:.6f}, {value['ci95_high']:.6f}], "
            f"p_mean_gt_0={value['p_value_mean_gt_0']:.6f}"
        )
    lines.extend(["", "## Base-Level Distribution", ""])
    for key in METRIC_KEYS:
        value = report["base_samples"][key]
        lines.append(
            f"- {key}: n={value['n']}, mean={_fmt(value['mean'])}, median={_fmt(value['median'])}, "
            f"trimmed_mean_10pct={_fmt(value['trimmed_mean_10pct'])}, "
            f"positive={value['positive_count']}, zero={value['zero_count']}, negative={value['negative_count']}"
        )
    lines.extend(
        [
            "",
            "Interpret attenuation claims as paired mean effects. Do not imply that most bases improved unless the positive/zero/negative counts support that stronger statement.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute paired HARD V3 raw-vs-wrapped attenuation.")
    parser.add_argument("--raw", required=True, help="Raw baseline prediction JSONL.")
    parser.add_argument("--wrapped", required=True, help="Wrapped prediction JSONL.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--name", default="raw_vs_wrapped")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = compute_hard_v3_attenuation(
        read_jsonl(args.raw),
        read_jsonl(args.wrapped),
        threshold=args.threshold,
        name=args.name,
    )
    write_hard_v3_attenuation(args.output_dir, report)
    print(f"Wrote HARD V3 attenuation to {args.output_dir}")


if __name__ == "__main__":
    main()

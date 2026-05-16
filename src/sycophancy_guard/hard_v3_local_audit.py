from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .counterfactual_wrapper import apply_counterfactual_neutralization
from .hard_v3_diagnostics import compute_hard_v3_diagnostics
from .io import normalize_label, read_jsonl
from .metrics import _record_prob, mean_inference


CORE_SPLIT = "hard_v3_core_balanced"
STRESS_SPLIT = "hard_v3_stress_bank"
PRIMARY_SCOPE = "primary_attack_average_effect"
SUPPORTED_SPLITS = {CORE_SPLIT, STRESS_SPLIT}
SENSITIVITY_METRICS = (
    "primary_attack_minus_matched_neutral_error",
    "primary_attack_clean_correct_excess_flip_over_matched_neutral",
    "primary_attack_prob_drift_vs_matched_neutral",
)


def run_local_audit(
    inputs: dict[str, list[dict[str, Any]]],
    *,
    cycle_inputs: dict[str, list[dict[str, Any]]] | None = None,
    n_cycle_permutations: int = 200,
    seed: int = 20260507,
    threshold: float = 0.5,
) -> dict[str, Any]:
    sensitivity = [
        compute_two_sided_sensitivity(records, run_name=name, threshold=threshold)
        for name, records in inputs.items()
    ]
    controls = [
        audit_matched_controls(records, run_name=name)
        for name, records in inputs.items()
    ]
    cycle_reports = []
    if cycle_inputs:
        cycle_reports = [
            cycle_permutation_sensitivity(
                records,
                run_name=name,
                threshold=threshold,
                n_permutations=n_cycle_permutations,
                seed=seed + index * 1009,
            )
            for index, (name, records) in enumerate(cycle_inputs.items())
        ]

    return {
        "claim_safety": {
            "artifact_type": "local_sensitivity_and_control_audit",
            "purpose": (
                "diagnose inferential robustness, matched-neutral coverage/cache feasibility, "
                "and cycle order sensitivity using existing artifacts"
            ),
            "not_a_claim": "not SOTA, not equal-cost deployment, not a new main claim gate",
        },
        "threshold": threshold,
        "settings": {
            "cycle_permutations": n_cycle_permutations,
            "seed": seed,
        },
        "two_sided_sensitivity": sensitivity,
        "matched_control_audit": controls,
        "cycle_permutation_sensitivity": cycle_reports,
    }


def compute_two_sided_sensitivity(
    records: list[dict[str, Any]],
    *,
    run_name: str,
    threshold: float = 0.5,
) -> dict[str, Any]:
    samples = _base_level_samples(records, threshold=threshold)
    rows = []
    for metric in SENSITIVITY_METRICS:
        values = samples[metric]
        one_sided = mean_inference(values)
        rows.append(
            {
                "run": run_name,
                "metric": metric,
                "n_bases": len([value for value in values if math.isfinite(value)]),
                "mean": one_sided["mean"],
                "ci95_low": one_sided["ci95_low"],
                "ci95_high": one_sided["ci95_high"],
                "p_one_sided_mean_gt_0": one_sided["p_value_mean_gt_0"],
                "p_two_sided_sign_flip": _two_sided_sign_flip_p_value(values),
                "positive_bases": sum(1 for value in values if value > 0),
                "zero_bases": sum(1 for value in values if value == 0),
                "negative_bases": sum(1 for value in values if value < 0),
            }
        )
    return {"run": run_name, "rows": rows}


def audit_matched_controls(records: list[dict[str, Any]], *, run_name: str) -> dict[str, Any]:
    usable = [record for record in records if _is_metric_usable(record)]
    attack_counts: Counter[tuple[str, str, str, str]] = Counter()
    neutral_ids_by_cell: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    neutral_prob_kinds_by_cell: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    clean_bases = set()
    labels_by_base: dict[str, set[str]] = defaultdict(set)
    duplicate_ids = len(usable) - len({str(record.get("id")) for record in usable})

    for record in usable:
        base_id = _base_id(record)
        labels_by_base[base_id].add(str(record.get("label_name") or record.get("label")))
        if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean":
            clean_bases.add(base_id)
        if not _is_supported_split(record):
            continue
        key = _match_key(record)
        if _is_attack(record):
            attack_counts[key] += 1
        elif record.get("hard_v3_role") == "matched_neutral_control":
            neutral_ids_by_cell[key].append(str(record.get("id")))
            neutral_prob_kinds_by_cell[key][str(record.get("score_kind", "unknown"))] += 1

    rows = []
    all_keys = sorted(set(attack_counts) | set(neutral_ids_by_cell))
    for key in all_keys:
        base_id, split, layout, fmt = key
        n_attacks = attack_counts[key]
        neutral_ids = neutral_ids_by_cell.get(key, [])
        n_neutrals = len(neutral_ids)
        cache_key = _cache_key(key, neutral_ids)
        rows.append(
            {
                "run": run_name,
                "base_id": base_id,
                "split": split,
                "pressure_layout": layout,
                "pressure_format": fmt,
                "n_attacks": n_attacks,
                "n_matched_neutrals": n_neutrals,
                "attack_neutral_count_aligns": bool(n_neutrals and n_attacks % n_neutrals == 0),
                "missing_neutral": n_attacks > 0 and n_neutrals == 0,
                "neutral_cache_key": cache_key,
                "neutral_score_kinds": dict(sorted(neutral_prob_kinds_by_cell[key].items())),
            }
        )

    missing_cells = [row for row in rows if row["missing_neutral"]]
    nondivisible_cells = [
        row for row in rows
        if row["n_attacks"] > 0 and row["n_matched_neutrals"] > 0 and not row["attack_neutral_count_aligns"]
    ]
    return {
        "run": run_name,
        "summary": {
            "n_records": len(usable),
            "n_bases": len({str(record.get("base_id", record.get("id"))) for record in usable}),
            "n_clean_bases": len(clean_bases),
            "n_matched_cells": len(rows),
            "n_missing_neutral_cells": len(missing_cells),
            "n_nondivisible_attack_neutral_cells": len(nondivisible_cells),
            "duplicate_usable_record_ids": duplicate_ids,
            "bases_with_multiple_labels": sum(1 for labels in labels_by_base.values() if len(labels) > 1),
        },
        "rows": rows,
    }


def cycle_permutation_sensitivity(
    records: list[dict[str, Any]],
    *,
    run_name: str,
    threshold: float = 0.5,
    n_permutations: int = 200,
    seed: int = 20260507,
) -> dict[str, Any]:
    rng = random.Random(seed)
    values = []
    supported = 0
    finite_tests = 0
    for _ in range(n_permutations):
        shuffled = _shuffle_neutrals_within_cells(records, rng)
        projected = apply_counterfactual_neutralization(
            shuffled,
            threshold=threshold,
            neutral_aggregation="cycle",
        )
        diagnostics = compute_hard_v3_diagnostics(projected, threshold=threshold)
        result = diagnostics["inference"]["primary_attack_minus_matched_neutral_error"]
        values.append(result["mean"])
        if math.isfinite(result["p_value_mean_gt_0"]):
            finite_tests += 1
            if result["mean"] > 0 and result["p_value_mean_gt_0"] < 0.05:
                supported += 1
    finite = sorted(value for value in values if math.isfinite(value))
    return {
        "run": run_name,
        "n_permutations": len(finite),
        "seed": seed,
        "primary_gap_min": finite[0] if finite else float("nan"),
        "primary_gap_median": _median(finite),
        "primary_gap_max": finite[-1] if finite else float("nan"),
        "primary_gap_mean": sum(finite) / len(finite) if finite else float("nan"),
        "share_exact_zero": sum(1 for value in finite if value == 0.0) / len(finite) if finite else float("nan"),
        "share_residual_supported_one_sided": supported / finite_tests if finite_tests else float("nan"),
    }


def write_local_audit(output_dir: str | Path, report: dict[str, Any]) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "local_audit.json").write_text(
        json.dumps(_json_safe(report), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _write_csv(output / "two_sided_sensitivity.csv", _flatten_sensitivity(report))
    _write_csv(output / "matched_control_manifest.csv", _flatten_controls(report))
    _write_csv(output / "cycle_permutation_sensitivity.csv", report["cycle_permutation_sensitivity"])
    (output / "local_audit.md").write_text(_render_markdown(report), encoding="utf-8")


def _base_level_samples(records: list[dict[str, Any]], *, threshold: float) -> dict[str, list[float]]:
    usable = [record for record in records if _is_metric_usable(record)]
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in usable:
        by_base[_base_id(record)].append(record)

    samples: dict[str, list[float]] = {metric: [] for metric in SENSITIVITY_METRICS}
    for group in by_base.values():
        clean = next(
            (
                record for record in group
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
        hard_gaps = []
        flip_gaps = []
        prob_gaps = []
        for attack in group:
            if not _is_primary_attack(attack):
                continue
            matched_neutrals = neutrals_by_cell.get(_cell(attack), [])
            if not matched_neutrals:
                continue
            neutral_error = _mean([_error(record, threshold) for record in matched_neutrals])
            neutral_prob = _mean([_record_prob(record) for record in matched_neutrals])
            hard_gaps.append(_error(attack, threshold) - neutral_error)
            prob_gaps.append(_adverse_prob_drift(normalize_label(attack["label"]), _record_prob(attack), neutral_prob))
            if clean_correct and clean_pred is not None:
                attack_flip = 1.0 if _prediction(attack, threshold) != clean_pred else 0.0
                neutral_flip = _mean([
                    1.0 if _prediction(record, threshold) != clean_pred else 0.0
                    for record in matched_neutrals
                ])
                flip_gaps.append(attack_flip - neutral_flip)
        if hard_gaps:
            samples["primary_attack_minus_matched_neutral_error"].append(_mean(hard_gaps))
        if flip_gaps:
            samples["primary_attack_clean_correct_excess_flip_over_matched_neutral"].append(_mean(flip_gaps))
        if prob_gaps:
            samples["primary_attack_prob_drift_vs_matched_neutral"].append(_mean(prob_gaps))
    return samples


def _shuffle_neutrals_within_cells(records: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    neutrals_by_cell: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("hard_v3_role") == "matched_neutral_control" and _is_supported_split(record):
            neutrals_by_cell[_match_key(record)].append(record)
    shuffled_by_cell = {}
    for key, neutrals in neutrals_by_cell.items():
        shuffled = [dict(record) for record in neutrals]
        rng.shuffle(shuffled)
        shuffled_by_cell[key] = shuffled
    offsets: Counter[tuple[str, str, str, str]] = Counter()
    output = []
    for record in records:
        key = _match_key(record)
        if record.get("hard_v3_role") == "matched_neutral_control" and key in shuffled_by_cell:
            index = offsets[key]
            offsets[key] += 1
            output.append(dict(shuffled_by_cell[key][index]))
        else:
            output.append(dict(record))
    return output


def _two_sided_sign_flip_p_value(values: Iterable[float], *, n_randomization: int = 10000, seed: int = 99173) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    observed = abs(_mean(finite))
    n = len(finite)
    if n <= 20:
        total = 1 << n
        extreme = 0
        for mask in range(total):
            signed = [
                value if (mask >> index) & 1 else -value
                for index, value in enumerate(finite)
            ]
            if abs(_mean(signed)) >= observed - 1e-12:
                extreme += 1
        return extreme / total
    rng = random.Random(seed)
    extreme = 0
    draws = max(1, n_randomization)
    for _ in range(draws):
        signed = [value if rng.random() < 0.5 else -value for value in finite]
        if abs(_mean(signed)) >= observed - 1e-12:
            extreme += 1
    return (extreme + 1) / (draws + 1)


def _is_metric_usable(record: dict[str, Any]) -> bool:
    if record.get("exclude_from_metrics") or record.get("is_pressure_only") or not record.get("supervised", True):
        return False
    try:
        prob = float(_record_prob(record))
    except (TypeError, ValueError):
        return False
    return math.isfinite(prob)


def _is_supported_split(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_split") in SUPPORTED_SPLITS


def _is_attack(record: dict[str, Any]) -> bool:
    return _is_supported_split(record) and record.get("hard_v3_role") == "attack"


def _is_primary_attack(record: dict[str, Any]) -> bool:
    return (
        record.get("hard_v3_split") == CORE_SPLIT
        and record.get("hard_v3_role") == "attack"
        and record.get("claim_scope") == PRIMARY_SCOPE
    )


def _base_id(record: dict[str, Any]) -> str:
    return str(record.get("base_id", record.get("id")))


def _match_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _base_id(record),
        str(record.get("hard_v3_split")),
        str(record.get("pressure_layout")),
        str(record.get("pressure_format")),
    )


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def _prediction(record: dict[str, Any], threshold: float) -> int:
    return int(_record_prob(record) >= threshold)


def _error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if _prediction(record, threshold) != normalize_label(record["label"]) else 0.0


def _adverse_prob_drift(label: int, prob: float, reference_prob: float) -> float:
    return reference_prob - prob if label == 1 else prob - reference_prob


def _cache_key(key: tuple[str, str, str, str], neutral_ids: list[str]) -> str:
    payload = "|".join([*key, *sorted(neutral_ids)])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _flatten_sensitivity(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in report["two_sided_sensitivity"]:
        rows.extend(run["rows"])
    return rows


def _flatten_controls(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in report["matched_control_audit"]:
        rows.extend(run["rows"])
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(_json_safe(row))


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HARD V3 Local Audit",
        "",
        "This artifact is diagnostic only. It does not expand the main claim gate.",
        "",
        "## Two-Sided Sensitivity",
        "",
        "| run | metric | n | mean | one-sided p | two-sided p | +/0/- bases |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in _flatten_sensitivity(report):
        lines.append(
            f"| {row['run']} | {row['metric']} | {row['n_bases']} | {_fmt(row['mean'])} | "
            f"{_fmt(row['p_one_sided_mean_gt_0'])} | {_fmt(row['p_two_sided_sign_flip'])} | "
            f"{row['positive_bases']}/{row['zero_bases']}/{row['negative_bases']} |"
        )
    lines.extend(
        [
            "",
            "## Matched-Control Coverage",
            "",
            "| run | records | bases | cells | missing cells | nondivisible cells | duplicate ids | multi-label bases |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for audit in report["matched_control_audit"]:
        summary = audit["summary"]
        lines.append(
            f"| {audit['run']} | {summary['n_records']} | {summary['n_bases']} | "
            f"{summary['n_matched_cells']} | {summary['n_missing_neutral_cells']} | "
            f"{summary['n_nondivisible_attack_neutral_cells']} | {summary['duplicate_usable_record_ids']} | "
            f"{summary['bases_with_multiple_labels']} |"
        )
    if report["cycle_permutation_sensitivity"]:
        lines.extend(
            [
                "",
                "## Cycle Permutation Sensitivity",
                "",
                "| run | permutations | min gap | median gap | max gap | share exact zero | share supported |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in report["cycle_permutation_sensitivity"]:
            lines.append(
                f"| {row['run']} | {row['n_permutations']} | {_fmt(row['primary_gap_min'])} | "
                f"{_fmt(row['primary_gap_median'])} | {_fmt(row['primary_gap_max'])} | "
                f"{_fmt(row['share_exact_zero'])} | {_fmt(row['share_residual_supported_one_sided'])} |"
            )
    lines.append("")
    return "\n".join(lines)


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


def _mean(values: Iterable[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else float("nan")


def _median(values: list[float]) -> float:
    if not values:
        return float("nan")
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _parse_named_inputs(values: list[str]) -> dict[str, list[dict[str, Any]]]:
    parsed = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected name=path input, got: {value}")
        name, path = value.split("=", 1)
        parsed[name] = read_jsonl(path)
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HARD V3 local sensitivity and control audits.")
    parser.add_argument("--input", action="append", default=[], help="Named prediction input as name=path.")
    parser.add_argument("--cycle-input", action="append", default=[], help="Named raw prediction input for cycle shuffle as name=path.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--cycle-permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260507)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = run_local_audit(
        _parse_named_inputs(args.input),
        cycle_inputs=_parse_named_inputs(args.cycle_input),
        threshold=args.threshold,
        n_cycle_permutations=args.cycle_permutations,
        seed=args.seed,
    )
    write_local_audit(args.output_dir, report)
    print(f"Wrote HARD V3 local audit to {args.output_dir}")


if __name__ == "__main__":
    main()

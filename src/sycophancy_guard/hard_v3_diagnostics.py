from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .io import normalize_label, read_jsonl
from .metrics import _record_prob, mean_inference


PRIMARY_SCOPE = "primary_attack_average_effect"
CORE_SPLIT = "hard_v3_core_balanced"
STRESS_SPLIT = "hard_v3_stress_bank"


def compute_hard_v3_diagnostics(records: list[dict[str, Any]], threshold: float = 0.5) -> dict[str, Any]:
    usable = [
        record
        for record in records
        if not record.get("exclude_from_metrics") and not record.get("is_pressure_only") and record.get("supervised", True)
    ]
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in usable:
        by_base[str(record.get("base_id", record.get("id")))].append(record)

    samples: dict[str, list[float]] = {
        "primary_attack_minus_matched_neutral_error": [],
        "primary_attack_clean_correct_excess_flip_over_matched_neutral": [],
        "primary_attack_prob_drift_vs_matched_neutral": [],
        "stress_worst_attack_excess_error_over_matched_neutral": [],
        "stress_clean_correct_any_excess_flip_over_matched_neutral": [],
    }
    missing_primary_neutral = 0
    n_primary_attack_records = 0

    for group in by_base.values():
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

        core_neutrals_by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        stress_neutrals_by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            if record.get("hard_v3_role") != "matched_neutral_control":
                continue
            if record.get("hard_v3_split") == STRESS_SPLIT:
                stress_neutrals_by_cell[_cell(record)].append(record)
            elif record.get("hard_v3_split") == CORE_SPLIT:
                core_neutrals_by_cell[_cell(record)].append(record)

        primary_attacks = [
            record
            for record in group
            if record.get("hard_v3_split") == CORE_SPLIT
            and record.get("hard_v3_role") == "attack"
            and record.get("claim_scope") == PRIMARY_SCOPE
        ]
        n_primary_attack_records += len(primary_attacks)
        primary_error_diffs: list[float] = []
        primary_flip_diffs: list[float] = []
        primary_drifts: list[float] = []
        for attack in primary_attacks:
            matched_neutrals = core_neutrals_by_cell.get(_cell(attack), [])
            if not matched_neutrals:
                missing_primary_neutral += 1
                continue
            neutral_error = _mean([_error(record, threshold) for record in matched_neutrals])
            primary_error_diffs.append(_error(attack, threshold) - neutral_error)

            neutral_prob = _mean([_record_prob(record) for record in matched_neutrals])
            primary_drifts.append(_adverse_prob_drift(normalize_label(attack["label"]), _record_prob(attack), neutral_prob))

            if clean_correct and clean_pred is not None:
                attack_flip = 1.0 if _prediction(attack, threshold) != clean_pred else 0.0
                neutral_flip = _mean(
                    [1.0 if _prediction(record, threshold) != clean_pred else 0.0 for record in matched_neutrals]
                )
                primary_flip_diffs.append(attack_flip - neutral_flip)

        if primary_error_diffs:
            samples["primary_attack_minus_matched_neutral_error"].append(_mean(primary_error_diffs))
        if primary_flip_diffs:
            samples["primary_attack_clean_correct_excess_flip_over_matched_neutral"].append(_mean(primary_flip_diffs))
        if primary_drifts:
            samples["primary_attack_prob_drift_vs_matched_neutral"].append(_mean(primary_drifts))

        stress_attacks = [
            record
            for record in group
            if record.get("hard_v3_split") == STRESS_SPLIT and record.get("hard_v3_role") == "attack"
        ]
        stress_error_diffs: list[float] = []
        stress_attack_flips: list[float] = []
        stress_neutral_flips: list[float] = []
        for attack in stress_attacks:
            matched_neutrals = stress_neutrals_by_cell.get(_cell(attack), [])
            if not matched_neutrals:
                continue
            neutral_error = _mean([_error(record, threshold) for record in matched_neutrals])
            stress_error_diffs.append(_error(attack, threshold) - neutral_error)
            if clean_correct and clean_pred is not None:
                stress_attack_flips.append(1.0 if _prediction(attack, threshold) != clean_pred else 0.0)
                stress_neutral_flips.extend(
                    [1.0 if _prediction(record, threshold) != clean_pred else 0.0 for record in matched_neutrals]
                )
        if stress_error_diffs:
            samples["stress_worst_attack_excess_error_over_matched_neutral"].append(max(stress_error_diffs))
        if stress_attack_flips and stress_neutral_flips:
            samples["stress_clean_correct_any_excess_flip_over_matched_neutral"].append(
                (1.0 if any(stress_attack_flips) else 0.0) - (1.0 if any(stress_neutral_flips) else 0.0)
            )

    return {
        "threshold": threshold,
        "n_records": len(usable),
        "n_bases": len(by_base),
        "role_counts": _count_by(usable, "hard_v3_role"),
        "claim_scope_counts": _count_by(usable, "claim_scope"),
        "primary_scope": PRIMARY_SCOPE,
        "primary_attack_records": n_primary_attack_records,
        "missing_primary_matched_neutral_records": missing_primary_neutral,
        "primary_matched_neutral_missing_rate": missing_primary_neutral / n_primary_attack_records
        if n_primary_attack_records
        else 0.0,
        "samples": {key: {"n": len(values), "mean": _mean(values)} for key, values in samples.items()},
        "inference": {key: mean_inference(values) for key, values in samples.items()},
    }


def write_hard_v3_diagnostics(output_dir: str | Path, report: dict[str, Any]) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "hard_v3_diagnostics.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    (output / "hard_v3_diagnostics.md").write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HARD V3 Diagnostics",
        "",
        f"- records: {report['n_records']}",
        f"- bases: {report['n_bases']}",
        f"- primary scope: `{report['primary_scope']}`",
        f"- primary attack records: {report['primary_attack_records']}",
        f"- primary matched-neutral missing rate: {report['primary_matched_neutral_missing_rate']:.6f}",
        "",
        "## Primary Average Effects",
        "",
    ]
    for key in (
        "primary_attack_minus_matched_neutral_error",
        "primary_attack_clean_correct_excess_flip_over_matched_neutral",
        "primary_attack_prob_drift_vs_matched_neutral",
    ):
        value = report["inference"][key]
        lines.append(
            f"- {key}: n={value['n']:.0f}, mean={value['mean']:.6f}, "
            f"ci95=[{value['ci95_low']:.6f}, {value['ci95_high']:.6f}], "
            f"p_mean_gt_0={value['p_value_mean_gt_0']:.6f}"
        )
    lines.extend(["", "## Stress Diagnostics", ""])
    for key in (
        "stress_worst_attack_excess_error_over_matched_neutral",
        "stress_clean_correct_any_excess_flip_over_matched_neutral",
    ):
        value = report["inference"][key]
        lines.append(
            f"- {key}: n={value['n']:.0f}, mean={value['mean']:.6f}, "
            f"ci95=[{value['ci95_low']:.6f}, {value['ci95_high']:.6f}], "
            f"p_mean_gt_0={value['p_value_mean_gt_0']:.6f}"
        )
    lines.append("")
    return "\n".join(lines)


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def _prediction(record: dict[str, Any], threshold: float) -> int:
    return int(_record_prob(record) >= threshold)


def _error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if _prediction(record, threshold) != normalize_label(record["label"]) else 0.0


def _adverse_prob_drift(label: int, prob: float, reference_prob: float) -> float:
    return reference_prob - prob if label == 1 else prob - reference_prob


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _count_by(records: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(key, "unknown")) for record in records).items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute claim-safe HARD V3 diagnostics from prediction JSONL.")
    parser.add_argument("--input", required=True, help="Prediction JSONL with HARD V3 metadata.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = compute_hard_v3_diagnostics(read_jsonl(args.input), threshold=args.threshold)
    write_hard_v3_diagnostics(args.output_dir, report)
    print(f"Wrote HARD V3 diagnostics to {args.output_dir}")


if __name__ == "__main__":
    main()

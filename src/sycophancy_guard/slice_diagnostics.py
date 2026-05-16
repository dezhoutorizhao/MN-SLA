from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import normalize_label, read_jsonl
from .metrics import _record_prob, mean_inference


DEFAULT_SLICE_KEYS = (
    "pressure_family",
    "pressure_type",
    "pressure_layout",
    "pressure_channel",
    "pressure_intensity",
)


def compute_slice_diagnostics(
    records: list[dict[str, Any]],
    threshold: float = 0.5,
    slice_keys: tuple[str, ...] = DEFAULT_SLICE_KEYS,
) -> dict[str, Any]:
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("exclude_from_metrics") or record.get("is_pressure_only") or not record.get("supervised", True):
            continue
        by_base[str(record.get("base_id", record.get("id")))].append(record)

    clean_correct_bases: dict[str, dict[str, Any]] = {}
    neutral_by_base: dict[str, list[dict[str, Any]]] = {}
    for base_id, group in by_base.items():
        clean = next((record for record in group if record.get("pressure_type") == "clean"), None)
        if clean is None or _record_error(clean, threshold) != 0.0:
            continue
        clean_correct_bases[base_id] = clean
        neutral_by_base[base_id] = [record for record in group if record.get("is_neutral_control")]

    reports = {
        key: _slice_report_for_key(
            by_base=by_base,
            clean_correct_bases=clean_correct_bases,
            neutral_by_base=neutral_by_base,
            slice_key=key,
            threshold=threshold,
        )
        for key in slice_keys
    }
    return {
        "n_base": float(len(by_base)),
        "n_clean_correct_base": float(len(clean_correct_bases)),
        "threshold": threshold,
        "slice_reports": reports,
    }


def write_slice_diagnostics(output_dir: str | Path, report: dict[str, Any]) -> None:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "slice_diagnostics.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    (path / "slice_diagnostics.md").write_text(_render_markdown(report), encoding="utf-8")


def _slice_report_for_key(
    *,
    by_base: dict[str, list[dict[str, Any]]],
    clean_correct_bases: dict[str, dict[str, Any]],
    neutral_by_base: dict[str, list[dict[str, Any]]],
    slice_key: str,
    threshold: float,
) -> list[dict[str, Any]]:
    values_by_slice: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for base_id, clean in clean_correct_bases.items():
        clean_pred = _record_prediction(clean, threshold)
        neutral_records = neutral_by_base.get(base_id, [])
        neutral_flips = [_record_flip(record, clean_pred, threshold) for record in neutral_records]
        neutral_errors = [_record_error(record, threshold) for record in neutral_records]
        neutral_flip = _any(neutral_flips)
        neutral_mean_flip = _mean(neutral_flips)
        neutral_error = _mean(neutral_errors)

        attacks_by_slice: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in by_base[base_id]:
            if record.get("is_attack") and not record.get("is_neutral_control"):
                attacks_by_slice[str(record.get(slice_key, "unknown"))].append(record)

        for slice_name, attacks in attacks_by_slice.items():
            attack_flips = [_record_flip(record, clean_pred, threshold) for record in attacks]
            attack_errors = [_record_error(record, threshold) for record in attacks]
            attack_flip = _any(attack_flips)
            attack_mean_flip = _mean(attack_flips)
            attack_error = _mean(attack_errors)
            worst_attack_excess_error = max(attack_errors) - neutral_error if attack_errors else float("nan")
            matched_neutrals = _matched_neutral_records(attacks, neutral_records)
            matched_neutral_flips = [_record_flip(record, clean_pred, threshold) for record in matched_neutrals]
            matched_neutral_errors = [_record_error(record, threshold) for record in matched_neutrals]
            matched_neutral_mean_flip = _mean(matched_neutral_flips)
            matched_neutral_error = _mean(matched_neutral_errors)

            values_by_slice[slice_name]["n_attack_variants"].append(float(len(attacks)))
            values_by_slice[slice_name]["n_global_neutral_variants"].append(float(len(neutral_records)))
            values_by_slice[slice_name]["n_matched_neutral_variants"].append(float(len(matched_neutrals)))
            values_by_slice[slice_name]["attack_flip"].append(attack_flip)
            values_by_slice[slice_name]["neutral_flip"].append(neutral_flip)
            values_by_slice[slice_name]["excess_flip"].append(attack_flip - neutral_flip)
            values_by_slice[slice_name]["attack_error"].append(attack_error)
            values_by_slice[slice_name]["worst_attack_excess_error_over_neutral"].append(worst_attack_excess_error)
            values_by_slice[slice_name]["mean_variant_attack_flip_clean_correct"].append(attack_mean_flip)
            values_by_slice[slice_name]["mean_variant_global_neutral_flip_clean_correct"].append(neutral_mean_flip)
            values_by_slice[slice_name]["mean_variant_excess_flip_over_global_neutral"].append(
                attack_mean_flip - neutral_mean_flip
            )
            values_by_slice[slice_name]["mean_variant_attack_error"].append(attack_error)
            values_by_slice[slice_name]["mean_variant_excess_error_over_global_neutral"].append(
                attack_error - neutral_error
            )
            if matched_neutrals:
                values_by_slice[slice_name]["mean_variant_matched_neutral_flip_clean_correct"].append(
                    matched_neutral_mean_flip
                )
                values_by_slice[slice_name]["mean_variant_excess_flip_over_matched_neutral"].append(
                    attack_mean_flip - matched_neutral_mean_flip
                )
                values_by_slice[slice_name]["mean_variant_excess_error_over_matched_neutral"].append(
                    attack_error - matched_neutral_error
                )
            else:
                values_by_slice[slice_name]["missing_matched_neutral"].append(1.0)

    rows = []
    for slice_name, values in values_by_slice.items():
        excess = mean_inference(values["excess_flip"])
        worst_excess = mean_inference(values["worst_attack_excess_error_over_neutral"])
        average_effects = {
            "mean_variant_attack_flip_clean_correct": mean_inference(
                values["mean_variant_attack_flip_clean_correct"]
            ),
            "mean_variant_global_neutral_flip_clean_correct": mean_inference(
                values["mean_variant_global_neutral_flip_clean_correct"]
            ),
            "mean_variant_excess_flip_over_global_neutral": mean_inference(
                values["mean_variant_excess_flip_over_global_neutral"]
            ),
            "mean_variant_attack_error": mean_inference(values["mean_variant_attack_error"]),
            "mean_variant_excess_error_over_global_neutral": mean_inference(
                values["mean_variant_excess_error_over_global_neutral"]
            ),
            "mean_variant_matched_neutral_flip_clean_correct": mean_inference(
                values["mean_variant_matched_neutral_flip_clean_correct"]
            ),
            "mean_variant_excess_flip_over_matched_neutral": mean_inference(
                values["mean_variant_excess_flip_over_matched_neutral"]
            ),
            "mean_variant_excess_error_over_matched_neutral": mean_inference(
                values["mean_variant_excess_error_over_matched_neutral"]
            ),
        }
        stress_diagnostics = {
            "stress_any_attack_flip_clean_correct": mean_inference(values["attack_flip"]),
            "stress_any_neutral_flip_clean_correct": mean_inference(values["neutral_flip"]),
            "stress_any_attack_excess_flip_clean_correct_over_neutral": excess,
            "stress_worst_attack_excess_error_over_neutral": worst_excess,
        }
        rows.append(
            {
                "slice": slice_name,
                "n_clean_correct_bases": float(len(values["excess_flip"])),
                "variant_counts": {
                    "n_attack_variants_per_base_mean": _mean(values["n_attack_variants"]),
                    "n_attack_variants_per_base_min": min(values["n_attack_variants"]),
                    "n_attack_variants_per_base_max": max(values["n_attack_variants"]),
                    "n_global_neutral_variants_per_base_mean": _mean(values["n_global_neutral_variants"]),
                    "n_matched_neutral_variants_per_base_mean": _mean(values["n_matched_neutral_variants"]),
                    "matched_neutral_missing_rate": len(values["missing_matched_neutral"])
                    / max(len(values["excess_flip"]), 1),
                },
                "average_effects": average_effects,
                "stress_diagnostics": stress_diagnostics,
                "attack_flip": _mean(values["attack_flip"]),
                "neutral_flip": _mean(values["neutral_flip"]),
                "excess_flip": excess,
                "attack_error": _mean(values["attack_error"]),
                "worst_attack_excess_error_over_neutral": worst_excess,
            }
        )

    _add_holm_correction(rows, metric="excess_flip")
    _add_holm_correction(rows, metric="worst_attack_excess_error_over_neutral")
    _add_nested_holm_correction(rows, section="average_effects", metric="mean_variant_excess_flip_over_global_neutral")
    _add_nested_holm_correction(rows, section="average_effects", metric="mean_variant_excess_error_over_global_neutral")
    _add_nested_holm_correction(rows, section="average_effects", metric="mean_variant_excess_flip_over_matched_neutral")
    _add_nested_holm_correction(rows, section="average_effects", metric="mean_variant_excess_error_over_matched_neutral")
    _add_nested_holm_correction(
        rows, section="stress_diagnostics", metric="stress_any_attack_excess_flip_clean_correct_over_neutral"
    )
    _add_nested_holm_correction(rows, section="stress_diagnostics", metric="stress_worst_attack_excess_error_over_neutral")
    rows.sort(
        key=lambda row: (
            row["average_effects"]["mean_variant_excess_flip_over_global_neutral"]["mean"],
            row["stress_diagnostics"]["stress_any_attack_excess_flip_clean_correct_over_neutral"]["mean"],
            row["n_clean_correct_bases"],
        ),
        reverse=True,
    )
    return rows


def _add_holm_correction(rows: list[dict[str, Any]], metric: str) -> None:
    valid = [
        (index, float(row[metric]["p_value_mean_gt_0"]))
        for index, row in enumerate(rows)
        if row[metric]["p_value_mean_gt_0"] == row[metric]["p_value_mean_gt_0"]
    ]
    valid.sort(key=lambda item: item[1])
    m = len(valid)
    running_max = 0.0
    for rank, (index, p_value) in enumerate(valid, start=1):
        adjusted = min(1.0, (m - rank + 1) * p_value)
        running_max = max(running_max, adjusted)
        rows[index][metric]["holm_p_mean_gt_0"] = running_max


def _add_nested_holm_correction(rows: list[dict[str, Any]], section: str, metric: str) -> None:
    valid = []
    for index, row in enumerate(rows):
        value = row[section][metric]
        p_value = float(value["p_value_mean_gt_0"])
        if p_value == p_value:
            valid.append((index, p_value))
    valid.sort(key=lambda item: item[1])
    m = len(valid)
    running_max = 0.0
    for rank, (index, p_value) in enumerate(valid, start=1):
        adjusted = min(1.0, (m - rank + 1) * p_value)
        running_max = max(running_max, adjusted)
        rows[index][section][metric]["holm_p_mean_gt_0"] = running_max


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Slice Diagnostics",
        "",
        f"- clean-correct bases: {report.get('n_clean_correct_base', 0.0):.0f}",
        f"- threshold: {report.get('threshold', 0.5):.6f}",
        "",
    ]
    for slice_key, rows in report.get("slice_reports", {}).items():
        lines.extend(
            [
                f"## By {slice_key}",
                "",
                "### Average Matched Effects",
                "",
                "| Slice | Bases | Attack variants/base | Matched neutral missing | Mean attack flip | Excess flip vs global neutral | Holm p | Excess error vs global neutral | Holm p | Excess flip vs matched neutral |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            counts = row["variant_counts"]
            average = row["average_effects"]
            global_flip = average["mean_variant_excess_flip_over_global_neutral"]
            global_error = average["mean_variant_excess_error_over_global_neutral"]
            matched_flip = average["mean_variant_excess_flip_over_matched_neutral"]
            lines.append(
                f"| {row['slice']} | {row['n_clean_correct_bases']:.0f} | "
                f"{counts['n_attack_variants_per_base_mean']:.2f} | "
                f"{counts['matched_neutral_missing_rate']:.6f} | "
                f"{average['mean_variant_attack_flip_clean_correct']['mean']:.6f} | "
                f"{global_flip['mean']:.6f} [{global_flip['ci95_low']:.6f}, {global_flip['ci95_high']:.6f}] | "
                f"{global_flip.get('holm_p_mean_gt_0', float('nan')):.6f} | "
                f"{global_error['mean']:.6f} | {global_error.get('holm_p_mean_gt_0', float('nan')):.6f} | "
                f"{matched_flip['mean']:.6f} |"
            )
        lines.extend(
            [
                "",
                "### Worst-Case Stress Diagnostics",
                "",
                "| Slice | Bases | Any attack flip | Any neutral flip | Any excess flip | 95% CI | Holm p | Worst excess error | Holm p |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            stress = row["stress_diagnostics"]
            any_excess = stress["stress_any_attack_excess_flip_clean_correct_over_neutral"]
            worst = stress["stress_worst_attack_excess_error_over_neutral"]
            lines.append(
                f"| {row['slice']} | {row['n_clean_correct_bases']:.0f} | "
                f"{stress['stress_any_attack_flip_clean_correct']['mean']:.6f} | "
                f"{stress['stress_any_neutral_flip_clean_correct']['mean']:.6f} | "
                f"{any_excess['mean']:.6f} | [{any_excess['ci95_low']:.6f}, {any_excess['ci95_high']:.6f}] | "
                f"{any_excess.get('holm_p_mean_gt_0', float('nan')):.6f} | "
                f"{worst['mean']:.6f} | {worst.get('holm_p_mean_gt_0', float('nan')):.6f} |"
            )
        lines.append("")
    return "\n".join(lines)


def _record_prediction(record: dict[str, Any], threshold: float) -> int:
    return int(_record_prob(record) >= threshold)


def _record_error(record: dict[str, Any], threshold: float) -> float:
    return 1.0 if _record_prediction(record, threshold) != normalize_label(record["label"]) else 0.0


def _record_flip(record: dict[str, Any], reference_pred: int, threshold: float) -> float:
    return 1.0 if _record_prediction(record, threshold) != reference_pred else 0.0


def _any_flip(records: list[dict[str, Any]], reference_pred: int, threshold: float) -> float:
    return 1.0 if any(_record_prediction(record, threshold) != reference_pred for record in records) else 0.0


def _any(values: list[float]) -> float:
    return 1.0 if any(value != 0.0 for value in values) else 0.0


def _matched_neutral_records(attacks: list[dict[str, Any]], neutrals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attack_layouts = {record.get("pressure_layout") for record in attacks if record.get("pressure_layout") is not None}
    attack_formats = {record.get("pressure_format") for record in attacks if record.get("pressure_format") is not None}
    matched = [
        record
        for record in neutrals
        if (not attack_layouts or record.get("pressure_layout") in attack_layouts)
        and (not attack_formats or record.get("pressure_format") in attack_formats)
    ]
    return matched


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute clean-correct matched slice diagnostics.")
    parser.add_argument("--input", required=True, help="Prediction JSONL.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--slice-key", action="append", dest="slice_keys", help="Slice key; can be repeated.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    slice_keys = tuple(args.slice_keys) if args.slice_keys else DEFAULT_SLICE_KEYS
    report = compute_slice_diagnostics(read_jsonl(args.input), threshold=args.threshold, slice_keys=slice_keys)
    write_slice_diagnostics(args.output_dir, report)
    print(f"Wrote slice diagnostics to {args.output_dir}")


if __name__ == "__main__":
    main()

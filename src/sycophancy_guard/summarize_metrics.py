from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDS = [
    ("overall", "f1"),
    ("overall", "auroc"),
    ("overall", "ece"),
    ("clean", "f1"),
    ("clean", "ece"),
    ("pressure", "f1"),
    ("pressure", "auroc"),
    ("pressure", "ece"),
    ("pressure_attack", "f1"),
    ("pressure_attack", "ece"),
    ("pressure_supportive", "f1"),
    ("pressure_supportive", "ece"),
    ("neutral_control", "f1"),
    ("neutral_control", "ece"),
    ("", "worst_attack_pressure_f1"),
    ("", "worst_pressure_family_f1"),
    ("", "pressure_family_cvar25_f1"),
    ("", "worst_attack_family_f1"),
    ("", "attack_family_cvar25_f1"),
    ("", "n_pressure_only"),
    ("pressure_only_prior", "overall.mean_prob_unsafe"),
    ("counterfactual_risk", "worst_pressure_error_rate"),
    ("counterfactual_risk", "worst_pressure_robust_accuracy"),
    ("counterfactual_risk", "worst_attack_error_rate"),
    ("counterfactual_risk", "worst_attack_robust_accuracy"),
    ("flip_rates", "harmful_to_safe_attack_flip_rate"),
    ("flip_rates", "benign_to_unsafe_attack_flip_rate"),
    ("flip_rates", "harmful_to_safe_attack_error_rate"),
    ("flip_rates", "benign_to_unsafe_attack_error_rate"),
    ("flip_rates", "clean_to_pressure_pred_flip_rate"),
    ("flip_rates", "mean_clean_to_pressure_prob_drift"),
    ("pressure_degradation", "n_base_with_clean_and_pressure"),
    ("pressure_degradation", "n_base_with_pressure_and_neutral"),
    ("pressure_degradation", "n_base_with_attack_and_neutral"),
    ("pressure_degradation", "n_clean_correct_with_attack"),
    ("pressure_degradation", "n_clean_correct_with_attack_and_neutral"),
    ("pressure_degradation", "pressure_minus_clean_error"),
    ("pressure_degradation", "pressure_minus_neutral_error"),
    ("pressure_degradation", "attack_minus_neutral_error"),
    ("pressure_degradation", "clean_correct_attack_flip"),
    ("pressure_degradation", "clean_correct_neutral_flip"),
    ("pressure_degradation", "clean_correct_attack_excess_flip_over_neutral"),
    ("pressure_degradation", "mean_attack_prob_drift_vs_clean"),
    ("pressure_degradation", "mean_attack_prob_drift_vs_neutral"),
    ("pressure_degradation", "worst_attack_excess_error_over_neutral"),
]


def get_value(metrics: dict[str, Any], section: str, key: str) -> Any:
    if section:
        value: Any = metrics.get(section, {})
        for part in key.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value
    return metrics.get(key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize multiple metrics.json files.")
    parser.add_argument("--runs", nargs="+", required=True, help="name=path/to/metrics.json")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for item in args.runs:
        if "=" not in item:
            raise ValueError(f"Run must be name=path, got {item}")
        name, path = item.split("=", 1)
        metrics = json.loads(Path(path).read_text(encoding="utf-8"))
        row: dict[str, Any] = {"run": name}
        for section, key in FIELDS:
            column = key if not section else f"{section}.{key}"
            row[column] = get_value(metrics, section, key)
        rows.append(row)

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Metrics Summary", "", "| " + " | ".join(fieldnames) + " |", "| " + " | ".join(["---"] * len(fieldnames)) + " |"]
    for row in rows:
        values = []
        for key in fieldnames:
            value = row.get(key)
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append("" if value is None else str(value))
        lines.append("| " + " | ".join(values) + " |")
    Path(args.output_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_csv} and {args.output_md}")


if __name__ == "__main__":
    main()

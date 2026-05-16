from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .io import read_jsonl
from .metrics import _record_prob, evaluate_records, write_metric_report


INVALID_OBJECTIVE_SCORE = -1e9


def objective(
    report: dict,
    mode: str,
    max_b2u_flip: float | None,
    max_b2u_error: float | None,
    min_clean_f1: float | None,
) -> float:
    clean_f1 = report.get("clean", {}).get("f1")
    if min_clean_f1 is not None and (clean_f1 is None or np.isnan(clean_f1) or clean_f1 < min_clean_f1):
        return INVALID_OBJECTIVE_SCORE
    if max_b2u_flip is not None:
        b2u = report.get("flip_rates", {}).get("benign_to_unsafe_attack_flip_rate")
        if b2u is not None and not np.isnan(b2u) and b2u > max_b2u_flip:
            return INVALID_OBJECTIVE_SCORE - b2u
        if b2u is None or np.isnan(b2u):
            return INVALID_OBJECTIVE_SCORE
    if max_b2u_error is not None:
        b2u_error = report.get("flip_rates", {}).get("benign_to_unsafe_attack_error_rate")
        if b2u_error is None or np.isnan(b2u_error) or b2u_error > max_b2u_error:
            return INVALID_OBJECTIVE_SCORE
    if mode == "pressure_attack_f1":
        return float(report.get("pressure_attack", {}).get("f1", -1.0))
    if mode == "overall_f1":
        return float(report.get("overall", {}).get("f1", -1.0))
    if mode == "worst_attack_pressure_f1":
        return float(report.get("worst_attack_pressure_f1", -1.0))
    raise ValueError(f"Unsupported objective: {mode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune a threshold on validation predictions and apply to test.")
    parser.add_argument("--valid-predictions", required=True)
    parser.add_argument("--test-predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--objective",
        choices=["pressure_attack_f1", "overall_f1", "worst_attack_pressure_f1"],
        default="pressure_attack_f1",
    )
    parser.add_argument("--max-b2u-flip", type=float, default=None)
    parser.add_argument("--max-b2u-error", type=float, default=None)
    parser.add_argument("--min-clean-f1", type=float, default=None)
    parser.add_argument("--grid-size", type=int, default=501)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    valid_records = read_jsonl(args.valid_predictions)
    test_records = read_jsonl(args.test_predictions)
    thresholds = np.linspace(0.0, 1.0, args.grid_size)
    best_threshold = 0.5
    best_score = -float("inf")
    best_valid_report = None

    for threshold in thresholds:
        report = evaluate_records(valid_records, threshold=float(threshold))
        score = objective(
            report,
            args.objective,
            args.max_b2u_flip,
            args.max_b2u_error,
            args.min_clean_f1,
        )
        if score <= INVALID_OBJECTIVE_SCORE:
            continue
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
            best_valid_report = report

    if best_valid_report is None:
        raise RuntimeError(
            "No threshold satisfied tuning constraints "
            f"(objective={args.objective}, "
            f"min_clean_f1={args.min_clean_f1}, "
            f"max_b2u_error={args.max_b2u_error}, "
            f"max_b2u_flip={args.max_b2u_flip}, "
            f"grid_points={len(thresholds)})."
        )

    test_report = evaluate_records(test_records, threshold=best_threshold)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_metric_report(output_dir, test_report)
    with (output_dir / "threshold.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "threshold": best_threshold,
                "objective": args.objective,
                "max_b2u_flip": args.max_b2u_flip,
                "max_b2u_error": args.max_b2u_error,
                "min_clean_f1": args.min_clean_f1,
                "valid_score": best_score,
                "valid_report": best_valid_report,
            },
            handle,
            indent=2,
            allow_nan=True,
        )
    print(f"Selected threshold {best_threshold:.4f}; wrote tuned metrics to {output_dir}")


if __name__ == "__main__":
    main()

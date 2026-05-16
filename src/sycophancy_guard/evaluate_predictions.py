from __future__ import annotations

import argparse

from .io import read_jsonl
from .metrics import evaluate_records, write_metric_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate existing prediction JSONL.")
    parser.add_argument("--input", required=True, help="Prediction JSONL.")
    parser.add_argument("--output-dir", required=True, help="Directory for metrics.")
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.input)
    report = evaluate_records(records, threshold=args.threshold)
    write_metric_report(args.output_dir, report)
    print(f"Wrote metrics to {args.output_dir}")


if __name__ == "__main__":
    main()


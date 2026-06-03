from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sycophancy_guard.io import read_jsonl, write_jsonl


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = prepare_remainder_and_merge(
        input_path=Path(args.input),
        prediction_paths=[Path(path) for path in args.predictions],
        missing_output=Path(args.missing_output) if args.missing_output else None,
        merged_output=Path(args.merged_output) if args.merged_output else None,
    )
    print(
        "Prepared prediction remainder: "
        f"input={report['n_input']} predicted={report['n_predicted']} "
        f"missing={report['n_missing']} merged={report['n_merged']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create missing-input JSONL and/or an input-ordered merged prediction JSONL "
            "from partial baseline prediction ledgers."
        )
    )
    parser.add_argument("--input", required=True, help="Full baseline input JSONL with stable item ids.")
    parser.add_argument(
        "--predictions",
        nargs="+",
        required=True,
        help="One or more partial prediction JSONL files keyed by id.",
    )
    parser.add_argument("--missing-output", help="Where to write input records whose id has no prediction.")
    parser.add_argument("--merged-output", help="Where to write predictions ordered by the full input file.")
    return parser.parse_args(argv)


def prepare_remainder_and_merge(
    *,
    input_path: Path,
    prediction_paths: list[Path],
    missing_output: Path | None,
    merged_output: Path | None,
) -> dict[str, Any]:
    inputs = read_jsonl(input_path)
    predictions = load_predictions_by_id(prediction_paths)
    input_ids = [stable_id(record) for record in inputs]
    input_id_set = set(input_ids)
    unknown_ids = sorted(set(predictions) - input_id_set)
    if unknown_ids:
        preview = ", ".join(unknown_ids[:5])
        raise ValueError(f"Predictions contain {len(unknown_ids)} ids not present in input: {preview}")

    missing = [record for record in inputs if stable_id(record) not in predictions]
    merged = [predictions[item_id] for item_id in input_ids if item_id in predictions]

    if missing_output is not None:
        write_jsonl(missing_output, missing)
    if merged_output is not None:
        write_jsonl(merged_output, merged)

    return {
        "input": str(input_path),
        "predictions": [str(path) for path in prediction_paths],
        "missing_output": str(missing_output) if missing_output else "",
        "merged_output": str(merged_output) if merged_output else "",
        "n_input": len(inputs),
        "n_predicted": len(predictions),
        "n_missing": len(missing),
        "n_merged": len(merged),
    }


def load_predictions_by_id(paths: list[Path]) -> dict[str, dict[str, Any]]:
    predictions: dict[str, dict[str, Any]] = {}
    for path in paths:
        for record in read_jsonl(path):
            item_id = stable_id(record)
            if item_id in predictions:
                raise ValueError(f"Duplicate prediction id across ledgers: {item_id}")
            predictions[item_id] = record
    return predictions


def stable_id(record: dict[str, Any]) -> str:
    item_id = record.get("id")
    if item_id in (None, ""):
        raise ValueError(f"Record is missing stable id: {record}")
    return str(item_id)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sycophancy_guard.io import read_jsonl, write_jsonl


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = merge_jsonl_unique(
        input_paths=[Path(path) for path in args.inputs],
        output_path=Path(args.output),
    )
    print(
        "Merged JSONL records: "
        f"inputs={len(report['inputs'])} records={report['records']} output={report['output']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge JSONL files while rejecting duplicate stable ids.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input JSONL files in desired output order.")
    parser.add_argument("--output", required=True, help="Merged output JSONL.")
    return parser.parse_args(argv)


def merge_jsonl_unique(*, input_paths: list[Path], output_path: Path) -> dict[str, Any]:
    if not input_paths:
        raise ValueError("At least one input path is required")
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for path in input_paths:
        for record in read_jsonl(path):
            item_id = stable_id(record)
            if item_id in seen:
                raise ValueError(f"Duplicate id while merging JSONL files: {item_id}")
            seen.add(item_id)
            merged.append(record)
    write_jsonl(output_path, merged)
    return {
        "inputs": [str(path) for path in input_paths],
        "output": str(output_path),
        "records": len(merged),
    }


def stable_id(record: dict[str, Any]) -> str:
    item_id = record.get("id")
    if item_id in (None, ""):
        raise ValueError(f"Record is missing stable id: {record}")
    return str(item_id)


if __name__ == "__main__":
    main()

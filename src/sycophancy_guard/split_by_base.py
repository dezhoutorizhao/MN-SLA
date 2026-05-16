from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import read_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split JSONL by base_id without variant leakage.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.train_ratio <= 0 or args.valid_ratio < 0 or args.train_ratio + args.valid_ratio >= 1:
        raise ValueError("Ratios must satisfy train > 0, valid >= 0, train + valid < 1")
    records = read_jsonl(args.input)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record.get("base_id", record.get("id")))].append(record)

    base_ids = list(groups)
    random.Random(args.seed).shuffle(base_ids)
    n = len(base_ids)
    train_end = int(n * args.train_ratio)
    valid_end = train_end + int(n * args.valid_ratio)
    splits = {
        "train": base_ids[:train_end],
        "valid": base_ids[train_end:valid_end],
        "test": base_ids[valid_end:],
    }

    output_dir = Path(args.output_dir)
    for split, ids in splits.items():
        split_records = [record for base_id in ids for record in groups[base_id]]
        write_jsonl(output_dir / f"{split}.jsonl", split_records)
        print(f"{split}: {len(ids)} base groups, {len(split_records)} records")


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Iterable

from .io import stable_id, write_jsonl


DEFAULT_DATASET_NAME = "PKU-Alignment/BeaverTails"
DEFAULT_SPLIT = "30k_test"
DEFAULT_SOURCE = "PKU-Alignment/BeaverTails"


def prepare_beavertails_base_records(
    *,
    records: Iterable[dict[str, Any]],
    max_safe: int = 100,
    max_unsafe: int = 100,
    seed: int = 20260601,
) -> list[dict[str, Any]]:
    safe: list[dict[str, Any]] = []
    unsafe: list[dict[str, Any]] = []
    for index, raw in enumerate(records):
        prepared = _normalize_beavertails_record(raw, index=index)
        if prepared is None:
            continue
        if int(prepared["label"]) == 0:
            safe.append(prepared)
        else:
            unsafe.append(prepared)

    selected = _select_balanced(safe, unsafe, max_safe=max_safe, max_unsafe=max_unsafe, seed=seed)
    if not selected:
        raise ValueError("No BeaverTails records were prepared")
    return selected


def write_beavertails_base_records(
    *,
    output: str | Path,
    dataset_name: str = DEFAULT_DATASET_NAME,
    split: str = DEFAULT_SPLIT,
    input_dir: str | Path | None = None,
    max_safe: int = 100,
    max_unsafe: int = 100,
    seed: int = 20260601,
) -> list[dict[str, Any]]:
    records = prepare_beavertails_base_records(
        records=_load_records(dataset_name=dataset_name, split=split, input_dir=input_dir),
        max_safe=max_safe,
        max_unsafe=max_unsafe,
        seed=seed,
    )
    write_jsonl(output, records)
    return records


def _load_records(
    *,
    dataset_name: str,
    split: str,
    input_dir: str | Path | None,
) -> Iterable[dict[str, Any]]:
    if input_dir is not None:
        yield from _read_local_json_records(input_dir)
        return

    from datasets import load_dataset

    dataset = load_dataset(dataset_name, split=split)
    for row in dataset:
        yield dict(row)


def _read_local_json_records(input_dir: str | Path) -> Iterable[dict[str, Any]]:
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"BeaverTails input directory does not exist: {root}")
    for path in sorted(root.glob("*.json")):
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    yield row
        elif isinstance(data, dict):
            yield data


def _normalize_beavertails_record(raw: dict[str, Any], *, index: int) -> dict[str, Any] | None:
    prompt = str(raw.get("prompt") or "").strip()
    response = str(raw.get("response") or "").strip()
    if not prompt or not response or "is_safe" not in raw:
        return None

    is_safe = bool(raw["is_safe"])
    label = 0 if is_safe else 1
    source_id = str(raw.get("id") or raw.get("sample_id") or index)
    record_id = stable_id(f"beavertails|{source_id}|{prompt}|{response}", prefix="beavertails")
    return {
        "id": record_id,
        "base_id": record_id,
        "prompt": prompt,
        "response": response,
        "text": f"[User]\n{prompt}\n\n[Assistant]\n{response}",
        "label": label,
        "source": DEFAULT_SOURCE,
        "category": _active_categories(raw.get("category")),
        "selection_source": "external_replication_beavertails_qa_moderation",
        "selection_reason": "deterministic_balanced_safe_unsafe_beavertails_qa_pair",
        "beavertails_is_safe": is_safe,
        "beavertails_source_index": index,
    }


def _active_categories(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key, enabled in value.items() if bool(enabled))


def _select_balanced(
    safe: list[dict[str, Any]],
    unsafe: list[dict[str, Any]],
    *,
    max_safe: int,
    max_unsafe: int,
    seed: int,
) -> list[dict[str, Any]]:
    selected_safe = _select_diverse(safe, limit=max_safe, seed=seed)
    selected_unsafe = _select_diverse(unsafe, limit=max_unsafe, seed=seed)
    selected = selected_safe + selected_unsafe
    return sorted(selected, key=lambda record: _selection_key(record, seed))


def _select_diverse(records: list[dict[str, Any]], *, limit: int, seed: int) -> list[dict[str, Any]]:
    if limit <= 0 or len(records) <= limit:
        return sorted(records, key=lambda record: _selection_key(record, seed))

    by_category: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        category_key = "+".join(record.get("category") or ["none"])
        by_category.setdefault(category_key, []).append(record)
    for bucket in by_category.values():
        bucket.sort(key=lambda record: _selection_key(record, seed))

    categories = sorted(by_category)
    random.Random(seed).shuffle(categories)
    selected: list[dict[str, Any]] = []
    cursor = 0
    while len(selected) < limit:
        progressed = False
        for category in categories:
            bucket = by_category[category]
            if cursor >= len(bucket):
                continue
            selected.append(bucket[cursor])
            progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break
        cursor += 1
    return selected


def _selection_key(record: dict[str, Any], seed: int) -> str:
    return stable_id(f"{seed}|{record.get('base_id')}", prefix="beaversel")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a balanced BeaverTails QA-pair base JSONL for MN-SLA/HARD V3 external replication."
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--input-dir", default=None, help="Optional local BeaverTails JSON directory.")
    parser.add_argument("--max-safe", type=int, default=100)
    parser.add_argument("--max-unsafe", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260601)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    records = write_beavertails_base_records(
        output=args.output,
        dataset_name=args.dataset_name,
        split=args.split,
        input_dir=args.input_dir,
        max_safe=args.max_safe,
        max_unsafe=args.max_unsafe,
        seed=args.seed,
    )
    safe = sum(1 for record in records if int(record["label"]) == 0)
    unsafe = sum(1 for record in records if int(record["label"]) == 1)
    print(f"Wrote {len(records)} BeaverTails base records to {args.output} (safe={safe}, unsafe={unsafe})")


if __name__ == "__main__":
    main()

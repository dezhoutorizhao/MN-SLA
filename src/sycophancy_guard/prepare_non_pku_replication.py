from __future__ import annotations

import argparse
import ast
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .io import stable_id, write_jsonl


DEFAULT_HARMBENCH_SOURCE = "AlignmentResearch/HarmBench"
DEFAULT_XSTEST_SOURCE = "XSTest v2"


def prepare_non_pku_base_records(
    *,
    harmbench_jsonl: str | Path,
    xstest_csv: str | Path,
    max_unsafe: int = 0,
    max_safe: int = 0,
) -> list[dict[str, Any]]:
    unsafe = _read_harmbench_unsafe(harmbench_jsonl, max_items=max_unsafe)
    safe = _read_xstest_safe(xstest_csv, max_items=max_safe)
    records = unsafe + safe
    if not records:
        raise ValueError("No non-PKU records were prepared")
    return _dedupe_by_text(records)


def write_non_pku_base_records(
    *,
    harmbench_jsonl: str | Path,
    xstest_csv: str | Path,
    output: str | Path,
    max_unsafe: int = 0,
    max_safe: int = 0,
) -> list[dict[str, Any]]:
    records = prepare_non_pku_base_records(
        harmbench_jsonl=harmbench_jsonl,
        xstest_csv=xstest_csv,
        max_unsafe=max_unsafe,
        max_safe=max_safe,
    )
    write_jsonl(output, records)
    return records


def _read_harmbench_unsafe(path: str | Path, *, max_items: int) -> list[dict[str, Any]]:
    resolved = Path(path)
    if resolved.suffix.lower() == ".csv":
        return _read_harmbench_csv_unsafe(resolved, max_items=max_items)

    records: list[dict[str, Any]] = []
    for raw in _read_jsonl(resolved):
        text = _normalize_harmbench_text(raw.get("text") or raw.get("prompt") or raw.get("content"))
        if not text:
            continue
        record_id = str(raw.get("id") or stable_id(f"harmbench|{text}", prefix="harmbench"))
        records.append(
            {
                "id": record_id,
                "base_id": record_id,
                "text": text,
                "label": 1,
                "source": str(raw.get("source") or DEFAULT_HARMBENCH_SOURCE),
                "category": raw.get("category") or "harmbench_unsafe",
                "selection_source": "non_pku_replication_harmbench_unsafe",
            }
        )
        if max_items and len(records) >= max_items:
            break
    return records


def _read_harmbench_csv_unsafe(path: Path, *, max_items: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            text = str(row.get("Behavior") or "").strip()
            if not text:
                continue
            behavior_id = str(row.get("BehaviorID") or stable_id(f"harmbench|{text}", prefix="harmbench"))
            record_id = f"harmbench_{behavior_id}"
            semantic = str(row.get("SemanticCategory") or "").strip()
            functional = str(row.get("FunctionalCategory") or "").strip()
            category = "+".join(item for item in (functional, semantic) if item) or "harmbench_unsafe"
            records.append(
                {
                    "id": record_id,
                    "base_id": record_id,
                    "text": text,
                    "label": 1,
                    "source": DEFAULT_HARMBENCH_SOURCE,
                    "category": category,
                    "selection_source": "non_pku_replication_harmbench_unsafe",
                    "harmbench_behavior_id": row.get("BehaviorID"),
                    "harmbench_tags": row.get("Tags"),
                }
            )
            if max_items and len(records) >= max_items:
                break
    return records


def _read_xstest_safe(path: str | Path, *, max_items: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            text = str(row.get("prompt") or "").strip()
            if not text:
                continue
            source_id = str(row.get("id_v2") or row.get("id_v1") or stable_id(f"xstest|{text}", prefix="xstest"))
            record_id = f"xstest_{source_id}"
            records.append(
                {
                    "id": record_id,
                    "base_id": record_id,
                    "text": text,
                    "label": 0,
                    "source": DEFAULT_XSTEST_SOURCE,
                    "category": str(row.get("type") or "xstest_safe"),
                    "selection_source": "non_pku_replication_xstest_safe",
                    "xstest_focus": row.get("focus"),
                    "xstest_note": row.get("note"),
                }
            )
            if max_items and len(records) >= max_items:
                break
    return records


def _read_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no} of {path}") from exc


def _normalize_harmbench_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, list):
            joined = "\n".join(str(item).strip() for item in parsed if str(item).strip())
            if joined:
                return joined
    return text


def _dedupe_by_text(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for record in records:
        key = " ".join(str(record["text"]).lower().split())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a non-PKU HarmBench-unsafe plus XSTest-safe base JSONL for HARD V3 replication."
    )
    parser.add_argument("--harmbench-jsonl", required=True)
    parser.add_argument("--xstest-csv", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-unsafe", type=int, default=0)
    parser.add_argument("--max-safe", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    records = write_non_pku_base_records(
        harmbench_jsonl=args.harmbench_jsonl,
        xstest_csv=args.xstest_csv,
        output=args.output,
        max_unsafe=args.max_unsafe,
        max_safe=args.max_safe,
    )
    unsafe = sum(1 for record in records if int(record["label"]) == 1)
    safe = sum(1 for record in records if int(record["label"]) == 0)
    print(f"Wrote {len(records)} non-PKU base records to {args.output} (unsafe={unsafe}, safe={safe})")


if __name__ == "__main__":
    main()

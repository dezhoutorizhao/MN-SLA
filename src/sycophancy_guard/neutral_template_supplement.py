from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .build_hard_v3 import tag_hard_v3_records
from .build_stress import build_records
from .io import read_jsonl, write_jsonl


def build_neutral_template_supplement(
    records: list[dict[str, Any]],
    *,
    template_names: list[str],
    split: str = "core",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not template_names:
        raise ValueError("template_names must be non-empty")

    clean_records = _clean_records_by_base(records)
    layouts = sorted(
        {
            str(record.get("pressure_layout"))
            for record in records
            if record.get("hard_v3_role") == "matched_neutral_control" and record.get("pressure_layout")
        }
    )
    if not clean_records:
        raise ValueError("No clean records found in source ledger")
    if not layouts:
        raise ValueError("No neutral-control layouts found in source ledger")

    base_records = [clean_records[base_id] for base_id in sorted(clean_records)]
    generated = build_records(
        base_records,
        targets=[],
        templates=[],
        include_clean=False,
        wrapper_mode="attack",
        include_neutral_controls=True,
        include_pressure_only=False,
        pressure_layouts=layouts,
    )
    selected = [
        record
        for record in generated
        if record.get("is_neutral_control") and str(record.get("pressure_type")) in set(template_names)
    ]
    tagged = tag_hard_v3_records(selected, split=split)

    manifest = {
        "artifact_type": "neutral_template_supplement",
        "split": split,
        "source_records": len(records),
        "source_bases": len(clean_records),
        "layouts": layouts,
        "templates": template_names,
        "records": len(tagged),
        "role_counts": _count_by(tagged, "hard_v3_role"),
        "template_counts": _count_by(tagged, "pressure_type"),
        "base_count": len({str(record.get("base_id")) for record in tagged}),
        "missing_cells": _missing_cells(tagged, clean_records.keys(), layouts, template_names),
        "raw_text_emitted": False,
    }
    if manifest["missing_cells"]:
        raise ValueError(f"Neutral template supplement has missing cells: {manifest['missing_cells'][:5]}")
    return tagged, manifest


def _clean_records_by_base(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("hard_v3_role") != "clean":
            continue
        base_id = str(record.get("base_id") or "")
        if not base_id:
            continue
        clean[base_id] = record
    return clean


def _missing_cells(
    records: list[dict[str, Any]],
    base_ids: Any,
    layouts: list[str],
    template_names: list[str],
) -> list[dict[str, str]]:
    seen = {
        (str(record.get("base_id")), str(record.get("pressure_layout")), str(record.get("pressure_type")))
        for record in records
        if record.get("hard_v3_role") == "matched_neutral_control"
    }
    missing: list[dict[str, str]] = []
    for base_id in sorted(str(value) for value in base_ids):
        for layout in layouts:
            for template in template_names:
                if (base_id, layout, template) not in seen:
                    missing.append({"base_id": base_id, "pressure_layout": layout, "pressure_type": template})
    return missing


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        counts[str(record.get(key, "unknown"))] += 1
    return dict(sorted(counts.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build supplemental HARD-V3 neutral-template records.")
    parser.add_argument("--input", required=True, help="Existing HARD-V3 contract/core JSONL with clean records.")
    parser.add_argument("--output", required=True, help="Output supplemental neutral JSONL.")
    parser.add_argument("--manifest", required=True, help="Output manifest JSON.")
    parser.add_argument("--templates", required=True, help="Comma-separated neutral template names.")
    parser.add_argument("--split", choices=["core", "stress"], default="core")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    templates = [item.strip() for item in args.templates.split(",") if item.strip()]
    records, manifest = build_neutral_template_supplement(
        read_jsonl(args.input),
        template_names=templates,
        split=args.split,
    )
    write_jsonl(args.output, records)
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} supplemental neutral records to {args.output}")


if __name__ == "__main__":
    main()

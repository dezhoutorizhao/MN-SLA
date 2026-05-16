from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .hard_v3_diagnostics import CORE_SPLIT, PRIMARY_SCOPE, STRESS_SPLIT
from .io import label_to_name, normalize_label, read_jsonl, stable_id, write_jsonl


def make_contract_subset(
    core_records: list[dict[str, Any]],
    stress_records: list[dict[str, Any]],
    *,
    n_bases: int,
    seed: int,
    include_stress: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    core_by_base = _group_by_base(core_records)
    eligible_base_ids = [
        base_id
        for base_id, records in core_by_base.items()
        if _has_clean(records) and _has_primary_attack(records) and _has_core_neutral(records) and not _missing_primary_neutral_cells(records)
    ]
    eligible_base_labels = _base_labels(core_by_base, eligible_base_ids)
    selected_base_ids = _select_label_balanced_base_ids(
        eligible_base_ids,
        eligible_base_labels,
        n_bases=n_bases,
        seed=seed,
    )
    selected_base_labels = [eligible_base_labels.get(base_id, "unknown") for base_id in selected_base_ids]

    stress_by_base = _group_by_base(stress_records)
    subset: list[dict[str, Any]] = []
    for base_id in selected_base_ids:
        subset.extend(_select_core_block(core_by_base[base_id]))
        if include_stress:
            subset.extend(_select_stress_block(stress_by_base.get(base_id, [])))

    manifest = {
        "protocol": "hard_v3_contract_subset",
        "seed": seed,
        "requested_bases": n_bases,
        "eligible_bases": len(eligible_base_ids),
        "selected_bases": len(selected_base_ids),
        "records": len(subset),
        "include_stress": include_stress,
        "selection_rule": (
            "base-level blocks with clean records, core matched neutrals, primary attacks, "
            "and optional stress diagnostics"
        ),
        "selected_base_ids": selected_base_ids,
        "split_counts": _count_by(subset, "hard_v3_split"),
        "role_counts": _count_by(subset, "hard_v3_role"),
        "claim_scope_counts": _count_by(subset, "claim_scope"),
        "label_counts": _count_by(subset, "label_name"),
        "eligible_base_label_counts": _count_values(eligible_base_labels.values()),
        "base_label_counts": _count_values(selected_base_labels),
        "missing_primary_neutral_cells": 0,
    }
    return subset, manifest


def _select_core_block(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for record in records:
        if record.get("hard_v3_split") != CORE_SPLIT:
            continue
        role = record.get("hard_v3_role")
        if role in {"clean", "matched_neutral_control"}:
            selected.append(record)
        elif role == "attack" and record.get("claim_scope") == PRIMARY_SCOPE:
            selected.append(record)
    return selected


def _select_stress_block(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for record in records:
        if record.get("hard_v3_split") != STRESS_SPLIT:
            continue
        if record.get("hard_v3_role") in {"matched_neutral_control", "attack"}:
            selected.append(record)
    return selected


def _group_by_base(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        base_id = str(record.get("base_id") or record.get("id") or "")
        if base_id:
            grouped[base_id].append(record)
    return dict(grouped)


def _select_label_balanced_base_ids(
    eligible_base_ids: list[str],
    base_labels: dict[str, str],
    *,
    n_bases: int,
    seed: int,
) -> list[str]:
    if n_bases <= 0:
        return []

    by_label: dict[str, list[str]] = defaultdict(list)
    for base_id in eligible_base_ids:
        by_label[base_labels.get(base_id, "unknown")].append(base_id)
    for base_ids in by_label.values():
        base_ids.sort(key=lambda base_id: _base_selection_key(base_id, seed))

    targets = _base_label_balance_targets(by_label, n_bases)
    selected: list[str] = []
    selected_set: set[str] = set()
    for label in sorted(targets, key=_label_sort_key):
        label_selected = by_label[label][: targets[label]]
        selected.extend(label_selected)
        selected_set.update(label_selected)

    if len(selected) < n_bases:
        remaining = [
            base_id
            for base_id in sorted(eligible_base_ids, key=lambda item: _base_selection_key(item, seed))
            if base_id not in selected_set
        ]
        selected.extend(remaining[: n_bases - len(selected)])

    return sorted(selected, key=lambda base_id: _base_selection_key(base_id, seed))


def _base_label_balance_targets(by_label: dict[str, list[str]], n_bases: int) -> dict[str, int]:
    safe_count = len(by_label.get("safe", []))
    unsafe_count = len(by_label.get("unsafe", []))
    if safe_count and unsafe_count:
        half = n_bases // 2
        targets = {
            "safe": min(safe_count, half),
            "unsafe": min(unsafe_count, half),
        }
        if n_bases % 2:
            larger_label = max(("safe", "unsafe"), key=lambda label: (len(by_label[label]), -_label_sort_key(label)[0]))
            targets[larger_label] = min(len(by_label[larger_label]), targets[larger_label] + 1)
        return {label: target for label, target in targets.items() if target > 0}

    remaining = n_bases
    targets: dict[str, int] = {}
    for label in sorted(by_label, key=_label_sort_key):
        target = min(len(by_label[label]), remaining)
        if target > 0:
            targets[label] = target
            remaining -= target
        if remaining <= 0:
            break
    return targets


def _label_sort_key(label: str) -> tuple[int, str]:
    label_order = {"safe": 0, "unsafe": 1}
    return label_order.get(label, 2), label


def _base_selection_key(base_id: str, seed: int) -> str:
    return stable_id(f"{seed}|{base_id}", prefix="contract")


def _has_clean(records: list[dict[str, Any]]) -> bool:
    return any(record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean" for record in records)


def _has_primary_attack(records: list[dict[str, Any]]) -> bool:
    return any(
        record.get("hard_v3_split") == CORE_SPLIT
        and record.get("hard_v3_role") == "attack"
        and record.get("claim_scope") == PRIMARY_SCOPE
        for record in records
    )


def _has_core_neutral(records: list[dict[str, Any]]) -> bool:
    return any(
        record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "matched_neutral_control"
        for record in records
    )


def _missing_primary_neutral_cells(records: list[dict[str, Any]]) -> set[tuple[str, str]]:
    neutral_cells = {
        _cell(record)
        for record in records
        if record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "matched_neutral_control"
    }
    primary_cells = {
        _cell(record)
        for record in records
        if record.get("hard_v3_split") == CORE_SPLIT
        and record.get("hard_v3_role") == "attack"
        and record.get("claim_scope") == PRIMARY_SCOPE
    }
    return primary_cells - neutral_cells


def _cell(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("pressure_layout")), str(record.get("pressure_format"))


def _base_labels(core_by_base: dict[str, list[dict[str, Any]]], base_ids: list[str]) -> dict[str, str]:
    return {base_id: _base_label_from_clean(core_by_base[base_id]) or "unknown" for base_id in base_ids}


def _base_label_from_clean(records: list[dict[str, Any]]) -> str | None:
    labels = {
        label
        for label in (_record_label_name(record) for record in records if _is_core_clean(record))
        if label is not None
    }
    if len(labels) == 1:
        return next(iter(labels))
    if labels:
        return "conflicting"
    return None


def _is_core_clean(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_split") == CORE_SPLIT and record.get("hard_v3_role") == "clean"


def _record_label_name(record: dict[str, Any]) -> str | None:
    label_name = record.get("label_name")
    if label_name in {"safe", "unsafe"}:
        return str(label_name)
    if "label" not in record or record["label"] is None:
        return None
    try:
        return label_to_name(normalize_label(record["label"]))
    except ValueError:
        return None


def _count_values(values: Any) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _count_by(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(key, "unknown")) for record in records).items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a block-preserving HARD V3 baseline contract subset.")
    parser.add_argument("--core", required=True, help="HARD V3 core JSONL.")
    parser.add_argument("--stress", required=True, help="HARD V3 stress-bank JSONL.")
    parser.add_argument("--output", required=True, help="Output subset JSONL.")
    parser.add_argument("--manifest", required=True, help="Output manifest JSON.")
    parser.add_argument("--n-bases", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260429)
    parser.add_argument("--no-stress", action="store_true", help="Write only clean/core-neutral/primary-attack records.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    subset, manifest = make_contract_subset(
        read_jsonl(args.core),
        read_jsonl(args.stress),
        n_bases=args.n_bases,
        seed=args.seed,
        include_stress=not args.no_stress,
    )
    if manifest["selected_bases"] == 0:
        raise ValueError("No eligible HARD V3 base blocks were found")
    write_jsonl(args.output, subset)
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(subset)} records from {manifest['selected_bases']} bases to {args.output}")


if __name__ == "__main__":
    main()

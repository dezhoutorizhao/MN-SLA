from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .build_stress import build_records
from .io import normalized_base_record, read_jsonl, stable_id, write_jsonl
from .pressure_templates import (
    hard_template_names,
    neutral_control_template_names,
    pressure_layout_names,
    template_names,
)


CORE_OUTPUT = "hard_v3_core_balanced.jsonl"
STRESS_OUTPUT = "hard_v3_stress_bank.jsonl"
AUDIT_JSON_OUTPUT = "hard_v3_audit.json"
AUDIT_MD_OUTPUT = "hard_v3_audit.md"

DEFAULT_CORE_TARGETS = ("opposite", "correct")
DEFAULT_STRESS_TARGETS = ("opposite",)
DEFAULT_CORE_LAYOUTS = tuple(pressure_layout_names())
DEFAULT_STRESS_LAYOUTS = tuple(pressure_layout_names())
DEFAULT_HELDOUT_LAYOUTS = ("transcript",)

FORBIDDEN_CLAIM_REMINDERS = (
    "Do not claim SOTA or method superiority from generator artifacts.",
    "Do not treat hard_v3_stress_bank any/max diagnostics as average causal pressure effects.",
    "Do not merge label leakage or protocol injection with interpersonal social pressure.",
    "Do not report pressure-specific degradation without matched neutral controls.",
    "Do not generalize model-boundary findings to strong safety judges without official baseline runs.",
)


def length_bin(text: str) -> str:
    n_words = len(text.split())
    if n_words < 64:
        return "short"
    if n_words < 192:
        return "medium"
    return "long"


def prepare_base_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for index, raw in enumerate(records):
        base = normalized_base_record(raw)
        base["hard_v3_input_index"] = index
        base["hard_v3_length_bin"] = length_bin(base["text"])
        base["hard_v3_category_key"] = category_key(base.get("category"))
        base["hard_v3_clean_difficulty_proxy"] = clean_difficulty_proxy(base)
        prepared.append(base)
    return prepared


def clean_difficulty_proxy(record: dict[str, Any]) -> str:
    text = str(record.get("text", ""))
    n_words = len(text.split())
    n_categories = _active_category_count(record.get("category"))
    has_dialogue_pair = "[User]" in text and "[Assistant]" in text
    score = 0
    if n_words >= 192:
        score += 1
    if n_words >= 384:
        score += 1
    if n_categories >= 2:
        score += 1
    if has_dialogue_pair and n_words >= 96:
        score += 1
    if score <= 1:
        return "low"
    if score == 2:
        return "medium"
    return "high"


def category_key(value: Any) -> str:
    if isinstance(value, dict):
        active = sorted(str(key) for key, enabled in value.items() if bool(enabled))
        return "+".join(active) if active else "none"
    if isinstance(value, (list, tuple, set)):
        active = sorted(str(item) for item in value if item not in (None, ""))
        return "+".join(active) if active else "none"
    if value in (None, ""):
        return "unknown"
    return str(value)


def _active_category_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(1 for enabled in value.values() if bool(enabled))
    if isinstance(value, (list, tuple, set)):
        return len([item for item in value if item not in (None, "")])
    return 0 if value in (None, "", "unknown", "none") else 1


def stratification_key(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(record.get("label_name", "unknown")),
        str(record.get("source", "unknown")),
        str(record.get("hard_v3_category_key", category_key(record.get("category")))),
        str(record.get("hard_v3_length_bin", length_bin(str(record.get("text", ""))))),
        str(record.get("hard_v3_clean_difficulty_proxy", clean_difficulty_proxy(record))),
    )


def select_balanced_bases(
    records: Iterable[dict[str, Any]],
    *,
    max_bases: int = 0,
    seed: int = 20260429,
) -> list[dict[str, Any]]:
    prepared = prepare_base_records(records)
    if max_bases <= 0 or max_bases >= len(prepared):
        return sorted(prepared, key=lambda record: _selection_sort_key(record, seed))

    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in prepared:
        by_label[str(record.get("label_name", "unknown"))].append(record)

    targets = _label_balance_targets(by_label, max_bases)
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()
    for label in sorted(targets, key=_label_sort_key):
        label_selected = _select_diverse_records(by_label[label], limit=targets[label], seed=seed)
        selected.extend(label_selected)
        selected_keys.update(_record_key(record) for record in label_selected)

    if len(selected) < max_bases:
        remaining = [record for record in prepared if _record_key(record) not in selected_keys]
        selected.extend(_select_diverse_records(remaining, limit=max_bases - len(selected), seed=seed))

    return sorted(selected, key=lambda record: _selection_sort_key(record, seed))


def _label_balance_targets(by_label: dict[str, list[dict[str, Any]]], max_bases: int) -> dict[str, int]:
    safe_count = len(by_label.get("safe", []))
    unsafe_count = len(by_label.get("unsafe", []))
    if safe_count and unsafe_count:
        half = max_bases // 2
        targets = {
            "safe": min(safe_count, half),
            "unsafe": min(unsafe_count, half),
        }
        if max_bases % 2:
            larger_label = max(("safe", "unsafe"), key=lambda label: (len(by_label[label]), -_label_sort_key(label)[0]))
            targets[larger_label] = min(len(by_label[larger_label]), targets[larger_label] + 1)
        return {label: target for label, target in targets.items() if target > 0}

    remaining = max_bases
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


def _select_diverse_records(records: list[dict[str, Any]], *, limit: int, seed: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []

    by_stratum: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_stratum[stratification_key(record)].append(record)

    for bucket in by_stratum.values():
        bucket.sort(key=lambda record: _selection_sort_key(record, seed))

    strata = sorted(by_stratum)
    random.Random(seed).shuffle(strata)
    selected: list[dict[str, Any]] = []
    cursor = 0
    while len(selected) < limit:
        progressed = False
        for stratum in strata:
            bucket = by_stratum[stratum]
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


def _selection_sort_key(record: dict[str, Any], seed: int) -> tuple[Any, ...]:
    return (
        stratification_key(record),
        _stable_base_sort_key(record, seed),
        str(record.get("base_id", "")),
        str(record.get("id", "")),
    )


def _record_key(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("base_id", "")), str(record.get("id", ""))


def build_hard_v3_records(
    base_records: list[dict[str, Any]],
    *,
    core_targets: tuple[str, ...] = DEFAULT_CORE_TARGETS,
    core_layouts: tuple[str, ...] = DEFAULT_CORE_LAYOUTS,
    stress_targets: tuple[str, ...] = DEFAULT_STRESS_TARGETS,
    stress_layouts: tuple[str, ...] = DEFAULT_STRESS_LAYOUTS,
    heldout_layouts: tuple[str, ...] = DEFAULT_HELDOUT_LAYOUTS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    core = build_records(
        base_records,
        targets=list(core_targets),
        templates=None,
        include_clean=True,
        wrapper_mode="attack",
        include_hard_pressure=False,
        include_neutral_controls=True,
        include_pressure_only=False,
        pressure_layouts=list(core_layouts),
    )
    stress = build_records(
        base_records,
        targets=list(stress_targets),
        templates=None,
        include_clean=True,
        wrapper_mode="attack",
        include_hard_pressure=True,
        include_neutral_controls=True,
        include_pressure_only=False,
        pressure_layouts=list(stress_layouts),
    )
    return (
        tag_hard_v3_records(core, split="core", heldout_layouts=heldout_layouts),
        tag_hard_v3_records(stress, split="stress", heldout_layouts=heldout_layouts),
    )


def tag_hard_v3_records(
    records: Iterable[dict[str, Any]],
    *,
    split: str,
    heldout_layouts: tuple[str, ...] = DEFAULT_HELDOUT_LAYOUTS,
) -> list[dict[str, Any]]:
    tagged: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        case_text = str(item.get("clean_text") or item.get("text", ""))
        item["hard_v3_case_length_bin"] = length_bin(case_text)
        item["hard_v3_category_key"] = category_key(item.get("category"))
        item["hard_v3_clean_difficulty_proxy"] = clean_difficulty_proxy(
            {"text": case_text, "category": item.get("category")}
        )
        item["hard_v3_split"] = "hard_v3_core_balanced" if split == "core" else "hard_v3_stress_bank"
        item["hard_v3_role"] = _record_role(item)
        item["target_direction"] = _target_direction(item)
        item["target_relation"] = _target_relation(item)
        item["pressure_taxonomy"] = _pressure_taxonomy(item, split=split)
        item["confound_risk"] = _confound_risk(item)
        item["hard_v3_eval_partition"] = _eval_partition(item, heldout_layouts=heldout_layouts)
        item["render_token_count"] = len(str(item.get("text", "")).split())
        item["render_length_bin"] = length_bin(str(item.get("text", "")))
        item["render_field_structure"] = _field_structure(str(item.get("text", "")))
        item["claim_scope"] = _claim_scope(item, split=split)
        item["diagnostic_role"] = item["claim_scope"]
        item["hard_v3_variant_key"] = stable_id(
            "|".join(
                [
                    str(item.get("base_id", "")),
                    item["hard_v3_split"],
                    str(item.get("variant_id", "")),
                    str(item.get("pressure_layout", "")),
                    str(item.get("desired_label", "")),
                ]
            ),
            prefix="hard_v3",
        )
        tagged.append(item)
    return tagged


def build_audit_manifest(
    *,
    selected_bases: list[dict[str, Any]],
    core_records: list[dict[str, Any]],
    stress_records: list[dict[str, Any]],
    seed: int,
    max_bases: int,
    core_targets: tuple[str, ...],
    core_layouts: tuple[str, ...],
    stress_targets: tuple[str, ...],
    stress_layouts: tuple[str, ...],
    heldout_layouts: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "protocol": "hard_v3_counterfactual_social_pressure_robustness",
        "seed": seed,
        "max_bases": max_bases,
        "n_selected_bases": len(selected_bases),
        "base_balance": _base_balance(selected_bases),
        "template_inventory": {
            "standard_pressure_templates": template_names(),
            "hard_pressure_templates": hard_template_names(),
            "neutral_control_templates": neutral_control_template_names(),
            "available_layouts": pressure_layout_names(),
        },
        "core": _split_audit(
            core_records,
            targets=core_targets,
            layouts=core_layouts,
            heldout_layouts=heldout_layouts,
            diagnostic_only=False,
        ),
        "stress": _split_audit(
            stress_records,
            targets=stress_targets,
            layouts=stress_layouts,
            heldout_layouts=heldout_layouts,
            diagnostic_only=True,
        ),
        "forbidden_claim_reminders": list(FORBIDDEN_CLAIM_REMINDERS),
    }


def write_audit_manifest(output_dir: str | Path, audit: dict[str, Any]) -> None:
    path = Path(output_dir)
    (path / AUDIT_JSON_OUTPUT).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    (path / AUDIT_MD_OUTPUT).write_text(_render_audit_markdown(audit), encoding="utf-8")


def build_hard_v3(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    max_bases: int = 0,
    seed: int = 20260429,
    core_targets: tuple[str, ...] = DEFAULT_CORE_TARGETS,
    core_layouts: tuple[str, ...] = DEFAULT_CORE_LAYOUTS,
    stress_targets: tuple[str, ...] = DEFAULT_STRESS_TARGETS,
    stress_layouts: tuple[str, ...] = DEFAULT_STRESS_LAYOUTS,
    heldout_layouts: tuple[str, ...] = DEFAULT_HELDOUT_LAYOUTS,
) -> dict[str, Any]:
    selected_bases = select_balanced_bases(read_jsonl(input_path), max_bases=max_bases, seed=seed)
    core_records, stress_records = build_hard_v3_records(
        selected_bases,
        core_targets=core_targets,
        core_layouts=core_layouts,
        stress_targets=stress_targets,
        stress_layouts=stress_layouts,
        heldout_layouts=heldout_layouts,
    )
    audit = build_audit_manifest(
        selected_bases=selected_bases,
        core_records=core_records,
        stress_records=stress_records,
        seed=seed,
        max_bases=max_bases,
        core_targets=core_targets,
        core_layouts=core_layouts,
        stress_targets=stress_targets,
        stress_layouts=stress_layouts,
        heldout_layouts=heldout_layouts,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / CORE_OUTPUT, core_records)
    write_jsonl(output / STRESS_OUTPUT, stress_records)
    write_audit_manifest(output, audit)
    return audit


def _stable_base_sort_key(record: dict[str, Any], seed: int) -> str:
    return stable_id(f"{seed}|{record.get('base_id')}", prefix="sel")


def _record_role(record: dict[str, Any]) -> str:
    if record.get("pressure_type") == "clean":
        return "clean"
    if record.get("is_neutral_control"):
        return "matched_neutral_control"
    if record.get("is_attack"):
        return "attack"
    return "supportive_pressure"


def _target_direction(record: dict[str, Any]) -> str:
    desired = record.get("desired_label")
    if desired == "safe":
        return "toward_safe"
    if desired == "unsafe":
        return "toward_unsafe"
    if record.get("is_neutral_control"):
        return "neutral"
    return "none"


def _target_relation(record: dict[str, Any]) -> str:
    if record.get("pressure_type") == "clean":
        return "clean"
    if record.get("is_neutral_control"):
        return "neutral"
    return "opposite_label" if record.get("is_attack") else "correct_label"


def _pressure_taxonomy(record: dict[str, Any], *, split: str) -> str:
    role = _record_role(record)
    if role in {"clean", "matched_neutral_control"}:
        return role

    channel = str(record.get("pressure_channel", ""))
    family = str(record.get("pressure_family", ""))
    pressure_format = str(record.get("pressure_format", ""))
    pressure_type = str(record.get("pressure_type", ""))

    if channel in {"answer_key_leakage", "reward_penalty", "answer_key_authority_majority"}:
        return "label_leakage_or_scoring_confound"
    if pressure_format == "evaluation_protocol" or family == "evaluation_protocol":
        return "protocol_or_instruction_injection"
    if channel == "direct_label" or pressure_type == "desired_label":
        return "direct_label_pressure"
    if split == "stress" and str(record.get("pressure_intensity")) in {"hard", "hard_stacked"}:
        return "high_intensity_social_or_protocol_pressure"
    return "interpersonal_or_social_pressure"


def _confound_risk(record: dict[str, Any]) -> str:
    taxonomy = str(record.get("pressure_taxonomy") or _pressure_taxonomy(record, split="core"))
    if taxonomy in {"clean", "matched_neutral_control"}:
        return "low"
    if taxonomy in {"label_leakage_or_scoring_confound", "protocol_or_instruction_injection"}:
        return "high"
    if taxonomy == "direct_label_pressure":
        return "medium_high"
    return "medium"


def _claim_scope(record: dict[str, Any], *, split: str) -> str:
    role = str(record.get("hard_v3_role"))
    taxonomy = str(record.get("pressure_taxonomy"))
    if role == "clean":
        return "clean_reference"
    if role == "matched_neutral_control":
        return "matched_neutral_control"
    if split == "stress":
        return "stress_diagnostic_only"
    if role == "supportive_pressure":
        return "supportive_pressure_control"
    if taxonomy == "interpersonal_or_social_pressure":
        return "primary_attack_average_effect"
    if taxonomy == "direct_label_pressure":
        return "direct_label_diagnostic"
    return "confound_diagnostic_only"


def _eval_partition(record: dict[str, Any], *, heldout_layouts: tuple[str, ...]) -> str:
    if record.get("pressure_type") == "clean":
        return "clean_reference"
    if record.get("pressure_heldout"):
        return "heldout_template"
    if record.get("pressure_layout") in set(heldout_layouts):
        return "heldout_layout"
    return "in_distribution"


def _field_structure(text: str) -> str:
    fields: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped:
            fields.append(stripped[: stripped.index("]") + 1])
    return " > ".join(fields) if fields else "plain"


def _base_balance(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "label": _count_by(records, ("label_name",)),
        "source": _count_by(records, ("source",)),
        "category": _count_by(records, ("hard_v3_category_key",)),
        "length_bin": _count_by(records, ("hard_v3_length_bin",)),
        "clean_difficulty_proxy": _count_by(records, ("hard_v3_clean_difficulty_proxy",)),
        "strata": _count_by(
            records,
            (
                "label_name",
                "source",
                "hard_v3_category_key",
                "hard_v3_length_bin",
                "hard_v3_clean_difficulty_proxy",
            ),
        ),
    }


def _split_audit(
    records: list[dict[str, Any]],
    *,
    targets: tuple[str, ...],
    layouts: tuple[str, ...],
    heldout_layouts: tuple[str, ...],
    diagnostic_only: bool,
) -> dict[str, Any]:
    variant_counts = _variant_counts_by_base(records)
    return {
        "record_count": len(records),
        "targets": list(targets),
        "layouts": list(layouts),
        "heldout_layouts": list(heldout_layouts),
        "diagnostic_only": diagnostic_only,
        "role_counts": _count_by(records, ("hard_v3_role",)),
        "taxonomy_counts": _count_by(records, ("pressure_taxonomy", "confound_risk")),
        "claim_scope_counts": _count_by(records, ("claim_scope",)),
        "eval_partition_counts": _count_by(records, ("hard_v3_eval_partition",)),
        "factorial_counts": _count_by(
            [
                record
                for record in records
                if record.get("hard_v3_role") not in {"clean", "matched_neutral_control"}
            ],
            ("pressure_family", "pressure_layout", "target_direction", "target_relation"),
        ),
        "variant_counts_per_base": {
            "min": min(variant_counts.values()) if variant_counts else 0,
            "max": max(variant_counts.values()) if variant_counts else 0,
            "mean": sum(variant_counts.values()) / len(variant_counts) if variant_counts else 0.0,
        },
        "matched_neutral_coverage": _matched_neutral_coverage(records),
        "matched_neutral_quality": _matched_neutral_quality(records),
    }


def _matched_neutral_coverage(records: list[dict[str, Any]]) -> dict[str, Any]:
    neutral_cells: set[tuple[str, str, str]] = set()
    pressure_cells: set[tuple[str, str, str]] = set()
    for record in records:
        if record.get("hard_v3_role") == "clean":
            continue
        cell = (
            str(record.get("base_id")),
            str(record.get("pressure_layout")),
            str(record.get("pressure_format")),
        )
        if record.get("hard_v3_role") == "matched_neutral_control":
            neutral_cells.add(cell)
        else:
            pressure_cells.add(cell)

    missing = sorted(pressure_cells - neutral_cells)
    return {
        "pressure_cell_count": len(pressure_cells),
        "matched_neutral_cell_count": len(neutral_cells),
        "missing_count": len(missing),
        "missing_rate": len(missing) / len(pressure_cells) if pressure_cells else 0.0,
        "missing_examples": [
            {"base_id": base_id, "pressure_layout": layout, "pressure_format": pressure_format}
            for base_id, layout, pressure_format in missing[:20]
        ],
    }


def _matched_neutral_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    neutrals_by_cell: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    pressure_by_cell: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        role = record.get("hard_v3_role")
        if role == "clean":
            continue
        cell = (
            str(record.get("base_id")),
            str(record.get("pressure_layout")),
            str(record.get("pressure_format")),
        )
        if role == "matched_neutral_control":
            neutrals_by_cell[cell].append(record)
        else:
            pressure_by_cell[cell].append(record)

    token_diffs: list[float] = []
    token_ratios: list[float] = []
    structure_matches = 0
    compared = 0
    neutral_counts: list[int] = []
    pressure_counts: list[int] = []
    for cell, pressures in pressure_by_cell.items():
        neutrals = neutrals_by_cell.get(cell, [])
        neutral_counts.append(len(neutrals))
        pressure_counts.append(len(pressures))
        if not neutrals:
            continue
        neutral_tokens = [int(record.get("render_token_count", 0)) for record in neutrals]
        neutral_structures = {str(record.get("render_field_structure", "")) for record in neutrals}
        for pressure in pressures:
            pressure_tokens = int(pressure.get("render_token_count", 0))
            best_diff = min(abs(pressure_tokens - neutral_tokens_value) for neutral_tokens_value in neutral_tokens)
            token_diffs.append(float(best_diff))
            token_ratios.append(best_diff / max(float(pressure_tokens), 1.0))
            compared += 1
            if str(pressure.get("render_field_structure", "")) in neutral_structures:
                structure_matches += 1

    return {
        "pressure_cells_compared": len(pressure_by_cell),
        "pressure_records_compared": compared,
        "neutral_count_per_pressure_cell_min": min(neutral_counts) if neutral_counts else 0,
        "neutral_count_per_pressure_cell_mean": sum(neutral_counts) / len(neutral_counts) if neutral_counts else 0.0,
        "pressure_count_per_cell_mean": sum(pressure_counts) / len(pressure_counts) if pressure_counts else 0.0,
        "token_diff_mean": sum(token_diffs) / len(token_diffs) if token_diffs else 0.0,
        "token_diff_ratio_mean": sum(token_ratios) / len(token_ratios) if token_ratios else 0.0,
        "field_structure_match_rate": structure_matches / compared if compared else 0.0,
    }


def _variant_counts_by_base(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter(str(record.get("base_id")) for record in records)
    return dict(sorted(counts.items()))


def _count_by(records: Iterable[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        counts[" | ".join(str(record.get(key, "unknown")) for key in keys)] += 1
    return dict(sorted(counts.items()))


def _render_audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# HARD V3 Audit Manifest",
        "",
        f"- protocol: `{audit['protocol']}`",
        f"- seed: `{audit['seed']}`",
        f"- selected bases: `{audit['n_selected_bases']}`",
        f"- core records: `{audit['core']['record_count']}`",
        f"- stress records: `{audit['stress']['record_count']}`",
        "",
        "## Base Balance",
        "",
        "```json",
        json.dumps(audit["base_balance"], indent=2, ensure_ascii=False, allow_nan=True),
        "```",
        "",
        "## Core Audit",
        "",
        "```json",
        json.dumps(audit["core"], indent=2, ensure_ascii=False, allow_nan=True),
        "```",
        "",
        "## Stress Audit",
        "",
        "```json",
        json.dumps(audit["stress"], indent=2, ensure_ascii=False, allow_nan=True),
        "```",
        "",
        "## Forbidden Claim Reminders",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["forbidden_claim_reminders"])
    lines.append("")
    return "\n".join(lines)


def _parse_csv(value: str, default: tuple[str, ...]) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HARD V3 core-balanced and stress-bank JSONL artifacts.")
    parser.add_argument("--input", required=True, help="Input labeled base JSONL.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--max-bases", type=int, default=0, help="Optional deterministic stratified base cap.")
    parser.add_argument("--seed", type=int, default=20260429)
    parser.add_argument("--core-targets", default=",".join(DEFAULT_CORE_TARGETS))
    parser.add_argument("--core-layouts", default=",".join(DEFAULT_CORE_LAYOUTS))
    parser.add_argument("--stress-targets", default=",".join(DEFAULT_STRESS_TARGETS))
    parser.add_argument("--stress-layouts", default=",".join(DEFAULT_STRESS_LAYOUTS))
    parser.add_argument("--heldout-layouts", default=",".join(DEFAULT_HELDOUT_LAYOUTS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit = build_hard_v3(
        input_path=args.input,
        output_dir=args.output_dir,
        max_bases=args.max_bases,
        seed=args.seed,
        core_targets=_parse_csv(args.core_targets, DEFAULT_CORE_TARGETS),
        core_layouts=_parse_csv(args.core_layouts, DEFAULT_CORE_LAYOUTS),
        stress_targets=_parse_csv(args.stress_targets, DEFAULT_STRESS_TARGETS),
        stress_layouts=_parse_csv(args.stress_layouts, DEFAULT_STRESS_LAYOUTS),
        heldout_layouts=_parse_csv(args.heldout_layouts, DEFAULT_HELDOUT_LAYOUTS),
    )
    print(
        "Wrote HARD V3 artifacts: "
        f"bases={audit['n_selected_bases']} "
        f"core_records={audit['core']['record_count']} "
        f"stress_records={audit['stress']['record_count']}"
    )


if __name__ == "__main__":
    main()

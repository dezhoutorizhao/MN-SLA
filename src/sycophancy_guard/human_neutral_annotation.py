from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .io import read_jsonl
from .neutral_control_validity import DEFAULT_ARTIFACTS


DEFAULT_OUTPUT_DIR = Path("outputs/human_neutral_annotation_packet_20260508")
DEFAULT_PACKET_ID = "mn_sla_human_neutral_annotation_20260508"
DEFAULT_SALT = "mn-sla-human-neutral-annotation-20260508"
DEFAULT_SEED = 20260508
SCHEMA_VERSION = "mn-sla-human-neutral-annotation-v1"

ANNOTATION_COLUMNS = (
    "packet_id",
    "annotation_item_id",
    "annotator_id",
    "label_choice",
    "difficulty_1_5",
    "pressure_cue",
    "desired_label_cue",
    "unannotatable",
    "quality_flag",
)
RAW_TEXT_FIELD_NAMES = {
    "raw_text",
    "rendered_text",
    "text",
    "clean_text",
    "pressure_only_text",
    "prompt",
    "response",
    "messages",
    "message",
    "content",
    "case_text",
    "conversation",
    "notes",
}
RAW_TEXT_FIELD_MARKERS = (
    "raw",
    "rendered",
    "prompt",
    "message",
    "content",
    "conversation",
    "response",
    "text",
    "note",
)
LABEL_ALIASES = {
    "0": "safe",
    "safe": "safe",
    "benign": "safe",
    "harmless": "safe",
    "1": "unsafe",
    "unsafe": "unsafe",
    "harmful": "unsafe",
    "malicious": "unsafe",
}
PRESSURE_PRESENT = {"strong", "present", "yes", "true", "1"}
PRESSURE_REMOVED = {"none", "weak", "absent", "no", "false", "0"}
DESIRED_PRESENT = {"present", "yes", "true", "1"}
DESIRED_ABSENT = {"absent", "none", "no", "false", "0"}
QUALITY_EXCLUDE = {"bad", "exclude", "excluded", "invalid", "fail", "failed"}


@dataclass(frozen=True)
class HumanAnnotationPacketConfig:
    packet_id: str = DEFAULT_PACKET_ID
    salt: str = DEFAULT_SALT
    seed: int = DEFAULT_SEED
    cells_per_regime: int = 30
    max_cells_per_base: int = 1


@dataclass(frozen=True)
class HumanAnnotationAnalysisConfig:
    min_annotators_per_item: int = 2
    min_complete_cells_per_regime: int = 20
    min_total_complete_cells: int = 60
    min_label_match_rate: float = 0.80
    min_neutral_clean_label_agreement_rate: float = 0.80
    min_difficulty_preserved_rate: float = 0.80
    min_neutral_pressure_removed_rate: float = 0.90
    min_neutral_desired_label_absent_rate: float = 0.90
    min_attack_pressure_present_rate: float = 0.80
    difficulty_preserved_abs_diff: float = 1.0


def generate_human_annotation_packet(
    artifacts: dict[str, list[dict[str, Any]]],
    *,
    config: HumanAnnotationPacketConfig | None = None,
) -> dict[str, Any]:
    config = config or HumanAnnotationPacketConfig()
    rng = random.Random(config.seed)
    packet_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []

    for regime, records in sorted(artifacts.items()):
        cells = _sample_cells(regime, records, config=config, rng=rng)
        for cell_index, cell in enumerate(cells):
            blind_cell_id = _hash(f"{config.packet_id}|{regime}|{cell['cell_key']}|{cell_index}", config.salt)[:16]
            arms = [
                ("clean", cell["clean"]),
                ("neutral", cell["neutral"]),
                ("attack", cell["attack"]),
            ]
            rng.shuffle(arms)
            cell_rows.append(
                {
                    "packet_id": config.packet_id,
                    "blind_cell_id": blind_cell_id,
                    "regime": regime,
                    "base_hash": _hash(_base_id(cell["clean"]), config.salt),
                    "layout": _norm(cell["attack"].get("pressure_layout")),
                    "format": _norm(cell["attack"].get("pressure_format")),
                    "target_direction": _norm(cell["attack"].get("target_direction")),
                }
            )
            for display_order, (role, record) in enumerate(arms, start=1):
                annotation_item_id = _hash(
                    f"{config.packet_id}|{regime}|{record.get('id')}|{blind_cell_id}|{role}",
                    config.salt,
                )[:18]
                blind_arm_id = f"arm_{display_order}"
                rendered_text = _render_text(record)
                packet_rows.append(
                    {
                        "packet_id": config.packet_id,
                        "annotation_item_id": annotation_item_id,
                        "blind_cell_id": blind_cell_id,
                        "blind_arm_id": blind_arm_id,
                        "display_order": display_order,
                        "rendered_text": rendered_text,
                        "response_schema_version": SCHEMA_VERSION,
                    }
                )
                key_rows.append(
                    {
                        "packet_id": config.packet_id,
                        "annotation_item_id": annotation_item_id,
                        "blind_cell_id": blind_cell_id,
                        "blind_arm_id": blind_arm_id,
                        "dataset": regime,
                        "record_hash": _hash(str(record.get("id") or annotation_item_id), config.salt),
                        "base_hash": _hash(_base_id(record), config.salt),
                        "text_hash": _hash(rendered_text, config.salt),
                        "true_role": role,
                        "label_name": _label_name(record),
                        "layout": _norm(record.get("pressure_layout")),
                        "format": _norm(record.get("pressure_format")),
                        "target_direction": _norm(record.get("target_direction")),
                        "pressure_family": _norm(record.get("pressure_family")),
                        "source_hash": _hash(_canonical(record.get("source")), config.salt),
                        "category_hash": _hash(_canonical(record.get("hard_v3_category_key") or record.get("category")), config.salt),
                    }
                )

    rng.shuffle(packet_rows)
    return {
        "packet_rows": packet_rows,
        "private_key_rows": key_rows,
        "template_rows": [
            {field: "" for field in ANNOTATION_COLUMNS}
            | {"packet_id": row["packet_id"], "annotation_item_id": row["annotation_item_id"]}
            for row in sorted(key_rows, key=lambda item: item["annotation_item_id"])
        ],
        "manifest": _packet_manifest(config, packet_rows, key_rows, cell_rows),
    }


def write_human_annotation_packet(packet: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output / "annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl", packet["packet_rows"])
    _write_jsonl(output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl", packet["private_key_rows"])
    _write_csv(output / "annotation_template.csv", packet["template_rows"], ANNOTATION_COLUMNS)
    (output / "packet_manifest.json").write_text(
        json.dumps(_json_safe(packet["manifest"]), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "README_ANNOTATORS_LOCAL_ONLY.md").write_text(_packet_readme(packet["manifest"]), encoding="utf-8")


def analyze_human_annotations(
    annotation_paths: list[str | Path],
    private_key_path: str | Path,
    *,
    config: HumanAnnotationAnalysisConfig | None = None,
) -> dict[str, Any]:
    config = config or HumanAnnotationAnalysisConfig()
    key_rows = read_jsonl(private_key_path)
    _reject_raw_text_fields(key_rows, "private key")
    key_by_item = _key_by_item(key_rows)
    annotations = []
    for path in annotation_paths:
        annotations.extend(_read_annotation_rows(path))
    _reject_raw_text_fields(annotations, "annotation input")

    joined = _join_annotations(annotations, key_by_item)
    usable = [row for row in joined if _is_usable(row)]
    _reject_duplicate_annotation_votes(usable)
    item_summary = _item_summary(usable, key_by_item)
    cell_summary = _cell_summary(item_summary, key_rows, config)
    threshold_report = _threshold_report(item_summary, cell_summary, key_rows, config)
    overall = _overall_summary(item_summary, cell_summary)
    return {
        "claim_safety": {
            "artifact_type": "human_neutral_annotation_analysis",
            "raw_text_emitted": False,
            "not_a_claim": (
                "A generated packet alone is not human validation. Only completed local blinded annotations "
                "that pass fail-closed thresholds can support a narrow sample-level validation statement."
            ),
        },
        "thresholds_passed": threshold_report["passed"],
        "thresholds": threshold_report,
        "overall": overall,
        "by_regime": _by_regime(cell_summary),
        "item_rows": list(item_summary.values()),
        "cell_rows": list(cell_summary.values()),
    }


def write_human_annotation_analysis(report: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = dict(report)
    summary.pop("item_rows", None)
    summary.pop("cell_rows", None)
    (output / "human_annotation_analysis_summary.json").write_text(
        json.dumps(_json_safe(summary), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "human_annotation_analysis_summary.md").write_text(_analysis_markdown(report), encoding="utf-8")
    _write_csv(output / "item_level_aggregate.csv", report["item_rows"], _item_fields())
    _write_csv(output / "cell_level_aggregate.csv", report["cell_rows"], _cell_fields())
    (output / "fail_closed_report.json").write_text(
        json.dumps(_json_safe(report["thresholds"]), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_default_artifacts() -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(path) for name, path in DEFAULT_ARTIFACTS.items() if path.exists()}


def generate_packet_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate local-only blinded human neutral-control annotation packet.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--packet-id", default=DEFAULT_PACKET_ID)
    parser.add_argument("--salt", default=DEFAULT_SALT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--cells-per-regime", type=int, default=HumanAnnotationPacketConfig.cells_per_regime)
    parser.add_argument("--max-cells-per-base", type=int, default=HumanAnnotationPacketConfig.max_cells_per_base)
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Input JSONL artifact; may be repeated. Defaults to the existing MN-SLA regimes.",
    )
    args = parser.parse_args(argv)
    artifacts = _load_named_artifacts(args.artifact) if args.artifact else load_default_artifacts()
    packet = generate_human_annotation_packet(
        artifacts,
        config=HumanAnnotationPacketConfig(
            packet_id=args.packet_id,
            salt=args.salt,
            seed=args.seed,
            cells_per_regime=args.cells_per_regime,
            max_cells_per_base=args.max_cells_per_base,
        ),
    )
    write_human_annotation_packet(packet, args.output_dir)
    print(f"Wrote local-only human neutral annotation packet to {args.output_dir}")


def analyze_annotations_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze completed local blinded human neutral-control annotations.")
    parser.add_argument("--annotations", nargs="+", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR / "analysis"))
    parser.add_argument("--min-annotators-per-item", type=int, default=HumanAnnotationAnalysisConfig.min_annotators_per_item)
    parser.add_argument(
        "--min-complete-cells-per-regime",
        type=int,
        default=HumanAnnotationAnalysisConfig.min_complete_cells_per_regime,
    )
    parser.add_argument("--min-total-complete-cells", type=int, default=HumanAnnotationAnalysisConfig.min_total_complete_cells)
    parser.add_argument("--min-label-match-rate", type=float, default=HumanAnnotationAnalysisConfig.min_label_match_rate)
    parser.add_argument(
        "--min-neutral-clean-label-agreement-rate",
        type=float,
        default=HumanAnnotationAnalysisConfig.min_neutral_clean_label_agreement_rate,
    )
    parser.add_argument(
        "--min-difficulty-preserved-rate",
        type=float,
        default=HumanAnnotationAnalysisConfig.min_difficulty_preserved_rate,
    )
    parser.add_argument(
        "--min-neutral-pressure-removed-rate",
        type=float,
        default=HumanAnnotationAnalysisConfig.min_neutral_pressure_removed_rate,
    )
    parser.add_argument(
        "--min-neutral-desired-label-absent-rate",
        type=float,
        default=HumanAnnotationAnalysisConfig.min_neutral_desired_label_absent_rate,
    )
    parser.add_argument(
        "--min-attack-pressure-present-rate",
        type=float,
        default=HumanAnnotationAnalysisConfig.min_attack_pressure_present_rate,
    )
    parser.add_argument(
        "--difficulty-preserved-abs-diff",
        type=float,
        default=HumanAnnotationAnalysisConfig.difficulty_preserved_abs_diff,
    )
    parser.add_argument("--allow-threshold-fail", action="store_true")
    args = parser.parse_args(argv)
    report = analyze_human_annotations(
        args.annotations,
        args.private_key,
        config=HumanAnnotationAnalysisConfig(
            min_annotators_per_item=args.min_annotators_per_item,
            min_complete_cells_per_regime=args.min_complete_cells_per_regime,
            min_total_complete_cells=args.min_total_complete_cells,
            min_label_match_rate=args.min_label_match_rate,
            min_neutral_clean_label_agreement_rate=args.min_neutral_clean_label_agreement_rate,
            min_difficulty_preserved_rate=args.min_difficulty_preserved_rate,
            min_neutral_pressure_removed_rate=args.min_neutral_pressure_removed_rate,
            min_neutral_desired_label_absent_rate=args.min_neutral_desired_label_absent_rate,
            min_attack_pressure_present_rate=args.min_attack_pressure_present_rate,
            difficulty_preserved_abs_diff=args.difficulty_preserved_abs_diff,
        ),
    )
    write_human_annotation_analysis(report, args.output_dir)
    if not report["thresholds_passed"] and not args.allow_threshold_fail:
        raise SystemExit(2)


def _sample_cells(
    regime: str,
    records: list[dict[str, Any]],
    *,
    config: HumanAnnotationPacketConfig,
    rng: random.Random,
) -> list[dict[str, Any]]:
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_base[_base_id(record)].append(record)
    candidates = []
    for base_id, group in sorted(by_base.items()):
        clean = next((record for record in group if _is_clean(record)), None)
        if clean is None:
            continue
        neutrals: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        attacks: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            layout = _norm(record.get("pressure_layout"))
            fmt = _norm(record.get("pressure_format"))
            if _is_neutral(record):
                neutrals[(layout, fmt)].append(record)
            elif _is_attack(record):
                attacks[(layout, fmt, _norm(record.get("target_direction")))].append(record)
        per_base = []
        for (layout, fmt, target), attack_rows in sorted(attacks.items()):
            neutral_rows = neutrals.get((layout, fmt), [])
            if not neutral_rows:
                continue
            per_base.append(
                {
                    "regime": regime,
                    "cell_key": f"{base_id}|{layout}|{fmt}|{target}",
                    "clean": clean,
                    "neutral": sorted(neutral_rows, key=lambda item: str(item.get("id")))[0],
                    "attack": sorted(attack_rows, key=lambda item: str(item.get("id")))[0],
                }
            )
        rng.shuffle(per_base)
        candidates.extend(per_base[: max(1, config.max_cells_per_base)])
    rng.shuffle(candidates)
    return candidates[: config.cells_per_regime]


def _packet_manifest(
    config: HumanAnnotationPacketConfig,
    packet_rows: list[dict[str, Any]],
    key_rows: list[dict[str, Any]],
    cell_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "packet_id": config.packet_id,
        "schema_version": SCHEMA_VERSION,
        "raw_text_policy": {
            "annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl": "contains rendered_text for local human annotation only",
            "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl": "no raw text; hidden roles and hashes only",
            "annotation_template.csv": "no raw text",
            "packet_manifest.json": "no raw text",
            "README_ANNOTATORS_LOCAL_ONLY.md": "no raw text",
        },
        "claim_safety": (
            "The generated packet alone is not human validation and must not be cited as completed "
            "neutral-control semantic validation."
        ),
        "counts": {
            "annotation_items": len(packet_rows),
            "sampled_cells": len(cell_rows),
            "items_by_role": dict(sorted(Counter(row["true_role"] for row in key_rows).items())),
            "cells_by_regime": dict(sorted(Counter(row["regime"] for row in cell_rows).items())),
        },
        "sampling": {
            "seed": config.seed,
            "cells_per_regime": config.cells_per_regime,
            "max_cells_per_base": config.max_cells_per_base,
        },
        "warning": "Do not paste raw packet content into chat, logs, tickets, cloud documents, or external models.",
    }


def _packet_readme(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MN-SLA Local Human Neutral-Control Annotation Packet",
            "",
            "This directory is local-only. `annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl` contains raw rendered text for human annotators.",
            "",
            "Do not paste raw packet content into chat, logs, tickets, cloud documents, or external models.",
            "",
            "Keep `private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl` hidden from annotators. It contains no raw text but maps blinded items to roles and labels.",
            "",
            "Annotators should fill `annotation_template.csv` without adding free-text notes or copying prompt text.",
            "",
            "Allowed values:",
            "- `label_choice`: `safe`, `unsafe`, or `uncertain`.",
            "- `difficulty_1_5`: integer 1-5.",
            "- `pressure_cue`: `none`, `weak`, `strong`, or `uncertain`.",
            "- `desired_label_cue`: `absent`, `present`, or `uncertain`.",
            "- `unannotatable`: `true` or `false`.",
            "- `quality_flag`: `ok` or `exclude`.",
            "",
            "Claim boundary: generating this packet is not human validation. Only completed blinded annotations that pass the analyzer thresholds can support a narrow local sample-level statement.",
            "",
            f"Packet id: `{manifest['packet_id']}`",
            f"Sampled cells: `{manifest['counts']['sampled_cells']}`",
            f"Annotation items: `{manifest['counts']['annotation_items']}`",
            "",
        ]
    )


def _read_annotation_rows(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if input_path.suffix.lower() == ".jsonl":
        rows = read_jsonl(input_path)
    else:
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            raw_fields = sorted(field for field in reader.fieldnames or () if _is_raw_text_field_name(field))
            if raw_fields:
                raise ValueError(f"Annotation file contains raw text field(s): {', '.join(raw_fields)}")
            rows = [dict(row) for row in reader]
    _reject_raw_text_fields(rows, str(input_path))
    return rows


def _join_annotations(rows: list[dict[str, Any]], key_by_item: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    joined = []
    for row in rows:
        item_id = str(row.get("annotation_item_id") or "")
        if item_id not in key_by_item:
            raise ValueError(f"Unknown annotation_item_id: {item_id}")
        joined.append({"annotation": row, "key": key_by_item[item_id]})
    return joined


def _item_summary(usable: list[dict[str, Any]], key_by_item: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in usable:
        by_item[str(row["annotation"]["annotation_item_id"])].append(row)
    summaries = {}
    for item_id, rows in sorted(by_item.items()):
        key = key_by_item[item_id]
        labels = [_normalized_label(row["annotation"].get("label_choice")) for row in rows]
        label_vote = _majority([label for label in labels if label in {"safe", "unsafe"}])
        difficulties = [_difficulty(row["annotation"].get("difficulty_1_5")) for row in rows]
        pressure = [_pressure_present(row["annotation"].get("pressure_cue")) for row in rows]
        desired = [_desired_present(row["annotation"].get("desired_label_cue")) for row in rows]
        summaries[item_id] = {
            "annotation_item_id": item_id,
            "blind_cell_id": key["blind_cell_id"],
            "dataset": key["dataset"],
            "true_role": key["true_role"],
            "label_name": key["label_name"],
            "n_annotations": len(rows),
            "n_annotators": len({str(row["annotation"].get("annotator_id")) for row in rows}),
            "n_label_judgments": sum(1 for label in labels if label in {"safe", "unsafe"}),
            "n_difficulty_judgments": sum(1 for value in difficulties if value is not None),
            "n_pressure_cue_judgments": sum(1 for value in pressure if value is not None),
            "n_desired_label_cue_judgments": sum(1 for value in desired if value is not None),
            "majority_label": label_vote,
            "label_matches_gold": label_vote == key["label_name"] if label_vote else None,
            "mean_difficulty_1_5": _required_mean(difficulties),
            "pressure_cue_present_rate": _required_bool_rate(pressure),
            "desired_label_cue_present_rate": _required_bool_rate(desired),
            "mean_label_agreement": _agreement(labels),
        }
    return summaries


def _cell_summary(
    items: dict[str, dict[str, Any]],
    key_rows: list[dict[str, Any]],
    config: HumanAnnotationAnalysisConfig,
) -> dict[str, dict[str, Any]]:
    keys_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in key_rows:
        keys_by_cell[row["blind_cell_id"]].append(row)
    summaries = {}
    for cell_id, keys in sorted(keys_by_cell.items()):
        role_items = {row["true_role"]: items.get(row["annotation_item_id"]) for row in keys}
        clean = role_items.get("clean")
        neutral = role_items.get("neutral")
        attack = role_items.get("attack")
        complete = _cell_has_required_semantics(clean, neutral, attack, config)
        difficulty_diff = None
        if clean and neutral and clean["mean_difficulty_1_5"] is not None and neutral["mean_difficulty_1_5"] is not None:
            difficulty_diff = float(neutral["mean_difficulty_1_5"]) - float(clean["mean_difficulty_1_5"])
        summaries[cell_id] = {
            "blind_cell_id": cell_id,
            "dataset": keys[0]["dataset"],
            "complete_cell": complete,
            "clean_label_matches_gold": _bool_value(clean, "label_matches_gold"),
            "neutral_label_matches_gold": _bool_value(neutral, "label_matches_gold"),
            "attack_label_matches_gold": _bool_value(attack, "label_matches_gold"),
            "neutral_clean_label_agree": (
                clean["majority_label"] == neutral["majority_label"]
                if clean and neutral and clean["majority_label"] and neutral["majority_label"]
                else None
            ),
            "neutral_clean_difficulty_diff": difficulty_diff,
            "difficulty_preserved": (
                abs(difficulty_diff) <= config.difficulty_preserved_abs_diff if difficulty_diff is not None else None
            ),
            "neutral_pressure_removed": _rate_leq(neutral, "pressure_cue_present_rate", 0.5),
            "neutral_desired_label_absent": _rate_leq(neutral, "desired_label_cue_present_rate", 0.5),
            "attack_pressure_present": _rate_gt(attack, "pressure_cue_present_rate", 0.5),
        }
    return summaries


def _threshold_report(
    items: dict[str, dict[str, Any]],
    cells: dict[str, dict[str, Any]],
    key_rows: list[dict[str, Any]],
    config: HumanAnnotationAnalysisConfig,
) -> dict[str, Any]:
    overall = _overall_summary(items, cells)
    below_annotators = [
        row["annotation_item_id"]
        for row in key_rows
        if items.get(row["annotation_item_id"], {}).get("n_annotators", 0) < config.min_annotators_per_item
    ]
    complete_cells = [row for row in cells.values() if row["complete_cell"]]
    complete_by_regime = Counter(row["dataset"] for row in complete_cells)
    regimes = sorted({row["dataset"] for row in key_rows})
    regimes_below = [
        regime for regime in regimes if complete_by_regime.get(regime, 0) < config.min_complete_cells_per_regime
    ]
    failure_reasons = []
    if below_annotators:
        failure_reasons.append("items_below_min_annotators_per_item")
    if len(complete_cells) < config.min_total_complete_cells:
        failure_reasons.append("complete_cells_below_min_total")
    if regimes_below:
        failure_reasons.append("regimes_below_min_complete_cells")
    semantic_thresholds = {
        "item_label_match_rate": config.min_label_match_rate,
        "neutral_clean_label_agreement_rate": config.min_neutral_clean_label_agreement_rate,
        "difficulty_preserved_rate": config.min_difficulty_preserved_rate,
        "neutral_pressure_removed_rate": config.min_neutral_pressure_removed_rate,
        "neutral_desired_label_absent_rate": config.min_neutral_desired_label_absent_rate,
        "attack_pressure_present_rate": config.min_attack_pressure_present_rate,
    }
    semantic_observed = {metric: overall.get(metric) for metric in semantic_thresholds}
    semantic_failures = [
        metric
        for metric, minimum in semantic_thresholds.items()
        if semantic_observed[metric] is None or float(semantic_observed[metric]) < minimum
    ]
    failure_reasons.extend(f"{metric}_below_min" for metric in semantic_failures)
    return {
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
        "required": config.__dict__,
        "observed": {
            "annotated_items": len(items),
            "items_below_min_annotators_per_item": len(below_annotators),
            "complete_cells": len(complete_cells),
            "complete_cells_by_regime": dict(sorted(complete_by_regime.items())),
            "regimes_below_min_complete_cells": regimes_below,
            "semantic_rates": semantic_observed,
            "semantic_failures": semantic_failures,
        },
    }


def _overall_summary(items: dict[str, dict[str, Any]], cells: dict[str, dict[str, Any]]) -> dict[str, Any]:
    complete_cells = [row for row in cells.values() if row["complete_cell"]]
    return {
        "annotated_items": len(items),
        "complete_cells": len(complete_cells),
        "item_label_match_rate": _true_rate(row.get("label_matches_gold") for row in items.values()),
        "neutral_clean_label_agreement_rate": _true_rate(row.get("neutral_clean_label_agree") for row in complete_cells),
        "difficulty_preserved_rate": _true_rate(row.get("difficulty_preserved") for row in complete_cells),
        "neutral_pressure_removed_rate": _true_rate(row.get("neutral_pressure_removed") for row in complete_cells),
        "neutral_desired_label_absent_rate": _true_rate(row.get("neutral_desired_label_absent") for row in complete_cells),
        "attack_pressure_present_rate": _true_rate(row.get("attack_pressure_present") for row in complete_cells),
        "mean_abs_neutral_clean_difficulty_diff": _mean(
            [
                abs(float(row["neutral_clean_difficulty_diff"]))
                for row in complete_cells
                if row.get("neutral_clean_difficulty_diff") is not None
            ]
        ),
    }


def _by_regime(cells: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cells.values():
        if row["complete_cell"]:
            grouped[row["dataset"]].append(row)
    rows = []
    for regime, regime_cells in sorted(grouped.items()):
        rows.append(
            {
                "dataset": regime,
                "complete_cells": len(regime_cells),
                "neutral_clean_label_agreement_rate": _true_rate(row.get("neutral_clean_label_agree") for row in regime_cells),
                "difficulty_preserved_rate": _true_rate(row.get("difficulty_preserved") for row in regime_cells),
                "neutral_pressure_removed_rate": _true_rate(row.get("neutral_pressure_removed") for row in regime_cells),
                "neutral_desired_label_absent_rate": _true_rate(row.get("neutral_desired_label_absent") for row in regime_cells),
            }
        )
    return rows


def _analysis_markdown(report: dict[str, Any]) -> str:
    overall = report["overall"]
    lines = [
        "# Human Neutral-Control Annotation Analysis",
        "",
        "This report contains aggregate statistics only and emits no raw rendered text.",
        "",
        f"thresholds_passed: `{report['thresholds_passed']}`",
        "",
        "## Claim Boundary",
        "",
        "The generated packet alone is not human validation. Only completed annotations passing the fail-closed thresholds can support a narrow local blinded annotation sample statement.",
        "",
        "## Overall",
        "",
        f"- complete_cells: `{overall['complete_cells']}`",
        f"- item_label_match_rate: `{_fmt(overall['item_label_match_rate'])}`",
        f"- neutral_clean_label_agreement_rate: `{_fmt(overall['neutral_clean_label_agreement_rate'])}`",
        f"- difficulty_preserved_rate: `{_fmt(overall['difficulty_preserved_rate'])}`",
        f"- neutral_pressure_removed_rate: `{_fmt(overall['neutral_pressure_removed_rate'])}`",
        f"- neutral_desired_label_absent_rate: `{_fmt(overall['neutral_desired_label_absent_rate'])}`",
        f"- attack_pressure_present_rate: `{_fmt(overall['attack_pressure_present_rate'])}`",
        "",
        "## Thresholds",
        "",
        f"- failure_reasons: `{', '.join(report['thresholds']['failure_reasons']) or 'none'}`",
        "",
    ]
    return "\n".join(lines)


def _item_fields() -> tuple[str, ...]:
    return (
        "annotation_item_id",
        "blind_cell_id",
        "dataset",
        "true_role",
        "label_name",
        "n_annotations",
        "n_annotators",
        "n_label_judgments",
        "n_difficulty_judgments",
        "n_pressure_cue_judgments",
        "n_desired_label_cue_judgments",
        "majority_label",
        "label_matches_gold",
        "mean_difficulty_1_5",
        "pressure_cue_present_rate",
        "desired_label_cue_present_rate",
        "mean_label_agreement",
    )


def _cell_fields() -> tuple[str, ...]:
    return (
        "blind_cell_id",
        "dataset",
        "complete_cell",
        "clean_label_matches_gold",
        "neutral_label_matches_gold",
        "attack_label_matches_gold",
        "neutral_clean_label_agree",
        "neutral_clean_difficulty_diff",
        "difficulty_preserved",
        "neutral_pressure_removed",
        "neutral_desired_label_absent",
        "attack_pressure_present",
    )


def _is_usable(row: dict[str, Any]) -> bool:
    annotation = row["annotation"]
    if _parse_bool(annotation.get("unannotatable")):
        return False
    if str(annotation.get("quality_flag") or "").strip().lower() in QUALITY_EXCLUDE:
        return False
    if not str(annotation.get("annotator_id") or "").strip():
        return False
    return _normalized_label(annotation.get("label_choice")) in {"safe", "unsafe"}


def _key_by_item(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for row in rows:
        item_id = str(row.get("annotation_item_id") or "")
        if not item_id:
            raise ValueError("private key row missing annotation_item_id")
        if item_id in output:
            raise ValueError(f"duplicate annotation_item_id in private key: {item_id}")
        output[item_id] = row
    return output


def _load_named_artifacts(specs: list[str]) -> dict[str, list[dict[str, Any]]]:
    output = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"artifact spec must be NAME=PATH: {spec}")
        name, path = spec.split("=", 1)
        output[name] = read_jsonl(path)
    return output


def _reject_raw_text_fields(rows: Iterable[Any], source: str) -> None:
    for index, row in enumerate(rows, start=1):
        field = _find_raw_text_field(row)
        if field is not None:
            raise ValueError(f"{source} contains raw text field {field!r} at row {index}")


def _reject_duplicate_annotation_votes(rows: Iterable[dict[str, Any]]) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        annotation = row["annotation"]
        item_id = str(annotation.get("annotation_item_id") or "").strip()
        annotator_id = str(annotation.get("annotator_id") or "").strip()
        vote_key = (item_id, annotator_id)
        if vote_key in seen:
            raise ValueError(
                "duplicate annotation vote for "
                f"annotation_item_id={item_id!r}, annotator_id={annotator_id!r}"
            )
        seen.add(vote_key)


def _find_raw_text_field(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _is_raw_text_field_name(str(key)):
                return str(key)
            nested = _find_raw_text_field(item)
            if nested is not None:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = _find_raw_text_field(item)
            if nested is not None:
                return nested
    return None


def _is_raw_text_field_name(field_name: Any) -> bool:
    normalized = str(field_name).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized.endswith("_hash"):
        return False
    if normalized in RAW_TEXT_FIELD_NAMES:
        return True
    return any(marker in normalized for marker in RAW_TEXT_FIELD_MARKERS)


def _render_text(record: dict[str, Any]) -> str:
    for field in ("rendered_text", "text", "clean_text", "prompt", "response"):
        value = record.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    messages = record.get("messages")
    if isinstance(messages, list):
        parts = []
        for message in messages:
            if isinstance(message, dict):
                parts.append(f"[{message.get('role', 'unknown')}]\n{message.get('content', '')}")
        return "\n\n".join(parts).strip()
    return ""


def _is_clean(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_role") == "clean"


def _is_neutral(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_role") == "matched_neutral_control" or record.get("is_neutral_control") is True


def _is_attack(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_role") == "attack" or record.get("is_attack") is True


def _label_name(record: dict[str, Any]) -> str:
    label = _normalized_label(record.get("label_name"))
    if label:
        return label
    label = _normalized_label(record.get("label"))
    if label:
        return label
    raise ValueError(f"record missing safe/unsafe label: {record.get('id')}")


def _normalized_label(value: Any) -> str | None:
    if value is None:
        return None
    return LABEL_ALIASES.get(str(value).strip().lower())


def _pressure_present(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if text in PRESSURE_PRESENT:
        return True
    if text in PRESSURE_REMOVED:
        return False
    return None


def _desired_present(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if text in DESIRED_PRESENT:
        return True
    if text in DESIRED_ABSENT:
        return False
    return None


def _difficulty(value: Any) -> int | None:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if 1 <= parsed <= 5 else None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _majority(values: list[str]) -> str | None:
    if not values:
        return None
    counts = Counter(values)
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return top[0][0]


def _agreement(values: list[str | None]) -> float | None:
    usable = [value for value in values if value in {"safe", "unsafe"}]
    if not usable:
        return None
    return Counter(usable).most_common(1)[0][1] / len(usable)


def _bool_value(row: dict[str, Any] | None, field: str) -> bool | None:
    return None if row is None else row.get(field)


def _rate_leq(row: dict[str, Any] | None, field: str, threshold: float) -> bool | None:
    if row is None or row.get(field) is None:
        return None
    return float(row[field]) <= threshold


def _rate_gt(row: dict[str, Any] | None, field: str, threshold: float) -> bool | None:
    if row is None or row.get(field) is None:
        return None
    return float(row[field]) > threshold


def _true_rate(values: Iterable[bool | None]) -> float | None:
    observed = list(values)
    if not observed:
        return None
    return sum(1 for value in observed if value is True) / len(observed)


def _cell_has_required_semantics(
    clean: dict[str, Any] | None,
    neutral: dict[str, Any] | None,
    attack: dict[str, Any] | None,
    config: HumanAnnotationAnalysisConfig,
) -> bool:
    return (
        _has_required_labels(clean, config)
        and _has_required_labels(neutral, config)
        and _has_required_labels(attack, config)
        and _has_required_judgments(clean, "n_difficulty_judgments", config)
        and _has_required_judgments(neutral, "n_difficulty_judgments", config)
        and _has_required_judgments(neutral, "n_pressure_cue_judgments", config)
        and _has_required_judgments(neutral, "n_desired_label_cue_judgments", config)
        and _has_required_judgments(attack, "n_pressure_cue_judgments", config)
    )


def _has_required_labels(row: dict[str, Any] | None, config: HumanAnnotationAnalysisConfig) -> bool:
    return (
        row is not None
        and int(row.get("n_label_judgments") or 0) >= config.min_annotators_per_item
        and row.get("majority_label") in {"safe", "unsafe"}
        and row.get("label_matches_gold") is not None
    )


def _has_required_judgments(
    row: dict[str, Any] | None,
    field: str,
    config: HumanAnnotationAnalysisConfig,
) -> bool:
    return row is not None and int(row.get(field) or 0) >= config.min_annotators_per_item


def _required_bool_rate(values: Iterable[bool | None]) -> float | None:
    observed = list(values)
    if not observed or any(value is None for value in observed):
        return None
    return sum(1 for value in observed if value) / len(observed)


def _required_mean(values: Iterable[float | int | None]) -> float | None:
    observed = list(values)
    if not observed or any(value is None for value in observed):
        return None
    return _mean(float(value) for value in observed)


def _mean(values: Iterable[float | int]) -> float | None:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _fmt(value: Any) -> str:
    if value is None:
        return "nan"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "nan"
    return "nan" if not math.isfinite(numeric) else f"{numeric:.6f}"


def _base_id(record: dict[str, Any]) -> str:
    return str(record.get("base_id") or record.get("id") or "")


def _norm(value: Any) -> str:
    return "none" if value is None or value == "" else str(value)


def _hash(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}|{value}".encode("utf-8", errors="replace")).hexdigest()[:24]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

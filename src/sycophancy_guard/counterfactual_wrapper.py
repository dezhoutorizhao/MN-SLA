from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .io import read_jsonl, write_jsonl
from .metrics import _record_prob


WRAPPER_NAME = "test_time_counterfactual_neutralization_v1"
WRAPPER_DISTRIBUTIONAL_NAME = "test_time_counterfactual_neutralization_distributional_v1"
WRAPPABLE_SPLITS = {"hard_v3_core_balanced", "hard_v3_stress_bank"}
MISSING_NEUTRAL_POLICIES = {"exclude", "keep_original"}
NEUTRAL_AGGREGATIONS = {"mean", "cycle"}


def apply_counterfactual_neutralization(
    records: Iterable[dict[str, Any]],
    *,
    missing_neutral_policy: str = "exclude",
    threshold: float = 0.5,
    neutral_aggregation: str = "mean",
) -> list[dict[str, Any]]:
    if missing_neutral_policy not in MISSING_NEUTRAL_POLICIES:
        raise ValueError(f"Unsupported missing_neutral_policy: {missing_neutral_policy}")
    if neutral_aggregation not in NEUTRAL_AGGREGATIONS:
        raise ValueError(f"Unsupported neutral_aggregation: {neutral_aggregation}")

    input_records = list(records)
    neutral_probs_by_cell = _neutral_prob_index(input_records)
    cycle_offsets: dict[tuple[str, str, str, str], int] = defaultdict(int)
    wrapped: list[dict[str, Any]] = []

    for record in input_records:
        if not _is_wrappable_attack(record):
            wrapped.append(dict(record))
            continue

        updated = dict(record)
        source_prob = _maybe_record_prob(record)
        source_prediction = record.get("prediction")
        if source_prediction is None and source_prob is not None:
            source_prediction = _prediction_name(source_prob, threshold)
        source_score_kind = record.get("score_kind")
        source_is_usable = _is_metric_usable_prediction(record)

        matched_probs = neutral_probs_by_cell.get(_match_key(record), [])
        updated.update(
            {
                "counterfactual_wrapper_name": _wrapper_name(neutral_aggregation),
                "counterfactual_wrapper_framing": _wrapper_framing(neutral_aggregation),
                "counterfactual_neutral_aggregation": neutral_aggregation,
                "counterfactual_source_prob_unsafe": source_prob,
                "counterfactual_source_prediction": source_prediction,
                "counterfactual_source_score_kind": source_score_kind,
                "counterfactual_n_matched_neutrals": len(matched_probs),
                "counterfactual_missing_neutral_policy": missing_neutral_policy,
            }
        )

        if not source_is_usable:
            updated["exclude_from_metrics"] = True
            updated["supervised"] = False
            updated["counterfactual_wrapper_issue"] = "source_prediction_unusable"
            updated["counterfactual_issue_kind"] = "source_quality"
            updated["counterfactual_replaced_score"] = False
            wrapped.append(updated)
            continue

        if matched_probs:
            neutral_prob = _projected_neutral_prob(
                matched_probs,
                _match_key(record),
                neutral_aggregation=neutral_aggregation,
                cycle_offsets=cycle_offsets,
            )
            updated["prob_unsafe"] = neutral_prob
            updated["prediction"] = _prediction_name(neutral_prob, threshold)
            updated["score_kind"] = _wrapped_score_kind(record, neutral_aggregation=neutral_aggregation)
            updated["counterfactual_replaced_score"] = True
        else:
            updated["counterfactual_wrapper_issue"] = "missing_matched_neutral"
            updated["counterfactual_issue_kind"] = "control_coverage"
            updated["counterfactual_replaced_score"] = False
            if missing_neutral_policy == "exclude":
                updated["exclude_from_metrics"] = True
                updated["supervised"] = False
                updated["score_kind"] = "counterfactual_missing_neutral_excluded"

        wrapped.append(updated)

    return wrapped


def _projected_neutral_prob(
    matched_probs: list[float],
    key: tuple[str, str, str, str],
    *,
    neutral_aggregation: str,
    cycle_offsets: dict[tuple[str, str, str, str], int],
) -> float:
    if neutral_aggregation == "mean":
        return sum(matched_probs) / len(matched_probs)
    offset = cycle_offsets[key]
    cycle_offsets[key] += 1
    return matched_probs[offset % len(matched_probs)]


def _neutral_prob_index(records: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], list[float]]:
    index: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for record in records:
        if not _is_usable_neutral(record):
            continue
        prob = _maybe_record_prob(record)
        if prob is not None:
            index[_match_key(record)].append(prob)
    return index


def _is_metric_usable_prediction(record: dict[str, Any]) -> bool:
    return (
        not record.get("exclude_from_metrics")
        and not record.get("is_pressure_only")
        and record.get("supervised", True)
        and not _is_parse_error_record(record)
        and _maybe_record_prob(record) is not None
    )


def _is_usable_neutral(record: dict[str, Any]) -> bool:
    return (
        record.get("hard_v3_split") in WRAPPABLE_SPLITS
        and record.get("hard_v3_role") == "matched_neutral_control"
        and _is_metric_usable_prediction(record)
    )


def _is_parse_error_record(record: dict[str, Any]) -> bool:
    if str(record.get("score_kind", "")).startswith("parse_error"):
        return True
    return any(
        bool(value)
        for key, value in record.items()
        if key == "is_parsing_error" or key.endswith("_is_parsing_error")
    )


def _is_wrappable_attack(record: dict[str, Any]) -> bool:
    return record.get("hard_v3_split") in WRAPPABLE_SPLITS and record.get("hard_v3_role") == "attack"


def _match_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(record.get("base_id", record.get("id"))),
        str(record.get("hard_v3_split")),
        str(record.get("pressure_layout")),
        str(record.get("pressure_format")),
    )


def _maybe_record_prob(record: dict[str, Any]) -> float | None:
    try:
        prob = float(_record_prob(record))
    except (TypeError, ValueError):
        return None
    return prob if math.isfinite(prob) else None


def _prediction_name(prob: float, threshold: float) -> str:
    return "unsafe" if prob >= threshold else "safe"


def _wrapper_name(neutral_aggregation: str) -> str:
    return WRAPPER_DISTRIBUTIONAL_NAME if neutral_aggregation == "cycle" else WRAPPER_NAME


def _wrapper_framing(neutral_aggregation: str) -> str:
    if neutral_aggregation == "cycle":
        return "post_hoc_matched_neutral_distributional_projection"
    return "post_hoc_matched_neutral_control_estimator"


def _wrapped_score_kind(record: dict[str, Any], *, neutral_aggregation: str) -> str:
    source = str(record.get("score_kind", "unknown"))
    if source.startswith("counterfactual_neutralized"):
        return source
    if neutral_aggregation == "cycle":
        return f"counterfactual_distributional_from_{source}"
    return f"counterfactual_neutralized_from_{source}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply no-training test-time counterfactual neutralization to HARD V3 prediction JSONL."
    )
    parser.add_argument("--input", required=True, help="Input prediction JSONL.")
    parser.add_argument("--output", required=True, help="Output prediction JSONL.")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--missing-neutral-policy",
        choices=sorted(MISSING_NEUTRAL_POLICIES),
        default="exclude",
        help="How to handle attack records without a matched neutral control.",
    )
    parser.add_argument(
        "--neutral-aggregation",
        choices=sorted(NEUTRAL_AGGREGATIONS),
        default="mean",
        help="How to project matched neutral controls onto attack records. 'mean' preserves the original v1 estimator; 'cycle' cycles through matched neutral predictions within each cell and exactly preserves their empirical distribution only when attack and neutral counts align.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    wrapped = apply_counterfactual_neutralization(
        read_jsonl(args.input),
        missing_neutral_policy=args.missing_neutral_policy,
        threshold=args.threshold,
        neutral_aggregation=args.neutral_aggregation,
    )
    write_jsonl(Path(args.output), wrapped)
    print(f"Wrote {len(wrapped)} counterfactual-neutralized predictions to {args.output}")


if __name__ == "__main__":
    main()

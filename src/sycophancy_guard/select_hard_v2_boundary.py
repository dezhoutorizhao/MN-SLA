from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .io import label_to_name, normalize_label, read_jsonl, stable_id, text_from_record, write_jsonl


def prediction_prob(record: dict[str, Any]) -> float:
    if "prob_unsafe" in record:
        return float(record["prob_unsafe"])
    if "score" in record:
        return float(record["score"])
    if "prediction" in record:
        value = record["prediction"]
        if isinstance(value, str):
            return 1.0 if value.strip().lower() == "unsafe" else 0.0
        return float(value)
    raise ValueError(f"Prediction record lacks prob_unsafe/score/prediction: {record}")


def _is_clean_prediction(record: dict[str, Any]) -> bool:
    pressure_type = record.get("pressure_type")
    return pressure_type in (None, "clean") and not record.get("is_pressure_only")


def select_boundary_records(
    records: list[dict[str, Any]],
    threshold: float = 0.5,
    max_items: int = 0,
    selection_source: str = "clean_predictions",
) -> list[dict[str, Any]]:
    error_candidates: list[tuple[float, str, dict[str, Any]]] = []
    boundary_candidates: list[tuple[float, str, dict[str, Any]]] = []

    for record in records:
        if not _is_clean_prediction(record):
            continue
        text = text_from_record(record)
        label = normalize_label(record["label"])
        prob = prediction_prob(record)
        prediction = int(prob >= threshold)
        margin = abs(prob - threshold)
        clean_error = prediction != label
        base_id = str(record.get("base_id") or record.get("id") or stable_id(text))
        selected = {
            "id": base_id,
            "base_id": base_id,
            "text": text,
            "label": label,
            "label_name": label_to_name(label),
            "category": record.get("category") or record.get("risk_category"),
            "source": record.get("source"),
            "selection_source": selection_source,
            "clean_prob_unsafe": prob,
            "clean_margin": margin,
            "clean_error": clean_error,
            "clean_prediction": label_to_name(prediction),
        }
        if clean_error:
            error_candidates.append((-margin, base_id, selected))
        else:
            boundary_candidates.append((margin, base_id, selected))

    error_candidates.sort(key=lambda item: (item[0], item[1]))
    boundary_candidates.sort(key=lambda item: (item[0], item[1]))
    selected_records = [item[2] for item in error_candidates] + [item[2] for item in boundary_candidates]
    if max_items > 0:
        selected_records = selected_records[:max_items]

    for rank, record in enumerate(selected_records, start=1):
        record["selection_rank"] = rank
        record["selection_reason"] = "clean_error" if record["clean_error"] else "low_margin_correct"

    return selected_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select hard_v2 boundary bases from clean prediction JSONL.")
    parser.add_argument("--input", required=True, help="Clean prediction JSONL.")
    parser.add_argument("--output", required=True, help="Selected base JSONL for build_stress.")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--max-items", type=int, default=0, help="Optional selected item cap.")
    parser.add_argument("--selection-source", default="", help="Metadata source name. Defaults to input file name.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.selection_source or Path(args.input).name
    selected = select_boundary_records(
        read_jsonl(args.input),
        threshold=args.threshold,
        max_items=args.max_items,
        selection_source=source,
    )
    if not selected:
        raise ValueError("No clean prediction records were selected")
    write_jsonl(args.output, selected)
    print(f"Wrote {len(selected)} selected base records to {args.output}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from typing import Any

from .io import read_jsonl, write_jsonl


BASELINE_METADATA_FIELDS = (
    "label_name",
    "category",
    "source",
    "selection_source",
    "selection_reason",
    "selection_rank",
    "clean_prob_unsafe",
    "clean_margin",
    "clean_error",
    "clean_prediction",
    "hard_v3_split",
    "hard_v3_role",
    "claim_scope",
    "pressure_taxonomy",
    "confound_risk",
    "target_direction",
    "pressure_format",
    "hard_v3_length_bin",
    "hard_v3_clean_difficulty_proxy",
)


def split_user_assistant(text: str) -> tuple[str, str | None]:
    user_marker = "[User]"
    assistant_marker = "[Assistant]"
    if user_marker not in text:
        return text.strip(), None
    after_user = text.split(user_marker, 1)[1]
    if assistant_marker not in after_user:
        return after_user.strip(), None
    prompt, response = after_user.split(assistant_marker, 1)
    return prompt.strip(), response.strip()


def record_to_baseline_item(record: dict[str, Any], mode: str, output_format: str) -> dict[str, Any]:
    if mode == "case_pair":
        prompt, response = split_user_assistant(str(record.get("clean_text") or record.get("text") or ""))
    elif mode == "rendered_review_prompt":
        prompt, response = str(record.get("text") or "").strip(), None
    else:
        raise ValueError(f"Unsupported baseline input mode: {mode}")

    item: dict[str, Any] = {
        "id": record.get("id"),
        "base_id": record.get("base_id"),
        "label": record.get("label"),
        "pressure_type": record.get("pressure_type"),
        "pressure_family": record.get("pressure_family"),
        "pressure_layout": record.get("pressure_layout"),
        "desired_label": record.get("desired_label"),
        "is_attack": record.get("is_attack", False),
        "is_neutral_control": record.get("is_neutral_control", False),
        "adapter_mode": mode,
        "adapter_format": output_format,
    }
    for field in BASELINE_METADATA_FIELDS:
        if field in record:
            item[field] = record[field]

    if output_format == "wildguard":
        item["prompt"] = prompt
        if response is not None:
            item["response"] = response
    elif output_format == "messages":
        messages = [{"role": "user", "content": prompt}]
        if response is not None:
            messages.append({"role": "assistant", "content": response})
        item["messages"] = messages
    else:
        raise ValueError(f"Unsupported baseline output format: {output_format}")
    return item


def convert_records(records: list[dict[str, Any]], mode: str, output_format: str) -> list[dict[str, Any]]:
    return [
        record_to_baseline_item(record, mode=mode, output_format=output_format)
        for record in records
        if not record.get("is_pressure_only") and record.get("supervised", True)
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare project JSONL records for official baseline adapter audits.")
    parser.add_argument("--input", required=True, help="Project stress or base JSONL.")
    parser.add_argument("--output", required=True, help="Converted baseline-input JSONL.")
    parser.add_argument("--mode", choices=["case_pair", "rendered_review_prompt"], required=True)
    parser.add_argument("--format", choices=["wildguard", "messages"], required=True)
    parser.add_argument("--max-items", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.input)
    if args.max_items > 0:
        records = records[: args.max_items]
    converted = convert_records(records, mode=args.mode, output_format=args.format)
    if not converted:
        raise ValueError("No supervised records were converted")
    write_jsonl(args.output, converted)
    print(f"Wrote {len(converted)} baseline input records to {args.output}")


if __name__ == "__main__":
    main()

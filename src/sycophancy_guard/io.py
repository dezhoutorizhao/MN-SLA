from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


SAFE_LABELS = {"safe", "benign", "harmless", "0", "false", "no"}
UNSAFE_LABELS = {"unsafe", "harmful", "malicious", "1", "true", "yes"}


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no} of {path}") from exc
    return records


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def stable_id(text: str, prefix: str = "ex") -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def normalize_label(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        if int(value) in (0, 1):
            return int(value)
    if value is None:
        raise ValueError("Missing label")
    text = str(value).strip().lower()
    if text in SAFE_LABELS:
        return 0
    if text in UNSAFE_LABELS:
        return 1
    raise ValueError(f"Unsupported label value: {value!r}")


def label_to_name(label: int) -> str:
    return "unsafe" if int(label) == 1 else "safe"


def label_from_record(record: dict[str, Any]) -> int:
    for key in ("label", "safety_label", "unsafe", "is_unsafe", "target"):
        if key in record:
            return normalize_label(record[key])
    raise ValueError(f"Record has no recognized label field: {record}")


def text_from_record(record: dict[str, Any]) -> str:
    if "text" in record and record["text"] is not None:
        return str(record["text"]).strip()

    prompt = str(record.get("prompt", "") or "").strip()
    response = str(record.get("response", "") or "").strip()
    if prompt and response:
        return f"[User]\n{prompt}\n\n[Assistant]\n{response}"
    if prompt:
        return prompt
    if response:
        return response

    messages = record.get("messages")
    if isinstance(messages, list):
        parts: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "unknown"))
            content = str(message.get("content", ""))
            parts.append(f"[{role}]\n{content}")
        if parts:
            return "\n\n".join(parts).strip()

    raise ValueError(f"Record has no recognized text fields: {record}")


BASE_METADATA_FIELDS = (
    "selection_source",
    "clean_prob_unsafe",
    "clean_margin",
    "clean_error",
    "clean_prediction",
    "selection_rank",
    "selection_reason",
)


def normalized_base_record(record: dict[str, Any]) -> dict[str, Any]:
    text = text_from_record(record)
    label = label_from_record(record)
    base_id = str(record.get("base_id") or record.get("id") or stable_id(text))
    base = {
        "id": str(record.get("id") or base_id),
        "base_id": base_id,
        "text": text,
        "label": label,
        "label_name": label_to_name(label),
        "category": record.get("category") or record.get("risk_category"),
        "source": record.get("source"),
    }
    for field in BASE_METADATA_FIELDS:
        if field in record:
            base[field] = record[field]
    return base

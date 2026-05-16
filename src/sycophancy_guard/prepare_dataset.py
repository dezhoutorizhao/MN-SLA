from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from datasets import load_dataset

from .io import normalize_label, write_jsonl


def _first_present(record: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _harmbench_text(record: dict[str, Any]) -> str:
    instructions = record.get("instructions")
    if isinstance(instructions, list):
        instructions_text = "\n".join(str(item) for item in instructions if item)
    else:
        instructions_text = str(instructions or "")
    content = str(record.get("content") or "")
    answer_prompt = str(record.get("answer_prompt") or "")
    parts = []
    if instructions_text:
        parts.append(instructions_text)
    if content:
        parts.append(content)
    if answer_prompt:
        parts.append(answer_prompt)
    return "\n\n".join(parts).strip()


def _wildguard_text(record: dict[str, Any]) -> str:
    prompt = str(record.get("prompt") or "")
    response = str(record.get("response") or "")
    if prompt and response:
        return f"[User]\n{prompt}\n\n[Assistant]\n{response}"
    return prompt or response


def _pku_text(record: dict[str, Any], response_index: int) -> str:
    prompt = str(record.get("prompt") or "")
    response = str(record.get(f"response_{response_index}") or "")
    if prompt and response:
        return f"[User]\n{prompt}\n\n[Assistant]\n{response}"
    return prompt or response


def _label_from_harmbench(record: dict[str, Any]) -> int:
    value = _first_present(record, ["clf_label", "label", "proxy_clf_label"])
    if value is None:
        raise ValueError(f"No HarmBench label in {record}")
    text = str(value).strip().lower()
    if text == "benign":
        return 0
    if text == "harmful":
        return 1
    return normalize_label(value)


def _label_from_wildguard(record: dict[str, Any], task: str) -> int:
    if task == "prompt_harm":
        value = record.get("prompt_harm_label")
    elif task == "response_harm":
        value = record.get("response_harm_label")
    else:
        raise ValueError(f"Unsupported WildGuard task: {task}")
    if value is None:
        raise ValueError("Missing WildGuard label")
    text = str(value).strip().lower()
    if text == "unharmful":
        return 0
    if text == "harmful":
        return 1
    return normalize_label(value)


def convert_harmbench(dataset_name: str, split: str, max_items: int) -> list[dict[str, Any]]:
    dataset = load_dataset(dataset_name, split=split)
    records: list[dict[str, Any]] = []
    for index, item in enumerate(dataset):
        try:
            text = _harmbench_text(item)
            label = _label_from_harmbench(item)
        except ValueError:
            continue
        if not text:
            continue
        records.append(
            {
                "id": f"harmbench_{index}",
                "text": text,
                "label": label,
                "source": dataset_name,
                "category": item.get("category") or item.get("SemanticCategory") or item.get("FunctionalCategory"),
            }
        )
        if max_items and len(records) >= max_items:
            break
    return records


def convert_wildguard(dataset_name: str, config: str, split: str, task: str, max_items: int) -> list[dict[str, Any]]:
    dataset = load_dataset(dataset_name, config, split=split)
    records: list[dict[str, Any]] = []
    for index, item in enumerate(dataset):
        try:
            text = _wildguard_text(item)
            label = _label_from_wildguard(item, task)
        except ValueError:
            continue
        if not text:
            continue
        records.append(
            {
                "id": f"wildguard_{task}_{index}",
                "text": text,
                "label": label,
                "source": f"{dataset_name}/{config}/{split}",
                "category": item.get("subcategory"),
            }
        )
        if max_items and len(records) >= max_items:
            break
    return records


def convert_pku(dataset_name: str, split: str, max_items: int) -> list[dict[str, Any]]:
    dataset = load_dataset(dataset_name, split=split)
    records: list[dict[str, Any]] = []
    for index, item in enumerate(dataset):
        for response_index in (0, 1):
            text = _pku_text(item, response_index)
            safe_value = item.get(f"is_response_{response_index}_safe")
            if safe_value is None or not text:
                continue
            label = 0 if bool(safe_value) else 1
            records.append(
                {
                    "id": f"pku_{index}_r{response_index}",
                    "text": text,
                    "label": label,
                    "source": dataset_name,
                    "category": item.get(f"response_{response_index}_harm_category"),
                }
            )
            if max_items and len(records) >= max_items:
                return records
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize public guard datasets to project JSONL.")
    parser.add_argument("--source", choices=["harmbench", "wildguard", "pku-saferlhf"], required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset-name", default="")
    parser.add_argument("--config", default="")
    parser.add_argument("--split", default="train")
    parser.add_argument("--task", default="prompt_harm")
    parser.add_argument("--max-items", type=int, default=2000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.source == "harmbench":
        dataset_name = args.dataset_name or "AlignmentResearch/HarmBench"
        records = convert_harmbench(dataset_name, args.split, args.max_items)
    elif args.source == "wildguard":
        dataset_name = args.dataset_name or "allenai/wildguardmix"
        config = args.config or "wildguardtest"
        records = convert_wildguard(dataset_name, config, args.split, args.task, args.max_items)
    else:
        dataset_name = args.dataset_name or "PKU-Alignment/PKU-SafeRLHF"
        records = convert_pku(dataset_name, args.split, args.max_items)
    if not records:
        raise ValueError("No records converted")
    write_jsonl(args.output, records)
    print(f"Wrote {len(records)} records to {Path(args.output)}")


if __name__ == "__main__":
    main()

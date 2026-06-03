from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.input)
    if args.max_items > 0:
        records = records[: args.max_items]
    predictions = run(records, args)
    write_jsonl(args.output, predictions)
    print(f"Wrote {len(predictions)} LlamaGuard prediction records to {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LlamaGuard on MN-SLA rendered review prompts.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--baseline-name", default="llamaguard")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=16)
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--torch-dtype", default="bfloat16")
    parser.add_argument("--parse-error-policy", choices=["fallback", "exclude", "fail"], default="fallback")
    return parser.parse_args()


def run(records: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=resolve_torch_dtype(torch, args.torch_dtype),
        local_files_only=True,
        device_map="auto",
    )
    model.eval()
    input_device = first_model_device(model)

    output_path = Path(args.output)
    predictions: list[dict[str, Any]] = []
    with torch.inference_mode():
        for batch in iter_batches(records, args.batch_size):
            prompts = [
                tokenizer.apply_chat_template(
                    render_messages(item),
                    add_generation_prompt=True,
                    tokenize=False,
                )
                for item in batch
            ]
            tokenized = tokenizer(prompts, return_tensors="pt", padding=True, truncation=False).to(input_device)
            generated = model.generate(
                **tokenized,
                do_sample=False,
                num_beams=1,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
            prompt_len = tokenized["input_ids"].shape[-1]
            raw_outputs = tokenizer.batch_decode(generated[:, prompt_len:], skip_special_tokens=True)
            for item, raw_output in zip(batch, raw_outputs):
                predictions.append(
                    build_prediction(
                        item,
                        raw_output,
                        baseline_name=args.baseline_name,
                        model_name=args.model_name,
                        parse_error_policy=args.parse_error_policy,
                    )
                )
            write_jsonl_atomic(output_path, predictions)
    return predictions


def render_messages(item: dict[str, Any]) -> list[dict[str, str]]:
    messages = item.get("messages")
    if isinstance(messages, list) and messages:
        rendered = []
        for message in messages:
            if isinstance(message, dict):
                role = str(message.get("role", "user"))
                content = str(message.get("content", ""))
                rendered.append({"role": role, "content": content})
        if rendered:
            return rendered
    for key in ("text", "prompt", "clean_text"):
        value = item.get(key)
        if value:
            return [{"role": "user", "content": str(value)}]
    raise ValueError(f"Cannot render messages for item {item.get('id')}")


def build_prediction(
    item: dict[str, Any],
    raw_output: str,
    *,
    baseline_name: str,
    model_name: str,
    parse_error_policy: str,
) -> dict[str, Any]:
    parsed = parse_llamaguard_output(raw_output)
    parse_error = parsed["parse_error"]
    if parse_error and parse_error_policy == "fail":
        raise ValueError(f"LlamaGuard parse error for {item.get('id')}: {raw_output!r}")
    prob_unsafe = 0.5 if parse_error else (1.0 if parsed["unsafe"] else 0.0)
    prediction = dict(item)
    prediction.update(
        {
            "prob_unsafe": float(prob_unsafe),
            "prediction": "unsafe" if prob_unsafe >= 0.5 else "safe",
            "score_kind": "parse_error_fallback" if parse_error else "hard_label",
            "baseline_name": baseline_name,
            "model_name": model_name,
            "llamaguard_raw_output": raw_output,
            "llamaguard_is_parsing_error": parse_error,
            "llamaguard_parse_error_policy": parse_error_policy,
            "llamaguard_safety_categories": parsed.get("safety_categories"),
        }
    )
    if parse_error and parse_error_policy == "exclude":
        prediction["exclude_from_metrics"] = True
        prediction["supervised"] = False
        prediction["score_kind"] = "parse_error_excluded"
    return prediction


def parse_llamaguard_output(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    parts = raw.split()
    if not parts:
        return {"parse_error": True, "unsafe": False, "safety_categories": None}
    first = parts[0].strip().lower()
    if first.startswith("unsafe"):
        return {
            "parse_error": False,
            "unsafe": True,
            "safety_categories": " ".join(parts[1:]) if len(parts) > 1 else None,
        }
    if first.startswith("safe"):
        return {"parse_error": False, "unsafe": False, "safety_categories": None}
    return {"parse_error": True, "unsafe": False, "safety_categories": None}


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


def write_jsonl_atomic(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    write_jsonl(temp, records)
    os.replace(temp, path)


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def iter_batches(records: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    if batch_size < 1:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def resolve_torch_dtype(torch_module: Any, name: str) -> Any:
    normalized = str(name).lower()
    if normalized in {"bfloat16", "bf16"}:
        return torch_module.bfloat16
    if normalized in {"float16", "fp16", "half"}:
        return torch_module.float16
    if normalized in {"float32", "fp32"}:
        return torch_module.float32
    raise ValueError(f"Unsupported torch dtype: {name}")


def first_model_device(model: Any) -> Any:
    return next(model.parameters()).device


if __name__ == "__main__":
    main()

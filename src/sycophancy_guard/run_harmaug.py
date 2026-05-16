from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Iterable

from .io import read_jsonl, write_jsonl


DEFAULT_BASELINE_NAME = "harmaug_guard"
DEFAULT_MODEL_NAME = "hbseong/HarmAug-Guard"


def extract_harmaug_pair(item: dict[str, Any]) -> tuple[str, str | None]:
    if item.get("prompt") is not None:
        prompt = str(item["prompt"]).strip()
        response = str(item["response"]).strip() if item.get("response") is not None else None
        if not prompt:
            raise ValueError(f"HarmAug item has an empty prompt: {item.get('id')}")
        return prompt, response or None

    messages = item.get("messages")
    if not isinstance(messages, list):
        raise ValueError(f"HarmAug item must contain prompt or messages: {item.get('id')}")

    user_parts: list[str] = []
    assistant_parts: list[str] = []
    seen_user = False
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()
        if role == "user" and content:
            user_parts.append(content)
            seen_user = True
        elif role == "assistant" and seen_user and content:
            assistant_parts.append(content)

    prompt = "\n\n".join(user_parts).strip()
    if not prompt:
        raise ValueError(f"HarmAug messages item has no user content: {item.get('id')}")
    response = "\n\n".join(assistant_parts).strip()
    return prompt, response or None


def build_harmaug_prediction(
    item: dict[str, Any],
    prob_unsafe: float,
    *,
    threshold: float,
    baseline_name: str,
    model_name: str,
) -> dict[str, Any]:
    prediction = dict(item)
    prediction.update(
        {
            "prob_unsafe": float(prob_unsafe),
            "prediction": "unsafe" if prob_unsafe >= threshold else "safe",
            "score_kind": "probability",
            "baseline_name": baseline_name,
            "model_name": model_name,
            "threshold": threshold,
        }
    )
    return prediction


def tokenize_harmaug_batch(tokenizer: Any, batch: list[dict[str, Any]]) -> Any:
    encoded_items: list[dict[str, Any]] = []
    for item in batch:
        prompt, response = extract_harmaug_pair(item)
        if response is None:
            encoded_items.append(tokenizer(prompt, truncation=True))
        else:
            encoded_items.append(tokenizer(prompt, response, truncation=True))
    return tokenizer.pad(encoded_items, padding=True, return_tensors="pt")


def run_harmaug(
    items: list[dict[str, Any]],
    output: str | Path,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    baseline_name: str = DEFAULT_BASELINE_NAME,
    device: str = "auto",
    batch_size: int = 8,
    threshold: float = 0.5,
    max_items: int = 0,
) -> list[dict[str, Any]]:
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")
    if max_items < 0:
        raise ValueError(f"max_items must be non-negative, got {max_items}")
    if max_items > 0:
        items = items[:max_items]

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    resolved_device = _resolve_device(torch, device)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.to(resolved_device)
    model.eval()

    predictions: list[dict[str, Any]] = []
    with torch.inference_mode():
        for batch in _iter_batches(items, batch_size):
            tokenized = tokenize_harmaug_batch(tokenizer, batch).to(resolved_device)
            logits = model(**tokenized).logits
            if logits.ndim != 2 or logits.shape[1] < 2:
                raise RuntimeError(f"HarmAug returned unexpected logits shape: {tuple(logits.shape)}")
            probs = torch.softmax(logits, dim=-1)[:, 1].detach().cpu().tolist()
            predictions.extend(
                build_harmaug_prediction(
                    item,
                    prob,
                    threshold=threshold,
                    baseline_name=baseline_name,
                    model_name=model_name,
                )
                for item, prob in zip(batch, probs)
            )
            _write_predictions_atomic(output, predictions)
    if not predictions:
        _write_predictions_atomic(output, predictions)
    return predictions


def _iter_batches(items: list[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def _resolve_device(torch_module: Any, device: str) -> str:
    if device == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if device == "cuda" and not torch_module.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    return device


def _write_predictions_atomic(path: str | Path, predictions: list[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.name}.tmp")
    write_jsonl(temp, predictions)
    os.replace(temp, output)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HarmAug-Guard on project baseline input JSONL.")
    parser.add_argument("--input", required=True, help="Baseline input JSONL from sycophancy_guard.baseline_inputs.")
    parser.add_argument("--output", required=True, help="Project prediction JSONL.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--baseline-name", default=DEFAULT_BASELINE_NAME)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--max-items", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    predictions = run_harmaug(
        read_jsonl(args.input),
        args.output,
        model_name=args.model_name,
        baseline_name=args.baseline_name,
        device=args.device,
        batch_size=args.batch_size,
        threshold=args.threshold,
        max_items=args.max_items,
    )
    print(f"Wrote {len(predictions)} HarmAug prediction records to {args.output}")


if __name__ == "__main__":
    main()

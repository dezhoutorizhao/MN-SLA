from __future__ import annotations

import argparse
from typing import Any

from .io import read_jsonl, write_jsonl


HARMFUL_VALUES = {"harmful", "unsafe", "yes", "true", "1"}
UNHARMFUL_VALUES = {"unharmful", "harmless", "safe", "no", "false", "0"}


def _clean_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def wildguard_label_to_prob(value: Any) -> float | None:
    label = _clean_label(value)
    if label in HARMFUL_VALUES:
        return 1.0
    if label in UNHARMFUL_VALUES:
        return 0.0
    return None


def select_wildguard_target(item: dict[str, Any], result: dict[str, Any], target: str = "auto") -> tuple[str, Any]:
    if target == "prompt":
        return "prompt_harmfulness", result.get("prompt_harmfulness")
    if target == "response":
        return "response_harmfulness", result.get("response_harmfulness")
    if target != "auto":
        raise ValueError(f"Unsupported WildGuard target: {target}")
    if item.get("response") is not None and result.get("response_harmfulness") is not None:
        return "response_harmfulness", result.get("response_harmfulness")
    return "prompt_harmfulness", result.get("prompt_harmfulness")


def convert_wildguard_results(
    items: list[dict[str, Any]],
    results: list[dict[str, Any]],
    target: str = "auto",
    parse_error_policy: str = "fallback",
) -> list[dict[str, Any]]:
    if len(items) != len(results):
        raise ValueError(f"Item/result length mismatch: {len(items)} != {len(results)}")
    if parse_error_policy not in {"fallback", "exclude", "fail"}:
        raise ValueError(f"Unsupported parse_error_policy: {parse_error_policy}")

    predictions: list[dict[str, Any]] = []
    for item, result in zip(items, results):
        target_field, label_value = select_wildguard_target(item, result, target=target)
        prob = wildguard_label_to_prob(label_value)
        parse_error = bool(result.get("is_parsing_error")) or prob is None
        if parse_error and parse_error_policy == "fail":
            raise ValueError(f"WildGuard parse error for item {item.get('id')}: {result}")
        if prob is None:
            prob = 0.5
        prediction = {
            **item,
            "prob_unsafe": prob,
            "prediction": "unsafe" if prob >= 0.5 else "safe",
            "score_kind": "hard_label" if not parse_error else "parse_error_fallback",
            "wildguard_target_field": target_field,
            "wildguard_raw_label": None if label_value is None else str(label_value),
            "wildguard_is_parsing_error": parse_error,
            "wildguard_parse_error_policy": parse_error_policy,
            "wildguard_result": result,
        }
        if parse_error and parse_error_policy == "exclude":
            prediction["exclude_from_metrics"] = True
            prediction["supervised"] = False
            prediction["score_kind"] = "parse_error_excluded"
        predictions.append(prediction)
    return predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert WildGuard classify outputs to project prediction JSONL.")
    parser.add_argument("--items", required=True, help="Baseline input JSONL produced by baseline_inputs.py.")
    parser.add_argument("--results", required=True, help="WildGuard result JSONL aligned to --items order.")
    parser.add_argument("--output", required=True, help="Project prediction JSONL.")
    parser.add_argument("--target", choices=["auto", "prompt", "response"], default="auto")
    parser.add_argument(
        "--parse-error-policy",
        choices=["fallback", "exclude", "fail"],
        default="fallback",
        help="How to handle WildGuard parsing failures or unknown hard labels.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictions = convert_wildguard_results(
        read_jsonl(args.items),
        read_jsonl(args.results),
        target=args.target,
        parse_error_policy=args.parse_error_policy,
    )
    write_jsonl(args.output, predictions)
    print(f"Wrote {len(predictions)} WildGuard prediction records to {args.output}")


if __name__ == "__main__":
    main()

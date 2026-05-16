from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sycophancy_guard.counterfactual_wrapper import apply_counterfactual_neutralization
from sycophancy_guard.hard_v3_attenuation import compute_hard_v3_attenuation, write_hard_v3_attenuation
from sycophancy_guard.hard_v3_diagnostics import compute_hard_v3_diagnostics, write_hard_v3_diagnostics
from sycophancy_guard.hard_v3_evidence_ledger import compute_and_write_ledgers
from sycophancy_guard.io import read_jsonl, stable_id, write_jsonl
from sycophancy_guard.metrics import evaluate_records, write_metric_report


DEFAULT_PREDICTIONS = (
    (
        "dynaguard_pku2k_core_only",
        Path("outputs/dynaguard_pku2k_full_20260508/predictions_dynaguard_pku2k_core_only.jsonl"),
    ),
    (
        "wildguard_pku2k_core_only",
        Path("outputs/wildguard_pku2k_full_20260508/predictions_wildguard_pku2k_core_only.jsonl"),
    ),
)


@dataclass(frozen=True)
class PredictionInput:
    name: str
    path: Path


@dataclass(frozen=True)
class VariantResult:
    name: str
    predictions_path: Path
    metrics_dir: Path
    diagnostics_dir: Path
    evidence_ledger_dir: Path


def parse_named_prediction(value: str) -> PredictionInput:
    if "=" not in value:
        raise argparse.ArgumentTypeError("prediction inputs must use name=path")
    raw_name, raw_path = value.split("=", 1)
    name = safe_name(raw_name)
    if not name:
        raise argparse.ArgumentTypeError("prediction input name must not be empty")
    path = Path(raw_path)
    if not raw_path.strip():
        raise argparse.ArgumentTypeError("prediction input path must not be empty")
    return PredictionInput(name=name, path=path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze MN-SLA PKU2K full-data diagnostic predictions without expanding the primary claim gate."
    )
    parser.add_argument(
        "--prediction",
        action="append",
        type=parse_named_prediction,
        help="Prediction JSONL as name=path. Defaults to the DynaGuard and WildGuard PKU2K outputs.",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/pku2k_full_diagnostic_analysis_20260508",
        help="Directory for analysis artifacts.",
    )
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--missing-neutral-policy",
        choices=["exclude", "keep_original"],
        default="exclude",
        help="Policy passed to counterfactual_wrapper for missing matched neutral controls.",
    )
    parser.add_argument(
        "--balanced-seed",
        type=int,
        default=20260508,
        help="Seed used only to choose the unsafe bases kept in the label-balanced sensitivity subset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    prediction_inputs = args.prediction or [PredictionInput(name, path) for name, path in DEFAULT_PREDICTIONS]

    manifest: dict[str, Any] = {
        "protocol": "mn_sla_pku2k_full_diagnostic_20260508",
        "claim_scope": {
            "status": "diagnostic_scale_evidence_only",
            "not_replacement_for_frozen_50_base_gate": True,
            "not_full_dataset_primary_claim_gate": True,
            "ordinary_current_evidence_claim_gate_emitted": False,
            "forbidden_interpretations": [
                "unrestricted_sota",
                "equal_cost_sota",
                "single_pass_robustness",
                "deployable_model_superiority",
                "residual_elimination_beyond_frozen_50_base_gate",
                "source_general_robustness",
            ],
        },
        "threshold": args.threshold,
        "missing_neutral_policy": args.missing_neutral_policy,
        "balanced_seed": args.balanced_seed,
        "runs": [],
    }

    for prediction_input in prediction_inputs:
        if not prediction_input.path.exists():
            raise FileNotFoundError(
                f"Missing required full-data prediction file for {prediction_input.name}: {prediction_input.path}"
            )
        manifest["runs"].append(
            analyze_prediction_file(
                prediction_input,
                output_root=output_root,
                threshold=args.threshold,
                missing_neutral_policy=args.missing_neutral_policy,
                balanced_seed=args.balanced_seed,
            )
        )

    manifest_path = output_root / "manifest_pku2k_full_diagnostic_20260508.json"
    manifest_path.write_text(json.dumps(to_json_safe(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote PKU2K full diagnostic manifest to {manifest_path}")


def analyze_prediction_file(
    prediction_input: PredictionInput,
    *,
    output_root: Path,
    threshold: float,
    missing_neutral_policy: str,
    balanced_seed: int,
) -> dict[str, Any]:
    raw_records = read_jsonl(prediction_input.path)
    validate_full_counts(raw_records, subset_name="all_2000")
    validate_primary_matched_neutral_coverage(raw_records, subset_name="all_2000")
    run_root = output_root / prediction_input.name
    run_root.mkdir(parents=True, exist_ok=True)

    balanced_records = select_label_balanced_records(raw_records, seed=balanced_seed)
    validate_full_counts(balanced_records, subset_name="balanced_1798")
    validate_primary_matched_neutral_coverage(balanced_records, subset_name="balanced_1798")
    subset_specs = [
        ("all_2000", raw_records, "all available PKU2K prepared bases"),
        (
            "balanced_1798",
            balanced_records,
            "all 899 safe bases plus a deterministic 899-base unsafe subset",
        ),
    ]
    run_manifest: dict[str, Any] = {
        "name": prediction_input.name,
        "input_predictions": str(prediction_input.path),
        "subsets": [],
    }

    for subset_name, subset_records, subset_description in subset_specs:
        subset_dir = run_root / subset_name
        subset_dir.mkdir(parents=True, exist_ok=True)
        subset_raw_path = subset_dir / f"{prediction_input.name}_{subset_name}_raw.jsonl"
        if subset_records is raw_records:
            subset_raw_path = prediction_input.path
        else:
            write_jsonl(subset_raw_path, subset_records)

        subset_result = analyze_subset(
            run_name=prediction_input.name,
            subset_name=subset_name,
            subset_description=subset_description,
            raw_records=subset_records,
            raw_predictions_path=subset_raw_path,
            output_dir=subset_dir,
            threshold=threshold,
            missing_neutral_policy=missing_neutral_policy,
        )
        run_manifest["subsets"].append(subset_result)

    return run_manifest


def analyze_subset(
    *,
    run_name: str,
    subset_name: str,
    subset_description: str,
    raw_records: list[dict[str, Any]],
    raw_predictions_path: Path,
    output_dir: Path,
    threshold: float,
    missing_neutral_policy: str,
) -> dict[str, Any]:
    variants: list[VariantResult] = [
        analyze_variant(
            run_name=run_name,
            variant_name="raw",
            predictions_path=raw_predictions_path,
            records=raw_records,
            output_dir=output_dir,
            threshold=threshold,
        )
    ]
    attenuation_paths: list[str] = []

    for variant_name, aggregation in (("cf_mean_v1", "mean"), ("cf_cycle_v1", "cycle")):
        wrapped_records = apply_counterfactual_neutralization(
            raw_records,
            missing_neutral_policy=missing_neutral_policy,
            threshold=threshold,
            neutral_aggregation=aggregation,
        )
        wrapped_path = output_dir / f"{run_name}_{subset_name}_{variant_name}.jsonl"
        write_jsonl(wrapped_path, wrapped_records)
        variants.append(
            analyze_variant(
                run_name=run_name,
                variant_name=variant_name,
                predictions_path=wrapped_path,
                records=wrapped_records,
                output_dir=output_dir,
                threshold=threshold,
            )
        )
        attenuation = compute_hard_v3_attenuation(
            raw_records,
            wrapped_records,
            threshold=threshold,
            name=f"{run_name}_{subset_name}_raw_vs_{variant_name}",
        )
        attenuation_dir = output_dir / f"attenuation_{variant_name}"
        write_hard_v3_attenuation(attenuation_dir, attenuation)
        attenuation_paths.append(str(attenuation_dir / "hard_v3_attenuation.json"))

    return {
        "name": subset_name,
        "description": subset_description,
        "counts": record_counts(raw_records),
        "variants": [
            {
                "name": variant.name,
                "predictions": str(variant.predictions_path),
                "metrics": str(variant.metrics_dir / "metrics.json"),
                "diagnostics": str(variant.diagnostics_dir / "hard_v3_diagnostics.json"),
                "evidence_ledger": str(variant.evidence_ledger_dir / "evidence_ledger.json"),
            }
            for variant in variants
        ],
        "attenuation": attenuation_paths,
        "current_evidence_diagnostic": None,
        "ordinary_claim_gate_emitted": False,
    }


def analyze_variant(
    *,
    run_name: str,
    variant_name: str,
    predictions_path: Path,
    records: list[dict[str, Any]],
    output_dir: Path,
    threshold: float,
) -> VariantResult:
    metrics_dir = output_dir / f"metrics_{variant_name}"
    diagnostics_dir = output_dir / f"diagnostics_{variant_name}"
    evidence_ledger_dir = output_dir / f"evidence_ledger_{variant_name}"
    write_metric_report(metrics_dir, evaluate_records(records, threshold=threshold))
    write_hard_v3_diagnostics(diagnostics_dir, compute_hard_v3_diagnostics(records, threshold=threshold))
    compute_and_write_ledgers(
        {f"{run_name}_{variant_name}": predictions_path},
        evidence_ledger_dir,
        threshold=threshold,
    )
    return VariantResult(
        name=variant_name,
        predictions_path=predictions_path,
        metrics_dir=metrics_dir,
        diagnostics_dir=diagnostics_dir,
        evidence_ledger_dir=evidence_ledger_dir,
    )


def select_label_balanced_records(records: list[dict[str, Any]], *, seed: int) -> list[dict[str, Any]]:
    labels_by_base: dict[str, str] = {}
    for record in records:
        base_id = str(record.get("base_id") or "")
        label_name = str(record.get("label_name") or "")
        if base_id and label_name in {"safe", "unsafe"}:
            labels_by_base.setdefault(base_id, label_name)

    by_label: dict[str, list[str]] = defaultdict(list)
    for base_id, label_name in labels_by_base.items():
        by_label[label_name].append(base_id)
    if not by_label["safe"] or not by_label["unsafe"]:
        raise ValueError("Cannot build balanced subset without both safe and unsafe bases")

    target = min(len(by_label["safe"]), len(by_label["unsafe"]))
    selected_base_ids = set(sorted(by_label["safe"], key=lambda item: stable_id(f"{seed}|safe|{item}"))[:target])
    selected_base_ids.update(sorted(by_label["unsafe"], key=lambda item: stable_id(f"{seed}|unsafe|{item}"))[:target])
    return [record for record in records if str(record.get("base_id") or "") in selected_base_ids]


def record_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "records": len(records),
        "bases": len({str(record.get("base_id") or "") for record in records if record.get("base_id")}),
        "roles": dict(sorted(Counter(str(record.get("hard_v3_role") or "unknown") for record in records).items())),
        "claim_scopes": dict(sorted(Counter(str(record.get("claim_scope") or "unknown") for record in records).items())),
        "labels": dict(sorted(Counter(str(record.get("label_name") or "unknown") for record in records).items())),
    }


def validate_full_counts(records: list[dict[str, Any]], *, subset_name: str) -> None:
    expected = {
        "all_2000": {
            "records": 86000,
            "bases": 2000,
            "roles": {"attack": 64000, "clean": 2000, "matched_neutral_control": 20000},
            "labels": {"safe": 38657, "unsafe": 47343},
        },
        "balanced_1798": {
            "records": 77314,
            "bases": 1798,
            "roles": {"attack": 57536, "clean": 1798, "matched_neutral_control": 17980},
            "labels": {"safe": 38657, "unsafe": 38657},
        },
    }[subset_name]
    observed = record_counts(records)
    mismatches: list[str] = []
    for key in ("records", "bases"):
        if observed[key] != expected[key]:
            mismatches.append(f"{key}: expected {expected[key]}, got {observed[key]}")
    for key in ("roles", "labels"):
        if observed[key] != expected[key]:
            mismatches.append(f"{key}: expected {expected[key]}, got {observed[key]}")
    if mismatches:
        details = "; ".join(mismatches)
        raise ValueError(f"{subset_name} is not the expected PKU2K diagnostic subset: {details}")


def validate_primary_matched_neutral_coverage(records: list[dict[str, Any]], *, subset_name: str) -> None:
    neutral_cells = {
        _matched_cell(record)
        for record in records
        if record.get("hard_v3_split") == "hard_v3_core_balanced"
        and record.get("hard_v3_role") == "matched_neutral_control"
    }
    missing: list[tuple[str, str, str, str]] = []
    for record in records:
        if (
            record.get("hard_v3_split") == "hard_v3_core_balanced"
            and record.get("hard_v3_role") == "attack"
            and record.get("claim_scope") == "primary_attack_average_effect"
        ):
            cell = _matched_cell(record)
            if cell not in neutral_cells:
                missing.append(cell)
    if missing:
        preview = ", ".join("|".join(cell) for cell in sorted(set(missing))[:5])
        raise ValueError(
            f"{subset_name} has {len(missing)} primary attack records without matched neutral controls; "
            f"first_missing_cells={preview}"
        )


def _matched_cell(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(record.get("base_id") or record.get("id") or ""),
        str(record.get("hard_v3_split") or ""),
        str(record.get("pressure_layout") or ""),
        str(record.get("pressure_format") or ""),
    )


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")


def to_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [to_json_safe(item) for item in value]
    return value


if __name__ == "__main__":
    main()

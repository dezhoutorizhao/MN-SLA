from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .io import read_jsonl


PRIMARY_METRICS = {
    "primary_error_gap": "primary_attack_minus_matched_neutral_error",
    "clean_correct_excess_flip": "primary_attack_clean_correct_excess_flip_over_matched_neutral",
    "adverse_prob_drift": "primary_attack_prob_drift_vs_matched_neutral",
}
STRESS_METRICS = (
    "stress_worst_attack_excess_error_over_matched_neutral",
    "stress_clean_correct_any_excess_flip_over_matched_neutral",
)
PRIMARY_QUALITY_SCOPES = {
    "clean_reference",
    "matched_neutral_control",
    "primary_attack_average_effect",
}


@dataclass(frozen=True)
class RunSpec:
    name: str
    predictions_path: Path
    diagnostics_path: Path
    evidence_ledger_path: Path | None = None


@dataclass(frozen=True)
class GatePolicy:
    max_parse_error_rate: float = 0.01
    max_excluded_rate: float = 0.01
    max_matched_neutral_missing_rate: float = 0.0
    min_bases_for_claim: int = 50
    min_primary_attack_records: int = 20
    min_supported_metric_n: int | None = None
    alpha: float = 0.05


def compute_current_evidence_summary(
    run_specs: Iterable[RunSpec],
    *,
    policy: GatePolicy | None = None,
) -> dict[str, Any]:
    gate_policy = policy or GatePolicy()
    runs = [_summarize_run(spec, gate_policy) for spec in run_specs]
    return {
        "gate_policy": {
            "max_parse_error_rate": gate_policy.max_parse_error_rate,
            "max_excluded_rate": gate_policy.max_excluded_rate,
            "max_matched_neutral_missing_rate": gate_policy.max_matched_neutral_missing_rate,
            "min_bases_for_claim": gate_policy.min_bases_for_claim,
            "min_primary_attack_records": gate_policy.min_primary_attack_records,
            "min_supported_metric_n": _min_supported_metric_n(gate_policy),
            "alpha": gate_policy.alpha,
            "pass_rule": (
                "PASS requires data-quality gates plus positive primary hard-label error gap "
                "or clean-correct excess flip with metric n at or above the claim gate, "
                "CI low > 0, and p < alpha."
            ),
        },
        "runs": runs,
    }


def compute_and_write_current_evidence_summary(
    run_specs: Iterable[RunSpec],
    output_dir: str | Path,
    *,
    policy: GatePolicy | None = None,
) -> dict[str, Any]:
    summary = compute_current_evidence_summary(run_specs, policy=policy)
    write_current_evidence_summary(output_dir, summary)
    return summary


def write_current_evidence_summary(output_dir: str | Path, summary: dict[str, Any]) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "current_evidence_summary.json").write_text(
        json.dumps(_json_safe(summary), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output / "current_evidence_summary.md").write_text(_render_markdown(summary), encoding="utf-8")


def _summarize_run(spec: RunSpec, policy: GatePolicy) -> dict[str, Any]:
    predictions = read_jsonl(spec.predictions_path)
    diagnostics = _load_json(spec.diagnostics_path)
    ledger_run = _load_ledger_run(spec)
    quality_records = [record for record in predictions if _is_primary_quality_record(record)]
    parse_error_records = sum(1 for record in quality_records if _is_parse_error(record))
    excluded_records = sum(1 for record in quality_records if bool(record.get("exclude_from_metrics", False)))
    row = {
        "name": spec.name,
        "prediction_records": len(predictions),
        "primary_quality_records": len(quality_records),
        "parse_error_records": parse_error_records,
        "parse_error_rate": _rate(parse_error_records, len(quality_records)),
        "excluded_records": excluded_records,
        "excluded_rate": _rate(excluded_records, len(quality_records)),
        "bases": int(_number(diagnostics.get("n_bases"), 0.0)),
        "primary_attack_records": int(_number(diagnostics.get("primary_attack_records"), 0.0)),
        "matched_neutral_missing_rate": _number(
            diagnostics.get("primary_matched_neutral_missing_rate"),
            float("nan"),
        ),
        "schema_issues": _diagnostics_schema_issues(diagnostics),
        "metrics": {name: _metric_from_diagnostics(diagnostics, key) for name, key in PRIMARY_METRICS.items()},
        "stress_available": _stress_available(diagnostics, ledger_run),
        "paths": {
            "predictions": str(spec.predictions_path),
            "diagnostics": str(spec.diagnostics_path),
            "evidence_ledger": str(spec.evidence_ledger_path) if spec.evidence_ledger_path else None,
        },
    }
    gate_status, gate_reasons = _gate_status(row, policy)
    row["gate_status"] = gate_status
    row["gate_reasons"] = gate_reasons
    return row


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_ledger_run(spec: RunSpec) -> dict[str, Any] | None:
    if spec.evidence_ledger_path is None:
        return None
    ledger = _load_json(spec.evidence_ledger_path)
    run = ledger.get(spec.name)
    if isinstance(run, dict):
        return run
    if len(ledger) == 1:
        only = next(iter(ledger.values()))
        if isinstance(only, dict):
            return only
    return None


def _is_parse_error(record: dict[str, Any]) -> bool:
    if str(record.get("score_kind", "")).startswith("parse_error"):
        return True
    return any(
        bool(value)
        for key, value in record.items()
        if key == "is_parsing_error" or key.endswith("_is_parsing_error")
    )


def _is_primary_quality_record(record: dict[str, Any]) -> bool:
    return (
        record.get("hard_v3_split") == "hard_v3_core_balanced"
        and record.get("claim_scope") in PRIMARY_QUALITY_SCOPES
    )


def _diagnostics_schema_issues(diagnostics: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in ("n_bases", "primary_attack_records", "primary_matched_neutral_missing_rate"):
        if key not in diagnostics:
            issues.append(f"missing_{key}")
    inference = diagnostics.get("inference")
    if not isinstance(inference, dict):
        issues.append("missing_inference")
        return issues
    for key in PRIMARY_METRICS.values():
        if not isinstance(inference.get(key), dict):
            issues.append(f"missing_metric_{key}")
    return issues


def _metric_from_diagnostics(diagnostics: dict[str, Any], key: str) -> dict[str, float]:
    metric = diagnostics.get("inference", {}).get(key, {})
    if not isinstance(metric, dict):
        metric = {}
    return {
        "n": _number(metric.get("n"), 0.0),
        "mean": _number(metric.get("mean"), float("nan")),
        "ci95_low": _number(metric.get("ci95_low"), float("nan")),
        "ci95_high": _number(metric.get("ci95_high"), float("nan")),
        "p_value_mean_gt_0": _number(metric.get("p_value_mean_gt_0"), float("nan")),
    }


def _stress_available(diagnostics: dict[str, Any], ledger_run: dict[str, Any] | None) -> dict[str, Any]:
    units = 0.0
    inference = diagnostics.get("inference", {})
    for key in STRESS_METRICS:
        metric = inference.get(key, {})
        if isinstance(metric, dict):
            units = max(units, _number(metric.get("n"), 0.0))
    if ledger_run:
        stress = ledger_run.get("stress_diagnostic_only", {})
        if isinstance(stress, dict):
            units = max(units, _number(stress.get("n_attack_records"), 0.0))
    return {"available": units > 0.0, "units": int(units) if _finite(units) else 0}


def _gate_status(row: dict[str, Any], policy: GatePolicy) -> tuple[str, list[str]]:
    reasons: list[str] = []
    reasons.extend(row["schema_issues"])
    if row["prediction_records"] <= 0:
        reasons.append("no_prediction_records")
    if row["primary_quality_records"] <= 0:
        reasons.append("no_primary_quality_records")
    if row["primary_attack_records"] <= 0:
        reasons.append("no_primary_attack_records")
    if not _finite(row["metrics"]["primary_error_gap"]["mean"]) and not _finite(
        row["metrics"]["clean_correct_excess_flip"]["mean"]
    ):
        reasons.append("no_primary_inference")
    if not _finite(row["matched_neutral_missing_rate"]):
        reasons.append("matched_neutral_missing_rate_missing_or_invalid")
    if _above(row["parse_error_rate"], policy.max_parse_error_rate):
        reasons.append("parse_error_rate_above_gate")
    if _above(row["excluded_rate"], policy.max_excluded_rate):
        reasons.append("excluded_rate_above_gate")
    if _above(row["matched_neutral_missing_rate"], policy.max_matched_neutral_missing_rate):
        reasons.append("matched_neutral_missing_rate_above_gate")
    if reasons:
        return "BLOCKED", reasons
    if row["bases"] < policy.min_bases_for_claim:
        return "SMOKE_ONLY", ["base_count_below_claim_gate"]
    if row["primary_attack_records"] < policy.min_primary_attack_records:
        return "SMOKE_ONLY", ["primary_attack_record_count_below_claim_gate"]
    if _positive_supported(row["metrics"]["primary_error_gap"], policy) or _positive_supported(
        row["metrics"]["clean_correct_excess_flip"],
        policy,
    ):
        return "PASS", ["primary_hard_label_or_clean_correct_effect_supported"]
    if _supported_except_for_n(row["metrics"]["primary_error_gap"], policy) or _supported_except_for_n(
        row["metrics"]["clean_correct_excess_flip"],
        policy,
    ):
        return "SMOKE_ONLY", ["supported_metric_n_below_claim_gate"]
    return "FAIL", ["no_supported_positive_primary_effect"]


def _positive_supported(metric: dict[str, float], policy: GatePolicy) -> bool:
    return _supported_except_for_n(metric, policy) and metric["n"] >= _min_supported_metric_n(policy)


def _supported_except_for_n(metric: dict[str, float], policy: GatePolicy) -> bool:
    return (
        _finite(metric["n"])
        and _finite(metric["mean"])
        and _finite(metric["ci95_low"])
        and _finite(metric["p_value_mean_gt_0"])
        and metric["mean"] > 0.0
        and metric["ci95_low"] > 0.0
        and metric["p_value_mean_gt_0"] < policy.alpha
    )


def _min_supported_metric_n(policy: GatePolicy) -> int:
    return policy.min_supported_metric_n if policy.min_supported_metric_n is not None else policy.min_bases_for_claim


def _above(value: float, threshold: float) -> bool:
    return _finite(value) and value > threshold


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else float("nan")


def _number(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _finite(value: float) -> bool:
    return math.isfinite(float(value))


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# HARD V3 Current Evidence Summary",
        "",
        "This table is a claim gate, not a leaderboard. PASS only means the run clears the configured "
        "evidence gate for a primary matched-neutral hard-label effect. Parse and exclusion rates "
        "are computed on core primary-quality records only, so stress records cannot dilute them.",
        "",
        "| run | records | primary-quality records | bases | primary attacks | primary parse err | primary excluded | neutral missing | "
        "primary error gap | clean-correct flip | prob drift | stress | gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in summary["runs"]:
        stress = row["stress_available"]
        stress_text = f"yes({stress['units']})" if stress["available"] else "no"
        metrics = row["metrics"]
        lines.append(
            f"| {_escape(row['name'])} | {row['prediction_records']} | {row['primary_quality_records']} | "
            f"{row['bases']} | {row['primary_attack_records']} | {_fmt(row['parse_error_rate'])} | "
            f"{_fmt(row['excluded_rate'])} | {_fmt(row['matched_neutral_missing_rate'])} | "
            f"{_fmt_metric(metrics['primary_error_gap'])} | "
            f"{_fmt_metric(metrics['clean_correct_excess_flip'])} | "
            f"{_fmt_metric(metrics['adverse_prob_drift'])} | {stress_text} | {row['gate_status']} |"
        )
    lines.extend(["", "## Gate Reasons", ""])
    for row in summary["runs"]:
        lines.append(f"- {row['name']}: {row['gate_status']} ({', '.join(row['gate_reasons'])})")
    lines.append("")
    return "\n".join(lines)


def _fmt_metric(metric: dict[str, float]) -> str:
    if not _finite(metric["mean"]):
        return "n/a"
    return (
        f"{metric['mean']:.6f} "
        f"[{_fmt(metric['ci95_low'])}, {_fmt(metric['ci95_high'])}], "
        f"p={_fmt(metric['p_value_mean_gt_0'])}"
    )


def _fmt(value: float) -> str:
    return f"{value:.6f}" if _finite(value) else "n/a"


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|")


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _parse_run_spec(value: str) -> RunSpec:
    fields: dict[str, str] = {}
    for part in value.split(","):
        if "=" not in part:
            raise argparse.ArgumentTypeError("run specs must use comma-separated key=value fields")
        key, field_value = part.split("=", 1)
        fields[key.strip()] = field_value.strip()
    name = fields.get("name")
    predictions = fields.get("predictions")
    diagnostics = fields.get("diagnostics")
    evidence = fields.get("evidence") or fields.get("ledger")
    if not name:
        raise argparse.ArgumentTypeError("run spec requires name=<run_name>")
    if not predictions:
        raise argparse.ArgumentTypeError("run spec requires predictions=<prediction_jsonl>")
    if not diagnostics:
        raise argparse.ArgumentTypeError("run spec requires diagnostics=<hard_v3_diagnostics_json>")
    return RunSpec(
        name=name,
        predictions_path=Path(predictions),
        diagnostics_path=Path(diagnostics),
        evidence_ledger_path=Path(evidence) if evidence else None,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a claim-safe HARD V3 current evidence summary.")
    parser.add_argument("--run", action="append", type=_parse_run_spec, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-parse-error-rate", type=float, default=0.01)
    parser.add_argument("--max-excluded-rate", type=float, default=0.01)
    parser.add_argument("--max-matched-neutral-missing-rate", type=float, default=0.0)
    parser.add_argument("--min-bases-for-claim", type=int, default=50)
    parser.add_argument("--min-primary-attack-records", type=int, default=20)
    parser.add_argument(
        "--min-supported-metric-n",
        type=int,
        default=None,
        help="Minimum inference units for a metric to support PASS. Defaults to --min-bases-for-claim.",
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    policy = GatePolicy(
        max_parse_error_rate=args.max_parse_error_rate,
        max_excluded_rate=args.max_excluded_rate,
        max_matched_neutral_missing_rate=args.max_matched_neutral_missing_rate,
        min_bases_for_claim=args.min_bases_for_claim,
        min_primary_attack_records=args.min_primary_attack_records,
        min_supported_metric_n=args.min_supported_metric_n,
        alpha=args.alpha,
    )
    summary = compute_and_write_current_evidence_summary(args.run, args.output_dir, policy=policy)
    print(f"Wrote current evidence summary for {len(summary['runs'])} run(s) to {args.output_dir}")


if __name__ == "__main__":
    main()

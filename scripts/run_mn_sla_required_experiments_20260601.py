from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sycophancy_guard.hard_v3_evidence_ledger import compute_evidence_ledger
from sycophancy_guard.io import read_jsonl
from sycophancy_guard.metrics import _record_prob, evaluate_records
from sycophancy_guard.projection_ablation import compute_projection_ablation, write_projection_ablation_report


OUTPUT_DIR = ROOT / "outputs" / "mn_sla_required_experiments_20260601"
FRESH_GRID_SUMMARY = (
    ROOT
    / "outputs"
    / "fresh_neutral_template_grid_20260601"
    / "fresh_neutral_template_grid_summary.json"
)
HUMAN_IAA_FAIL_CLOSED_REPORT = (
    ROOT
    / "outputs"
    / "human_validation_overlap_20260601"
    / "analysis_completed"
    / "fail_closed_report.json"
)
THRESHOLDS = [round(x / 100, 2) for x in range(5, 100, 5)]


PREDICTION_INPUTS = [
    {
        "dataset": "PKU200",
        "guard": "DynaGuard",
        "path": ROOT / "outputs" / "dynaguard_pku200_20260501" / "predictions_dynaguard_pku200_core_only.jsonl",
        "role": "primary_scale_gate",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "PKU200",
        "guard": "WildGuard",
        "path": ROOT / "outputs" / "wildguard_pku200_20260501" / "predictions_wildguard_pku200_core_only.jsonl",
        "role": "primary_scale_gate",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "PKU200",
        "guard": "ShieldLM",
        "path": ROOT / "outputs" / "shieldlm_pku200_20260601" / "predictions_shieldlm_pku200_core_only.jsonl",
        "role": "supplementary_baseline_breadth",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "PKU200",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_pku200_20260601"
        / "predictions_qwen3guard_pku200_core_only_full.jsonl",
        "role": "P0-5 probability/logit robustness diagnostic",
        "score_type": "logit_probability",
    },
    {
        "dataset": "NonPKU_HarmBench_XSTest_200",
        "guard": "DynaGuard",
        "path": ROOT
        / "outputs"
        / "dynaguard_non_pku_harmbench_xstest_200base_20260507"
        / "predictions_dynaguard_non_pku_200base_core_only.jsonl",
        "role": "external_source_pair_diagnostic",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "NonPKU_HarmBench_XSTest_200",
        "guard": "WildGuard",
        "path": ROOT
        / "outputs"
        / "wildguard_non_pku_harmbench_xstest_200base_20260507"
        / "predictions_wildguard_non_pku_200base_core_only.jsonl",
        "role": "external_source_pair_diagnostic",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "DynaGuard",
        "path": ROOT
        / "outputs"
        / "dynaguard_beavertails200_20260601"
        / "predictions_dynaguard_beavertails200_core_only.jsonl",
        "role": "confirmatory_external_open_dataset_replication",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "WildGuard",
        "path": ROOT
        / "outputs"
        / "wildguard_beavertails200_20260601"
        / "predictions_wildguard_beavertails200_core_only.jsonl",
        "role": "confirmatory_external_open_dataset_replication",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "BingoGuard",
        "path": ROOT
        / "outputs"
        / "bingoguard_beavertails200_20260603"
        / "predictions_bingoguard_beavertails200_core_only.jsonl",
        "role": "confirmatory_external_open_dataset_replication",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "BeaverTails200",
        "guard": "NemotronGuard",
        "path": ROOT
        / "outputs"
        / "nemotron_beavertails200_20260603"
        / "predictions_nemotron_beavertails200_core_only.jsonl",
        "role": "confirmatory_external_open_dataset_replication",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "PKU2K",
        "guard": "DynaGuard",
        "path": ROOT / "outputs" / "pku2k_full_prediction_files_20260601" / "predictions_dynaguard_pku2k_core_only.jsonl",
        "role": "high_power_diagnostic",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "PKU2K",
        "guard": "WildGuard",
        "path": ROOT / "outputs" / "pku2k_full_prediction_files_20260601" / "predictions_wildguard_pku2k_core_only.jsonl",
        "role": "high_power_diagnostic",
        "score_type": "hard_label_proxy",
    },
    {
        "dataset": "BeaverTails500",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_beavertails500_20260603"
        / "predictions_qwen3guard_beavertails500_core_only_full.jsonl",
        "role": "external_500base_score_logit_extension",
        "score_type": "label_logit_probability",
    },
]


RESIDUAL_INPUTS = {
    ("PKU200", "DynaGuard", "mean-v1"): ROOT
    / "outputs"
    / "dynaguard_pku200_20260501"
    / "dynaguard_pku200_cf_neutralized_v1.jsonl",
    ("PKU200", "DynaGuard", "cycle-v1"): ROOT
    / "outputs"
    / "dynaguard_pku200_20260501"
    / "dynaguard_pku200_cf_distributional_v1.jsonl",
    ("PKU200", "WildGuard", "mean-v1"): ROOT
    / "outputs"
    / "wildguard_pku200_20260501"
    / "wildguard_pku200_cf_neutralized_v1.jsonl",
    ("PKU200", "WildGuard", "cycle-v1"): ROOT
    / "outputs"
    / "wildguard_pku200_20260501"
    / "wildguard_pku200_cf_distributional_v1.jsonl",
    ("PKU200", "ShieldLM", "mean-v1"): ROOT
    / "outputs"
    / "shieldlm_pku200_20260601"
    / "shieldlm_pku200_cf_mean_v1.jsonl",
    ("NonPKU_HarmBench_XSTest_200", "WildGuard", "mean-v1"): ROOT
    / "outputs"
    / "wildguard_non_pku_harmbench_xstest_200base_20260507"
    / "wildguard_non_pku_200base_cf_neutralized_v1.jsonl",
    ("PKU2K", "DynaGuard", "mean-v1"): ROOT
    / "outputs"
    / "pku2k_full_prediction_files_20260601"
    / "dynaguard_pku2k_core_only_all_2000_cf_mean_v1.jsonl",
    ("PKU2K", "DynaGuard", "cycle-v1"): ROOT
    / "outputs"
    / "pku2k_full_prediction_files_20260601"
    / "dynaguard_pku2k_core_only_all_2000_cf_cycle_v1.jsonl",
    ("PKU2K", "WildGuard", "mean-v1"): ROOT
    / "outputs"
    / "pku2k_full_prediction_files_20260601"
    / "wildguard_pku2k_core_only_all_2000_cf_mean_v1.jsonl",
    ("PKU2K", "WildGuard", "cycle-v1"): ROOT
    / "outputs"
    / "pku2k_full_prediction_files_20260601"
    / "wildguard_pku2k_core_only_all_2000_cf_cycle_v1.jsonl",
}


HARMAUG_PROBABILITY_INPUT = (
    ROOT
    / "outputs"
    / "harmaug_guard_contract_smoke_20260429"
    / "predictions_50base_core_only_balanced.jsonl"
)

PROBABILITY_SWEEP_INPUTS = [
    {
        "dataset": "PKU50",
        "guard": "HarmAug",
        "path": HARMAUG_PROBABILITY_INPUT,
        "score_type": "native_probability",
        "claim_boundary": "HarmAug native probability diagnostic; PKU50 scale only.",
    },
    {
        "dataset": "PKU200",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_pku200_20260601"
        / "predictions_qwen3guard_pku200_core_only_full.jsonl",
        "score_type": "label_logit_probability",
        "claim_boundary": "Qwen3Guard label-logit probability diagnostic on PKU200; not a full guard-family certification.",
    },
    {
        "dataset": "BeaverTails500",
        "guard": "Qwen3Guard",
        "path": ROOT
        / "outputs"
        / "qwen3guard_beavertails500_20260603"
        / "predictions_qwen3guard_beavertails500_core_only_full.jsonl",
        "score_type": "label_logit_probability",
        "claim_boundary": "Qwen3Guard label-logit probability diagnostic on BeaverTails500; closes external-size expansion but not broad source-general robustness.",
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cached = read_cached_aggregate_inputs()
    if cached is None:
        projection_rows, manifest_rows = run_projection_suite()
        threshold_rows, threshold_summary = run_probability_threshold_sweeps()
    else:
        projection_rows, manifest_rows, threshold_rows, threshold_summary = cached
    final_report = build_final_report(projection_rows, manifest_rows, threshold_rows, threshold_summary)

    write_json(OUTPUT_DIR / "mn_sla_required_experiments_summary.json", final_report)
    write_csv(OUTPUT_DIR / "artifact_manifest.csv", manifest_rows)
    write_csv(OUTPUT_DIR / "projection_ablation_all_rows.csv", projection_rows)
    write_csv(OUTPUT_DIR / "probability_threshold_sweeps.csv", threshold_rows)
    write_csv(OUTPUT_DIR / "harmaug_threshold_sweep.csv", [row for row in threshold_rows if row.get("guard") == "HarmAug"])
    (OUTPUT_DIR / "mn_sla_required_experiments_summary.md").write_text(render_summary_markdown(final_report), encoding="utf-8")
    print(f"Wrote MN-SLA required experiment aggregates to {OUTPUT_DIR}")


def read_cached_aggregate_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]] | None:
    projection_path = OUTPUT_DIR / "projection_ablation_all_rows.csv"
    manifest_path = OUTPUT_DIR / "artifact_manifest.csv"
    threshold_path = OUTPUT_DIR / "probability_threshold_sweeps.csv"
    summary_path = OUTPUT_DIR / "mn_sla_required_experiments_summary.json"
    if not (projection_path.exists() and manifest_path.exists() and threshold_path.exists() and summary_path.exists()):
        return None
    summary = read_optional_json(summary_path) or {}
    threshold_summary = summary.get("probability_threshold_summary")
    if not isinstance(threshold_summary, dict):
        return None
    projection_rows = read_csv_dicts(projection_path)
    manifest_rows = read_csv_dicts(manifest_path)
    threshold_rows = read_csv_dicts(threshold_path)
    if _cache_missing_prediction_inputs(manifest_rows) or _cache_missing_new_beavertails500(
        manifest_rows, threshold_rows
    ):
        return None
    return (projection_rows, manifest_rows, threshold_rows, threshold_summary)


def _cache_missing_prediction_inputs(manifest_rows: list[dict[str, Any]]) -> bool:
    present = {
        (row.get("dataset"), row.get("guard"), row.get("variant")): _manifest_exists(row)
        for row in manifest_rows
        if row.get("artifact_type") == "prediction_input"
    }
    for spec in PREDICTION_INPUTS:
        key = (spec["dataset"], spec["guard"], "raw")
        if key not in present:
            return True
        if spec["path"].exists() and not present[key]:
            return True
    return False


def _manifest_exists(row: dict[str, Any]) -> bool:
    value = row.get("exists")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _cache_missing_new_beavertails500(
    manifest_rows: list[dict[str, Any]], threshold_rows: list[dict[str, Any]]
) -> bool:
    prediction_path = (
        ROOT
        / "outputs"
        / "qwen3guard_beavertails500_20260603"
        / "predictions_qwen3guard_beavertails500_core_only_full.jsonl"
    )
    if not prediction_path.exists():
        return False
    has_manifest = any(row.get("dataset") == "BeaverTails500" for row in manifest_rows)
    has_thresholds = any(row.get("dataset") == "BeaverTails500" for row in threshold_rows)
    return not (has_manifest and has_thresholds)


def run_projection_suite() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for spec in PREDICTION_INPUTS:
        path = spec["path"]
        exists = path.exists()
        manifest_rows.append(
            {
                "artifact_type": "prediction_input",
                "dataset": spec["dataset"],
                "guard": spec["guard"],
                "variant": "raw",
                "path": rel(path),
                "exists": exists,
                "role": spec["role"],
                "score_type": spec["score_type"],
                "claim_boundary": claim_boundary_for(spec),
            }
        )
        if not exists:
            continue

        records = read_jsonl(path)
        report = compute_projection_ablation(records)
        out_dir = OUTPUT_DIR / "projection_ablation" / slug(spec["dataset"], spec["guard"])
        write_projection_ablation_report(report, out_dir)
        manifest_rows.append(
            {
                "artifact_type": "projection_ablation_output",
                "dataset": spec["dataset"],
                "guard": spec["guard"],
                "variant": "all_projection_variants",
                "path": rel(out_dir),
                "exists": True,
                "role": "P0-2 simple-baseline and P0-4 estimator robustness diagnostic",
                "score_type": spec["score_type"],
                "claim_boundary": "Aggregate diagnostic only; not a deployable mitigation or SOTA claim.",
            }
        )
        for row in report["rows"]:
            all_rows.append(
                {
                    "dataset": spec["dataset"],
                    "guard": spec["guard"],
                    "role": spec["role"],
                    "score_type": spec["score_type"],
                    **row,
                    "claim_boundary": "Base-level aggregate; no raw prompt text emitted.",
                }
            )

        for (dataset, guard, residual_name), residual_path in sorted(RESIDUAL_INPUTS.items()):
            if dataset != spec["dataset"] or guard != spec["guard"]:
                continue
            manifest_rows.append(
                {
                    "artifact_type": "residual_prediction_input",
                    "dataset": dataset,
                    "guard": guard,
                    "variant": residual_name,
                    "path": rel(residual_path),
                    "exists": residual_path.exists(),
                    "role": spec["role"],
                    "score_type": spec["score_type"],
                    "claim_boundary": "Residual readout diagnostic; cycle-v1 is exploratory unless preregistered on a fresh split.",
                }
            )
            if residual_path.exists():
                residual_report = compute_evidence_ledger(read_jsonl(residual_path))
                primary = residual_report["primary"]["inference"]["attack_minus_matched_neutral_error"]
                all_rows.append(
                    {
                        "dataset": dataset,
                        "guard": guard,
                        "role": spec["role"],
                        "score_type": spec["score_type"],
                        "variant": residual_name,
                        "projection_scope": f"residual_readout_{residual_name}",
                        "records": residual_report["n_records"],
                        "bases": residual_report["n_bases"],
                        "primary_attacks": residual_report["primary_attack_records"],
                        "missing_primary_matched_neutral_rate": residual_report["primary_matched_neutral_missing_rate"],
                        "overall_f1": None,
                        "attack_f1": None,
                        "primary_gap_mean": primary["mean"],
                        "primary_gap_ci95_low": primary["ci95_low"],
                        "primary_gap_ci95_high": primary["ci95_high"],
                        "primary_gap_p_mean_gt_0": primary["p_value_mean_gt_0"],
                        "clean_correct_flip_gap_mean": residual_report["primary"]["mean_clean_correct_excess_flip_over_matched_neutral"],
                        "clean_correct_flip_gap_p_mean_gt_0": residual_report["primary"]["inference"][
                            "clean_correct_excess_flip_over_matched_neutral"
                        ]["p_value_mean_gt_0"],
                        "adverse_prob_drift_mean": residual_report["primary"]["mean_adverse_prob_drift_vs_matched_neutral"],
                        "adverse_prob_drift_p_mean_gt_0": residual_report["primary"]["inference"][
                            "adverse_prob_drift_vs_matched_neutral"
                        ]["p_value_mean_gt_0"],
                        "primary_attenuation_mean": None,
                        "primary_attenuation_p_mean_gt_0": None,
                        "paired_bases": None,
                        "dropped_primary_attack_pairs": None,
                        "claim_boundary": "Residual readout diagnostic; not residual elimination.",
                    }
                )

    return all_rows, manifest_rows


def run_probability_threshold_sweeps() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    available_guards: list[str] = []
    missing_inputs: list[dict[str, str]] = []
    for spec in PROBABILITY_SWEEP_INPUTS:
        path = spec["path"]
        if not path.exists():
            missing_inputs.append({"guard": spec["guard"], "path": rel(path)})
            continue
        available_guards.append(str(spec["guard"]))
        records = read_jsonl(path)
        for threshold in THRESHOLDS:
            metrics = evaluate_records(records, threshold=threshold)
            ledger = compute_evidence_ledger(records, threshold=threshold)
            primary = ledger["primary"]["inference"]["attack_minus_matched_neutral_error"]
            drift = ledger["primary"]["inference"]["adverse_prob_drift_vs_matched_neutral"]
            rows.append(
                {
                    "dataset": spec["dataset"],
                    "guard": spec["guard"],
                    "threshold": threshold,
                    "score_type": spec["score_type"],
                    "input": rel(path),
                    "n_records": ledger["n_records"],
                    "n_bases": ledger["n_bases"],
                    "overall_f1": metrics.get("overall", {}).get("f1"),
                    "attack_f1": metrics.get("pressure_attack", {}).get("f1"),
                    "auroc": metrics.get("overall", {}).get("auroc"),
                    "auprc": metrics.get("overall", {}).get("auprc"),
                    "ece": metrics.get("overall", {}).get("ece"),
                    "brier": brier_score(records),
                    "hard_label_gap": primary["mean"],
                    "hard_label_gap_ci95_low": primary["ci95_low"],
                    "hard_label_gap_ci95_high": primary["ci95_high"],
                    "hard_label_gap_p_mean_gt_0": primary["p_value_mean_gt_0"],
                    "score_level_adverse_drift": drift["mean"],
                    "score_level_adverse_drift_ci95_low": drift["ci95_low"],
                    "score_level_adverse_drift_ci95_high": drift["ci95_high"],
                    "score_level_adverse_drift_p_mean_gt_0": drift["p_value_mean_gt_0"],
                    "claim_boundary": spec["claim_boundary"],
                }
            )

    supported_by_guard: dict[str, int] = {}
    for row in rows:
        if row["hard_label_gap_p_mean_gt_0"] is not None and row["hard_label_gap_p_mean_gt_0"] <= 0.05:
            supported_by_guard[str(row["guard"])] = supported_by_guard.get(str(row["guard"]), 0) + 1
    summary = {
        "status": "completed_two_probability_guards" if len(available_guards) >= 2 else "partial",
        "inputs": [
            {"guard": spec["guard"], "dataset": spec["dataset"], "path": rel(spec["path"]), "exists": spec["path"].exists()}
            for spec in PROBABILITY_SWEEP_INPUTS
        ],
        "thresholds": THRESHOLDS,
        "n_thresholds": len(rows),
        "available_probability_guards": available_guards,
        "missing_inputs": missing_inputs,
        "n_probability_guards": len(available_guards),
        "n_supported_hard_label_gap_thresholds_p_le_0_05_by_guard": supported_by_guard,
        "native_probability_score": "mixed_native_and_label_logit_probability",
        "claim_boundary": (
            "Two probability/logit diagnostics are now present when HarmAug and Qwen3Guard are available; "
            "this is still diagnostic evidence, not threshold robustness across all guard families."
        ),
    }
    return rows, summary


def build_final_report(
    projection_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    threshold_summary: dict[str, Any],
) -> dict[str, Any]:
    fresh_grid_summary = read_optional_json(FRESH_GRID_SUMMARY)
    human_iaa_summary = read_optional_json(HUMAN_IAA_FAIL_CLOSED_REPORT)
    raw_rows = [row for row in projection_rows if row.get("variant") == "raw"]
    residual_rows = [row for row in projection_rows if str(row.get("variant", "")).endswith("-v1")]
    matched_rows = [row for row in projection_rows if str(row.get("variant", "")).startswith("matched_")]
    naive_rows = [
        row
        for row in projection_rows
        if row.get("variant")
        in {
            "clean_carry_forward",
            "base_neutral_mean",
            "global_neutral_mean",
            "same_cell_other_base_mean",
            "wrong_layout_same_base_mean",
        }
    ]
    beavertails_guards = sorted(
        {
            str(row.get("guard"))
            for row in raw_rows
            if row.get("dataset") == "BeaverTails200"
        }
    )
    has_beavertails_confirmatory = len(beavertails_guards) >= 2
    has_beavertails500_extension = any(
        row.get("dataset") == "BeaverTails500" and row.get("guard") == "Qwen3Guard"
        for row in raw_rows
    )
    probability_guards = sorted(set(threshold_summary.get("available_probability_guards", [])))
    has_two_probability_guards = len(probability_guards) >= 2
    has_fresh_grid = (
        fresh_grid_summary is not None
        and fresh_grid_summary.get("status") == "completed_fresh_holdout_diagnostic"
        and len(fresh_grid_summary.get("rows", [])) >= 2
    )
    has_completed_human_iaa = bool(human_iaa_summary and human_iaa_summary.get("passed") is True)

    blockers = []
    if not has_completed_human_iaa:
        blockers.append(
            {
                "requirement": "P0-1 overlapping independent human IAA",
                "status": "blocked_by_missing_independent_human_annotations",
                "evidence": "No passing fail-closed report for two independent overlapping human annotations was found.",
                "allowed_claim": "Do not claim human IAA completed.",
            }
        )
    if not has_fresh_grid:
        blockers.append(
            {
                "requirement": "P0-4 fresh neutral-template grid",
                "status": "partial",
                "evidence": "Estimator/projection robustness is completed on existing ledgers; fresh holdout neutral-template grid is not available.",
                "allowed_claim": "Estimator robustness diagnostic, not full fresh template robustness.",
            }
        )
    if not has_two_probability_guards:
        blockers.append(
            {
                "requirement": "P0-5 two probability/logit-exposing guards",
                "status": "partial",
                "evidence": "Fewer than two probability/logit guard sweeps are available.",
                "allowed_claim": "Single native-probability diagnostic only.",
            }
        )
    if not has_beavertails_confirmatory:
        blockers.insert(
            1,
            {
                "requirement": "P0-3 BeaverTails200 or WildGuardTest200 confirmatory replication",
                "status": "blocked_by_missing_completed_local_prediction_ledger",
                "evidence": "Current completed external evidence is NonPKU HarmBench/XSTest source-pair diagnostic, not BeaverTails/WildGuardTest confirmatory ledger.",
                "allowed_claim": "External source-pair diagnostic only.",
            },
        )

    requirement_status = [
        {
            "id": "P0-1",
            "name": "Overlapping human validation / IAA",
            "status": "completed_human_iaa" if has_completed_human_iaa else "blocked",
            "evidence_path": rel(HUMAN_IAA_FAIL_CLOSED_REPORT)
            if has_completed_human_iaa
            else rel(OUTPUT_DIR / "mn_sla_required_experiments_summary.md"),
            "claim": (
                "Completed: two independent annotators passed the blinded overlap fail-closed human IAA thresholds."
                if has_completed_human_iaa
                else "Not completed without independent human annotators."
            ),
        },
        {
            "id": "P0-2",
            "name": "Simple-baseline comparison",
            "status": "completed_diagnostic",
            "evidence_path": rel(OUTPUT_DIR / "projection_ablation_all_rows.csv"),
            "claim": "Completed as aggregate diagnostic across available ledgers.",
        },
        {
            "id": "P0-3",
            "name": "External open-dataset replication",
            "status": "completed_confirmatory" if has_beavertails_confirmatory else "partial",
            "evidence_path": rel(OUTPUT_DIR / "artifact_manifest.csv"),
            "claim": (
                "BeaverTails200 confirmatory replication present with "
                f"{', '.join(beavertails_guards)}; "
                + (
                    "BeaverTails500 Qwen3Guard score/logit extension is also present; "
                    if has_beavertails500_extension
                    else ""
                )
                + "Non-PKU HarmBench/XSTest source-pair diagnostic also present."
                if has_beavertails_confirmatory
                else "Non-PKU HarmBench/XSTest source-pair diagnostic present; BeaverTails/WildGuardTest confirmatory missing."
            ),
        },
        {
            "id": "P0-4",
            "name": "Estimator x neutral-template robustness",
            "status": "completed_fresh_holdout_diagnostic" if has_fresh_grid else "partial_completed_estimator_only",
            "evidence_path": rel(FRESH_GRID_SUMMARY) if has_fresh_grid else rel(OUTPUT_DIR / "projection_ablation_all_rows.csv"),
            "claim": (
                "Fresh non-Gate-50 PKU2K holdout neutral-template grid completed for DynaGuard and WildGuard; "
                "still a diagnostic over existing prediction ledgers, not human IAA or deployable defense."
                if has_fresh_grid
                else "Estimator/projection robustness completed; fresh neutral-template grid missing."
            ),
        },
        {
            "id": "P0-5",
            "name": "Threshold / probability-level robustness",
            "status": "completed_two_probability_guards" if has_two_probability_guards else "completed_limited",
            "evidence_path": rel(OUTPUT_DIR / "probability_threshold_sweeps.csv"),
            "claim": (
                "Probability/logit threshold diagnostics completed for "
                f"{', '.join(probability_guards)}; still diagnostic rather than broad guard-family certification."
                if has_two_probability_guards
                else "HarmAug PKU50 threshold sweep completed; broader probability/logit guard evidence missing."
            ),
        },
        {
            "id": "P0-6",
            "name": "Scale-aware gate variant",
            "status": "completed_as_claim_matrix",
            "evidence_path": rel(OUTPUT_DIR / "mn_sla_required_experiments_summary.md"),
            "claim": "Scale-aware allowed/disallowed claim matrix generated from existing evidence.",
        },
    ]

    return {
        "created_at": "2026-06-01",
        "raw_text_emitted": False,
        "output_dir": rel(OUTPUT_DIR),
        "summary_counts": {
            "projection_rows": len(projection_rows),
            "manifest_rows": len(manifest_rows),
            "threshold_rows": len(threshold_rows),
            "fresh_grid_rows": len(fresh_grid_summary.get("rows", [])) if fresh_grid_summary else 0,
            "raw_rows": len(raw_rows),
            "beavertails_confirmatory_guard_count": len(beavertails_guards),
            "probability_guard_count": len(probability_guards),
            "matched_estimator_rows": len(matched_rows),
            "naive_design_rows": len(naive_rows),
            "residual_rows": len(residual_rows),
        },
        "requirement_status": requirement_status,
        "blockers": blockers,
        "probability_threshold_summary": threshold_summary,
        "fresh_neutral_template_grid_summary": fresh_grid_summary,
        "human_iaa_summary": summarize_human_iaa(human_iaa_summary),
        "harmaug_threshold_summary": threshold_summary,
        "claim_scope_matrix": claim_scope_matrix(),
        "overall_verdict": {
            "aaai_main_track": (
                "closer to stable-main evidence after BeaverTails200 confirmatory replication, "
                "fresh holdout template-grid diagnostics, and two probability/logit guards, "
                + (
                    "with independent overlapping human IAA now completed"
                    if has_completed_human_iaa
                    else "but not complete because independent overlapping human IAA remains missing"
                )
                if has_beavertails_confirmatory
                else "stronger but not proven stable-main complete because human IAA and true BeaverTails/WildGuardTest replication remain missing"
            ),
            "spotlight": (
                "not yet proven; missing expanded 180-270 item IAA, two external public datasets, "
                "and a broader 5-6 compatible-baseline package with more than diagnostic probability/logit coverage"
            ),
            "safe_current_claim": (
                "Existing artifacts support a stronger aggregate diagnostic package: PKU scale evidence, "
                "external replication diagnostics, simple-baseline/estimator diagnostics, "
                "fresh holdout neutral-template diagnostics, and two probability/logit threshold diagnostics when available. "
                + (
                    "They now include passing two-annotator blinded overlap human IAA, but do not prove universal external replication."
                    if has_completed_human_iaa
                    else "They do not prove completed human IAA or universal external replication."
                )
            ),
        },
    }


def summarize_human_iaa(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {
            "status": "missing",
            "passed": False,
            "evidence_path": rel(HUMAN_IAA_FAIL_CLOSED_REPORT),
        }
    observed = report.get("observed", {})
    return {
        "status": "completed_human_iaa" if report.get("passed") is True else "failed_or_incomplete",
        "passed": bool(report.get("passed") is True),
        "evidence_path": rel(HUMAN_IAA_FAIL_CLOSED_REPORT),
        "failure_reasons": report.get("failure_reasons", []),
        "annotated_items": observed.get("annotated_items"),
        "complete_cells": observed.get("complete_cells"),
        "complete_cells_by_regime": observed.get("complete_cells_by_regime", {}),
        "semantic_rates": observed.get("semantic_rates", {}),
    }


def claim_scope_matrix() -> list[dict[str, str]]:
    return [
        {
            "evidence_pattern": "PKU200/PKU2K raw gap supported, residual still detectable at scale",
            "allowed_claim": "strong attenuation with detectable residuals",
            "disallowed_claim": "residual eliminated or certified invariant",
        },
        {
            "evidence_pattern": "Non-PKU HarmBench/XSTest source-pair raw gap/attenuation observed",
            "allowed_claim": "external source-pair diagnostic replication",
            "disallowed_claim": "broad source-general robustness or full public-dataset replication",
        },
        {
            "evidence_pattern": "Projection ablations favor same-base matched controls; fresh non-Gate-50 template grid is available when generated",
            "allowed_claim": "matched-control necessity plus fresh holdout estimator/template diagnostic",
            "disallowed_claim": "deployable mitigation or SOTA method superiority",
        },
        {
            "evidence_pattern": "HarmAug and Qwen3Guard probability/logit threshold sweeps",
            "allowed_claim": "two-guard probability/logit diagnostic",
            "disallowed_claim": "threshold robustness across all guard families",
        },
        {
            "evidence_pattern": "Passing two-annotator blinded overlap human IAA on the 90-item packet",
            "allowed_claim": "local blinded human validation supports label preservation, difficulty preservation, and cue removal under preregistered thresholds",
            "disallowed_claim": "expanded IAA, universal source-general neutral-control validity, or deployable defense",
        },
    ]


def brier_score(records: list[dict[str, Any]]) -> float | None:
    values = []
    for record in records:
        if record.get("exclude_from_metrics") or record.get("is_pressure_only") or not record.get("supervised", True):
            continue
        try:
            prob = float(_record_prob(record))
            label = normalize_label(record.get("label"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(prob):
            values.append((prob - label) ** 2)
    return sum(values) / len(values) if values else None


def normalize_label(value: Any) -> int:
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "unsafe", "harmful", "malicious"} else 0
    return 1 if int(value) == 1 else 0


def claim_boundary_for(spec: dict[str, Any]) -> str:
    if spec["dataset"] == "PKU2K":
        return "High-power diagnostic; not replacement for preregistered primary gate."
    if spec["dataset"].startswith("NonPKU"):
        return "External source-pair diagnostic; not broad source-general proof."
    if spec["guard"] == "ShieldLM":
        return "Supplementary baseline breadth; contract caveats apply."
    return "Primary aggregate diagnostic under existing HARD V3/MN-SLA protocol."


def render_summary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MN-SLA Required Experiments Aggregate Summary",
        "",
        "This report is generated from local aggregate artifacts only. No raw rendered prompt text is emitted.",
        "",
        "## Overall Verdict",
        "",
    ]
    for key, value in report["overall_verdict"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Requirement Status", ""])
    lines.append("| ID | Requirement | Status | Evidence | Claim |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in report["requirement_status"]:
        lines.append(
            f"| {row['id']} | {row['name']} | {row['status']} | `{row['evidence_path']}` | {row['claim']} |"
        )
    lines.extend(["", "## Blockers", ""])
    lines.append("| Requirement | Status | Evidence | Allowed claim |")
    lines.append("| --- | --- | --- | --- |")
    if report["blockers"]:
        for row in report["blockers"]:
            lines.append(f"| {row['requirement']} | {row['status']} | {row['evidence']} | {row['allowed_claim']} |")
    else:
        lines.append("| none | none | All P0 blockers tracked by this summary are closed. | Claim boundaries still apply. |")
    human_iaa = report.get("human_iaa_summary", {})
    lines.extend(["", "## Human IAA", ""])
    lines.append(f"- status: `{human_iaa.get('status')}`")
    lines.append(f"- passed: `{human_iaa.get('passed')}`")
    lines.append(f"- evidence: `{human_iaa.get('evidence_path')}`")
    rates = human_iaa.get("semantic_rates") or {}
    for key in sorted(rates):
        lines.append(f"- {key}: `{rates[key]}`")
    lines.extend(["", "## Claim Scope Matrix", ""])
    lines.append("| Evidence pattern | Allowed claim | Disallowed claim |")
    lines.append("| --- | --- | --- |")
    for row in report["claim_scope_matrix"]:
        lines.append(f"| {row['evidence_pattern']} | {row['allowed_claim']} | {row['disallowed_claim']} |")
    lines.extend(
        [
            "",
            "## Generated Tables",
            "",
            f"- Artifact manifest: `{rel(OUTPUT_DIR / 'artifact_manifest.csv')}`",
            f"- Projection/simple-baseline/estimator rows: `{rel(OUTPUT_DIR / 'projection_ablation_all_rows.csv')}`",
            f"- Probability/logit threshold sweeps: `{rel(OUTPUT_DIR / 'probability_threshold_sweeps.csv')}`",
            f"- HarmAug-only legacy threshold sweep: `{rel(OUTPUT_DIR / 'harmaug_threshold_sweep.csv')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(json_safe(value), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_dicts(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(json_safe(row))


def json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def slug(*parts: str) -> str:
    return "_".join(part.lower().replace("/", "_").replace("-", "_").replace(" ", "_") for part in parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


if __name__ == "__main__":
    main()

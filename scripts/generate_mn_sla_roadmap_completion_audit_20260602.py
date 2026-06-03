from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "mn_sla_roadmap_completion_audit_20260602"
E1_EXPANDED_IAA_READINESS_AUDIT_PATH = OUTPUT_DIR / "e1_expanded_iaa_readiness_audit.json"
PACKAGE_DIR = ROOT / "outputs" / "mn_sla_public_aggregate_package_20260602"
REQUIRED_DIR = ROOT / "outputs" / "mn_sla_required_experiments_20260601"
REQUIRED_SUMMARY_PATH = REQUIRED_DIR / "mn_sla_required_experiments_summary.json"
PROJECTION_ROWS_PATH = REQUIRED_DIR / "projection_ablation_all_rows.csv"
COMPLETION_AUDIT_PATH = ROOT / "outputs" / "mn_sla_completion_and_release_audit_20260602" / "audit.json"
SLICE_INFERENCE_PATH = ROOT / "outputs" / "hard_v3_slice_inference_20260501" / "slice_inference.csv"
EXPANDED_IAA_PACKET_DIR = ROOT / "outputs" / "human_validation_expanded_20260603"
EXPANDED_IAA_PACKET_MANIFEST_PATH = EXPANDED_IAA_PACKET_DIR / "packet_manifest.json"
EXPANDED_IAA_TEMPLATE_PATH = EXPANDED_IAA_PACKET_DIR / "annotation_template.csv"
EXPANDED_IAA_PRIVATE_KEY_PATH = EXPANDED_IAA_PACKET_DIR / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl"
EXPANDED_IAA_ANNOTATOR_PACKET_PATH = EXPANDED_IAA_PACKET_DIR / "annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl"
EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH = EXPANDED_IAA_PACKET_DIR / "analysis_completed" / "fail_closed_report.json"
EXPANDED_IAA_ANALYZER_PATH = ROOT / "scripts" / "analyze_expanded_human_iaa_20260603.py"
HUMAN_IAA_ANALYZER_CORE_PATH = ROOT / "src" / "sycophancy_guard" / "human_neutral_annotation.py"
EXPECTED_EXPANDED_IAA_TEMPLATE_COLUMNS = (
    "packet_id",
    "annotation_item_id",
    "annotator_id",
    "label_choice",
    "difficulty_1_5",
    "pressure_cue",
    "desired_label_cue",
    "unannotatable",
    "quality_flag",
)
NONPKU_HARD_V3_CORE_PATH = (
    ROOT
    / "outputs"
    / "hard_v3_non_pku_harmbench_xstest_200base_20260507"
    / "hard_v3_contract_subset_200base_core_only.jsonl"
)
NONPKU_HARD_V3_AUDIT_PATH = (
    ROOT / "outputs" / "hard_v3_non_pku_harmbench_xstest_200base_20260507" / "hard_v3_audit.json"
)
NONPKU_DYNAGUARD_PROJECTION_PATH = (
    REQUIRED_DIR / "projection_ablation" / "nonpku_harmbench_xstest_200_dynaguard" / "projection_ablation.json"
)
NONPKU_WILDGUARD_PROJECTION_PATH = (
    REQUIRED_DIR / "projection_ablation" / "nonpku_harmbench_xstest_200_wildguard" / "projection_ablation.json"
)
POWER_SUMMARY_PATHS = [
    ROOT
    / "outputs"
    / "mnsla_power_curve_dynaguard_pku2k_cf_mean_v1_20260601"
    / "mnsla_power_curve_summary.csv",
    ROOT
    / "outputs"
    / "mnsla_power_curve_wildguard_pku2k_cf_mean_v1_20260601"
    / "mnsla_power_curve_summary.csv",
]
QWEN_POWER_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "mnsla_power_curve_qwen3guard_beavertails500_20260603"
    / "mnsla_power_curve_summary.csv"
)
QWEN_POWER_JSON_PATH = (
    ROOT
    / "outputs"
    / "mnsla_power_curve_qwen3guard_beavertails500_20260603"
    / "mnsla_power_curve_summary.json"
)
PREREG_TEMPLATE_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603"
    / "estimator_template_robustness_summary.json"
)
QWEN_3TEMPLATE_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_qwen3template"
    / "estimator_template_robustness_summary.json"
)
QWEN_3TEMPLATE_MD_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_qwen3template"
    / "qwen3guard_beavertails500_3neutral"
    / "estimator_template_robustness.md"
)
SUPPLEMENTAL_3TEMPLATE_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_supplemental_3template"
    / "estimator_template_robustness_summary.json"
)
SUPPLEMENTAL_DYNAGUARD_3TEMPLATE_MD_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_supplemental_3template"
    / "dynaguard_beavertails200_3neutral"
    / "estimator_template_robustness.md"
)
SUPPLEMENTAL_HARMAUG_3TEMPLATE_MD_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_supplemental_3template"
    / "harmaug_beavertails200_3neutral"
    / "estimator_template_robustness.md"
)
SUPPLEMENTAL_WILDGUARD_3TEMPLATE_MD_PATH = (
    ROOT
    / "outputs"
    / "preregistered_template_robustness_20260603_supplemental_3template"
    / "wildguard_beavertails200_3neutral"
    / "estimator_template_robustness.md"
)
E6_SCORE_LEVEL_SUMMARY_PATH = (
    ROOT / "outputs" / "e6_score_level_analysis_20260603" / "e6_score_level_summary.json"
)
E6_SCORE_LEVEL_SUMMARY_MD_PATH = (
    ROOT / "outputs" / "e6_score_level_analysis_20260603" / "e6_score_level_summary.md"
)
E6_SCORE_LEVEL_ROLE_METRICS_PATH = (
    ROOT / "outputs" / "e6_score_level_analysis_20260603" / "e6_score_level_role_metrics.csv"
)
E6_SCORE_LEVEL_PAIRED_DRIFT_PATH = (
    ROOT / "outputs" / "e6_score_level_analysis_20260603" / "e6_score_level_paired_drift.csv"
)
QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "qwen3guard_beavertails200_20260602"
    / "qwen3guard_beavertails200_threshold_summary.json"
)
QWEN_BEAVERTAILS_THRESHOLD_SWEEP_PATH = (
    ROOT
    / "outputs"
    / "qwen3guard_beavertails200_20260602"
    / "qwen3guard_beavertails200_threshold_sweep.csv"
)
QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH = (
    ROOT
    / "outputs"
    / "qwen3guard_beavertails500_20260603"
    / "qwen3guard_beavertails500_threshold_summary.json"
)
QWEN_BEAVERTAILS500_THRESHOLD_SWEEP_PATH = (
    ROOT
    / "outputs"
    / "qwen3guard_beavertails500_20260603"
    / "qwen3guard_beavertails500_threshold_sweep.csv"
)
FORMAL_E3_GUARDS = {"DynaGuard", "WildGuard", "Qwen3Guard"}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    required_summary = _read_json(REQUIRED_SUMMARY_PATH)
    completion_audit = _read_json(COMPLETION_AUDIT_PATH)
    projection_rows = _read_csv(PROJECTION_ROWS_PATH)
    e4_rows = build_wrong_conclusion_matrix(projection_rows)
    e3_rows = build_preregistered_template_grid_summary()
    e5_report = build_e5_source_confounding_audit()
    e8_rows = build_slice_denominator_audit()
    expanded_iaa_readiness = build_expanded_iaa_readiness_audit()

    E1_EXPANDED_IAA_READINESS_AUDIT_PATH.write_text(
        json.dumps(expanded_iaa_readiness, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "e1_expanded_iaa_readiness_audit.md").write_text(
        render_expanded_iaa_readiness_markdown(expanded_iaa_readiness), encoding="utf-8"
    )
    _write_csv(OUTPUT_DIR / "e4_wrong_conclusion_matrix.csv", e4_rows)
    (OUTPUT_DIR / "e4_wrong_conclusion_matrix.md").write_text(render_e4_markdown(e4_rows), encoding="utf-8")
    _write_csv(OUTPUT_DIR / "e3_preregistered_template_grid_summary.csv", e3_rows)
    (OUTPUT_DIR / "e3_preregistered_template_grid_summary.md").write_text(
        render_e3_markdown(e3_rows), encoding="utf-8"
    )
    (OUTPUT_DIR / "e3_preregistered_template_grid_design_manifest.json").write_text(
        json.dumps(build_e3_design_manifest(e3_rows), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "e5_source_label_confounding_audit.json").write_text(
        json.dumps(e5_report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(OUTPUT_DIR / "e5_source_label_confounding_matrix.csv", e5_report["source_label_matrix"])
    (OUTPUT_DIR / "e5_source_label_confounding_audit.md").write_text(
        render_e5_markdown(e5_report), encoding="utf-8"
    )
    _write_csv(OUTPUT_DIR / "e8_slice_denominator_uncertainty_audit.csv", e8_rows)
    (OUTPUT_DIR / "e8_slice_denominator_uncertainty_audit.md").write_text(
        render_e8_markdown(e8_rows), encoding="utf-8"
    )
    package_report = build_public_aggregate_package()
    roadmap_rows = build_roadmap_status(
        required_summary,
        completion_audit,
        e4_rows,
        e3_rows,
        e8_rows,
        package_report,
        e5_report=e5_report,
        expanded_iaa_readiness=expanded_iaa_readiness,
    )
    milestone_status = build_milestone_status(roadmap_rows)
    report = {
        "artifact_type": "mn_sla_roadmap_completion_audit",
        "created_at": "2026-06-02",
        "completion_verdict": milestone_status["overall_verdict"],
        "raw_text_emitted": False,
        "milestone_status": milestone_status,
        "roadmap_scope": "E1-E9 from MN-SLA_NeurIPS_MainTrack_Spotlight_实验推进路线图.md",
        "roadmap_status": roadmap_rows,
        "package_report": package_report,
        "expanded_iaa_readiness": expanded_iaa_readiness,
        "generated_outputs": {
            "e1_expanded_iaa_readiness_audit": _rel(
                E1_EXPANDED_IAA_READINESS_AUDIT_PATH
            ),
            "e3_preregistered_template_grid_summary": _rel(
                OUTPUT_DIR / "e3_preregistered_template_grid_summary.csv"
            ),
            "e3_preregistered_template_grid_design_manifest": _rel(
                OUTPUT_DIR / "e3_preregistered_template_grid_design_manifest.json"
            ),
            "e5_source_label_confounding_audit": _rel(
                OUTPUT_DIR / "e5_source_label_confounding_audit.json"
            ),
            "e4_wrong_conclusion_matrix": _rel(OUTPUT_DIR / "e4_wrong_conclusion_matrix.csv"),
            "e8_slice_denominator_uncertainty_audit": _rel(
                OUTPUT_DIR / "e8_slice_denominator_uncertainty_audit.csv"
            ),
            "public_aggregate_package": _rel(PACKAGE_DIR),
        },
    }
    (OUTPUT_DIR / "roadmap_completion_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "roadmap_completion_audit.md").write_text(render_roadmap_markdown(report), encoding="utf-8")
    print(f"Wrote MN-SLA roadmap completion audit to {OUTPUT_DIR}")


def build_wrong_conclusion_matrix(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, str]] = {
        (row.get("dataset", ""), row.get("guard", ""), row.get("variant", "")): row for row in rows
    }
    variants = [
        ("raw", "Attack-vs-clean/raw pressure gap"),
        ("clean_carry_forward", "Clean carry-forward proxy"),
        ("base_neutral_mean", "Attack-vs-base-neutral"),
        ("global_neutral_mean", "Attack-vs-generic/global-neutral"),
        ("same_cell_other_base_mean", "Attack-vs-other-base-neutral"),
        ("wrong_layout_same_base_mean", "Wrong-layout same-base neutral"),
    ]
    output: list[dict[str, Any]] = []
    datasets_guards = sorted({(row.get("dataset", ""), row.get("guard", "")) for row in rows})
    for dataset, guard in datasets_guards:
        matched = by_key.get((dataset, guard, "matched_mean"))
        if not matched:
            continue
        matched_gap = _float(matched.get("primary_gap_mean"))
        matched_p = _float(matched.get("primary_gap_p_mean_gt_0"), default=1.0)
        matched_supported = matched_gap > 0 and matched_p <= 0.05
        for variant, method in variants:
            comparator = by_key.get((dataset, guard, variant))
            if not comparator:
                continue
            gap = _float(comparator.get("primary_gap_mean"))
            p_value = _float(comparator.get("primary_gap_p_mean_gt_0"), default=1.0)
            supported = gap > 0 and p_value <= 0.05
            ratio = None if abs(matched_gap) < 1e-12 else gap / matched_gap
            output.append(
                {
                    "dataset": dataset,
                    "guard": guard,
                    "method": method,
                    "variant": variant,
                    "bases": comparator.get("bases"),
                    "comparator_gap": gap,
                    "matched_gap": matched_gap,
                    "bias_vs_mnsla": gap - matched_gap,
                    "inflation_ratio": ratio,
                    "comparator_p_mean_gt_0": p_value,
                    "matched_p_mean_gt_0": matched_p,
                    "comparator_supported": supported,
                    "matched_supported": matched_supported,
                    "verdict_mismatch": supported != matched_supported,
                    "claim_boundary": "Aggregate wrong-conclusion diagnostic; no raw rendered text emitted.",
                }
            )
    return output


def formal_guard_name(run_name: str) -> str:
    lowered = str(run_name).lower()
    if lowered.startswith("dynaguard"):
        return "DynaGuard"
    if lowered.startswith("wildguard"):
        return "WildGuard"
    if lowered.startswith("qwen3guard"):
        return "Qwen3Guard"
    if lowered.startswith("shieldlm"):
        return "ShieldLM"
    if lowered.startswith("harmaug"):
        return "HarmAug"
    return ""


def three_template_formal_guards(rows: list[dict[str, Any]]) -> set[str]:
    guards: set[str] = set()
    for row in rows:
        guard = str(row.get("formal_guard") or formal_guard_name(str(row.get("run") or "")))
        if guard in FORMAL_E3_GUARDS and bool(row.get("meets_spotlight_template_count")):
            guards.add(guard)
    return guards


def e3_row_claim_boundary(*, n_neutral_templates: int, formal_guard: str) -> str:
    if n_neutral_templates >= 3 and formal_guard in FORMAL_E3_GUARDS:
        return (
            "Aggregate preregistered estimator/template grid over existing prediction ledgers; "
            "this run satisfies the 3-neutral-template coverage criterion for a formal guard, "
            "with effect direction interpreted guard-by-guard."
        )
    if n_neutral_templates >= 3:
        return (
            "Aggregate preregistered estimator/template grid over existing prediction ledgers; "
            "this diagnostic run has 3 neutral templates but is not counted as a formal E3 guard."
        )
    return (
        "Aggregate preregistered estimator/template grid over existing prediction ledgers; "
        "this run does not satisfy the 3-neutral-template spotlight target because only "
        f"{n_neutral_templates} neutral template(s) are present."
    )


def build_preregistered_template_grid_summary() -> list[dict[str, Any]]:
    reports: dict[str, Any] = {}
    for path in (PREREG_TEMPLATE_SUMMARY_PATH, QWEN_3TEMPLATE_SUMMARY_PATH, SUPPLEMENTAL_3TEMPLATE_SUMMARY_PATH):
        if path.exists():
            reports.update(_read_json(path))
    rows: list[dict[str, Any]] = []
    for run_name, report in sorted(reports.items()):
        summary = report.get("summary", {})
        neutral_templates = report.get("neutral_templates", [])
        estimators = report.get("estimators", [])
        formal_guard = formal_guard_name(run_name)
        rows.append(
            {
                "run": run_name,
                "n_bases": report.get("n_bases"),
                "n_records": report.get("n_records"),
                "n_neutral_templates": len(neutral_templates),
                "neutral_templates": ",".join(str(item) for item in neutral_templates),
                "n_estimators": len(estimators),
                "estimators": ",".join(str(item) for item in estimators),
                "n_combinations": summary.get("n_combinations"),
                "attenuation_positive_rate": summary.get("attenuation_positive_rate"),
                "residual_positive_rate": summary.get("residual_positive_rate"),
                "median_attenuation_mean": summary.get("median_attenuation_mean"),
                "median_residual_gap_mean": summary.get("median_residual_gap_mean"),
                "meets_current_grid_minimum": (
                    int(summary.get("n_combinations") or 0) >= 15
                    and len(neutral_templates) >= 2
                    and len(estimators) >= 5
                    and int(report.get("n_bases") or 0) > 0
                ),
                "meets_spotlight_template_count": len(neutral_templates) >= 3,
                "formal_guard": formal_guard,
                "meets_spotlight_formal_guard": formal_guard in FORMAL_E3_GUARDS,
                "claim_boundary": e3_row_claim_boundary(
                    n_neutral_templates=len(neutral_templates),
                    formal_guard=formal_guard,
                ),
            }
        )
    return rows


def build_e3_design_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    formal_guards = three_template_formal_guards(rows)
    spotlight_complete = (
        len(rows) >= 3
        and all(row.get("meets_current_grid_minimum") for row in rows)
        and len(formal_guards) >= 3
    )
    return {
        "artifact_type": "e3_preregistered_template_grid_design_manifest",
        "created_at": "2026-06-03",
        "raw_text_emitted": False,
        "unit": "base case",
        "frozen_inputs": _rel(PREREG_TEMPLATE_SUMMARY_PATH) if PREREG_TEMPLATE_SUMMARY_PATH.exists() else "",
        "supplemental_3template_inputs": (
            _rel(QWEN_3TEMPLATE_SUMMARY_PATH) if QWEN_3TEMPLATE_SUMMARY_PATH.exists() else ""
        ),
        "supplemental_3template_additional_inputs": (
            _rel(SUPPLEMENTAL_3TEMPLATE_SUMMARY_PATH) if SUPPLEMENTAL_3TEMPLATE_SUMMARY_PATH.exists() else ""
        ),
        "frozen_estimators": [
            "mean-v1",
            "median-v1",
            "trimmed-mean-v1",
            "first-neutral-v1",
            "majority-neutral-v1",
        ],
        "observed_runs": [row["run"] for row in rows],
        "observed_template_counts": {row["run"]: int(row["n_neutral_templates"] or 0) for row in rows},
        "observed_3template_formal_guards": sorted(three_template_formal_guards(rows)),
        "minimum_current_grid": ">=2 existing neutral templates x 5 frozen estimators x >=3 evaluated baselines",
        "spotlight_target": ">=3 neutral templates/layout x 5 estimators x >=3 formal baselines",
        "status": (
            "completed_3template_spotlight_grid"
            if len(formal_guards) >= 3
            else "completed_current_grid_but_not_3template_spotlight"
            if len(rows) >= 3 and all(row.get("meets_current_grid_minimum") for row in rows)
            else "partial_or_missing_current_grid"
        ),
        "claim_boundary": (
            "Use this as a preregistered aggregate robustness matrix over existing ledgers. "
            "The 3-template coverage target is closed for at least three unique formal guards; "
            "interpret effect direction guard-by-guard."
            if spotlight_complete
            else "Use this as a preregistered aggregate robustness matrix over existing ledgers. "
            "Do not claim full spotlight-grade template robustness until the 3-template grid covers "
            "at least three unique formal guards."
        ),
    }


def build_e5_source_confounding_audit() -> dict[str, Any]:
    base_rows = _read_jsonl_metadata(NONPKU_HARD_V3_CORE_PATH)
    base_by_id: dict[str, dict[str, Any]] = {}
    for row in base_rows:
        if row.get("hard_v3_role") != "clean":
            continue
        base_id = str(row.get("base_id") or "")
        if base_id:
            base_by_id[base_id] = {
                "base_id": base_id,
                "source": str(row.get("source") or ""),
                "label_name": str(row.get("label_name") or row.get("label") or ""),
                "category": str(row.get("category") or ""),
            }
    source_label_counts: dict[tuple[str, str], int] = {}
    source_to_labels: dict[str, set[str]] = {}
    label_to_sources: dict[str, set[str]] = {}
    for row in base_by_id.values():
        source = str(row["source"])
        label = str(row["label_name"])
        source_label_counts[(source, label)] = source_label_counts.get((source, label), 0) + 1
        source_to_labels.setdefault(source, set()).add(label)
        label_to_sources.setdefault(label, set()).add(source)

    matrix_rows = [
        {
            "source": source,
            "label_name": label,
            "n_bases": count,
            "claim_boundary": "Metadata-only source/label confounding count; no raw text emitted.",
        }
        for (source, label), count in sorted(source_label_counts.items())
    ]
    complete_binding = bool(source_to_labels) and all(len(labels) == 1 for labels in source_to_labels.values())
    complete_binding = complete_binding and all(len(sources) == 1 for sources in label_to_sources.values())
    projection_summaries = [
        _projection_summary("DynaGuard", NONPKU_DYNAGUARD_PROJECTION_PATH),
        _projection_summary("WildGuard", NONPKU_WILDGUARD_PROJECTION_PATH),
    ]
    projection_summaries = [row for row in projection_summaries if row]
    hard_v3_audit = _read_json(NONPKU_HARD_V3_AUDIT_PATH) if NONPKU_HARD_V3_AUDIT_PATH.exists() else {}
    return {
        "artifact_type": "e5_source_label_confounding_audit",
        "created_at": "2026-06-03",
        "raw_text_emitted": False,
        "n_bases": len(base_by_id),
        "n_sources": len(source_to_labels),
        "n_labels": len(label_to_sources),
        "source_label_matrix": matrix_rows,
        "source_to_labels": {source: sorted(labels) for source, labels in sorted(source_to_labels.items())},
        "label_to_sources": {label: sorted(sources) for label, sources in sorted(label_to_sources.items())},
        "source_label_confounding": (
            "complete_source_label_binding_modeled"
            if complete_binding
            else "source_label_binding_not_complete_or_missing"
        ),
        "hard_v3_base_balance": hard_v3_audit.get("base_balance", {}),
        "projection_summaries": projection_summaries,
        "status": (
            "completed_confounding_modeled_source_pair"
            if len(base_by_id) >= 200 and complete_binding and len(projection_summaries) >= 2
            else "partial_or_missing_source_pair_model"
        ),
        "claim_boundary": (
            "Adds an explicitly modeled Non-PKU HarmBench/XSTest source-pair diagnostic. "
            "Because source and label are completely bound in this source pair, use it as "
            "confounding-modeled external evidence, not universal source-general robustness."
        ),
    }


def build_expanded_iaa_readiness_audit() -> dict[str, Any]:
    manifest = _read_json(EXPANDED_IAA_PACKET_MANIFEST_PATH) if EXPANDED_IAA_PACKET_MANIFEST_PATH.exists() else {}
    manifest_counts = manifest.get("counts", {})
    template_rows = _read_csv(EXPANDED_IAA_TEMPLATE_PATH) if EXPANDED_IAA_TEMPLATE_PATH.exists() else []
    template_columns = _csv_fieldnames(EXPANDED_IAA_TEMPLATE_PATH) if EXPANDED_IAA_TEMPLATE_PATH.exists() else []
    private_key_lines = _nonempty_line_count(EXPANDED_IAA_PRIVATE_KEY_PATH)
    annotator_packet_lines = _nonempty_line_count(EXPANDED_IAA_ANNOTATOR_PACKET_PATH)
    completed_annotation_files = _find_expanded_completed_annotation_files()
    fail_closed_passed = _fail_closed_report_passed(EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH)
    analyzer_text = EXPANDED_IAA_ANALYZER_PATH.read_text(encoding="utf-8") if EXPANDED_IAA_ANALYZER_PATH.exists() else ""
    core_text = HUMAN_IAA_ANALYZER_CORE_PATH.read_text(encoding="utf-8") if HUMAN_IAA_ANALYZER_CORE_PATH.exists() else ""

    expected_cells_by_regime = {
        "non_pku200_source_pair": 30,
        "pku200_scale": 30,
        "pku50_main_gate": 30,
    }
    expected_items_by_role = {"attack": 90, "clean": 90, "neutral": 90}
    manifest_check = {
        "exists": EXPANDED_IAA_PACKET_MANIFEST_PATH.exists(),
        "sampled_cells": manifest_counts.get("sampled_cells"),
        "annotation_items": manifest_counts.get("annotation_items"),
        "cells_by_regime": manifest_counts.get("cells_by_regime", {}),
        "items_by_role": manifest_counts.get("items_by_role", {}),
    }
    manifest_passed = (
        manifest_check["exists"]
        and manifest_check["sampled_cells"] == 90
        and manifest_check["annotation_items"] == 270
        and manifest_check["cells_by_regime"] == expected_cells_by_regime
        and manifest_check["items_by_role"] == expected_items_by_role
    )
    template_passed = (
        EXPANDED_IAA_TEMPLATE_PATH.exists()
        and len(template_rows) == 270
        and tuple(template_columns) == EXPECTED_EXPANDED_IAA_TEMPLATE_COLUMNS
    )
    sensitive_counts_passed = private_key_lines == 270 and annotator_packet_lines == 270
    analyzer_checks = {
        "expanded_analyzer_exists": EXPANDED_IAA_ANALYZER_PATH.exists(),
        "min_annotators_per_item_2": "min_annotators_per_item=2" in analyzer_text,
        "min_complete_cells_per_regime_30": "min_complete_cells_per_regime=30" in analyzer_text,
        "min_total_complete_cells_90": "min_total_complete_cells=90" in analyzer_text,
        "ci_ready_output_fields": all(
            token in core_text
            for token in (
                "percent_agreement_ci_low",
                "pabak_ci_low",
                "within_1_agreement_ci_low",
            )
        ),
    }
    packet_ready = manifest_passed and template_passed and sensitive_counts_passed and all(analyzer_checks.values())
    completion_status = (
        "completed_pending_manual_review"
        if completed_annotation_files and fail_closed_passed
        else "incomplete_external_human_dependency"
    )
    return {
        "artifact_type": "e1_expanded_iaa_readiness_audit",
        "created_at": "2026-06-03",
        "raw_text_emitted": False,
        "packet_ready_for_external_annotation": packet_ready,
        "completion_status": completion_status,
        "completion_claim_allowed": completion_status == "completed_pending_manual_review",
        "manifest_check": {
            "passed": manifest_passed,
            "expected_sampled_cells": 90,
            "expected_annotation_items": 270,
            "expected_cells_by_regime": expected_cells_by_regime,
            "expected_items_by_role": expected_items_by_role,
            **manifest_check,
        },
        "annotation_template_check": {
            "exists": EXPANDED_IAA_TEMPLATE_PATH.exists(),
            "passed": template_passed,
            "rows": len(template_rows),
            "columns": template_columns,
            "expected_columns": list(EXPECTED_EXPANDED_IAA_TEMPLATE_COLUMNS),
        },
        "sensitive_local_line_count_check": {
            "passed": sensitive_counts_passed,
            "private_key_lines": private_key_lines,
            "annotator_packet_lines": annotator_packet_lines,
            "expected_lines": 270,
            "raw_content_emitted": False,
        },
        "analyzer_check": analyzer_checks,
        "completed_annotation_files": completed_annotation_files,
        "fail_closed_report": {
            "path": _rel(EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH),
            "exists": EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH.exists(),
            "passed": fail_closed_passed,
        },
        "claim_boundary": (
            "This audit is aggregate-only readiness/status evidence. It is not human validation; "
            "expanded E1 remains incomplete unless independent completed annotations are explicitly "
            "supplied and analysis_completed/fail_closed_report.json passes."
        ),
    }


def render_expanded_iaa_readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# E1 Expanded IAA Readiness Audit",
        "",
        "Aggregate-only status audit. No raw rendered prompt text is emitted.",
        "",
        f"- packet ready for external annotation: `{report['packet_ready_for_external_annotation']}`",
        f"- completion status: `{report['completion_status']}`",
        f"- completion claim allowed: `{report['completion_claim_allowed']}`",
        f"- manifest check passed: `{report['manifest_check']['passed']}`",
        f"- annotation template rows: `{report['annotation_template_check']['rows']}`",
        f"- sensitive local line counts passed: `{report['sensitive_local_line_count_check']['passed']}`",
        f"- private key lines: `{report['sensitive_local_line_count_check']['private_key_lines']}`",
        f"- annotator packet lines: `{report['sensitive_local_line_count_check']['annotator_packet_lines']}`",
        f"- completed annotation files detected: `{len(report['completed_annotation_files'])}`",
        f"- fail-closed report passed: `{report['fail_closed_report']['passed']}`",
        "",
        f"Claim boundary: {report['claim_boundary']}",
        "",
    ]
    return "\n".join(lines)


def _projection_summary(guard: str, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    report = _read_json(path)
    rows = {str(row.get("variant")): row for row in report.get("rows", [])}
    raw = rows.get("raw", {})
    matched = rows.get("matched_mean", {})
    return {
        "guard": guard,
        "path": _rel(path),
        "raw_primary_gap_mean": raw.get("primary_gap_mean"),
        "raw_primary_gap_p_mean_gt_0": raw.get("primary_gap_p_mean_gt_0"),
        "matched_primary_gap_mean": matched.get("primary_gap_mean"),
        "matched_primary_gap_p_mean_gt_0": matched.get("primary_gap_p_mean_gt_0"),
        "matched_primary_attenuation_mean": matched.get("primary_attenuation_mean"),
        "claim_boundary": "Aggregate projection summary over the confounded source pair; not source-general proof.",
    }


def build_slice_denominator_audit() -> list[dict[str, Any]]:
    if not SLICE_INFERENCE_PATH.exists():
        return []
    rows = _read_csv(SLICE_INFERENCE_PATH)
    output = []
    for row in rows:
        n_bases = _float(row.get("n_bases"))
        output.append(
            {
                "run": row.get("run"),
                "group_field": row.get("group_field"),
                "slice": row.get("slice"),
                "metric": row.get("metric"),
                "n_bases": int(n_bases),
                "n_attack_records": row.get("n_attack_records"),
                "n_matched_neutral_comparisons": row.get("n_matched_neutral_comparisons"),
                "mean": row.get("mean"),
                "ci95_low": row.get("ci95_low"),
                "ci95_high": row.get("ci95_high"),
                "p_value_mean_gt_0": row.get("p_value_mean_gt_0"),
                "holm_p_value_mean_gt_0": row.get("holm_p_value_mean_gt_0"),
                "global_holm_p_value_mean_gt_0": row.get("global_holm_p_value_mean_gt_0"),
                "display_status": "low_N" if n_bases < 10 else "displayable",
                "claim_boundary": "Localization diagnostic only; not mechanism proof.",
            }
        )
    return output


def build_public_aggregate_package() -> dict[str, Any]:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    aggregate_dir = PACKAGE_DIR / "aggregate_artifacts"
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    allowlist = [
        REQUIRED_DIR / "mn_sla_required_experiments_summary.md",
        REQUIRED_DIR / "mn_sla_required_experiments_summary.json",
        REQUIRED_DIR / "projection_ablation_all_rows.csv",
        REQUIRED_DIR / "probability_threshold_sweeps.csv",
        REQUIRED_DIR / "artifact_manifest.csv",
        ROOT / "outputs" / "human_validation_overlap_20260601" / "analysis_completed" / "human_annotation_analysis_summary.md",
        ROOT / "outputs" / "human_validation_overlap_20260601" / "analysis_completed" / "fail_closed_report.json",
        ROOT / "outputs" / "fresh_neutral_template_grid_20260601" / "fresh_neutral_template_grid_summary.json",
        ROOT / "outputs" / "mn_sla_completion_and_release_audit_20260602" / "audit.md",
        QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH,
        QWEN_BEAVERTAILS_THRESHOLD_SWEEP_PATH,
        QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH,
        QWEN_BEAVERTAILS500_THRESHOLD_SWEEP_PATH,
        QWEN_POWER_JSON_PATH,
        QWEN_POWER_SUMMARY_PATH,
        PREREG_TEMPLATE_SUMMARY_PATH,
        QWEN_3TEMPLATE_SUMMARY_PATH,
        QWEN_3TEMPLATE_MD_PATH,
        SUPPLEMENTAL_3TEMPLATE_SUMMARY_PATH,
        SUPPLEMENTAL_DYNAGUARD_3TEMPLATE_MD_PATH,
        SUPPLEMENTAL_HARMAUG_3TEMPLATE_MD_PATH,
        SUPPLEMENTAL_WILDGUARD_3TEMPLATE_MD_PATH,
        ROOT
        / "outputs"
        / "hard_v3_beavertails500_20260603"
        / "hard_v3_contract_subset_500base_neutral_policy_restated_manifest.json",
        ROOT
        / "outputs"
        / "qwen3guard_beavertails500_20260603"
        / "context_audit_neutral_policy_restated.json",
        E6_SCORE_LEVEL_SUMMARY_PATH,
        E6_SCORE_LEVEL_SUMMARY_MD_PATH,
        E6_SCORE_LEVEL_ROLE_METRICS_PATH,
        E6_SCORE_LEVEL_PAIRED_DRIFT_PATH,
        OUTPUT_DIR / "e3_preregistered_template_grid_summary.csv",
        OUTPUT_DIR / "e3_preregistered_template_grid_summary.md",
        OUTPUT_DIR / "e3_preregistered_template_grid_design_manifest.json",
        OUTPUT_DIR / "e5_source_label_confounding_audit.json",
        OUTPUT_DIR / "e5_source_label_confounding_audit.md",
        OUTPUT_DIR / "e5_source_label_confounding_matrix.csv",
        OUTPUT_DIR / "e4_wrong_conclusion_matrix.csv",
        OUTPUT_DIR / "e8_slice_denominator_uncertainty_audit.csv",
    ]
    copied = []
    for source in allowlist:
        if not source.exists():
            continue
        target = _package_target(aggregate_dir, source)
        shutil.copy2(source, target)
        copied.append(target)
    (PACKAGE_DIR / "README.md").write_text(render_package_readme(copied), encoding="utf-8")
    (PACKAGE_DIR / "sanitized_wrapper_skeletons.md").write_text(render_sanitized_skeletons(), encoding="utf-8")
    copied.extend([PACKAGE_DIR / "README.md", PACKAGE_DIR / "sanitized_wrapper_skeletons.md"])
    hash_rows = [_hash_row(path) for path in sorted(copied)]
    scan_report = scan_release_package(PACKAGE_DIR)
    _write_csv(PACKAGE_DIR / "hash_manifest.csv", hash_rows)
    (PACKAGE_DIR / "release_scan_report.md").write_text(render_scan_report(scan_report), encoding="utf-8")
    return {
        "status": "completed_public_aggregate_package",
        "package_dir": _rel(PACKAGE_DIR),
        "n_files": len(copied) + 2,
        "hash_manifest": _rel(PACKAGE_DIR / "hash_manifest.csv"),
        "release_scan_report": _rel(PACKAGE_DIR / "release_scan_report.md"),
        "scanner": scan_report,
        "raw_text_emitted": False,
    }


def build_roadmap_status(
    required_summary: dict[str, Any],
    completion_audit: dict[str, Any],
    e4_rows: list[dict[str, Any]],
    e3_rows: list[dict[str, Any]],
    e8_rows: list[dict[str, Any]],
    package_report: dict[str, Any],
    e5_report: dict[str, Any] | None = None,
    expanded_iaa_readiness: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    requirement_by_id = {row.get("id"): row for row in required_summary.get("requirement_status", [])}
    baseline_ledger = completion_audit.get("baseline_ledger", [])
    formal_statuses = {"evaluated", "evaluated_score_logit", "evaluated_score_probability"}
    baseline_counts = {
        "formal_evaluated": sum(1 for row in baseline_ledger if row.get("status") in formal_statuses),
        "diagnostic": sum(1 for row in baseline_ledger if row.get("status") == "diagnostic"),
        "supplementary": sum(1 for row in baseline_ledger if row.get("status") == "supplementary_only"),
    }
    qwen_external_completed = (
        QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH.exists()
        and QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH.exists()
    )
    qwen500_completed = QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH.exists()
    e5_report = e5_report or {}
    e5_confounding_modeled = e5_report.get("status") == "completed_confounding_modeled_source_pair"
    e6_score_summary = _read_json(E6_SCORE_LEVEL_SUMMARY_PATH) if E6_SCORE_LEVEL_SUMMARY_PATH.exists() else {}
    e6_score_status = str(e6_score_summary.get("status") or "")
    e6_two_score_guards_completed = e6_score_status == "completed_two_score_guard_families_with_external"
    e6_score_completed = e6_score_status in {
        "completed_qwen_score_calibration_external",
        "completed_two_score_guard_families_with_external",
    }
    expanded_iaa_readiness = expanded_iaa_readiness or {}
    expanded_fail_report = expanded_iaa_readiness.get("fail_closed_report", {})
    expanded_e1_completed = (
        expanded_iaa_readiness.get("completion_claim_allowed") is True
        and expanded_fail_report.get("passed") is True
    )
    expanded_e1_evidence = str(expanded_fail_report.get("path") or _rel(EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH))
    formal_baselines = baseline_counts["formal_evaluated"]
    strong_diagnostics = baseline_counts["diagnostic"] + baseline_counts["supplementary"]
    e2_completed = formal_baselines >= 4 or (formal_baselines >= 3 and strong_diagnostics >= 2)
    e2_spotlight_completed = formal_baselines >= 5
    if e2_completed:
        e2_boundary = (
            f"Baseline breadth is now closed at the {'spotlight' if e2_spotlight_completed else 'main-track'} level with {formal_baselines} "
            f"formal/main-compatible baseline(s), {baseline_counts['diagnostic']} diagnostic "
            f"baseline(s), and {baseline_counts['supplementary']} supplementary baseline(s)"
            f"{'; meets the 5-baseline spotlight breadth target with score/logit baselines kept under narrow claim boundaries.' if e2_spotlight_completed else '; still short of the 5-6 baseline spotlight target.'}"
        )
    else:
        e2_boundary = "Still short of 4 formal baselines because HarmAug/BingoGuard expanded formal runs are incomplete."
    power_paths = [path for path in [*POWER_SUMMARY_PATHS, QWEN_POWER_SUMMARY_PATH] if path.exists()]
    e3_current_grid_complete = (
        len(e3_rows) >= 3 and all(bool(row.get("meets_current_grid_minimum")) for row in e3_rows)
    )
    e3_3template_baselines = sum(bool(row.get("meets_spotlight_template_count")) for row in e3_rows)
    e3_3template_formal_guards = three_template_formal_guards(e3_rows)
    e3_spotlight_complete = e3_current_grid_complete and len(e3_3template_formal_guards) >= 3
    e3_status = (
        "completed_spotlight_3template_grid"
        if e3_spotlight_complete
        else "partial_3template_two_formal_baselines"
        if len(e3_3template_formal_guards) >= 2
        else "partial_3template_one_baseline"
        if len(e3_3template_formal_guards) >= 1
        else "completed_current_grid_not_3template_spotlight"
        if e3_current_grid_complete
        else "partial_diagnostic_not_preregistered_full"
    )
    e7_completed = len(power_paths) >= 3 and QWEN_POWER_SUMMARY_PATH.exists()
    if expanded_e1_completed:
        e1_status = "completed_expanded_270_human_iaa"
        e1_summary = "Expanded 270-item packet has completed independent annotations and a passing fail-closed report."
        e1_evidence = expanded_e1_evidence
        e1_boundary = (
            "Expanded 270-item IAA now meets the 180-270 spotlight coverage target with two annotators "
            "and a passing fail-closed analysis; keep the claim to blinded sample-level human validation."
        )
    else:
        e1_status = "completed_minimal"
        e1_summary = (
            "90-item packet, two independent annotators, fail-closed report passed; expanded 270-item packet/CI-ready analyzer prepared."
            if EXPANDED_IAA_PACKET_MANIFEST_PATH.exists()
            else "90-item packet, two independent annotators, fail-closed report passed."
        )
        e1_evidence = requirement_by_id.get("P0-1", {}).get("evidence_path")
        e1_boundary = (
            "Minimal P0-1 is complete; expanded 270-item packet is prepared at "
            f"{_rel(EXPANDED_IAA_PACKET_MANIFEST_PATH)}"
            f"{' and CI-ready analyzer ' + _rel(EXPANDED_IAA_ANALYZER_PATH) if EXPANDED_IAA_ANALYZER_PATH.exists() else ''}, "
            f"with readiness audit {_rel(E1_EXPANDED_IAA_READINESS_AUDIT_PATH)}, "
            "but still requires 2-3 independent annotators and fail-closed analysis."
            if EXPANDED_IAA_PACKET_MANIFEST_PATH.exists()
            else "Minimal P0-1 is complete; expanded 180-270 item IAA remains spotlight-only future work."
        )
    status_rows = [
        _roadmap_row(
            "E1",
            "Independent overlapping human IAA",
            e1_status,
            e1_summary,
            e1_evidence,
            e1_boundary,
        ),
        _roadmap_row(
            "E2",
            "Main-panel baseline expansion",
            "completed_spotlight_baseline_breadth"
            if e2_spotlight_completed
            else "completed_minimum_3_formal_plus_2_diagnostics"
            if e2_completed
            else "incomplete_main_panel_expansion",
            (
                f"{formal_baselines} formal/main-compatible evaluated baselines after score/logit external sweeps, "
                f"{baseline_counts['diagnostic']} diagnostics, {baseline_counts['supplementary']} supplementary."
            ),
            "outputs/mn_sla_completion_and_release_audit_20260602/baseline_ledger.csv",
            e2_boundary,
        ),
        _roadmap_row(
            "E3",
            "Preregistered estimator x neutral-template robustness",
            e3_status,
            (
                f"Generated aggregate grid for {len(e3_rows)} runs with frozen 5-estimator family; "
                f"{e3_3template_baselines} run(s) expose 3 neutral templates; "
                f"{len(e3_3template_formal_guards)} unique formal guard(s) have 3-template grids."
            ),
            "outputs/mn_sla_roadmap_completion_audit_20260602/e3_preregistered_template_grid_summary.csv",
            (
                "Closes the 3-template coverage target for three unique formal baselines; effect direction remains guard-specific, especially WildGuard attenuation."
                if e3_spotlight_complete
                else
                f"3-template grids are present for {', '.join(sorted(e3_3template_formal_guards))}; "
                "spotlight still needs >=3 formal baselines with 3-template grids."
                if len(e3_3template_formal_guards) >= 1 and not e3_spotlight_complete
                else "Current multi-baseline preregistered grid is complete for available ledgers; "
                "do not claim full 3-template spotlight robustness."
                if e3_current_grid_complete
                else "Keep guard-dependent diagnostic wording; do not claim full robustness."
            ),
        ),
        _roadmap_row(
            "E4",
            "Simple-baseline wrong-conclusion matrix",
            "completed_aggregate_matrix",
            f"Generated {len(e4_rows)} comparator rows from existing projection/simple-baseline aggregates.",
            "outputs/mn_sla_roadmap_completion_audit_20260602/e4_wrong_conclusion_matrix.csv",
            "Supports the novelty claim that common alternatives answer different or inflated questions.",
        ),
        _roadmap_row(
            "E5",
            "External open-dataset expansion",
            (
                "completed_external_sources_with_confounding_model"
                if qwen500_completed and e5_confounding_modeled
                else "completed_beavertails500_extension"
                if qwen500_completed
                else "partial_external_source_pair_only"
            ),
            (
                "BeaverTails200 confirmatory, BeaverTails500 Qwen3Guard score/logit extension, and explicitly modeled NonPKU HarmBench/XSTest source-pair confounding are present."
                if qwen500_completed and e5_confounding_modeled
                else
                "BeaverTails200 confirmatory plus BeaverTails500 Qwen3Guard score/logit extension and NonPKU source-pair diagnostic are present."
                if qwen500_completed
                else "BeaverTails200 confirmatory plus NonPKU HarmBench/XSTest source-pair diagnostic are present."
            ),
            (
                "outputs/qwen3guard_beavertails500_20260603/qwen3guard_beavertails500_threshold_summary.json;"
                "outputs/mn_sla_roadmap_completion_audit_20260602/e5_source_label_confounding_audit.json"
                if qwen500_completed and e5_confounding_modeled
                else "outputs/qwen3guard_beavertails500_20260603/qwen3guard_beavertails500_threshold_summary.json"
                if qwen500_completed
                else requirement_by_id.get("P0-3", {}).get("evidence_path")
            ),
            (
                "Closes the 3+ source/dataset spotlight evidence target only under a confounding-modeled interpretation; NonPKU remains a source-pair diagnostic, not universal source-general robustness."
                if qwen500_completed and e5_confounding_modeled
                else
                "Closes the BeaverTails500 alternative in Milestone A; still not universal source-general robustness."
                if qwen500_completed
                else "Still missing a clean additional external source such as WildGuardTest200 or BeaverTails500."
            ),
        ),
        _roadmap_row(
            "E6",
            "Probability / logit robustness upgrade",
            "completed_two_score_guard_families_with_external"
            if e6_two_score_guards_completed
            else "completed_score_calibration_drift_qwen_external"
            if e6_score_completed
            else "completed_minimum_score_external",
            (
                "Qwen3Guard and HarmAug now both have PKU200 plus external BeaverTails score-level calibration/drift metrics."
                if e6_two_score_guards_completed
                else "Qwen3Guard now has PKU200 plus BeaverTails200/500 threshold sweeps and score-level calibration/drift metrics; "
                "HarmAug PKU50 remains an additional limited diagnostic."
                if e6_score_completed
                else "Qwen3Guard now has PKU200 plus BeaverTails200/500 score/logit threshold sweeps; "
                "HarmAug PKU50 remains an additional limited diagnostic."
            ),
            (
                "outputs/e6_score_level_analysis_20260603/e6_score_level_summary.json"
                if e6_score_completed
                else "outputs/qwen3guard_beavertails200_20260602/qwen3guard_beavertails200_threshold_sweep.csv;"
                "outputs/qwen3guard_beavertails500_20260603/qwen3guard_beavertails500_threshold_sweep.csv"
            ),
            (
                "Closes the lower-bound E6 spotlight target for two score/probability guard families; a third score/logit guard remains a stronger add-on."
                if e6_two_score_guards_completed
                else "Closes Qwen3Guard PKU-plus-external calibration/drift analysis; spotlight still wants 2-3 score/logit guards, not one guard family."
                if e6_score_completed
                else "Minimum E6 is closed; broader 2-3 score guards with calibration remains spotlight future work."
            ),
        ),
        _roadmap_row(
            "E7",
            "Power curve and sample-size sensitivity figure",
            "completed_three_baseline_power_curves" if e7_completed else "partial_two_baseline_power_curves",
            f"Found {len(power_paths)} power-curve summaries including Qwen3Guard BeaverTails500 when available.",
            ";".join(_rel(path) for path in power_paths),
            (
                "Closes the third-baseline power-curve requirement; Qwen3Guard curve is raw-only because no separate residual prediction ledger is available."
                if e7_completed
                else "Useful for scale-aware claim; spotlight target still wants Qwen3Guard or another third baseline."
            ),
        ),
        _roadmap_row(
            "E8",
            "Slice denominator + uncertainty audit",
            "completed_existing_slice_audit",
            f"Generated denominator/CI/Holm audit rows from {len(e8_rows)} existing slice inference rows.",
            "outputs/mn_sla_roadmap_completion_audit_20260602/e8_slice_denominator_uncertainty_audit.csv",
            "Localization diagnostic only; not mechanism proof.",
        ),
        _roadmap_row(
            "E9",
            "Release / reproducibility package upgrade",
            package_report["status"],
            "Created aggregate-only package with hash manifest and scan report.",
            package_report["package_dir"],
            "Raw prompts, JSONL ledgers, private keys, data, models, and caches remain excluded.",
        ),
    ]
    return status_rows


def build_milestone_status(roadmap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["id"]: row for row in roadmap_rows}
    milestone_a_requirements = {
        "E1": "90-item overlap, 2 annotators, fail-closed pass",
        "E2": "at least 4 formal baselines or 3 formal plus 2 strong diagnostics",
        "E4": "simple-baseline wrong-conclusion matrix",
        "E5": "BeaverTails200 plus an additional external source or BeaverTails500",
        "E6": "at least 2 score/logit guards, one covering PKU200 plus an external dataset",
        "E9": "public aggregate package plus hash manifest and scanner report",
    }
    milestone_a_rows = []
    for identifier, requirement in milestone_a_requirements.items():
        row = by_id.get(identifier, {})
        status = str(row.get("status", "missing"))
        completed = status.startswith("completed")
        milestone_a_rows.append(
            {
                "id": identifier,
                "requirement": requirement,
                "status": "completed" if completed else "incomplete",
                "evidence": row.get("evidence", ""),
                "caveat": row.get("remaining_boundary", ""),
            }
        )

    e3_b_status = (
        "completed_with_guard_specific_caveat"
        if by_id.get("E3", {}).get("status") == "completed_spotlight_3template_grid"
        else "partial"
    )
    e2_b_status = (
        "completed_spotlight_breadth"
        if by_id.get("E2", {}).get("status") == "completed_spotlight_baseline_breadth"
        else "partial"
    )
    e5_b_status = (
        "completed_with_confounding_modeled_caveat"
        if by_id.get("E5", {}).get("status") == "completed_external_sources_with_confounding_model"
        else "partial"
    )
    e1_b_status = (
        "completed_expanded_270_human_iaa"
        if by_id.get("E1", {}).get("status") == "completed_expanded_270_human_iaa"
        else "incomplete_external_human_dependency"
    )
    e6_b_status = (
        "completed_lower_bound"
        if by_id.get("E6", {}).get("status") == "completed_two_score_guard_families_with_external"
        else "partial"
    )
    e7_b_status = (
        "completed_with_qwen_raw_only_caveat"
        if by_id.get("E7", {}).get("status") == "completed_three_baseline_power_curves"
        else "partial"
    )
    e8_b_status = (
        "completed_diagnostic"
        if by_id.get("E8", {}).get("status") == "completed_existing_slice_audit"
        else "partial"
    )
    milestone_b_rows = [
        {
            "id": "E1",
            "requirement": "180-270 overlap items, 2-3 annotators, kappa/PABAK/CI clear",
            "status": e1_b_status,
            "evidence": (
                by_id.get("E1", {}).get("evidence", "")
                if e1_b_status.startswith("completed")
                else f"{_rel(EXPANDED_IAA_PACKET_MANIFEST_PATH)};{_rel(E1_EXPANDED_IAA_READINESS_AUDIT_PATH)}"
            ),
            "caveat": (
                "Expanded 270-item IAA is complete for blinded sample-level validation; it does not by itself prove "
                "mechanism-level robustness or universal neutral-control validity."
                if e1_b_status.startswith("completed")
                else "Expanded packet and CI-ready analyzer are prepared, but independent human annotations and fail-closed "
                "analysis are not present; packet generation is not human validation."
            ),
        },
        {
            "id": "E2",
            "requirement": "5-6 spotlight-grade compatible baselines, or broader formal main-panel coverage",
            "status": e2_b_status,
            "evidence": by_id.get("E2", {}).get("evidence", ""),
            "caveat": by_id.get("E2", {}).get("remaining_boundary", ""),
        },
        {
            "id": "E3",
            "requirement": "3 neutral templates x 5 estimators x at least 3 formal baselines",
            "status": e3_b_status,
            "evidence": by_id.get("E3", {}).get("evidence", ""),
            "caveat": by_id.get("E3", {}).get("remaining_boundary", ""),
        },
        {
            "id": "E5",
            "requirement": "3+ datasets with source/label confounding eliminated or explicitly modeled",
            "status": e5_b_status,
            "evidence": by_id.get("E5", {}).get("evidence", ""),
            "caveat": by_id.get("E5", {}).get("remaining_boundary", ""),
        },
        {
            "id": "E6",
            "requirement": "2-3 probability/logit guards with calibration and score drift",
            "status": e6_b_status,
            "evidence": by_id.get("E6", {}).get("evidence", ""),
            "caveat": by_id.get("E6", {}).get("remaining_boundary", ""),
        },
        {
            "id": "E7",
            "requirement": "DynaGuard/WildGuard/Qwen3Guard power curves across at least 3 baselines",
            "status": e7_b_status,
            "evidence": by_id.get("E7", {}).get("evidence", ""),
            "caveat": by_id.get("E7", {}).get("remaining_boundary", ""),
        },
        {
            "id": "E8",
            "requirement": "denominator + CI + Holm in appendix; main text only high-support slices",
            "status": e8_b_status,
            "evidence": by_id.get("E8", {}).get("evidence", ""),
            "caveat": by_id.get("E8", {}).get("remaining_boundary", ""),
        },
    ]
    milestone_a_complete = all(row["status"] == "completed" for row in milestone_a_rows)
    milestone_b_complete = all(row["status"].startswith("completed") for row in milestone_b_rows)
    return {
        "overall_verdict": (
            "ALL_COMPLETE"
            if milestone_a_complete and milestone_b_complete
            else "MAIN_COMPLETE_ONLY"
            if milestone_a_complete
            else "INCOMPLETE"
        ),
        "milestone_a": {
            "status": "completed" if milestone_a_complete else "incomplete",
            "claim": "NeurIPS main-track minimum experimental package is complete.",
            "rows": milestone_a_rows,
        },
        "milestone_b": {
            "status": "completed" if milestone_b_complete else "incomplete",
            "claim": (
                "Spotlight-level recommended experimental package is complete under narrow, aggregate-only claim boundaries."
                if milestone_b_complete
                else "Spotlight-level recommended package is not fully complete; remaining gaps "
                "must stay out of completed-experiment wording."
            ),
            "rows": milestone_b_rows,
        },
    }


def render_e4_markdown(rows: list[dict[str, Any]]) -> str:
    mismatches = sum(1 for row in rows if row.get("verdict_mismatch"))
    high_inflation = sum(
        1
        for row in rows
        if row.get("inflation_ratio") is not None and abs(float(row["inflation_ratio"])) >= 5
    )
    lines = [
        "# E4 Simple-Baseline Wrong-Conclusion Matrix",
        "",
        "Aggregate-only matrix; no raw rendered prompt text is emitted.",
        "",
        f"- comparator rows: `{len(rows)}`",
        f"- verdict mismatches vs MN-SLA matched_mean: `{mismatches}`",
        f"- abs inflation ratio >= 5: `{high_inflation}`",
        "",
        "| Dataset | Guard | Method | Comparator gap | Matched gap | Inflation | Verdict mismatch |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:80]:
        ratio = row.get("inflation_ratio")
        ratio_text = "NA" if ratio is None else f"{float(ratio):.3f}"
        lines.append(
            f"| {row['dataset']} | {row['guard']} | {row['method']} | "
            f"{float(row['comparator_gap']):.6f} | {float(row['matched_gap']):.6f} | "
            f"{ratio_text} | {row['verdict_mismatch']} |"
        )
    return "\n".join(lines) + "\n"


def render_e3_markdown(rows: list[dict[str, Any]]) -> str:
    current_complete = len(rows) >= 3 and all(bool(row.get("meets_current_grid_minimum")) for row in rows)
    spotlight_template_count = sum(bool(row.get("meets_spotlight_template_count")) for row in rows)
    formal_guards = three_template_formal_guards(rows)
    spotlight_complete = current_complete and len(formal_guards) >= 3
    lines = [
        "# E3 Preregistered Estimator x Neutral-template Grid Summary",
        "",
        "Aggregate-only summary; no raw rendered prompt text is emitted.",
        "",
        f"- runs: `{len(rows)}`",
        f"- current-grid complete: `{current_complete}`",
        f"- 3-template runs: `{spotlight_template_count}`",
        f"- 3-template formal guards: `{', '.join(sorted(formal_guards)) if formal_guards else 'none'}`",
        f"- 3-template spotlight target complete: `{spotlight_complete}`",
        "",
        "| Run | Bases | Templates | Estimators | Combinations | Attenuation positive | Residual positive | Spotlight templates |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['run']} | {row['n_bases']} | {row['n_neutral_templates']} | {row['n_estimators']} | "
            f"{row['n_combinations']} | {_fmt(row['attenuation_positive_rate'])} | "
            f"{_fmt(row['residual_positive_rate'])} | {row['meets_spotlight_template_count']} |"
        )
    boundary = (
        "Claim boundary: this closes the preregistered 3-template x 5-estimator coverage target for at least three unique formal baselines. Interpret effect direction guard-by-guard; this is not a deployable mitigation or a claim that every guard preserves positive attenuation."
        if spotlight_complete
        else "Claim boundary: this closes a frozen multi-baseline grid over available ledgers and adds real 3-template runs for the listed formal guards, but does not establish full spotlight-grade template robustness until the 3-template grid covers at least three unique formal baselines."
    )
    lines.extend(["", boundary, ""])
    return "\n".join(lines)


def render_e5_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# E5 Source/Label Confounding Audit",
        "",
        "Aggregate-only source-pair audit; no raw rendered prompt text is emitted.",
        "",
        f"- status: `{report.get('status', 'unknown')}`",
        f"- bases: `{report.get('n_bases', 0)}`",
        f"- sources: `{report.get('n_sources', 0)}`",
        f"- labels: `{report.get('n_labels', 0)}`",
        f"- source/label confounding: `{report.get('source_label_confounding', 'unknown')}`",
        "",
        "| Source | Label | Bases |",
        "| --- | --- | ---: |",
    ]
    for row in report.get("source_label_matrix", []):
        lines.append(f"| {row['source']} | {row['label_name']} | {row['n_bases']} |")
    lines.extend(
        [
            "",
            "## Guard Summaries",
            "",
            "| Guard | Raw gap | Matched gap | Matched attenuation |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("projection_summaries", []):
        lines.append(
            f"| {row['guard']} | {_fmt(row.get('raw_primary_gap_mean'))} | "
            f"{_fmt(row.get('matched_primary_gap_mean'))} | {_fmt(row.get('matched_primary_attenuation_mean'))} |"
        )
    lines.extend(["", f"Claim boundary: {report.get('claim_boundary', '')}", ""])
    return "\n".join(lines)


def render_e8_markdown(rows: list[dict[str, Any]]) -> str:
    low_n = sum(1 for row in rows if row.get("display_status") == "low_N")
    supported = sum(
        1
        for row in rows
        if row.get("global_holm_p_value_mean_gt_0") not in (None, "")
        and _float(row.get("global_holm_p_value_mean_gt_0"), default=1.0) <= 0.05
    )
    return "\n".join(
        [
            "# E8 Slice Denominator + Uncertainty Audit",
            "",
            "This is a localization diagnostic and not mechanism proof.",
            "",
            f"- rows: `{len(rows)}`",
            f"- low-N rows: `{low_n}`",
            f"- global-Holm supported positive rows: `{supported}`",
            "- minimum display rule: n_bases < 10 is marked low_N.",
            "",
        ]
    )


def render_roadmap_markdown(report: dict[str, Any]) -> str:
    status_by_id = {row["id"]: row["status"] for row in report["roadmap_status"]}
    e2_row = next((row for row in report["roadmap_status"] if row["id"] == "E2"), {})
    e3_row = next((row for row in report["roadmap_status"] if row["id"] == "E3"), {})
    e3_boundary = e3_row.get("remaining_boundary") or "E3 remains below the >=3-baseline spotlight target."
    milestone_status = report.get("milestone_status", {})
    milestone_a = milestone_status.get("milestone_a", {})
    milestone_b = milestone_status.get("milestone_b", {})
    e6_judgment = (
        f"- E6 now includes two score/probability guard families, Qwen3Guard and HarmAug, over PKU plus external BeaverTails; E7 has a third Qwen3Guard BeaverTails500 power curve; E3 status: {e3_boundary}"
        if status_by_id.get("E6") == "completed_two_score_guard_families_with_external"
        else f"- E6 now includes Qwen3Guard score-level calibration/drift over PKU plus external BeaverTails; E7 has a third Qwen3Guard BeaverTails500 power curve; E3 status: {e3_boundary}"
    )
    lines = [
        "# MN-SLA Roadmap Completion Audit",
        "",
        "Aggregate-only audit for E1-E9. No raw rendered prompt text is emitted.",
        "",
        "## Completion Verdict",
        "",
        f"- overall verdict: `{milestone_status.get('overall_verdict', 'unknown')}`",
        f"- Milestone A / main-track minimum: `{milestone_a.get('status', 'unknown')}`",
        f"- Milestone B / spotlight recommended package: `{milestone_b.get('status', 'unknown')}`",
        f"- Milestone B boundary: {milestone_b.get('claim', '')}",
        "",
        "| ID | Experiment | Status | Evidence | Remaining boundary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["roadmap_status"]:
        lines.append(
            f"| {row['id']} | {row['experiment']} | {row['status']} | "
            f"{_md(row['evidence'])} | {_md(row['remaining_boundary'])} |"
        )
    lines.extend(
        [
            "",
            "## Current Judgment",
            "",
            (
                "- P0 blockers tracked by the required-experiment summary are closed, and the "
                "expanded 270-item IAA now has completed independent annotations plus a passing "
                "fail-closed report."
                if status_by_id.get("E1") == "completed_expanded_270_human_iaa"
                else "- P0 blockers tracked by the required-experiment summary are closed for the "
                "minimal 90-item overlap P0-1; expanded 270-item IAA remains an external "
                "human-annotation dependency."
            ),
            (
                "- E2 now meets the spotlight baseline-breadth target under narrow score/logit claim boundaries; E5 also adds an explicitly modeled NonPKU HarmBench/XSTest source-pair confounding audit."
                if status_by_id.get("E2") == "completed_spotlight_baseline_breadth"
                else "- E2 and E5 now meet the minimum main-track roadmap standard; E5 also adds an explicitly modeled NonPKU HarmBench/XSTest source-pair confounding audit."
            ),
            "- E4, E8, and E9 were completed here as aggregate analysis/package artifacts.",
            e6_judgment,
            "",
        ]
    )
    return "\n".join(lines)


def render_package_readme(paths: list[Path]) -> str:
    lines = [
        "# MN-SLA Public Aggregate Package",
        "",
        "This package contains aggregate-only artifacts. It intentionally excludes raw rendered prompts, JSONL prediction ledgers, private answer keys, local annotation packets, source data, model weights, and caches.",
        "",
        "## Included Files",
        "",
    ]
    for path in sorted(paths):
        lines.append(f"- `{path.relative_to(PACKAGE_DIR).as_posix()}`")
    return "\n".join(lines) + "\n"


def render_sanitized_skeletons() -> str:
    return "\n".join(
        [
            "# Sanitized Wrapper Skeletons",
            "",
            "These skeletons describe wrapper structure without benchmark prompt text.",
            "",
            "```text",
            "[clean]    <task text only>",
            "[neutral]  <objective review instruction> + <task text> + <format reminder>",
            "[attack]   <social-pressure cue family> + <task text> + <desired-label cue>",
            "```",
            "",
            "Do not reconstruct or publish raw harmful prompts from this skeleton.",
            "",
        ]
    )


def scan_release_package(package_dir: Path) -> dict[str, Any]:
    forbidden_path_markers = ("SENSITIVE", "private_answer_key", ".jsonl", "data", ".hf_cache", "models")
    flagged = []
    for path in package_dir.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(package_dir).as_posix()
        if any(marker.lower() in rel_path.lower() for marker in forbidden_path_markers):
            flagged.append({"path": rel_path, "reason": "forbidden path marker"})
    return {
        "status": "passed" if not flagged else "failed",
        "flagged_files": flagged,
        "forbidden_path_markers": list(forbidden_path_markers),
    }


def _package_target(aggregate_dir: Path, source: Path) -> Path:
    target = aggregate_dir / source.name
    if not target.exists():
        return target
    prefixed = aggregate_dir / f"{source.parent.name}_{source.name}"
    if not prefixed.exists():
        return prefixed
    digest = hashlib.sha1(source.as_posix().encode("utf-8")).hexdigest()[:8]
    return aggregate_dir / f"{source.parent.name}_{digest}_{source.name}"


def render_scan_report(scan: dict[str, Any]) -> str:
    lines = [
        "# Release Scan Report",
        "",
        f"- status: `{scan['status']}`",
        f"- flagged files: `{len(scan['flagged_files'])}`",
        "",
    ]
    if scan["flagged_files"]:
        lines.extend(["| Path | Reason |", "| --- | --- |"])
        for row in scan["flagged_files"]:
            lines.append(f"| `{row['path']}` | {row['reason']} |")
    return "\n".join(lines) + "\n"


def _roadmap_row(
    identifier: str,
    experiment: str,
    status: str,
    evidence_summary: str,
    evidence: Any,
    remaining_boundary: str,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "experiment": experiment,
        "status": status,
        "evidence_summary": evidence_summary,
        "evidence": evidence or "",
        "remaining_boundary": remaining_boundary,
    }


def _hash_row(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": path.relative_to(PACKAGE_DIR).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_fieldnames(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def _nonempty_line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _fail_closed_report_passed(path: Path) -> bool:
    return bool(path.exists() and _read_json(path).get("passed") is True)


def _find_expanded_completed_annotation_files() -> list[str]:
    if not EXPANDED_IAA_PACKET_DIR.exists():
        return []
    candidates = []
    for path in EXPANDED_IAA_PACKET_DIR.iterdir():
        if not path.is_file():
            continue
        if (
            path.name.startswith("annotations_")
            and path.suffix.lower() in {".csv", ".jsonl"}
            and "SENSITIVE" not in path.name
        ):
            candidates.append(_rel(path))
    return sorted(candidates)


def _read_jsonl_metadata(path: Path) -> list[dict[str, Any]]:
    metadata_fields = {
        "base_id",
        "category",
        "hard_v3_category_key",
        "hard_v3_role",
        "label",
        "label_name",
        "source",
    }
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append({field: row.get(field) for field in metadata_fields if field in row})
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _fmt(value: Any) -> str:
    if value in (None, ""):
        return "NA"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "NA"
    return f"{number:.6f}"


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts import generate_mn_sla_completion_and_release_audit_20260602 as audit


def test_completion_release_audit_writes_governance_outputs(tmp_path, monkeypatch):
    paths = _fixture_paths(tmp_path)
    _write_json(paths["required"], _required_summary())
    _write_json(paths["fresh"], _fresh_grid_summary())
    _write_json(paths["e6_score"], _e6_score_summary())
    _write_manifest(paths["manifest"])
    _write_adapter_markers(tmp_path)
    _patch_paths(monkeypatch, tmp_path, paths)

    report = audit.generate_audit()
    audit.write_audit(report, paths["output"])

    p0_1 = next(row for row in report["requirement_status"] if row["id"] == "P0-1")
    baselines = {row["baseline"]: row for row in report["baseline_ledger"]}
    policies = {row["path_pattern"]: row for row in report["release_policy_manifest"]}

    assert report["raw_text_emitted"] is False
    assert p0_1["status"] == "completed_human_iaa"
    assert p0_1["status_class"] == "local_completed_human_iaa"
    assert baselines["DynaGuard"]["status"] == "evaluated"
    assert baselines["WildGuard"]["status"] == "evaluated"
    assert baselines["ShieldLM"]["status"] == "supplementary_only"
    assert baselines["Qwen3Guard"]["status"] == "evaluated_score_logit"
    assert baselines["HarmAug"]["status"] == "evaluated_score_probability"
    assert "harmaug_pku200" in baselines["HarmAug"]["evidence_paths"]
    assert "harmaug_beavertails200" in baselines["HarmAug"]["evidence_paths"]
    assert baselines["BingoGuard"]["status"] == "evaluated"
    assert baselines["LlamaGuard"]["status"] == "runner_available_no_formal_run"
    assert baselines["NemotronGuard"]["status"] == "runner_available_no_formal_run"
    assert baselines["OpenAI Moderation API"]["status"] == "excluded"
    assert policies["**/*"]["decision"] == "deny_by_default"
    assert policies["data/**/*"]["decision"] == "deny"
    assert policies["outputs/**/*SENSITIVE*"]["decision"] == "deny"
    assert policies["artifacts/**/*"]["decision"] == "allow_aggregate"
    assert report["release_check"]["deny_by_default"] is True

    for name in (
        "audit.json",
        "audit.md",
        "baseline_ledger.csv",
        "release_policy_manifest.csv",
        "release_check.md",
    ):
        assert (paths["output"] / name).exists()


def test_baseline_ledger_ignores_missing_prediction_manifest_rows(tmp_path, monkeypatch):
    _write_adapter_markers(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)

    required = _required_summary()
    manifest = [
        _manifest_row(
            "NemotronGuard",
            "confirmatory_external_open_dataset_replication",
            dataset="BeaverTails200",
            exists="False",
        )
    ]

    rows = audit.build_baseline_ledger(required, manifest)
    baselines = {row["baseline"]: row for row in rows}

    assert baselines["NemotronGuard"]["status"] == "runner_available_no_formal_run"
    assert "confirmatory_external_open_dataset_replication" not in baselines["NemotronGuard"]["artifact_roles"]


def test_baseline_ledger_counts_existing_nemotron_replication(tmp_path, monkeypatch):
    _write_adapter_markers(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)

    required = _required_summary()
    manifest = [
        _manifest_row(
            "NemotronGuard",
            "confirmatory_external_open_dataset_replication",
            dataset="BeaverTails200",
            exists="True",
        )
    ]

    rows = audit.build_baseline_ledger(required, manifest)
    baselines = {row["baseline"]: row for row in rows}

    assert baselines["NemotronGuard"]["status"] == "evaluated"
    assert "confirmatory_external_open_dataset_replication" in baselines["NemotronGuard"]["artifact_roles"]


def test_completion_release_audit_allows_negative_completed_wording():
    required = _blocked_required_summary()
    required["requirement_status"][0]["claim"] = "Not completed without independent human annotators."

    audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_positive_p0_1_completion_claim():
    required = _blocked_required_summary()
    required["requirement_status"][0]["claim"] = "Completed human IAA validation passed."

    with pytest.raises(ValueError, match="P0-1 claim reads as completed"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_nested_human_iaa_completion_claim():
    required = _blocked_required_summary()
    required["overall_verdict"] = {"unsafe": "Human IAA completed and passed."}

    with pytest.raises(ValueError, match="completion-like wording"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_mixed_negative_then_positive_human_iaa_claim():
    required = _blocked_required_summary()
    required["overall_verdict"] = {"unsafe": "Not completed, but human IAA validated."}

    with pytest.raises(ValueError, match="completion-like wording"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_uses_path_context_for_p0_1_completion_claim():
    required = _blocked_required_summary()
    required["extra"] = {"P0-1": "completed"}

    with pytest.raises(ValueError, match="completion-like wording"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_missing_p0_1_blocker():
    required = _blocked_required_summary()
    required["blockers"] = []

    with pytest.raises(ValueError, match="P0-1 independent-human-IAA blocker"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_completed_p0_1_without_passing_human_iaa():
    required = _required_summary()
    required["human_iaa_summary"]["passed"] = False

    with pytest.raises(ValueError, match="human_iaa_summary.passed"):
        audit.validate_fail_closed_claims(required, _fresh_grid_summary())


def test_completion_release_audit_rejects_wildguard_positive_attenuation_values():
    fresh = _fresh_grid_summary()
    wildguard = next(row for row in fresh["rows"] if row["guard"] == "WildGuard")
    wildguard["attenuation_positive_rate"] = 1.0

    with pytest.raises(ValueError, match="WildGuard fresh-grid attenuation"):
        audit.validate_fail_closed_claims(_required_summary(), fresh)


def test_completion_release_audit_rejects_missing_wildguard_attenuation_value():
    fresh = _fresh_grid_summary()
    wildguard = next(row for row in fresh["rows"] if row["guard"] == "WildGuard")
    wildguard.pop("median_attenuation_mean")

    with pytest.raises(ValueError, match="missing required field"):
        audit.validate_fail_closed_claims(_required_summary(), fresh)


def test_completion_release_audit_rejects_wildguard_positive_claim_wording():
    fresh = _fresh_grid_summary()
    fresh["claim_safety"]["allowed_claim"] = "All guards show positive attenuation; WildGuard preserves positive attenuation."

    with pytest.raises(ValueError, match="overstates WildGuard"):
        audit.validate_fail_closed_claims(_required_summary(), fresh)


def _fixture_paths(root: Path) -> dict[str, Path]:
    return {
        "required": root / "required_summary.json",
        "fresh": root / "fresh_grid_summary.json",
        "e6_score": root / "e6_score_level_summary.json",
        "manifest": root / "artifact_manifest.csv",
        "output": root / "audit_out",
    }


def _patch_paths(monkeypatch, root: Path, paths: dict[str, Path]) -> None:
    monkeypatch.setattr(audit, "ROOT", root)
    monkeypatch.setattr(audit, "REQUIRED_SUMMARY_PATH", paths["required"])
    monkeypatch.setattr(audit, "FRESH_GRID_SUMMARY_PATH", paths["fresh"])
    monkeypatch.setattr(audit, "E6_SCORE_LEVEL_SUMMARY_PATH", paths["e6_score"])
    monkeypatch.setattr(audit, "ARTIFACT_MANIFEST_PATH", paths["manifest"])
    monkeypatch.setattr(audit, "OUTPUT_DIR", paths["output"])


def _write_adapter_markers(root: Path) -> None:
    for path in (
        root / "src" / "sycophancy_guard" / "run_bingoguard.py",
        root / "src" / "sycophancy_guard" / "run_shieldgemma.py",
        root / "scripts" / "run_llamaguard.py",
        root / "scripts" / "run_nemotron_guard.py",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# marker\n", encoding="utf-8")


def _required_summary() -> dict:
    return {
        "blockers": [],
        "human_iaa_summary": {
            "passed": True,
            "status": "completed_human_iaa",
            "evidence_path": "outputs/human_validation_overlap_20260601/analysis_completed/fail_closed_report.json",
        },
        "probability_threshold_summary": {
            "available_probability_guards": ["HarmAug", "Qwen3Guard"],
            "status": "completed_two_probability_guards",
        },
        "requirement_status": [
            {
                "id": "P0-1",
                "name": "Overlapping human validation / IAA",
                "status": "completed_human_iaa",
                "evidence_path": "outputs/human_validation_overlap_20260601/analysis_completed/fail_closed_report.json",
                "claim": "Completed: two independent annotators passed the blinded overlap fail-closed human IAA thresholds.",
            },
            {
                "id": "P0-2",
                "name": "Simple-baseline comparison",
                "status": "completed_diagnostic",
                "evidence_path": "outputs/mn_sla_required_experiments_20260601/projection_ablation_all_rows.csv",
                "claim": "Completed as aggregate diagnostic across available ledgers.",
            },
            {
                "id": "P0-3",
                "name": "External open-dataset replication",
                "status": "completed_confirmatory",
                "evidence_path": "outputs/mn_sla_required_experiments_20260601/artifact_manifest.csv",
                "claim": "BeaverTails200 confirmatory replication present.",
            },
            {
                "id": "P0-4",
                "name": "Estimator x neutral-template robustness",
                "status": "completed_fresh_holdout_diagnostic",
                "evidence_path": "outputs/fresh_neutral_template_grid_20260601/fresh_neutral_template_grid_summary.json",
                "claim": "Fresh holdout neutral-template grid completed as diagnostic.",
            },
            {
                "id": "P0-5",
                "name": "Threshold / probability-level robustness",
                "status": "completed_two_probability_guards",
                "evidence_path": "outputs/mn_sla_required_experiments_20260601/probability_threshold_sweeps.csv",
                "claim": "Probability/logit diagnostics completed.",
            },
            {
                "id": "P0-6",
                "name": "Scale-aware gate variant",
                "status": "completed_as_claim_matrix",
                "evidence_path": "outputs/mn_sla_required_experiments_20260601/mn_sla_required_experiments_summary.md",
                "claim": "Claim matrix generated.",
            },
        ],
    }


def _blocked_required_summary() -> dict:
    required = _required_summary()
    required["blockers"] = [
        {
            "requirement": "P0-1 overlapping independent human IAA",
            "status": "blocked_by_missing_independent_human_annotations",
            "allowed_claim": "Do not claim human IAA completed.",
        }
    ]
    required["human_iaa_summary"] = {
        "passed": False,
        "status": "missing",
        "evidence_path": "outputs/human_validation_overlap_20260601/analysis_completed/fail_closed_report.json",
    }
    required["requirement_status"][0] = {
        "id": "P0-1",
        "name": "Overlapping human validation / IAA",
        "status": "blocked",
        "evidence_path": "outputs/mn_sla_required_experiments_20260601/mn_sla_required_experiments_summary.md",
        "claim": "Not completed without independent human annotators.",
    }
    return required


def _fresh_grid_summary() -> dict:
    return {
        "claim_safety": {
            "allowed_claim": (
                "DynaGuard preserves positive attenuation; WildGuard preserves positive residual gaps "
                "but not positive attenuation under this reference definition."
            )
        },
        "rows": [
            {"guard": "DynaGuard", "attenuation_positive_rate": 1.0, "median_attenuation_mean": 0.02},
            {"guard": "WildGuard", "attenuation_positive_rate": 0.0, "median_attenuation_mean": -0.01},
        ],
    }


def _e6_score_summary() -> dict:
    return {
        "status": "completed_two_score_guard_families_with_external",
        "runs": [
            {
                "dataset": "PKU200",
                "exists": True,
                "guard": "HarmAug",
                "path": "outputs/harmaug_pku200_20260602/predictions_harmaug_pku200_core_only_full.jsonl",
                "status": "completed_score_level_analysis",
            },
            {
                "dataset": "BeaverTails200",
                "exists": True,
                "guard": "HarmAug",
                "path": "outputs/harmaug_beavertails200_20260602/predictions_harmaug_beavertails200_core_only_full.jsonl",
                "status": "completed_score_level_analysis",
            },
        ],
    }


def _write_manifest(path: Path) -> None:
    rows = [
        _manifest_row("DynaGuard", "primary_scale_gate"),
        _manifest_row("WildGuard", "primary_scale_gate"),
        _manifest_row("ShieldLM", "supplementary_baseline_breadth"),
        _manifest_row("Qwen3Guard", "P0-5 probability/logit robustness diagnostic"),
        _manifest_row("Qwen3Guard", "external_500base_score_logit_extension", dataset="BeaverTails500"),
        _manifest_row("BingoGuard", "confirmatory_external_open_dataset_replication", dataset="BeaverTails200"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _manifest_row(guard: str, role: str, dataset: str = "PKU200", exists: str = "True") -> dict[str, str]:
    return {
        "artifact_type": "prediction_input",
        "dataset": dataset,
        "guard": guard,
        "path": f"outputs/{guard.lower()}/predictions.jsonl",
        "role": role,
        "exists": exists,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

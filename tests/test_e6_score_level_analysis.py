from __future__ import annotations

from scripts.generate_e6_score_level_analysis_20260603 import (
    classify_score_guard_status,
    compute_paired_score_drift,
    compute_role_metrics,
)


def test_e6_score_level_metrics_use_matched_neutral_cells():
    records = [
        _record("a::clean", "a", "clean", None, 1, 0.9),
        _record("a::neutral", "a", "matched_neutral_control", None, 1, 0.8),
        _record("a::attack", "a", "attack", "primary_attack_average_effect", 1, 0.2),
        _record("b::clean", "b", "clean", None, 0, 0.1),
        _record("b::neutral", "b", "matched_neutral_control", None, 0, 0.2),
        _record("b::attack", "b", "attack", "primary_attack_average_effect", 0, 0.7),
    ]

    roles = compute_role_metrics(records)
    paired = compute_paired_score_drift(records)

    assert roles["primary_attack"]["n"] == 2.0
    assert roles["primary_attack"]["hard_label_error_rate"] == 1.0
    assert roles["primary_attack"]["brier"] == 0.5650000000000001
    assert paired["n_bases"] == 2
    assert paired["n_primary_attacks_with_matched_neutral"] == 2
    assert paired["mean_adverse_probability_drift_vs_matched_neutral"] == 0.55
    assert paired["mean_attack_error_minus_matched_neutral_error"] == 1.0


def test_e6_status_requires_two_score_guards_with_pku_and_external():
    qwen_only = [
        _run("PKU200", "Qwen3Guard"),
        _run("BeaverTails500", "Qwen3Guard"),
    ]
    two_guards = [
        *qwen_only,
        _run("PKU200", "HarmAug"),
        _run("BeaverTails200", "HarmAug"),
    ]

    assert classify_score_guard_status(qwen_only) == "completed_qwen_score_calibration_external"
    assert classify_score_guard_status(two_guards) == "completed_two_score_guard_families_with_external"


def _run(dataset: str, guard: str) -> dict:
    return {
        "dataset": dataset,
        "guard": guard,
        "status": "completed_score_level_analysis",
    }


def _record(
    record_id: str,
    base_id: str,
    role: str,
    claim_scope: str | None,
    label: int,
    prob_unsafe: float,
) -> dict:
    return {
        "id": record_id,
        "base_id": base_id,
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": claim_scope or role,
        "pressure_layout": "pre_case",
        "pressure_format": "submitter_note",
        "label": label,
        "prob_unsafe": prob_unsafe,
        "prediction": "unsafe" if prob_unsafe >= 0.5 else "safe",
        "supervised": True,
    }

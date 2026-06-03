from __future__ import annotations

import json
from pathlib import Path

from scripts import generate_mn_sla_roadmap_completion_audit_20260602 as roadmap


def test_roadmap_marks_e3_limited_grid_and_e7_third_power_curve(tmp_path, monkeypatch):
    qwen200 = _touch(tmp_path / "qwen200.json")
    qwen500 = _touch(tmp_path / "qwen500.json")
    power_a = _touch(tmp_path / "dynaguard_power.csv")
    power_b = _touch(tmp_path / "wildguard_power.csv")
    power_qwen = _touch(tmp_path / "qwen_power.csv")

    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH", qwen200)
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH", qwen500)
    monkeypatch.setattr(roadmap, "POWER_SUMMARY_PATHS", [power_a, power_b])
    monkeypatch.setattr(roadmap, "QWEN_POWER_SUMMARY_PATH", power_qwen)

    required_summary = {
        "requirement_status": [
            {"id": "P0-1", "evidence_path": "human.json"},
            {"id": "P0-3", "evidence_path": "external.csv"},
            {"id": "P0-4", "evidence_path": "fresh_grid.json"},
        ]
    }
    completion_audit = {
        "baseline_ledger": [
            {"status": "evaluated"},
            {"status": "evaluated"},
            {"status": "diagnostic"},
            {"status": "supplementary_only"},
        ]
    }
    e3_rows = [
        {
            "run": name,
            "meets_current_grid_minimum": True,
            "meets_spotlight_template_count": False,
        }
        for name in ("dynaguard_pku2k", "wildguard_pku2k", "qwen3guard_beavertails500")
    ]

    rows = roadmap.build_roadmap_status(
        required_summary,
        completion_audit,
        e4_rows=[],
        e3_rows=e3_rows,
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
    )
    by_id = {row["id"]: row for row in rows}

    assert by_id["E3"]["status"] == "completed_current_grid_not_3template_spotlight"
    assert "do not claim full 3-template spotlight robustness" in by_id["E3"]["remaining_boundary"]
    assert by_id["E7"]["status"] == "completed_three_baseline_power_curves"
    assert "qwen_power.csv" in by_id["E7"]["evidence"]


def test_roadmap_e2_boundary_uses_actual_baseline_counts(tmp_path, monkeypatch):
    qwen200 = _touch(tmp_path / "qwen200.json")
    qwen500 = _touch(tmp_path / "qwen500.json")
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH", qwen200)
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH", qwen500)
    monkeypatch.setattr(roadmap, "POWER_SUMMARY_PATHS", [])
    monkeypatch.setattr(roadmap, "QWEN_POWER_SUMMARY_PATH", tmp_path / "missing_power.csv")

    rows = roadmap.build_roadmap_status(
        required_summary={"requirement_status": []},
        completion_audit={
            "baseline_ledger": [
                {"status": "evaluated"},
                {"status": "evaluated"},
                {"status": "evaluated"},
                {"status": "evaluated_score_logit"},
                {"status": "diagnostic"},
                {"status": "supplementary_only"},
            ]
        },
        e4_rows=[],
        e3_rows=[],
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
    )
    e2 = {row["id"]: row for row in rows}["E2"]

    assert e2["status"] == "completed_minimum_3_formal_plus_2_diagnostics"
    assert "4 formal/main-compatible baseline(s)" in e2["remaining_boundary"]
    assert "1 diagnostic baseline(s)" in e2["remaining_boundary"]
    assert "1 supplementary baseline(s)" in e2["remaining_boundary"]
    assert "3 formal/main-compatible baselines plus 2 diagnostics" not in e2["remaining_boundary"]
    assert "5-6 baseline spotlight target" in e2["remaining_boundary"]


def test_roadmap_e2_spotlight_breadth_closes_milestone_b(tmp_path, monkeypatch):
    qwen200 = _touch(tmp_path / "qwen200.json")
    qwen500 = _touch(tmp_path / "qwen500.json")
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH", qwen200)
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH", qwen500)
    monkeypatch.setattr(roadmap, "POWER_SUMMARY_PATHS", [])
    monkeypatch.setattr(roadmap, "QWEN_POWER_SUMMARY_PATH", tmp_path / "missing_power.csv")

    rows = roadmap.build_roadmap_status(
        required_summary={"requirement_status": []},
        completion_audit={"baseline_ledger": [{"status": "evaluated"} for _ in range(5)]},
        e4_rows=[],
        e3_rows=[],
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
    )
    by_id = {row["id"]: row for row in rows}
    e2 = by_id["E2"]

    assert e2["status"] == "completed_spotlight_baseline_breadth"
    assert "meets the 5-baseline spotlight breadth target" in e2["remaining_boundary"]


def test_roadmap_counts_e3_spotlight_by_unique_formal_guard(tmp_path, monkeypatch):
    qwen200 = _touch(tmp_path / "qwen200.json")
    qwen500 = _touch(tmp_path / "qwen500.json")
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS_THRESHOLD_SUMMARY_PATH", qwen200)
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH", qwen500)
    monkeypatch.setattr(roadmap, "POWER_SUMMARY_PATHS", [])
    monkeypatch.setattr(roadmap, "QWEN_POWER_SUMMARY_PATH", tmp_path / "missing_power.csv")

    required_summary = {"requirement_status": [{"id": "P0-1", "evidence_path": "human.json"}]}
    completion_audit = {
        "baseline_ledger": [
            {"status": "evaluated"},
            {"status": "evaluated"},
            {"status": "evaluated"},
            {"status": "evaluated_score_logit"},
        ]
    }
    duplicated_qwen_rows = [
        _e3_row("qwen3guard_beavertails500_3neutral"),
        _e3_row("qwen3guard_pku200_3neutral"),
        _e3_row("dynaguard_beavertails200_3neutral"),
    ]
    complete_rows = [*duplicated_qwen_rows, _e3_row("wildguard_beavertails200_3neutral")]

    duplicated_status = roadmap.build_roadmap_status(
        required_summary,
        completion_audit,
        e4_rows=[],
        e3_rows=duplicated_qwen_rows,
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
    )
    complete_status = roadmap.build_roadmap_status(
        required_summary,
        completion_audit,
        e4_rows=[],
        e3_rows=complete_rows,
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
    )

    assert {row["id"]: row for row in duplicated_status}["E3"]["status"] == "partial_3template_two_formal_baselines"
    complete_e3 = {row["id"]: row for row in complete_status}["E3"]
    assert complete_e3["status"] == "completed_spotlight_3template_grid"
    assert "Closes the 3-template coverage target" in complete_e3["remaining_boundary"]
    assert "guard-specific" in complete_e3["remaining_boundary"]

    milestones = roadmap.build_milestone_status(complete_status)
    assert milestones["overall_verdict"] == "MAIN_COMPLETE_ONLY"
    assert milestones["milestone_a"]["status"] == "completed"
    assert milestones["milestone_b"]["status"] == "incomplete"
    assert milestones["milestone_b"]["rows"][0]["status"] == "incomplete_external_human_dependency"


def test_roadmap_marks_e5_confounding_modeled_as_spotlight_complete(tmp_path, monkeypatch):
    qwen500 = _touch(tmp_path / "qwen500.json")
    monkeypatch.setattr(roadmap, "QWEN_BEAVERTAILS500_THRESHOLD_SUMMARY_PATH", qwen500)

    required_summary = {"requirement_status": [{"id": "P0-3", "evidence_path": "external.csv"}]}
    completion_audit = {"baseline_ledger": [{"status": "evaluated"} for _ in range(3)]}
    rows = roadmap.build_roadmap_status(
        required_summary,
        completion_audit,
        e4_rows=[],
        e3_rows=[],
        e8_rows=[],
        package_report={"status": "completed_public_aggregate_package", "package_dir": "package"},
        e5_report={"status": "completed_confounding_modeled_source_pair"},
    )

    e5 = {row["id"]: row for row in rows}["E5"]
    assert e5["status"] == "completed_external_sources_with_confounding_model"
    assert "confounding-modeled" in e5["remaining_boundary"]

    b_rows = {row["id"]: row for row in roadmap.build_milestone_status(rows)["milestone_b"]["rows"]}
    assert b_rows["E5"]["status"] == "completed_with_confounding_modeled_caveat"


def test_e3_row_claim_boundary_matches_template_and_guard_role():
    formal = roadmap.e3_row_claim_boundary(n_neutral_templates=3, formal_guard="DynaGuard")
    diagnostic = roadmap.e3_row_claim_boundary(n_neutral_templates=3, formal_guard="HarmAug")
    two_template = roadmap.e3_row_claim_boundary(n_neutral_templates=2, formal_guard="WildGuard")

    assert "satisfies the 3-neutral-template coverage criterion" in formal
    assert "not counted as a formal E3 guard" in diagnostic
    assert "does not satisfy the 3-neutral-template spotlight target" in two_template


def test_roadmap_markdown_renders_milestone_verdict():
    report = {
        "milestone_status": {
            "overall_verdict": "MAIN_COMPLETE_ONLY",
            "milestone_a": {"status": "completed"},
            "milestone_b": {
                "status": "incomplete",
                "claim": "Spotlight-level recommended package is not fully complete.",
            },
        },
        "roadmap_status": [
            {
                "id": "E3",
                "experiment": "Preregistered estimator x neutral-template robustness",
                "status": "completed_spotlight_3template_grid",
                "evidence": "e3.csv",
                "remaining_boundary": "guard-specific",
            }
        ],
    }

    markdown = roadmap.render_roadmap_markdown(report)

    assert "overall verdict: `MAIN_COMPLETE_ONLY`" in markdown
    assert "Milestone A / main-track minimum: `completed`" in markdown
    assert "Milestone B / spotlight recommended package: `incomplete`" in markdown


def test_milestone_b_substatuses_follow_roadmap_rows():
    rows = [
        _status_row("E1", "completed_minimal"),
        _status_row("E2", "completed_minimum_3_formal_plus_2_diagnostics"),
        _status_row("E3", "completed_current_grid_not_3template_spotlight"),
        _status_row("E4", "completed_aggregate_matrix"),
        _status_row("E5", "completed_beavertails500_extension"),
        _status_row("E6", "completed_minimum_score_external"),
        _status_row("E7", "partial_two_baseline_power_curves"),
        _status_row("E8", "partial_missing_slice_audit"),
        _status_row("E9", "completed_public_aggregate_package"),
    ]

    milestones = roadmap.build_milestone_status(rows)
    b_by_id = {row["id"]: row for row in milestones["milestone_b"]["rows"]}

    assert b_by_id["E3"]["status"] == "partial"
    assert b_by_id["E6"]["status"] == "partial"
    assert b_by_id["E7"]["status"] == "partial"
    assert b_by_id["E8"]["status"] == "partial"


def test_milestone_b_marks_expanded_iaa_complete():
    rows = [_status_row("E1", "completed_expanded_270_human_iaa")]

    milestones = roadmap.build_milestone_status(rows)
    e1 = {row["id"]: row for row in milestones["milestone_b"]["rows"]}["E1"]

    assert e1["status"] == "completed_expanded_270_human_iaa"
    assert "sample-level validation" in e1["caveat"]


def test_milestone_b_all_complete_when_spotlight_rows_completed():
    rows = [
        _status_row("E1", "completed_expanded_270_human_iaa"),
        _status_row("E2", "completed_spotlight_baseline_breadth"),
        _status_row("E3", "completed_spotlight_3template_grid"),
        _status_row("E4", "completed_aggregate_matrix"),
        _status_row("E5", "completed_external_sources_with_confounding_model"),
        _status_row("E6", "completed_two_score_guard_families_with_external"),
        _status_row("E7", "completed_three_baseline_power_curves"),
        _status_row("E8", "completed_existing_slice_audit"),
        _status_row("E9", "completed_public_aggregate_package"),
    ]

    milestones = roadmap.build_milestone_status(rows)

    assert milestones["overall_verdict"] == "ALL_COMPLETE"
    assert milestones["milestone_a"]["status"] == "completed"
    assert milestones["milestone_b"]["status"] == "completed"


def test_read_jsonl_metadata_strips_raw_text_fields(tmp_path):
    path = tmp_path / "metadata.jsonl"
    path.write_text(
        json.dumps(
            {
                "base_id": "b1",
                "hard_v3_role": "clean",
                "source": "xstest",
                "label_name": "safe",
                "category": "benign",
                "raw_text": "do not emit",
                "rendered_text": "do not emit either",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = roadmap._read_jsonl_metadata(path)

    assert rows == [
        {
            "base_id": "b1",
            "hard_v3_role": "clean",
            "source": "xstest",
            "label_name": "safe",
            "category": "benign",
        }
    ]


def test_expanded_iaa_readiness_audit_is_aggregate_only_and_incomplete(tmp_path, monkeypatch):
    packet_dir = tmp_path / "expanded"
    packet_dir.mkdir()
    manifest = packet_dir / "packet_manifest.json"
    template = packet_dir / "annotation_template.csv"
    private_key = packet_dir / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl"
    annotator_packet = packet_dir / "annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl"
    analyzer = tmp_path / "analyze_expanded.py"
    core = tmp_path / "human_neutral_annotation.py"

    manifest.write_text(
        json.dumps(
            {
                "counts": {
                    "sampled_cells": 90,
                    "annotation_items": 270,
                    "cells_by_regime": {
                        "non_pku200_source_pair": 30,
                        "pku200_scale": 30,
                        "pku50_main_gate": 30,
                    },
                    "items_by_role": {"attack": 90, "clean": 90, "neutral": 90},
                }
            }
        ),
        encoding="utf-8",
    )
    template.write_text(
        ",".join(roadmap.EXPECTED_EXPANDED_IAA_TEMPLATE_COLUMNS)
        + "\n"
        + "\n".join(f"p,item_{index},,,,,,," for index in range(270))
        + "\n",
        encoding="utf-8",
    )
    private_key.write_text(("{}\n" * 270), encoding="utf-8")
    annotator_packet.write_text(('{"rendered_text":"SECRET_RENDERED_TEXT"}\n' * 270), encoding="utf-8")
    analyzer.write_text(
        "min_annotators_per_item=2\nmin_complete_cells_per_regime=30\nmin_total_complete_cells=90\n",
        encoding="utf-8",
    )
    core.write_text("percent_agreement_ci_low\npabak_ci_low\nwithin_1_agreement_ci_low\n", encoding="utf-8")

    monkeypatch.setattr(roadmap, "EXPANDED_IAA_PACKET_DIR", packet_dir)
    monkeypatch.setattr(roadmap, "EXPANDED_IAA_PACKET_MANIFEST_PATH", manifest)
    monkeypatch.setattr(roadmap, "EXPANDED_IAA_TEMPLATE_PATH", template)
    monkeypatch.setattr(roadmap, "EXPANDED_IAA_PRIVATE_KEY_PATH", private_key)
    monkeypatch.setattr(roadmap, "EXPANDED_IAA_ANNOTATOR_PACKET_PATH", annotator_packet)
    monkeypatch.setattr(
        roadmap,
        "EXPANDED_IAA_FAIL_CLOSED_REPORT_PATH",
        packet_dir / "analysis_completed" / "fail_closed_report.json",
    )
    monkeypatch.setattr(roadmap, "EXPANDED_IAA_ANALYZER_PATH", analyzer)
    monkeypatch.setattr(roadmap, "HUMAN_IAA_ANALYZER_CORE_PATH", core)

    report = roadmap.build_expanded_iaa_readiness_audit()
    markdown = roadmap.render_expanded_iaa_readiness_markdown(report)

    assert report["packet_ready_for_external_annotation"] is True
    assert report["completion_status"] == "incomplete_external_human_dependency"
    assert report["completion_claim_allowed"] is False
    assert report["fail_closed_report"]["passed"] is False
    assert report["completed_annotation_files"] == []
    serialized = json.dumps(report) + markdown
    assert "SECRET_RENDERED_TEXT" not in serialized


def _e3_row(name: str) -> dict:
    return {
        "run": name,
        "meets_current_grid_minimum": True,
        "meets_spotlight_template_count": True,
    }


def _status_row(identifier: str, status: str) -> dict:
    return {
        "id": identifier,
        "experiment": identifier,
        "status": status,
        "evidence": f"{identifier}.csv",
        "remaining_boundary": f"{identifier} boundary",
    }


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n", encoding="utf-8")
    return path

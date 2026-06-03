from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scripts.run_fresh_neutral_template_grid_20260601 import (
    base_id,
    filter_holdout_records,
    load_base_ids,
    run_fresh_neutral_template_grid,
)


def test_filter_holdout_records_excludes_gate_base_ids_without_touching_other_bases():
    records = [
        {"id": "gate::clean", "base_id": "gate"},
        {"id": "gate::neutral_a", "base_id": "gate"},
        {"id": "fresh::clean", "base_id": "fresh"},
        {"id": "fresh::attack"},
    ]

    holdout = filter_holdout_records(records, {"gate"})

    assert [base_id(record) for record in holdout] == ["fresh", "fresh"]


def test_base_id_falls_back_to_record_id_prefix():
    assert base_id({"id": "pku_1::neutral_format_reminder"}) == "pku_1"


def test_fresh_grid_summary_requires_dyna_and_wildguard_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gate_path = root / "gate.jsonl"
        dyna_path = root / "dyna.jsonl"
        wild_path = root / "wild.jsonl"
        output = root / "out"
        _write_jsonl(gate_path, [{"id": "gate"}])
        rows = _records_for_base("gate") + _records_for_base("fresh_a") + _records_for_base("fresh_b")
        _write_jsonl(dyna_path, rows)
        _write_jsonl(wild_path, rows)

        summary = run_fresh_neutral_template_grid_for_test(
            inputs=[
                {"dataset": "PKU2K_non_gate50_holdout", "guard": "DynaGuard", "path": dyna_path},
                {"dataset": "PKU2K_non_gate50_holdout", "guard": "WildGuard", "path": wild_path},
            ],
            gate_base_path=gate_path,
            output_dir=output,
        )

        assert summary["status"] == "completed_fresh_holdout_diagnostic"
        assert {row["guard"] for row in summary["rows"]} == {"DynaGuard", "WildGuard"}
        assert all(row["holdout_bases_seen"] == 2 for row in summary["rows"])


def test_load_base_ids_rejects_empty_gate_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.jsonl"
        path.write_text("", encoding="utf-8")

        try:
            load_base_ids(path)
        except ValueError as exc:
            assert "No base ids" in str(exc)
        else:
            raise AssertionError("expected empty gate file to fail")


def run_fresh_neutral_template_grid_for_test(*, inputs, gate_base_path: Path, output_dir: Path):
    from scripts import run_fresh_neutral_template_grid_20260601 as module

    old_inputs = module.FRESH_GRID_INPUTS
    old_gate = module.GATE50_BASE_PATH
    old_output = module.OUTPUT_DIR
    try:
        module.FRESH_GRID_INPUTS = inputs
        module.GATE50_BASE_PATH = gate_base_path
        module.OUTPUT_DIR = output_dir
        return module.run_fresh_neutral_template_grid()
    finally:
        module.FRESH_GRID_INPUTS = old_inputs
        module.GATE50_BASE_PATH = old_gate
        module.OUTPUT_DIR = old_output


def _records_for_base(base: str) -> list[dict]:
    return [
        _record(f"{base}::clean", base, "clean", "clean", "clean", 1.0),
        _record(f"{base}::neutral_a", base, "matched_neutral_control", "matched_neutral_control", "neutral_careful_review", 1.0),
        _record(f"{base}::neutral_b", base, "matched_neutral_control", "matched_neutral_control", "neutral_format_reminder", 0.0),
        _record(f"{base}::attack", base, "attack", "primary_attack_average_effect", "authority", 0.0, is_attack=True),
    ]


def _record(record_id, base, role, claim_scope, pressure_type, prob, *, is_attack=False):
    return {
        "id": record_id,
        "base_id": base,
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": claim_scope,
        "pressure_type": pressure_type,
        "pressure_layout": "pre_case" if role != "clean" else None,
        "pressure_format": "submitter_note" if role != "clean" else None,
        "is_attack": is_attack,
        "is_neutral_control": role == "matched_neutral_control",
        "label": 1,
        "prob_unsafe": prob,
        "prediction": "unsafe" if prob >= 0.5 else "safe",
        "supervised": True,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

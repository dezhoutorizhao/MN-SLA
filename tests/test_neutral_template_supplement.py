from __future__ import annotations

from sycophancy_guard.neutral_template_supplement import build_neutral_template_supplement
from sycophancy_guard.pressure_templates import neutral_control_template_names


def test_neutral_policy_restated_is_registered():
    assert "neutral_policy_restated" in neutral_control_template_names()


def test_builds_supplement_for_existing_base_layout_cells():
    source = [
        _record("a::clean", "a", "clean", None),
        _record("a::neutral_a_pre", "a", "matched_neutral_control", "pre_case"),
        _record("a::neutral_a_post", "a", "matched_neutral_control", "post_case"),
        _record("b::clean", "b", "clean", None, label=0, label_name="safe"),
        _record("b::neutral_a_pre", "b", "matched_neutral_control", "pre_case", label=0, label_name="safe"),
        _record("b::neutral_a_post", "b", "matched_neutral_control", "post_case", label=0, label_name="safe"),
    ]

    records, manifest = build_neutral_template_supplement(
        source,
        template_names=["neutral_policy_restated"],
    )

    assert manifest["records"] == 4
    assert manifest["missing_cells"] == []
    assert manifest["template_counts"] == {"neutral_policy_restated": 4}
    assert {record["base_id"] for record in records} == {"a", "b"}
    assert {record["pressure_layout"] for record in records} == {"pre_case", "post_case"}
    assert all(record["hard_v3_role"] == "matched_neutral_control" for record in records)
    assert all(record["claim_scope"] == "matched_neutral_control" for record in records)
    assert all(record["desired_label"] is None for record in records)


def _record(
    record_id: str,
    base_id: str,
    role: str,
    layout: str | None,
    *,
    label: int = 1,
    label_name: str = "unsafe",
) -> dict:
    return {
        "id": record_id,
        "base_id": base_id,
        "text": "[User]\nrequest\n\n[Assistant]\nresponse",
        "clean_text": "[User]\nrequest\n\n[Assistant]\nresponse",
        "label": label,
        "label_name": label_name,
        "source": "unit",
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": "clean_reference" if role == "clean" else "matched_neutral_control",
        "pressure_type": "clean" if role == "clean" else "neutral_careful_review",
        "pressure_layout": layout,
        "pressure_format": None if layout is None else "submitter_note",
        "is_neutral_control": role == "matched_neutral_control",
        "supervised": True,
    }

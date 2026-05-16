from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sycophancy_guard.projection_ablation import (
    apply_projection_variant,
    compute_projection_ablation,
    write_projection_ablation_report,
)


class ProjectionAblationTest(unittest.TestCase):
    def test_matched_median_projects_attack_from_same_cell(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral_low", "a", "matched_neutral_control", 0, 0.1),
            _record("a::neutral_high", "a", "matched_neutral_control", 0, 0.9),
            _record("a::neutral_mid", "a", "matched_neutral_control", 0, 0.3),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]

        projected = apply_projection_variant(records, "matched_median")
        attack = [record for record in projected if record["hard_v3_role"] == "attack"][0]

        self.assertAlmostEqual(attack["prob_unsafe"], 0.3)
        self.assertEqual(attack["prediction"], "safe")
        self.assertEqual(attack["projection_ablation_n_controls"], 3)
        self.assertTrue(attack["projection_ablation_replaced_score"])

    def test_other_base_same_cell_excludes_own_base_controls(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral", "a", "matched_neutral_control", 0, 0.9),
            _record("b::neutral", "b", "matched_neutral_control", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]

        projected = apply_projection_variant(records, "same_cell_other_base_mean")
        attack = [record for record in projected if record["hard_v3_role"] == "attack"][0]

        self.assertAlmostEqual(attack["prob_unsafe"], 0.1)
        self.assertEqual(attack["projection_ablation_n_controls"], 1)

    def test_missing_wrong_layout_controls_fail_closed(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral", "a", "matched_neutral_control", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]

        projected = apply_projection_variant(records, "wrong_layout_same_base_mean")
        attack = [record for record in projected if record["hard_v3_role"] == "attack"][0]

        self.assertTrue(attack["exclude_from_metrics"])
        self.assertFalse(attack["supervised"])
        self.assertEqual(attack["projection_ablation_issue"], "missing_projection_controls")

    def test_report_writer_sanitizes_nonfinite_values(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral", "a", "matched_neutral_control", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]
        report = compute_projection_ablation(records, variants=("raw", "matched_mean"))

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_projection_ablation_report(report, output)
            self.assertTrue((output / "projection_ablation.json").exists())
            self.assertTrue((output / "projection_ablation.csv").exists())
            self.assertIn("not a SOTA claim", (output / "projection_ablation.md").read_text(encoding="utf-8"))


def _record(
    record_id: str,
    base_id: str,
    role: str,
    label: int,
    prob_unsafe: float,
) -> dict[str, object]:
    return {
        "id": record_id,
        "base_id": base_id,
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": "primary_attack_average_effect" if role == "attack" else role,
        "pressure_type": "clean" if role == "clean" else "authority",
        "pressure_family": "authority",
        "pressure_layout": "pre_case",
        "pressure_format": "submitter_note",
        "target_direction": "toward_unsafe",
        "is_attack": role == "attack",
        "is_neutral_control": role == "matched_neutral_control",
        "label": label,
        "label_name": "unsafe" if label else "safe",
        "prob_unsafe": prob_unsafe,
        "prediction": "unsafe" if prob_unsafe >= 0.5 else "safe",
        "score_kind": "probability",
        "supervised": True,
    }


if __name__ == "__main__":
    unittest.main()

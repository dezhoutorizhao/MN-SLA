from __future__ import annotations

import unittest

from sycophancy_guard.estimator_template_robustness import compute_estimator_template_robustness


class EstimatorTemplateRobustnessTest(unittest.TestCase):
    def test_computes_template_groups_and_estimators(self):
        records = [
            _record("a::clean", "a", "clean", None, 1, 1.0),
            _record("a::neutral_a", "a", "matched_neutral_control", "neutral_a", 1, 1.0),
            _record("a::neutral_b", "a", "matched_neutral_control", "neutral_b", 1, 0.0),
            _record("a::attack", "a", "attack", "authority", 1, 0.0, is_attack=True),
            _record("b::clean", "b", "clean", None, 0, 0.0),
            _record("b::neutral_a", "b", "matched_neutral_control", "neutral_a", 0, 0.0),
            _record("b::neutral_b", "b", "matched_neutral_control", "neutral_b", 0, 1.0),
            _record("b::attack", "b", "attack", "authority", 0, 1.0, is_attack=True),
        ]

        report = compute_estimator_template_robustness(records)

        self.assertEqual(report["n_bases"], 2)
        self.assertEqual(report["neutral_templates"], ["neutral_a", "neutral_b"])
        self.assertEqual(report["summary"]["n_combinations"], 15)
        all_mean = _row(report, "all_neutral_templates", "mean-v1")
        self.assertEqual(all_mean["n_bases"], 2)
        self.assertAlmostEqual(all_mean["raw_gap_mean"], 1.0)
        self.assertAlmostEqual(all_mean["residual_gap_mean"], 0.5)
        neutral_a_mean = _row(report, "neutral_a", "mean-v1")
        self.assertAlmostEqual(neutral_a_mean["residual_gap_mean"], 1.0)
        neutral_b_mean = _row(report, "neutral_b", "mean-v1")
        self.assertAlmostEqual(neutral_b_mean["residual_gap_mean"], 0.0)


def _row(report: dict, template_group: str, estimator: str) -> dict:
    return next(
        row
        for row in report["rows"]
        if row["template_group"] == template_group and row["estimator"] == estimator
    )


def _record(
    record_id: str,
    base_id: str,
    role: str,
    pressure_type: str | None,
    label: int,
    prob_unsafe: float,
    *,
    is_attack: bool = False,
) -> dict:
    return {
        "id": record_id,
        "base_id": base_id,
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": "primary_attack_average_effect" if is_attack else role,
        "pressure_type": pressure_type,
        "pressure_layout": "pre_case",
        "pressure_format": "submitter_note",
        "is_attack": is_attack,
        "is_neutral_control": role == "matched_neutral_control",
        "label": label,
        "prob_unsafe": prob_unsafe,
        "prediction": "unsafe" if prob_unsafe >= 0.5 else "safe",
        "supervised": True,
    }


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from sycophancy_guard.hard_v3_slice_inference import (
    add_holm_adjustments,
    add_stronger_multiplicity_adjustments,
    compute_run_slice_inference,
    holm_adjust,
    json_safe,
    summarize_multiplicity,
    write_slice_inference_report,
)


class HardV3SliceInferenceTest(unittest.TestCase):
    def test_holm_adjust_is_step_down_monotone(self):
        adjusted = holm_adjust([0.04, 0.01, 0.03])

        self.assertAlmostEqual(adjusted[0], 0.06)
        self.assertAlmostEqual(adjusted[1], 0.03)
        self.assertAlmostEqual(adjusted[2], 0.06)
        self.assertTrue(math.isnan(holm_adjust([float("nan")])[0]))

    def test_stronger_multiplicity_scopes_are_reported(self):
        rows = [
            {
                "run": "r1",
                "group_field": "pressure_family",
                "metric": "hard_error_gap",
                "p_value_mean_gt_0": 0.01,
                "mean": 0.2,
                "ci95_low": 0.1,
            },
            {
                "run": "r1",
                "group_field": "pressure_layout",
                "metric": "hard_error_gap",
                "p_value_mean_gt_0": 0.02,
                "mean": 0.2,
                "ci95_low": 0.1,
            },
            {
                "run": "r2",
                "group_field": "pressure_family",
                "metric": "adverse_prob_gap",
                "p_value_mean_gt_0": 0.03,
                "mean": 0.2,
                "ci95_low": 0.1,
            },
        ]

        add_holm_adjustments(rows)
        add_stronger_multiplicity_adjustments(rows)
        summary = {item["scope"]: item for item in summarize_multiplicity(rows)}

        self.assertAlmostEqual(rows[0]["holm_p_value_mean_gt_0"], 0.01)
        self.assertAlmostEqual(rows[0]["run_metric_holm_p_value_mean_gt_0"], 0.02)
        self.assertAlmostEqual(rows[0]["metric_global_holm_p_value_mean_gt_0"], 0.02)
        self.assertAlmostEqual(rows[0]["global_holm_p_value_mean_gt_0"], 0.03)
        self.assertEqual(summary["global"]["n_tests"], 3.0)
        self.assertEqual(summary["global"]["n_supported_positive_slices"], 3.0)

    def test_missing_neutral_fails_closed_by_default(self):
        records = [
            _record("a::attack", "a", "attack", "primary_attack_average_effect", 0, 0.9),
        ]

        with self.assertRaisesRegex(ValueError, "without usable matched-neutral controls"):
            compute_run_slice_inference(
                records,
                run_name="toy",
                group_fields=("pressure_family",),
                n_bootstrap=0,
                n_randomization=8,
            )

        report = compute_run_slice_inference(
            records,
            run_name="toy",
            group_fields=("pressure_family",),
            n_bootstrap=0,
            n_randomization=8,
            fail_on_missing_neutral=False,
        )
        self.assertEqual(report["summary"]["missing_neutral_attack_records"], 1.0)
        self.assertEqual(report["rows"], [])
        self.assertEqual(report["missing_neutral_records"][0]["pressure_family"], "authority")

    def test_slice_inference_uses_base_level_mean_gaps(self):
        records = [
            _record("a::neutral", "a", "matched_neutral_control", "matched_neutral_control", 0, 0.1),
            _record("a::attack1", "a", "attack", "primary_attack_average_effect", 0, 0.9),
            _record("a::attack2", "a", "attack", "primary_attack_average_effect", 0, 0.1),
            _record("b::neutral", "b", "matched_neutral_control", "matched_neutral_control", 1, 0.9),
            _record("b::attack", "b", "attack", "primary_attack_average_effect", 1, 0.1),
        ]

        report = compute_run_slice_inference(
            records,
            run_name="toy",
            group_fields=("pressure_family",),
            n_bootstrap=0,
            n_randomization=8,
        )

        hard_row = [row for row in report["rows"] if row["metric"] == "hard_error_gap"][0]
        adverse_row = [row for row in report["rows"] if row["metric"] == "adverse_prob_gap"][0]
        self.assertEqual(hard_row["n_bases"], 2.0)
        self.assertAlmostEqual(hard_row["mean"], 0.75)
        self.assertAlmostEqual(adverse_row["mean"], 0.6)
        self.assertIn("n_matched_neutral_comparisons", hard_row)

    def test_json_artifact_sanitizes_nonfinite_values(self):
        report = {
            "settings": {
                "threshold": 0.5,
                "group_fields": ["pressure_family"],
                "match_fields": ["pressure_layout", "pressure_format"],
                "slice_metrics": ["hard_error_gap"],
                "n_bootstrap": 0,
                "n_randomization": 0,
                "seed": 1,
                "missing_neutral_policy": "report_and_exclude",
                "holm_family": "test",
            },
            "runs": [],
            "skipped_runs": [],
            "rows": [
                {
                    "run": "toy",
                    "group_field": "pressure_family",
                    "metric": "hard_error_gap",
                    "slice": "authority",
                    "n_bases": 1.0,
                    "ci95_low": float("nan"),
                    "ci95_high": float("nan"),
                    "p_value_mean_gt_0": float("nan"),
                    "holm_p_value_mean_gt_0": float("nan"),
                    "positive_bases": 0.0,
                    "zero_bases": 1.0,
                    "negative_bases": 0.0,
                    "mean": float("nan"),
                }
            ],
        }

        self.assertIsNone(json_safe(report)["rows"][0]["mean"])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_slice_inference_report(report, output)
            self.assertIn('"mean": null', (output / "slice_inference.json").read_text(encoding="utf-8"))


def _record(
    record_id: str,
    base_id: str,
    role: str,
    claim_scope: str,
    label: int,
    prob_unsafe: float,
) -> dict[str, object]:
    return {
        "id": record_id,
        "base_id": base_id,
        "hard_v3_role": role,
        "claim_scope": claim_scope,
        "pressure_family": "authority",
        "pressure_layout": "pre_case",
        "pressure_format": "submitter_note",
        "target_direction": "toward_unsafe",
        "label": label,
        "prob_unsafe": prob_unsafe,
        "prediction": "unsafe" if prob_unsafe >= 0.5 else "safe",
    }


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sycophancy_guard.hard_v3_local_audit import (
    audit_matched_controls,
    compute_two_sided_sensitivity,
    cycle_permutation_sensitivity,
    run_local_audit,
    write_local_audit,
)


class HardV3LocalAuditTest(unittest.TestCase):
    def test_two_sided_sensitivity_reports_two_sided_p(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral", "a", "matched_neutral_control", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]

        report = compute_two_sided_sensitivity(records, run_name="toy")
        hard_row = [
            row for row in report["rows"]
            if row["metric"] == "primary_attack_minus_matched_neutral_error"
        ][0]

        self.assertEqual(hard_row["n_bases"], 1)
        self.assertAlmostEqual(hard_row["mean"], 1.0)
        self.assertAlmostEqual(hard_row["p_two_sided_sign_flip"], 1.0)

    def test_control_audit_flags_nondivisible_cells(self):
        records = [
            _record("a::neutral1", "a", "matched_neutral_control", 0, 0.1),
            _record("a::neutral2", "a", "matched_neutral_control", 0, 0.9),
            _record("a::attack1", "a", "attack", 0, 0.9),
            _record("a::attack2", "a", "attack", 0, 0.9),
            _record("a::attack3", "a", "attack", 0, 0.9),
        ]

        audit = audit_matched_controls(records, run_name="toy")

        self.assertEqual(audit["summary"]["n_nondivisible_attack_neutral_cells"], 1)
        self.assertFalse(audit["rows"][0]["attack_neutral_count_aligns"])
        self.assertTrue(audit["rows"][0]["neutral_cache_key"])

    def test_cycle_permutation_reports_order_sensitivity_summary(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral1", "a", "matched_neutral_control", 0, 0.1),
            _record("a::neutral2", "a", "matched_neutral_control", 0, 0.9),
            _record("a::attack1", "a", "attack", 0, 0.9),
            _record("a::attack2", "a", "attack", 0, 0.9),
            _record("a::attack3", "a", "attack", 0, 0.9),
        ]

        report = cycle_permutation_sensitivity(records, run_name="toy", n_permutations=8, seed=1)

        self.assertEqual(report["n_permutations"], 8)
        self.assertLessEqual(report["primary_gap_min"], report["primary_gap_max"])
        self.assertIn("share_exact_zero", report)

    def test_writer_outputs_json_csv_and_markdown(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral", "a", "matched_neutral_control", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]
        report = run_local_audit({"toy": records}, cycle_inputs={"toy": records}, n_cycle_permutations=2)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_local_audit(output, report)
            self.assertTrue((output / "local_audit.json").exists())
            self.assertTrue((output / "two_sided_sensitivity.csv").exists())
            self.assertTrue((output / "matched_control_manifest.csv").exists())
            self.assertIn("diagnostic only", (output / "local_audit.md").read_text(encoding="utf-8"))


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

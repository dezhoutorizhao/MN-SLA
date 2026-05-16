from __future__ import annotations

import tempfile
import unittest
import math
import json
from pathlib import Path

from sycophancy_guard.neutral_control_consistency_gate import (
    compute_neutral_control_consistency_gate,
    write_neutral_control_consistency_gate_report,
)


class NeutralControlConsistencyGateTest(unittest.TestCase):
    def test_gate_captures_attack_error_when_neutral_disagrees(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral1", "a", "matched_neutral_control", 0, 0.1),
            _record("a::neutral2", "a", "matched_neutral_control", 0, 0.2),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]

        report = compute_neutral_control_consistency_gate(records, n_bootstrap=20, n_randomization=20)

        attack = report["attack_metrics"]
        self.assertEqual(attack["n_primary_attacks"], 1)
        self.assertEqual(attack["raw_attack_errors"], 1.0)
        self.assertEqual(attack["escalated_attacks"], 1.0)
        self.assertEqual(attack["attack_error_capture_rate"], 1.0)
        self.assertEqual(attack["residual_error_mass"], 0.0)
        wrapper = report["neutral_consensus_wrapper_metrics"]
        self.assertEqual(wrapper["auto_decision_rate"], 1.0)
        self.assertEqual(wrapper["wrapped_error_rate_on_auto"], 0.0)
        self.assertEqual(wrapper["correction_rate_given_raw_error"], 1.0)
        self.assertTrue(math.isnan(wrapper["induced_error_given_raw_correct"]))

    def test_gate_keeps_consistent_correct_attack(self):
        records = [
            _record("a::clean", "a", "clean", 1, 0.9),
            _record("a::neutral1", "a", "matched_neutral_control", 1, 0.8),
            _record("a::neutral2", "a", "matched_neutral_control", 1, 0.7),
            _record("a::attack", "a", "attack", 1, 0.9),
        ]

        report = compute_neutral_control_consistency_gate(records, n_bootstrap=20, n_randomization=20)

        attack = report["attack_metrics"]
        self.assertEqual(attack["attack_escalation_rate"], 0.0)
        self.assertEqual(attack["retained_attacks"], 1.0)
        self.assertEqual(attack["retained_attack_error_rate"], 0.0)
        wrapper = report["neutral_consensus_wrapper_metrics"]
        self.assertEqual(wrapper["auto_decision_rate"], 1.0)
        self.assertEqual(wrapper["override_rate_on_auto"], 0.0)
        self.assertEqual(wrapper["wrapped_error_rate_on_auto"], 0.0)

    def test_missing_controls_fail_closed(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::attack", "a", "attack", 0, 0.1),
        ]

        report = compute_neutral_control_consistency_gate(records, n_bootstrap=20, n_randomization=20)

        attack = report["attack_metrics"]
        self.assertEqual(attack["attack_escalation_rate"], 1.0)
        self.assertEqual(attack["missing_control_rate"], 1.0)
        wrapper = report["neutral_consensus_wrapper_metrics"]
        self.assertEqual(wrapper["auto_decision_rate"], 0.0)
        self.assertEqual(wrapper["abstention_rate"], 1.0)

    def test_k_sensitivity_does_not_recurse_and_writes_report(self):
        records = [
            _record("a::clean", "a", "clean", 0, 0.1),
            _record("a::neutral1", "a", "matched_neutral_control", 0, 0.1),
            _record("a::neutral2", "a", "matched_neutral_control", 0, 0.9),
            _record("a::attack", "a", "attack", 0, 0.9),
        ]
        report = compute_neutral_control_consistency_gate(records, n_bootstrap=20, n_randomization=20)

        self.assertIn("k_sensitivity", report)
        self.assertIn("k1_first_control", report["k_sensitivity"])
        self.assertIn("k1_second_control", report["k_sensitivity"])

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_neutral_control_consistency_gate_report({"toy": report}, output)
            self.assertTrue((output / "neutral_control_consistency_gate.json").exists())
            self.assertTrue((output / "neutral_control_consistency_gate_table.csv").exists())
            json_text = (output / "neutral_control_consistency_gate.json").read_text(encoding="utf-8")
            self.assertNotIn("NaN", json_text)
            json.loads(json_text)
            self.assertIn(
                "not a deployable single-pass claim",
                (output / "neutral_control_consistency_gate_summary.md").read_text(encoding="utf-8"),
            )


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

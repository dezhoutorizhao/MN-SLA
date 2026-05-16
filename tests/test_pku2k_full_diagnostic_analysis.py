from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_pku2k_full_diagnostic_20260508.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("analyze_pku2k_full_diagnostic_20260508", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Pku2kFullDiagnosticAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_primary_matched_neutral_coverage_passes_for_same_cell(self):
        records = [
            _record("a::attack", "a", "attack", "primary_attack_average_effect", "pre", "fmt"),
            _record("a::neutral", "a", "matched_neutral_control", "matched_neutral_control", "pre", "fmt"),
        ]

        self.module.validate_primary_matched_neutral_coverage(records, subset_name="unit")

    def test_primary_matched_neutral_coverage_fails_on_missing_cell(self):
        records = [
            _record("a::attack", "a", "attack", "primary_attack_average_effect", "pre", "fmt"),
            _record("a::neutral", "a", "matched_neutral_control", "matched_neutral_control", "post", "fmt"),
        ]

        with self.assertRaisesRegex(ValueError, "unit has 1 primary attack records without matched neutral controls"):
            self.module.validate_primary_matched_neutral_coverage(records, subset_name="unit")

    def test_non_primary_attack_does_not_require_primary_neutral_cell(self):
        records = [
            _record("a::diagnostic", "a", "attack", "confound_diagnostic_only", "pre", "fmt"),
        ]

        self.module.validate_primary_matched_neutral_coverage(records, subset_name="unit")


def _record(
    record_id: str,
    base_id: str,
    role: str,
    claim_scope: str,
    layout: str,
    fmt: str,
) -> dict[str, object]:
    return {
        "id": record_id,
        "base_id": base_id,
        "label": 1,
        "label_name": "unsafe",
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": role,
        "claim_scope": claim_scope,
        "pressure_layout": layout,
        "pressure_format": fmt,
        "prob_unsafe": 0.5,
        "prediction": "unsafe",
        "score_kind": "probability",
    }


if __name__ == "__main__":
    unittest.main()

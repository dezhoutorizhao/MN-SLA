from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sycophancy_guard.hard_v3_current_evidence import (
    GatePolicy,
    RunSpec,
    compute_current_evidence_summary,
    write_current_evidence_summary,
)


class CurrentEvidenceSummaryTest(unittest.TestCase):
    def test_supported_primary_effect_passes_gate_and_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            output = root / "summary"
            _write_jsonl(
                predictions,
                [
                    _hard_record("a"),
                    _hard_record("b"),
                ],
            )
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=2,
                    primary_attack_records=2,
                    primary_mean=0.25,
                    primary_ci_low=0.05,
                    primary_p=0.01,
                    flip_mean=0.0,
                    flip_ci_low=0.0,
                    flip_p=1.0,
                    drift_mean=0.1,
                    drift_ci_low=0.01,
                    drift_p=0.01,
                    stress_n=2,
                ),
            )

            summary = compute_current_evidence_summary(
                [RunSpec("synthetic_pass", predictions, diagnostics)],
                policy=GatePolicy(min_bases_for_claim=2, min_primary_attack_records=2),
            )
            write_current_evidence_summary(output, summary)

            run = summary["runs"][0]
            self.assertEqual(run["gate_status"], "PASS")
            self.assertEqual(run["gate_reasons"], ["primary_hard_label_or_clean_correct_effect_supported"])
            self.assertEqual(run["stress_available"], {"available": True, "units": 2})
            self.assertAlmostEqual(run["metrics"]["primary_error_gap"]["mean"], 0.25)
            written = json.loads((output / "current_evidence_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["runs"][0]["gate_status"], "PASS")
            md = (output / "current_evidence_summary.md").read_text(encoding="utf-8")
            self.assertIn("synthetic_pass", md)
            self.assertIn("PASS", md)

    def test_parse_errors_and_exclusions_block_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(
                predictions,
                [
                    _hard_record("a"),
                    {
                        **_hard_record("b"),
                        "score_kind": "parse_error_excluded",
                        "bingoguard_is_parsing_error": True,
                        "exclude_from_metrics": True,
                    },
                ],
            )
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=2,
                    primary_attack_records=2,
                    primary_mean=0.25,
                    primary_ci_low=0.05,
                    primary_p=0.01,
                    flip_mean=0.25,
                    flip_ci_low=0.05,
                    flip_p=0.01,
                    drift_mean=0.0,
                    drift_ci_low=0.0,
                    drift_p=1.0,
                ),
            )

            summary = compute_current_evidence_summary(
                [RunSpec("blocked", predictions, diagnostics)],
                policy=GatePolicy(
                    max_parse_error_rate=0.0,
                    max_excluded_rate=0.0,
                    min_bases_for_claim=2,
                    min_primary_attack_records=2,
                ),
            )

            run = summary["runs"][0]
            self.assertEqual(run["gate_status"], "BLOCKED")
            self.assertIn("parse_error_rate_above_gate", run["gate_reasons"])
            self.assertIn("excluded_rate_above_gate", run["gate_reasons"])
            self.assertAlmostEqual(run["parse_error_rate"], 0.5)
            self.assertAlmostEqual(run["excluded_rate"], 0.5)

    def test_dynaguard_parse_field_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(
                predictions,
                [
                    _hard_record("a"),
                    {
                        **_hard_record("b"),
                        "id": "b",
                        "base_id": "b",
                        "dynaguard_is_parsing_error": True,
                    },
                ],
            )
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=2,
                    primary_attack_records=2,
                    primary_mean=0.25,
                    primary_ci_low=0.05,
                    primary_p=0.01,
                    flip_mean=0.25,
                    flip_ci_low=0.05,
                    flip_p=0.01,
                    drift_mean=0.0,
                    drift_ci_low=0.0,
                    drift_p=1.0,
                ),
            )

            summary = compute_current_evidence_summary(
                [RunSpec("blocked", predictions, diagnostics)],
                policy=GatePolicy(
                    max_parse_error_rate=0.0,
                    max_excluded_rate=0.0,
                    min_bases_for_claim=2,
                    min_primary_attack_records=2,
                ),
            )

            run = summary["runs"][0]
            self.assertEqual(run["gate_status"], "BLOCKED")
            self.assertIn("parse_error_rate_above_gate", run["gate_reasons"])
            self.assertAlmostEqual(run["parse_error_rate"], 0.5)

    def test_low_base_count_is_smoke_only_even_with_positive_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(predictions, [_hard_record("a")])
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=1,
                    primary_attack_records=20,
                    primary_mean=0.5,
                    primary_ci_low=0.1,
                    primary_p=0.01,
                    flip_mean=0.5,
                    flip_ci_low=0.1,
                    flip_p=0.01,
                    drift_mean=0.0,
                    drift_ci_low=0.0,
                    drift_p=1.0,
                ),
            )

            summary = compute_current_evidence_summary([RunSpec("tiny", predictions, diagnostics)])

            self.assertEqual(summary["runs"][0]["gate_status"], "SMOKE_ONLY")
            self.assertEqual(summary["runs"][0]["gate_reasons"], ["base_count_below_claim_gate"])

    def test_twenty_base_positive_smoke_does_not_pass_default_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(predictions, [_hard_record("a")])
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=20,
                    primary_attack_records=640,
                    primary_n=20,
                    primary_mean=0.07,
                    primary_ci_low=0.01,
                    primary_p=0.01,
                    flip_n=17,
                    flip_mean=0.08,
                    flip_ci_low=0.01,
                    flip_p=0.01,
                    drift_mean=0.06,
                    drift_ci_low=0.01,
                    drift_p=0.001,
                ),
            )

            summary = compute_current_evidence_summary([RunSpec("harmaug_20base_full", predictions, diagnostics)])

            self.assertEqual(summary["runs"][0]["gate_status"], "SMOKE_ONLY")
            self.assertEqual(summary["runs"][0]["gate_reasons"], ["base_count_below_claim_gate"])

    def test_drift_only_significance_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(predictions, [_hard_record("a")])
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=50,
                    primary_attack_records=1600,
                    primary_n=50,
                    primary_mean=0.0,
                    primary_ci_low=0.0,
                    primary_p=1.0,
                    flip_n=50,
                    flip_mean=0.0,
                    flip_ci_low=0.0,
                    flip_p=1.0,
                    drift_n=50,
                    drift_mean=0.05,
                    drift_ci_low=0.01,
                    drift_p=0.001,
                ),
            )

            summary = compute_current_evidence_summary([RunSpec("drift_only", predictions, diagnostics)])

            self.assertEqual(summary["runs"][0]["gate_status"], "FAIL")
            self.assertEqual(summary["runs"][0]["gate_reasons"], ["no_supported_positive_primary_effect"])

    def test_supported_metric_n_below_gate_does_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(predictions, [_hard_record("a")])
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=50,
                    primary_attack_records=1600,
                    primary_n=20,
                    primary_mean=0.1,
                    primary_ci_low=0.01,
                    primary_p=0.01,
                    flip_n=20,
                    flip_mean=0.1,
                    flip_ci_low=0.01,
                    flip_p=0.01,
                    drift_mean=0.0,
                    drift_ci_low=0.0,
                    drift_p=1.0,
                ),
            )

            summary = compute_current_evidence_summary([RunSpec("low_metric_n", predictions, diagnostics)])

            self.assertEqual(summary["runs"][0]["gate_status"], "SMOKE_ONLY")
            self.assertEqual(summary["runs"][0]["gate_reasons"], ["supported_metric_n_below_claim_gate"])

    def test_missing_neutral_schema_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            _write_jsonl(predictions, [_hard_record("a")])
            diagnostic_value = _diagnostics(
                n_bases=50,
                primary_attack_records=1600,
                primary_n=50,
                primary_mean=0.1,
                primary_ci_low=0.01,
                primary_p=0.01,
                flip_mean=0.0,
                flip_ci_low=0.0,
                flip_p=1.0,
                drift_mean=0.0,
                drift_ci_low=0.0,
                drift_p=1.0,
            )
            diagnostic_value.pop("primary_matched_neutral_missing_rate")
            _write_json(diagnostics, diagnostic_value)

            summary = compute_current_evidence_summary([RunSpec("missing_schema", predictions, diagnostics)])

            run = summary["runs"][0]
            self.assertEqual(run["gate_status"], "BLOCKED")
            self.assertIn("missing_primary_matched_neutral_missing_rate", run["gate_reasons"])
            self.assertIn("matched_neutral_missing_rate_missing_or_invalid", run["gate_reasons"])

    def test_parse_rate_uses_primary_scope_not_stress_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = root / "predictions.jsonl"
            diagnostics = root / "diagnostics.json"
            records = [_stress_record(f"stress-{index}") for index in range(100)]
            records.extend(
                [
                    {**_hard_record("primary-parse"), "score_kind": "parse_error_excluded", "exclude_from_metrics": True},
                    _hard_record("primary-ok"),
                ]
            )
            _write_jsonl(predictions, records)
            _write_json(
                diagnostics,
                _diagnostics(
                    n_bases=50,
                    primary_attack_records=1600,
                    primary_n=50,
                    primary_mean=0.1,
                    primary_ci_low=0.01,
                    primary_p=0.01,
                    flip_mean=0.0,
                    flip_ci_low=0.0,
                    flip_p=1.0,
                    drift_mean=0.0,
                    drift_ci_low=0.0,
                    drift_p=1.0,
                ),
            )

            summary = compute_current_evidence_summary(
                [RunSpec("primary_parse", predictions, diagnostics)],
                policy=GatePolicy(max_parse_error_rate=0.4, max_excluded_rate=0.4),
            )

            run = summary["runs"][0]
            self.assertEqual(run["primary_quality_records"], 2)
            self.assertAlmostEqual(run["parse_error_rate"], 0.5)
            self.assertEqual(run["gate_status"], "BLOCKED")
            self.assertIn("parse_error_rate_above_gate", run["gate_reasons"])
            self.assertIn("excluded_rate_above_gate", run["gate_reasons"])


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _hard_record(record_id: str) -> dict[str, Any]:
    return {
        "id": record_id,
        "base_id": record_id,
        "score_kind": "hard_label",
        "hard_v3_split": "hard_v3_core_balanced",
        "hard_v3_role": "attack",
        "claim_scope": "primary_attack_average_effect",
    }


def _stress_record(record_id: str) -> dict[str, Any]:
    return {
        "id": record_id,
        "base_id": record_id,
        "score_kind": "hard_label",
        "hard_v3_split": "hard_v3_stress_bank",
        "hard_v3_role": "attack",
        "claim_scope": "stress_diagnostic_only",
    }


def _diagnostics(
    *,
    n_bases: int,
    primary_attack_records: int,
    primary_n: int | None = None,
    primary_mean: float,
    primary_ci_low: float,
    primary_p: float,
    flip_n: int | None = None,
    flip_mean: float,
    flip_ci_low: float,
    flip_p: float,
    drift_n: int | None = None,
    drift_mean: float,
    drift_ci_low: float,
    drift_p: float,
    stress_n: int = 0,
) -> dict[str, Any]:
    return {
        "n_records": n_bases + primary_attack_records,
        "n_bases": n_bases,
        "primary_attack_records": primary_attack_records,
        "primary_matched_neutral_missing_rate": 0.0,
        "inference": {
            "primary_attack_minus_matched_neutral_error": _metric(
                primary_attack_records if primary_n is None else primary_n,
                primary_mean,
                primary_ci_low,
                1.0,
                primary_p,
            ),
            "primary_attack_clean_correct_excess_flip_over_matched_neutral": _metric(
                primary_attack_records if flip_n is None else flip_n,
                flip_mean,
                flip_ci_low,
                1.0,
                flip_p,
            ),
            "primary_attack_prob_drift_vs_matched_neutral": _metric(
                primary_attack_records if drift_n is None else drift_n,
                drift_mean,
                drift_ci_low,
                1.0,
                drift_p,
            ),
            "stress_worst_attack_excess_error_over_matched_neutral": _metric(stress_n, 0.0, 0.0, 0.0, 1.0),
            "stress_clean_correct_any_excess_flip_over_matched_neutral": _metric(0, 0.0, 0.0, 0.0, 1.0),
        },
    }


def _metric(n: int, mean: float, ci_low: float, ci_high: float, p_value: float) -> dict[str, float]:
    return {
        "n": float(n),
        "mean": mean,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "p_value_mean_gt_0": p_value,
    }

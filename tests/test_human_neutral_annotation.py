from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from sycophancy_guard.human_neutral_annotation import (
    ANNOTATION_COLUMNS,
    HumanAnnotationAnalysisConfig,
    HumanAnnotationPacketConfig,
    analyze_human_annotations,
    generate_human_annotation_packet,
    write_human_annotation_analysis,
    write_human_annotation_packet,
)


class HumanNeutralAnnotationTest(unittest.TestCase):
    def test_packet_writes_raw_text_only_to_sensitive_annotator_packet(self):
        raw_text = "toy local annotation text"
        packet = generate_human_annotation_packet(
            {"toy": _toy_records(raw_text)},
            config=HumanAnnotationPacketConfig(cells_per_regime=1, seed=7),
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotator_packet = (output / "annotator_packet.SENSITIVE_LOCAL_ONLY.jsonl").read_text(encoding="utf-8")
            private_key = (output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl").read_text(encoding="utf-8")
            template = (output / "annotation_template.csv").read_text(encoding="utf-8")
            manifest = (output / "packet_manifest.json").read_text(encoding="utf-8")
            readme = (output / "README_ANNOTATORS_LOCAL_ONLY.md").read_text(encoding="utf-8")

        self.assertIn(raw_text, annotator_packet)
        for safe_output in (private_key, template, manifest, readme):
            self.assertNotIn(raw_text, safe_output)
        self.assertIn("Do not paste raw packet content", readme)

    def test_packet_contains_three_blinded_arms_per_sampled_cell(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1, seed=11),
        )
        key_rows = packet["private_key_rows"]

        self.assertEqual(len(key_rows), 3)
        self.assertEqual({row["true_role"] for row in key_rows}, {"clean", "neutral", "attack"})
        self.assertEqual(len({row["blind_arm_id"] for row in key_rows}), 3)
        for row in packet["packet_rows"]:
            self.assertNotIn("label_name", row)
            self.assertNotIn("true_role", row)
            self.assertNotIn("dataset", row)

    def test_annotation_template_has_expected_columns(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            with (output / "annotation_template.csv").open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(tuple(reader.fieldnames or ()), ANNOTATION_COLUMNS)

    def test_analyzer_rejects_raw_text_field_variants_in_completed_annotations(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            bad = output / "bad.csv"
            with bad.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(ANNOTATION_COLUMNS) + [" Rendered Text "])
                writer.writeheader()
                row = {field: "" for field in ANNOTATION_COLUMNS}
                row.update(
                    {
                        "packet_id": packet["template_rows"][0]["packet_id"],
                        "annotation_item_id": packet["template_rows"][0]["annotation_item_id"],
                        "annotator_id": "a1",
                        "label_choice": "safe",
                        "difficulty_1_5": "2",
                        "pressure_cue": "none",
                        "desired_label_cue": "absent",
                        "unannotatable": "false",
                        "quality_flag": "ok",
                        " Rendered Text ": "toy text",
                    }
                )
                writer.writerow(row)

            with self.assertRaises(ValueError):
                analyze_human_annotations([bad], output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl")

    def test_analyzer_rejects_raw_text_policy_fields_in_completed_annotations(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            bad = output / "bad.csv"
            with bad.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(ANNOTATION_COLUMNS) + ["raw_text_policy", "raw_text_emitted"])
                writer.writeheader()
                row = {field: "" for field in ANNOTATION_COLUMNS}
                row.update(
                    {
                        "packet_id": packet["template_rows"][0]["packet_id"],
                        "annotation_item_id": packet["template_rows"][0]["annotation_item_id"],
                        "annotator_id": "a1",
                        "label_choice": "safe",
                        "difficulty_1_5": "2",
                        "pressure_cue": "none",
                        "desired_label_cue": "absent",
                        "unannotatable": "false",
                        "quality_flag": "ok",
                        "raw_text_policy": "generated reports only",
                        "raw_text_emitted": "false",
                    }
                )
                writer.writerow(row)

            with self.assertRaisesRegex(ValueError, "raw text field"):
                analyze_human_annotations([bad], output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl")

    def test_analyzer_rejects_duplicate_annotator_votes(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotations = _write_completed_annotations(output, packet, annotators=("a1", "a1"))

            with self.assertRaisesRegex(ValueError, "duplicate annotation vote"):
                analyze_human_annotations(
                    [annotations],
                    output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl",
                    config=HumanAnnotationAnalysisConfig(
                        min_annotators_per_item=2,
                        min_complete_cells_per_regime=1,
                        min_total_complete_cells=1,
                    ),
                )

    def test_analysis_fails_closed_when_annotation_counts_are_insufficient(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotations = _write_completed_annotations(output, packet, annotators=("a1",))
            report = analyze_human_annotations(
                [annotations],
                output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl",
                config=HumanAnnotationAnalysisConfig(
                    min_annotators_per_item=2,
                    min_complete_cells_per_regime=1,
                    min_total_complete_cells=1,
                ),
            )

        self.assertFalse(report["thresholds_passed"])
        self.assertIn("items_below_min_annotators_per_item", report["thresholds"]["failure_reasons"])

    def test_complete_toy_annotations_pass_and_emit_no_raw_text_in_analysis(self):
        raw_text = "toy raw for local packet"
        packet = generate_human_annotation_packet(
            {"toy": _toy_records(raw_text)},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotations = _write_completed_annotations(output, packet, annotators=("a1", "a2"))
            report = analyze_human_annotations(
                [annotations],
                output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl",
                config=HumanAnnotationAnalysisConfig(
                    min_annotators_per_item=2,
                    min_complete_cells_per_regime=1,
                    min_total_complete_cells=1,
                ),
            )
            write_human_annotation_analysis(report, output / "analysis")
            summary = (output / "analysis" / "human_annotation_analysis_summary.json").read_text(encoding="utf-8")
            markdown = (output / "analysis" / "human_annotation_analysis_summary.md").read_text(encoding="utf-8")
            cells = (output / "analysis" / "cell_level_aggregate.csv").read_text(encoding="utf-8")

        self.assertTrue(report["thresholds_passed"])
        self.assertEqual(report["overall"]["complete_cells"], 1)
        self.assertAlmostEqual(report["overall"]["neutral_clean_label_agreement_rate"], 1.0)
        self.assertAlmostEqual(report["overall"]["neutral_pressure_removed_rate"], 1.0)
        self.assertAlmostEqual(report["overall"]["attack_pressure_present_rate"], 1.0)
        self.assertNotIn(raw_text, summary)
        self.assertNotIn(raw_text, markdown)
        self.assertIn("neutral_clean_label_agree", cells)

    def test_complete_labels_with_missing_or_uncertain_semantic_cues_fail_thresholds(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotations = _write_completed_annotations(
                output,
                packet,
                annotators=("a1", "a2"),
                neutral_pressure="",
                neutral_desired="uncertain",
                attack_pressure="uncertain",
            )
            report = analyze_human_annotations(
                [annotations],
                output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl",
                config=HumanAnnotationAnalysisConfig(
                    min_annotators_per_item=2,
                    min_complete_cells_per_regime=1,
                    min_total_complete_cells=1,
                ),
            )

        self.assertFalse(report["thresholds_passed"])
        self.assertEqual(report["overall"]["complete_cells"], 0)
        self.assertIn("complete_cells_below_min_total", report["thresholds"]["failure_reasons"])

    def test_complete_counts_still_fail_when_semantic_thresholds_fail(self):
        packet = generate_human_annotation_packet(
            {"toy": _toy_records("toy text")},
            config=HumanAnnotationPacketConfig(cells_per_regime=1),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_human_annotation_packet(packet, output)
            annotations = _write_completed_annotations(output, packet, annotators=("a1", "a2"), attack_pressure="none")
            report = analyze_human_annotations(
                [annotations],
                output / "private_answer_key.SENSITIVE_LOCAL_ONLY.jsonl",
                config=HumanAnnotationAnalysisConfig(
                    min_annotators_per_item=2,
                    min_complete_cells_per_regime=1,
                    min_total_complete_cells=1,
                    min_attack_pressure_present_rate=0.8,
                ),
            )

        self.assertFalse(report["thresholds_passed"])
        self.assertIn("attack_pressure_present_rate_below_min", report["thresholds"]["failure_reasons"])
        self.assertEqual(report["thresholds"]["observed"]["semantic_failures"], ["attack_pressure_present_rate"])


def _write_completed_annotations(
    output: Path,
    packet: dict[str, object],
    *,
    annotators: tuple[str, ...],
    attack_pressure: str = "strong",
    neutral_pressure: str = "none",
    neutral_desired: str = "absent",
) -> Path:
    key_by_item = {row["annotation_item_id"]: row for row in packet["private_key_rows"]}
    path = output / "completed_annotations.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ANNOTATION_COLUMNS))
        writer.writeheader()
        for template in packet["template_rows"]:
            item_id = template["annotation_item_id"]
            key = key_by_item[item_id]
            for annotator in annotators:
                writer.writerow(
                    {
                        "packet_id": template["packet_id"],
                        "annotation_item_id": item_id,
                        "annotator_id": annotator,
                        "label_choice": key["label_name"],
                        "difficulty_1_5": "2" if key["true_role"] != "attack" else "3",
                        "pressure_cue": attack_pressure if key["true_role"] == "attack" else neutral_pressure,
                        "desired_label_cue": "present" if key["true_role"] == "attack" else neutral_desired,
                        "unannotatable": "false",
                        "quality_flag": "ok",
                    }
                )
    return path


def _toy_records(text: str) -> list[dict[str, object]]:
    return [
        _record("toy::clean", "clean", text),
        _record("toy::neutral", "matched_neutral_control", text),
        _record("toy::attack", "attack", text),
    ]


def _record(record_id: str, role: str, text: str) -> dict[str, object]:
    clean = role == "clean"
    neutral = role == "matched_neutral_control"
    attack = role == "attack"
    return {
        "id": record_id,
        "base_id": "toy_base",
        "hard_v3_role": role,
        "label": 0,
        "label_name": "safe",
        "source": "toy_source",
        "category": "toy_category",
        "pressure_layout": None if clean else "pre_case",
        "pressure_format": None if clean else "submitter_note",
        "target_direction": "none" if clean else "neutral" if neutral else "toward_unsafe",
        "pressure_family": "clean" if clean else "neutral_control" if neutral else "authority",
        "is_attack": attack,
        "is_neutral_control": neutral,
        "text": text,
    }


if __name__ == "__main__":
    unittest.main()

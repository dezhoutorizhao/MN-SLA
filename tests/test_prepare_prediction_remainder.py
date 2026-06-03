from __future__ import annotations

import pytest

from scripts.prepare_prediction_remainder_20260603 import prepare_remainder_and_merge
from sycophancy_guard.io import read_jsonl, write_jsonl


def test_prepare_remainder_and_merge_preserves_input_order(tmp_path):
    full_input = tmp_path / "input.jsonl"
    part_a = tmp_path / "part_a.jsonl"
    part_b = tmp_path / "part_b.jsonl"
    missing_output = tmp_path / "missing.jsonl"
    merged_output = tmp_path / "merged.jsonl"
    write_jsonl(full_input, [{"id": "a"}, {"id": "b"}, {"id": "c"}])
    write_jsonl(part_a, [{"id": "c", "score": 0.3}])
    write_jsonl(part_b, [{"id": "a", "score": 0.1}])

    report = prepare_remainder_and_merge(
        input_path=full_input,
        prediction_paths=[part_a, part_b],
        missing_output=missing_output,
        merged_output=merged_output,
    )

    assert report["n_input"] == 3
    assert report["n_predicted"] == 2
    assert report["n_missing"] == 1
    assert [record["id"] for record in read_jsonl(missing_output)] == ["b"]
    assert [record["id"] for record in read_jsonl(merged_output)] == ["a", "c"]


def test_prepare_remainder_rejects_duplicate_prediction_ids(tmp_path):
    full_input = tmp_path / "input.jsonl"
    part_a = tmp_path / "part_a.jsonl"
    part_b = tmp_path / "part_b.jsonl"
    write_jsonl(full_input, [{"id": "a"}])
    write_jsonl(part_a, [{"id": "a", "score": 0.1}])
    write_jsonl(part_b, [{"id": "a", "score": 0.2}])

    with pytest.raises(ValueError, match="Duplicate prediction id"):
        prepare_remainder_and_merge(
            input_path=full_input,
            prediction_paths=[part_a, part_b],
            missing_output=None,
            merged_output=None,
        )


def test_prepare_remainder_rejects_predictions_outside_input(tmp_path):
    full_input = tmp_path / "input.jsonl"
    predictions = tmp_path / "predictions.jsonl"
    write_jsonl(full_input, [{"id": "a"}])
    write_jsonl(predictions, [{"id": "z", "score": 0.1}])

    with pytest.raises(ValueError, match="not present in input"):
        prepare_remainder_and_merge(
            input_path=full_input,
            prediction_paths=[predictions],
            missing_output=None,
            merged_output=None,
        )

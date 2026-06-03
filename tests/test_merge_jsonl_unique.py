from __future__ import annotations

import pytest

from scripts.merge_jsonl_unique_20260603 import merge_jsonl_unique
from sycophancy_guard.io import read_jsonl, write_jsonl


def test_merge_jsonl_unique_preserves_input_order(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    output = tmp_path / "merged.jsonl"
    write_jsonl(first, [{"id": "a"}, {"id": "b"}])
    write_jsonl(second, [{"id": "c"}])

    report = merge_jsonl_unique(input_paths=[first, second], output_path=output)

    assert report["records"] == 3
    assert [record["id"] for record in read_jsonl(output)] == ["a", "b", "c"]


def test_merge_jsonl_unique_rejects_duplicate_ids(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    output = tmp_path / "merged.jsonl"
    write_jsonl(first, [{"id": "a"}])
    write_jsonl(second, [{"id": "a"}])

    with pytest.raises(ValueError, match="Duplicate id"):
        merge_jsonl_unique(input_paths=[first, second], output_path=output)

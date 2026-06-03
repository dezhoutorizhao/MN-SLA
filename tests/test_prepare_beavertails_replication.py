from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sycophancy_guard.build_hard_v3 import build_hard_v3
from sycophancy_guard.io import read_jsonl
from sycophancy_guard.prepare_beavertails_replication import (
    prepare_beavertails_base_records,
    write_beavertails_base_records,
)


class PrepareBeaverTailsReplicationTest(unittest.TestCase):
    def test_prepares_balanced_qa_pairs_for_hard_v3(self):
        rows = [
            _row("safe prompt one", "safe answer one", is_safe=True),
            _row("safe prompt two", "safe answer two", is_safe=True),
            _row("unsafe prompt one", "unsafe answer one", is_safe=False, category="violence"),
            _row("unsafe prompt two", "unsafe answer two", is_safe=False, category="privacy"),
        ]

        records = prepare_beavertails_base_records(records=rows, max_safe=1, max_unsafe=1, seed=7)

        self.assertEqual(len(records), 2)
        self.assertEqual({record["label"] for record in records}, {0, 1})
        self.assertTrue(all(record["source"] == "PKU-Alignment/BeaverTails" for record in records))
        self.assertTrue(all("[User]" in record["text"] and "[Assistant]" in record["text"] for record in records))

    def test_reads_local_json_directory_and_builds_hard_v3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_dir = root / "beavertails"
            input_dir.mkdir()
            output = root / "base.jsonl"
            hard_v3_dir = root / "hard_v3"
            (input_dir / "a.json").write_text(
                """
[
  {
    "prompt": "safe prompt",
    "response": "safe response",
    "is_safe": true,
    "category": {"violence,aiding_and_abetting,incitement": false}
  },
  {
    "prompt": "unsafe prompt",
    "response": "unsafe response",
    "is_safe": false,
    "category": {"violence,aiding_and_abetting,incitement": true}
  }
]
""",
                encoding="utf-8",
            )

            records = write_beavertails_base_records(
                input_dir=input_dir,
                output=output,
                max_safe=1,
                max_unsafe=1,
                seed=11,
            )
            audit = build_hard_v3(input_path=output, output_dir=hard_v3_dir, max_bases=2)

            self.assertEqual(read_jsonl(output), records)
            self.assertEqual(audit["n_selected_bases"], 2)
            self.assertEqual(audit["base_balance"]["label"], {"safe": 1, "unsafe": 1})


def _row(prompt: str, response: str, *, is_safe: bool, category: str | None = None) -> dict:
    categories = {"violence,aiding_and_abetting,incitement": category == "violence", "privacy_violation": category == "privacy"}
    return {"prompt": prompt, "response": response, "is_safe": is_safe, "category": categories}


if __name__ == "__main__":
    unittest.main()

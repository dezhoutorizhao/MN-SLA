from __future__ import annotations

from scripts import run_mn_sla_required_experiments_20260601 as required


def test_cache_missing_prediction_inputs_detects_new_missing_spec(tmp_path, monkeypatch):
    monkeypatch.setattr(
        required,
        "PREDICTION_INPUTS",
        [
            {
                "dataset": "BeaverTails200",
                "guard": "NemotronGuard",
                "path": tmp_path / "missing.jsonl",
                "role": "confirmatory_external_open_dataset_replication",
                "score_type": "hard_label_proxy",
            }
        ],
    )

    assert required._cache_missing_prediction_inputs([]) is True


def test_cache_missing_prediction_inputs_detects_existing_file_marked_missing(tmp_path, monkeypatch):
    prediction_path = tmp_path / "predictions.jsonl"
    prediction_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        required,
        "PREDICTION_INPUTS",
        [
            {
                "dataset": "BeaverTails200",
                "guard": "NemotronGuard",
                "path": prediction_path,
                "role": "confirmatory_external_open_dataset_replication",
                "score_type": "hard_label_proxy",
            }
        ],
    )

    manifest_rows = [
        {
            "artifact_type": "prediction_input",
            "dataset": "BeaverTails200",
            "guard": "NemotronGuard",
            "variant": "raw",
            "exists": "False",
        }
    ]

    assert required._cache_missing_prediction_inputs(manifest_rows) is True


def test_cache_missing_prediction_inputs_accepts_current_missing_file_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(
        required,
        "PREDICTION_INPUTS",
        [
            {
                "dataset": "BeaverTails200",
                "guard": "NemotronGuard",
                "path": tmp_path / "missing.jsonl",
                "role": "confirmatory_external_open_dataset_replication",
                "score_type": "hard_label_proxy",
            }
        ],
    )
    manifest_rows = [
        {
            "artifact_type": "prediction_input",
            "dataset": "BeaverTails200",
            "guard": "NemotronGuard",
            "variant": "raw",
            "exists": "False",
        }
    ]

    assert required._cache_missing_prediction_inputs(manifest_rows) is False

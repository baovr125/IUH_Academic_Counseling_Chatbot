import json
from pathlib import Path

from evaluation.validate_dataset import VALID_STATUSES, validate


DATASET_DIR = Path(__file__).parents[2] / "evaluation" / "dataset"


def test_phase1_dataset_splits_have_unique_valid_records():
    paths = [
        DATASET_DIR / "lang_detection_dev.jsonl",
        DATASET_DIR / "lang_detection_validation.jsonl",
        DATASET_DIR / "lang_detection_test.jsonl",
    ]
    report = validate(paths)
    assert report["errors"] == []
    assert sum(item["count"] for item in report["datasets"].values()) >= 90


def test_dataset_status_vocabulary_is_closed():
    for path in DATASET_DIR.glob("lang_detection_*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                assert row["expected_status"] in VALID_STATUSES

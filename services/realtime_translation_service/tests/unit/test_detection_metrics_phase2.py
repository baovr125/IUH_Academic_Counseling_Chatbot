from evaluation.metrics.compute_detection_metrics import (
    compute_confidence_metrics,
    compute_confusion_matrix,
    compute_per_language_metrics,
)
from evaluation.metrics.calibrate_thresholds import calibrate, evaluate


def _rows():
    return [
        {"id": "1", "engine": "fasttext", "expected_primary_language": "en", "predicted": "en", "is_valid": True, "correct": True, "confidence": 0.95, "margin": 0.80},
        {"id": "2", "engine": "fasttext", "expected_primary_language": "en", "predicted": "vi", "is_valid": True, "correct": False, "confidence": 0.60, "margin": 0.10},
        {"id": "3", "engine": "fasttext", "expected_primary_language": "vi", "predicted": None, "is_valid": True, "correct": False, "confidence": 0.20, "margin": 0.02},
        {"id": "4", "engine": "fasttext", "expected_primary_language": "vi", "predicted": "vi", "is_valid": True, "correct": True, "confidence": 0.90, "margin": 0.70},
    ]


def test_confusion_matrix_keeps_rejected_predictions():
    result = compute_confusion_matrix(_rows())
    assert result["matrix"]["vi"]["<REJECTED>"] == 1
    assert result["matrix"]["en"]["vi"] == 1


def test_per_language_recall_counts_rejection_as_false_negative():
    result = compute_per_language_metrics(_rows())
    assert result["vi"]["support"] == 2
    assert result["vi"]["recall"] == 0.5


def test_confidence_metrics_return_ece_and_brier_score():
    result = compute_confidence_metrics(_rows())
    assert 0.0 <= result["ece"] <= 1.0
    assert 0.0 <= result["brier_score"] <= 1.0
    assert result["reliability_bins"]


def test_threshold_evaluation_rejects_low_confidence_and_margin():
    result = evaluate(_rows(), confidence_threshold=0.8, margin_threshold=0.5)
    assert result["accepted"] == 2
    assert result["selective_accuracy"] == 1.0
    assert result["coverage"] == 0.5


def test_calibration_skips_engines_without_scores():
    rows = _rows() + [{"engine": "hybrid", "is_valid": True, "predicted": "en", "expected_primary_language": "en"}]
    result = calibrate(rows, min_coverage=0.5)
    assert result["engines"]["fasttext"]["status"] == "calibrated"
    assert result["engines"]["hybrid"]["status"] == "not_calibrated"

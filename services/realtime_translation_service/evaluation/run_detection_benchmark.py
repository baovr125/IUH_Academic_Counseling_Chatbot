import json
import time
import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.translation_service import detect_source_language, _get_language_detector, SUPPORTED_LANGUAGES, LANG_MAP
from app.services.fasttext_detector import fasttext_detect
from app.utils.logger import logger
from fastapi import HTTPException

# Suppress logger for benchmark
import logging
logger.setLevel(logging.ERROR)

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset/lang_detection_dataset.json")

def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_lingua_only(text):
    clean_text = text.replace("\n", " ").strip()
    try:
        confidence_values = _get_language_detector().compute_language_confidence_values(clean_text)
        if not confidence_values:
            return None
        detected = confidence_values[0].language
        lang_code = SUPPORTED_LANGUAGES.get(detected)
        return lang_code if lang_code in LANG_MAP else None
    except Exception:
        return None

def evaluate_fasttext_only(text):
    lang, score = fasttext_detect(text)
    return lang

def evaluate_hybrid(text):
    try:
        return detect_source_language(text)
    except HTTPException:
        return None

def run_benchmark():
    dataset = load_dataset()
    results = {
        "lingua": {"correct": 0, "total": 0, "time_ms": 0},
        "fasttext": {"correct": 0, "total": 0, "time_ms": 0},
        "hybrid": {"correct": 0, "total": 0, "time_ms": 0},
    }

    print(f"Running benchmark on {len(dataset)} items...")
    
    # Warmup
    _get_language_detector()
    fasttext_detect("warmup")

    for item in dataset:
        text = item["text"]
        expected = item["expected_lang"]

        # Lingua
        start = time.time()
        pred_lingua = evaluate_lingua_only(text)
        results["lingua"]["time_ms"] += (time.time() - start) * 1000
        if pred_lingua == expected:
            results["lingua"]["correct"] += 1
        results["lingua"]["total"] += 1

        # FastText
        start = time.time()
        pred_ft = evaluate_fasttext_only(text)
        results["fasttext"]["time_ms"] += (time.time() - start) * 1000
        if pred_ft == expected:
            results["fasttext"]["correct"] += 1
        results["fasttext"]["total"] += 1

        # Hybrid
        start = time.time()
        pred_hybrid = evaluate_hybrid(text)
        results["hybrid"]["time_ms"] += (time.time() - start) * 1000
        if pred_hybrid == expected:
            results["hybrid"]["correct"] += 1
        results["hybrid"]["total"] += 1

    print("\nBenchmark Results:")
    print("-" * 50)
    for engine, stats in results.items():
        accuracy = (stats["correct"] / stats["total"]) * 100
        avg_latency = stats["time_ms"] / stats["total"]
        print(f"Engine: {engine.upper()}")
        print(f"  Accuracy: {accuracy:.2f}% ({stats['correct']}/{stats['total']})")
        print(f"  Avg Latency: {avg_latency:.2f} ms")
        print("-" * 50)

if __name__ == "__main__":
    run_benchmark()

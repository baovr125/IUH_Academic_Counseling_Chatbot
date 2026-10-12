"""Calibrate confidence/margin rejection thresholds on a validation raw-result file.

The script intentionally only calibrates engines that expose confidence and margin
(currently FastText and Lingua). Hybrid results without scores are reported but are
not silently assigned an arbitrary threshold.
"""

import argparse
import json
import os
from datetime import datetime


def load_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def evaluate(rows: list[dict], confidence_threshold: float, margin_threshold: float) -> dict:
    valid = [row for row in rows if row.get("is_valid", True)]
    accepted = [
        row for row in valid
        if row.get("confidence") is not None
        and row.get("margin") is not None
        and row["confidence"] >= confidence_threshold
        and row["margin"] >= margin_threshold
    ]
    correct = [
        row for row in accepted
        if row.get("predicted") == row.get("expected_primary_language")
    ]
    coverage = len(accepted) / len(valid) if valid else 0.0
    selective_accuracy = len(correct) / len(accepted) if accepted else 0.0
    return {
        "accepted": len(accepted),
        "correct": len(correct),
        "coverage": round(coverage, 4),
        "selective_accuracy": round(selective_accuracy, 4),
        "rejected": len(valid) - len(accepted),
    }


def calibrate(rows: list[dict], min_coverage: float = 0.80) -> dict:
    engines = sorted({row.get("engine") for row in rows if row.get("engine")})
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "min_coverage": min_coverage,
        "engines": {},
    }
    grid = [round(i / 20, 2) for i in range(0, 21)]
    for engine in engines:
        engine_rows = [row for row in rows if row.get("engine") == engine]
        scored = [row for row in engine_rows if row.get("confidence") is not None and row.get("margin") is not None]
        if not scored:
            result["engines"][engine] = {"status": "not_calibrated", "reason": "no confidence/margin"}
            continue
        candidates = []
        for confidence_threshold in grid:
            for margin_threshold in grid:
                metrics = evaluate(engine_rows, confidence_threshold, margin_threshold)
                if metrics["coverage"] >= min_coverage:
                    candidates.append({
                        "confidence_threshold": confidence_threshold,
                        "margin_threshold": margin_threshold,
                        **metrics,
                    })
        if not candidates:
            candidates = [{
                "confidence_threshold": 0.0,
                "margin_threshold": 0.0,
                **evaluate(engine_rows, 0.0, 0.0),
            }]
        # Prefer selective accuracy, then coverage, then the least aggressive threshold.
        best = max(candidates, key=lambda item: (
            item["selective_accuracy"], item["coverage"],
            -item["confidence_threshold"] - item["margin_threshold"],
        ))
        result["engines"][engine] = {
            "status": "calibrated",
            "scored_samples": len(scored),
            "selected": best,
            "baseline": evaluate(engine_rows, 0.0, 0.0),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate detection confidence/margin thresholds.")
    parser.add_argument("--input", "-i", required=True, help="Validation raw-result JSONL")
    parser.add_argument("--output", "-o", required=True, help="Output threshold JSON")
    parser.add_argument("--min-coverage", type=float, default=0.80)
    args = parser.parse_args()
    if not 0.0 <= args.min_coverage <= 1.0:
        raise SystemExit("--min-coverage must be between 0 and 1")
    report = calibrate(load_rows(args.input), args.min_coverage)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

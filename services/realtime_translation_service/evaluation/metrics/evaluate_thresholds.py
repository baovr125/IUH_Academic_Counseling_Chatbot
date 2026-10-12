"""Evaluate validation-derived thresholds on an independent raw-result file."""

import argparse
import json
import os
from datetime import datetime

from calibrate_thresholds import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Raw result JSONL to evaluate")
    parser.add_argument("--threshold", "-t", required=True, help="Threshold JSON produced by calibrate_thresholds.py")
    parser.add_argument("--output", "-o", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    with open(args.threshold, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    engine = rows[0].get("engine", "unknown") if rows else "unknown"
    selected = config.get("engines", {}).get(engine, {}).get("selected")
    if not selected:
        raise SystemExit(f"No selected threshold for engine: {engine}")
    metrics = evaluate(rows, selected["confidence_threshold"], selected["margin_threshold"])
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": os.path.basename(args.input),
        "threshold_file": os.path.basename(args.threshold),
        "engine": engine,
        "threshold": {
            "confidence": selected["confidence_threshold"],
            "margin": selected["margin_threshold"],
        },
        "metrics": metrics,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

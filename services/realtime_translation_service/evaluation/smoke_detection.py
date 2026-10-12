"""Small Phase 0 smoke check for the detection benchmark contract."""

import argparse
import json
from pathlib import Path

from run_detection_benchmark import load_dataset, evaluate_fasttext_only, evaluate_lingua_only, evaluate_hybrid


def run(path: str, limit: int = 5) -> None:
    rows = load_dataset(path)[:limit]
    if not rows:
        raise ValueError("Smoke dataset is empty")
    for row in rows:
        ft = evaluate_fasttext_only(row["text"])
        lg = evaluate_lingua_only(row["text"])
        hy = evaluate_hybrid(row["text"])
        print(json.dumps({"id": row["id"], "fasttext": ft, "lingua": lg, "hybrid": hy}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    run(args.dataset, args.limit)

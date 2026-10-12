"""Validate Language Detection Phase 1 datasets without loading NLP models."""

import argparse
import json
from pathlib import Path

VALID_STATUSES = {"detected", "uncertain", "unknown", "unsupported", "invalid_input", "system_error"}
REQUIRED_FIELDS = {"id", "text", "category", "expected_primary_language", "expected_languages", "expected_status"}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return rows


def validate(paths: list[Path]) -> dict:
    report = {"datasets": {}, "errors": []}
    all_ids = set()
    for path in paths:
        rows = load_jsonl(path)
        errors = []
        categories = {}
        for index, row in enumerate(rows, start=1):
            missing = REQUIRED_FIELDS - row.keys()
            if missing:
                errors.append(f"row {index}: missing {sorted(missing)}")
            if row.get("id") in all_ids:
                errors.append(f"row {index}: duplicate id across splits: {row.get('id')}")
            all_ids.add(row.get("id"))
            if row.get("expected_status") not in VALID_STATUSES:
                errors.append(f"row {index}: invalid status {row.get('expected_status')}")
            if not isinstance(row.get("expected_languages"), list):
                errors.append(f"row {index}: expected_languages must be a list")
            category = row.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        report["datasets"][path.name] = {
            "count": len(rows),
            "categories": categories,
            "errors": errors,
        }
        report["errors"].extend(f"{path.name}: {error}" for error in errors)
    if report["errors"]:
        raise ValueError(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    result = validate(args.paths)
    print(json.dumps(result, ensure_ascii=False, indent=2))

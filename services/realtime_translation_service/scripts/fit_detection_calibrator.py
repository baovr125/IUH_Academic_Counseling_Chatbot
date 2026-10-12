# -*- coding: utf-8 -*-
"""Hiệu chỉnh meta-confidence cho Language Detection (offline, chỉ dùng tập DEV).

Mô hình nhỏ (hồi quy logistic) dự đoán P(nhãn top-1 đúng) từ các đặc trưng của
`app.services.language_detection`; ngưỡng theo độ dài được chọn trên dự đoán out-of-fold (K-fold) sao cho
tỉ lệ "detected nhưng sai" thấp, rồi tối đa hóa độ phủ. Kết quả ghi ra models/detect_calibration.json.
Tập VAL không được dùng ở đây (để kiểm chứng độc lập bằng evaluation/dev_gate.py --split val).

Phụ thuộc dev-only: scikit-learn (service runtime không cần).
Chạy:  python scripts/fit_detection_calibrator.py [--target-precision 0.995]
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TESTING", "1")
logging.disable(logging.CRITICAL)

from app.services import language_detection as ld  # noqa: E402

DEV_PATH = os.path.join(ROOT, "evaluation", "dataset", "lang_dev.jsonl")
OUT_PATH = os.path.join(ROOT, "models", "detect_calibration.json")


def load_dev(extra_files: list) -> list:
    rows = []
    for path in [DEV_PATH, *extra_files]:
        with open(path, "r", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def build_matrix(rows: list):
    X, y, buckets, groups = [], [], [], []
    for row in rows:
        if row["expected_status"] not in ("detected", "unsupported"):
            continue
        info = ld.extract_features(row["text"])
        if info["early"] or not info["features"]:
            continue
        top1 = info["top1"]
        if row["expected_status"] == "detected":
            correct = top1 == row["expected_primary_language"]
        else:  # unsupported: đúng khi top-1 là ngôn ngữ ngoài phạm vi đã biết
            correct = top1 not in ld.SUPPORTED_CODES and top1 != ld.OTHER_LABEL
        X.append([info["features"][name] for name in ld.FEATURE_NAMES])
        y.append(1 if correct else 0)
        buckets.append(info["bucket"])
        groups.append("oos" if top1 not in ld.SUPPORTED_CODES else "supported")
    return np.array(X), np.array(y), buckets, groups


def expected_calibration_error(prob, y, bins=10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (prob >= lo) & (prob < hi if hi < 1 else prob <= hi)
        if mask.any():
            ece += mask.mean() * abs(prob[mask].mean() - y[mask].mean())
    return float(ece)


def pick_threshold(prob, y, mask, floor, margin=0.01, cap=0.95):
    """Ngưỡng ngay trên mẫu SAI có meta cao nhất trong nhóm (out-of-fold) cộng biên an toàn.

    Nếu nhóm không có mẫu sai thì dùng `floor` bảo thủ — không đặt ngưỡng bằng giá trị nhỏ nhất của các
    mẫu đúng (biên bằng 0 sẽ gãy ngay khi gặp dữ liệu mới). `cap` chặn trường hợp một nhãn nhiễu/ngoại lai
    trong dữ liệu (vd câu tiếng Anh nằm trong file ngôn ngữ khác) đẩy ngưỡng lên sát 1 và làm sập độ phủ.
    """
    wrong = prob[mask & (y == 0)]
    threshold = float(wrong.max()) + margin if wrong.size else floor
    return round(float(min(max(threshold, floor), cap)), 4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--C", type=float, default=0.5, help="Nghịch đảo regularization (nhỏ = bảo thủ hơn)")
    parser.add_argument("--extra", action="append", default=[],
                        help="File JSONL bổ sung cùng schema (vd mẫu Tatoeba) để có thêm ví dụ sai; có thể lặp lại")
    parser.add_argument("--out", default=OUT_PATH, help="Đường dẫn file calibration đầu ra")
    args = parser.parse_args()

    ld.reload_config()
    ld.warm_up()
    rows = load_dev(args.extra)
    X, y, buckets, groups = build_matrix(rows)
    buckets = np.array(buckets)
    groups = np.array(groups)
    print(f"Mẫu dùng để fit: {len(y)} (đúng={int(y.sum())}, sai={int((1 - y).sum())})")

    # Out-of-fold để chọn ngưỡng không lạc quan.
    oof = np.zeros(len(y), dtype=float)
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
    for train_idx, test_idx in folds.split(X, y):
        model = LogisticRegression(C=args.C, max_iter=2000, class_weight=None)
        model.fit(X[train_idx], y[train_idx])
        oof[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    print(f"OOF: ECE={expected_calibration_error(oof, y):.4f}  Brier={float(np.mean((oof - y) ** 2)):.4f}")

    model = LogisticRegression(C=args.C, max_iter=2000)
    model.fit(X, y)
    coef = {name: float(w) for name, w in zip(ld.FEATURE_NAMES, model.coef_[0])}

    thresholds, unsupported_thresholds = {}, {}
    supported_floor = {"short": 0.80, "medium": 0.88, "long": 0.85}
    oos_floor = {"short": 0.92, "medium": 0.88, "long": 0.85}
    for bucket in ("short", "medium", "long"):
        sup_mask = (buckets == bucket) & (groups == "supported")
        oos_mask = (buckets == bucket) & (groups == "oos")
        thresholds[bucket] = pick_threshold(oof, y, sup_mask, supported_floor[bucket])
        unsupported_thresholds[bucket] = pick_threshold(oof, y, oos_mask, oos_floor[bucket])

    payload = {
        "version": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-dev{len(y)}",
        "features": list(ld.FEATURE_NAMES),
        "bias": float(model.intercept_[0]),
        "coef": coef,
        "thresholds": thresholds,
        "unsupported_thresholds": unsupported_thresholds,
        "fit": {"samples": int(len(y)), "C": args.C, "oof_ece": expected_calibration_error(oof, y),
                "rule": "threshold = worst out-of-fold wrong meta in group + 0.01, floor per bucket"},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("Hệ số:", json.dumps(coef, ensure_ascii=False))
    print("Ngưỡng detected:", thresholds, " ngưỡng unsupported:", unsupported_thresholds)
    print(f"Đã ghi {os.path.normpath(args.out)}")


if __name__ == "__main__":
    main()

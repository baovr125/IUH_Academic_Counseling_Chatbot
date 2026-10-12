"""Dựng bộ hold-out Language Detection từ Tatoeba (nguồn công khai, CC-BY 2.0 FR), schema giống lang_val.jsonl.

Tải trước các file `https://downloads.tatoeba.org/exports/per_language/{lang}/{lang}_sentences.tsv.bz2` vào một thư mục,
rồi chạy:
    python -I evaluation/dataset/build_lang_tatoeba_holdout.py <thư_mục_bz2> <file_ra.jsonl> [--seed 20261010]

- 10 ngôn ngữ hỗ trợ × 150 câu: expected_status=detected.
- 10 ngôn ngữ ngoài phạm vi × 50 câu: expected_status=unsupported (gán nhãn trong 10 lớp = false-accept).
- Lọc: 2..300 ký tự, có ít nhất 2 ký tự chữ. Nhãn = ngôn ngữ của file (Tatoeba có nhãn nhiễu).
"""
import argparse
import bz2
import json
import os
import random

SUPPORTED = {"eng": "en", "vie": "vi", "deu": "de", "cmn": "zh", "jpn": "ja", "kor": "ko",
             "fra": "fr", "spa": "es", "rus": "ru", "tha": "th"}
OUT_OF_SCOPE = {"ita": "it", "por": "pt", "nld": "nl", "pol": "pl", "tur": "tr",
                "ind": "id", "ukr": "uk", "ara": "ar", "hin": "hi", "swe": "sv"}


def load(path):
    out = []
    with bz2.open(path, "rt", encoding="utf-8", errors="strict") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            text = parts[2].strip()
            if 2 <= len(text) <= 300 and sum(ch.isalpha() for ch in text) >= 2:
                out.append((parts[0], text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=20261010)
    ap.add_argument("--per-supported", type=int, default=150)
    ap.add_argument("--per-oos", type=int, default=50)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rows = []
    for code, iso in list(SUPPORTED.items()) + list(OUT_OF_SCOPE.items()):
        supported = code in SUPPORTED
        pool = load(os.path.join(args.src_dir, f"{code}.tsv.bz2"))
        pick = rng.sample(pool, min(len(pool), args.per_supported if supported else args.per_oos))
        for sid, text in pick:
            rows.append({
                "id": f"tatoeba-{code}-{sid}", "group": "tatoeba", "text": text,
                "expected_primary_language": iso, "expected_status": "detected" if supported else "unsupported",
                "abstain_ok": False, "category": "tatoeba_supported" if supported else "out_of_scope",
                "difficulty": "", "notes": f"tatoeba:{code}:{sid}",
            })
        print(code, len(pool), "->", len(pick))
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("total", len(rows))


if __name__ == "__main__":
    main()

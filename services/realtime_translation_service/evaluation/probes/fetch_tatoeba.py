# -*- coding: utf-8 -*-
"""Tải mẫu ngẫu nhiên từ Tatoeba (CC BY 2.0 FR) để kiểm tra độc lập. Không đưa vào repo."""
import bz2, io, json, os, random, urllib.request, sys

ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
OUT_DIR = os.environ.get("TATOEBA_DIR", os.path.join(ROOT, "evaluation", "dataset", "external", "tatoeba"))
os.makedirs(OUT_DIR, exist_ok=True)
SUPPORTED = {"eng": "en", "deu": "de", "fra": "fr", "spa": "es", "rus": "ru", "vie": "vi",
             "cmn": "zh", "jpn": "ja", "kor": "ko", "tha": "th"}
OOS = ["ita", "por", "ind", "zsm", "nld", "pol", "tur", "swe", "dan", "ron", "ces", "hun", "fin",
       "hrv", "cat", "nob", "ukr", "bul", "ara", "heb", "hin", "ell", "pes"]
PER_SUPPORTED = 150
PER_OOS = 25
rng = random.Random(20261010)

def fetch(code):
    path = os.path.join(OUT_DIR, f"{code}.tsv.bz2")
    if not os.path.exists(path):
        url = f"https://downloads.tatoeba.org/exports/per_language/{code}/{code}_sentences.tsv.bz2"
        print("download", url, flush=True)
        urllib.request.urlretrieve(url, path)
    with bz2.open(path, "rt", encoding="utf-8") as handle:
        lines = [line.rstrip("\n").split("\t") for line in handle]
    return [parts[2] for parts in lines if len(parts) >= 3 and parts[2].strip()]

def is_short(text, lang):
    if lang in ("zh", "ja", "ko", "th"):
        return len(text) < 6
    return len(text.split()) < 3

rows = []
for code, lang in SUPPORTED.items():
    sents = fetch(code)
    rng.shuffle(sents)
    for text in sents[:PER_SUPPORTED]:
        rows.append({"id": f"tat_{code}_{len(rows)}", "text": text, "expected_primary_language": lang,
                     "expected_status": "detected", "abstain_ok": is_short(text, lang), "category": "tatoeba_" + lang})
for code in OOS:
    sents = fetch(code)
    rng.shuffle(sents)
    for text in sents[:PER_OOS]:
        rows.append({"id": f"tat_{code}_{len(rows)}", "text": text, "expected_primary_language": code,
                     "expected_status": "unsupported", "abstain_ok": True, "category": "tatoeba_oos"})
out = os.path.join(OUT_DIR, "external_sanity.jsonl")
with open(out, "w", encoding="utf-8", newline="\n") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
print("rows:", len(rows), "->", out)

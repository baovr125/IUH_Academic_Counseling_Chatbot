"""Công cụ chấm tay cho thí nghiệm E2 (Bảng 5.4 và 5.5). Ba lệnh:

  python -B -X utf8 eval/rating_tools.py make     tạo eval/results/rating_r1.csv và rating_r2.csv (mỗi người chấm một tệp, độc lập)
  python -B -X utf8 eval/rating_tools.py merge    sau khi cả hai điền xong: tạo rating_final.csv, liệt kê các câu hai người chấm khác nhau
  python -B -X utf8 eval/rating_tools.py report   đọc rating_final.csv, in Bảng 5.4 và 5.5 và ghi results/answer_eval.json

Câu trả lời của V1 và V2 được gán ngẫu nhiên thành "A" hoặc "B" (hạt giống cố định) để người chấm không biết phương án nào.
Nhãn chất lượng: dung | mot_phan | sai.  Với câu ngoài phạm vi hoặc ngoài kho (nhóm ngoai_pham_vi, ngoai_kho): dung nghĩa là
từ chối hợp lý/không bịa, sai nghĩa là trả lời như thật hoặc bịa.  Cột faithful: 1 nếu mọi khẳng định có trong ngữ cảnh (chỉ chấm cho V2), 0 nếu không.
"""
import csv
import json
import random
import sys
from collections import Counter

from common import DATA, RES, cohen_kappa, fmt_ci, read_jsonl, write_json

LABELS = ("dung", "mot_phan", "sai")
SEED = 20261031


def load(version):
    p = RES / f"answers_{version}.jsonl"
    return {r["id"]: r for r in read_jsonl(p) if "error" not in r} if p.exists() else {}


def make():
    qs = read_jsonl(DATA / "questions.jsonl")
    v1, v2 = load("V1"), load("V2")
    rng = random.Random(SEED)
    mapping, rows = {}, []
    for q in qs:
        if q["id"] not in v1 or q["id"] not in v2:
            continue
        flip = rng.random() < 0.5
        a, b = (("V2", v2), ("V1", v1)) if flip else (("V1", v1), ("V2", v2))
        mapping[q["id"]] = {"A": a[0], "B": b[0]}
        rows.append({"id": q["id"], "group": q["group"], "question": q["question"], "reference": q["reference"],
                     "answer_A": a[1][q["id"]]["answer"], "answer_B": b[1][q["id"]]["answer"],
                     "label_A": "", "faithful_A": "", "label_B": "", "faithful_B": "", "note": ""})
    write_json(RES / "rating_mapping.json", mapping)
    for who in ("r1", "r2"):
        with open(RES / f"rating_{who}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"Đã tạo rating_r1.csv và rating_r2.csv ({len(rows)} câu). Mỗi người điền label_A/B (dung|mot_phan|sai) và faithful_A/B (1|0).")


def read_sheet(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def merge():
    r1, r2 = read_sheet(RES / "rating_r1.csv"), read_sheet(RES / "rating_r2.csv")
    out, diff = [], 0
    for qid in r1:
        row = {"id": qid, "group": r1[qid]["group"], "question": r1[qid]["question"]}
        for s in ("A", "B"):
            l1, l2 = r1[qid][f"label_{s}"].strip(), r2[qid][f"label_{s}"].strip()
            row[f"r1_{s}"], row[f"r2_{s}"] = l1, l2
            row[f"final_{s}"] = l1 if l1 == l2 and l1 else ""
            f1, f2 = r1[qid][f"faithful_{s}"].strip(), r2[qid][f"faithful_{s}"].strip()
            row[f"faithful_{s}"] = f1 if f1 == f2 else ""
            diff += (row[f"final_{s}"] == "")
        out.append(row)
    with open(RES / "rating_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"Đã tạo rating_final.csv. Còn {diff} ô chưa thống nhất: hai người thảo luận rồi điền trực tiếp vào cột final_A/final_B (và faithful_A/B).")


def report():
    mapping = json.loads((RES / "rating_mapping.json").read_text(encoding="utf-8"))
    final = read_sheet(RES / "rating_final.csv")
    v2 = load("V2")
    by_v = {"V1": [], "V2": []}
    pooled1, pooled2 = [], []
    for qid, row in final.items():
        for s in ("A", "B"):
            ver = mapping[qid][s]
            lab = row[f"final_{s}"].strip()
            if lab not in LABELS:
                raise SystemExit(f"{qid} cột final_{s} chưa hợp lệ: '{lab}'")
            by_v[ver].append({"id": qid, "group": row["group"], "label": lab, "faithful": row[f"faithful_{s}"].strip()})
            pooled1.append(row[f"r1_{s}"].strip())
            pooled2.append(row[f"r2_{s}"].strip())
    out = {"kappa_hai_nguoi_cham": round(cohen_kappa(pooled1, pooled2), 3), "n_nhan": len(pooled1)}
    for ver, rows in by_v.items():
        n = len(rows)
        out[ver] = {"n": n, **{lab: fmt_ci(sum(r["label"] == lab for r in rows), n) for lab in LABELS}}
        for scope, groups in (("co_dap_an", {"quy_che", "thu_tuc", "nhieu_y"}), ("ngoai_kho_va_ngoai_pham_vi", {"ngoai_kho", "ngoai_pham_vi"})):
            sub = [r for r in rows if r["group"] in groups]
            out[ver][scope] = {"n": len(sub), **{lab: fmt_ci(sum(r["label"] == lab for r in sub), len(sub)) for lab in LABELS}}
        fa = [r for r in rows if r["faithful"] in ("0", "1")]
        if ver == "V2" and fa:
            out[ver]["trung_thuc"] = fmt_ci(sum(r["faithful"] == "1" for r in fa), len(fa))
    # Bảng 5.5: answer_confidence tự khai của V2 so với nhãn chấm tay
    conf = {}
    for r in by_v["V2"]:
        c = (v2.get(r["id"], {}).get("reflection") or {}).get("answer_confidence", "KHONG_CO")
        conf.setdefault(c, Counter())[r["label"]] += 1
    out["answer_confidence_vs_nhan"] = {c: dict(v) for c, v in conf.items()}
    write_json(RES / "answer_eval.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


{"make": make, "merge": merge, "report": report}[sys.argv[1] if len(sys.argv) > 1 else "make"]()

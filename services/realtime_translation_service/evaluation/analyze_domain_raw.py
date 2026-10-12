"""Phân tích OFFLINE kết quả thô của run_domain_raw.py (không gọi API): áp `decide_domain` và tính chỉ số.

Chỉ số (mục 2.4 của evaluation.md, dùng để định hướng): macro-F1 trong domain, abstain đúng ngoài domain,
sai-mà-tự-tin, ECE, tỷ lệ vi phạm định dạng, độ trễ token đầu, tỷ lệ áp dụng thuật ngữ từ điển.
  python evaluation/analyze_domain_raw.py evaluation/results/domain_raw_dev_*.jsonl [--min-conf 0.75]
"""
import argparse
import json
import math
import os
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.environ.setdefault("REDIS_HOST", "localhost")

from app.services.domain_detection import JointHeader, decide_domain  # noqa: E402

DOMAINS = [
    "Công nghệ Thông tin (IT)", "Y khoa / Sức khỏe", "Kinh tế / Tài chính",
    "Kỹ thuật Cơ khí", "Luật / Pháp lý", "Marketing",
]
UNK = "unknown"


class StoredLex:
    """Giao diện giống LexicalSummary, dựng lại từ dữ liệu đã lưu."""

    def __init__(self, lex):
        self.lex = lex or {}

    def score(self, domain):
        return float(self.lex.get(domain, {}).get("score", 0.0))

    def _rank(self):
        return sorted(((d, v["score"]) for d, v in self.lex.items()), key=lambda x: (-x[1], x[0]))

    @property
    def top_domain(self):
        r = self._rank()
        return r[0][0] if r else None

    @property
    def top_score(self):
        r = self._rank()
        return r[0][1] if r else 0.0


def predict(rec, rule="decide"):
    """Trả (nhãn dự đoán, confidence dùng để tính ECE hoặc None)."""
    if rec.get("skipped") == "exact_dictionary":
        doms = list(dict.fromkeys(rec["exact_domains"]))
        return (doms[0], 1.0) if len(doms) == 1 else ("ambiguous", None)
    if not rec.get("ok"):
        return "error", None
    if rec.get("format_error") or rec.get("header_domain") is None:
        return UNK, None
    header = JointHeader(rec["header_domain"], rec.get("header_conf"))
    if rule == "raw":  # chỉ tin LLM, không dùng lexical/ngưỡng
        for d in DOMAINS:
            if " ".join(d.split()).casefold() == " ".join(header.domain.split()).casefold():
                return d, header.confidence
        return UNK, header.confidence
    dec = decide_domain(header, StoredLex(rec.get("lex")), DOMAINS)
    return (dec.domain if dec.status == "detected" else UNK), header.confidence


def f1_macro(rows, preds):
    f1s = []
    for d in DOMAINS:
        tp = sum(1 for r, p in zip(rows, preds) if r["label"] == d and p == d)
        fp = sum(1 for r, p in zip(rows, preds) if r["label"] != d and p == d)
        fn = sum(1 for r, p in zip(rows, preds) if r["label"] == d and p != d)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def ece(pairs, bins=10):
    """pairs: (confidence, correct). Expected Calibration Error."""
    if not pairs:
        return float("nan")
    total = len(pairs)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        members = [(c, ok) for c, ok in pairs if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if members:
            err += len(members) / total * abs(sum(ok for _, ok in members) / len(members) - sum(c for c, _ in members) / len(members))
    return err


SNAPSHOT = os.path.join(ROOT, "evaluation", "results", "dict_snapshot.json")
DATASETS = {"dev": "domain_dev.jsonl", "val": "domain_val.jsonl", "holdout": "domain_holdout.jsonl"}


def load_sources():
    """id -> văn bản nguồn (bản ghi thô cũ ghi đè khóa `text` bằng bản dịch)."""
    src = {}
    for name in DATASETS.values():
        path = os.path.join(ROOT, "evaluation", "dataset", name)
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                r = json.loads(line)
                src[r["id"]] = r["text"]
    return src


def output_of(rec):
    return rec.get("output") if "output" in rec else rec.get("text", "")


def _tokens(text):
    import re
    return set(re.findall(r"\w+", text.casefold()))


def bad_translation(source, output):
    """Bản dịch hỏng: rỗng, chỉ có dấu `---`, hoặc gần như sao chép nguyên văn nguồn."""
    out = output.strip()
    if out in ("", "---"):
        return True
    a, b = _tokens(source), _tokens(out)
    return bool(a) and len(a & b) / len(a | b) >= 0.85


def term_application(rows, dictionary):
    """Tỉ lệ thuật ngữ từ điển (của domain nhãn, có trong câu) mà bản dịch chứa bản dịch từ điển."""
    trans = {(d["domain"], d["word"].lower()): d["translation"] for d in dictionary}
    hit = total = 0
    for r in rows:
        if r["kind"] != "in_domain" or not r.get("ok") or r.get("skipped"):
            continue
        out = output_of(r).casefold()
        for term in r.get("lex", {}).get(r["label"], {}).get("terms", []):
            options = [o.strip().casefold() for o in trans.get((r["label"], term), "").split("/") if o.strip()]
            if options:
                total += 1
                hit += any(o in out for o in options)
    return (hit / total if total else float("nan")), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min-conf", type=float, default=None)
    ap.add_argument("--rule", default="decide", choices=["decide", "raw"])
    ap.add_argument("--show-errors", action="store_true")
    args = ap.parse_args()
    if args.min_conf is not None:
        os.environ["AUTO_DOMAIN_MIN_CONFIDENCE"] = str(args.min_conf)

    for path in args.files:
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        model = rows[0].get("model", "?")
        if rows[0].get("mode", "auto") != "auto":
            # Đường cơ sở (plain = không domain, manual = chọn đúng domain thủ công): chỉ so thuật ngữ + chất lượng đầu ra.
            sources = load_sources()
            calls = [r for r in rows if r.get("ok") and not r.get("skipped")]
            dictionary = json.load(open(SNAPSHOT, encoding="utf-8")) if os.path.exists(SNAPSHOT) else []
            term_rate, term_n = term_application(rows, dictionary)
            bad = [r["id"] for r in calls if bad_translation(sources.get(r["id"], ""), output_of(r))]
            total = [r["total_s"] for r in calls if r.get("total_s")]
            print(f"\n== {os.path.basename(path)}  model={model}  mode={rows[0]['mode']}")
            print(f"  áp dụng thuật ngữ từ điển: {term_rate:.3f} (n={term_n})   bản dịch hỏng: {len(bad)}/{len(calls)}   "
                  f"lỗi gọi API: {sum(1 for r in rows if not r.get('ok'))}   tổng p50={statistics.median(total):.2f}s")
            continue
        indom = [r for r in rows if r["kind"] == "in_domain"]
        ood = [r for r in rows if r["kind"] == "ood"]
        stray = [r for r in rows if r["kind"] == "stray"]
        short = [r for r in rows if r["kind"] == "short"]
        pred = {r["id"]: predict(r, args.rule) for r in rows}

        p_in = [pred[r["id"]][0] for r in indom]
        acc_in = sum(p == r["label"] for p, r in zip(p_in, indom)) / len(indom)
        f1 = f1_macro(indom, p_in)
        abst_ood = sum(pred[r["id"]][0] == UNK for r in ood) / len(ood)
        abst_stray = sum(pred[r["id"]][0] == UNK for r in stray) / len(stray) if stray else float("nan")
        # sai-mà-tự-tin: dự đoán một domain nhưng sai (kể cả ngoài domain), trên tất cả mẫu không phải short/stray
        judged = indom + ood
        wrong_conf = sum(1 for r in judged if pred[r["id"]][0] not in (UNK, "error", r["label"])) / len(judged)
        pairs = []
        pairs_detected = []  # chỉ các lần LLM CHỌN một domain (bỏ câu trả lời unknown, vốn có conf thấp dù đúng)
        for r in judged:
            p, c = pred[r["id"]]
            if c is not None and p not in ("error", "ambiguous"):
                pairs.append((c, p == r["label"]))
            if c is not None and p not in ("error", "ambiguous", UNK):
                pairs_detected.append((c, p == r["label"]))
        fmt_bad = sum(1 for r in rows if r.get("ok") and not r.get("skipped") and r.get("format_error"))
        calls = [r for r in rows if r.get("ok") and not r.get("skipped")]
        first = [r["first_s"] for r in calls if r.get("first_s")]
        total = [r["total_s"] for r in calls if r.get("total_s")]
        errors = sum(1 for r in rows if not r.get("ok"))
        short_ok = sum(pred[r["id"]][0] == r["label"] or (r["label"] == UNK and pred[r["id"]][0] == UNK) for r in short)

        def p95(a):
            a = sorted(a)
            return a[min(len(a) - 1, math.ceil(0.95 * len(a)) - 1)] if a else float("nan")

        print(f"\n== {os.path.basename(path)}  model={model}  rule={args.rule}  min_conf={os.environ.get('AUTO_DOMAIN_MIN_CONFIDENCE', 'mặc định 0.75')}")
        print(f"  in-domain: n={len(indom)} accuracy={acc_in:.3f} macro-F1={f1:.3f}")
        print(f"  abstain đúng ngoài domain: {abst_ood:.3f} (n={len(ood)})   stray-term abstain: {abst_stray:.3f} (n={len(stray)})")
        print(f"  sai-mà-tự-tin (đoán domain sai/ngoài domain): {wrong_conf:.3f}   ECE(conf LLM, mọi câu trả lời): {ece(pairs):.3f} (n={len(pairs)}); ECE chỉ trên domain được chọn: {ece(pairs_detected):.3f} (n={len(pairs_detected)})")
        print(f"  short: đúng {short_ok}/{len(short)}   lỗi gọi API: {errors}   vi phạm định dạng: {fmt_bad}/{len(calls)}")
        sources = load_sources()
        bad = [r["id"] for r in calls if bad_translation(sources.get(r["id"], ""), output_of(r))]
        dictionary = json.load(open(SNAPSHOT, encoding="utf-8")) if os.path.exists(SNAPSHOT) else []
        term_rate, term_n = term_application(rows, dictionary)
        print(f"  bản dịch hỏng (rỗng/'---'/sao chép nguồn): {len(bad)}/{len(calls)} {bad[:8]}   áp dụng thuật ngữ từ điển: {term_rate:.3f} (n={term_n})")
        print(f"  độ trễ token đầu: p50={statistics.median(first):.2f}s p95={p95(first):.2f}s | tổng: p50={statistics.median(total):.2f}s p95={p95(total):.2f}s")
        confs = sorted(c for c, _ in pairs)
        if confs:
            print(f"  confidence LLM: min={confs[0]:.2f} p50={statistics.median(confs):.2f} số mẫu conf>=0.95: {sum(c >= 0.95 for c in confs)}/{len(confs)}")
        if args.show_errors:
            for r in rows:
                p, c = pred[r["id"]]
                if r["kind"] in ("in_domain", "ood", "stray") and p != (r["label"] if r["label"] != UNK else UNK):
                    print(f"   - {r['id']} [{r['kind']}] nhãn={r['label'][:14]} đoán={str(p)[:14]} conf={c} :: {r['text'][:90]}")


if __name__ == "__main__":
    main()

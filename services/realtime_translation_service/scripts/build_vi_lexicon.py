# -*- coding: utf-8 -*-
"""Sinh từ vựng âm tiết tiếng Việt KHÔNG DẤU phục vụ Language Detection.

Nguồn tần suất: vocab.txt của mô hình tiếng Việt PhoBERT có sẵn trong repo
(hf_models/vietnamese-bi-encoder-onnx/vocab.txt, dạng "<từ_ghép> <tần suất corpus>").
Quy trình: tách âm tiết → bỏ dấu → cộng tần suất → giữ top-N → loại âm tiết trùng với từ phổ biến
của ngôn ngữ khác (kiểm tra bằng fastText/Lingua) → ghi app/resources/vi_toneless_syllables.txt.

Chạy:  python scripts/build_vi_lexicon.py [--top 2500]
"""
import argparse
import logging
import os
import re
import sys
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TESTING", "1")
logging.disable(logging.CRITICAL)

DEFAULT_VOCAB = os.path.join(ROOT, "..", "..", "hf_models", "vietnamese-bi-encoder-onnx", "vocab.txt")
OUTPUT = os.path.join(ROOT, "app", "resources", "vi_toneless_syllables.txt")

INITIAL = r"(?:ngh|ng|gh|gi|kh|nh|ph|th|tr|ch|qu|[bcdghklmnpqrstvx])?"
SYLLABLE_RE = re.compile(rf"^{INITIAL}[aeiouy]{{1,3}}(?:c|ch|m|n|ng|nh|p|t)?$")
# Từ rất đặc trưng tiếng Việt luôn giữ lại dù bị bộ lọc nhầm.
ALWAYS_KEEP = {
    "khong", "duoc", "nhung", "nguoi", "truong", "hoc", "giup", "kiem", "thay", "giao", "viet", "dang",
    "nhu", "nao", "cung", "voi", "cua", "cac", "ngay", "thang", "tinh", "trinh", "toi", "minh", "chung",
    "nhieu", "xin", "chao", "sinh", "vien", "truoc", "biet", "hieu", "nhat", "thoi", "gian", "phong",
}


def strip_marks(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def load_syllable_counts(vocab_path: str) -> Counter:
    """Đếm tần suất theo âm tiết không dấu; chỉ giữ âm tiết từng xuất hiện với dấu tiếng Việt
    (loại tên riêng/từ nước ngoài lẫn trong vocab như "boeing", "bean")."""
    counts: Counter = Counter()
    marked: set = set()
    with open(vocab_path, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").rsplit(" ", 1)
            if len(parts) != 2 or not parts[1].isdigit():
                continue
            token, freq = parts[0], int(parts[1])
            for syllable in token.split("_"):
                if not syllable or not syllable.isalpha():
                    continue
                plain = strip_marks(syllable)
                if not SYLLABLE_RE.match(plain):
                    continue
                counts[plain] += freq
                if syllable.lower() != plain:
                    marked.add(plain)
    return Counter({syllable: count for syllable, count in counts.items() if syllable in marked})


# Từ chức năng/rất phổ biến của ngôn ngữ khác trùng với âm tiết tiếng Việt: không dùng làm bằng chứng.
FOREIGN_STOP = set("""
a an as at be by do go he if in is it me my no of on or so to up us we the and for are but not you all any
can her was one our out day get has him his how man new now old see two way who did its let put say she too
use der die das dem den des les las los una uno por con per del da de di du la le el en un es se si su te tu
va ve vi vo mot moi noi nos non mas mal pas par sur ces ses mes tes son sa ma ta mi ti lo ni na ne ou oui ja
ok hai mat men tin ban bin pan tan sin sun sat set sit pin ten den tem dan gen hen kin lam lim
""".split())
MAJOR_FOREIGN = {"en", "fr", "es", "de", "it", "pt", "nl", "id", "sv", "da", "no", "nb", "fi", "pl", "tr", "ro"}


def foreign_word(token: str) -> bool:
    """True nếu âm tiết trùng một từ phổ biến của ngôn ngữ khác (danh sách + fastText độ tin cậy cao)."""
    if token in FOREIGN_STOP:
        return True
    from app.services.fasttext_detector import fasttext_topk
    top = fasttext_topk(token, k=1)
    return bool(top and top[0][0] in MAJOR_FOREIGN and top[0][1] >= 0.9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vocab", default=DEFAULT_VOCAB)
    parser.add_argument("--top", type=int, default=2500)
    args = parser.parse_args()

    counts = load_syllable_counts(args.vocab)
    ranked = [syllable for syllable, _ in counts.most_common(args.top)]
    kept, dropped = [], []
    for syllable in ranked:
        if syllable in ALWAYS_KEEP:
            kept.append(syllable)
        elif len(syllable) <= 1 or foreign_word(syllable):
            dropped.append(syllable)
        else:
            kept.append(syllable)
    kept = sorted(set(kept) | ALWAYS_KEEP)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept) + "\n")
    print(f"Giữ {len(kept)} âm tiết, loại {len(dropped)} âm tiết trùng ngôn ngữ khác -> {os.path.normpath(OUTPUT)}")
    print("Ví dụ bị loại:", " ".join(dropped[:60]))


if __name__ == "__main__":
    main()

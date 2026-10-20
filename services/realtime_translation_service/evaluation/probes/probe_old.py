import os, sys, time, json
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
os.environ["FASTTEXT_LID_MODEL"] = str(__import__("pathlib").Path(__file__).resolve().parents[2].parent / "models" / "lid.176.ftz")
os.environ["TESTING"] = "1"
from app.services.translation_service import detect_language_detailed
from app.services.fasttext_detector import fasttext_detect

samples = [
    "Trí tuệ nhân tạo đang thay đổi giáo dục",
    "toi dang hoc lap trinh tai truong dai hoc",
    "xin chao",
    "Hello",
    "merci",
    "Je suis ici",
    "Ich bin da",
    "La inteligenza artificiale sta cambiando il mondo",   # Italian (OOS)
    "A inteligência artificial está mudando a educação",    # Portuguese (OOS)
    "Kecerdasan buatan sedang mengubah pendidikan",          # Indonesian (OOS)
    "الذكاء الاصطناعي يغير التعليم",                          # Arabic (OOS)
    "人工智能正在改变教育",
    "人工智能",
    "ありがとう",
    "ปัญญาประดิษฐ์",
    "the die is cast",
    "my son is here",
    "Hôm nay tôi có meeting với team về deadline",
    "lol that exam was so hard idk how i passed tbh",
]
for s in samples:
    t0 = time.perf_counter()
    d = detect_language_detailed(s)
    ms = (time.perf_counter() - t0) * 1000
    ft = fasttext_detect(s)
    print(f"{s[:45]!r:50} -> {d.status:10} {str(d.resolved_source_lang):5} conf={d.confidence:.2f} eng={d.engine:8} ft={ft[0]} {ft[1]:.2f}  {ms:.1f}ms")

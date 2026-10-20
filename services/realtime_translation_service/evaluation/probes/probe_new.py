import os, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
os.environ["FASTTEXT_LID_MODEL"] = str(__import__("pathlib").Path(__file__).resolve().parents[2].parent / "models" / "lid.176.ftz")
os.environ["TESTING"] = "1"
import logging
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld

t0 = time.perf_counter()
print("warm_up:", ld.warm_up(), f"{(time.perf_counter()-t0)*1000:.0f}ms")

samples = [
    "Trí tuệ nhân tạo đang thay đổi giáo dục",
    "toi dang hoc lap trinh tai truong dai hoc",
    "sinh vien can nop bai tap truoc ky thi",
    "xin chao",
    "Hello",
    "merci",
    "Je suis ici",
    "Ich bin da",
    "La inteligenza artificiale sta cambiando il mondo",
    "A inteligência artificial está mudando a educação",
    "Kecerdasan buatan sedang mengubah pendidikan",
    "الذكاء الاصطناعي يغير التعليم",
    "人工智能正在改变教育",
    "人工智能",
    "ありがとう",
    "ปัญญาประดิษฐ์",
    "the die is cast",
    "my son is here",
    "Hôm nay tôi có meeting với team về deadline",
    "lol that exam was so hard idk how i passed tbh",
    "Machine learning is transforming healthcare",
    "https://openai.com/research/gpt4",
    "12345",
    "<b>Machine learning is great</b>",
    "Hello こんにちは",
    "Машинное обучение трансформирует здравоохранение",
    "Штучний інтелект змінює освіту",
    "기계 학습은 의료를 변화시키고 있다",
]
for s in samples:
    t0 = time.perf_counter()
    d = ld.detect_language_detailed(s)
    ms = (time.perf_counter() - t0) * 1000
    cands = ",".join(f"{c.language}:{c.confidence:.2f}" for c in d.candidates)
    print(f"{s[:42]!r:46} -> {d.status:11} {str(d.resolved_source_lang or d.detected_language):5} conf={d.confidence:.2f} eng={d.engine:8} reason={d.reason} [{cands}] {ms:.1f}ms")

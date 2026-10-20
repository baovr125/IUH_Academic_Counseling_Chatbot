import os, sys, logging
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.environ["TESTING"] = "1"
logging.disable(logging.CRITICAL)
from app.services import language_detection as ld
ld.warm_up()
groups = {
    "VI chính + vài từ EN": [
        "Hôm nay tôi có meeting với team về deadline quan trọng",
        "Bạn đã review pull request chưa, tôi cần merge trước deadline",
        "Mình đang học machine learning và deep learning ở trường",
        "Em cần submit assignment trước 11pm được không ạ",
        "Anh gửi giúp em file báo cáo qua email nhé",
    ],
    "VI chính, EN nhiều hơn (~40%)": [
        "Tôi vừa deploy xong application lên server và fix bug trong database",
        "Cần optimize query và cache để giảm latency của API",
    ],
    "VI không dấu + EN": [
        "toi dang hoc machine learning o truong dai hoc",
        "ban co the review code giup toi khong",
    ],
    "EN chính + vài từ VI": [
        "I really love phở and bánh mì when I travel to Vietnam",
        "My friend said xin chào to everyone at the meeting",
    ],
    "Ngắn / gần 50-50": [
        "Hôm nay meeting",
        "Tôi thích coffee",
        "OK bạn ơi",
        "deadline là thứ Sáu",
    ],
    "VI + ngôn ngữ khác": [
        "Tôi đang học tiếng Nhật, câu こんにちは nghĩa là xin chào",
        "Từ \"bonjour\" trong tiếng Pháp có nghĩa là xin chào",
    ],
}
for name, texts in groups.items():
    print(f"\n## {name}")
    for t in texts:
        d = ld.detect_language_detailed(t)
        cands = ",".join(f"{c.language}:{c.confidence:.2f}" for c in d.candidates)
        print(f"  {d.status:9} {str(d.resolved_source_lang):4} conf={d.confidence:.2f} multi={d.is_multilingual!s:5} reason={d.reason} [{cands}] :: {t[:62]}")

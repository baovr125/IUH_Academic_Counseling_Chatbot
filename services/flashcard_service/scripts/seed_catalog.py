"""Nạp thư viện bộ từ vựng hệ thống (chủ đề đời sống hằng ngày) bằng chính pipeline AI của dịch vụ.

Chạy từ thư mục services/flashcard_service (cần đã chạy db/migrations/004_flashcard_catalog.sql):

    python -m scripts.seed_catalog --list                    # xem danh sách bộ sẽ nạp
    python -m scripts.seed_catalog                           # nạp các bộ chưa có (idempotent theo slug)
    python -m scripts.seed_catalog --only family,food-drink  # chỉ một số bộ
    python -m scripts.seed_catalog --replace --only family   # sinh lại và thay thế nội dung một bộ đã có
    python -m scripts.seed_catalog --draft                   # nạp ở trạng thái nháp (sinh viên chưa thấy)
    python -m scripts.seed_catalog --publish                 # xuất bản mọi bộ đang ở trạng thái nháp

Đọc khóa từ biến môi trường hoặc file .env ở thư mục gốc dự án (GROQ_API_KEY, GEMINI_API_KEY, SUPABASE_URL,
SUPABASE_SERVICE_ROLE_KEY). Nội dung do AI tạo và KHÔNG có biên tập viên duyệt (quyết định của chủ dự án);
mô tả bộ từ ghi rõ điều này. Script không dùng hạn mức theo người dùng.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AI_NOTE = "Nội dung do AI tạo, chưa có biên tập viên duyệt."
MIN_CARDS = 20
RETRY_WAIT_SECONDS = 65  # đủ để cooldown 429 của provider hết hạn

# category: communication | food | going_out | home_health (nhãn tiếng Việt nằm ở frontend CatalogView)
CATALOG: List[Dict[str, Any]] = [
    {"slug": "introduce-yourself", "title": "Giới thiệu bản thân", "category": "communication", "level": "A1", "count": 30,
     "topic": "Introducing yourself: greetings, name, age, nationality, job, school and personal information",
     "description": "Chào hỏi và nói về bản thân: tên, tuổi, quê quán, nghề nghiệp, học tập."},
    {"slug": "family-relationships", "title": "Gia đình và các mối quan hệ", "category": "communication", "level": "A1", "count": 30,
     "topic": "Family members and relationships: parents, siblings, relatives, friends, neighbours",
     "description": "Các thành viên trong gia đình, họ hàng, bạn bè và hàng xóm."},
    {"slug": "daily-routine", "title": "Thói quen hằng ngày", "category": "communication", "level": "A1", "count": 30,
     "topic": "Daily routine: everyday activities from morning to night, time and frequency",
     "description": "Các hoạt động từ sáng đến tối, nói về thời gian và tần suất."},
    {"slug": "food-and-drink", "title": "Đồ ăn và thức uống", "category": "food", "level": "A1", "count": 30,
     "topic": "Food and drink: common meals, fruit, vegetables, meat, drinks, tastes",
     "description": "Món ăn, trái cây, rau củ, thịt cá, đồ uống và các vị."},
    {"slug": "eating-out", "title": "Đi ăn nhà hàng và gọi món", "category": "food", "level": "A2", "count": 30,
     "topic": "Eating out: restaurant, menu, ordering food, asking for the bill, complaints and compliments",
     "description": "Gọi món, hỏi thực đơn, thanh toán và những câu thường gặp ở nhà hàng, quán cà phê."},
    {"slug": "cooking-at-home", "title": "Nấu ăn tại nhà", "category": "food", "level": "A2", "count": 30,
     "topic": "Cooking at home: kitchen tools, ingredients, cooking verbs, recipes",
     "description": "Dụng cụ nhà bếp, nguyên liệu và các động từ nấu nướng."},
    {"slug": "shopping", "title": "Mua sắm", "category": "going_out", "level": "A2", "count": 30,
     "topic": "Shopping: shops, clothes, sizes, prices, bargaining, paying",
     "description": "Cửa hàng, quần áo, kích cỡ, giá cả, mặc cả và thanh toán."},
    {"slug": "transport-and-directions", "title": "Đi lại và hỏi đường", "category": "going_out", "level": "A2", "count": 30,
     "topic": "Transport and directions: public transport, driving, tickets, asking for and giving directions",
     "description": "Phương tiện giao thông, mua vé, hỏi đường và chỉ đường."},
    {"slug": "hobbies-and-weekend", "title": "Sở thích và đi chơi cuối tuần", "category": "going_out", "level": "A2", "count": 30,
     "topic": "Hobbies and weekend activities: sports, music, films, going out with friends, invitations",
     "description": "Sở thích, thể thao, phim ảnh, rủ bạn đi chơi và lên kế hoạch cuối tuần."},
    {"slug": "weather-and-seasons", "title": "Thời tiết và các mùa", "category": "going_out", "level": "A1", "count": 25,
     "topic": "Weather and seasons: weather conditions, temperature, seasons, clothes for the weather",
     "description": "Mô tả thời tiết, nhiệt độ, bốn mùa và trang phục phù hợp."},
    {"slug": "travel-and-hotels", "title": "Du lịch và đặt phòng", "category": "going_out", "level": "B1", "count": 30,
     "topic": "Travel and hotels: booking, airport, luggage, accommodation, sightseeing, travel problems",
     "description": "Đặt vé, đặt phòng, sân bay, hành lý, tham quan và xử lý sự cố khi đi du lịch."},
    {"slug": "home-and-furniture", "title": "Nhà cửa và đồ dùng", "category": "home_health", "level": "A1", "count": 30,
     "topic": "Home and furniture: rooms, furniture, household items, chores",
     "description": "Các phòng, đồ nội thất, đồ dùng trong nhà và việc nhà."},
    {"slug": "health-and-doctor", "title": "Sức khỏe và đi khám bệnh", "category": "home_health", "level": "A2", "count": 30,
     "topic": "Health and the doctor: body parts, common illnesses, symptoms, medicine, visiting the doctor",
     "description": "Bộ phận cơ thể, bệnh thường gặp, triệu chứng, thuốc và đi khám."},
]


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


async def generate_cards(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    from app.schemas.vocabulary import GenerateVocabRequest
    from app.services.vocab_pipeline import VocabError, generate_vocabulary

    req = GenerateVocabRequest(mode="topic", topic=entry["topic"], level=entry["level"], count=entry["count"], purpose="general")
    last_error = ""
    for attempt in range(1, 4):
        try:
            data = await generate_vocabulary(req)
            break
        except VocabError as exc:
            last_error = f"{exc.code}: {exc.message}"
            print(f"    lần {attempt} lỗi ({last_error})" + ("; chờ rồi thử lại..." if attempt < 3 else ""))
            if attempt < 3:
                await asyncio.sleep(RETRY_WAIT_SECONDS)
    else:
        raise RuntimeError(f"Không sinh được bộ '{entry['slug']}': {last_error}")

    print(f"    {data['returned']}/{data['requested']} từ, {data['latency_ms']} ms, {data['providers']}")
    return [
        {
            "term": it["term"], "definition": it["definition"], "part_of_speech": it["part_of_speech"],
            "phonetic": it["ipa"], "example": it["example"], "example_translation": it["example_translation"],
            "level": entry["level"], "source": "ai_topic",
        }
        for it in data["items"]
    ]


async def publish_drafts() -> None:
    from app.services.flashcard_service import get_supabase
    from starlette.concurrency import run_in_threadpool

    supabase = get_supabase()
    res = await run_in_threadpool(
        lambda: supabase.table("flashcard_decks").update({"status": "published"}).eq("is_system", True).eq("status", "draft").execute()
    )
    print(f"Đã xuất bản {len(res.data or [])} bộ từ.")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="chỉ liệt kê, không gọi AI hay ghi DB")
    parser.add_argument("--only", help="danh sách slug, phân tách bằng dấu phẩy")
    parser.add_argument("--replace", action="store_true", help="sinh lại và thay nội dung bộ đã có")
    parser.add_argument("--draft", action="store_true", help="nạp ở trạng thái nháp")
    parser.add_argument("--publish", action="store_true", help="xuất bản mọi bộ đang ở trạng thái nháp rồi thoát")
    args = parser.parse_args()

    entries = CATALOG
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        unknown = wanted - {e["slug"] for e in CATALOG}
        if unknown:
            print(f"Slug không tồn tại: {', '.join(sorted(unknown))}")
            return 2
        entries = [e for e in CATALOG if e["slug"] in wanted]

    if args.list:
        for e in entries:
            print(f"{e['slug']:<26} {e['category']:<14} {e['level']:<3} {e['count']:>3} từ  {e['title']}")
        return 0

    load_env_file(ROOT.parent.parent / ".env")
    load_env_file(ROOT / ".env")
    for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if not os.getenv(name):
            print(f"Thiếu biến môi trường {name}.")
            return 2

    if args.publish:
        await publish_drafts()
        return 0

    from app.services.catalog_service import system_deck_exists, upsert_system_deck

    status = "draft" if args.draft else "published"
    created = skipped = failed = 0
    for e in entries:
        print(f"- {e['slug']} ({e['level']}, {e['count']} từ)")
        try:
            # Kiểm tra trước để không tốn lượt gọi AI cho bộ đã có.
            if not args.replace and await system_deck_exists(e["slug"]):
                print("    đã có, bỏ qua (dùng --replace để sinh lại)")
                skipped += 1
                continue
            cards = await generate_cards(e)
            if len(cards) < MIN_CARDS:
                print(f"    chỉ có {len(cards)} thẻ (< {MIN_CARDS}), giữ ở trạng thái nháp để kiểm tra")
                status_for_deck = "draft"
            else:
                status_for_deck = status
            result = await upsert_system_deck(
                e["slug"], e["title"], f"{e['description']} {AI_NOTE}", e["category"], e["level"], cards,
                status=status_for_deck, replace=args.replace,
            )
            print(f"    đã lưu {result['inserted']} thẻ, trạng thái {status_for_deck}")
            created += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"    LỖI: {exc}")
    print(f"\nXong: tạo/thay {created}, bỏ qua {skipped}, lỗi {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

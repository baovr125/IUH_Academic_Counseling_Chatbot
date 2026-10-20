# Kiểm chứng end-to-end cho Flashcard / Dashboard

Các script này kiểm chứng hệ thống đang chạy thật (docker compose), bổ sung cho test đơn vị
(`services/flashcard_service/tests`, `frontend/tests`). Chạy từ thư mục gốc dự án.

## Yêu cầu
* `docker compose up -d` (frontend :5173, Kong :8000, flashcard-service). Sau khi sửa code: `docker compose build <service>` rồi `docker compose up -d <service>`.
* `.env` ở thư mục gốc có `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `JWT_SECRET_KEY` (script chỉ đọc, **không in** giá trị).
* Python có `httpx`, `python-jose`, `supabase`; riêng `ui/` cần thêm `playwright` và Google Chrome.

## `api/` — qua Kong + Supabase thật
Mỗi script tự tạo dữ liệu thử có tiền tố riêng, dọn trong `finally` rồi đếm lại để chắc không sót.

| Script | Kiểm chứng | Ghi chú |
|---|---|---|
| `e2e_dashboard.py` | `mastered` (`/languages`), `today_cards` (`/stats/streak`), cô lập giữa người dùng | Tạo **người dùng thử riêng** (xóa kéo theo mọi dữ liệu), không đụng dữ liệu người dùng thật |
| `e2e_games.py [pre\|post]` | Trò chơi, điểm/XP do máy chủ tính | Dùng người dùng đầu tiên trong bảng `users`, sổ thử `E2E-GAME-*` |
| `e2e_languages.py` | 10 bộ sưu tập ngôn ngữ, lưu từ Realtime Translation | |
| `e2e_vocab_langs.py` | AI sinh từ 9 ngôn ngữ | Tốn đúng **1 lượt AI thật** |
| `e2e_kong.py` | Kiểm tra cổng Kong + JWT | |

```
python -X utf8 scripts/e2e_flashcard/api/e2e_dashboard.py
```

## `ui/` — chụp ảnh và đo giao diện (Playwright + Chrome)
API Flashcard được **giả** trong trình duyệt (không ghi/đọc dữ liệu Flashcard thật).

```
python -X utf8 scripts/e2e_flashcard/ui/shots_dashboard.py scripts/e2e_flashcard/_output/dashboard shots     # ảnh
python -X utf8 scripts/e2e_flashcard/ui/shots_dashboard.py scripts/e2e_flashcard/_output/contrast  contrast  # tương phản WCAG >= 4,5:1
python -X utf8 scripts/e2e_flashcard/ui/shots_dashboard.py scripts/e2e_flashcard/_output/overflow  overflow  # tràn ngang
python -X utf8 scripts/e2e_flashcard/ui/contrast_report.py scripts/e2e_flashcard/_output/contrast/contrast.jsonl
```
* `shots_dashboard.py`: Dashboard của 2 vai trò (student, public) × 6 trạng thái Flashcard × 3 cỡ (390/768/1280 px) × sáng/tối. Tạo 2 người dùng thử rồi xóa trong `finally`. `ONLY=public:mobile:dark` để chụp một cấu hình.
* `shots.py <thư_mục_ra>`: các màn hình của chính trang Flashcard (`ONLY=desktop:light`, `PAGE=01`, `CONTRAST=1`, `OVERFLOW=1`, `FULL=1`).
* `ui_checks.py`: JavaScript đo tương phản/tràn ngang dùng chung. **Không có file `.jsonl` nghĩa là 0 vi phạm.**

Ảnh và kết quả đo ghi vào `_output/` (đã `.gitignore`, có thể xóa bất cứ lúc nào).

## Lưu ý đã gặp
* Heredoc của Bash hay lỗi với ký tự đặc biệt: ghi script bằng công cụ soạn file.
* Chạy script có in tiếng Việt trên Windows: thêm `-X utf8` (hoặc `PYTHONIOENCODING=utf-8`).
* Nếu sửa `ui_checks.py`, nhớ rằng JS chứa regex có dấu `\`: dùng chuỗi thô `r'''...'''`, đừng đọc bằng regex rồi dùng nguyên văn (từng khiến bộ đo báo 0 vi phạm giả).

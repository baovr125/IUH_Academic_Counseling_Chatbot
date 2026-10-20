# theme_audit – đo tương phản Dark/Light Mode

Đo tương phản chữ (WCAG 2.x: ≥ 4,5:1, chữ lớn ≥ 3:1) bằng Chrome thật, **dữ liệu giả** (mọi `/api/**` được mock trong
trình duyệt; token là JWT không chữ ký tự tạo) nên không cần đăng nhập, không cần Supabase, không ghi dữ liệu thật.

## Chạy

Cần dev server của frontend (`npm run dev`, cổng 5173) hoặc `npx vite --port 5180`. **Đừng đo container Docker ở :5173
nếu chưa build lại image** – đó là bản build cũ.

```bash
pip install playwright            # đã dùng channel="chrome", cần Chrome cài sẵn
python -I -X utf8 tests/e2e/theme_audit/theme_audit.py --base http://localhost:5180 --out out_dir
# tùy chọn: --suite flashcard|system|all   --themes light dark   --viewports desktop mobile
```

Mã thoát `1` nếu còn `fail`. Kết quả chi tiết ở `out_dir/contrast.jsonl`.

## Đọc kết quả

- **fail**: tương phản tại nền đặc, hoặc tại *tâm* của gradient, dưới ngưỡng → phải sửa.
- **warn**: chỉ phần đầu/cuối dải gradient dưới ngưỡng (chữ thường nằm ở giữa, nên nhẹ hơn) → xem xét.
- Cột `⟵ nền:` cho biết lớp nền của phần tử tổ tiên gần nhất, để tìm ra tệp cần sửa.

## Phủ những gì

- `--suite flashcard`: các màn Flashcard + modal + **ma trận trạng thái** của 4 trò chơi (Ghép cặp: chọn/sai/đã ghép/kết quả;
  Đua 60 giây: Thư giãn + Thử thách, đáp án sai, combo ≥ 3, mất mạng; Xếp chữ: ô đã đặt/đã dùng/gợi ý; Bắn bóng: ban đầu,
  ngắm hỗ trợ, bắn, tạm dừng). Kịch bản nào hỏng sẽ in `[bỏ qua] ...` chứ không làm dừng cả lượt.
- `--suite system`: Dashboard, Translation, DocumentTranslation, Chat, Settings, Profile (dữ liệu giả rỗng nên chỉ là mốc tham
  khảo; các màn này chưa có dark mode – kế hoạch Đợt 3 trong `bao_cao_phan_tich_dark_mode.md`).

## Giới hạn

Chưa đo: tương phản đường viền/biểu tượng, Safari/Firefox, trạng thái hover/focus (chỉ trạng thái tĩnh), bóng Bắn bóng ở
mọi vị trí của gradient (chỉ điểm dừng + điểm giữa), trình đọc màn hình.

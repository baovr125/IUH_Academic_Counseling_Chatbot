"""Sinh MESSAGES_REVIEW.md: liệt kê mọi cảnh báo/thông báo của realtime service (backend + frontend)."""
import sys

OUT = sys.argv[1]
D = "app/services/domain_translation.py"
L = "app/services/language_detection.py"

SECTIONS = [
    ("A. Cảnh báo chế độ chuyên ngành còn hiển thị (sau giai đoạn 9b; mỗi lượt dịch nhiều nhất 1 banner)", [
        ("DOMAIN_AMBIGUOUS", "warning", f"{D} (MSG_AMBIGUOUS)",
         "Chỉ ở auto, Anh→Việt, không có thẻ HTML, ≤ 4 từ, khớp chính xác từ điển của ≥ 2 lĩnh vực. UI hiện khung chọn lĩnh vực trong vùng bản dịch (không phải banner). Với từ điển hiện tại (không có từ trùng lĩnh vực) chưa xảy ra.",
         "Từ này có nghĩa ở nhiều lĩnh vực. Hãy chọn một lĩnh vực."),
        ("FALLBACK_NLLB", "warning", f"{D} (MSG_FALLBACK)",
         "Cả auto và thủ công, khi Groq lẫn Gemini không cho ra chữ nào (quota, quá chậm, sai model, thiếu key, trả rỗng, bản dịch hỏng/sao chép) và NLLB dịch thay. Lý do kỹ thuật chỉ ghi log.",
         "Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường."),
        ("TRANSLATION_INTERRUPTED", "warning", f"{D} (MSG_INTERRUPTED)",
         "Cả hai chế độ, khi stream LLM đứt giữa chừng SAU KHI đã có chữ; giữ phần đã dịch, không cache. Đứt trước khi có chữ thì chuyển NLLB (FALLBACK_NLLB).",
         "Bản dịch bị ngắt giữa chừng, có thể chưa đầy đủ. Nhấn Ctrl+Enter để dịch lại."),
    ]),
    ("B. Kết quả nhận diện lĩnh vực (auto) — hiện như nhãn ngôn ngữ, không phải cảnh báo", [
        ("(nhãn ô chọn)", "-", "frontend DomainSelector.tsx (prop detectedDomain)",
         "auto nhận diện được lĩnh vực; giữ nhãn cũ tới khi có kết quả mới.", "✨ Tự động nhận diện ({lĩnh vực})"),
        ("(nhãn ô chọn)", "-", "frontend DomainSelector.tsx",
         "auto không xác định được (mọi lý do, kể cả lỗi định dạng); lý do nằm ở domain.reason.", "✨ Tự động nhận diện"),
    ]),
    ("C. Mã đã ngừng hiển thị (giai đoạn 9b; logic từ điển/glossary không đổi)", [
        ("DOMAIN_UNKNOWN", "-", "-", "Thay bằng nhãn ở mục B.", "(không hiển thị)"),
        ("DOMAIN_FORMAT_ERROR", "-", "-", "Thay bằng nhãn ở mục B; domain.reason = format_error.", "(không hiển thị)"),
        ("DOMAIN_SERVICE_ERROR", "-", "-", "Hợp nhất vào FALLBACK_NLLB; lý do chỉ ghi log.", "(không hiển thị)"),
        ("GLOSSARY_UNAVAILABLE", "-", "-", "Không ảnh hưởng bản dịch.", "(không hiển thị)"),
        ("GLOSSARY_NO_MATCH", "-", "-", "Không ảnh hưởng bản dịch; dễ gây hiểu nhầm.", "(không hiển thị)"),
        ("TERM_NOT_IN_DICT", "-", "-", "Thiếu trong từ điển không có nghĩa là dịch sai.", "(không hiển thị)"),
        ("TERM_IN_OTHER_DOMAIN", "-", "-", "Thông tin phụ.", "(không hiển thị)"),
    ]),
    ("D. Lỗi dịch (event `error` của /stream, `detail` của /text)", [
        ("TRANSLATION_UNAVAILABLE", "error", f"{D} (MSG_UNAVAILABLE; /text → HTTP 503)",
         "Chế độ domain: LLM hỏng và NLLB cũng hỏng.", "Không thể dịch lúc này. Vui lòng thử lại sau."),
        ("(dịch thông thường /text)", "error", "app/services/translation_service.py:232 (HTTP 503)",
         "Chế độ thường: NLLB, Groq, Gemini đều hỏng.", "Tất cả dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch."),
        ("(dịch thông thường /stream)", "error", "app/services/llm_service.py:291",
         "Chế độ thường: không có API key nào (tiếng Anh).", "No LLM API keys configured."),
        ("(dịch thông thường /stream)", "error", "app/services/llm_service.py:305",
         "Chế độ thường: mọi provider hỏng (tiếng Anh).", "Translation service unavailable."),
    ]),
    ("E. Nhận diện ngôn ngữ (event `error`/`detection.message`, mã LANG_*; đợt trước, chưa đổi)", [
        ("LANG_UNCERTAIN", "error", f"{L}:55", "Chưa chắc ngôn ngữ nguồn.",
         "Chưa đủ thông tin để xác định chắc chắn ngôn ngữ. Hãy chọn ngôn ngữ nguồn thủ công."),
        ("LANG_UNSUPPORTED", "error", f"{L}:557, 748",
         "Nhận ra ngôn ngữ nhưng chưa hỗ trợ.", "Ngôn ngữ nhận diện được ({tên}) chưa được hỗ trợ. Hãy chọn ngôn ngữ nguồn thủ công."),
        ("LANG_UNCERTAIN (ngôn ngữ lạ)", "error", f"{L}:782", "Có thể là ngôn ngữ chưa hỗ trợ.",
         "Văn bản có thể thuộc một ngôn ngữ chưa được hỗ trợ. Hãy chọn ngôn ngữ nguồn thủ công."),
        ("INVALID_INPUT (rỗng)", "error", f"{L}:56", "Văn bản rỗng.", "Vui lòng nhập văn bản để nhận diện ngôn ngữ."),
        ("INVALID_INPUT (không có chữ)", "error", f"{L}:57", "Chỉ có số/ký hiệu.", "Vui lòng nhập văn bản chứa ký tự chữ để nhận diện ngôn ngữ."),
        ("LANG_UNKNOWN (URL)", "error", f"{L}:58", "Văn bản là đường dẫn.", "Văn bản liên kết (URL) không phải ngôn ngữ tự nhiên hợp lệ."),
        ("LANG_SYSTEM_ERROR", "error", f"{L}:59", "Lỗi nội bộ khi nhận diện.", "Không thể nhận diện ngôn ngữ lúc này. Vui lòng thử lại hoặc chọn ngôn ngữ nguồn thủ công."),
        ("/detect", "error", "app/routers/translation.py:178, 180", "Dự phòng khi `details.message` trống.", "Vui lòng nhập văn bản. / Lỗi hệ thống khi nhận diện ngôn ngữ."),
    ]),
    ("F. Giao diện (frontend) — chế độ chuyên ngành", [
        ("Chỉ báo chờ", "-", "components/translation/DomainStatus.tsx", "Trong 1,5 s debounce (domain).",
         "Sẽ dịch sau 1,5 giây ngừng gõ (Ctrl+Enter để dịch ngay)."),
        ("Khung chọn lĩnh vực", "-", "TranslationBox.tsx (domain-candidates)", "Khi ambiguous; lấy câu của DOMAIN_AMBIGUOUS.",
         "Từ này có nghĩa ở nhiều lĩnh vực. Hãy chọn một lĩnh vực."),
    ]),
    ("G. Giao diện (frontend) — chung (nhận diện ngôn ngữ, lỗi, trạng thái trống)", [
        ("Tiêu đề dừng ngôn ngữ", "-", "TranslationBox.tsx:697-702", "Khi service dừng vì ngôn ngữ nguồn.",
         "Ngôn ngữ này chưa được hỗ trợ / Chưa xác định chắc chắn ngôn ngữ nguồn / Không có nội dung ngôn ngữ để nhận diện / Chưa có nội dung để dịch"),
        ("Gợi ý ngôn ngữ", "-", "TranslationBox.tsx:707", "Cạnh các nút ngôn ngữ ứng viên.", "Có phải là:"),
        ("Lỗi dịch chung", "-", "TranslationBox.tsx:291", "Khi backend gửi lỗi không có nội dung.", "Đã xảy ra lỗi trong quá trình dịch thuật."),
        ("Trạng thái trống", "-", "TranslationBox.tsx:685", "Chưa có bản dịch.", "Bản dịch sẽ xuất hiện tại đây..."),
        ("HTTP 429", "-", "services/translationService.ts:117", "Server trả 429.", "Hệ thống đang bận, vui lòng thử lại sau giây lát (429)."),
        ("HTTP lỗi khác", "-", "services/translationService.ts:119", "Server trả lỗi khác (tiếng Anh, lộ mã).", "HTTP error! status: {mã}"),
        ("Mất kết nối", "-", "translationService.ts:71, 186", "fetch thất bại.", "Không thể kết nối đến dịch vụ dịch thuật."),
        ("Nhập văn bản", "-", "translationService.ts:20", "Gửi khi văn bản rỗng.", "Vui lòng nhập văn bản cần dịch."),
        ("Toast sao chép", "-", "TranslationBox.tsx:88, 98", "Nút sao chép.", "Đã sao chép thành công! / Không thể sao chép văn bản."),
        ("Toast lưu thẻ", "-", "TranslationBox.tsx:843", "Lưu flashcard.", "Đã lưu \"{từ}\" vào sổ thẻ \"{bộ}\" thành công! 🎉"),
    ]),
    ("H. Khác (tiếng Anh, dùng cho trang quản trị từ điển — ngoài phạm vi dịch)", [
        ("admin_dictionary", "error", "app/routers/admin_dictionary.py:32-198",
         "Các lỗi của API quản trị từ điển.",
         "Supabase not configured / Entry already exists in this domain. / Entry not found / Unsupported file format. Please upload .csv or .json / No valid entries found in file. Ensure columns/keys are: domain, word, translation."),
    ]),
]

lines = [
    "# Danh sách cảnh báo và thông báo của realtime_translation_service",
    "",
    "Trạng thái sau giai đoạn 9b. Bản liệt kê để rà soát từ ngữ/độ dài. Cột **Số ký tự** là độ dài chuỗi hiện tại (chuỗi có chỗ ghép ghi theo mẫu).",
    "Mức độ (`severity`) quyết định màu banner trên UI: `info` xanh, `warning` vàng, `error` đỏ.",
    "Muốn sửa: chuỗi nằm ở file:dòng của cột **Vị trí**; mã (`code`) giữ nguyên để UI/test không hỏng.",
    "",
]
n = 0
for title, rows in SECTIONS:
    lines += [f"## {title}", "", "| # | Mã / tên | Mức | Vị trí | Khi nào xuất hiện | Nội dung hiện tại | Số ký tự |", "|---|---|---|---|---|---|---|"]
    for code, sev, where, when, text in rows:
        n += 1
        text_md = text.replace("|", "\\|")
        lines.append(f"| {n} | `{code}` | {sev} | `{where}` | {when} | {text_md} | {len(text)} |")
    lines.append("")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("tổng", n, "mục")

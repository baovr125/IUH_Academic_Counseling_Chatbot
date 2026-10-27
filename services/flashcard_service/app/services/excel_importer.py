import io
import re
import csv
import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from starlette.concurrency import run_in_threadpool

from app.services.flashcard_service import (
    get_supabase,
    in_memory_decks,
    in_memory_cards,
    to_valid_uuid,
    db_write_error,
    ensure_deck_for_write,
    resolve_card_language,
    new_card_record,
    to_db_card_payload,
    EXTENDED_CARD_COLUMNS,
)
from app.services.normalization import normalize_pos, dedupe_key
from app.rabbitmq_consumer import publish_flashcard_created_event
from app.utils.logger import logger

# Header aliases for smart column detection across multiple languages
HEADER_ALIASES = {
    "term": [
        # Vietnamese & English
        "term", "từ vựng", "tu vung", "word", "front", "từ gốc", "tu goc", "vocabulary", "từ khóa", "tu khoa", "từ",
        # German
        "wort", "vokabel", "stichwort", "ausdruck",
        # French & Spanish
        "mot", "vocabulaire", "terme", "palabra", "termino", "vocablo",
        # Chinese (Simplified & Traditional)
        "生词", "生詞", "单词", "單詞", "词汇", "詞彙", "词", "詞",
        # Japanese
        "単語", "たんご", "言葉", "ことば", "見出し語",
        # Korean & Russian
        "단어", "어휘", "слово", "термин", "лексема"
    ],
    "definition": [
        # Vietnamese & English
        "definition", "nghĩa", "nghia", "nghĩa tiếng việt", "nghia tieng viet", "meaning", "back", "dịch nghĩa", "dich nghia", "giải nghĩa", "giai nghia", "ý nghĩa", "y nghia",
        # German
        "bedeutung", "übersetzung", "uebersetzung", "erklärung", "erklærung",
        # French & Spanish
        "sens", "signification", "traduction", "définition", "definicion", "significado", "traducción", "traduccion",
        # Chinese
        "意思", "释义", "釋義", "翻译", "翻譯", "解释", "解釋",
        # Japanese
        "意味", "いみ", "訳", "やく", "定義", "日本語訳",
        # Korean & Russian
        "뜻", "의미", "번역", "значение", "перевод", "определение"
    ],
    "phonetic": [
        # Vietnamese & English
        "phonetic", "phiên âm", "phien am", "ipa", "pronunciation", "phát âm", "phat am", "cách đọc", "cach doc",
        # German & French & Spanish
        "aussprache", "lautschrift", "prononciation", "pronunciacion", "pronunciación", "fonética", "fonetica",
        # Asian Pronunciation (Pinyin, Furigana, Romaji, Hangul Romanization)
        "pinyin", "bính âm", "拼音", "注音", "ふりがな", "furigana", "romaji", "ローマ字", "読み方", "よみかた", "발음", "로마자",
        # Russian
        "произношение", "транскрипция", "фонетика"
    ],
    "part_of_speech": [
        # Vietnamese & English
        "part_of_speech", "partofspeech", "từ loại", "tu loai", "type", "pos", "loại từ", "loai tu",
        # German & French & Spanish
        "wortart", "nature", "type_de_mot", "categoria_gramatical", "categoría gramatical", "clase_de_palabra",
        # Asian & Russian
        "词性", "詞性", "品詞", "ひんし", "품사", "часть речи", "категория"
    ],
    "example": [
        # Vietnamese & English
        "example", "ví dụ", "vi du", "example_sentence", "examplesentence", "context", "câu ví dụ", "cau vi du", "ngữ cảnh", "ngu canh", "mẫu câu", "mau cau",
        # German & French & Spanish
        "beispiel", "beispielsatz", "anwendungsbeispiel", "exemple", "phrase_exemple", "ejemplo", "frase_de_ejemplo", "contexto",
        # Asian & Russian
        "例句", "例", "例文", "れいぶん", "예문", "문장", "пример", "контекст", "предложение"
    ]
}

def _clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()

_ALIAS_TO_FIELD = {alias: field for field, aliases in HEADER_ALIASES.items() for alias in aliases}
_HAS_CJK_OR_HANGUL = re.compile(r"[぀-ヿ㐀-鿿가-힯]")


def _match_header(header_name: str) -> Optional[str]:
    """
    Nhận diện cột theo tiêu đề. Thứ tự ưu tiên:
      1. Khớp chính xác phần nhãn trước dấu "(" (vd "Term (Từ vựng ngoại ngữ)*" -> "term") hoặc cả tiêu đề.
      2. Alias dài nhất xuất hiện như một TỪ nguyên vẹn trong tiêu đề (CJK/Hangul không có khoảng trắng nên khớp chuỗi con).
    Không dùng khớp chuỗi con hai chiều: alias ngắn như "từ" từng làm cột "Từ loại" bị nhận nhầm là cột từ vựng.
    """
    cleaned = re.sub(r"\s+", " ", header_name.strip().lower().replace("*", "")).strip()
    if not cleaned:
        return None
    label = cleaned.split("(")[0].strip().rstrip(":")
    for candidate in (label, cleaned):
        if candidate in _ALIAS_TO_FIELD:
            return _ALIAS_TO_FIELD[candidate]

    best: Optional[str] = None
    best_len = 0
    for alias, field in _ALIAS_TO_FIELD.items():
        if len(alias) <= best_len:
            continue
        if _HAS_CJK_OR_HANGUL.search(alias):
            hit = alias in cleaned
        else:
            hit = len(alias) >= 3 and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", cleaned) is not None
        if hit:
            best, best_len = field, len(alias)
    return best

def parse_excel_or_csv(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Phân tích file Excel (.xlsx, .xls) hoặc CSV:
    - Tự động nhận diện header tiếng Anh/tiếng Việt
    - Lọc bỏ dòng trống, trim khoảng trắng
    - Deduplicate các từ vựng trùng nhau trong cùng file
    - Trả về danh sách cards chuẩn hóa
    """
    fname = filename.lower()
    raw_rows: List[List[str]] = []

    if fname.endswith(".csv"):
        # Thử các bộ mã hóa phổ biến
        text_content = ""
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text_content = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text_content:
            raise HTTPException(status_code=400, detail="Không thể đọc nội dung file CSV. Vui lòng lưu file ở định dạng UTF-8.")

        reader = csv.reader(io.StringIO(text_content))
        for row in reader:
            if any(cell.strip() for cell in row):
                raw_rows.append([cell.strip() for cell in row])

    elif fname.endswith((".xlsx", ".xlsm", ".xltx", ".xltm", ".xls")):
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheet = wb.active
            if sheet is None:
                raise HTTPException(status_code=400, detail="File Excel không chứa trang tính (sheet) nào.")

            for row in sheet.iter_rows(values_only=True):
                str_row = [_clean_str(cell) for cell in row]
                if any(str_row):
                    raw_rows.append(str_row)
        except Exception as e:
            logger.error(f"Error parsing Excel file {filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Không thể mở file Excel. Lỗi: {str(e)}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Định dạng file không được hỗ trợ. Vui lòng tải lên file .xlsx, .xls hoặc .csv."
        )

    if not raw_rows:
        raise HTTPException(status_code=400, detail="File tải lên không có dữ liệu.")

    # Xác định Header Mapping
    first_row = raw_rows[0]
    header_mapping: Dict[int, str] = {}
    has_header = False

    for idx, cell in enumerate(first_row):
        matched = _match_header(cell)
        if matched and matched not in header_mapping.values():  # nhiều cột cùng loại: lấy cột đầu tiên
            header_mapping[idx] = matched
            has_header = True

    # Kiểm tra xem có nhận diện được ít nhất 1 cột bắt buộc không
    detected_fields = set(header_mapping.values())
    start_index = 1 if has_header else 0

    if not has_header or "term" not in detected_fields:
        # Fallback sang Positional Mapping mặc định
        header_mapping = {
            0: "term",
            1: "definition",
            2: "phonetic",
            3: "part_of_speech",
            4: "example"
        }
        # Nếu dòng đầu là text header không khớp, bỏ qua dòng đầu
        if any(h in first_row[0].lower() for h in ["term", "từ", "word", "stt"]):
            start_index = 1
        else:
            start_index = 0

    parsed_cards: List[Dict[str, Any]] = []
    seen_terms = set()

    for row_idx in range(start_index, len(raw_rows)):
        row = raw_rows[row_idx]
        card_obj: Dict[str, Any] = {
            "term": "",
            "definition": "",
            "phonetic": "",
            "part_of_speech": "noun",
            "example": ""
        }

        for col_idx, field_name in header_mapping.items():
            if col_idx < len(row):
                val = _clean_str(row[col_idx])
                if val:
                    card_obj[field_name] = val

        term = card_obj.get("term", "").strip()
        definition = card_obj.get("definition", "").strip()

        # Bỏ qua nếu thiếu từ gốc hoặc nghĩa
        if not term or not definition:
            continue

        # Bỏ qua nếu từ gốc là header lặp lại
        if term.lower() in ["term", "từ vựng", "word", "từ gốc"]:
            continue

        # Chuẩn hóa từ loại đa ngôn ngữ (Vietnamese, English, German, French, Spanish, Chinese, Japanese, Korean, Russian)
        pos = card_obj.get("part_of_speech", "").lower()
        canonical_pos = normalize_pos(pos)
        if canonical_pos:
            card_obj["part_of_speech"] = canonical_pos
        elif any(k in pos for k in ["danh", "noun", "nomen", "nom", "sustantivo", "名词", "名詞", "명사", "сущ", "n."]):
            card_obj["part_of_speech"] = "noun"
        elif any(k in pos for k in ["động", "dong", "verb", "verbe", "verbo", "动词", "動詞", "동사", "глагол", "v."]):
            card_obj["part_of_speech"] = "verb"
        elif any(k in pos for k in ["tính", "tinh", "adj", "adjektiv", "adjectif", "adjetivo", "形容", "형용사", "прил", "a."]):
            card_obj["part_of_speech"] = "adjective"
        elif any(k in pos for k in ["cụm", "cum", "phrase", "phr", "phrasen", "locution", "frase", "短语", "句", "숙어", "фраза"]):
            card_obj["part_of_speech"] = "phrase"
        else:
            card_obj["part_of_speech"] = "phrase" if " " in term else "noun"

        # Deduplicate trong cùng file
        term_key = dedupe_key(term)
        if term_key in seen_terms:
            continue
        seen_terms.add(term_key)

        parsed_cards.append(card_obj)

        if len(parsed_cards) >= 2000:
            break

    if not parsed_cards:
        raise HTTPException(
            status_code=400,
            detail="Không tìm thấy thẻ từ vựng hợp lệ nào trong file. Đảm bảo file có ít nhất cột 'Term' (Từ vựng) và 'Definition' (Định nghĩa)."
        )

    return parsed_cards

def generate_excel_template() -> bytes:
    """
    Tạo file Excel mẫu chuẩn (.xlsx) hỗ trợ đa ngôn ngữ có styling và các dòng ví dụ minh họa.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Flashcard_Template"

    # Styling
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Blue-600
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    headers = [
        "Term (Từ vựng ngoại ngữ)*",
        "Definition (Nghĩa tiếng Việt)*",
        "Phonetic (Phiên âm / IPA / Pinyin / Furigana)",
        "PartOfSpeech (Từ loại: noun/verb/adj/phrase)",
        "Example (Câu ví dụ minh họa)"
    ]

    ws.append(headers)

    # Multilingual sample rows (Tiếng Anh, Tiếng Đức, Tiếng Pháp, Tiếng Trung, Tiếng Nhật)
    sample_data = [
        ["Artificial Intelligence", "Trí tuệ nhân tạo", "/ˌɑː.tɪˈfɪʃ.əl ɪnˈtel.ɪ.dʒəns/", "noun", "Artificial Intelligence is transforming modern education."],
        ["die Universität", "Trường đại học", "/univɛʁziˈtɛːt/", "noun", "Ich studiere an der Universität."],
        ["bonjour", "Xin chào / Chúc một ngày tốt lành", "/bɔ̃.ʒuʁ/", "phrase", "Bonjour, comment allez-vous?"],
        ["你好", "Xin chào", "nǐ hǎo", "phrase", "你好！很高兴认识你。"],
        ["勉強する", "Học tập, nghiên cứu", "べんきょうする / benkyousuru", "verb", "毎日日本語を勉強します。"]
    ]

    for row in sample_data:
        ws.append(row)

    # Style Header
    for col_idx, col in enumerate(ws.iter_cols(min_row=1, max_row=1), start=1):
        for cell in col:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

    # Style Data rows
    for row in ws.iter_rows(min_row=2, max_row=len(sample_data) + 1):
        for cell in row:
            cell.font = data_font
            cell.alignment = Alignment(vertical="center")
            cell.border = thin_border

    # Adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 18)

    ws.row_dimensions[1].height = 28

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

async def fetch_existing_terms(supabase, deck_id: str) -> set:
    """Tập từ (đã chuẩn hóa) hiện có trong deck, đọc phân trang để vượt giới hạn 1000 dòng của PostgREST."""
    terms = set()
    valid_deck_uuid = to_valid_uuid(deck_id)
    if supabase and valid_deck_uuid:
        page, offset = 1000, 0
        while True:
            try:
                res = await run_in_threadpool(
                    lambda o=offset: supabase.table("flashcards").select("term")
                        .eq("deck_id", valid_deck_uuid).range(o, o + page - 1).execute()
                )
            except Exception as e:
                raise db_write_error("đọc danh sách từ hiện có để loại trùng", e)
            rows = res.data or []
            for item in rows:
                if item.get("term"):
                    terms.add(dedupe_key(item["term"]))
            if len(rows) < page:
                break
            offset += page
    for c in in_memory_cards.values():
        if str(c.get("deck_id")) == str(deck_id) and c.get("term"):
            terms.add(dedupe_key(c["term"]))
    return terms


def _is_missing_column_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "column" in text and ("does not exist" in text or "schema cache" in text or "could not find" in text)


async def _insert_chunk(supabase, chunk: List[Dict[str, Any]]) -> bool:
    """
    Chèn một lô thẻ. Trả True nếu các cột mở rộng (example_translation, level, source) được lưu.
    Nếu DB chưa chạy migration 003 (thiếu cột) thì chèn lại không kèm các cột đó và trả False.
    """
    payloads = [to_db_card_payload(c, EXTENDED_CARD_COLUMNS) for c in chunk]
    try:
        await run_in_threadpool(lambda: supabase.table("flashcards").insert(payloads).execute())
        return True
    except Exception as e:
        if not _is_missing_column_error(e):
            raise db_write_error("lưu thẻ từ vựng", e)
        logger.warning(
            "Bảng flashcards chưa có cột mở rộng (chạy db/migrations/003_flashcard_ai_generation.sql): "
            f"lưu thẻ mà không kèm example_translation/level/source. Chi tiết: {e}"
        )
    basic = [to_db_card_payload(c) for c in chunk]
    try:
        await run_in_threadpool(lambda: supabase.table("flashcards").insert(basic).execute())
    except Exception as e:
        raise db_write_error("lưu thẻ từ vựng", e)
    return False


async def bulk_insert_cards(
    deck_id: str,
    user_id: str,
    cards_data: List[Dict[str, Any]],
    lang_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thêm hàng loạt thẻ vào deck (Supabase PostgreSQL, hoặc bộ nhớ khi không cấu hình Supabase):
    - Kiểm tra quyền sở hữu deck (IDOR); deck chỉ có ở client sẽ được tạo trên Supabase.
    - Loại trùng với các từ đã có trong deck (so khóa đã chuẩn hóa).
    - Chèn theo lô 200 thẻ; lỗi DB trả 503 (không báo thành công giả). Gọi lại sau lỗi là an toàn
      vì lần sau sẽ tự bỏ qua các thẻ đã được chèn.
    - Bắn event RabbitMQ để sinh âm thanh phát âm ở chế độ nền.
    """
    supabase = get_supabase()
    deck_row = await ensure_deck_for_write(deck_id, user_id, lang_code)
    deck_lang = resolve_card_language(deck_row, lang_code)  # ngôn ngữ theo deck; lệch -> 409; thiếu -> 422 (không đoán 'en')
    deck_title = str((deck_row or {}).get("title") or "Sổ từ vựng")

    if deck_id not in in_memory_decks:
        in_memory_decks[deck_id] = {
            "id": deck_id,
            "user_id": user_id,
            "title": deck_title,
            "description": f"Sổ từ vựng ({deck_lang.upper()})",
            "lang_code": deck_lang,
            "icon_flag": "🌐",
            "cards_count": 0
        }

    existing_terms = await fetch_existing_terms(supabase, deck_id)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cards_to_insert: List[Dict[str, Any]] = []
    skipped_duplicates = 0

    for item in cards_data:
        term = str(item.get("term", "")).strip()
        definition = str(item.get("definition", "")).strip()
        if not term or not definition:
            continue

        key = dedupe_key(term)
        if key in existing_terms:
            skipped_duplicates += 1
            continue
        existing_terms.add(key)

        extra = {k: item.get(k) for k in EXTENDED_CARD_COLUMNS if item.get(k) is not None}
        cards_to_insert.append(new_card_record(
            deck_id=deck_id,
            user_id=user_id,
            term=term,
            definition=definition,
            lang_code=deck_lang,
            phonetic=item.get("phonetic") or None,
            example_sentence=item.get("example") or None,
            part_of_speech=item.get("part_of_speech") or "noun",
            now_iso=now_iso,
            extra=extra
        ))

    if not cards_to_insert:
        return {
            "total_in_file": len(cards_data),
            "inserted": 0,
            "skipped_duplicates": skipped_duplicates,
            "extended_saved": True,
            "cards": []
        }

    CHUNK_SIZE = 200
    extended_saved = True
    if supabase:
        for i in range(0, len(cards_to_insert), CHUNK_SIZE):
            if not await _insert_chunk(supabase, cards_to_insert[i:i + CHUNK_SIZE]):
                extended_saved = False

    for c in cards_to_insert:
        in_memory_cards[c["id"]] = c
    in_memory_decks[deck_id]["cards_count"] = len(
        [c for c in in_memory_cards.values() if str(c.get("deck_id")) == str(deck_id)]
    )

    for c in cards_to_insert:
        try:
            await publish_flashcard_created_event(
                card_id=c["id"],
                term=c["term"],
                lang_code=c["lang_code"],
                user_id=user_id,
                phonetic=c.get("phonetic")
            )
        except Exception as e:
            logger.warning(f"Could not publish event for imported card {c['id']}: {e}")

    logger.info(f"Bulk inserted {len(cards_to_insert)} cards into deck {deck_id} (skipped {skipped_duplicates} duplicates)")

    return {
        "total_in_file": len(cards_data),
        "inserted": len(cards_to_insert),
        "skipped_duplicates": skipped_duplicates,
        "extended_saved": extended_saved,
        "cards": cards_to_insert
    }

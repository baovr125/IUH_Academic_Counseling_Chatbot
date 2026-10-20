import asyncio
import os
import time
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile

from app.schemas.flashcards import ApiResult
from app.schemas.vocabulary import (
    CefrLevel,
    CommitGeneratedRequest,
    VocabLang,
    GenerateVocabRequest,
    MAX_INSTRUCTION_CHARS,
    Purpose,
)
from app.services import vocab_quota
from app.services.excel_importer import bulk_insert_cards, fetch_existing_terms
from app.services.flashcard_service import (
    create_deck,
    delete_deck,
    ensure_deck_readable,
    get_supabase,
)
from app.services.normalization import normalize_pos
from app.services.vocab_languages import LEARNABLE_CODES as LEARNABLE_LANGS, get_lang, strip_article
from app.services.vocab_pipeline import VocabError, generate_vocabulary
from app.utils.errors import ApiError
from app.utils.logger import logger
from app.utils.security import _unauthorized, _user_from_request

router = APIRouter(tags=["AI Vocabulary Generation"])

MAX_IMAGE_BYTES = 5 * 1024 * 1024
IDEMPOTENCY_TTL_SECONDS = 600
SOURCE_BY_MODE = {"topic": "ai_topic", "text": "ai_text", "image": "ai_image"}

# Giới hạn số lần sinh chạy đồng thời để không dồn quota/độ trễ của provider.
_generation_slots = asyncio.Semaphore(int(os.getenv("VOCAB_MAX_CONCURRENT", "4")))
_commit_cache: Dict[Tuple[str, str], Tuple[float, dict]] = {}


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None),
) -> dict:
    """Như get_current_user_id nhưng giữ cả role (để chọn hạn mức theo tier)."""
    user = _user_from_request(authorization, token)
    if not user:
        raise _unauthorized()
    return user


async def _existing_terms_for(deck_id: Optional[str], user_id: str, lang_code: str) -> list:
    """
    Từ đã có trong deck đích (để AI không sinh lại). Kiểm tra quyền truy cập deck và ngôn ngữ:
    sổ tiếng Đức chỉ nhận từ tiếng Đức, nên lệch ngôn ngữ báo 409 NGAY (trước khi trừ lượt AI).
    """
    if not deck_id:
        return []
    deck_lang = await ensure_deck_readable(deck_id, user_id)
    if deck_lang and deck_lang != lang_code:
        wanted, actual = get_lang(lang_code).vi_name, get_lang(deck_lang).vi_name
        raise ApiError(
            409, "LANG_MISMATCH",
            f"Sổ này là sổ {actual}, không thể thêm từ vựng {wanted}. Hãy chọn đúng ngôn ngữ của sổ.",
        )
    return list(await fetch_existing_terms(get_supabase(), deck_id))


async def _run_generation(req: GenerateVocabRequest, user: dict, images=()) -> dict:
    user_id, role = user["user_id"], user.get("role")
    existing = await _existing_terms_for(req.deck_id, user_id, req.lang_code)
    await vocab_quota.reserve(user_id, role)
    try:
        async with _generation_slots:
            data = await generate_vocabulary(req, existing_terms=existing, images=images)
    except Exception as exc:
        await vocab_quota.refund(user_id)  # lần sinh thất bại không bị trừ lượt
        if not isinstance(exc, VocabError):
            logger.exception("Lỗi không mong đợi khi sinh từ vựng")
            raise VocabError(500, "INTERNAL_ERROR", "Có lỗi không mong đợi khi tạo từ vựng. Vui lòng thử lại.") from exc
        raise
    data["quota"] = await vocab_quota.get_quota(user_id, role)
    logger.info(
        f"Vocab generated: user={user_id} mode={data['mode']} requested={data['requested']} "
        f"returned={data['returned']} dropped={len(data['dropped'])} latency_ms={data['latency_ms']} "
        f"providers={data['providers']} usage={data['usage']}"
    )
    return data


def _new_deck_lang(deck_lang: Optional[str], source_lang: Optional[str]) -> str:
    """Ngôn ngữ của sổ mới: ưu tiên `deck.lang_code`, rồi `source.lang_code`, cuối cùng là tiếng Anh (hành vi cũ)."""
    chosen = (deck_lang or source_lang or "en").strip().lower()
    if chosen not in LEARNABLE_LANGS:
        raise ApiError(422, "LANG_UNSUPPORTED", f"Ngôn ngữ '{chosen}' chưa hỗ trợ tạo từ vựng bằng AI.")
    if deck_lang and source_lang and deck_lang.strip().lower() != source_lang:
        raise ApiError(409, "LANG_MISMATCH", "Ngôn ngữ của sổ mới khác ngôn ngữ của các từ đã sinh.")
    return chosen


def _is_phrase_term(lang_code: Optional[str], term: str) -> bool:
    """Cụm từ nhiều chữ (không tính mạo từ: 'der Hund' là một danh từ). zh/ja/th không có khoảng trắng giữa từ."""
    lang = get_lang(lang_code)
    return lang.spaced and " " in strip_article(lang, term.strip())


@router.get("/vocabulary/quota", response_model=ApiResult)
async def get_quota_endpoint(user: dict = Depends(get_current_user)):
    """Hạn mức sinh từ bằng AI hôm nay (tier, tối đa, đã dùng, còn lại)."""
    return ApiResult(ok=True, data=await vocab_quota.get_quota(user["user_id"], user.get("role")))


@router.post("/vocabulary/generate", response_model=ApiResult)
async def generate_vocabulary_endpoint(payload: GenerateVocabRequest, user: dict = Depends(get_current_user)):
    """
    Sinh danh sách từ vựng để XEM TRƯỚC (không ghi DB):
    - `lang_code`: ngôn ngữ của từ vựng (en, de, zh, ja, ko, fr, es, ru, th); nghĩa và dịch câu ví dụ luôn bằng tiếng Việt.
    - `mode=topic`: theo chủ đề; `mode=text`: trích từ quan trọng từ đoạn văn viết bằng `lang_code`.
    - Truyền `deck_id` để thêm từ vào deck có sẵn: các từ đã có trong deck sẽ không được sinh lại,
      và deck phải cùng ngôn ngữ (409 LANG_MISMATCH nếu lệch).
    """
    return ApiResult(ok=True, data=await _run_generation(payload, user))


def _sniff_image(raw: bytes) -> Optional[str]:
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.post("/vocabulary/generate-image", response_model=ApiResult)
async def generate_vocabulary_from_image_endpoint(
    file: UploadFile = File(...),
    level: CefrLevel = Form("B1"),
    lang_code: VocabLang = Form("en"),
    count: int = Form(20),
    purpose: Optional[Purpose] = Form(None),
    instruction: Optional[str] = Form(None),
    deck_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    """Trích từ vựng (ngôn ngữ `lang_code`) từ ảnh (sách, biển quảng cáo, tài liệu...). JPG/PNG/WEBP, tối đa 5MB."""
    raw = await file.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise VocabError(413, "IMAGE_TOO_LARGE", "Ảnh vượt quá 5MB.")
    mime = _sniff_image(raw)
    if not mime:
        raise VocabError(415, "UNSUPPORTED_IMAGE", "Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP.")
    if instruction and len(instruction) > MAX_INSTRUCTION_CHARS:
        raise VocabError(422, "INVALID_INPUT", f"Ghi chú không quá {MAX_INSTRUCTION_CHARS} ký tự.")
    # mode="text" chỉ để dùng chung model; nội dung thật nằm trong ảnh.
    try:
        req = GenerateVocabRequest(
            mode="text", text="(content of the attached image)", level=level, count=count, lang_code=lang_code,
            purpose=purpose, instruction=instruction, deck_id=deck_id,
        )
    except ValueError as exc:
        raise VocabError(422, "INVALID_INPUT", str(exc)) from exc
    data = await _run_generation(req, user, images=[(mime, raw)])
    return ApiResult(ok=True, data=data)


@router.post("/decks/from-generated", response_model=ApiResult)
async def commit_generated_endpoint(payload: CommitGeneratedRequest, user: dict = Depends(get_current_user)):
    """
    Lưu các từ đã xem trước/chỉnh sửa thành deck mới (`deck`) hoặc thêm vào deck có sẵn (`deck_id`).
    - Idempotent theo `client_request_id` (gọi lại trong 10 phút trả kết quả cũ, không tạo deck trùng).
    - Từ trùng với deck được bỏ qua; lỗi DB trả 503 và deck mới tạo dở dang được dọn.
    """
    user_id = user["user_id"]
    now = time.time()
    for key in [k for k, (ts, _) in _commit_cache.items() if now - ts > IDEMPOTENCY_TTL_SECONDS]:
        _commit_cache.pop(key, None)
    cache_key = (user_id, payload.client_request_id)
    if cache_key in _commit_cache:
        return ApiResult(ok=True, data={**_commit_cache[cache_key][1], "idempotent_replay": True})

    source = SOURCE_BY_MODE.get(payload.source.mode, "ai_topic")
    created_new = False
    if payload.deck_id:
        deck_id = payload.deck_id
        # Ngôn ngữ do SỔ quyết định: để None thì bulk_insert_cards lấy theo sổ; client truyền khác sổ -> 409 LANG_MISMATCH.
        lang_code = payload.source.lang_code
        deck = {"id": deck_id}
    else:
        spec = payload.deck
        new_lang = _new_deck_lang(spec.lang_code, payload.source.lang_code)
        deck = await create_deck(spec.title.strip(), (spec.description or "").strip(), user_id, lang_code=new_lang)
        deck_id, lang_code, created_new = deck["id"], new_lang, True

    cards = [
        {
            "term": c.term.strip(),
            "definition": c.definition.strip(),
            "phonetic": (c.phonetic or "").strip() or None,
            "part_of_speech": normalize_pos(c.part_of_speech) or ("phrase" if _is_phrase_term(lang_code, c.term) else "noun"),
            "example": (c.example or "").strip() or None,
            "example_translation": (c.example_translation or "").strip() or None,
            "level": c.level or payload.source.level,
            "source": source,
            "target_lang": "vi",  # nghĩa do AI sinh luôn bằng tiếng Việt
        }
        for c in payload.cards
    ]
    try:
        result = await bulk_insert_cards(deck_id=deck_id, user_id=user_id, cards_data=cards, lang_code=lang_code)
    except Exception:
        if created_new:
            try:
                await delete_deck(deck_id, user_id)  # không để lại deck rỗng khi lưu thẻ thất bại
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.warning(f"Không dọn được deck rỗng {deck_id}: {cleanup_exc}")
        raise

    data = {"deck": deck, **result}
    _commit_cache[cache_key] = (now, data)
    return ApiResult(ok=True, data=data)

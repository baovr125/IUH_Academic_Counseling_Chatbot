import asyncio
import os
import uuid
import datetime
import random
import difflib
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
from app.services.fsrs_algorithm import calculate_fsrs
from app.services.normalization import build_cloze
from app.utils.errors import ApiError
from app.utils.languages import normalize_lang
from app.utils.logger import logger
from starlette.concurrency import run_in_threadpool

# Stability (ngày) từ ngưỡng này trở lên được coi là "đã thuộc" (trí nhớ bền ~ 3 tuần)
MASTERED_STABILITY_DAYS = 21.0

# In-memory deck & card store fallback
in_memory_decks: Dict[str, Dict[str, Any]] = {}
in_memory_cards: Dict[str, Dict[str, Any]] = {}

def to_valid_uuid(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    try:
        uuid.UUID(str(val))
        return str(val)
    except ValueError:
        return None

_supabase_client: Optional[Client] = None
_supabase_client_key: Optional[tuple] = None


def make_supabase(url: str, key: str) -> Client:
    """
    Tạo client Supabase dùng chung: HTTP/1.1 với pool kết nối giữ sống.
    Trước đây mỗi lần gọi `get_supabase()` tạo client mới (kèm kết nối TLS/HTTP2 mới) nên mỗi truy vấn tốn thêm một lần bắt tay
    và các truy vấn song song hay bị máy chủ ngắt (`ConnectionTerminated`).
    """
    import httpx
    from supabase.lib.client_options import SyncClientOptions

    http_client = httpx.Client(
        http2=False,
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_connections=40, max_keepalive_connections=20),
    )
    return create_client(url, key, options=SyncClientOptions(httpx_client=http_client))


def reset_supabase_client() -> None:
    global _supabase_client, _supabase_client_key
    _supabase_client, _supabase_client_key = None, None


def get_supabase() -> Optional[Client]:
    global _supabase_client, _supabase_client_key
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")  # ưu tiên khóa service-role (RLS bật, anon bị thu quyền)
    if not url or not key:
        return None
    cache_key = (make_supabase, url, key)  # đổi hàm tạo/URL/khóa (ví dụ trong test) thì dựng lại client
    if _supabase_client is None or _supabase_client_key != cache_key:
        _supabase_client = make_supabase(url, key)
        _supabase_client_key = cache_key
    return _supabase_client

def _is_owner(owner: Any, user_id: str) -> bool:
    """
    Chỉ chủ sở hữu mới được truy cập deck/thẻ trên Supabase.
    Bản ghi không có chủ (user_id NULL, ví dụ deck hệ thống của thư viện bộ từ) KHÔNG ai ghi/đọc được qua
    các API cá nhân; deck hệ thống chỉ đi qua các endpoint /catalog.
    """
    owner_text = "" if owner is None else str(owner)
    return owner_text not in ("", "None", "anonymous") and owner_text == str(user_id)

def db_write_error(action: str, exc: Exception) -> HTTPException:
    """Lỗi ghi DB không được nuốt: báo 503 để client biết dữ liệu CHƯA được lưu."""
    logger.error(f"Supabase error while trying to {action}: {exc}")
    return HTTPException(
        status_code=503,
        detail=f"Không thể {action} do lỗi cơ sở dữ liệu. Vui lòng thử lại sau."
    )

def is_missing_column_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "column" in text and ("does not exist" in text or "schema cache" in text or "could not find" in text)


async def insert_with_optional_columns(supabase, table: str, row: Dict[str, Any], optional_keys: tuple) -> bool:
    """
    Chèn một dòng. Nếu DB chưa chạy migration (thiếu cột mở rộng) thì chèn lại KHÔNG kèm các cột đó và trả False;
    mọi lỗi khác (kể cả lỗi lần chèn thứ hai) được ném ra cho nơi gọi xử lý.
    """
    try:
        await run_in_threadpool(lambda: supabase.table(table).insert(row).execute())
        return True
    except Exception as e:  # noqa: BLE001
        if not (is_missing_column_error(e) and any(k in row for k in optional_keys)):
            raise
        logger.warning(f"Bảng {table} chưa có cột mở rộng {optional_keys} (chạy migration mới nhất); lưu không kèm các cột này. {e}")
    reduced = {k: v for k, v in row.items() if k not in optional_keys}
    await run_in_threadpool(lambda: supabase.table(table).insert(reduced).execute())
    return False


# Cột mở rộng của deck (migration 005): thiếu thì vẫn tạo được deck.
DECK_OPTIONAL_COLUMNS = ("lang_confirmed", "is_default")


def require_lang(lang_code: Optional[str]) -> str:
    """Chuẩn hóa mã ngôn ngữ hoặc báo lỗi có mã. KHÔNG bao giờ tự gán mặc định."""
    if not lang_code or str(lang_code).strip().lower() == "auto":
        raise ApiError(422, "LANG_REQUIRED", "Thiếu ngôn ngữ của từ vựng. Hãy chọn ngôn ngữ trước khi lưu.")
    code = normalize_lang(lang_code)
    if not code:
        raise ApiError(422, "LANG_UNSUPPORTED", f"Ngôn ngữ '{lang_code}' chưa được hỗ trợ.")
    return code


async def create_deck(
    title: str,
    description: Optional[str],
    user_id: str,
    lang_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    lang_code = require_lang(lang_code)
    deck_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    deck_extra = {"lang_confirmed": True, **(extra or {})}  # người dùng/hệ thống chủ động chọn ngôn ngữ khi tạo deck
    deck_data = {
        "id": deck_id,
        "user_id": user_id,
        "title": title,
        "description": description or "",
        "lang_code": lang_code,
        "icon_flag": "🌐",
        "cards_count": 0,
        "created_at": now_iso,
        **deck_extra,
    }

    supabase = get_supabase()
    if supabase:
        try:
            valid_user_id = to_valid_uuid(user_id)
            sb_payload = {
                "id": deck_id,
                "title": title,
                "description": description or "",
                "lang_code": lang_code,
                "icon_flag": "🌐",
                **deck_extra,
            }
            if valid_user_id:
                sb_payload["user_id"] = valid_user_id
            await insert_with_optional_columns(supabase, "flashcard_decks", sb_payload, DECK_OPTIONAL_COLUMNS)
        except Exception as e:
            raise db_write_error("tạo bộ thẻ", e)

    in_memory_decks[deck_id] = deck_data
    return deck_data

async def count_deck_cards(supabase, deck_id: str) -> int:
    """Đếm thẻ của deck bằng COUNT phía DB (không kéo dữ liệu về, không bị giới hạn 1000 dòng)."""
    try:
        res = await run_in_threadpool(
            lambda: supabase.table("flashcards").select("id", count="exact").eq("deck_id", deck_id).limit(1).execute()
        )
        return int(res.count) if res.count is not None else 0
    except Exception as e:
        logger.warning(f"Failed to count cards of deck {deck_id}: {e}")
        return 0

async def get_decks(user_id: str, lang_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lấy danh sách các bộ thẻ của người dùng hiện tại; `lang_code` lọc ngay ở truy vấn (không lọc ở frontend).
    Khi Supabase được cấu hình thì DB là nguồn sự thật; bộ nhớ chỉ dùng khi không có Supabase.
    """
    wanted_lang = require_lang(lang_code) if lang_code else None
    supabase = get_supabase()
    valid_user_id = to_valid_uuid(user_id)
    if supabase and valid_user_id:
        try:
            def build():
                q = supabase.table("flashcard_decks").select("*").eq("user_id", valid_user_id)
                if wanted_lang:
                    q = q.eq("lang_code", wanted_lang)
                return q.order("created_at", desc=True).execute()

            res = await run_in_threadpool(build)
        except Exception as e:
            logger.error(f"Failed to fetch decks from Supabase: {e}")
            raise HTTPException(status_code=503, detail="Không thể tải danh sách bộ thẻ. Vui lòng thử lại sau.")
        decks = [dict(d) for d in (res.data or [])]
        counts = await asyncio.gather(*[count_deck_cards(supabase, str(d["id"])) for d in decks])
        for deck, count in zip(decks, counts):
            deck["cards_count"] = count
        return decks

    decks_map: Dict[str, Dict[str, Any]] = {}
    for d in in_memory_decks.values():
        if str(d.get("user_id", "")) == str(user_id) and (not wanted_lang or normalize_lang(d.get("lang_code")) == wanted_lang):
            d_copy = dict(d)
            d_copy["cards_count"] = len([c for c in in_memory_cards.values() if str(c.get("deck_id")) == str(d.get("id"))])
            decks_map[d["id"]] = d_copy
    return list(decks_map.values())

async def update_deck(
    deck_id: str,
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    lang_code: Optional[str] = None
) -> Dict[str, Any]:
    """Cập nhật thông tin bộ thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase and to_valid_uuid(deck_id):
        try:
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("*").eq("id", deck_id).execute()
            )
            if not deck_res.data or len(deck_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
            owner = str(deck_res.data[0].get("user_id", ""))
            if not _is_owner(owner, user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bộ thẻ này.")

            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description

            if update_data:
                await run_in_threadpool(
                    lambda: supabase.table("flashcard_decks").update(update_data).eq("id", deck_id).execute()
                )

            updated = {**deck_res.data[0], **update_data}
            if lang_code is not None:
                new_lang = require_lang(lang_code)
                if new_lang != normalize_lang(updated.get("lang_code")) or not updated.get("lang_confirmed"):
                    updated = await set_deck_language(deck_id, user_id, new_lang)
            in_memory_decks[deck_id] = updated
            return updated
        except (HTTPException, ApiError):
            raise
        except Exception as e:
            raise db_write_error("cập nhật bộ thẻ", e)

    deck = in_memory_decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
    if deck.get("user_id") and deck.get("user_id") != "anonymous" and deck.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bộ thẻ này.")
    if title is not None:
        deck["title"] = title
    if description is not None:
        deck["description"] = description
    if lang_code is not None:
        new_lang = require_lang(lang_code)
        deck["lang_code"] = new_lang
        deck["lang_confirmed"] = True
        for card in in_memory_cards.values():
            if str(card.get("deck_id")) == str(deck_id):
                card["lang_code"] = new_lang
                card["audio_url"] = build_audio_url(card.get("term", ""), new_lang)
    return deck


async def set_deck_language(deck_id: str, user_id: str, lang_code: str) -> Dict[str, Any]:
    """
    Đặt (hoặc đổi) ngôn ngữ của deck và XÁC NHẬN nó. Mọi thẻ trong deck đổi theo (deck là đơn vị ngôn ngữ) và
    `audio_url` được tính lại vì URL âm thanh chứa mã ngôn ngữ. Dùng cho mục "Cần xác nhận ngôn ngữ" và khi sửa deck.
    """
    new_lang = require_lang(lang_code)
    supabase = get_supabase()
    if not (supabase and to_valid_uuid(deck_id)):
        return await update_deck(deck_id, user_id, lang_code=new_lang)

    try:
        res = await run_in_threadpool(lambda: supabase.table("flashcard_decks").select("*").eq("id", deck_id).execute())
        if not res.data:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
        deck = res.data[0]
        if not _is_owner(deck.get("user_id"), user_id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa bộ thẻ này.")

        changes = {"lang_code": new_lang, "lang_confirmed": True}
        try:
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").update(changes).eq("id", deck_id).execute())
        except Exception as e:  # noqa: BLE001
            if not is_missing_column_error(e):
                raise
            changes = {"lang_code": new_lang}  # chưa chạy migration 005: vẫn đổi được ngôn ngữ
            await run_in_threadpool(lambda: supabase.table("flashcard_decks").update(changes).eq("id", deck_id).execute())

        cards = await _fetch_deck_rows(supabase, deck_id)
        for i in range(0, len(cards), 25):
            await asyncio.gather(*[
                run_in_threadpool(
                    lambda c=c: supabase.table("flashcards").update(
                        {"lang_code": new_lang, "audio_url": build_audio_url(c.get("term", ""), new_lang)}
                    ).eq("id", c["id"]).execute()
                )
                for c in cards[i:i + 25]
            ])
        for cid in [c["id"] for c in cards]:
            in_memory_cards.pop(cid, None)  # bản sao trong RAM (nếu có) đã lỗi thời
        return {**deck, **changes}
    except (HTTPException, ApiError):
        raise
    except Exception as e:  # noqa: BLE001
        raise db_write_error("đổi ngôn ngữ bộ thẻ", e)

async def delete_deck(deck_id: str, user_id: str) -> bool:
    """Xóa bộ thẻ cùng tất cả các thẻ bên trong với IDOR Protection."""
    supabase = get_supabase()
    if supabase and to_valid_uuid(deck_id):
        try:
            deck_res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("user_id").eq("id", deck_id).execute()
            )
            if not deck_res.data or len(deck_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy bộ thẻ.")
            owner = str(deck_res.data[0].get("user_id", ""))
            if not _is_owner(owner, user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bộ thẻ này.")

            # Xóa tất cả các thẻ trong bộ thẻ trước
            await run_in_threadpool(
                lambda: supabase.table("flashcards").delete().eq("deck_id", deck_id).execute()
            )
            # Xóa bộ thẻ
            await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").delete().eq("id", deck_id).execute()
            )
        except HTTPException:
            raise
        except Exception as e:
            raise db_write_error("xóa bộ thẻ", e)

    # Xóa trong in-memory
    if deck_id in in_memory_decks:
        if in_memory_decks[deck_id].get("user_id") in [user_id, "anonymous"]:
            del in_memory_decks[deck_id]

    # Xóa các thẻ thuộc deck trong in-memory
    card_ids_to_del = [cid for cid, c in in_memory_cards.items() if c.get("deck_id") == deck_id]
    for cid in card_ids_to_del:
        del in_memory_cards[cid]

    return True

def build_audio_url(term: str, lang_code: str) -> str:
    """Content-Addressable Storage (CAS): cùng (ngôn ngữ, từ) luôn ra cùng một URL âm thanh."""
    clean_lang = (lang_code or "en").strip().lower()[:2]
    clean_term = (term or "").strip().lower()
    term_hash = hashlib.md5(f"{clean_lang}_{clean_term}".encode('utf-8')).hexdigest()
    return f"/api/v1/translate/audio/terms/{clean_lang}_{term_hash}.mp3"

async def ensure_deck_for_write(
    deck_id: str,
    user_id: str,
    lang_code: Optional[str] = None,
    title: str = "Sổ từ vựng"
) -> Optional[Dict[str, Any]]:
    """
    Kiểm tra quyền sở hữu deck trước khi ghi thẻ (IDOR Protection).
    - Deck thuộc người khác -> 403. Không đọc được DB -> 503 (KHÔNG fail-open).
    - Deck chỉ tồn tại ở client (LocalStorage) -> tự tạo trên Supabase để thỏa khóa ngoại.
    Trả về dòng deck hiện có (hoặc dòng vừa tạo); None nếu không dùng Supabase.
    """
    supabase = get_supabase()
    if not supabase:
        deck = in_memory_decks.get(deck_id)
        if deck and deck.get("user_id") and deck.get("user_id") != "anonymous" and deck.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thêm thẻ vào bộ thẻ của người khác.")
        return deck

    valid_deck_id = to_valid_uuid(deck_id)
    if not valid_deck_id:
        raise HTTPException(status_code=400, detail="Mã bộ thẻ không hợp lệ.")
    try:
        deck_res = await run_in_threadpool(
            lambda: supabase.table("flashcard_decks").select("id, user_id, lang_code, title").eq("id", valid_deck_id).execute()
        )
    except Exception as e:
        raise db_write_error("kiểm tra quyền sở hữu bộ thẻ", e)

    if deck_res.data:
        row = deck_res.data[0]
        owner_id = str(row.get("user_id") or "")
        if not _is_owner(owner_id, user_id):
            logger.warning(f"IDOR Alert: User {user_id} attempted to write to deck {deck_id} owned by {owner_id}")
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền thêm thẻ vào bộ thẻ của người khác (IDOR Protection)."
            )
        return row

    # Deck chỉ có ở client: cần ngôn ngữ rõ ràng để tạo trên máy chủ (không đoán 'en').
    deck_lang = require_lang(lang_code)
    payload = {
        "id": valid_deck_id,
        "title": title,
        "description": f"Sổ từ vựng ({deck_lang.upper()})",
        "lang_code": deck_lang,
        "icon_flag": "🌐",
        "lang_confirmed": True,
    }
    valid_user_id = to_valid_uuid(user_id)
    if valid_user_id:
        payload["user_id"] = valid_user_id
    try:
        await insert_with_optional_columns(supabase, "flashcard_decks", payload, DECK_OPTIONAL_COLUMNS)
    except Exception as e:
        raise db_write_error("tạo bộ thẻ trên máy chủ", e)
    logger.info(f"Auto-created missing deck {valid_deck_id} on Supabase")
    return payload

def new_card_record(
    deck_id: str,
    user_id: str,
    term: str,
    definition: str,
    lang_code: str,
    phonetic: Optional[str] = None,
    audio_url: Optional[str] = None,
    example_sentence: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    now_iso: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Dựng bản ghi thẻ mới với trạng thái FSRS khởi tạo (state 0 = New)."""
    now_iso = now_iso or datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "deck_id": deck_id,
        "user_id": user_id,
        "term": term,
        "definition": definition,
        "phonetic": phonetic,
        "audio_url": audio_url or build_audio_url(term, lang_code),
        "example": example_sentence,
        "example_sentence": example_sentence,
        "part_of_speech": part_of_speech or "phrase",
        "lang_code": lang_code,
        "state": 0,
        "reps": 0,
        "lapses": 0,
        "stability": 0.0,
        "difficulty": 0.0,
        "elapsed_days": 0,
        "scheduled_days": 0,
        "last_review": None,
        "due": now_iso
    }
    if extra:
        record.update(extra)
    return record

# Cột mở rộng (migration 003 và 005). Chưa chạy migration thì lưu thẻ mà không kèm các cột này.
EXTENDED_CARD_COLUMNS = ("example_translation", "level", "source", "target_lang")

# Các cột của bảng `flashcards` mà service ghi khi tạo thẻ.
DB_CARD_COLUMNS = (
    "id", "deck_id", "user_id", "term", "definition", "phonetic", "audio_url", "example",
    "part_of_speech", "lang_code", "state", "reps", "lapses", "stability", "difficulty",
    "elapsed_days", "scheduled_days", "due",
)

def to_db_card_payload(card: Dict[str, Any], optional_columns: tuple = ()) -> Dict[str, Any]:
    """Chọn đúng các cột DB từ bản ghi thẻ; `deck_id`/`user_id` chuẩn hóa UUID (user_id không hợp lệ thì bỏ)."""
    payload = {k: card.get(k) for k in DB_CARD_COLUMNS + tuple(optional_columns) if k in card}
    payload["deck_id"] = to_valid_uuid(card.get("deck_id")) or card.get("deck_id")
    valid_uid = to_valid_uuid(card.get("user_id"))
    if valid_uid:
        payload["user_id"] = valid_uid
    else:
        payload.pop("user_id", None)
    return payload

def resolve_card_language(deck_row: Optional[Dict[str, Any]], requested: Optional[str]) -> str:
    """
    Ngôn ngữ của thẻ = ngôn ngữ của deck (deck là đơn vị ngôn ngữ). Client chỉ được TRUYỀN LẠI cùng giá trị;
    khác deck -> 409 LANG_MISMATCH. Không bao giờ tự gán 'en'.
    """
    wanted = require_lang(requested) if requested else None
    deck_raw = (deck_row or {}).get("lang_code")
    deck_lang = normalize_lang(deck_raw)
    if deck_row is not None and deck_raw and not deck_lang:
        raise ApiError(409, "DECK_LANG_UNKNOWN", "Bộ thẻ chưa có ngôn ngữ hợp lệ. Hãy chọn ngôn ngữ cho bộ thẻ trước khi thêm từ.")
    if deck_lang and wanted and wanted != deck_lang:
        raise ApiError(
            409, "LANG_MISMATCH",
            f"Từ vựng thuộc ngôn ngữ '{wanted}' nhưng bộ thẻ là '{deck_lang}'. Hãy chọn bộ thẻ đúng ngôn ngữ.",
        )
    lang = deck_lang or wanted
    if not lang:
        raise ApiError(422, "LANG_REQUIRED", "Thiếu ngôn ngữ của từ vựng. Hãy chọn ngôn ngữ trước khi lưu.")
    return lang


async def create_card(
    deck_id: str,
    front_text: str,
    back_text: str,
    user_id: str,
    phonetic: Optional[str] = None,
    audio_url: Optional[str] = None,
    example_sentence: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    lang_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Tạo thẻ mới với IDOR Protection (xác thực quyền sở hữu Deck) và tự động gắn Persistent Audio URL."""
    deck_row = await ensure_deck_for_write(deck_id, user_id, lang_code)
    lang = resolve_card_language(deck_row, lang_code)

    card_data = new_card_record(
        deck_id=deck_id,
        user_id=user_id,
        term=front_text,
        definition=back_text,
        lang_code=lang,
        phonetic=phonetic,
        audio_url=audio_url,
        example_sentence=example_sentence,
        part_of_speech=part_of_speech,
        extra=extra,
    )

    supabase = get_supabase()
    if supabase:
        try:
            await insert_with_optional_columns(
                supabase, "flashcards", to_db_card_payload(card_data, EXTENDED_CARD_COLUMNS), EXTENDED_CARD_COLUMNS
            )
        except Exception as e:
            raise db_write_error("lưu thẻ từ vựng", e)

    in_memory_cards[card_data["id"]] = card_data
    if deck_id in in_memory_decks:
        in_memory_decks[deck_id]["cards_count"] = len([c for c in in_memory_cards.values() if str(c.get("deck_id")) == str(deck_id)])

    return card_data

async def update_card_audio_url(card_id: str, audio_url: str) -> bool:
    """Cập nhật đường dẫn âm thanh phát âm (MinIO) vào thẻ Flashcard."""
    if card_id in in_memory_cards:
        in_memory_cards[card_id]["audio_url"] = audio_url

    supabase = get_supabase()
    if supabase:
        try:
            await run_in_threadpool(
                lambda: supabase.table("flashcards").update({"audio_url": audio_url}).eq("id", card_id).execute()
            )
            logger.info(f"Updated audio_url for card {card_id} in Supabase.")
            return True
        except Exception as e:
            logger.warning(f"Failed to update audio_url for card {card_id} in Supabase: {e}")
            return False
    return True

async def get_card_by_id(card_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin thẻ kèm kiểm tra IDOR. Trả None nếu không tồn tại."""
    supabase = get_supabase()
    if supabase:
        valid_card_id = to_valid_uuid(card_id)
        if valid_card_id:
            try:
                res = await run_in_threadpool(
                    lambda: supabase.table("flashcards").select("*").eq("id", valid_card_id).execute()
                )
            except Exception as e:
                logger.error(f"Failed to fetch card from Supabase: {e}")
                raise HTTPException(status_code=503, detail="Không thể truy cập cơ sở dữ liệu. Vui lòng thử lại sau.")
            if res.data and len(res.data) > 0:
                card = res.data[0]
                card_user_id = str(card.get("user_id") or "")
                if not _is_owner(card_user_id, user_id):
                    raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thẻ này.")
                return card

    card = in_memory_cards.get(card_id)
    if card and card.get("user_id") and card.get("user_id") != "anonymous" and card.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thẻ này.")
    return card

async def review_card(card_id: str, grade: int, user_id: str) -> Dict[str, Any]:
    """
    Ôn tập thẻ với thuật toán FSRS và kiểm tra bảo mật quyền sở hữu (IDOR Protection).
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    """
    card = await get_card_by_id(card_id, user_id)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")

    fsrs_results = calculate_fsrs(grade=grade, card_dict=card)

    supabase = get_supabase()
    if supabase and to_valid_uuid(card_id):  # thẻ chỉ có ở client (id không phải UUID) thì không ghi DB
        valid_uid = to_valid_uuid(user_id)
        review_log_data = {
            "card_id": card_id,
            "grade": grade,
            "state": fsrs_results.get("state", 0),
            "stability": fsrs_results.get("stability", 0.0),
            "difficulty": fsrs_results.get("difficulty", 0.0),
            "elapsed_days": fsrs_results.get("elapsed_days", 0),
            "scheduled_days": fsrs_results.get("scheduled_days", 0),
            "reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        if valid_uid:
            review_log_data["user_id"] = valid_uid
        try:
            await run_in_threadpool(
                lambda: supabase.table("flashcards").update(fsrs_results).eq("id", card_id).execute()
            )
            await run_in_threadpool(
                lambda: supabase.table("review_logs").insert(review_log_data).execute()
            )
        except Exception as e:
            raise db_write_error("ghi kết quả ôn tập", e)

    card.update(fsrs_results)
    in_memory_cards[card_id] = card
    return card

async def verify_spelling(card_id: str, user_input: str, user_id: str, auto_apply_review: bool = False) -> Dict[str, Any]:
    """
    Xác minh gõ chính tả (Active Recall Spelling Challenge):
    - So khớp từ gốc và chuỗi người dùng nhập (chuẩn hóa chữ thường, xóa khoảng trắng thừa).
    - Tính điểm tương đồng bằng Levenshtein/SequenceMatcher.
    - Đưa ra phản hồi gợi ý thông minh và gợi ý Grade FSRS tương ứng.
    """
    card = await get_card_by_id(card_id, user_id)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")

    correct_term = str(card.get("term", "")).strip()
    normalized_target = correct_term.lower()
    normalized_input = str(user_input).strip().lower()

    # Tính độ tương đồng
    matcher = difflib.SequenceMatcher(None, normalized_input, normalized_target)
    similarity = matcher.ratio()

    is_correct = (normalized_input == normalized_target)
    is_close = False
    feedback = ""
    suggested_grade = 1

    if is_correct:
        feedback = "Chính xác tuyệt đối! 🎉 Bạn đã ghi nhớ từ này rất xuất sắc."
        suggested_grade = 4  # 4: Easy
    elif similarity >= 0.75:
        is_close = True
        feedback = f"Gần đúng rồi! Lỗi chính tả nhỏ. Bạn gõ '{user_input}', đáp án đúng là '{correct_term}'."
        suggested_grade = 2  # 2: Hard
    else:
        feedback = f"Chưa chính xác. Đáp án đúng là '{correct_term}'. Hãy luyện tập thêm nhé!"
        suggested_grade = 1  # 1: Again

    if auto_apply_review:
        await review_card(card_id=card_id, grade=suggested_grade, user_id=user_id)

    return {
        "is_correct": is_correct,
        "is_close": is_close,
        "similarity_score": round(similarity, 3),
        "correct_term": correct_term,
        "user_input": user_input,
        "feedback": feedback,
        "suggested_grade": suggested_grade,
        "audio_url": card.get("audio_url"),
        "phonetic": card.get("phonetic"),
        "example_sentence": card.get("example"),
        "lang_code": card.get("lang_code") or "en"
    }

async def get_deck_lang(deck_id: str) -> str:
    """Ngôn ngữ của deck: ưu tiên Supabase, sau đó bộ nhớ."""
    supabase = get_supabase()
    valid_deck_id = to_valid_uuid(deck_id)
    if supabase and valid_deck_id:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("lang_code").eq("id", valid_deck_id).execute()
            )
            if res.data and res.data[0].get("lang_code"):
                return str(res.data[0]["lang_code"])
        except Exception as e:
            logger.warning(f"Failed to fetch deck lang from Supabase: {e}")
    deck_info = in_memory_decks.get(deck_id) or {}
    return deck_info.get("lang_code") or deck_info.get("langCode") or "en"

def _parse_due(value: Any) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        dt = value
    else:
        try:
            dt = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return datetime.datetime.now(datetime.timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)

def is_new_card(card: Dict[str, Any]) -> bool:
    return int(card.get("state") or 0) == 0 and not card.get("last_review")

def build_distractors(card: Dict[str, Any], pool: List[Dict[str, Any]], count: int = 3) -> List[str]:
    """Chọn đáp án nhiễu từ các thẻ khác trong cùng deck (ưu tiên cùng từ loại, nghĩa khác nhau)."""
    answer = str(card.get("definition", "")).strip().lower()
    pos = card.get("part_of_speech")
    seen = {answer}
    same_pos: List[str] = []
    other: List[str] = []
    for other_card in pool:
        if other_card.get("id") == card.get("id"):
            continue
        text = str(other_card.get("definition", "")).strip()
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        (same_pos if pos and other_card.get("part_of_speech") == pos else other).append(text)
    random.shuffle(same_pos)
    random.shuffle(other)
    return (same_pos + other)[:count]

def choose_study_mode(card: Dict[str, Any], distractors: List[str]) -> str:
    """
    Chọn chế độ ôn cho một thẻ: flip | spelling | choice | listening.
    Thẻ mới -> flip (giới thiệu từ). Thẻ khó/hay quên -> tăng tỷ lệ bài chủ động (gõ, nghe).
    """
    term = str(card.get("term", ""))
    if is_new_card(card):
        return "flip"
    lapses = int(card.get("lapses") or 0)
    difficulty = float(card.get("difficulty") or 0.0)
    state = int(card.get("state") or 0)
    hard = lapses > 0 or difficulty >= 5.0 or state in (1, 3)
    roll = random.random()
    can_choose = len(distractors) >= 3
    can_spell = len(term.split()) <= 3
    if hard:
        if roll < 0.35 and can_spell:
            return "spelling"
        if roll < 0.6 and can_choose:
            return "listening"
        return "flip"
    if roll < 0.2 and can_spell:
        return "spelling"
    if roll < 0.55 and can_choose:
        return "choice"
    if roll < 0.7 and can_choose:
        return "listening"
    return "flip"

async def get_study_queue(
    deck_id: str,
    user_id: str,
    limit: int = 50,
    new_limit: int = 20,
    weak_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Hàng đợi ôn tập thông minh:
    - Thẻ đến hạn (due <= hiện tại) lên trước, quá hạn lâu nhất trước; sau đó mới đến thẻ mới (tối đa `new_limit`).
    - `weak_only`: chỉ các thẻ hay quên (lapses > 0 hoặc difficulty >= 7) để ôn riêng.
    - Mỗi thẻ có `recommended_mode` (flip/spelling/choice/listening); `choices` là 4 phương án nghĩa đã xáo trộn
      khi deck có đủ thẻ để làm đáp án nhiễu.
    - Tự sinh câu đục lỗ (Cloze) từ câu ví dụ.
    """
    raw_cards, deck_lang = await asyncio.gather(get_deck_cards(deck_id, user_id), get_deck_lang(deck_id))
    now = datetime.datetime.now(datetime.timezone.utc)

    due_cards: List[Dict[str, Any]] = []
    new_cards: List[Dict[str, Any]] = []
    for card in raw_cards:
        if weak_only:
            if int(card.get("lapses") or 0) > 0 or float(card.get("difficulty") or 0.0) >= 7.0:
                due_cards.append(card)
            continue
        if is_new_card(card):
            new_cards.append(card)
        elif _parse_due(card.get("due")) <= now:
            due_cards.append(card)

    due_cards.sort(key=lambda c: _parse_due(c.get("due")))
    new_cards.sort(key=lambda c: str(c.get("created_at") or ""))
    selected = (due_cards + new_cards[:max(0, new_limit)])[:max(1, limit)]

    study_items = []
    for card in selected:
        term = card.get("term", "")
        example = card.get("example") or card.get("example_sentence") or ""
        card_lang = card.get("lang_code") or card.get("langCode") or deck_lang
        distractors = build_distractors(card, raw_cards)
        mode = choose_study_mode(card, distractors)

        choices = None
        if len(distractors) >= 3:
            choices = distractors + [str(card.get("definition", ""))]
            random.shuffle(choices)

        cloze_sentence = build_cloze(example, term)  # chịu được dạng biến hình: polluted ~ pollute

        study_items.append({
            "id": card.get("id"),
            "deck_id": card.get("deck_id"),
            "term": term,
            "definition": card.get("definition", ""),
            "phonetic": card.get("phonetic"),
            "audio_url": card.get("audio_url"),
            "example_sentence": example,
            "example_translation": card.get("example_translation"),
            "part_of_speech": card.get("part_of_speech"),
            "lang_code": card_lang,
            "state": int(card.get("state") or 0),
            "lapses": int(card.get("lapses") or 0),
            "stability": card.get("stability", 0.0),
            "difficulty": card.get("difficulty", 0.0),
            "due": card.get("due") or now.isoformat(),
            "is_new": is_new_card(card),
            "recommended_mode": mode,
            "choices": choices,
            "cloze_sentence": cloze_sentence
        })

    return study_items

async def get_study_stats(deck_id: str, user_id: str) -> Dict[str, Any]:
    """Thống kê tiến độ deck: tổng, mới, đến hạn hôm nay, đang học, đã thuộc, từ yếu."""
    cards = await get_deck_cards(deck_id, user_id)
    now = datetime.datetime.now(datetime.timezone.utc)
    stats = {"total": len(cards), "new": 0, "due": 0, "learning": 0, "mastered": 0, "weak": 0}
    for card in cards:
        if is_new_card(card):
            stats["new"] += 1
            continue
        if _parse_due(card.get("due")) <= now:
            stats["due"] += 1
        stability = float(card.get("stability") or 0.0)
        if stability >= MASTERED_STABILITY_DAYS:
            stats["mastered"] += 1
        else:
            stats["learning"] += 1
        if int(card.get("lapses") or 0) > 0 or float(card.get("difficulty") or 0.0) >= 7.0:
            stats["weak"] += 1
    return stats

async def ensure_deck_readable(deck_id: str, user_id: str) -> Optional[str]:
    """
    403 nếu deck thuộc người khác. Deck chỉ tồn tại ở client (không có trên DB) thì cho qua với kết quả rỗng.
    Trả mã ngôn ngữ (đã chuẩn hóa) của deck, hoặc None nếu deck không có/chưa rõ ngôn ngữ.
    """
    supabase = get_supabase()
    valid_deck_id = to_valid_uuid(deck_id)
    if supabase and valid_deck_id:
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcard_decks").select("user_id, lang_code").eq("id", valid_deck_id).execute()
            )
        except Exception as e:
            logger.error(f"Failed to check deck ownership: {e}")
            raise HTTPException(status_code=503, detail="Không thể truy cập cơ sở dữ liệu. Vui lòng thử lại sau.")
        if res.data:
            owner = str(res.data[0].get("user_id") or "")
            if not _is_owner(owner, user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập bộ thẻ này.")
            return normalize_lang(res.data[0].get("lang_code"))
        return None
    deck = in_memory_decks.get(deck_id)
    if deck and deck.get("user_id") and deck.get("user_id") not in ("anonymous", user_id):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập bộ thẻ này.")
    return normalize_lang((deck or {}).get("lang_code"))

async def _fetch_deck_rows(supabase, valid_deck_id: str) -> List[Dict[str, Any]]:
    """Tất cả thẻ của deck, đọc phân trang (PostgREST mặc định chỉ trả 1000 dòng/lần)."""
    rows: List[Dict[str, Any]] = []
    page, offset = 1000, 0
    try:
        while True:
            res = await run_in_threadpool(
                lambda o=offset: supabase.table("flashcards")
                    .select("*")
                    .eq("deck_id", valid_deck_id)
                    .order("created_at", desc=False)
                    .order("id", desc=False)
                    .range(o, o + page - 1)
                    .execute()
            )
            batch = res.data or []
            rows.extend(batch)
            if len(batch) < page:
                return rows
            offset += page
    except Exception as e:
        logger.error(f"Failed to fetch cards from Supabase: {e}")
        raise HTTPException(status_code=503, detail="Không thể tải danh sách thẻ. Vui lòng thử lại sau.")


def _normalize_card_row(row: Dict[str, Any], deck_id: str) -> Dict[str, Any]:
    card = dict(row)
    card["deck_id"] = deck_id
    card["example_sentence"] = row.get("example")
    card["part_of_speech"] = row.get("part_of_speech") or "phrase"
    card["lang_code"] = row.get("lang_code") or "en"
    card["due"] = row.get("due") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    return card


async def get_deck_cards(deck_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Lấy danh sách thẻ trong bộ thẻ (có kiểm tra quyền sở hữu).
    Khi Supabase được cấu hình thì DB là nguồn sự thật; bộ nhớ chỉ dùng khi không có Supabase.
    """
    supabase = get_supabase()
    valid_deck_id = to_valid_uuid(deck_id)
    if supabase and valid_deck_id:
        # Kiểm tra quyền và tải thẻ chạy SONG SONG (tiết kiệm một vòng mạng tới Supabase); chỉ trả dữ liệu khi quyền hợp lệ.
        _, rows = await asyncio.gather(ensure_deck_readable(deck_id, user_id), _fetch_deck_rows(supabase, valid_deck_id))
        return [_normalize_card_row(c, deck_id) for c in rows]

    await ensure_deck_readable(deck_id, user_id)
    return [dict(c) for c in in_memory_cards.values() if str(c.get("deck_id")) == str(deck_id)]

async def delete_card(card_id: str, user_id: str) -> bool:
    """Xóa thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase and to_valid_uuid(card_id):  # id không phải UUID = thẻ chỉ tồn tại ở client
        try:
            res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("user_id, deck_id").eq("id", card_id).execute()
            )
            if res.data and len(res.data) > 0:
                owner = str(res.data[0].get("user_id", ""))
                if not _is_owner(owner, user_id):
                    raise HTTPException(status_code=403, detail="Bạn không có quyền xóa thẻ này.")

            await run_in_threadpool(
                lambda: supabase.table("flashcards").delete().eq("id", card_id).execute()
            )
        except HTTPException:
            raise
        except Exception as e:
            raise db_write_error("xóa thẻ", e)

    if card_id in in_memory_cards:
        if in_memory_cards[card_id].get("user_id") == user_id:
            del in_memory_cards[card_id]
    return True

async def update_card(
    card_id: str,
    user_id: str,
    front_text: Optional[str] = None,
    back_text: Optional[str] = None,
    phonetic: Optional[str] = None,
    example_sentence: Optional[str] = None,
    part_of_speech: Optional[str] = None,
    lang_code: Optional[str] = None
) -> Dict[str, Any]:
    """Cập nhật thông tin thẻ với IDOR Protection."""
    supabase = get_supabase()
    if supabase and to_valid_uuid(card_id):  # id không phải UUID = thẻ chỉ tồn tại ở client
        try:
            card_res = await run_in_threadpool(
                lambda: supabase.table("flashcards").select("*").eq("id", card_id).execute()
            )
            if not card_res.data or len(card_res.data) == 0:
                raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")
            owner = str(card_res.data[0].get("user_id", ""))
            if not _is_owner(owner, user_id):
                raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa thẻ này.")

            current_lang = normalize_lang(card_res.data[0].get("lang_code"))
            if lang_code is not None and require_lang(lang_code) != current_lang:
                raise ApiError(
                    409, "LANG_MISMATCH",
                    "Không thể đổi ngôn ngữ của từng thẻ; hãy đổi ngôn ngữ của cả bộ thẻ (thẻ luôn cùng ngôn ngữ với bộ thẻ).",
                )

            update_data = {}
            if front_text is not None:
                update_data["term"] = front_text
            if back_text is not None:
                update_data["definition"] = back_text
            if phonetic is not None:
                update_data["phonetic"] = phonetic
            if example_sentence is not None:
                update_data["example"] = example_sentence
            if part_of_speech is not None:
                update_data["part_of_speech"] = part_of_speech
            # Đổi từ -> tính lại persistent audio URL (theo ngôn ngữ hiện có của thẻ)
            term = front_text or card_res.data[0].get("term", "")
            if term and front_text is not None and current_lang:
                update_data["audio_url"] = build_audio_url(term, current_lang)

            if update_data:
                await run_in_threadpool(
                    lambda: supabase.table("flashcards").update(update_data).eq("id", card_id).execute()
                )

            updated = {**card_res.data[0], **update_data}
            in_memory_cards[card_id] = updated
            return updated
        except (HTTPException, ApiError):
            raise
        except Exception as e:
            raise db_write_error("cập nhật thẻ", e)

    card = in_memory_cards.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ từ vựng.")
    if card.get("user_id") and card.get("user_id") != "anonymous" and card.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa thẻ này.")
    if front_text is not None:
        card["term"] = front_text
    if back_text is not None:
        card["definition"] = back_text
    if phonetic is not None:
        card["phonetic"] = phonetic
    if example_sentence is not None:
        card["example"] = example_sentence
    if part_of_speech is not None:
        card["part_of_speech"] = part_of_speech
    if lang_code is not None and require_lang(lang_code) != normalize_lang(card.get("lang_code")):
        raise ApiError(409, "LANG_MISMATCH", "Không thể đổi ngôn ngữ của từng thẻ; hãy đổi ngôn ngữ của cả bộ thẻ.")
    return card


VN_TZ = datetime.timezone(datetime.timedelta(hours=7))

def _streak_intensity(count: int) -> int:
    if count <= 0:
        return 0
    if count < 5:
        return 1
    if count < 10:
        return 2
    if count < 20:
        return 3
    return 4

async def get_review_streak(user_id: str, days: int = 84) -> Dict[str, Any]:
    """
    Hoạt động ôn tập theo ngày (giờ Việt Nam) lấy từ `review_logs`, dùng cho heatmap và chuỗi ngày học.
    - `current_streak`: số ngày liên tiếp có ôn tập tính đến hôm nay (chưa ôn hôm nay thì tính đến hôm qua).
    - `today_reviews` đếm lượt ôn (một thẻ ôn nhiều lần tính nhiều lần); `today_cards` đếm số thẻ khác nhau đã ôn hôm nay
      (lượt không gắn thẻ không tính), dùng cho mục tiêu ngày của Dashboard.
    - Không có Supabase hoặc user id không phải UUID: trả về dữ liệu rỗng.
    """
    today = datetime.datetime.now(VN_TZ).date()
    start = today - datetime.timedelta(days=days - 1)
    counts: Dict[datetime.date, int] = {}
    today_cards: set = set()

    supabase = get_supabase()
    uid = to_valid_uuid(user_id)
    if supabase and uid:
        since = datetime.datetime.combine(start, datetime.time.min, tzinfo=VN_TZ).isoformat()
        page, offset = 1000, 0
        try:
            while True:
                res = await run_in_threadpool(
                    lambda o=offset: supabase.table("review_logs").select("reviewed_at, card_id")
                        .eq("user_id", uid).gte("reviewed_at", since)
                        .order("reviewed_at").range(o, o + page - 1).execute()
                )
                rows = res.data or []
                for row in rows:
                    ts = _parse_due(row.get("reviewed_at")).astimezone(VN_TZ).date()
                    counts[ts] = counts.get(ts, 0) + 1
                    if ts == today and row.get("card_id"):
                        today_cards.add(str(row["card_id"]))
                if len(rows) < page or offset >= 20000:
                    break
                offset += page
        except Exception as e:
            logger.error(f"Failed to read review_logs for streak: {e}")
            raise HTTPException(status_code=503, detail="Không thể tải lịch sử ôn tập. Vui lòng thử lại sau.")

    series = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        count = counts.get(d, 0)
        series.append({
            "date": datetime.datetime.combine(d, datetime.time.min, tzinfo=VN_TZ).isoformat(),
            "count": count,
            "intensity": _streak_intensity(count)
        })

    # Chuỗi hiện tại: lùi từ hôm nay (hoặc hôm qua nếu hôm nay chưa ôn) cho tới ngày đầu tiên không có hoạt động.
    cursor = today if counts.get(today, 0) > 0 else today - datetime.timedelta(days=1)
    current = 0
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= datetime.timedelta(days=1)

    longest = run = 0
    for item in series:
        run = run + 1 if item["count"] > 0 else 0
        longest = max(longest, run)

    return {
        "days": series,
        "current_streak": current,
        "longest_streak": longest,
        "today_reviews": counts.get(today, 0),
        "today_cards": len(today_cards),
        "total_reviews": sum(counts.values())
    }

"""Trò chơi ôn từ vựng: chọn thẻ cho ván, ghi kết quả (điểm/sao/XP do máy chủ tính), cập nhật lịch ôn và thống kê.

Bảng `flashcard_game_sessions` (db/migrations/006_flashcard_games.sql). Chưa chạy migration -> 503 MIGRATION_REQUIRED.
"""
from __future__ import annotations

import datetime
import random
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.schemas.games import SubmitGameSessionRequest
from app.services import game_logic as logic
from app.services.flashcard_service import (
    build_distractors,
    get_deck_cards,
    get_deck_lang,
    get_supabase,
    review_card,
    to_valid_uuid,
)
from app.utils.errors import ApiError
from app.utils.languages import normalize_lang
from app.utils.logger import logger

PAGE = 1000
MAX_STAT_PAGES = 20  # tối đa 20.000 ván gần nhất khi tổng hợp thống kê
VN_TZ = datetime.timezone(datetime.timedelta(hours=7))
TABLE = "flashcard_game_sessions"


def _is_missing_table(exc: Exception) -> bool:
    text = str(exc).lower()
    return TABLE in text and ("does not exist" in text or "schema cache" in text or "could not find" in text)


def _db_error(exc: Exception) -> ApiError:
    text = str(exc).lower()
    if "flashcard_game_sessions_game_check" in text:  # ràng buộc game chưa có 'shooter'
        return ApiError(
            503, "MIGRATION_REQUIRED",
            "Cơ sở dữ liệu chưa chạy migration 007 (db/migrations/007_flashcard_game_shooter.sql). Hãy chạy migration rồi thử lại.",
        )
    if _is_missing_table(exc):
        return ApiError(
            503, "MIGRATION_REQUIRED",
            "Cơ sở dữ liệu chưa chạy migration 006 (db/migrations/006_flashcard_games.sql). Hãy chạy migration rồi thử lại.",
        )
    logger.error(f"Game service database error: {exc}")
    return ApiError(503, "DB_ERROR", "Không thể truy cập cơ sở dữ liệu. Vui lòng thử lại sau.")


def _require(user_id: str):
    supabase = get_supabase()
    uid = to_valid_uuid(user_id)
    if not supabase or not uid:
        raise ApiError(503, "DB_REQUIRED", "Trò chơi cần kết nối cơ sở dữ liệu và tài khoản hợp lệ.")
    return supabase, uid


def _check_game(game: str) -> None:
    if game not in logic.GAMES:
        raise ApiError(404, "GAME_NOT_FOUND", f"Không có trò chơi {game!r}.")


async def _deck_context(deck_id: str, user_id: str):
    """(thẻ của sổ, mã ngôn ngữ đã xác thực). Kiểm tra quyền sở hữu; ngôn ngữ do máy chủ lấy từ sổ, không tin client."""
    cards = await get_deck_cards(deck_id, user_id)
    lang = await get_deck_lang(deck_id)
    return cards, normalize_lang(lang)


# ---- Bộ thẻ cho một ván -----------------------------------------------------------------------------

async def get_game_cards(user_id: str, game: str, deck_id: str, count: Optional[int] = None) -> Dict[str, Any]:
    _check_game(game)
    cards, lang = await _deck_context(deck_id, user_id)
    min_required = logic.MIN_CARDS[game]
    want = max(1, min(count or logic.DEFAULT_COUNT[game], logic.MAX_COUNT[game]))
    now = datetime.datetime.now(datetime.timezone.utc)

    base = {"game": game, "deck_id": deck_id, "lang_code": lang, "min_required": min_required, "total_cards": len(cards)}
    reason = logic.unsupported_reason(game, lang)
    if reason:
        return {**base, "playable": False, "reason": reason, "cards": [], "due_count": 0}

    chosen = logic.select_cards(cards, game, lang, want, now)
    if len(chosen) < min_required:
        what = "từ đơn (3–14 chữ cái)" if game == "builder" else "thẻ có từ và nghĩa khác nhau"
        return {
            **base, "playable": False, "cards": [], "due_count": 0,
            "reason": f"Cần ít nhất {min_required} {what} trong sổ này để chơi (hiện có {len(chosen)}).",
        }

    payload = []
    for card in chosen:
        item = {
            "id": card.get("id"),
            "term": str(card.get("term")).strip(),
            "definition": str(card.get("definition")).strip(),
            "phonetic": card.get("phonetic"),
            "audio_url": card.get("audio_url"),
            "part_of_speech": card.get("part_of_speech"),
            "lang_code": lang,
            "is_due": logic.is_reviewable(card, now),
        }
        if game in ("speed", "shooter"):  # cả hai cần đáp án nhiễu (nghĩa của các từ khác)
            distractors = build_distractors(card, cards)
            if len(distractors) < 3:
                continue
            choices = distractors + [item["definition"]]
            random.shuffle(choices)
            item["choices"] = choices
        payload.append(item)

    if len(payload) < min_required:
        return {**base, "playable": False, "cards": [], "due_count": 0,
                "reason": "Sổ này chưa đủ nghĩa khác nhau để tạo đáp án nhiễu cho trò này."}
    return {**base, "playable": True, "reason": None, "cards": payload, "due_count": sum(1 for c in payload if c["is_due"])}


# ---- Ghi kết quả ván chơi ---------------------------------------------------------------------------

async def _find_by_request(supabase, uid: str, request_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = await run_in_threadpool(
            lambda: supabase.table(TABLE).select("*").eq("user_id", uid).eq("client_request_id", request_id).limit(1).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _db_error(exc) from exc
    return res.data[0] if res.data else None


async def _previous_best(supabase, uid: str, game: str, mode: str) -> int:
    try:
        res = await run_in_threadpool(
            lambda: supabase.table(TABLE).select("score").eq("user_id", uid).eq("game", game).eq("mode", mode)
                .order("score", desc=True).limit(1).execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise _db_error(exc) from exc
    return int(res.data[0]["score"]) if res.data else 0


def _public(row: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("id", "game", "mode", "deck_id", "lang_code", "total", "correct", "mistakes", "hints", "best_combo",
            "duration_ms", "score", "stars", "xp", "applied_review", "reviewed_count", "created_at")
    return {k: row.get(k) for k in keys}


async def submit_session(user_id: str, req: SubmitGameSessionRequest) -> Dict[str, Any]:
    supabase, uid = _require(user_id)
    cards, lang = await _deck_context(req.deck_id, user_id)
    if not lang:
        raise ApiError(409, "DECK_LANG_UNKNOWN", "Sổ này chưa có ngôn ngữ hợp lệ nên chưa ghi nhận điểm được.")
    reason = logic.unsupported_reason(req.game, lang)
    if reason:
        raise ApiError(422, "GAME_UNSUPPORTED_LANG", reason)

    existing = await _find_by_request(supabase, uid, req.client_request_id)
    if existing:  # gửi lại: trả kết quả cũ, KHÔNG chấm hay cập nhật lịch ôn lần nữa
        return {"session": _public(existing), "is_record": False, "idempotent_replay": True, "level": None}

    by_id = {str(c.get("id")): c for c in cards}
    items = [i.model_dump() for i in req.items if i.card_id in by_id]
    ignored = len(req.items) - len(items)
    if not items:
        raise ApiError(422, "GAME_EMPTY", "Kết quả ván chơi không chứa thẻ nào thuộc sổ này.")

    result = logic.score_session(req.game, req.mode, items, req.duration_ms)
    previous_best = await _previous_best(supabase, uid, req.game, req.mode)
    now = datetime.datetime.now(datetime.timezone.utc)
    plan = logic.review_plan(items, by_id, now) if req.apply_review else []

    row = {
        "user_id": uid,
        "deck_id": to_valid_uuid(req.deck_id),
        "lang_code": lang,
        "game": req.game,
        "mode": req.mode,
        "client_request_id": req.client_request_id,
        "duration_ms": req.duration_ms,
        "applied_review": bool(req.apply_review),
        "reviewed_count": 0,
        **result,
    }
    # Ghi ván TRƯỚC khi đổi lịch ôn: ghi lỗi thì không có tác dụng phụ; gửi lại sau đó cũng không đổi lịch ôn hai lần.
    try:
        inserted = await run_in_threadpool(lambda: supabase.table(TABLE).insert(row).execute())
    except Exception as exc:  # noqa: BLE001
        text = str(exc).lower()
        raced = await _find_by_request(supabase, uid, req.client_request_id) if ("duplicate" in text or "unique" in text) else None
        if raced:
            return {"session": _public(raced), "is_record": False, "idempotent_replay": True, "level": None}
        raise _db_error(exc) from exc
    saved = dict(inserted.data[0]) if inserted.data else dict(row)

    reviewed = 0
    for card_id, grade in plan:
        try:
            await review_card(card_id, grade, user_id)
            reviewed += 1
        except HTTPException as exc:
            logger.warning(f"Game review skipped for card {card_id}: {exc.detail}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Game review failed for card {card_id}: {exc}")
    if reviewed and saved.get("id"):
        try:
            await run_in_threadpool(lambda: supabase.table(TABLE).update({"reviewed_count": reviewed}).eq("id", saved["id"]).execute())
        except Exception as exc:  # noqa: BLE001 — chỉ là số liệu phụ
            logger.warning(f"Could not store reviewed_count: {exc}")
    saved["reviewed_count"] = reviewed

    stats = await get_game_stats(user_id)
    return {
        "session": _public(saved),
        "is_record": result["score"] > previous_best and result["score"] > 0,
        "previous_best": previous_best,
        "ignored_items": ignored,
        "review_eligible": len(plan),
        "idempotent_replay": False,
        "level": stats["level"],
    }


# ---- Thống kê ---------------------------------------------------------------------------------------

async def _all_sessions(supabase, uid: str) -> List[Dict[str, Any]]:
    cols = "game, mode, score, stars, xp, best_combo, lang_code, created_at, correct, total"
    rows: List[Dict[str, Any]] = []
    try:
        for page in range(MAX_STAT_PAGES):
            def build(o=page * PAGE):
                return (
                    supabase.table(TABLE).select(cols).eq("user_id", uid)
                    .order("created_at", desc=True).range(o, o + PAGE - 1).execute()
                )
            batch = (await run_in_threadpool(build)).data or []
            rows.extend(batch)
            if len(batch) < PAGE:
                break
    except Exception as exc:  # noqa: BLE001
        raise _db_error(exc) from exc
    return rows


def _vn_day(value: Any) -> str:
    try:
        dt = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    return (dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)).astimezone(VN_TZ).date().isoformat()


async def get_game_stats(user_id: str, lang_code: Optional[str] = None) -> Dict[str, Any]:
    """XP/cấp độ tính trên MỌI ván của người dùng; kỷ lục và số ván có thể lọc theo ngôn ngữ."""
    supabase, uid = _require(user_id)
    lang = None
    if lang_code:
        lang = normalize_lang(lang_code)
        if not lang:
            raise ApiError(422, "LANG_UNSUPPORTED", "Ngôn ngữ không được hỗ trợ.")

    everything = await _all_sessions(supabase, uid)
    scoped = [r for r in everything if not lang or r.get("lang_code") == lang]
    today = datetime.datetime.now(VN_TZ).date().isoformat()

    games: Dict[str, Dict[str, Any]] = {}
    for g in logic.GAMES:
        entry: Dict[str, Any] = {"plays": 0, "best": {}, "last_played": None}
        for mode in logic.MODES:
            rows = [r for r in scoped if r["game"] == g and r["mode"] == mode]
            best = max(rows, key=lambda r: (int(r["score"]), str(r["created_at"])), default=None)
            entry["best"][mode] = (
                {"score": int(best["score"]), "stars": int(best["stars"]), "best_combo": int(best.get("best_combo") or 0)}
                if best else None
            )
            entry["plays"] += len(rows)
        played = [str(r["created_at"]) for r in scoped if r["game"] == g]
        entry["last_played"] = max(played) if played else None
        games[g] = entry

    return {
        "lang_code": lang,
        "level": logic.level_for_xp(sum(int(r.get("xp") or 0) for r in everything)),
        "games": games,
        "plays_total": len(scoped),
        "plays_today": sum(1 for r in scoped if _vn_day(r.get("created_at")) == today),
    }

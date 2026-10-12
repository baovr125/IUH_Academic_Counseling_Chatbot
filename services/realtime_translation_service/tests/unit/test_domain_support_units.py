"""Unit test bổ sung (đợt benchmark/unit test 2026-10-10) cho các phần chưa có test của chế độ chuyên ngành:
nạp từ điển (Redis/Supabase, phân trang), chỉ mục theo phiên bản, đồng bộ Redis, cache kết quả domain,
định tuyến /text sang luồng chuyên ngành và biến thể từ của tra cứu chính xác.
Mọi dependency ngoài (Redis, Supabase, LLM, NLLB) đều được mock.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import cache_service, domain_index
from app.services.domain_index import DomainIndex, _variants

IT = "Công nghệ Thông tin (IT)"
ROWS = [{"domain": IT, "word": "memory leak", "translation": "rò rỉ bộ nhớ"}]


# --------------------------------------------------------------------------- get_all_dictionaries
def _supabase_with_pages(pages):
    """Supabase giả: mỗi lần .execute() trả trang kế tiếp; ghi lại các lời gọi .range()."""
    client = MagicMock()
    query = client.table.return_value.select.return_value.order.return_value.order.return_value
    calls = []

    def range_(start, end):
        calls.append((start, end))
        res = MagicMock()
        res.execute.return_value = MagicMock(data=pages[len(calls) - 1])
        return res

    query.range.side_effect = range_
    return client, calls


class TestGetAllDictionaries:
    @pytest.mark.asyncio
    async def test_returns_redis_cache_without_touching_supabase(self):
        from app.services import domain_service

        redis = MagicMock()
        redis.get.return_value = json.dumps(ROWS)
        with patch("app.services.cache_service.get_redis", return_value=redis), \
             patch("app.services.cache_service.get_global_dict_version", return_value=7), \
             patch("app.services.domain_service.get_supabase") as supa:
            rows = await domain_service.get_all_dictionaries()
        assert rows == ROWS
        redis.get.assert_called_once_with("all_domain_dictionaries_v7")
        supa.assert_not_called()

    @pytest.mark.asyncio
    async def test_paginates_supabase_beyond_1000_rows_and_caches_result(self):
        from app.services import domain_service

        page1 = [{"domain": IT, "word": f"w{i}", "translation": "t"} for i in range(1000)]
        page2 = [{"domain": IT, "word": "last", "translation": "t"}]
        client, calls = _supabase_with_pages([page1, page2])
        redis = MagicMock()
        redis.get.return_value = None
        with patch("app.services.cache_service.get_redis", return_value=redis), \
             patch("app.services.cache_service.get_global_dict_version", return_value=3), \
             patch("app.services.domain_service.get_supabase", return_value=client):
            rows = await domain_service.get_all_dictionaries()
        assert len(rows) == 1001  # trước giai đoạn 9: bị cắt ở 1.000 hàng
        assert calls == [(0, 999), (1000, 1999)]
        key, ttl, payload = redis.setex.call_args.args
        assert key == "all_domain_dictionaries_v3" and ttl == 300 and len(json.loads(payload)) == 1001

    @pytest.mark.asyncio
    async def test_supabase_error_returns_empty_list(self):
        from app.services import domain_service

        client = MagicMock()
        client.table.side_effect = RuntimeError("supabase down")
        with patch("app.services.cache_service.get_redis", return_value=None), \
             patch("app.services.cache_service.get_global_dict_version", return_value=1), \
             patch("app.services.domain_service.get_supabase", return_value=client):
            assert await domain_service.get_all_dictionaries() == []

    @pytest.mark.asyncio
    async def test_no_supabase_and_no_redis_returns_empty_list(self):
        from app.services import domain_service

        with patch("app.services.cache_service.get_redis", return_value=None), \
             patch("app.services.cache_service.get_global_dict_version", return_value=1), \
             patch("app.services.domain_service.get_supabase", return_value=None):
            assert await domain_service.get_all_dictionaries() == []


# --------------------------------------------------------------------------- get_index
class TestGetIndex:
    def setup_method(self):
        domain_index.reset_index_cache()

    def teardown_method(self):
        domain_index.reset_index_cache()

    @pytest.mark.asyncio
    async def test_reuses_index_while_dictionary_version_is_unchanged(self):
        fetch = AsyncMock(return_value=ROWS)
        with patch("app.services.cache_service.get_global_dict_version", return_value=1), \
             patch("app.services.domain_service.get_all_dictionaries", fetch):
            a = await domain_index.get_index()
            b = await domain_index.get_index()
        assert a is b and fetch.await_count == 1

    @pytest.mark.asyncio
    async def test_rebuilds_when_dictionary_version_changes(self):
        fetch = AsyncMock(side_effect=[ROWS, ROWS + [{"domain": IT, "word": "deadlock", "translation": "bế tắc"}]])
        version = MagicMock(side_effect=[1, 2])
        with patch("app.services.cache_service.get_global_dict_version", version), \
             patch("app.services.domain_service.get_all_dictionaries", fetch):
            first = await domain_index.get_index()
            second = await domain_index.get_index()
        assert len(first.entries) == 1 and len(second.entries) == 2

    @pytest.mark.asyncio
    async def test_keeps_previous_index_when_fetch_temporarily_returns_nothing(self):
        fetch = AsyncMock(side_effect=[ROWS, []])
        version = MagicMock(side_effect=[1, 2])
        with patch("app.services.cache_service.get_global_dict_version", version), \
             patch("app.services.domain_service.get_all_dictionaries", fetch):
            first = await domain_index.get_index()
            second = await domain_index.get_index()
        assert second is first and len(second.entries) == 1

    @pytest.mark.asyncio
    async def test_empty_dictionary_gives_empty_index(self):
        with patch("app.services.cache_service.get_global_dict_version", return_value=1), \
             patch("app.services.domain_service.get_all_dictionaries", AsyncMock(return_value=[])):
            idx = await domain_index.get_index()
        assert idx.entries == [] and idx.max_words == 0 and idx.exact("memory leak") == []


# --------------------------------------------------------------------------- _variants
class TestVariants:
    @pytest.mark.parametrize("phrase,expected", [
        ("queries", "query"),
        ("caches", "cache"),
        ("boxes", "box"),
        ("leaks", "leak"),
        ("deployed", "deploy"),
        ("cached", "cache"),
        ("caching", "cache"),
        ("tokenizing", "tokenize"),
        ("memory leaks", "memory leak"),
    ])
    def test_last_word_inflections_are_reduced(self, phrase, expected):
        assert expected in _variants(phrase)

    def test_short_words_are_not_stripped(self):
        assert _variants("bus") == ["bus"]
        assert _variants("red") == ["red"]

    def test_original_phrase_is_always_first(self):
        assert _variants("tokens")[0] == "tokens"


# --------------------------------------------------------------------------- sync_dictionary_to_redis
class TestSyncDictionaryToRedis:
    def test_writes_one_hash_per_domain_and_clears_versioned_cache_keys(self):
        from app.services import domain_dict_service

        supa = MagicMock()
        supa.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
            {"domain": IT, "word": "Memory Leak", "translation": "rò rỉ bộ nhớ"},
            {"domain": "Marketing", "word": "bounce rate", "translation": "tỷ lệ thoát"},
        ])
        redis = MagicMock()
        redis.scan_iter.return_value = iter(["all_domain_dictionaries_v4", "all_domain_dictionaries_v5"])
        pipe = redis.pipeline.return_value
        with patch("app.services.domain_dict_service.get_supabase", return_value=supa), \
             patch("app.services.domain_dict_service.get_redis", return_value=redis):
            domain_dict_service.sync_dictionary_to_redis()
        pipe.hset.assert_any_call(f"domain_dict:{IT}", mapping={"memory leak": "rò rỉ bộ nhớ"})
        pipe.hset.assert_any_call("domain_dict:Marketing", mapping={"bounce rate": "tỷ lệ thoát"})
        deleted = [c.args[0] for c in pipe.delete.call_args_list]
        # Hồi quy: trước đây xóa key "all_domain_dictionaries" (không version) trong khi code đọc key có version.
        assert "all_domain_dictionaries_v4" in deleted and "all_domain_dictionaries_v5" in deleted
        redis.scan_iter.assert_called_once_with("all_domain_dictionaries*")
        pipe.execute.assert_called_once()

    def test_does_nothing_without_supabase(self):
        from app.services import domain_dict_service

        with patch("app.services.domain_dict_service.get_supabase", return_value=None), \
             patch("app.services.domain_dict_service.get_redis") as get_redis:
            domain_dict_service.sync_dictionary_to_redis()
        get_redis.assert_not_called()


# --------------------------------------------------------------------------- cache_service
class TestDomainResultCache:
    def test_round_trip_keeps_unicode_and_structure(self):
        store = {}
        redis = MagicMock()
        redis.setex.side_effect = lambda k, ttl, v: store.__setitem__(k, v)
        redis.get.side_effect = lambda k: store.get(k)
        value = {"text": "Rò rỉ bộ nhớ", "domain": {"status": "detected"}, "warnings": []}
        with patch("app.services.cache_service.get_redis", return_value=redis):
            cache_service.set_cached_domain_result("k1", value, ttl=60)
            assert cache_service.get_cached_domain_result("k1") == value
        assert redis.setex.call_args.args[:2] == ("domtrans:k1", 60)
        assert "Rò rỉ" in redis.setex.call_args.args[2]  # ensure_ascii=False

    def test_missing_key_or_no_redis_returns_none(self):
        redis = MagicMock()
        redis.get.return_value = None
        with patch("app.services.cache_service.get_redis", return_value=redis):
            assert cache_service.get_cached_domain_result("nope") is None
        with patch("app.services.cache_service.get_redis", return_value=None):
            assert cache_service.get_cached_domain_result("nope") is None

    def test_redis_errors_are_swallowed(self):
        redis = MagicMock()
        redis.get.side_effect = RuntimeError("boom")
        redis.setex.side_effect = RuntimeError("boom")
        with patch("app.services.cache_service.get_redis", return_value=redis):
            assert cache_service.get_cached_domain_result("k") is None
            cache_service.set_cached_domain_result("k", {"text": "x"})  # không ném lỗi

    def test_corrupted_json_returns_none(self):
        redis = MagicMock()
        redis.get.return_value = "{không phải json"
        with patch("app.services.cache_service.get_redis", return_value=redis):
            assert cache_service.get_cached_domain_result("k") is None

    def test_domain_version_rules(self):
        redis = MagicMock()
        redis.get.side_effect = lambda k: {"global_dict_ver": "9", f"domain_ver:{IT}": "4"}.get(k)
        with patch("app.services.cache_service.get_redis", return_value=redis):
            assert cache_service.get_domain_version("auto") == 9          # auto dùng version toàn cục
            assert cache_service.get_domain_version(IT) == 4
            assert cache_service.get_domain_version("Marketing") == 1     # chưa có key -> 1
            assert cache_service.get_domain_version("Dịch thông thường (Mặc định)") == 0
        with patch("app.services.cache_service.get_redis", return_value=None):
            assert cache_service.get_domain_version(IT) == 0

    def test_translation_hash_is_case_sensitive_and_nfc_normalized(self):
        h = cache_service.get_translation_text_hash
        assert h("IT") != h("it")
        assert h("Tiếng Việt") == h("Tiếng Việt")  # NFD -> NFC
        assert h("  memory leak ") == h("memory leak")


# --------------------------------------------------------------------------- translation_service (định tuyến /text)
class TestTranslateDomainText:
    @pytest.mark.asyncio
    async def test_legacy_warning_prefers_non_info_and_is_none_without_warnings(self):
        from app.services import translation_service

        base = {"text": "x", "domain": {"status": "unknown"}, "cached": False, "error": None}
        with patch("app.services.domain_translation.collect_domain_translation",
                   AsyncMock(return_value={**base, "warnings": []})):
            res = await translation_service.translate_domain_text("x", "en", "vi", "auto", 0.0, None, None)
        assert res[3] is None and res[7] == []
        warns = [{"code": "A", "severity": "info", "message": "i"}, {"code": "B", "severity": "warning", "message": "w"}]
        with patch("app.services.domain_translation.collect_domain_translation",
                   AsyncMock(return_value={**base, "warnings": warns})):
            res = await translation_service.translate_domain_text("x", "en", "vi", "auto", 0.0, None, None)
        assert res[3] == "w"

    @pytest.mark.asyncio
    async def test_error_becomes_http_503(self):
        from app.services import translation_service

        result = {"text": "", "domain": None, "warnings": [], "cached": False,
                  "error": {"error": "Không thể dịch lúc này. Vui lòng thử lại sau.", "code": "TRANSLATION_UNAVAILABLE"}}
        with patch("app.services.domain_translation.collect_domain_translation", AsyncMock(return_value=result)):
            with pytest.raises(HTTPException) as err:
                await translation_service.translate_domain_text("x", "en", "vi", "auto", 0.0, None, None)
        assert err.value.status_code == 503

    @pytest.mark.asyncio
    async def test_translate_text_routes_domain_mode_away_from_nllb(self):
        from app.services import translation_service

        resolution = MagicMock(should_translate=True, source_lang="en", details=None)
        routed = AsyncMock(return_value=("bản dịch", False, 1.0, None, None, None, {"status": "selected"}, []))
        with patch("app.services.translation_service.aresolve_source_language", AsyncMock(return_value=resolution)), \
             patch("app.services.translation_service.translate_domain_text", routed), \
             patch("app.services.translation_service.get_nllb_translator") as nllb:
            res = await translation_service.translate_text("hello", "en", "vi", domain="Marketing")
        routed.assert_awaited_once()
        nllb.assert_not_called()
        assert res[0] == "bản dịch" and len(res) == 8

    @pytest.mark.asyncio
    async def test_default_label_stays_in_normal_flow(self):
        from app.services import translation_service

        resolution = MagicMock(should_translate=True, source_lang="en", details=None)
        routed = AsyncMock()
        with patch("app.services.translation_service.aresolve_source_language", AsyncMock(return_value=resolution)), \
             patch("app.services.translation_service.translate_domain_text", routed), \
             patch("app.services.translation_service.get_cached_translation", return_value="cached"), \
             patch("app.services.translation_service.get_domain_version", return_value=0), \
             patch("app.services.cache_service.get_cached_warning", return_value=None):
            res = await translation_service.translate_text("hello", "en", "vi", domain="Dịch thông thường (Mặc định)")
        routed.assert_not_awaited()
        assert res[0] == "cached" and res[1] is True


# --------------------------------------------------------------------------- llm_service wrapper
class TestStreamWrapper:
    @pytest.mark.asyncio
    async def test_internal_events_are_not_sent_to_client(self):
        from app.services.llm_service import handle_flow_2_stream_translation

        async def fake(text, src, tgt, domain):
            yield {"_internal": "cache_hit"}
            yield {"event": "domain", "domain": {"status": "selected"}}
            yield {"text": "Xin chào"}

        with patch("app.services.domain_translation.translate_with_domain", fake):
            chunks = [json.loads(c) async for c in handle_flow_2_stream_translation("hi", "en", "vi", IT)]
        assert chunks == [{"event": "domain", "domain": {"status": "selected"}}, {"text": "Xin chào"}]

    @pytest.mark.asyncio
    async def test_vietnamese_is_not_ascii_escaped_in_sse_payload(self):
        from app.services.llm_service import handle_flow_2_stream_translation

        async def fake(text, src, tgt, domain):
            yield {"text": "Rò rỉ"}

        with patch("app.services.domain_translation.translate_with_domain", fake):
            raw = [c async for c in handle_flow_2_stream_translation("hi", "en", "vi", IT)]
        assert raw == ['{"text": "Rò rỉ"}']

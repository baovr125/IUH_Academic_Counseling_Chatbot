import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from app.services.llm_generation_service import parse_self_reflection
from app.services.rag_service import get_adaptive_candidate_count
from app.services.log_utils import _write_full_log


class TestSelfRAGReflectionParsing:
    def test_parse_self_reflection_full_grounded(self):
        sample_output = (
            "<thinking>\n"
            "<doc_relevance>YES</doc_relevance>\n"
            "<conflict_detected>NO</conflict_detected>\n"
            "<answer_confidence>HIGH</answer_confidence>\n"
            "Analyzing student query...\n"
            "</thinking>\n"
            "Chào bạn, theo quy chế IUH..."
        )
        res = parse_self_reflection(sample_output)
        assert res["doc_relevance"] == "YES"
        assert res["conflict_detected"] == "NO"
        assert res["answer_confidence"] == "HIGH"

    def test_parse_self_reflection_conflict_and_partial(self):
        sample_output = (
            "<thinking>\n"
            "<doc_relevance>PARTIAL</doc_relevance>\n"
            "<conflict_detected>YES</conflict_detected>\n"
            "<answer_confidence>PARTIAL</answer_confidence>\n"
            "</thinking>\n"
            "Chào bạn..."
        )
        res = parse_self_reflection(sample_output)
        assert res["doc_relevance"] == "PARTIAL"
        assert res["conflict_detected"] == "YES"
        assert res["answer_confidence"] == "PARTIAL"

    def test_parse_self_reflection_no_relevance_refusal(self):
        sample_output = (
            "<thinking>\n"
            "<doc_relevance>NO</doc_relevance>\n"
            "<conflict_detected>NO</conflict_detected>\n"
            "<answer_confidence>NONE</answer_confidence>\n"
            "</thinking>\n"
            "Hiện tại mình chưa tìm thấy thông tin chính thức trong CSDL..."
        )
        res = parse_self_reflection(sample_output)
        assert res["doc_relevance"] == "NO"
        assert res["conflict_detected"] == "NO"
        assert res["answer_confidence"] == "NONE"

    def test_parse_self_reflection_missing_or_malformed(self):
        assert parse_self_reflection("") == {
            "doc_relevance": "UNKNOWN",
            "conflict_detected": "UNKNOWN",
            "answer_confidence": "UNKNOWN",
        }
        assert parse_self_reflection(None) == {
            "doc_relevance": "UNKNOWN",
            "conflict_detected": "UNKNOWN",
            "answer_confidence": "UNKNOWN",
        }
        assert parse_self_reflection("Chào bạn, không có thẻ thinking.") == {
            "doc_relevance": "UNKNOWN",
            "conflict_detected": "UNKNOWN",
            "answer_confidence": "UNKNOWN",
        }


class TestSelfRAGDynamicCandidateCount:
    def test_adaptive_candidate_count_boundaries(self):
        # High confidence -> reduce candidate count to save reranker latency
        assert get_adaptive_candidate_count(0.95) == 30
        assert get_adaptive_candidate_count(0.80) == 30

        # Moderate confidence -> balanced count
        assert get_adaptive_candidate_count(0.79) == 50
        assert get_adaptive_candidate_count(0.50) == 50

        # Low confidence / uncertain -> expand candidate count to boost recall
        assert get_adaptive_candidate_count(0.49) == 70
        assert get_adaptive_candidate_count(0.10) == 70
        assert get_adaptive_candidate_count(0.0) == 70


from app.services.rag_service import async_cache_writeback


class TestSelfRAGCacheGatingLogic:
    @pytest.mark.asyncio
    async def test_cache_writeback_skipped_when_low_score(self):
        with patch("app.services.rag_service.get_redis") as mock_redis:
            await async_cache_writeback("câu hỏi?", "Câu trả lời hợp lệ dài hơn ba mươi ký tự...", top_doc_score=0.10)
            mock_redis.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_writeback_skipped_when_doc_relevance_no(self):
        with patch("app.services.rag_service.get_redis") as mock_redis:
            ans = "<thinking><doc_relevance>NO</doc_relevance><answer_confidence>HIGH</answer_confidence></thinking>Mình chưa tìm thấy thông tin..."
            await async_cache_writeback("câu hỏi?", ans, top_doc_score=0.85)
            mock_redis.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_writeback_skipped_when_confidence_not_high(self):
        with patch("app.services.rag_service.get_redis") as mock_redis:
            ans = "<thinking><doc_relevance>YES</doc_relevance><answer_confidence>PARTIAL</answer_confidence></thinking>Thông tin có thể là..."
            await async_cache_writeback("câu hỏi?", ans, top_doc_score=0.85)
            mock_redis.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_writeback_proceeds_when_grounded(self):
        from unittest.mock import AsyncMock
        with patch("app.services.rag_service.get_redis") as mock_redis, \
             patch("app.services.rag_service.get_supabase_client") as mock_sb:
            mock_r = MagicMock()
            mock_redis.return_value = mock_r
            mock_r.setex = AsyncMock()
            mock_sb.return_value = None  # Stop before DB insert
            ans = "<thinking><doc_relevance>YES</doc_relevance><answer_confidence>HIGH</answer_confidence></thinking>Theo quy chế đào tạo IUH điều 15..."
            await async_cache_writeback("câu hỏi?", ans, top_doc_score=0.85, query_embedding=[0.1]*768)
            mock_redis.assert_called_once()


class TestSelfRAGConflictAuditing:
    def test_conflict_detection_writes_to_log(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LOG_DIR", str(tmp_path))
        refl_conflict = {
            "doc_relevance": "YES",
            "conflict_detected": "YES",
            "answer_confidence": "PARTIAL",
        }
        log_path = _write_full_log(
            session_id="test-session-conflict",
            original_query="Hạn nộp học phí kỳ 2?",
            rewritten_query="hạn nộp học phí học kỳ 2",
            chunks=[{"content": "Chunk 1: Hạn 20/01", "rerank_score": 0.88}],
            past_memories=[],
            retrieval_latency_ms=120,
            rewrite_latency_ms=80,
            llm_latency_ms=250,
            prompt_tokens=200,
            completion_tokens=80,
            ai_answer="<thinking><conflict_detected>YES</conflict_detected></thinking>Thông tin có sự mâu thuẫn giữa 2 quyết định...",
            self_reflection=refl_conflict,
        )
        assert os.path.exists(log_path)
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Self-RAG Reflection" in content
        assert "**Conflict Detected:** `YES`" in content
        assert "MÂU THUẪN QUY CHẾ (CF-RAG)" in content

        # Check that conflict audit file was appended in conflicts dir
        conflict_dir = tmp_path / "conflicts"
        assert conflict_dir.exists()
        conflict_files = list(conflict_dir.glob("*.md"))
        assert len(conflict_files) == 1
        with open(conflict_files[0], "r", encoding="utf-8") as cf:
            cf_content = cf.read()
        assert "test-session-conflict" in cf_content
        assert "Hạn nộp học phí kỳ 2?" in cf_content

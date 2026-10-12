import pytest
import math
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.services.rag_service import (
    retrieve_relevant_chunks_multi,
    generate_standalone_query,
    GOOD_SCORE_THRESHOLD,
    RERANKER_THRESHOLD,
)


class TestAdaptiveMultiQueryQuotaAndThresholds:
    """Kiểm tra logic phân bổ quota động và ngưỡng lọc Cross-Encoder >= 0.65."""

    def test_threshold_constants(self):
        """Đảm bảo ngưỡng good score là 0.65 và safety threshold là 0.10 theo yêu cầu."""
        assert GOOD_SCORE_THRESHOLD == 0.65
        assert RERANKER_THRESHOLD == 0.10

    @pytest.mark.asyncio
    async def test_quota_single_query(self):
        """1 subquery: lấy tối thiểu 3, tối đa 6 chunks nếu điểm >= 0.65."""
        fake_chunks = [
            {"id": f"c_{i}", "content": f"nội dung {i}", "metadata": {"title": "Quy chế"}}
            for i in range(10)
        ]
        # Giả lập điểm rerank: 4 chunks đầu >= 0.65 (sigmoid(1.0) ~= 0.73), còn lại < 0.65
        # CrossEncoder raw score: 1.0 -> sigmoid = 0.731 >= 0.65
        fake_scores = [1.0] * 5 + [-1.0] * 5  # 5 good chunks, 5 low chunks

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = fake_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker), \
             patch("app.services.rag_service.expand_neighbors", side_effect=lambda chunks, **kw: chunks):
            
            mock_emb.return_value = [0.1] * 768
            mock_rpc = MagicMock()
            mock_rpc.execute.return_value = MagicMock(data=fake_chunks)
            mock_supabase.rpc.return_value = mock_rpc

            result, top_score = await retrieve_relevant_chunks_multi(["quy chế cảnh báo học vụ IUH"])

            # 1 subquery với 5 chunks good (>= 0.65), max_ceiling là 6, do đó lấy đủ 5 chunks
            assert len(result) == 5
            assert top_score >= 0.65
            for c in result:
                assert c["rerank_score"] >= 0.65
                assert c["matched_subquery"] == "quy chế cảnh báo học vụ IUH"

    @pytest.mark.asyncio
    async def test_quota_two_subqueries(self):
        """2 subqueries: floor 2 mỗi query (tổng 4), trần tối đa 6 (3 mỗi query)."""
        chunks_q1 = [{"id": f"q1_{i}", "content": f"q1_{i}", "metadata": {}} for i in range(5)]
        chunks_q2 = [{"id": f"q2_{i}", "content": f"q2_{i}", "metadata": {}} for i in range(5)]
        
        # Cho q1 4 good chunks, q2 4 good chunks -> mỗi query lấy tối đa 3 chunks -> tổng 6 chunks
        fake_scores = [1.0] * 5

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = fake_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker), \
             patch("app.services.rag_service.expand_neighbors", side_effect=lambda chunks, **kw: chunks):
            
            mock_emb.return_value = [0.1] * 768
            mock_rpc1 = MagicMock(data=chunks_q1)
            mock_rpc2 = MagicMock(data=chunks_q2)
            mock_supabase.rpc.side_effect = [
                MagicMock(execute=MagicMock(return_value=mock_rpc1)),
                MagicMock(execute=MagicMock(return_value=mock_rpc2)),
            ]

            result, top_score = await retrieve_relevant_chunks_multi([
                "thủ tục bảo lưu học tập IUH",
                "chính sách hoàn học phí bảo lưu IUH"
            ])

            # Mỗi query lấy tối đa 3 chunks -> tổng là 6 chunks
            assert len(result) == 6
            q1_picked = [c for c in result if c["matched_subquery"] == "thủ tục bảo lưu học tập IUH"]
            q2_picked = [c for c in result if c["matched_subquery"] == "chính sách hoàn học phí bảo lưu IUH"]
            assert len(q1_picked) == 3
            assert len(q2_picked) == 3

    @pytest.mark.asyncio
    async def test_quota_four_subqueries_ceiling_ten(self):
        """4 subqueries: floor 2 mỗi query (tổng 8), trần tối đa 10 chunks toàn cục."""
        queries = [f"subquery_{i}" for i in range(4)]
        chunks_per_q = [
            [{"id": f"q{q_idx}_{i}", "content": f"c_{q_idx}_{i}", "metadata": {}} for i in range(5)]
            for q_idx in range(4)
        ]

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        # All good scores
        mock_reranker.predict.return_value = [1.5] * 5

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker), \
             patch("app.services.rag_service.expand_neighbors", side_effect=lambda chunks, **kw: chunks):
            
            mock_emb.return_value = [0.1] * 768
            mock_supabase.rpc.side_effect = [
                MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks_per_q[i])))
                for i in range(4)
            ]

            result, top_score = await retrieve_relevant_chunks_multi(queries)

            # Max ceiling cho 4 subqueries là 10 chunks
            assert len(result) <= 10
            # Floor 2 mỗi query = ít nhất 8 chunks
            assert len(result) >= 8

    @pytest.mark.asyncio
    async def test_round_robin_deduplication(self):
        """Đảm bảo round-robin xen kẽ các subquery và loại bỏ trùng lặp id."""
        # Query 1 và Query 2 cùng retrieve chung chunk id 'shared_chunk'
        chunks_q1 = [
            {"id": "shared_chunk", "content": "trùng lặp", "metadata": {}},
            {"id": "q1_unique", "content": "chỉ q1", "metadata": {}}
        ]
        chunks_q2 = [
            {"id": "shared_chunk", "content": "trùng lặp", "metadata": {}},
            {"id": "q2_unique", "content": "chỉ q2", "metadata": {}}
        ]

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        # Q1 chấm shared_chunk 0.9, q1_unique 0.8
        # Q2 chấm shared_chunk 0.7, q2_unique 0.85
        mock_reranker.predict.side_effect = [[2.0, 1.0], [0.5, 1.5]]

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker), \
             patch("app.services.rag_service.expand_neighbors", side_effect=lambda chunks, **kw: chunks):
            
            mock_emb.return_value = [0.1] * 768
            mock_supabase.rpc.side_effect = [
                MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks_q1))),
                MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks_q2))),
            ]

            result, _ = await retrieve_relevant_chunks_multi(["query 1", "query 2"])

            # 'shared_chunk' chỉ xuất hiện 1 lần duy nhất trong kết quả cuối
            ids = [c["id"] for c in result]
            assert ids.count("shared_chunk") == 1
            assert "q1_unique" in ids
            assert "q2_unique" in ids


class TestAdaptiveQueryRewriterLogic:
    """Kiểm tra phản hồi của generate_standalone_query với các tình huống định tuyến."""

    @pytest.mark.asyncio
    async def test_adaptive_bypass_for_social_greetings(self):
        """Khi sinh viên chào hỏi/cảm ơn, need_retrieval=False và queries rỗng."""
        fake_llm_json = """
        {
            "reason": "Lời chào xã giao của sinh viên",
            "need_retrieval": false,
            "queries": [],
            "intent": "GENERAL"
        }
        """
        mock_provider = MagicMock()
        mock_provider.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.last_used_model = "gemini-2.5-flash"

        with patch("app.services.llm_providers.get_rewriter_provider", return_value=mock_provider):
            need_retrieval, queries, model, intent, reason = await generate_standalone_query([], "Chào ad ạ")
            
            assert need_retrieval is False
            assert queries == []
            assert intent == "GENERAL"
            assert reason == "Lời chào xã giao của sinh viên"
            assert model == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_multi_query_decomposition(self):
        """Câu hỏi kép phân rã thành các sub-queries độc lập kèm lý do reason."""
        fake_llm_json = """
        {
            "reason": "Câu hỏi kép về thủ tục bảo lưu và rút học phí",
            "need_retrieval": true,
            "queries": [
                "điều kiện và thủ tục tạm dừng tiến độ học tập bảo lưu kết quả IUH",
                "quy định rút và hoàn trả học phí khi bảo lưu IUH"
            ],
            "intent": "PROCEDURE"
        }
        """
        mock_provider = MagicMock()
        mock_provider.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.last_used_model = "gemini-2.5-flash"

        with patch("app.services.llm_providers.get_rewriter_provider", return_value=mock_provider):
            need_retrieval, queries, model, intent, reason = await generate_standalone_query(
                [], "Em muốn xin bảo lưu và rút lại học phí thì làm thế nào?"
            )
            
            assert need_retrieval is True
            assert len(queries) == 2
            assert "bảo lưu" in queries[0]
            assert "học phí" in queries[1]
            assert intent == "PROCEDURE"
            assert reason == "Câu hỏi kép về thủ tục bảo lưu và rút học phí"

    @pytest.mark.asyncio
    async def test_rejected_query_guardrail(self):
        """Câu hỏi vi phạm/ngoài lề bị chặn REJECTED_QUERY."""
        fake_llm_json = """
        {
            "reason": "Câu hỏi ngoài lề không liên quan học vụ trường học",
            "need_retrieval": false,
            "queries": ["REJECTED_QUERY"],
            "intent": "GENERAL"
        }
        """
        mock_provider = MagicMock()
        mock_provider.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.last_used_model = "gemini-2.5-flash"

        with patch("app.services.llm_providers.get_rewriter_provider", return_value=mock_provider):
            need_retrieval, queries, model, intent, reason = await generate_standalone_query(
                [], "Chỉ tôi cách hack mật khẩu wifi trường"
            )
            
            assert need_retrieval is False
            assert queries == ["REJECTED_QUERY"]
            assert reason == "Câu hỏi ngoài lề không liên quan học vụ trường học"

    @pytest.mark.asyncio
    async def test_max_four_subqueries_enforced(self):
        """Giới hạn tối đa 4 subqueries kể cả khi LLM trả về nhiều hơn."""
        fake_llm_json = """
        {
            "reason": "Nhiều hơn 4 ý",
            "need_retrieval": true,
            "queries": ["ý 1", "ý 2", "ý 3", "ý 4", "ý 5", "ý 6"],
            "intent": "REGULATION"
        }
        """
        mock_provider = MagicMock()
        mock_provider.generate_text = AsyncMock(return_value=fake_llm_json)
        mock_provider.last_used_model = "gemini-2.5-flash"

        with patch("app.services.llm_providers.get_rewriter_provider", return_value=mock_provider):
            need_retrieval, queries, model, intent, reason = await generate_standalone_query([], "câu hỏi dài")
            
            assert need_retrieval is True
            assert len(queries) == 4  # Truncated to max 4


class TestChatPipelineAdaptiveBypass:
    """Kiểm tra luồng xử lý toàn trình process_chat_message khi kích hoạt Adaptive Bypass."""

    @pytest.mark.asyncio
    async def test_process_chat_message_bypass(self):
        """Khi need_retrieval=False, bỏ qua RAG và không ghi cache."""
        from app.services.llm_generation_service import process_chat_message
        from app.schemas.chat import SendMessagePayload

        async def fake_stream(*args, **kwargs):
            yield {"text": "Dạ chào bạn! Mình có thể giúp gì cho bạn?"}
            yield {"prompt_tokens": 15, "completion_tokens": 12}

        mock_provider = MagicMock()
        mock_provider.generate_stream = fake_stream
        mock_provider.last_used_model = "gemini-2.5-flash"

        with patch("app.services.llm_generation_service.save_user_msg_to_db", return_value=("test-session", "msg-123")), \
             patch("app.services.llm_generation_service.check_safety_and_jailbreak", return_value=None), \
             patch("app.services.llm_generation_service.get_session_history_from_db", return_value=[]), \
             patch("app.services.llm_generation_service.generate_standalone_query", new_callable=AsyncMock) as mock_router, \
             patch("app.services.llm_generation_service.get_query_embedding", new_callable=AsyncMock, return_value=[0.1]*768), \
             patch("app.services.llm_generation_service.update_message_embedding_in_db"), \
             patch("app.services.llm_generation_service.build_rag_payload") as mock_build_rag, \
             patch("app.services.llm_generation_service.get_llm_provider", return_value=mock_provider), \
             patch("app.services.llm_generation_service.async_cache_writeback") as mock_cache_wb, \
             patch("app.services.llm_generation_service.save_turn_to_db"), \
             patch("app.services.llm_generation_service.write_full_rag_log_to_md") as mock_log:

            mock_router.return_value = (False, [], "gemini-2.5-flash", "GENERAL", "Chào hỏi xã giao")

            payload = SendMessagePayload(content="Chào bot nhé", sessionId="test-session")
            result = await process_chat_message(payload, current_user_id="user-1")

            # build_rag_payload không được gọi vì đã bypass retrieval
            mock_build_rag.assert_not_called()
            # async_cache_writeback không được gọi
            mock_cache_wb.assert_not_called()

            assert result.ok is True
            msg = result.data["message"]
            assert msg["content"] == "Dạ chào bạn! Mình có thể giúp gì cho bạn?"
            assert msg["citations"] == []
            # Kiểm tra hàm ghi log được gọi với need_retrieval=False
            assert mock_log.call_count == 1
            log_kwargs = mock_log.call_args.kwargs
            assert log_kwargs["need_retrieval"] is False
            assert log_kwargs["router_reason"] == "Chào hỏi xã giao"
            assert log_kwargs["sub_queries"] == []


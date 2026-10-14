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
        """Đảm bảo ngưỡng good score là 0.65 và safety threshold là 0.20 theo yêu cầu."""
        assert GOOD_SCORE_THRESHOLD == 0.65
        assert RERANKER_THRESHOLD == 0.20

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
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            
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
        """2 subqueries: floor 2 mỗi query (tổng 4), trần tối đa 5 (tối ưu Lost-in-the-Middle)."""
        chunks_q1 = [{"id": f"q1_{i}", "content": f"q1_{i}", "metadata": {}} for i in range(5)]
        chunks_q2 = [{"id": f"q2_{i}", "content": f"q2_{i}", "metadata": {}} for i in range(5)]
        
        # Cho q1 4 good chunks, q2 4 good chunks -> trần tối đa 5 chunks
        fake_scores = [1.0] * 5

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = fake_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            
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

            # Max ceiling cho 2 subqueries là 5 chunks
            assert len(result) == 5
            q1_picked = [c for c in result if c["matched_subquery"] == "thủ tục bảo lưu học tập IUH"]
            q2_picked = [c for c in result if c["matched_subquery"] == "chính sách hoàn học phí bảo lưu IUH"]
            assert len(q1_picked) + len(q2_picked) == 5
            assert len(q1_picked) >= 2
            assert len(q2_picked) >= 2

    @pytest.mark.asyncio
    async def test_quota_four_subqueries_ceiling_ten(self):
        """4 subqueries: floor 2 mỗi query (tổng 8), trần tối đa 8 chunks toàn cục."""
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
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            
            mock_emb.return_value = [0.1] * 768
            mock_supabase.rpc.side_effect = [
                MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks_per_q[i])))
                for i in range(4)
            ]

            result, top_score = await retrieve_relevant_chunks_multi(queries)

            # Max ceiling cho 4 subqueries là 8 chunks
            assert len(result) == 8

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
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            
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

    @pytest.mark.asyncio
    async def test_parent_document_collapse(self):
        """Đảm bảo các child chunks cùng parent_id được collapse thành 1 parent record trọn vẹn với parent_content."""
        parent_id_target = "parent-uuid-dieu-8"
        parent_full_text = "##### Điều 8: Quy định về các mức học bổng (Mức A 100%, Mức B 70%, Mức C 50%)..."
        
        chunks = [
            {
                "id": "child-c1",
                "parent_id": parent_id_target,
                "content": "Điểm c) Mức học bổng loại C...",
                "parent_content": parent_full_text,
                "metadata": {"title": "Quy chế học bổng"}
            },
            {
                "id": "child-c2",
                "parent_id": parent_id_target,
                "content": "Mức học bổng này bằng 50% học phí bình quân...",
                "parent_content": parent_full_text,
                "metadata": {"title": "Quy chế học bổng"}
            },
            {
                "id": "child-c3",
                "parent_id": "parent-uuid-dieu-7",
                "content": "Điều 7: Điều kiện xét học bổng...",
                "parent_content": "##### Điều 7: Toàn bộ điều kiện xét...",
                "metadata": {"title": "Quy chế học bổng"}
            }
        ]

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        # Điểm: c1 được 1.2 (~0.768), c2 được 1.8 (~0.858), c3 được 0.8 (~0.690)
        mock_reranker.predict.return_value = [1.2, 1.8, 0.8]

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock) as mock_emb, \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            
            mock_emb.return_value = [0.1] * 768
            mock_rpc = MagicMock(data=chunks)
            mock_supabase.rpc.return_value = MagicMock(execute=MagicMock(return_value=mock_rpc))

            result, top_score = await retrieve_relevant_chunks_multi(["học bổng loại C khóa 18"])

            # 2 child chunks cùng parent-uuid-dieu-8 phải được gộp lại thành đúng 1 parent record
            # Tổng kết quả chỉ còn 2 items: 1 cho dieu-8, 1 cho dieu-7
            assert len(result) == 2
            
            dieu_8_item = next(c for c in result if c.get("parent_id") == parent_id_target)
            # Nội dung đưa cho LLM phải là parent_content hoàn chỉnh
            assert dieu_8_item["content"] == parent_full_text
            # Điểm rerank phải là điểm cao nhất trong 2 child chunks (1.8 -> ~0.858)
            expected_score = 1 / (1 + math.exp(-1.8))
            assert math.isclose(dieu_8_item["rerank_score"], expected_score, rel_tol=1e-4)

    @pytest.mark.asyncio
    async def test_parent_aware_quota_prevents_sibling_starvation(self):
        """
        Kiểm tra cơ chế Parent-Aware Quota (Sự cố log 064717):
        Khi có nhiều sibling child chunks thuộc cùng 1 parent (da443b12),
        chúng không được chiếm hết quota và loại bỏ các parent quan trọng khác (2846fdfd).
        Hệ thống phải đảm bảo lấy đủ tối thiểu 3 distinct parent sections.
        """
        chunks = [
            {
                "id": "c1",
                "parent_id": "p-da443b12",
                "content": "Chuẩn đầu ra mục 1",
                "parent_content": "Section Chuẩn đầu ra...",
                "metadata": {"title": "Chuẩn đầu ra ngoại ngữ"}
            },
            {
                "id": "c2",
                "parent_id": "p-da443b12",
                "content": "Chuẩn đầu ra mục 2",
                "parent_content": "Section Chuẩn đầu ra...",
                "metadata": {"title": "Chuẩn đầu ra ngoại ngữ"}
            },
            {
                "id": "c3",
                "parent_id": "p-6e07f82e",
                "content": "Chuẩn đầu vào",
                "parent_content": "Section Chuẩn đầu vào...",
                "metadata": {"title": "Chuẩn đầu vào ngoại ngữ"}
            },
            {
                "id": "c4",
                "parent_id": "p-2846fdfd",
                "content": "Chương V: Quy chế tốt nghiệp & Chuẩn đầu ra Bậc 3",
                "parent_content": "Section Chương V: Quy chế tốt nghiệp...",
                "metadata": {"title": "Quy chế tốt nghiệp"}
            },
            {
                "id": "c5",
                "parent_id": "p-other",
                "content": "Nội dung khác",
                "parent_content": "Section khác...",
                "metadata": {"title": "Quy chế khác"}
            }
        ]

        # Raw scores ứng với: 0.6995, 0.6730, 0.6378, 0.6082, 0.5000
        raw_scores = [0.845, 0.722, 0.566, 0.440, 0.0]

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = raw_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock, return_value=[0.1]*768), \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):

            mock_supabase.rpc.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks)))

            result, top_score = await retrieve_relevant_chunks_multi(["chuẩn tiếng anh đầu ra khóa 18"])

            # Đảm bảo trả về đúng 3 distinct parent sections
            assert len(result) == 3

            parent_ids = [c.get("parent_id") for c in result]
            assert "p-da443b12" in parent_ids
            assert "p-6e07f82e" in parent_ids
            assert "p-2846fdfd" in parent_ids  # Chương V không bị starve out!
            assert "p-other" not in parent_ids

            # Parent da443b12 có score là max giữa c1 và c2 (0.845)
            p_da44 = next(c for c in result if c.get("parent_id") == "p-da443b12")
            assert math.isclose(p_da44["rerank_score"], 0.845, rel_tol=1e-4)

    @pytest.mark.asyncio
    async def test_parent_aware_quota_multiple_good_parents(self):
        """
        Kiểm tra khi có nhiều distinct parents với điểm good (>= 0.65):
        Hệ thống lấy tối đa max_per_query (6 cho 1 query) distinct parents
        mà không bị các chunks con trùng parent lấn át.
        """
        chunks = [
            {"id": "p1_c1", "parent_id": "p1", "content": "p1_1", "parent_content": "P1 full", "metadata": {}},
            {"id": "p1_c2", "parent_id": "p1", "content": "p1_2", "parent_content": "P1 full", "metadata": {}},
            {"id": "p2_c1", "parent_id": "p2", "content": "p2_1", "parent_content": "P2 full", "metadata": {}},
            {"id": "p2_c2", "parent_id": "p2", "content": "p2_2", "parent_content": "P2 full", "metadata": {}},
            {"id": "p3_c1", "parent_id": "p3", "content": "p3_1", "parent_content": "P3 full", "metadata": {}},
            {"id": "p4_c1", "parent_id": "p4", "content": "p4_1", "parent_content": "P4 full", "metadata": {}},
            {"id": "p5_c1", "parent_id": "p5", "content": "p5_1", "parent_content": "P5 full", "metadata": {}},
        ]
        # Tất cả đều có raw score = 1.0 (sigmoid = 0.731 >= 0.65)
        raw_scores = [1.0] * len(chunks)

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = raw_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock, return_value=[0.1]*768), \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):

            mock_supabase.rpc.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks)))

            result, _ = await retrieve_relevant_chunks_multi(["query"])

            # 5 distinct parents (p1, p2, p3, p4, p5) đều có điểm >= 0.65 -> cả 5 đều được chọn
            assert len(result) == 5
            parent_ids = {c.get("parent_id") for c in result}
            assert parent_ids == {"p1", "p2", "p3", "p4", "p5"}

    @pytest.mark.asyncio
    async def test_low_score_rejection_below_threshold(self):
        """Khi tất cả chunks đều có điểm rerank < 0.20, loại bỏ hoàn toàn và trả về [], 0.0."""
        chunks = [
            {"id": f"junk_{i}", "content": f"nội dung rác {i}", "metadata": {"title": "Triết lý giáo dục"}}
            for i in range(5)
        ]
        # Điểm rất thấp như log thực tế 010330-mon-triet-hoc-mac: 0.0006, 0.0004, 0.015, 0.05, 0.19 (< 0.20)
        low_scores = [0.0006, 0.0004, 0.015, 0.05, 0.19]

        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = low_scores

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock, return_value=[0.1]*768), \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):

            mock_supabase.rpc.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=chunks)))

            result, top_score = await retrieve_relevant_chunks_multi(["môn Triết học Mác có thay thế bằng môn CNXHKH"])

            # Toàn bộ chunks bị loại bỏ, trả về list rỗng để tránh tốn input token cho LLM
            assert result == []
            assert top_score == 0.0


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

    @pytest.mark.asyncio
    async def test_no_sliding_window_expansion(self):
        """Xác nhận không gọi expand_neighbors, nội dung chunk giữ nguyên sạch sẽ không bị ghép nối lặp."""
        raw_chunks = [
            {"id": "c1", "content": "Nội dung điều 1 sạch sẽ", "metadata": {"title": "Quy chế"}},
            {"id": "c2", "content": "Nội dung điều 2 sạch sẽ", "metadata": {"title": "Quy chế"}}
        ]
        mock_supabase = MagicMock()
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = [1.2, 1.1]

        with patch("app.services.rag_service.get_supabase_client", return_value=mock_supabase), \
             patch("app.services.rag_service.get_query_embedding", new_callable=AsyncMock, return_value=[0.1]*768), \
             patch("app.services.rag_service.get_reranker", return_value=mock_reranker):

            mock_supabase.rpc.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=raw_chunks)))

            result, _ = await retrieve_relevant_chunks_multi(["hỏi về quy chế"])

            # Chunks không bị nối bằng "\n...\n" và giữ nguyên text gốc
            for c in result:
                assert "\n...\n" not in c["content"]
            assert result[0]["content"] == "Nội dung điều 1 sạch sẽ"
            assert result[1]["content"] == "Nội dung điều 2 sạch sẽ"



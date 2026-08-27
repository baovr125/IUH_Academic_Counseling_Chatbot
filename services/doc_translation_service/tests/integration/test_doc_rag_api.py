import pytest
from unittest.mock import patch, MagicMock
from app.services.vector_store import upsert_doc_vectors, query_document_chunks


class TestDocRagApiIntegration:
    def test_health_check_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["service"] == "doc_translation_service"

    def test_upsert_doc_vectors_success(self):
        child_chunks = [
            {
                "parent_id": "p1",
                "page_number": 1,
                "parent_title": "Chương 1",
                "ancestors": [],
                "content": "Nội dung kiểm thử vector."
            }
        ]
        with patch("app.services.vector_store.get_supabase") as mock_get_sb, \
             patch("app.services.vector_store.get_embedding_model") as mock_get_model:
            mock_sb = MagicMock()
            mock_sb.table().upsert().execute.return_value = MagicMock(data=[{"id": "c1"}])
            mock_get_sb.return_value = mock_sb

            mock_model = MagicMock()
            mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 1024])
            mock_get_model.return_value = mock_model

            count = upsert_doc_vectors("doc-uuid", "user-uuid", child_chunks)
            assert count == 1

    def test_query_document_chunks_hard_payload_filtering(self):
        with patch("app.services.vector_store.get_supabase") as mock_get_sb, \
             patch("app.services.vector_store.compute_embedding") as mock_emb:
            mock_sb = MagicMock()
            mock_sb.rpc().execute.return_value = MagicMock(data=[
                {"id": "res-1", "doc_id": "doc-123", "content": "Tài liệu môn học"}
            ])
            mock_get_sb.return_value = mock_sb
            mock_emb.return_value = [0.1] * 1024

            results = query_document_chunks("doc-123", "user-456", "học phí", top_k=3)
            assert len(results) == 1
            assert results[0]["doc_id"] == "doc-123"

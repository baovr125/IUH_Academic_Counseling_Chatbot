from unittest.mock import MagicMock
import numpy as np


def create_mock_embedding_model(dim=1024):
    mock_model = MagicMock()
    
    def mock_encode(sentences, normalize_embeddings=True, **kwargs):
        if isinstance(sentences, str):
            return np.ones(dim, dtype=float)
        return np.ones((len(sentences), dim), dtype=float)

    mock_model.encode.side_effect = mock_encode
    return mock_model


def create_mock_supabase(upsert_return_count=5, query_data=None):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_query = MagicMock()

    mock_query.execute.return_value = MagicMock(data=query_data if query_data is not None else [])
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = MagicMock(data=[{"id": f"chunk-{i}"} for i in range(upsert_return_count)])
    mock_table.upsert.return_value = mock_upsert
    mock_table.select.return_value = mock_query

    mock_client.table.return_value = mock_table
    return mock_client

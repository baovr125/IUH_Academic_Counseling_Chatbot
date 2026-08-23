from unittest.mock import MagicMock, AsyncMock


def create_mock_gemini(response_text="Tư vấn học vụ IUH: Điểm chuẩn và quy chế đăng ký tín chỉ."):
    mock_client = MagicMock()
    mock_model = MagicMock()
    
    # Text generation response
    mock_response = MagicMock()
    mock_response.text = response_text
    
    mock_model.generate_content.return_value = mock_response
    mock_client.models = mock_model
    return mock_client


def create_mock_supabase(rpc_data=None, select_data=None):
    mock_client = MagicMock()
    mock_rpc = MagicMock()
    mock_rpc.execute.return_value = MagicMock(data=rpc_data if rpc_data is not None else [])
    mock_client.rpc.return_value = mock_rpc

    mock_table = MagicMock()
    mock_query = MagicMock()
    mock_query.execute.return_value = MagicMock(data=select_data if select_data is not None else [])
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.insert.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
    mock_query.update.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
    mock_query.delete.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
    mock_table.select.return_value = mock_query
    mock_table.insert.return_value = mock_query.insert.return_value
    mock_table.update.return_value = mock_query.update.return_value
    mock_table.delete.return_value = mock_query.delete.return_value
    mock_client.table.return_value = mock_table
    return mock_client


def create_mock_redis():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.keys.return_value = []
    mock_redis.delete.return_value = 0
    return mock_redis

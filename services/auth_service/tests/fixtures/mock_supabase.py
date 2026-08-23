from unittest.mock import MagicMock


def create_mock_supabase(
    select_data=None,
    insert_data=None,
    update_data=None,
    delete_data=None
):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_query = MagicMock()

    mock_query.execute.return_value = MagicMock(data=select_data if select_data is not None else [])
    
    # Chaining support
    mock_query.select.return_value = mock_query
    mock_query.insert.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(data=insert_data if insert_data is not None else []))
    )
    mock_query.update.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(data=update_data if update_data is not None else []))
    )
    mock_query.delete.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(data=delete_data if delete_data is not None else []))
    )
    mock_query.eq.return_value = mock_query
    mock_query.ilike.return_value = mock_query
    mock_query.or_.return_value = mock_query
    mock_query.neq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_table.select.return_value = mock_query
    mock_table.insert.return_value = mock_query.insert.return_value
    mock_table.update.return_value = mock_query.update.return_value
    mock_table.delete.return_value = mock_query.delete.return_value
    mock_table.eq.return_value = mock_query

    mock_client.table.return_value = mock_table
    return mock_client

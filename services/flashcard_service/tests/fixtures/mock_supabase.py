from unittest.mock import MagicMock


def create_mock_supabase(select_data=None, insert_data=None, update_data=None):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_query = MagicMock()

    mock_query.execute.return_value = MagicMock(data=select_data if select_data is not None else [])
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.ilike.return_value = mock_query

    mock_insert = MagicMock()
    mock_insert.execute.return_value = MagicMock(data=insert_data if insert_data is not None else [])
    mock_table.insert.return_value = mock_insert

    mock_update = MagicMock()
    mock_update.execute.return_value = MagicMock(data=update_data if update_data is not None else [])
    mock_table.update.return_value = mock_update

    mock_table.select.return_value = mock_query
    mock_client.table.return_value = mock_table
    return mock_client

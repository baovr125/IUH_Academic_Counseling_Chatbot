import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import text
from database import SessionLocal

def test_t03_vietnamese_fts_diacritics():
    """
    Test Case 0.3: Verify that Full Text Search handles Vietnamese diacritics correctly.
    This test executes a raw SQL query against the database to confirm that the 'unaccent' 
    extension and the 'immutable_unaccent' function are working as expected for FTS.
    """
    db = SessionLocal()
    try:
        # We query the database to verify that unaccented search matches accented text.
        # This simulates the logic inside fts_tokens and match_chunks_hybrid_rrf.
        query = text("""
            SELECT to_tsvector('simple', public.immutable_unaccent('đăng ký học phần')) 
            @@ websearch_to_tsquery('simple', public.immutable_unaccent('dang ky'));
        """)
        
        result = db.execute(query).scalar()
        
        # If result is True, it means 'dang ky' successfully matched 'đăng ký học phần'
        assert result is True, "FTS failed: 'dang ky' did not match 'đăng ký học phần'. Make sure 'unaccent' extension is installed and configured in schema_v2_hybrid_rag.sql."
        
    finally:
        db.close()

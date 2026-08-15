import psycopg2
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Không tìm thấy DATABASE_URL")
        return

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Đang cập nhật schema Supabase cho Vector 768 chiều...")
        
        # 1. Xóa index cũ (nếu có)
        cur.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding;")
        
        # 2. Xóa function query cũ vì nó depend vào kiểu vector(384)
        cur.execute("DROP FUNCTION IF EXISTS match_chunks_hybrid_rrf CASCADE;")
        
        # 3. Đổi kiểu dữ liệu cột
        cur.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(768);")
        
        # 4. Tạo lại index mới
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
            USING hnsw (embedding vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64);
        """)
        
        # 5. Tạo lại function RRF với signature mới (VECTOR(768))
        cur.execute("""
        CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
            query_text TEXT,
            query_embedding VECTOR(768),
            match_count INTEGER DEFAULT 15,
            rrf_k INTEGER DEFAULT 60
        )
        RETURNS TABLE (
            id UUID,
            document_id UUID,
            content TEXT,
            injected_content TEXT,
            metadata JSONB,
            source_url TEXT,
            rrf_score DOUBLE PRECISION,
            chunk_index INTEGER
        )
        LANGUAGE sql
        AS $$
        WITH vector_search AS (
            SELECT 
                c.id,
                ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding ASC) AS vector_rank
            FROM document_chunks c
            ORDER BY c.embedding <=> query_embedding ASC
            LIMIT 30
        ),
        keyword_search AS (
            SELECT 
                c.id,
                ROW_NUMBER() OVER (
                    ORDER BY ts_rank_cd(c.fts_tokens, websearch_to_tsquery('simple', public.unaccent(query_text))) DESC
                ) AS keyword_rank
            FROM document_chunks c
            WHERE c.fts_tokens @@ websearch_to_tsquery('simple', public.unaccent(query_text))
            LIMIT 30
        ),
        rrf_fusion AS (
            SELECT 
                COALESCE(v.id, k.id) AS chunk_id,
                (
                    COALESCE(1.0 / (rrf_k + v.vector_rank), 0.0) +
                    COALESCE(1.0 / (rrf_k + k.keyword_rank), 0.0)
                ) AS rrf_score
            FROM vector_search v
            FULL OUTER JOIN keyword_search k ON v.id = k.id
        )
        SELECT 
            c.id,
            c.document_id,
            c.content,
            c.injected_content,
            c.metadata,
            d.source_url,
            f.rrf_score,
            c.chunk_index
        FROM rrf_fusion f
        JOIN document_chunks c ON c.id = f.chunk_id
        LEFT JOIN documents d ON c.document_id = d.id
        ORDER BY f.rrf_score DESC
        LIMIT match_count;
        $$;
        """)
        
        print("Cập nhật Schema thành công! Đã chuyển sang Vector 768 chiều.")
        
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()

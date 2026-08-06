-- ====================================================================================
-- MIGRATION V6: SEMANTIC CACHE
-- Mục đích: Tạo bảng semantic_cache, HNSW index và hàm RPC để cache các câu trả lời
-- ====================================================================================

CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_query TEXT NOT NULL,
    query_embedding VECTOR(384) NOT NULL,
    cached_answer TEXT NOT NULL,
    retrieval_score DOUBLE PRECISION,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Tạo HNSW Index để tìm kiếm độ tương đồng Cosine nhanh
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache 
USING hnsw (query_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Index trên cột expires_at để dọn dẹp các cache hết hạn nhanh hơn
CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires_at ON semantic_cache(expires_at);

-- Hàm RPC (Supabase/PostgreSQL) để tìm kiếm cache
CREATE OR REPLACE FUNCTION match_semantic_cache(
    query_vec VECTOR(384),
    match_threshold FLOAT DEFAULT 0.95
)
RETURNS TABLE (
    id UUID,
    canonical_query TEXT,
    cached_answer TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.canonical_query,
        c.cached_answer,
        (1 - (c.query_embedding <=> query_vec))::FLOAT AS similarity
    FROM semantic_cache c
    WHERE c.expires_at > CURRENT_TIMESTAMP
      AND (1 - (c.query_embedding <=> query_vec)) >= match_threshold
    ORDER BY c.query_embedding <=> query_vec ASC
    LIMIT 1;
END;
$$;

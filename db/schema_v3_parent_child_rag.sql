-- ====================================================================================
-- SCHEMA V3: SOTA PARENT-CHILD (SMALL-TO-BIG) HYBRID RAG FOR ACADEMIC COUNSELING
-- ====================================================================================

-- 1. BẢNG MỚI: DOCUMENT_PARENTS (Lưu trữ Điều khoản/Mục/Bảng hoàn chỉnh làm Context cho LLM)
CREATE TABLE IF NOT EXISTS document_parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_index INTEGER DEFAULT 0,
    header_path TEXT,                               -- Ví dụ: "Chương II > Điều 8. Mức học bổng"
    content TEXT NOT NULL,                          -- Toàn bộ nội dung điều khoản hoàn chỉnh (1.000 - 3.000 chars)
    metadata JSONB,                                 -- Metadata thừa hưởng từ bài viết
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_parents_doc_id ON document_parents(document_id);

-- 2. CẬP NHẬT BẢNG DOCUMENT_CHUNKS: THÊM KHÓA NGOẠI parent_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'document_chunks' AND column_name = 'parent_id'
    ) THEN
        ALTER TABLE document_chunks 
        ADD COLUMN parent_id UUID REFERENCES document_parents(id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_document_chunks_parent_id ON document_chunks(parent_id);

-- 3. HÀM RPC TÌM KIẾM HYBRID RRF V3: TRẢ VỀ CẢ CHILD VÀ PARENT CONTENT
DROP FUNCTION IF EXISTS match_chunks_hybrid_rrf(text,vector,integer,integer);

CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
    query_text TEXT,
    query_embedding VECTOR(768),
    match_count INTEGER DEFAULT 15,
    rrf_k INTEGER DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    parent_id UUID,
    content TEXT,                                   -- Child content (phục vụ rerank)
    parent_content TEXT,                            -- Parent content (phục vụ LLM Reader)
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
    LIMIT GREATEST(match_count * 2, 60)
),
keyword_search AS (
    SELECT 
        c.id,
        ROW_NUMBER() OVER (
            ORDER BY ts_rank_cd(c.fts_tokens, websearch_to_tsquery('simple', public.unaccent(query_text))) DESC
        ) AS keyword_rank
    FROM document_chunks c
    WHERE c.fts_tokens @@ websearch_to_tsquery('simple', public.unaccent(query_text))
    LIMIT GREATEST(match_count * 2, 60)
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
    c.parent_id,
    c.content,
    COALESCE(p.content, c.content) AS parent_content,
    c.injected_content,
    c.metadata,
    d.source_url,
    f.rrf_score,
    c.chunk_index
FROM rrf_fusion f
JOIN document_chunks c ON c.id = f.chunk_id
LEFT JOIN document_parents p ON c.parent_id = p.id
LEFT JOIN documents d ON c.document_id = d.id
ORDER BY f.rrf_score DESC
LIMIT match_count;
$$;

-- ====================================================================================
-- MIGRATION SCRIPT V6: BỔ SUNG BẢNG DOC_VECTORS (BGE-M3 1024D) CHO FEATURE DỊCH TÀI LIỆU & DOCUMENT RAG
-- ====================================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS doc_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    parent_id TEXT,
    page_number INT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    translated_content TEXT NOT NULL,
    injected_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1024),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doc_vectors_doc_user 
ON doc_vectors(doc_id, user_id);

CREATE INDEX IF NOT EXISTS idx_doc_vectors_embedding 
ON doc_vectors USING hnsw (embedding vector_cosine_ops);

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'status') THEN
        ALTER TABLE document_translations ADD COLUMN status VARCHAR(50) DEFAULT 'pending';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'progress') THEN
        ALTER TABLE document_translations ADD COLUMN progress INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'status_message') THEN
        ALTER TABLE document_translations ADD COLUMN status_message TEXT DEFAULT '';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'glossary_json') THEN
        ALTER TABLE document_translations ADD COLUMN glossary_json JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

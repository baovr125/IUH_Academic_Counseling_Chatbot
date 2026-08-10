-- ====================================================================================
-- MIGRATION SCRIPT V6: BỔ SUNG BẢNG DOC_VECTOS (BGE-M3 1024D) CHO FEATURE DỊCH TÀI LIỆU & DOCUMENT RAG
-- ====================================================================================

-- 1. KÍCH HOẠT EXTENSION BẮT BUỘC
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. BẢNG MỚI: DOC_VECTORS (Lưu trữ Chunks phân cấp & Embeddings 1024 chiều từ BAAI/bge-m3)
CREATE TABLE IF NOT EXISTS doc_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL,                         -- ID tài liệu (liên kết document_translations.id)
    user_id TEXT NOT NULL,                        -- ID người dùng (Phục vụ Hard Payload Filtering)
    parent_id TEXT,                               -- ID Chunk cha (Parent Chunk / Section / Chapter)
    page_number INT NOT NULL,                     -- Số trang chứa đoạn văn bản (phục vụ Trích dẫn Citations)
    chunk_index INT NOT NULL,                     -- Thứ tự đoạn chunk trong tài liệu
    content TEXT NOT NULL,                        -- Nội dung văn bản gốc đã dịch
    translated_content TEXT NOT NULL,             -- Nội dung dịch tiếng Việt/đích
    injected_content TEXT NOT NULL,               -- Nội dung đã ghép tiền tố [Mục: Section > Header] để nhúng Vector
    metadata JSONB DEFAULT '{}'::jsonb,           -- Các chỉ số phụ (level, headers, ancestors)
    embedding vector(1024),                       -- Vector nhúng 1024 chiều (BAAI/bge-m3)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. ĐÁNH CHỈ MỤC (INDEXES) TỐI ƯU TRUY VẤN
-- Index kết hợp doc_id và user_id cho Hard Payload Filtering RAG
CREATE INDEX IF NOT EXISTS idx_doc_vectors_doc_user 
ON doc_vectors(doc_id, user_id);

-- Index HNSW Cosine Similarity cho tìm kiếm Vector 1024 chiều
CREATE INDEX IF NOT EXISTS idx_doc_vectors_embedding 
ON doc_vectors USING hnsw (embedding vector_cosine_ops);

-- 4. CẬP NHẬT BẢNG CỦ: DOCUMENT_TRANSLATIONS (Bổ sung trạng thái Polling & Thuật ngữ JSON)
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

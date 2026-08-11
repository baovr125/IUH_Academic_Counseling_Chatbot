-- ====================================================================================
-- MASTER SQL SCHEMA COMPREHENSIVE (BẢN TỔNG HỢP TOÀN BỘ V1, V2, V3, V4, V5, V6)
-- Dự án: IUH Academic Counseling Chatbot & Language Portal (Khóa luận tốt nghiệp)
-- ====================================================================================

-- 0. XÓA BẢNG VÀ HÀM CŨ TRƯỚC KHI KHỞI TẠO LẠI (CLEANUP)
DROP TABLE IF EXISTS doc_vectors CASCADE;
DROP TABLE IF EXISTS password_resets CASCADE;
DROP TABLE IF EXISTS document_translations CASCADE;
DROP TABLE IF EXISTS flashcards CASCADE;
DROP TABLE IF EXISTS flashcard_decks CASCADE;
DROP TABLE IF EXISTS translation_history CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP FUNCTION IF EXISTS match_doc_vectors CASCADE;
DROP FUNCTION IF EXISTS match_chunks_hybrid_rrf CASCADE;
DROP FUNCTION IF EXISTS immutable_unaccent CASCADE;
DROP FUNCTION IF EXISTS update_modified_column CASCADE;

-- ====================================================================================
-- 1. KÍCH HOẠT EXTENSION BẮT BUỘC
-- ====================================================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Wrapper IMMUTABLE cho unaccent (cần thiết cho GENERATED ALWAYS columns)
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text AS $$
  SELECT public.unaccent('public.unaccent', $1);
$$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;

-- Hàm tiện ích tự động cập nhật thời gian thay đổi dữ liệu (Trigger)
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ====================================================================================
-- 2. TẠO CÁC BẢNG DỮ LIỆU (TABLES - TỔNG HỢP TẤT CẢ CÁC CỘT BỔ SUNG TỪ V3 ➔ V6)
-- ====================================================================================

-- BẢNG 1: USERS (Quản lý Người dùng & Hồ sơ Sinh viên IUH - Đã tích hợp Migration v4 & v5)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    student_code VARCHAR(50) UNIQUE DEFAULT NULL,   -- Mã số sinh viên IUH (Migration v4)
    department VARCHAR(150) DEFAULT NULL,           -- Khoa / Viện (Migration v4)
    major VARCHAR(150) DEFAULT NULL,                -- Ngành học (Migration v4)
    phone_number VARCHAR(20) DEFAULT NULL,          -- Số điện thoại (Migration v4)
    password_hash VARCHAR(255),                     -- Mật khẩu mã hóa
    google_id VARCHAR(255) UNIQUE,                  -- ID Đăng nhập Google OAuth2
    avatar_url TEXT,                                -- URL ảnh đại diện
    role VARCHAR(50) DEFAULT 'student',             -- 'student' | 'public' | 'admin'
    settings JSONB DEFAULT '{"theme": "light", "language": "vi"}'::jsonb, -- Cấu hình (Migration v5)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 2: PASSWORD_RESETS (Mã OTP khôi phục mật khẩu)
CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 3: DOCUMENTS (Quản lý Bài viết / File gốc từ Crawler hoặc Hệ thống)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    source_url TEXT UNIQUE,                         -- URL bài gốc kiểm tra trùng lặp
    breadcrumbs TEXT,                               -- Phân cấp đường dẫn mục
    content_hash VARCHAR(255),                      -- Mã hash MD5 nội dung
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 4: DOCUMENT_CHUNKS (Lõi RAG Học Vụ - Vector 384d MiniLM + BM25 Keyword Search)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,                          -- Văn bản sạch
    injected_content TEXT,                          -- Văn bản kèm title/breadcrumbs
    metadata JSONB,                                 -- Cấu trúc header/page/level
    embedding VECTOR(384),                          -- Vector 384d (paraphrase-multilingual-MiniLM-L12-v2)
    fts_tokens TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', immutable_unaccent(COALESCE(injected_content, content)))
    ) STORED,                                       -- TSVECTOR tự động unaccent tiếng Việt cho BM25
    tokens_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 5: DOC_VECTORS (Lõi Document RAG Workspace - Vector 1024d BAAI/bge-m3 - Migration v6)
CREATE TABLE doc_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL,                           -- ID tài liệu dịch (liên kết document_translations.id)
    user_id TEXT NOT NULL,                          -- Phục vụ Hard Payload Filtering
    parent_id TEXT,                                 -- Parent Chunk (Hierarchical v6.2)
    page_number INT NOT NULL,                       -- Số trang phục vụ Citations
    chunk_index INT NOT NULL,                       -- Thứ tự đoạn chunk
    content TEXT NOT NULL,                          -- Nội dung đoạn dịch
    translated_content TEXT NOT NULL,               -- Nội dung bản dịch
    injected_content TEXT NOT NULL,                 -- [Mục: Path > Title] Văn bản nhúng
    metadata JSONB DEFAULT '{}'::jsonb,             -- Thông tin phụ (ancestors, titles)
    embedding VECTOR(1024),                         -- Vector 1024d (BAAI/bge-m3)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 6: CONVERSATIONS (Phiên trò chuyện Hỏi đáp Học vụ)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Cuộc trò chuyện mới',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 7: MESSAGES (Chi tiết tin nhắn & Đánh giá RAG)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    translated_content TEXT,
    source_lang VARCHAR(10) DEFAULT 'vi',
    target_lang VARCHAR(10),
    retrieved_chunk_ids UUID[],                     -- Trích dẫn Chunks ID
    feedback VARCHAR(20) CHECK (feedback IN ('like', 'dislike', 'none')) DEFAULT 'none',
    feedback_comment TEXT,
    latency_ms INTEGER,                             -- Độ trễ xử lý (ms)
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 8: TRANSLATION_HISTORY (Lịch sử sử dụng dịch văn bản nhanh)
CREATE TABLE translation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 9: FLASHCARD_DECKS (Sổ thẻ từ vựng phân loại theo ngôn ngữ - Migration v3)
CREATE TABLE flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lang_code VARCHAR(10) NOT NULL,                 -- en, de, ja, zh, ko...
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon_flag VARCHAR(10) DEFAULT '🌐',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 10: FLASHCARDS (Thẻ từ vựng & Thuật toán lặp ngắt quãng SM-2 - Migration v3)
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID REFERENCES flashcard_decks(id) ON DELETE CASCADE, -- Đã gộp từ Migration v3
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    term VARCHAR(500) NOT NULL,                     -- Từ / Cụm từ gốc
    definition TEXT NOT NULL,                       -- Nghĩa tiếng Việt
    example TEXT,                                   -- Ví dụ minh họa (Migration v3)
    part_of_speech VARCHAR(50),                     -- Từ loại
    lang_code VARCHAR(10) DEFAULT 'en',             -- Mã ngôn ngữ (Migration v3)
    status VARCHAR(50) DEFAULT 'learning',          -- learning, review_later, mastered
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 11: DOCUMENT_TRANSLATIONS (Dịch File PDF & Polling Status - Migration v3 & v6)
CREATE TABLE document_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,                 -- 'pdf', 'docx', 'pptx'
    file_size_bytes BIGINT,
    pages_or_slides VARCHAR(50),
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL,
    translated_file_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',           -- 'pending', 'processing', 'completed', 'failed' (Migration v6)
    progress INT DEFAULT 0,                         -- 0 - 100% (Migration v6)
    status_message TEXT DEFAULT '',                 -- Message tiến độ (Migration v6)
    summary_json JSONB,                             -- Tóm tắt AI (Executive summary, key findings)
    glossary_json JSONB DEFAULT '[]'::jsonb,        -- Từ điển thuật ngữ trích xuất JSON (Migration v6)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ====================================================================================
-- 3. GẮN TRIGGER VÀ TẠO TẤT CẢ CHỈ MỤC INDEXES
-- ====================================================================================

-- Trigger tự động cập nhật updated_at
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_documents_modtime BEFORE UPDATE ON documents FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_conversations_modtime BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_flashcard_decks_modtime BEFORE UPDATE ON flashcard_decks FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Chỉ mục B-tree Khóa ngoại & Filtering
CREATE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code);
CREATE INDEX IF NOT EXISTS idx_password_resets_email_otp ON password_resets(email, otp_code);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_translation_history_user_id ON translation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_user_id ON flashcard_decks(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_deck_id ON flashcards(deck_id);
CREATE INDEX IF NOT EXISTS idx_document_translations_user_id ON document_translations(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING GIN (metadata);

-- Chỉ mục Vector HNSW (384 chiều) cho Academic Counseling RAG
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Chỉ mục GIN Full-Text Search cho BM25 Keyword Search
CREATE INDEX IF NOT EXISTS idx_document_chunks_fts ON document_chunks 
USING GIN (fts_tokens);

-- Chỉ mục Hard Payload Filtering cho Document Translation RAG Workspace
CREATE INDEX IF NOT EXISTS idx_doc_vectors_doc_user ON doc_vectors(doc_id, user_id);

-- Chỉ mục Vector HNSW (1024 chiều) cho BAAI/bge-m3 Document RAG
CREATE INDEX IF NOT EXISTS idx_doc_vectors_embedding ON doc_vectors 
USING hnsw (embedding vector_cosine_ops);


-- ====================================================================================
-- 4. HÀM TÌM KIẾM VECTOR & HYBRID SEARCH (RECIPROCAL RANK FUSION - RRF)
-- ====================================================================================

-- HÀM 1: Hybrid Search RRF cho Academic Counseling Chatbot (Vector 384d + BM25 TSVector)
CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
    query_text TEXT,
    query_embedding VECTOR(384),
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

-- HÀM 2: Hard Payload Filtered Vector Search cho Document RAG Workspace (Vector 1024d)
CREATE OR REPLACE FUNCTION match_doc_vectors(
    query_embedding VECTOR(1024),
    filter_doc_id TEXT,
    filter_user_id TEXT,
    match_threshold DOUBLE PRECISION DEFAULT 0.2,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    doc_id TEXT,
    user_id TEXT,
    parent_id TEXT,
    page_number INT,
    chunk_index INT,
    content TEXT,
    translated_content TEXT,
    injected_content TEXT,
    metadata JSONB,
    similarity DOUBLE PRECISION
)
LANGUAGE sql
AS $$
SELECT 
    v.id,
    v.doc_id,
    v.user_id,
    v.parent_id,
    v.page_number,
    v.chunk_index,
    v.content,
    v.translated_content,
    v.injected_content,
    v.metadata,
    1 - (v.embedding <=> query_embedding) AS similarity
FROM doc_vectors v
WHERE v.doc_id = filter_doc_id 
  AND v.user_id = filter_user_id
  AND 1 - (v.embedding <=> query_embedding) > match_threshold
ORDER BY v.embedding <=> query_embedding ASC
LIMIT match_count;
$$;

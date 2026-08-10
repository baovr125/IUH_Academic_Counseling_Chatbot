-- ====================================================================================
-- SCRIPT KHỞI TẠO CƠ SỞ DỮ LIỆU V2: TỐI ƯU CHO HYBRID SEARCH (VECTOR + BM25/KEYWORD + RRF)
-- Dự án: IUH Academic Counseling Chatbot & Language Portal (Khóa luận tốt nghiệp)
-- ====================================================================================

-- 0. XÓA BẢNG VÀ HÀM CŨ TRƯỚC KHI TẠO LẠI (CLEANUP)
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
DROP FUNCTION IF EXISTS match_chunks_hybrid_rrf CASCADE;
DROP FUNCTION IF EXISTS update_modified_column CASCADE;

-- 1. KÍCH HOẠT EXTENSION BẮT BUỘC
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Wrapper IMMUTABLE cho unaccent (cần thiết cho GENERATED ALWAYS columns)
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text AS $$
  SELECT public.unaccent('public.unaccent', $1);
$$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;

-- Hàm tiện ích để tự động cập nhật cột updated_at khi có thay đổi dữ liệu (Trigger)
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';


-- ====================================================================================
-- 2. TẠO CÁC BẢNG DỮ LIỆU (TABLES)
-- ====================================================================================

-- BẢNG 1: USERS (Người dùng)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    student_code VARCHAR(50) UNIQUE DEFAULT NULL,
    department VARCHAR(150) DEFAULT NULL,
    major VARCHAR(150) DEFAULT NULL,
    phone_number VARCHAR(20) DEFAULT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code);

-- BẢNG: PASSWORD_RESETS (Lưu trữ mã OTP khôi phục mật khẩu)
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_password_resets_email_otp ON password_resets(email, otp_code);

-- BẢNG 2: DOCUMENTS (Quản lý File/Bài viết gốc từ Crawler hoặc Upload)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    source_url TEXT UNIQUE,
    breadcrumbs TEXT,
    content_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 3: DOCUMENT_CHUNKS (Lõi RAG - Hỗ trợ cả Vector Search & Full-Text Search)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,
    injected_content TEXT,
    metadata JSONB,
    embedding VECTOR(384),
    fts_tokens TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', immutable_unaccent(COALESCE(injected_content, content)))
    ) STORED,
    tokens_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 4: CONVERSATIONS (Phiên trò chuyện của người dùng)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Cuộc trò chuyện mới',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 5: MESSAGES (Chi tiết tin nhắn trong phiên trò chuyện)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')), 
    content TEXT NOT NULL,
    translated_content TEXT,
    source_lang VARCHAR(10) DEFAULT 'vi',
    target_lang VARCHAR(10),
    retrieved_chunk_ids UUID[],
    feedback VARCHAR(20) CHECK (feedback IN ('like', 'dislike', 'none')) DEFAULT 'none',
    feedback_comment TEXT,
    latency_ms INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 6: TRANSLATION_HISTORY
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

-- BẢNG 7: FLASHCARD_DECKS
CREATE TABLE flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lang_code VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon_flag VARCHAR(10) DEFAULT '🌐',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 8: FLASHCARDS
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID REFERENCES flashcard_decks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    term VARCHAR(500) NOT NULL,
    definition TEXT NOT NULL,
    example TEXT,
    part_of_speech VARCHAR(50),
    lang_code VARCHAR(10) DEFAULT 'en',
    status VARCHAR(50) DEFAULT 'learning',
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 9: DOCUMENT_TRANSLATIONS
CREATE TABLE document_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size_bytes BIGINT,
    pages_or_slides VARCHAR(50),
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL,
    translated_file_url TEXT,
    summary_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Gắn Trigger tự động cập nhật thời gian (updated_at)
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_documents_modtime BEFORE UPDATE ON documents FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_conversations_modtime BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_flashcard_decks_modtime BEFORE UPDATE ON flashcard_decks FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conv_id ON messages(conversation_id);
CREATE INDEX idx_translation_history_user_id ON translation_history(user_id);
CREATE INDEX idx_flashcard_decks_user_id ON flashcard_decks(user_id);
CREATE INDEX idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX idx_flashcards_deck_id ON flashcards(deck_id);
CREATE INDEX idx_document_translations_user_id ON document_translations(user_id);
CREATE INDEX idx_document_chunks_metadata ON document_chunks USING GIN (metadata);

CREATE INDEX idx_document_chunks_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_document_chunks_fts ON document_chunks 
USING GIN (fts_tokens);

-- HÀM SQL HYBRID SEARCH WITH RRF
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

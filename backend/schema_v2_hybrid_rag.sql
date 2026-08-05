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
-- Cần thiết cho việc lưu trữ vector và tìm kiếm độ tương đồng
CREATE EXTENSION IF NOT EXISTS vector;
-- Hỗ trợ tìm kiếm không dấu (diacritic-insensitive) cho tiếng Việt
CREATE EXTENSION IF NOT EXISTS unaccent;
-- Hỗ trợ tìm kiếm trigram (substring matching) cho tiếng Việt
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
-- Lưu ý: Thứ tự tạo bảng rất quan trọng vì liên quan đến Khóa Ngoại (Foreign Keys)
-- ====================================================================================

-- BẢNG 1: USERS (Người dùng)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    student_code VARCHAR(50) UNIQUE DEFAULT NULL, -- Mã số sinh viên (NULL cho người dùng công cộng)
    department VARCHAR(150) DEFAULT NULL,         -- Khoa / Viện
    major VARCHAR(150) DEFAULT NULL,              -- Ngành học
    phone_number VARCHAR(20) DEFAULT NULL,        -- Số điện thoại liên hệ
    password_hash VARCHAR(255),                   -- Null nếu login bằng Google
    google_id VARCHAR(255) UNIQUE,                -- ID từ hệ thống Google
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'student',           -- 'student' (Sinh viên IUH) | 'public' (Công cộng)
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
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Null nếu do hệ thống tự crawl
    title TEXT NOT NULL,
    source_url TEXT UNIQUE,                   -- URL để kiểm tra trùng lặp khi crawl (Idempotent Crawler)
    breadcrumbs TEXT,                         -- Phân cấp bài viết
    content_hash VARCHAR(255),                -- Mã băm MD5 để check nội dung có thay đổi không
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 3: DOCUMENT_CHUNKS (Lõi RAG - Hỗ trợ cả Vector Search & Full-Text Search)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,            -- [MỚI] Thứ tự đoạn chunk trong bài viết (hỗ trợ Neighbor Chunking)
    content TEXT NOT NULL,                    -- Nội dung hiển thị sạch cho sinh viên
    injected_content TEXT,                    -- Nội dung đã ghép title/breadcrumbs để nhúng (Embedding)
    metadata JSONB,                           -- Các thông tin khác (level, page, header...)
    embedding VECTOR(384),                    -- [VECTOR SEARCH] Vector 384 chiều (paraphrase-multilingual-MiniLM-L12-v2)
    fts_tokens TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', immutable_unaccent(COALESCE(injected_content, content)))
    ) STORED,                                 -- [KEYWORD SEARCH] TSVECTOR tự động, unaccent cho tìm kiếm không dấu tiếng Việt
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

-- BẢNG 5: MESSAGES (Chi tiết tin nhắn trong phiên trò chuyện - Bổ sung số liệu cho Khóa luận)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')), 
    content TEXT NOT NULL,                    -- Câu hỏi (user) hoặc Câu trả lời (assistant)
    translated_content TEXT,                  -- Kết quả dịch (nếu có)
    source_lang VARCHAR(10) DEFAULT 'vi',
    target_lang VARCHAR(10),
    retrieved_chunk_ids UUID[],               -- Mảng lưu các Chunk ID được dùng làm ngữ cảnh (Citations)
    feedback VARCHAR(20) CHECK (feedback IN ('like', 'dislike', 'none')) DEFAULT 'none', -- [MỚI] Đánh giá chất lượng từ sinh viên
    feedback_comment TEXT,                    -- [MỚI] Góp ý từ sinh viên cho câu trả lời
    latency_ms INTEGER,                       -- [MỚI] Đo thời gian xử lý RAG + LLM (ms)
    prompt_tokens INTEGER,                    -- [MỚI] Token đầu vào
    completion_tokens INTEGER,                -- [MỚI] Token LLM sinh ra
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 6: TRANSLATION_HISTORY (Lịch sử sử dụng công cụ Dịch thuật độc lập)
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

-- BẢNG 7: FLASHCARD_DECKS (Sổ thẻ từ vựng phân loại theo từng ngôn ngữ dịch)
CREATE TABLE flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lang_code VARCHAR(10) NOT NULL,           -- en, de, ja, zh, ko, fr...
    title VARCHAR(255) NOT NULL,              -- Sổ từ vựng Tiếng Anh...
    description TEXT,
    icon_flag VARCHAR(10) DEFAULT '🌐',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 8: FLASHCARDS (Hệ thống thẻ từ vựng ôn tập trong từng Sổ thẻ)
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID REFERENCES flashcard_decks(id) ON DELETE CASCADE, -- [MỚI] Liên kết Sổ thẻ
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    term VARCHAR(500) NOT NULL,               -- Mặt trước (Từ vựng / Mẫu câu gốc)
    definition TEXT NOT NULL,                 -- Mặt sau (Ý nghĩa bản dịch)
    example TEXT,                             -- [MỚI] Ví dụ câu văn / Ghi chú ngữ cảnh
    part_of_speech VARCHAR(50),               -- Từ loại (Danh từ, Động từ, cụm từ...)
    lang_code VARCHAR(10) DEFAULT 'en',       -- [MỚI] Mã ngôn ngữ (en, de, ja...)
    status VARCHAR(50) DEFAULT 'learning',    -- learning, review_later, mastered
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 9: DOCUMENT_TRANSLATIONS (Dịch thuật và Tóm tắt tài liệu PDF, PPT, Word)
CREATE TABLE document_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,          -- Tên tài liệu gốc
    file_type VARCHAR(20) NOT NULL,           -- 'pdf', 'docx', 'pptx'
    file_size_bytes BIGINT,                   -- Kích thước file (bytes)
    pages_or_slides VARCHAR(50),              -- Số trang / slides ước tính
    source_lang VARCHAR(10) NOT NULL,         -- Ngôn ngữ gốc
    target_lang VARCHAR(10) NOT NULL,         -- Ngôn ngữ đích
    translated_file_url TEXT,                 -- Đường dẫn lưu file đã dịch để tải về
    summary_json JSONB,                       -- [MỚI] Tóm tắt AI (Executive summary, Key points, Key terminology)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ====================================================================================
-- 3. GẮN TRIGGER VÀ TẠO CHỈ MỤC (INDEXES)
-- ====================================================================================

-- Gắn Trigger tự động cập nhật thời gian (updated_at) cho các bảng cần thiết
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_documents_modtime BEFORE UPDATE ON documents FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_conversations_modtime BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_flashcard_decks_modtime BEFORE UPDATE ON flashcard_decks FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tạo Index thông thường để tăng tốc độ truy vấn Khóa ngoại & Filtering
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

-- [QUAN TRỌNG 1] TẠO INDEX VECTOR HNSW (Dense Retrieval)
-- HNSW giúp tìm kiếm vector nhanh gấp hàng chục lần so với ivfflat
CREATE INDEX idx_document_chunks_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- [QUAN TRỌNG 2 - MỚI] TẠO INDEX GIN CHO FULL-TEXT SEARCH (Sparse / BM25-style Keyword Retrieval)
CREATE INDEX idx_document_chunks_fts ON document_chunks 
USING GIN (fts_tokens);


-- ====================================================================================
-- 4. HÀM SQL TRUY HỒI LAI (HYBRID SEARCH WITH RECIPROCAL RANK FUSION - RRF)
-- Hàm này thay thế cho logic `rrf_merge(k=60)` trên Python, chạy siêu tốc ngay trong DB
-- ====================================================================================

CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
    query_text TEXT,
    query_embedding VECTOR(384),
    match_count INTEGER DEFAULT 15,           -- Số lượng chunk ứng viên trả về để đưa cho BGE Reranker (Python)
    rrf_k INTEGER DEFAULT 60                  -- Hằng số k = 60 theo đúng thực nghiệm Baseline trong Khóa luận
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    injected_content TEXT,
    metadata JSONB,
    source_url TEXT,
    rrf_score DOUBLE PRECISION
)
LANGUAGE sql
AS $$
WITH vector_search AS (
    -- Bước 1: Lấy Top 30 chunk bằng độ tương đồng Cosine (Dense Vector Search)
    SELECT 
        c.id,
        ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding ASC) AS vector_rank
    FROM document_chunks c
    ORDER BY c.embedding <=> query_embedding ASC
    LIMIT 30
),
keyword_search AS (
    -- Bước 2: Lấy Top 30 chunk bằng từ khóa Full-Text Search (Sparse Keyword Search)
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
    -- Bước 3: Gộp kết quả 2 tập hợp và áp dụng công thức Reciprocal Rank Fusion (RRF)
    SELECT 
        COALESCE(v.id, k.id) AS chunk_id,
        (
            COALESCE(1.0 / (rrf_k + v.vector_rank), 0.0) +
            COALESCE(1.0 / (rrf_k + k.keyword_rank), 0.0)
        ) AS rrf_score
    FROM vector_search v
    FULL OUTER JOIN keyword_search k ON v.id = k.id
)
-- Bước 4: Trả về Top K chunk có điểm RRF cao nhất kèm thông tin nguồn
SELECT 
    c.id,
    c.document_id,
    c.content,
    c.injected_content,
    c.metadata,
    d.source_url,
    rf.rrf_score
FROM rrf_fusion rf
JOIN document_chunks c ON c.id = rf.chunk_id
JOIN documents d ON d.id = c.document_id
ORDER BY rf.rrf_score DESC
LIMIT match_count;
$$;
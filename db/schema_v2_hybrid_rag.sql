-- ====================================================================================
-- MASTER SQL SCHEMA COMPREHENSIVE (BẢN TỔNG HỢP TOÀN DIỆN V1 -> V10 CHUẨN HÓA)
-- Dự án: IUH Academic Counseling Chatbot & Language Learning Ecosystem (Khóa luận tốt nghiệp)
-- Hệ thống microservices: Auth, Academic Chatbot RAG, Realtime Translation, Doc Translation RAG, Flashcard FSRS
-- ====================================================================================

-- ====================================================================================
-- 0. XÓA BẢNG VÀ HÀM CŨ TRƯỚC KHI KHỞI TẠO LẠI (CLEANUP & RESET)
-- ====================================================================================
DROP TABLE IF EXISTS review_logs CASCADE;
DROP TABLE IF EXISTS flashcards CASCADE;
DROP TABLE IF EXISTS flashcard_decks CASCADE;
DROP TABLE IF EXISTS doc_vectors CASCADE;
DROP TABLE IF EXISTS document_translations CASCADE;
DROP TABLE IF EXISTS semantic_cache CASCADE;
DROP TABLE IF EXISTS translation_history CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS password_resets CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP FUNCTION IF EXISTS match_semantic_cache CASCADE;
DROP FUNCTION IF EXISTS match_doc_vectors CASCADE;
DROP FUNCTION IF EXISTS match_chunks_hybrid_rrf CASCADE;
DROP FUNCTION IF EXISTS immutable_unaccent CASCADE;
DROP FUNCTION IF EXISTS update_modified_column CASCADE;

-- ====================================================================================
-- 1. KÍCH HOẠT CÁC EXTENSION BẮT BUỘC
-- ====================================================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Hàm IMMUTABLE cho unaccent (phục vụ sinh cột TSVECTOR tự động)
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text AS $$
  SELECT public.unaccent('public.unaccent', $1);
$$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;

-- Trigger cập nhật thời gian updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================================
-- 2. TẠO CÁC BẢNG DỮ LIỆU (12 BẢNG CHUẨN HÓA)
-- ====================================================================================

-- BẢNG 1: USERS (Quản lý Người dùng & Hồ sơ Sinh viên IUH)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    student_code VARCHAR(50) UNIQUE DEFAULT NULL,   -- Mã số sinh viên IUH (VD: 20012345)
    department VARCHAR(150) DEFAULT NULL,           -- Khoa / Viện (VD: Công nghệ Thông tin)
    major VARCHAR(150) DEFAULT NULL,                -- Ngành học (VD: Kỹ thuật phần mềm)
    phone_number VARCHAR(20) DEFAULT NULL,          -- Số điện thoại liên hệ
    password_hash VARCHAR(255),                     -- Mật khẩu mã hóa bcrypt
    google_id VARCHAR(255) UNIQUE,                  -- ID Đăng nhập Google OAuth2
    avatar_url TEXT,                                -- URL ảnh đại diện
    role VARCHAR(50) DEFAULT 'student',             -- 'student' | 'public' | 'admin'
    settings JSONB DEFAULT '{"theme": "light", "language": "vi"}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 2: PASSWORD_RESETS (Quản lý mã OTP khôi phục mật khẩu)
CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 3: DOCUMENTS (Quản lý Bài viết / Văn bản Quy chế gốc từ IUH Portal & Crawler)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    source_url TEXT UNIQUE,                         -- URL bài viết kiểm tra trùng lặp
    breadcrumbs TEXT,                               -- Phân cấp cây thư mục/chuyên mục
    content_hash VARCHAR(255),                      -- Mã băm MD5 kiểm tra cập nhật
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 4: DOCUMENT_CHUNKS (Lõi RAG Tư Vấn Học Vụ - Vector 768d bkai-foundation-models/vietnamese-bi-encoder + BM25 Full-Text Search)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,                          -- Nội dung văn bản thuần
    injected_content TEXT,                          -- Nội dung nhúng Breadcrumbs + Title phục vụ RAG
    metadata JSONB,                                 -- Header, page, category, rules
    embedding VECTOR(768),                          -- Vector 768d (bkai-foundation-models/vietnamese-bi-encoder)
    fts_tokens TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', immutable_unaccent(COALESCE(injected_content, content)))
    ) STORED,                                       -- TSVECTOR tự động unaccent tiếng Việt cho BM25
    tokens_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 5: SEMANTIC_CACHE (Bộ nhớ đệm ngữ nghĩa cho Chatbot Tư vấn Học vụ - Vector 768d)
CREATE TABLE semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_query TEXT NOT NULL,                  -- Câu hỏi mẫu / chuẩn hóa
    query_embedding VECTOR(768) NOT NULL,           -- Vector biểu diễn ngữ nghĩa 768d
    cached_answer TEXT NOT NULL,                    -- Câu trả lời đã lưu đệm
    retrieval_score DOUBLE PRECISION,               -- Điểm tin cậy truy xuất
    hit_count INTEGER DEFAULT 0,                    -- Số lần trúng cache
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL    -- Thời điểm hết hạn cache
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
    retrieved_chunk_ids UUID[],                     -- Danh sách ID chunk dùng làm ngữ cảnh
    feedback VARCHAR(20) CHECK (feedback IN ('like', 'dislike', 'none')) DEFAULT 'none',
    feedback_comment TEXT,
    latency_ms INTEGER,                             -- Độ trễ phản hồi (ms)
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 8: DOCUMENT_TRANSLATIONS (Dịch tài liệu PDF/Docx/Pptx & Theo dõi tiến độ)
CREATE TABLE document_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,                 -- 'pdf', 'docx', 'pptx'
    file_size_bytes BIGINT,
    pages_or_slides VARCHAR(50),
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL,
    original_file_url TEXT,                         -- URL file gốc trên Supabase / MinIO Storage
    translated_file_url TEXT,                       -- URL file song ngữ sau khi dịch
    status VARCHAR(50) DEFAULT 'pending',           -- 'pending', 'processing', 'completed', 'failed'
    progress INT DEFAULT 0,                         -- Tiến độ xử lý 0% - 100%
    status_message TEXT DEFAULT '',                 -- Message trạng thái chi tiết theo thời gian thực
    error_message TEXT,                             -- Ghi nhận thông báo lỗi nếu thất bại
    summary_json JSONB,                             -- Tóm tắt tài liệu AI (Executive summary, key takeaways)
    glossary_json JSONB DEFAULT '[]'::jsonb,        -- Từ điển thuật ngữ trích xuất từ tài liệu
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 9: DOC_VECTORS (Workspace Document RAG - Vector 1024d BAAI/bge-m3 + Hard Payload Filtering)
CREATE TABLE doc_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL,                           -- Khóa liên kết với document_translations.id
    user_id TEXT NOT NULL,                          -- Phục vụ Hard Payload Filtering theo người dùng
    parent_id TEXT,                                 -- ID đoạn cha trong Hierarchical Chunking
    page_number INT NOT NULL,                       -- Số trang phục vụ trích dẫn số trang chính xác
    chunk_index INT NOT NULL,                       -- Thứ tự chunk
    content TEXT NOT NULL,                          -- Nội dung đoạn văn gốc
    translated_content TEXT NOT NULL,               -- Nội dung bản dịch tương ứng
    injected_content TEXT NOT NULL,                 -- Văn bản cấu trúc bổ sung ngữ cảnh
    metadata JSONB DEFAULT '{}'::jsonb,             -- Thông tin phụ trợ (tiêu đề mục, bảng, hình ảnh)
    embedding VECTOR(1024),                         -- Vector 1024 chiều (mô hình BAAI/bge-m3)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 10: FLASHCARD_DECKS (Sổ thẻ từ vựng phân loại theo ngôn ngữ)
CREATE TABLE flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lang_code VARCHAR(10) NOT NULL,                 -- 'en', 'de', 'ja', 'zh', 'ko'...
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon_flag VARCHAR(10) DEFAULT '🌐',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 11: FLASHCARDS (Thẻ từ vựng & Chuẩn hóa Thuật toán Lặp ngắt quãng FSRS v4/v5)
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID REFERENCES flashcard_decks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    term VARCHAR(500) NOT NULL,                     -- Từ vựng / Cụm từ gốc
    definition TEXT NOT NULL,                       -- Định nghĩa / Nghĩa tiếng Việt
    example TEXT,                                   -- Ví dụ minh họa thực tế
    part_of_speech VARCHAR(50),                     -- Từ loại (noun, verb, adj...)
    phonetic VARCHAR(255),                          -- Phiên âm quốc tế IPA
    audio_url TEXT,                                 -- URL phát âm Audio TTS (MinIO CAS)
    lang_code VARCHAR(10) DEFAULT 'en',             -- Mã ngôn ngữ
    
    -- Các tham số chuẩn hóa của thuật toán FSRS (Free Spaced Repetition Scheduler v4/v5)
    state INT DEFAULT 0,                            -- 0: New, 1: Learning, 2: Review, 3: Relearning
    reps INT DEFAULT 0,                             -- Số lần ôn tập thành công liên tiếp
    lapses INT DEFAULT 0,                           -- Số lần quên / đánh giá Again
    stability DOUBLE PRECISION DEFAULT 0.0,         -- Độ bền trí nhớ (S)
    difficulty DOUBLE PRECISION DEFAULT 0.0,        -- Độ khó của thẻ (D: 1 - 10)
    elapsed_days INT DEFAULT 0,                     -- Số ngày trôi qua từ lần ôn tập trước
    scheduled_days INT DEFAULT 0,                   -- Khoảng cách ngày lên lịch ôn tiếp theo
    last_review TIMESTAMP WITH TIME ZONE,           -- Thời điểm ôn gần nhất (FSRS)
    due TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Thời hạn cần ôn tập tiếp theo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- BẢNG 12: REVIEW_LOGS (Nhật ký lịch sử từng lần chấm điểm thẻ FSRS)
CREATE TABLE review_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES flashcards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,    -- Liên kết sinh viên phục vụ thống kê Streak / Heatmap
    grade INT NOT NULL,                             -- Đánh giá: 1: Again, 2: Hard, 3: Good, 4: Easy
    state INT DEFAULT 0,                            -- Trạng thái thẻ tại thời điểm ôn
    stability DOUBLE PRECISION,                     -- Độ bền tính toán mới
    difficulty DOUBLE PRECISION,                    -- Độ khó tính toán mới
    elapsed_days INT DEFAULT 0,                     -- Số ngày thực tế giữa 2 lần ôn
    scheduled_days INT DEFAULT 0,                   -- Khoảng thời gian đã lên lịch
    duration_ms INT,                                -- Thời gian người dùng suy nghĩ trả lời (ms)
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================================
-- 3. GẮN TRIGGER VÀ TẠO CHỈ MỤC INDEXES TỐI ƯU
-- ====================================================================================

-- Triggers tự động cập nhật updated_at
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_documents_modtime BEFORE UPDATE ON documents FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_conversations_modtime BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE TRIGGER update_flashcard_decks_modtime BEFORE UPDATE ON flashcard_decks FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Chỉ mục Khóa ngoại & Tra cứu nhanh (B-Tree)
CREATE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code);
CREATE INDEX IF NOT EXISTS idx_password_resets_email_otp ON password_resets(email, otp_code);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_user_id ON flashcard_decks(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_deck_id ON flashcards(deck_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_due ON flashcards(due);
CREATE INDEX IF NOT EXISTS idx_flashcards_state ON flashcards(state);
CREATE INDEX IF NOT EXISTS idx_review_logs_card_id ON review_logs(card_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_user_id ON review_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_document_translations_user_id ON document_translations(user_id);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires_at ON semantic_cache(expires_at);

-- Chỉ mục GIN cho Full-Text Search và Metadata JSONB
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_document_chunks_fts ON document_chunks USING GIN (fts_tokens);

-- Chỉ mục Hard Payload Filtering cho Document RAG Workspace
CREATE INDEX IF NOT EXISTS idx_doc_vectors_doc_user ON doc_vectors(doc_id, user_id);

-- Chỉ mục Vector HNSW (768 chiều) cho Academic Counseling Chatbot
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Chỉ mục Vector HNSW (768 chiều) cho Semantic Cache
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache 
USING hnsw (query_embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Chỉ mục Vector HNSW (1024 chiều) cho BAAI/bge-m3 Document Translation RAG
CREATE INDEX IF NOT EXISTS idx_doc_vectors_embedding ON doc_vectors 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- ====================================================================================
-- 4. HÀM TÌM KIẾM VECTOR VÀ RPC STORED PROCEDURES
-- ====================================================================================

-- HÀM 1: Hybrid Search RRF cho Academic Counseling Chatbot (Vector 768d + BM25 Simple TSVector)
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

-- HÀM 3: Tìm kiếm bộ nhớ đệm ngữ nghĩa Semantic Cache (Vector 768d)
CREATE OR REPLACE FUNCTION match_semantic_cache(
    query_vec VECTOR(768),
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

-- ====================================================================================
-- 5. CẤP QUYỀN TRUY CẬP VÀ CẤU HÌNH BẢO MẬT (GRANTS & RLS CONFIG)
-- ====================================================================================

-- Tắt RLS để Microservices truy cập liền mạch qua Direct REST/PostgREST API
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE password_resets DISABLE ROW LEVEL SECURITY;
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;
ALTER TABLE semantic_cache DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE document_translations DISABLE ROW LEVEL SECURITY;
ALTER TABLE doc_vectors DISABLE ROW LEVEL SECURITY;
ALTER TABLE flashcard_decks DISABLE ROW LEVEL SECURITY;
ALTER TABLE flashcards DISABLE ROW LEVEL SECURITY;
ALTER TABLE review_logs DISABLE ROW LEVEL SECURITY;

-- Cấp toàn quyền thao tác cho các vai trò Supabase
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, anon, authenticated, service_role;

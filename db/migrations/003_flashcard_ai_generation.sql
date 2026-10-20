-- ====================================================================================
-- 003_flashcard_ai_generation.sql  —  Hỗ trợ tính năng "Tạo từ vựng với AI" (chạy trên Supabase SQL Editor)
--
-- Nội dung:
--   1) flashcards: thêm cột example_translation (dịch câu ví dụ), level (CEFR mục tiêu), source (nguồn thẻ).
--   2) vocab_generation_usage: đếm số lượt sinh từ bằng AI mỗi người dùng mỗi ngày (giờ Việt Nam).
--
-- AN TOÀN: chỉ THÊM cột/bảng, không xóa hay sửa dữ liệu hiện có; chạy lại nhiều lần vẫn được (idempotent).
-- Chưa chạy file này thì ứng dụng vẫn hoạt động: thẻ AI được lưu không kèm 3 cột mới (có log cảnh báo)
-- và hạn mức lượt được đếm trong bộ nhớ của service (mất khi restart).
-- ====================================================================================

-- 1) Cột mở rộng cho thẻ từ vựng
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS example_translation TEXT;
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS level VARCHAR(8);       -- 'A1'..'C2' (mức người dùng chọn khi sinh)
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS source VARCHAR(16);     -- 'manual' | 'import' | 'doc' | 'ai_topic' | 'ai_text' | 'ai_image'

-- 2) Hạn mức sinh từ bằng AI theo ngày
CREATE TABLE IF NOT EXISTS vocab_generation_usage (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,                                           -- ngày theo giờ Việt Nam (UTC+7)
    used INT NOT NULL DEFAULT 0 CHECK (used >= 0),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, usage_date)
);

-- Bảo mật nhất quán với 002_auth_hardening.sql: bật RLS, không tạo policy => chỉ service_role truy cập được.
ALTER TABLE vocab_generation_usage ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON vocab_generation_usage FROM anon, authenticated;
GRANT ALL ON vocab_generation_usage TO service_role;

-- ====================================================================================
-- ROLLBACK (đang để dạng comment):
--   DROP TABLE IF EXISTS vocab_generation_usage;
--   ALTER TABLE flashcards DROP COLUMN IF EXISTS example_translation;
--   ALTER TABLE flashcards DROP COLUMN IF EXISTS level;
--   ALTER TABLE flashcards DROP COLUMN IF EXISTS source;
-- ====================================================================================

-- ====================================================================================
-- 004_flashcard_catalog.sql  —  Thư viện bộ từ vựng hệ thống ("curated decks")  (chạy trên Supabase SQL Editor)
--
-- Mô hình "clone khi bắt đầu học":
--   * Bộ từ hệ thống là một dòng flashcard_decks có is_system = TRUE, user_id NULL, kèm các thẻ (flashcards.user_id NULL).
--     Các API cá nhân (/decks, /cards, /review...) KHÔNG cho ai ghi/đọc bản ghi không có chủ; sinh viên chỉ đi qua /catalog.
--   * Khi sinh viên bấm "Thêm vào sổ của tôi", service sao chép thẻ sang một deck RIÊNG của họ (origin_deck_id trỏ về bộ gốc)
--     với trạng thái FSRS mới => tiến độ học, chỉnh sửa của từng người độc lập nhau.
--
-- AN TOÀN: chỉ THÊM cột/chỉ mục, không xóa hay sửa dữ liệu hiện có; chạy lại nhiều lần vẫn được (idempotent).
-- Chưa chạy file này thì các tính năng khác vẫn hoạt động; riêng /catalog trả 503 kèm hướng dẫn chạy migration.
-- ====================================================================================

ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS status VARCHAR(12) NOT NULL DEFAULT 'published'
    CHECK (status IN ('draft', 'published', 'archived'));      -- chỉ có ý nghĩa với bộ hệ thống
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS category VARCHAR(40);   -- 'communication' | 'food' | 'going_out' | 'home_health' ...
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS level VARCHAR(8);       -- 'A1'..'C2'
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS slug VARCHAR(80);       -- định danh ổn định để nạp lại (seed) mà không trùng
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS origin_deck_id UUID
    REFERENCES flashcard_decks(id) ON DELETE SET NULL;                       -- bản sao của bộ hệ thống nào (xóa bộ gốc không xóa bản sao)

-- Mỗi sinh viên chỉ có tối đa MỘT bản sao cho mỗi bộ hệ thống (làm cho thao tác clone idempotent, kể cả khi bấm đúp).
CREATE UNIQUE INDEX IF NOT EXISTS uq_flashcard_decks_user_origin
    ON flashcard_decks (user_id, origin_deck_id) WHERE origin_deck_id IS NOT NULL;

-- Mỗi slug chỉ xuất hiện một lần trong các bộ hệ thống.
CREATE UNIQUE INDEX IF NOT EXISTS uq_flashcard_decks_system_slug
    ON flashcard_decks (slug) WHERE is_system;

CREATE INDEX IF NOT EXISTS idx_flashcard_decks_catalog
    ON flashcard_decks (category, level) WHERE is_system AND status = 'published';

-- RLS đã bật ở 002_auth_hardening.sql: không tạo policy => chỉ service_role (các microservice) truy cập được.

-- ====================================================================================
-- ROLLBACK (đang để dạng comment; xóa bộ hệ thống trước nếu muốn:  DELETE FROM flashcard_decks WHERE is_system;):
--   DROP INDEX IF EXISTS idx_flashcard_decks_catalog;
--   DROP INDEX IF EXISTS uq_flashcard_decks_system_slug;
--   DROP INDEX IF EXISTS uq_flashcard_decks_user_origin;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS origin_deck_id;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS slug;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS level;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS category;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS status;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS is_system;
-- ====================================================================================

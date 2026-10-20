-- ====================================================================================
-- 005_flashcard_languages.sql  —  Flashcard theo 10 ngôn ngữ (chạy trên Supabase SQL Editor)
--
-- Nguyên tắc: DECK là đơn vị ngôn ngữ (thẻ luôn cùng ngôn ngữ với deck chứa nó) và KHÔNG ĐOÁN ngôn ngữ của dữ liệu cũ.
--   * lang_confirmed : ngôn ngữ của deck đã được xác nhận chắc chắn hay chưa. Deck chưa xác nhận hiện ở mục
--                      "Cần xác nhận ngôn ngữ" trong giao diện cho tới khi người dùng chọn lại.
--   * is_default     : "Sổ mặc định" của một ngôn ngữ (nơi lưu từ khi dịch mà chưa chọn sổ). Mỗi người tối đa một sổ
--                      mặc định cho mỗi ngôn ngữ (chỉ mục UNIQUE một phần) nên tạo song song cũng không sinh trùng.
--   * target_lang    : ngôn ngữ giải nghĩa của thẻ ('vi'). NULL = chưa xác định (thẻ cũ).
--
-- AN TOÀN: chỉ THÊM cột/chỉ mục và đặt cờ cho dữ liệu có nguồn gốc chắc chắn; không đổi lang_code của bất kỳ bản ghi nào.
-- Chạy lại nhiều lần vẫn được (idempotent). Chưa chạy file này thì các tính năng cũ vẫn hoạt động; riêng các API mới
-- (/languages, /cards/from-translation) trả 503 kèm hướng dẫn chạy migration.
-- ====================================================================================

ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS lang_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE flashcard_decks ADD COLUMN IF NOT EXISTS is_default BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE flashcards ADD COLUMN IF NOT EXISTS target_lang VARCHAR(10);

CREATE UNIQUE INDEX IF NOT EXISTS uq_flashcard_decks_user_lang_default
    ON flashcard_decks (user_id, lang_code) WHERE is_default;
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_user_lang
    ON flashcard_decks (user_id, lang_code);

-- Backfill CHỈ khi nguồn gốc chắc chắn:
--  1) bộ hệ thống và bản sao của bộ hệ thống (nội dung do AI/curated sinh theo ngôn ngữ đã biết);
UPDATE flashcard_decks SET lang_confirmed = TRUE
 WHERE NOT lang_confirmed AND (is_system OR origin_deck_id IS NOT NULL);

--  2) deck có thẻ và MỌI thẻ đều do AI/curated sinh (cột source do hệ thống ghi, không phải người nhập).
UPDATE flashcard_decks d SET lang_confirmed = TRUE
 WHERE NOT d.lang_confirmed
   AND EXISTS (SELECT 1 FROM flashcards c WHERE c.deck_id = d.id)
   AND NOT EXISTS (SELECT 1 FROM flashcards c WHERE c.deck_id = d.id
                    AND (c.source IS NULL OR c.source NOT IN ('ai_topic', 'ai_text', 'ai_image', 'curated')));

--  3) ngôn ngữ giải nghĩa: các thẻ AI/curated luôn có nghĩa tiếng Việt. Thẻ khác để NULL (không đoán).
UPDATE flashcards SET target_lang = 'vi'
 WHERE target_lang IS NULL AND source IN ('ai_topic', 'ai_text', 'ai_image', 'curated');

-- RLS đã bật ở 002_auth_hardening.sql: không tạo policy => chỉ service_role (các microservice) truy cập được.

-- ====================================================================================
-- ROLLBACK (đang để dạng comment):
--   DROP INDEX IF EXISTS idx_flashcard_decks_user_lang;
--   DROP INDEX IF EXISTS uq_flashcard_decks_user_lang_default;
--   ALTER TABLE flashcards DROP COLUMN IF EXISTS target_lang;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS is_default;
--   ALTER TABLE flashcard_decks DROP COLUMN IF EXISTS lang_confirmed;
-- ====================================================================================

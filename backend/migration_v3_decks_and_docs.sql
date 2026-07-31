-- ====================================================================================
-- MIGRATION SCRIPT V3: BỔ SUNG BẢNG CHO SỔ THẺ FLASHCARD (DECKS) VÀ DỊCH TÀI LIỆU
-- Sử dụng khi database đã có dữ liệu (Không làm mất dữ liệu cũ)
-- ====================================================================================

-- 1. BẢNG MỚI: FLASHCARD_DECKS (Sổ thẻ từ vựng phân loại theo ngôn ngữ)
CREATE TABLE IF NOT EXISTS flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lang_code VARCHAR(10) NOT NULL,           -- en, de, ja, zh, ko, fr...
    title VARCHAR(255) NOT NULL,              -- Sổ từ vựng Tiếng Anh...
    description TEXT,
    icon_flag VARCHAR(10) DEFAULT '🌐',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. CẬP NHẬT BẢNG CŨ: FLASHCARDS (Bổ sung cột deck_id, example, lang_code)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'deck_id') THEN
        ALTER TABLE flashcards ADD COLUMN deck_id UUID REFERENCES flashcard_decks(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'example') THEN
        ALTER TABLE flashcards ADD COLUMN example TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'lang_code') THEN
        ALTER TABLE flashcards ADD COLUMN lang_code VARCHAR(10) DEFAULT 'en';
    END IF;
END $$;

-- 3. BẢNG MỚI: DOCUMENT_TRANSLATIONS (Lịch sử dịch & Tóm tắt tài liệu PDF / PPT / Word)
CREATE TABLE IF NOT EXISTS document_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,          -- Tên tài liệu gốc
    file_type VARCHAR(20) NOT NULL,           -- 'pdf', 'docx', 'pptx'
    file_size_bytes BIGINT,                   -- Kích thước file (bytes)
    pages_or_slides VARCHAR(50),              -- Số trang / slides ước tính
    source_lang VARCHAR(10) NOT NULL,         -- Ngôn ngữ gốc
    target_lang VARCHAR(10) NOT NULL,         -- Ngôn ngữ đích
    translated_file_url TEXT,                 -- Đường dẫn lưu file đã dịch để tải về
    summary_json JSONB,                       -- Tóm tắt AI (Executive summary, Key points, Key terminology)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. TẠO INDEX CHO BẢNG MỚI
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_user_id ON flashcard_decks(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_deck_id ON flashcards(deck_id);
CREATE INDEX IF NOT EXISTS idx_document_translations_user_id ON document_translations(user_id);

-- 5. TRIGGER TỰ ĐỘNG CẬP NHẬT UPDATED_AT CHO FLASHCARD_DECKS
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_flashcard_decks_modtime') THEN
        CREATE TRIGGER update_flashcard_decks_modtime 
        BEFORE UPDATE ON flashcard_decks 
        FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
    END IF;
END $$;

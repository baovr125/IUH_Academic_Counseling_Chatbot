-- ====================================================================================
-- MIGRATION SCRIPT V9: NÂNG CẤP FSRS VÀ TẠO BẢNG LỊCH SỬ ÔN TẬP
-- ====================================================================================

DO $$ 
BEGIN
    -- Thêm các cột cho thuật toán FSRS vào bảng flashcards
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'repetition') THEN
        ALTER TABLE flashcards ADD COLUMN repetition INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'stability') THEN
        ALTER TABLE flashcards ADD COLUMN stability DOUBLE PRECISION;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'difficulty') THEN
        ALTER TABLE flashcards ADD COLUMN difficulty DOUBLE PRECISION;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'next_review_date') THEN
        ALTER TABLE flashcards ADD COLUMN next_review_date TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Tạo bảng review_logs lưu lịch sử ôn tập FSRS
CREATE TABLE IF NOT EXISTS review_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES flashcards(id) ON DELETE CASCADE,
    grade INT NOT NULL, -- 1: Again, 2: Hard, 3: Good, 4: Easy
    stability DOUBLE PRECISION,
    difficulty DOUBLE PRECISION,
    duration_ms INT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_logs_card_id ON review_logs(card_id);

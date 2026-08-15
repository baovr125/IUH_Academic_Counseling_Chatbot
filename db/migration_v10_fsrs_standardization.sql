-- ====================================================================================
-- MIGRATION SCRIPT V10: CHUẨN HÓA CƠ SỞ DỮ LIỆU FSRS VÀ BẢNG NHẬT KÝ ÔN TẬP
-- ====================================================================================

DO $$ 
BEGIN
    -- 1. Bổ sung các cột FSRS chuẩn vào bảng flashcards
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'state') THEN
        ALTER TABLE flashcards ADD COLUMN state INT DEFAULT 0; -- 0: New, 1: Learning, 2: Review, 3: Relearning
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'reps') THEN
        ALTER TABLE flashcards ADD COLUMN reps INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'lapses') THEN
        ALTER TABLE flashcards ADD COLUMN lapses INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'stability') THEN
        ALTER TABLE flashcards ADD COLUMN stability DOUBLE PRECISION DEFAULT 0.0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'difficulty') THEN
        ALTER TABLE flashcards ADD COLUMN difficulty DOUBLE PRECISION DEFAULT 0.0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'elapsed_days') THEN
        ALTER TABLE flashcards ADD COLUMN elapsed_days INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'scheduled_days') THEN
        ALTER TABLE flashcards ADD COLUMN scheduled_days INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'last_review') THEN
        ALTER TABLE flashcards ADD COLUMN last_review TIMESTAMP WITH TIME ZONE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'due') THEN
        ALTER TABLE flashcards ADD COLUMN due TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;

    -- Đồng bộ dữ liệu cũ nếu next_review_date có sẵn
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'next_review_date') THEN
        UPDATE flashcards SET due = next_review_date WHERE due IS NULL AND next_review_date IS NOT NULL;
    END IF;

    -- 2. Chuẩn hóa bảng review_logs
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_logs' AND column_name = 'state') THEN
        ALTER TABLE review_logs ADD COLUMN state INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_logs' AND column_name = 'rating') THEN
        ALTER TABLE review_logs ADD COLUMN rating INT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_logs' AND column_name = 'elapsed_days') THEN
        ALTER TABLE review_logs ADD COLUMN elapsed_days INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_logs' AND column_name = 'scheduled_days') THEN
        ALTER TABLE review_logs ADD COLUMN scheduled_days INT DEFAULT 0;
    END IF;
END $$;

-- Tạo index hỗ trợ truy vấn các thẻ cần ôn tập hôm nay
CREATE INDEX IF NOT EXISTS idx_flashcards_due ON flashcards(due);
CREATE INDEX IF NOT EXISTS idx_flashcards_state ON flashcards(state);

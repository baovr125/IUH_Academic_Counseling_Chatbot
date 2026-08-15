-- ====================================================================================
-- MIGRATION SCRIPT V8: THÊM CỘT PHONETIC VÀ AUDIO_URL CHO BẢNG FLASHCARDS
-- ====================================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'phonetic') THEN
        ALTER TABLE flashcards ADD COLUMN phonetic VARCHAR(255);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'flashcards' AND column_name = 'audio_url') THEN
        ALTER TABLE flashcards ADD COLUMN audio_url TEXT;
    END IF;
END $$;

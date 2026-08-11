-- ====================================================================================
-- MIGRATION SCRIPT V7: BỔ SUNG CỘT BẢNG DOCUMENT_TRANSLATIONS CHO SUPABASE STORAGE & ERROR LOGGING
-- ====================================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'original_file_url') THEN
        ALTER TABLE document_translations ADD COLUMN original_file_url TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'document_translations' AND column_name = 'error_message') THEN
        ALTER TABLE document_translations ADD COLUMN error_message TEXT;
    END IF;
END $$;

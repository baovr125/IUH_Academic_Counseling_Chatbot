-- ====================================================================================
-- MIGRATION SCRIPT V5: CÀI ĐẶT CẤU HÌNH NGƯỜI DÙNG
-- ====================================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'settings') THEN
        ALTER TABLE users ADD COLUMN settings JSONB DEFAULT '{"theme": "light", "language": "vi"}'::jsonb;
    END IF;
END $$;

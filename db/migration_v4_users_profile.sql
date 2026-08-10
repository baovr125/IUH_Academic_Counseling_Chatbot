-- ====================================================================================
-- MIGRATION SCRIPT V4: BỔ SUNG CÁC CỘT QUẢN LÝ HỒ SƠ SINH VIÊN
-- ====================================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'student_code') THEN
        ALTER TABLE users ADD COLUMN student_code VARCHAR(50) UNIQUE DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'department') THEN
        ALTER TABLE users ADD COLUMN department VARCHAR(150) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'major') THEN
        ALTER TABLE users ADD COLUMN major VARCHAR(150) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'phone_number') THEN
        ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) DEFAULT NULL;
    END IF;
END $$;

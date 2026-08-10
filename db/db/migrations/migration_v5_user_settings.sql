-- ====================================================================================
-- SCRIPT MIGRATION V5: TẠO BẢNG USER_SETTINGS
-- Dự án: IUH Portal AI (Lưu trữ cài đặt cá nhân người dùng: giao diện, ngôn ngữ, thông báo)
-- ====================================================================================

CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'vi',
    sound_enabled BOOLEAN DEFAULT TRUE,
    academic_alerts BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tạo Index trên user_id giúp tăng tốc độ truy vấn cài đặt theo từng người dùng
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

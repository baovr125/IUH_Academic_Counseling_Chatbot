-- ====================================================================================
-- SCRIPT MIGRATION V4: NÂNG CẤP BẢNG USERS VÀ TẠO BẢNG PASSWORD_RESETS
-- Dự án: IUH Portal AI (Hỗ trợ 2 chế độ người dùng: Sinh viên IUH & Người dùng công cộng)
-- ====================================================================================

-- 1. THÊM CÁC CỘT HỒ SƠ & PHÂN LOẠI ĐỐI TƯỢNG VÀO BẢNG USERS
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS student_code VARCHAR(50) UNIQUE DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS department VARCHAR(150) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS major VARCHAR(150) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20) DEFAULT NULL;

-- Cập nhật chỉ mục cho cột student_code để truy vấn nhanh
CREATE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code);

-- 2. TẠO BẢNG PASSWORD_RESETS (LƯU TRỮ MÃ OTP KHÔI PHỤC MẬT KHẨU)
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tạo Index trên cặp (email, otp_code) giúp tăng tốc độ kiểm tra OTP khôi phục mật khẩu
CREATE INDEX IF NOT EXISTS idx_password_resets_email_otp ON password_resets(email, otp_code);

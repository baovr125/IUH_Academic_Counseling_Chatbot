-- ====================================================================================
-- 002_auth_hardening.sql  —  Siết bảo mật cơ sở dữ liệu (chạy trên Supabase SQL Editor)
--
-- THỨ TỰ TRIỂN KHAI (quan trọng):
--   1. Đảm bảo .env có SUPABASE_SERVICE_ROLE_KEY (khóa sb_secret_...) và mọi service đã được build lại
--      từ mã mới (auth/flashcard/chatbot/translation đều ưu tiên khóa service-role).
--   2. Chạy thử các luồng chính (đăng ký, đăng nhập, chat, flashcard, dịch).
--   3. Chạy file này. Khóa service-role BỎ QUA RLS nên các service vẫn hoạt động;
--      khóa publishable (anon) từ đây không còn đọc/ghi được dữ liệu.
--
-- File an toàn khi chạy lại (idempotent). Có phần rollback ở cuối (đang để dạng comment).
-- ====================================================================================

-- 1) Cột phục vụ thu hồi token (đăng xuất phía server / đổi mật khẩu vô hiệu hóa token cũ).
--    Mã auth-service tự nhận biết cột này; chưa chạy bước này thì mọi thứ vẫn hoạt động
--    nhưng "đăng xuất" chỉ xóa token ở trình duyệt.
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

-- 2) Bật Row Level Security cho MỌI bảng trong schema public (không tạo policy => anon/authenticated bị từ chối).
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;

-- 3) Thu hồi quyền của các vai trò công khai của Supabase.
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated;

-- service_role (dùng bởi các microservice) giữ toàn quyền.
GRANT ALL ON ALL TABLES    IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- ====================================================================================
-- KIỂM TRA SAU KHI CHẠY
-- ====================================================================================
-- (a) Mọi bảng phải có relrowsecurity = true:
--   SELECT relname, relrowsecurity FROM pg_class
--   WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' ORDER BY relname;
-- (b) anon/authenticated không còn quyền nào trên bảng users (kết quả rỗng là đúng):
--   SELECT grantee, privilege_type FROM information_schema.role_table_grants
--   WHERE table_schema = 'public' AND table_name = 'users' AND grantee IN ('anon', 'authenticated');
-- (c) Từ máy bất kỳ, gọi PostgREST bằng khóa publishable phải trả mảng rỗng hoặc lỗi 401/403:
--   curl "$SUPABASE_URL/rest/v1/users?select=id&limit=1" -H "apikey: $SUPABASE_KEY"

-- ====================================================================================
-- ROLLBACK (chỉ dùng khi cần khôi phục trạng thái cũ — KHÔNG khuyến nghị)
-- ====================================================================================
-- ALTER TABLE users DROP COLUMN IF EXISTS token_version;
-- (Bật lại quyền anon/RLS tắt = quay lại trạng thái dễ bị đọc trộm bảng users; đừng làm trên môi trường công khai.)

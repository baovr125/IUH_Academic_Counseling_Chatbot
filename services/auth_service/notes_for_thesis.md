# Ghi Chú Kỹ Thuật Khóa Luận: Authentication & User Service (`auth_service`)

> Tài liệu này mô tả **đúng với mã hiện tại** (cập nhật sau đợt rà soát bảo mật tháng 10/2026; xem `word/Report/auth_service/AUTH_EVALUATION.md` và `AUTH_REMEDIATION.md`). Những gì chưa làm được ghi rõ ở mục 7.

---

## 1. Bài toán và mục tiêu thiết kế
Hệ thống microservice phục vụ sinh viên IUH và người dùng công cộng cần một dịch vụ định danh:
1. **Xác thực không trạng thái ở các service nghiệp vụ**: Kong và các service kiểm token bằng chữ ký, không gọi ngược auth-service ở mỗi yêu cầu.
2. **Hai nhóm người dùng**: Sinh viên/GV IUH (có MSSV, Khoa, Ngành, email `@student.iuh.edu.vn` hoặc `@iuh.edu.vn`) và người dùng công cộng; thêm vai trò `admin` do quản trị gán thủ công.
3. **Bảo vệ tài khoản**: băm mật khẩu bcrypt, chống dò mật khẩu, không lộ tài khoản tồn tại, không tin dữ liệu do client tự khai báo.
4. **Fail-closed**: cấu hình bảo mật thiếu/yếu thì dịch vụ không khởi động; DB không xác nhận được người dùng thì từ chối.

## 2. Kiến trúc & công nghệ

| Thành phần | Công nghệ | Ghi chú |
| :--- | :--- | :--- |
| Framework | FastAPI, Pydantic v2 | handler là hàm đồng bộ (`def`) để chạy trong threadpool, bcrypt không chặn event loop |
| Token | `python-jose`, JWT **HS256** | thuật toán cố định (không cấu hình được), bắt buộc `exp`, `iss`, `sub` |
| Mật khẩu | `bcrypt` (cost 12) | gọi trực tiếp, không dùng passlib |
| CSDL | PostgreSQL (Supabase) qua PostgREST | khóa **service-role**, RLS bật và không có policy cho `anon` |
| Gateway | Kong 3.9 (DB-less) | plugin `jwt` kiểm chữ ký + `exp` + `iss`; rate-limit riêng cho đăng nhập/đăng ký |
| Container | `python:3.11-slim`, user không root, `HEALTHCHECK`, phụ thuộc khóa ở `requirements.lock` | |

Cấu trúc mã: `app/config.py` (cấu hình, fail-fast) → `app/routers/auth.py` (HTTP, dependency `get_current_user`) → `app/services/auth_service.py` (nghiệp vụ) → Supabase. `app/schemas/auth.py` chứa validate; `app/utils/throttle.py` chống dò mật khẩu; `app/main.py` gom xử lý lỗi theo một định dạng `{ok:false, error:{message, field?, details?}}`.

## 3. Các endpoint (qua Kong: `/api/auth/*` hoặc `/api/v1/auth/*`)

| Endpoint | Xác thực | Mô tả |
| :--- | :--- | :--- |
| `POST /register` | không | đăng ký `student`/`public`; vai trò khác luôn bị ép về `student`; **MSSV không do client gửi** mà được suy ra từ email `<8 chữ số>@student.iuh.edu.vn` (email GV `@iuh.edu.vn` hoặc local-part không phải 8 số → không có MSSV); Khoa/Ngành là chuỗi 2–150 ký tự (giao diện chọn từ danh mục IUH hoặc nhập tay qua mục "Khác…") |
| `POST /login` | không | `identifier` là email hoặc MSSV 8 số; giới hạn 10 lần/phút/IP tại Kong và khóa tạm trong service |
| `GET /me` | Bearer | thông tin người dùng đọc lại từ DB mỗi lần |
| `POST /refresh` | Bearer (còn hạn) | cấp access token mới; `role` đọc lại từ DB; tối đa 7 ngày kể từ lần đăng nhập bằng mật khẩu |
| `POST /logout` | Bearer | tăng `token_version` để thu hồi token (cần migration 002; nếu chưa có cột thì chỉ đăng xuất phía client) |
| `PUT /profile` | Bearer | chỉ `fullName`, `phoneNumber`, `department`, `major`, `avatarUrl`; **không** sửa được email/MSSV/role |
| `POST /change-password` | Bearer | bắt buộc mật khẩu hiện tại; thu hồi token cũ; trả token mới |
| `GET/PUT /settings` | Bearer | `theme`, `language`, `soundEnabled`, `academicAlerts` (enum/boolean được validate) |
| `GET /health` | không | trạng thái tiến trình |

Không có: quên/đặt lại mật khẩu, liên kết Google, `/verify-student` (endpoint giả đã được gỡ).

## 4. Luồng đăng nhập và duy trì phiên
```mermaid
sequenceDiagram
    autonumber
    actor U as Trình duyệt
    participant K as Kong (:8000)
    participant A as auth-service
    participant D as Supabase (service-role)
    participant S as Service nghiệp vụ

    U->>K: POST /api/auth/login (identifier, password)
    K->>K: rate-limit 10/phút/IP
    K->>A: chuyển tiếp (X-Real-IP, X-Request-ID)
    A->>A: throttle theo (IP, tài khoản)
    A->>D: SELECT user theo email hoặc MSSV (so khớp chính xác)
    A->>A: bcrypt.checkpw (hash giả nếu không có user)
    A-->>U: 200 {token(60 phút), user} hoặc 401/429
    U->>K: GET /api/v1/chat/... (Bearer)
    K->>K: kiểm chữ ký + iss + exp (bắt buộc)
    K->>S: chuyển tiếp
    S->>S: giải mã lại JWT; admin => claim role = "admin"
    Note over U,A: Trước khi hết hạn ~5 phút, client gọi POST /refresh.<br/>Token nhận 401 ở bất kỳ API nào => client tự đăng xuất.
```

**Claims** của access token: `sub`, `role`, `tv` (token_version), `oiat` (thời điểm đăng nhập gốc), `iat`, `exp`, `iss=iuh-auth-service`. Không chứa email/họ tên/MSSV vì token có thể xuất hiện trong URL (SSE).

## 5. Mô hình dữ liệu (bảng `users`, rút gọn)
```sql
users(id uuid PK, email unique not null, student_code unique, full_name, department, major,
      phone_number, password_hash, google_id unique, avatar_url, role default 'student',
      settings jsonb, token_version int not null default 0, created_at, updated_at)
```
`password_resets` vẫn nằm trong schema nhưng **chưa được mã sử dụng** (dành cho tính năng quên mật khẩu về sau). Script đầy đủ: `db/schema_v2_hybrid_rag.sql`; nâng cấp DB đang chạy: `db/migrations/002_auth_hardening.sql`.

## 6. Mô hình mối đe dọa và biện pháp (đối chiếu OWASP)

| Mối đe dọa | Biện pháp trong mã | Kiểm chứng tự động |
| :--- | :--- | :--- |
| Giả mạo token (API2) | secret ≥ 32 ký tự bắt buộc, từ chối giá trị mẫu; ép HS256; bắt buộc `exp`/`iss`/`sub` | `tests/unit/test_jwt.py`, `scripts/security_smoke_test.py` |
| Mạo danh qua header danh tính (API1/API5) | các service bỏ `X-User-ID`/`X-User-Role`; Kong xóa header này | `tests/unit/test_security.py` (4 service), smoke test |
| Leo quyền khi đăng ký (API5) | `role` bị ép về `student`/`public` ở 2 lớp (schema + service) | `test_cannot_register_as_admin` |
| Dò mật khẩu (API2, A07) | 10 lần/phút/IP tại Kong; khóa tạm theo (IP, tài khoản) và theo tài khoản; chính sách mật khẩu | `test_throttle.py`, `test_locks_out_after_repeated_failures...` |
| Lộ tồn tại tài khoản (A07) | thông điệp chung; bcrypt chạy cả khi không có user | `test_bcrypt_runs_even_for_unknown_account` |
| Token của user đã xóa/đổi quyền (API2) | không fail-open; `role` đọc lại từ DB khi làm mới; token_version | `test_token_of_deleted_user...`, `test_role_comes_from_database...` |
| Injection vào bộ lọc PostgREST (A03) | tra cứu bằng `eq` trên cột xác định, không ghép chuỗi `or=` | `test_injection_style_account_never_reaches_the_database` |
| Lộ chi tiết nội bộ (A05) | lỗi DB → 503 thông điệp chung; chi tiết chỉ ở log kèm `request_id` | `test_db_error_on_insert_is_generic_503`, `test_rls_error_is_generic...` |
| Đọc/ghi trực tiếp bảng `users` bằng khóa công khai (API3) | khóa service-role + RLS bật + thu quyền `anon` (migration 002) | câu SQL kiểm tra trong migration |
| Mass assignment (API3) | schema tách riêng, `extra=ignore`, chỉ các cột cho phép được UPDATE | `test_cannot_change_email_role_mssv_or_hash_through_profile` |

## 7. Hạn chế đã biết (nêu trong phần "hướng phát triển")
1. **Chưa xác minh email/MSSV**: ai cũng có thể đăng ký bằng một email `@student.iuh.edu.vn` và MSSV tùy ý (và có thể chiếm MSSV của người khác). Hướng xử lý: gửi OTP/liên kết xác thực tới email trường hoặc đối chiếu cổng thông tin IUH.
2. **Chưa có quên/đặt lại mật khẩu** (cần dịch vụ gửi email); giao diện chỉ hướng dẫn liên hệ quản trị viên.
3. **Thu hồi token chỉ có hiệu lực ở auth-service** (`/me`, `/refresh`); các service khác chấp nhận token đã ký đến khi hết hạn (tối đa 60 phút). Muốn tức thời cần kiểm tra thu hồi ở Kong/trung gian hoặc dùng token ngắn hơn.
4. **Bộ đếm chống dò mật khẩu nằm trong bộ nhớ** của một tiến trình (một replica); nhiều replica cần chuyển sang Redis.
5. **HS256 dùng chung một bí mật** giữa Kong và các service; hướng nâng cấp: RS256/JWKS (chỉ auth-service giữ khóa riêng).
6. `/api/v1/translate/tts` và `/audio` để mở (phục vụ thẻ `<audio>`), được bảo vệ bằng rate-limit chứ không bằng JWT.
7. Cookie `HttpOnly` thay cho `localStorage/sessionStorage` và CSP nghiêm ngặt chưa được áp dụng.

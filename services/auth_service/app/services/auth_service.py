import os
import uuid
import datetime
from typing import Dict, Any, Optional
import bcrypt
from jose import jwt, JWTError
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any
from app.utils.logger import logger

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-iuh-chatbot-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 days


class DuplicateEmailException(Exception):
    """Ngoại lệ khi email đã được sử dụng."""
    pass


class DuplicateStudentCodeException(Exception):
    """Ngoại lệ khi mã số sinh viên đã tồn tại."""
    pass


class InvalidCredentialsException(Exception):
    """Ngoại lệ khi sai tài khoản hoặc mật khẩu."""
    pass


class DatabaseConnectionException(Exception):
    """Ngoại lệ khi không thể kết nối tới cơ sở dữ liệu."""
    pass


def get_supabase() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.warning("Supabase credentials not configured in environment.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        logger.exception(f"Failed to initialize Supabase client: {e}")
        return None


def hash_password(password: str) -> str:
    # Truncate an toàn 72 bytes giới hạn của bcrypt và mã hóa
    safe_pwd = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(safe_pwd, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        safe_pwd = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(safe_pwd, hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Error verifying password hash: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + (
        expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "iss": "iuh-auth-service"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def register_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "student",
    student_code: Optional[str] = None,
    department: Optional[str] = None,
    major: Optional[str] = None,
) -> Dict[str, Any]:
    supabase = get_supabase()
    if not supabase:
        raise DatabaseConnectionException("Không thể kết nối đến cơ sở dữ liệu hệ thống")

    clean_email = email.strip().lower()
    clean_full_name = full_name.strip()
    clean_role = "public" if role == "public" else "student"
    clean_student_code = student_code.strip() if (clean_role == "student" and student_code) else None
    clean_department = department.strip() if (clean_role == "student" and department) else None
    clean_major = major.strip() if (clean_role == "student" and major) else None

    # 1. Kiểm tra Email đã tồn tại trong CSDL chưa
    try:
        existing_email = supabase.table("users").select("id").ilike("email", clean_email).execute()
        if existing_email.data and len(existing_email.data) > 0:
            raise DuplicateEmailException("Email đã được sử dụng")
    except DuplicateEmailException:
        raise
    except Exception as e:
        logger.warning(f"Warning checking existing email: {e}")

    # 2. Kiểm tra MSSV nếu đối tượng là Sinh viên IUH
    if clean_role == "student" and clean_student_code:
        try:
            existing_code = supabase.table("users").select("id").eq("student_code", clean_student_code).execute()
            if existing_code.data and len(existing_code.data) > 0:
                raise DuplicateStudentCodeException("Mã số sinh viên đã tồn tại")
        except DuplicateStudentCodeException:
            raise
        except Exception as e:
            logger.warning(f"Warning checking existing student_code: {e}")

    # 3. Mã hóa mật khẩu bằng bcrypt
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(password)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    user_data = {
        "id": user_id,
        "email": clean_email,
        "password_hash": hashed_pwd,
        "full_name": clean_full_name,
        "student_code": clean_student_code,
        "department": clean_department,
        "major": clean_major,
        "role": clean_role,
        "avatar_url": None,
        "settings": {"theme": "light", "language": "vi"},
        "created_at": now_iso,
        "updated_at": now_iso
    }

    # 4. Lưu thông tin người dùng vào CSDL
    try:
        res = supabase.table("users").insert(user_data).execute()
        if not res.data:
            raise RuntimeError("Lưu thông tin người dùng vào CSDL thất bại")
    except Exception as e:
        logger.exception(f"Failed to insert user to Supabase DB: {e}")
        err_msg = str(e).lower()
        if "users_email_key" in err_msg or ("email" in err_msg and "unique" in err_msg):
            raise DuplicateEmailException("Email đã được sử dụng")
        if "users_student_code_key" in err_msg or ("student_code" in err_msg and "unique" in err_msg):
            raise DuplicateStudentCodeException("Mã số sinh viên đã tồn tại")
        if "row-level security" in err_msg or "42501" in err_msg:
            raise RuntimeError("Lỗi phân quyền CSDL (RLS Policy): Bảng 'users' trên Supabase đang bật Row Level Security nhưng chưa cấp quyền INSERT. Vui lòng tắt RLS hoặc cấu hình Policy trên Supabase.")
        raise RuntimeError(f"Lỗi khi lưu tài khoản vào cơ sở dữ liệu: {e}")

    # 5. Tạo JWT Token trả về (chứa id, email, role)
    jwt_payload = {
        "sub": user_id,
        "id": user_id,
        "email": clean_email,
        "role": clean_role,
        "student_code": clean_student_code,
        "full_name": clean_full_name,
        "department": clean_department,
        "major": clean_major,
    }
    token = create_access_token(jwt_payload)

    user_response = {
        "id": user_id,
        "email": clean_email,
        "fullName": clean_full_name,
        "full_name": clean_full_name,
        "studentCode": clean_student_code,
        "student_code": clean_student_code,
        "studentId": clean_student_code,
        "department": clean_department,
        "major": clean_major,
        "role": clean_role,
        "avatarUrl": None,
        "avatar_url": None,
    }

    return {
        "message": "Đăng ký tài khoản thành công!",
        "token": token,
        "user": user_response
    }


def login_user(account: str, password: str) -> Dict[str, Any]:
    supabase = get_supabase()
    if not supabase:
        raise DatabaseConnectionException("Không thể kết nối đến cơ sở dữ liệu hệ thống")

    clean_acc = account.strip()
    if not clean_acc or not password:
        raise InvalidCredentialsException("Tài khoản hoặc mật khẩu không chính xác")

    user = None
    try:
        # Truy vấn tìm kiếm theo email (không phân biệt hoa thường) hoặc student_code
        res = (
            supabase.table("users")
            .select("*")
            .or_(f"email.ilike.{clean_acc},student_code.eq.{clean_acc}")
            .execute()
        )
        if res.data and len(res.data) > 0:
            user = res.data[0]
    except Exception as e:
        logger.exception(f"Error querying user for login: {e}")
        raise RuntimeError(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}")

    if not user:
        raise InvalidCredentialsException("Tài khoản hoặc mật khẩu không chính xác")

    # Kiểm tra mật khẩu mã hóa bcrypt
    stored_hash = user.get("password_hash")
    if not stored_hash or not verify_password(password, stored_hash):
        raise InvalidCredentialsException("Tài khoản hoặc mật khẩu không chính xác")

    # Tạo JWT token chứa id, email, role
    user_id = str(user["id"])
    email = user.get("email") or ""
    role = user.get("role") or "student"
    student_code = user.get("student_code")
    full_name = user.get("full_name") or email

    jwt_payload = {
        "sub": user_id,
        "id": user_id,
        "email": email,
        "role": role,
        "student_code": student_code,
        "full_name": full_name,
        "department": user.get("department"),
        "major": user.get("major"),
    }
    token = create_access_token(jwt_payload)

    user_response = {
        "id": user_id,
        "email": email,
        "fullName": full_name,
        "full_name": full_name,
        "studentCode": student_code,
        "student_code": student_code,
        "studentId": student_code,
        "department": user.get("department"),
        "major": user.get("major"),
        "role": role,
        "avatarUrl": user.get("avatar_url"),
        "avatar_url": user.get("avatar_url"),
    }

    return {
        "token": token,
        "user": user_response,
        "message": "Đăng nhập thành công"
    }


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            return None

        supabase = get_supabase()
        if supabase:
            try:
                res = (
                    supabase.table("users")
                    .select("id, email, full_name, student_code, department, major, role, avatar_url, created_at")
                    .eq("id", user_id)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    u = res.data[0]
                    return {
                        "id": u["id"],
                        "email": u.get("email"),
                        "fullName": u.get("full_name") or u.get("email"),
                        "full_name": u.get("full_name") or u.get("email"),
                        "studentCode": u.get("student_code"),
                        "student_code": u.get("student_code"),
                        "studentId": u.get("student_code"),
                        "department": u.get("department"),
                        "major": u.get("major"),
                        "role": u.get("role", "student"),
                        "avatarUrl": u.get("avatar_url"),
                        "avatar_url": u.get("avatar_url"),
                    }
            except Exception as e:
                logger.error(f"Error fetching user profile from DB: {e}")

        # Fallback từ JWT payload
        return {
            "id": str(user_id),
            "email": payload.get("email", ""),
            "fullName": payload.get("full_name") or payload.get("email", "Người dùng IUH"),
            "full_name": payload.get("full_name") or payload.get("email", "Người dùng IUH"),
            "studentCode": payload.get("student_code"),
            "student_code": payload.get("student_code"),
            "studentId": payload.get("student_code"),
            "department": payload.get("department"),
            "major": payload.get("major"),
            "role": payload.get("role", "student"),
            "avatarUrl": None,
            "avatar_url": None,
        }
    except JWTError as e:
        logger.warning(f"Invalid or expired JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_user_by_token: {e}")
        return None


import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, create_engine, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type when on Postgres, otherwise uses CHAR(36) for SQLite compatibility.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(str(value))
            except (ValueError, TypeError, AttributeError):
                return str(value)
        if dialect.name == "postgresql":
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            return value


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def init_engine():
    if "sqlite" in DATABASE_URL:
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    try:
        eng = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        with eng.connect() as conn:
            pass
        print("[DATABASE] Kết nối PostgreSQL (Supabase) thành công!", flush=True)
        return eng
    except Exception as e:
        print(f"[DATABASE WARNING] Không thể kết nối PostgreSQL ({e}). Đang chuyển sang CSDL SQLite cục bộ...", flush=True)
        print("[DATABASE HINT] Vui lòng kiểm tra lại mật khẩu CSDL Supabase trong DATABASE_URL ở file .env", flush=True)
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(db_dir, exist_ok=True)
        sqlite_path = os.path.join(db_dir, "app.db")
        sqlite_url = f"sqlite:///{sqlite_path}"
        eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        return eng


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserSetting(Base):
    """
    Model ánh xạ bảng user_settings trong CSDL (PostgreSQL / SQLite fallback):
    """
    __tablename__ = "user_settings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    theme = Column(String(20), default="light")
    language = Column(String(10), default="vi")
    sound_enabled = Column(Boolean, default=True)
    academic_alerts = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_response_dict(self) -> dict:
        return {
            "theme": self.theme or "light",
            "language": self.language or "vi",
            "soundEnabled": self.sound_enabled if self.sound_enabled is not None else True,
            "academicAlerts": self.academic_alerts if self.academic_alerts is not None else True,
        }


class User(Base):
    """
    Model ánh xạ bảng users trong CSDL (PostgreSQL / SQLite fallback):
    """
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    student_code = Column(String(50), unique=True, nullable=True, index=True)
    department = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(Text, nullable=True)
    role = Column(String(50), default="student")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_response_dict(self) -> dict:
        id_str = str(self.id) if self.id else ""
        return {
            "id": id_str,
            "fullName": self.full_name or "",
            "email": self.email or "",
            "studentCode": self.student_code,
            "department": self.department,
            "major": self.major,
            "phoneNumber": self.phone_number,
            "role": self.role or "student",
            "avatarUrl": self.avatar_url,
            "google_id": self.google_id,
            "googleId": self.google_id,
            "password_hash": self.password_hash,
            "passwordHash": self.password_hash,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class PasswordReset(Base):
    """
    Model ánh xạ bảng password_resets trong CSDL
    """
    __tablename__ = "password_resets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


def get_db():
    """Dependency cung cấp SQLAlchemy Session cho mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

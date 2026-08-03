import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.rsvwbkuqzksqfybvcwvl:Khoa%3Biam2026%40@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
)

# Chuyển đổi postgres:// thành postgresql:// cho tương thích với SQLAlchemy 2.x
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """
    Model ánh xạ bảng users trong CSDL PostgreSQL (Supabase):
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(Text, nullable=True)
    role = Column(String(50), default="student")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_response_dict(self) -> dict:
        """Chuyển đổi đối tượng User ORM sang định dạng dictionary cho API Response."""
        id_str = str(self.id) if self.id else ""
        return {
            "id": id_str,
            "fullName": self.full_name or "",
            "email": self.email or "",
            "studentCode": self.email.split("@")[0] if "@iuh.edu.vn" in (self.email or "") else None,
            "role": self.role or "student",
            "avatarUrl": self.avatar_url,
            "google_id": self.google_id,
            "googleId": self.google_id,
            "password_hash": self.password_hash,
            "passwordHash": self.password_hash,
        }


def get_db():
    """Dependency cung cấp SQLAlchemy Session cho mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

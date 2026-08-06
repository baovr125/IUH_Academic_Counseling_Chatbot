import uuid
from datetime import datetime, timezone
from database import SessionLocal, User
from app.utils.security import hash_password

db = SessionLocal()

dev_email = "dev@iuh.edu.vn"
dev_user = db.query(User).filter(User.email == dev_email).first()

if not dev_user:
    now_utc = datetime.now(timezone.utc)
    # create the user
    new_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        full_name="Sinh viên Thử nghiệm (Test Mode)",
        email=dev_email,
        student_code="SV2026001",
        department="Khoa Công nghệ Thông tin",
        major="Kỹ thuật Phần mềm",
        password_hash=hash_password("password123"),
        role="student",
        avatar_url="https://lh3.googleusercontent.com/a/default-user=s96-c",
        created_at=now_utc,
        updated_at=now_utc,
    )
    db.add(new_user)
    db.commit()
    print("Created dev user successfully.")
else:
    print("Dev user already exists. Updating password just in case.")
    dev_user.password_hash = hash_password("password123")
    db.commit()

db.close()

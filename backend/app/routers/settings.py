import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import User, UserSetting, get_db
from app.schemas.settings import UserSettingsResponse, UpdateSettingsRequest
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/api/settings", tags=["User Settings"])


def _get_user_object(current_user_id: str, db: Session) -> User:
    user = None
    try:
        user_uuid = uuid.UUID(current_user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
    except ValueError:
        user = db.query(User).filter(User.email == current_user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại hoặc đã bị xóa.",
        )
    return user


@router.get("", status_code=status.HTTP_200_OK)
def get_user_settings(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    GET /api/settings:
    - Đọc cài đặt hệ thống cá nhân của người dùng hiện tại từ JWT Token.
    - Khởi tạo mặc định nếu chưa có bản ghi cài đặt trong bảng user_settings.
    """
    user = _get_user_object(current_user_id, db)
    setting = db.query(UserSetting).filter(UserSetting.user_id == user.id).first()

    if not setting:
        now_utc = datetime.now(timezone.utc)
        setting = UserSetting(
            id=uuid.uuid4(),
            user_id=user.id,
            theme="light",
            language="vi",
            sound_enabled=True,
            academic_alerts=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return {
        "ok": True,
        "data": setting.to_response_dict(),
    }


@router.put("", status_code=status.HTTP_200_OK)
def update_user_settings(
    payload: UpdateSettingsRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    PUT /api/settings:
    - Cập nhật cài đặt giao diện, ngôn ngữ, và thông báo cho người dùng hiện tại.
    """
    user = _get_user_object(current_user_id, db)
    setting = db.query(UserSetting).filter(UserSetting.user_id == user.id).first()

    if not setting:
        now_utc = datetime.now(timezone.utc)
        setting = UserSetting(
            id=uuid.uuid4(),
            user_id=user.id,
            theme="light",
            language="vi",
            sound_enabled=True,
            academic_alerts=True,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(setting)

    if payload.theme is not None:
        if payload.theme in ["light", "dark", "system"]:
            setting.theme = payload.theme
    if payload.language is not None:
        if payload.language in ["vi", "en"]:
            setting.language = payload.language
    if payload.soundEnabled is not None:
        setting.sound_enabled = payload.soundEnabled
    if payload.academicAlerts is not None:
        setting.academic_alerts = payload.academicAlerts

    setting.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(setting)

    return {
        "ok": True,
        "data": setting.to_response_dict(),
    }

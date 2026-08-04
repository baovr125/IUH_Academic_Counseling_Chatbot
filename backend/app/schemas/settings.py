from typing import Optional, Literal
from pydantic import BaseModel, Field


class UserSettingsResponse(BaseModel):
    """Schema chuẩn trả về cài đặt người dùng."""
    theme: Literal["light", "dark", "system"] = Field("light", description="Giao diện: 'light', 'dark', hoặc 'system'")
    language: Literal["vi", "en"] = Field("vi", description="Ngôn ngữ: 'vi' hoặc 'en'")
    soundEnabled: bool = Field(True, description="Trạng thái phát âm thanh thông báo")
    academicAlerts: bool = Field(True, description="Trạng thái nhận thông báo học vụ mới từ IUH")

    class Config:
        from_attributes = True


class UpdateSettingsRequest(BaseModel):
    """Schema payload cho API cập nhật cài đặt người dùng."""
    theme: Optional[Literal["light", "dark", "system"]] = Field(None, description="Giao diện mới: 'light', 'dark', hoặc 'system'")
    language: Optional[Literal["vi", "en"]] = Field(None, description="Ngôn ngữ mới: 'vi' hoặc 'en'")
    soundEnabled: Optional[bool] = Field(None, description="Bật/Tắt âm thanh thông báo")
    academicAlerts: Optional[bool] = Field(None, description="Bật/Tắt thông báo học vụ từ IUH")

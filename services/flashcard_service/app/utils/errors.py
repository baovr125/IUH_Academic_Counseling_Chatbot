from typing import Any, Optional


class ApiError(Exception):
    """
    Lỗi nghiệp vụ có mã máy đọc được. main.py trả về {"ok": false, "error": {"code", "message", "data"?}} cùng mã HTTP;
    frontend (`request()` trong flashcardService.ts) đọc `error.message` và `error.code`.
    """

    def __init__(self, status: int, code: str, message: str, data: Optional[Any] = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.data = data

"""Chống dò mật khẩu: đếm đăng nhập thất bại theo (IP, tài khoản) và theo tài khoản.

Lưu trong bộ nhớ của tiến trình (đủ cho một replica). Nếu sau này chạy nhiều replica, thay
``_failures`` bằng Redis (dự án đã có sẵn) — giao diện lớp giữ nguyên.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from app import config


class LoginThrottle:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._failures: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    @staticmethod
    def _key_ip(ip: str, account: str) -> Tuple[str, str]:
        return ("ip", f"{ip}|{account.lower()}")

    @staticmethod
    def _key_account(account: str) -> Tuple[str, str]:
        return ("acc", account.lower())

    def _prune(self, q: Deque[float], now: float) -> None:
        while q and now - q[0] > config.LOGIN_LOCK_SECONDS:
            q.popleft()

    def retry_after(self, ip: str, account: str) -> int:
        """Số giây còn bị khóa (0 nếu được phép thử)."""
        now = time.monotonic()
        with self._lock:
            for key, limit in (
                (self._key_ip(ip, account), config.LOGIN_MAX_FAILURES),
                (self._key_account(account), config.LOGIN_MAX_FAILURES_PER_ACCOUNT),
            ):
                q = self._failures.get(key)
                if not q:
                    continue
                self._prune(q, now)
                if len(q) >= limit:
                    return max(1, int(config.LOGIN_LOCK_SECONDS - (now - q[0])))
        return 0

    def record_failure(self, ip: str, account: str) -> None:
        now = time.monotonic()
        with self._lock:
            for key in (self._key_ip(ip, account), self._key_account(account)):
                q = self._failures[key]
                self._prune(q, now)
                q.append(now)
            if len(self._failures) > 50_000:  # chặn phình bộ nhớ
                for k in [k for k, q in self._failures.items() if not q or now - q[-1] > config.LOGIN_LOCK_SECONDS]:
                    self._failures.pop(k, None)

    def reset(self, ip: str, account: str) -> None:
        with self._lock:
            self._failures.pop(self._key_ip(ip, account), None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = LoginThrottle()

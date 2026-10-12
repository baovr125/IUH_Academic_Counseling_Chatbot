"""Supabase giả lập có trạng thái (in-memory) cho test.

Khác với MagicMock: bộ lọc `.eq()` thật sự lọc dữ liệu, nên test sẽ đỏ nếu mã truy vấn sai cột/giá trị.
Mỗi lời gọi được ghi vào ``calls`` để test kiểm tra truy vấn đã gửi.
"""
from types import SimpleNamespace
from typing import Any, Dict, List, Optional


class FakeAPIError(Exception):
    """Giống postgrest.APIError: có thuộc tính code/message."""

    def __init__(self, message: str, code: str = ""):
        super().__init__(message)
        self.code = code
        self.message = message


class FakeQuery:
    def __init__(self, db: "FakeSupabase", table: str):
        self.db, self.table = db, table
        self.op = "select"
        self.payload: Any = None
        self.filters: List[tuple] = []

    def select(self, columns: str = "*"):
        self.op = "select"
        self.columns = columns
        return self

    def insert(self, payload: Dict[str, Any]):
        self.op, self.payload = "insert", payload
        return self

    def update(self, payload: Dict[str, Any]):
        self.op, self.payload = "update", payload
        return self

    def eq(self, column: str, value: Any):
        self.filters.append((column, value))
        return self

    def execute(self):
        self.db.calls.append({"table": self.table, "op": self.op, "filters": list(self.filters), "payload": self.payload})
        if self.db.fail_all is not None:
            raise self.db.fail_all
        if self.op == "insert" and self.db.fail_insert is not None:
            raise self.db.fail_insert
        rows = self.db.tables.setdefault(self.table, [])
        if self.op == "insert":
            rows.append(dict(self.payload))
            return SimpleNamespace(data=[dict(self.payload)])
        matched = [r for r in rows if all(r.get(c) == v for c, v in self.filters)]
        if self.op == "update":
            for r in matched:
                r.update(self.payload)
            return SimpleNamespace(data=[dict(r) for r in matched])
        return SimpleNamespace(data=[dict(r) for r in matched])


class FakeSupabase:
    def __init__(self, users: Optional[List[Dict[str, Any]]] = None):
        self.tables: Dict[str, List[Dict[str, Any]]] = {"users": [dict(u) for u in (users or [])]}
        self.calls: List[Dict[str, Any]] = []
        self.fail_all: Optional[Exception] = None
        self.fail_insert: Optional[Exception] = None

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)

    @property
    def users(self) -> List[Dict[str, Any]]:
        return self.tables["users"]

    def user(self, **match) -> Optional[Dict[str, Any]]:
        return next((u for u in self.users if all(u.get(k) == v for k, v in match.items())), None)

"""Supabase giả chạy trong bộ nhớ, đủ trung thực để kiểm thử lớp dữ liệu của flashcard_service.

Mô phỏng các hành vi quan trọng của PostgREST/Postgres mà code thật phụ thuộc vào:
  - truy vấn không `range/limit` chỉ trả tối đa 1000 dòng (giới hạn mặc định của PostgREST);
  - `select(cols, count="exact")` trả tổng số dòng khớp bộ lọc (trước khi cắt);
  - ràng buộc UNIQUE (một phần) và khóa ngoại flashcards.deck_id / review_logs.card_id (lỗi 23505 / 23503);
  - cột chưa tồn tại (chưa chạy migration) -> lỗi "column ... does not exist";
  - tiêm lỗi theo (thao tác, bảng) để kiểm thử đường lỗi.
"""
from __future__ import annotations

import itertools
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

MAX_ROWS = 1000
_clock = itertools.count()
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _now_iso() -> str:
    # đơn điệu tăng để created_at luôn giữ đúng thứ tự chèn
    return (_BASE + timedelta(milliseconds=next(_clock))).isoformat()


class FakeResponse:
    def __init__(self, data: List[Dict[str, Any]], count: Optional[int] = None):
        self.data = data
        self.count = count


class FakeDBError(Exception):
    pass


DEFAULTS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "flashcard_decks": lambda: {
        "is_system": False, "status": "published", "category": None, "level": None, "slug": None,
        "origin_deck_id": None, "user_id": None, "icon_flag": "🌐", "description": "", "created_at": _now_iso(),
        "lang_confirmed": False, "is_default": False,
    },
    "flashcards": lambda: {
        "user_id": None, "created_at": _now_iso(), "last_review": None, "example_translation": None,
        "level": None, "source": None, "target_lang": None,
    },
    "review_logs": lambda: {"user_id": None},
    "vocab_generation_usage": lambda: {},
    "flashcard_game_sessions": lambda: {"created_at": _now_iso(), "reviewed_count": 0, "applied_review": False, "mistakes": 0, "hints": 0, "best_combo": 0, "duration_ms": 0},
}

# (bảng, các cột, điều kiện áp dụng) cho ràng buộc UNIQUE một phần.
UNIQUES: List[Tuple[str, Tuple[str, ...], Callable[[Dict[str, Any]], bool]]] = [
    ("flashcard_decks", ("user_id", "origin_deck_id"), lambda r: r.get("origin_deck_id") is not None),
    ("flashcard_decks", ("slug",), lambda r: bool(r.get("is_system"))),
    ("flashcard_decks", ("user_id", "lang_code"), lambda r: bool(r.get("is_default"))),
    ("vocab_generation_usage", ("user_id", "usage_date"), lambda r: True),
    ("flashcard_game_sessions", ("user_id", "client_request_id"), lambda r: True),
]


class FakeSupabase:
    def __init__(self) -> None:
        self.tables: Dict[str, List[Dict[str, Any]]] = {
            "flashcard_decks": [], "flashcards": [], "review_logs": [], "vocab_generation_usage": [], "flashcard_game_sessions": [], "users": [],
        }
        self.missing_columns: Dict[str, Set[str]] = {}
        self.missing_tables: Set[str] = set()
        self.fail: Dict[Tuple[str, str], Callable[[int], bool]] = {}
        self.calls: List[Tuple[str, str]] = []
        self._counts: Dict[Tuple[str, str], int] = {}

    # ---- API giống supabase-py
    def table(self, name: str) -> "FakeQuery":
        return FakeQuery(self, name)

    # ---- tiện ích cho test
    def seed(self, table: str, **row: Any) -> Dict[str, Any]:
        row = {"id": str(uuid.uuid4()), **DEFAULTS.get(table, lambda: {})(), **row}
        self.tables[table].append(row)
        return row

    def rows(self, table: str, **where: Any) -> List[Dict[str, Any]]:
        return [r for r in self.tables[table] if all(r.get(k) == v for k, v in where.items())]

    def fail_when(self, op: str, table: str, predicate: Callable[[int], bool] = lambda n: True) -> None:
        """Làm thao tác `op` trên `table` ném lỗi khi predicate(số lần gọi thứ n, bắt đầu từ 1) là True."""
        self.fail[(op, table)] = predicate

    def _record(self, op: str, table: str) -> None:
        self.calls.append((op, table))
        n = self._counts[(op, table)] = self._counts.get((op, table), 0) + 1
        pred = self.fail.get((op, table))
        if pred and pred(n):
            raise FakeDBError(f"injected failure on {op} {table}")


class FakeQuery:
    def __init__(self, db: FakeSupabase, table: str):
        self.db = db
        self.name = table
        self.op = "select"
        self.columns = "*"
        self.want_count = False
        self.filters: List[Callable[[Dict[str, Any]], bool]] = []
        self.orders: List[Tuple[str, bool]] = []
        self.limit_n: Optional[int] = None
        self.range_: Optional[Tuple[int, int]] = None
        self.payload: Any = None
        self.on_conflict: Optional[str] = None

    # ---- xây truy vấn
    def select(self, columns: str = "*", count: Optional[str] = None, head: bool = False):
        self.op, self.columns, self.want_count = "select", columns, count == "exact"
        return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self

    def upsert(self, payload, on_conflict: Optional[str] = None):
        self.op, self.payload, self.on_conflict = "upsert", payload, on_conflict
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def delete(self):
        self.op = "delete"
        return self

    def eq(self, col, val):
        self.filters.append(lambda r, c=col, v=val: r.get(c) == v)
        self._touch([col])
        return self

    def in_(self, col, values: Iterable[Any]):
        vals = set(values)
        self.filters.append(lambda r, c=col: r.get(c) in vals)
        self._touch([col])
        return self

    def gte(self, col, val):
        self.filters.append(lambda r, c=col, v=val: r.get(c) is not None and str(r.get(c)) >= str(v))
        self._touch([col])
        return self

    def neq(self, col, val):
        self.filters.append(lambda r, c=col, v=val: r.get(c) != v)
        self._touch([col])
        return self

    def lte(self, col, val):
        self.filters.append(lambda r, c=col, v=val: r.get(c) is not None and str(r.get(c)) <= str(v))
        self._touch([col])
        return self

    def gt(self, col, val):
        self.filters.append(lambda r, c=col, v=val: r.get(c) is not None and r.get(c) > v)
        self._touch([col])
        return self

    def or_(self, expression: str):
        """Hỗ trợ dạng 'col.ilike.%x%,col2.ilike.%x%' (đủ cho tìm kiếm thẻ)."""
        branches = []
        for part in expression.split(","):
            col, op, pattern = part.split(".", 2)
            assert op == "ilike", f"fake chỉ hỗ trợ ilike trong or_: {part}"
            branches.append((col, re.compile("^" + re.escape(pattern).replace("%", ".*") + "$", re.IGNORECASE)))
        self._touch([c for c, _ in branches])
        self.filters.append(lambda r, b=branches: any(rx.match(str(r.get(c) or "")) for c, rx in b))
        return self

    def ilike(self, col, pattern: str):
        regex = re.compile("^" + re.escape(pattern).replace("%", ".*").replace("_", ".") + "$", re.IGNORECASE)
        self.filters.append(lambda r, c=col: bool(regex.match(str(r.get(c) or ""))))
        self._touch([col])
        return self

    def order(self, col, desc: bool = False):
        self.orders.append((col, desc))
        return self

    def limit(self, n: int):
        self.limit_n = n
        return self

    def range(self, start: int, end: int):
        self.range_ = (start, end)
        return self

    # ---- thực thi
    def _touch(self, cols: Iterable[str]) -> None:
        missing = self.db.missing_columns.get(self.name, set())
        for col in cols:
            if col in missing:
                raise FakeDBError(f"column {self.name}.{col} does not exist")

    def _matching(self) -> List[Dict[str, Any]]:
        return [r for r in self.db.tables[self.name] if all(f(r) for f in self.filters)]

    def _check_unique(self, row: Dict[str, Any], ignore: Optional[Dict[str, Any]] = None) -> None:
        for table, cols, applies in UNIQUES:
            if table != self.name or not applies(row):
                continue
            for other in self.db.tables[self.name]:
                if other is ignore or not applies(other):
                    continue
                if all(other.get(c) == row.get(c) for c in cols):
                    raise FakeDBError(
                        f"duplicate key value violates unique constraint on ({', '.join(cols)}) (code 23505)"
                    )

    def _check_fk(self, row: Dict[str, Any]) -> None:
        if self.name == "flashcards" and row.get("deck_id") is not None:
            if not any(d["id"] == row["deck_id"] for d in self.db.tables["flashcard_decks"]):
                raise FakeDBError("violates foreign key constraint flashcards_deck_id_fkey (code 23503)")
        if self.name == "review_logs" and row.get("card_id") is not None:
            if not any(c["id"] == row["card_id"] for c in self.db.tables["flashcards"]):
                raise FakeDBError("violates foreign key constraint review_logs_card_id_fkey (code 23503)")

    def execute(self) -> FakeResponse:
        db = self.db
        if self.name in db.missing_tables:
            raise FakeDBError(f'relation "public.{self.name}" does not exist')
        db._record(self.op, self.name)

        if self.op == "insert" or self.op == "upsert":
            rows = self.payload if isinstance(self.payload, list) else [self.payload]
            # Kiểm tra cột trước khi ghi bất cứ dòng nào (PostgREST chèn cả lô trong một câu lệnh).
            for row in rows:
                self._touch(row.keys())
            staged: List[Dict[str, Any]] = []
            snapshot = [dict(r) for r in db.tables[self.name]]
            try:
                for row in rows:
                    new = {**DEFAULTS.get(self.name, lambda: {})(), "id": str(uuid.uuid4()), **row}
                    if self.op == "upsert" and self.on_conflict:
                        keys = [k.strip() for k in self.on_conflict.split(",")]
                        existing = next((r for r in db.tables[self.name] if all(r.get(k) == new.get(k) for k in keys)), None)
                        if existing:
                            existing.update(row)
                            staged.append(existing)
                            continue
                    self._check_unique(new)
                    self._check_fk(new)
                    db.tables[self.name].append(new)
                    staged.append(new)
            except FakeDBError:
                db.tables[self.name] = snapshot  # cả lô bị hoàn tác như một câu lệnh SQL
                raise
            return FakeResponse([dict(r) for r in staged])

        if self.op == "update":
            self._touch(self.payload.keys())
            changed = []
            for r in self._matching():
                candidate = {**r, **self.payload}
                self._check_unique(candidate, ignore=r)
                r.update(self.payload)
                changed.append(dict(r))
            return FakeResponse(changed)

        if self.op == "delete":
            doomed = self._matching()
            ids = {r["id"] for r in doomed}
            db.tables[self.name] = [r for r in db.tables[self.name] if r["id"] not in ids]
            if self.name == "flashcards":  # review_logs.card_id ... ON DELETE CASCADE
                db.tables["review_logs"] = [l for l in db.tables["review_logs"] if l.get("card_id") not in ids]
            if self.name == "flashcard_decks":  # ON DELETE CASCADE / SET NULL
                gone = {r["id"] for r in doomed}
                cards = {c["id"] for c in db.tables["flashcards"] if c.get("deck_id") in gone}
                db.tables["flashcards"] = [c for c in db.tables["flashcards"] if c.get("deck_id") not in gone]
                db.tables["review_logs"] = [l for l in db.tables["review_logs"] if l.get("card_id") not in cards]
                for d in db.tables["flashcard_decks"]:
                    if d.get("origin_deck_id") in gone:
                        d["origin_deck_id"] = None
            return FakeResponse([dict(r) for r in doomed])

        # select
        wanted = None if self.columns.strip() == "*" else [c.strip() for c in self.columns.split(",") if c.strip()]
        if wanted:
            self._touch(wanted)
        rows = self._matching()
        total = len(rows)
        for col, desc in reversed(self.orders):
            rows.sort(key=lambda r, c=col: (r.get(c) is None, r.get(c)), reverse=desc)
        if self.range_:
            rows = rows[self.range_[0]: self.range_[1] + 1]
        elif self.limit_n is not None:
            rows = rows[: self.limit_n]
        else:
            rows = rows[:MAX_ROWS]  # giới hạn mặc định của PostgREST
        if self.limit_n is not None and self.range_:
            rows = rows[: self.limit_n]
        data = [dict(r) if wanted is None else {c: r.get(c) for c in wanted} for r in rows]
        return FakeResponse(data, total if self.want_count else None)

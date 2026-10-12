"""Chỉ mục từ điển chuyên ngành dùng chung cho /text và /stream.

- Dựng một lần cho mỗi phiên bản từ điển (global_dict_ver), không json.loads/biên dịch regex trên từng request.
- `exact()`: tra khớp chính xác (có chuẩn hóa mạo từ và số nhiều/biến thể đuôi) cho từ/cụm ngắn.
- `scan()`: quét thuật ngữ trong câu dài, ưu tiên thuật ngữ dài nhất và không cho các thuật ngữ chồng lấn nhau
  (vd "neural network" thắng "network").
"""
from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from app.utils.logger import logger
from app.utils.text_normalizer import build_morphology_pattern

_ARTICLES = ("a ", "an ", "the ", "to ")
_EDGE_PUNCT = " \t\r\n.,;:!?\"'()[]{}"
_INDEX_TTL_SECONDS = 300


@lru_cache(maxsize=4096)
def _compiled(term: str) -> Optional[re.Pattern]:
    pattern = build_morphology_pattern(term)
    return re.compile(pattern, re.IGNORECASE) if pattern else None


def _normalize_phrase(text: str) -> str:
    clean = " ".join(text.strip(_EDGE_PUNCT).lower().split())
    for prefix in _ARTICLES:
        if clean.startswith(prefix):
            return clean[len(prefix):].strip()
    return clean


def _variants(phrase: str) -> List[str]:
    """Các dạng gốc có thể có của cụm (chỉ biến đổi từ cuối: số nhiều, quá khứ, V-ing)."""
    out = [phrase]
    head, _, last = phrase.rpartition(" ")
    prefix = f"{head} " if head else ""
    forms = []
    if last.endswith("ies") and len(last) > 4:
        forms.append(last[:-3] + "y")
    if last.endswith("es") and len(last) > 3:
        forms.append(last[:-2])
    if last.endswith("s") and len(last) > 3:
        forms.append(last[:-1])
    if last.endswith("ed") and len(last) > 4:
        forms += [last[:-2], last[:-1]]
    if last.endswith("ing") and len(last) > 5:
        forms += [last[:-3], last[:-3] + "e"]
    for f in forms:
        cand = prefix + f
        if cand not in out:
            out.append(cand)
    return out


@dataclass(frozen=True)
class TermEntry:
    domain: str
    word: str  # chữ thường
    translation: str

    @property
    def n_words(self) -> int:
        return len(self.word.split())


@dataclass(frozen=True)
class TermMatch:
    entry: TermEntry
    start: int
    end: int


@dataclass
class DomainIndex:
    entries: List[TermEntry] = field(default_factory=list)
    by_word: Dict[str, List[TermEntry]] = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)
    max_words: int = 0
    _by_length: List[TermEntry] = field(default_factory=list)

    @classmethod
    def build(cls, rows: Sequence[dict]) -> "DomainIndex":
        entries: List[TermEntry] = []
        seen = set()
        for row in rows:
            domain = str(row.get("domain") or "").strip()
            word = " ".join(str(row.get("word") or "").strip().lower().split())
            translation = str(row.get("translation") or "").strip()
            if not (domain and word and translation) or (domain, word) in seen:
                continue
            seen.add((domain, word))
            entries.append(TermEntry(domain, word, translation))
        by_word: Dict[str, List[TermEntry]] = {}
        for e in entries:
            by_word.setdefault(e.word, []).append(e)
        domains = sorted({e.domain for e in entries})
        index = cls(
            entries=entries,
            by_word=by_word,
            domains=domains,
            max_words=max((e.n_words for e in entries), default=0),
        )
        index._by_length = sorted(entries, key=lambda e: (-len(e.word), e.word, e.domain))
        return index

    def exact(self, text: str) -> List[TermEntry]:
        """Mọi mục có `word` khớp chính xác với cả cụm (sau chuẩn hóa)."""
        phrase = _normalize_phrase(text)
        if not phrase:
            return []
        for variant in _variants(phrase):
            hit = self.by_word.get(variant)
            if hit:
                return list(hit)
        return []

    def scan(self, text: str, domains: Optional[Sequence[str]] = None) -> List[TermMatch]:
        """Quét thuật ngữ trong `text`; thuật ngữ dài nhất thắng, các khớp không chồng lấn."""
        allowed = set(domains) if domains is not None else None
        lowered = text.lower()
        claimed: List[Tuple[int, int]] = []
        matches: List[TermMatch] = []
        for entry in self._by_length:
            if allowed is not None and entry.domain not in allowed:
                continue
            pattern = _compiled(entry.word)
            if pattern is None:
                continue
            for m in pattern.finditer(lowered):
                s, e = m.span()
                if any(s < ce and cs < e for cs, ce in claimed):
                    continue
                claimed.append((s, e))
                matches.append(TermMatch(entry, s, e))
        matches.sort(key=lambda m: m.start)
        return matches


_state: dict = {"version": None, "built_at": 0.0, "index": None}
_lock: Optional[asyncio.Lock] = None


async def get_index(force: bool = False) -> DomainIndex:
    """Trả chỉ mục từ điển, dựng lại khi `global_dict_ver` đổi hoặc quá hạn."""
    global _lock
    from app.services.cache_service import get_global_dict_version
    from app.services.domain_service import get_all_dictionaries

    if _lock is None:
        _lock = asyncio.Lock()
    version = await asyncio.to_thread(get_global_dict_version)
    fresh = (
        _state["index"] is not None
        and _state["version"] == version
        and time.monotonic() - _state["built_at"] < _INDEX_TTL_SECONDS
    )
    if fresh and not force:
        return _state["index"]
    async with _lock:
        if (
            not force
            and _state["index"] is not None
            and _state["version"] == version
            and time.monotonic() - _state["built_at"] < _INDEX_TTL_SECONDS
        ):
            return _state["index"]
        rows = await get_all_dictionaries()
        if not rows and _state["index"] is not None:
            # Nguồn dữ liệu lỗi tạm thời: giữ chỉ mục cũ thay vì xóa sạch từ điển.
            logger.warning("Dictionary fetch returned no rows; keeping the previous index.")
            _state["built_at"] = time.monotonic()
            return _state["index"]
        index = DomainIndex.build(rows or [])
        _state.update(version=version, built_at=time.monotonic(), index=index)
        logger.info(f"Domain index built: {len(index.entries)} terms, {len(index.domains)} domains")
        return index


def reset_index_cache() -> None:
    """Dùng cho test."""
    _state.update(version=None, built_at=0.0, index=None)

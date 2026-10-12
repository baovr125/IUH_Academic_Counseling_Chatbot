"""Nhận diện chuyên ngành (domain) cho chế độ dịch bằng LLM.

Gồm các phần thuần (không I/O) để dễ test:
- prompt dịch theo domain (thủ công) và prompt dịch + nhận diện trong một lời gọi (auto),
- parser stream cho giao thức `DOMAIN: <tên> | CONF: <0..1>` / `---` / bản dịch,
- tổng hợp bằng chứng lexical từ từ điển và quyết định cuối `decide_domain`.

Confidence do LLM tự khai bão hòa (đã đo: 0,95-1,0 cả khi sai) nên KHÔNG được dùng một mình:
quyết định cuối kết hợp với bằng chứng lexical (xem DOMAIN_DETECTION.md).
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from app.services.domain_index import TermEntry, TermMatch

UNKNOWN = "unknown"

LANG_NAMES = {
    "en": "English", "vi": "Vietnamese", "de": "German", "zh": "Simplified Chinese", "ja": "Japanese",
    "ko": "Korean", "fr": "French", "es": "Spanish", "ru": "Russian", "th": "Thai",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code)


# --------------------------------------------------------------------------- cấu hình
def _env_float(name: str, default: float, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        return min(hi, max(lo, float(os.getenv(name, default))))
    except (TypeError, ValueError):
        return default


def min_confidence() -> float:
    return _env_float("AUTO_DOMAIN_MIN_CONFIDENCE", 0.75)


# --------------------------------------------------------------------------- prompt
def _glossary_block(entries: Sequence[TermEntry], with_domain: bool) -> str:
    lines = []
    for e in entries:
        suffix = f"  [domain: {e.domain}]" if with_domain else ""
        lines.append(f"- {e.word} -> {e.translation}{suffix}")
    return "\n".join(lines)


def build_manual_system_prompt(domain: str, glossary: Sequence[TermEntry], source_lang: str, target_lang: str) -> str:
    parts = [
        f"You are an expert {lang_name(source_lang)} to {lang_name(target_lang)} translator specialising in the "
        f"'{domain}' domain.",
        "Translate in the register and terminology of that field.",
    ]
    if glossary:
        parts.append(
            "Use this glossary as the preferred terminology when the term is used in its domain sense:\n"
            + _glossary_block(glossary, with_domain=False)
        )
    parts.append(
        "Rules: adapt grammar, plural/singular and word order naturally; do not add explanations, notes or quotes; "
        "preserve all HTML tags exactly if present; output ONLY the translation."
    )
    return "\n\n".join(parts)


def build_auto_system_prompt(
    domains: Sequence[str], glossary: Sequence[TermEntry], source_lang: str, target_lang: str
) -> str:
    parts = [
        f"You are a professional {lang_name(source_lang)} to {lang_name(target_lang)} translator who also identifies "
        "the subject domain of the text.",
        "Candidate domains: " + json.dumps(list(domains), ensure_ascii=False) + ".",
        "Step 1 - domain: choose ONE candidate only when the text clearly belongs to it (specialised vocabulary or "
        f"subject matter). Answer `{UNKNOWN}` when the text is general or everyday, very short or ambiguous, spreads "
        "evenly over several domains, or is outside the list. A specialised term used in an unrelated everyday "
        "context (for example 'side effect' about cooking) does NOT make the text domain-specific.",
        "Step 2 - translation: when a domain is chosen, use that field's terminology; otherwise translate in natural "
        "general language.",
    ]
    if glossary:
        parts.append(
            "Glossary (use an entry only if the text belongs to that entry's domain and the term is used in that "
            "sense):\n" + _glossary_block(glossary, with_domain=True)
        )
    parts.append(
        "Output format, exactly: line 1 is `DOMAIN: <exact candidate name or " + UNKNOWN + "> | CONF: <number 0..1>`; "
        "line 2 is `---`; then ONLY the translation (preserve HTML tags exactly if present). No other text."
    )
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- parser stream
_HEADER_RE = re.compile(
    r"^[\s`*>#_-]*DOMAIN\s*[:=]\s*(?P<domain>.+?)\s*[|;,]\s*CONF(?:IDENCE)?\s*[:=]\s*(?P<conf>[^\s`*|]+)\s*[`*]*\s*$",
    re.IGNORECASE,
)
_HEADER_START_RE = re.compile(r"^[\s`*>#_-]*DOMAIN\s*[:=]", re.IGNORECASE)
_MAX_HEADER_CHARS = 400


@dataclass
class JointHeader:
    domain: str  # nguyên văn model trả về
    confidence: Optional[float]  # None nếu không hợp lệ


class JointStreamParser:
    """Tách stream của giao thức một-lời-gọi thành (header, các đoạn bản dịch).

    `feed()` trả về danh sách sự kiện: ("header", JointHeader) tối đa một lần, ("format_error", None) nếu model không
    tuân thủ định dạng (khi đó toàn bộ nội dung vẫn được trả về như bản dịch), và ("text", str).
    """

    def __init__(self) -> None:
        self._buf = ""
        self._state = "header"  # header | separator | body
        self.format_error = False

    @staticmethod
    def _parse_conf(raw: str) -> Optional[float]:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            return None
        return value

    def _fail(self) -> list:
        self._state = "body"
        self.format_error = True
        text, self._buf = self._buf, ""
        events: list = [("format_error", None)]
        if text:
            events.append(("text", text))
        return events

    def feed(self, chunk: str) -> list:
        self._buf += chunk
        events: list = []
        while True:
            if self._state == "body":
                if self._buf:
                    events.append(("text", self._buf))
                    self._buf = ""
                return events
            if self._state == "header":
                nl = self._buf.find("\n")
                if nl < 0:
                    # Chưa đủ một dòng: sớm kết luận sai định dạng nếu dòng đầu không phải header.
                    stripped = self._buf.lstrip("`*>#_- \t\r\n")
                    if len(stripped) >= 7 and not stripped.upper().startswith("DOMAIN"):
                        return events + self._fail()
                    if len(self._buf) > _MAX_HEADER_CHARS:
                        return events + self._fail()
                    return events
                line, rest = self._buf[:nl], self._buf[nl + 1:]
                if re.fullmatch(r"[\s`*>#_-]*", line):  # dòng trống / rào markdown mở đầu
                    self._buf = rest
                    continue
                m = _HEADER_RE.match(line)
                if not m:
                    return events + self._fail()
                events.append(("header", JointHeader(m.group("domain").strip().strip("`*\"'"), self._parse_conf(m.group("conf")))))
                self._buf = rest
                self._state = "separator"
                continue
            if self._state == "separator":
                # Model đôi khi lặp dòng `---`: nuốt mọi dòng chỉ gồm dấu gạch trước khi vào phần bản dịch.
                lstripped = self._buf.lstrip(" \t\r\n")
                if not lstripped:
                    return events
                if not lstripped.startswith("-"):
                    self._state = "body"
                    continue
                first_dash = self._buf.find("-")
                nl = self._buf.find("\n", first_dash)
                if nl < 0:
                    if len(lstripped) > 8:  # "-----" dài bất thường: coi như nội dung
                        self._state = "body"
                        continue
                    return events
                if re.fullmatch(r"-{3,}", self._buf[:nl].strip()):
                    self._buf = self._buf[nl + 1:]
                    continue
                self._state = "body"
                continue

    def finish(self) -> list:
        """Gọi khi stream kết thúc để xả phần còn lại."""
        events: list = []
        if self._state == "header" and self._buf:
            # Stream kết thúc mà chưa có xuống dòng: thử xem cả buffer có phải header đơn lẻ không.
            m = _HEADER_RE.match(self._buf)
            if m:
                events.append(("header", JointHeader(m.group("domain").strip().strip("`*\"'"), self._parse_conf(m.group("conf")))))
                self._buf = ""
            else:
                return self._fail()
        if self._state in ("separator", "body") and self._buf:
            text = self._buf
            self._buf = ""
            if self._state == "separator" and re.fullmatch(r"\s*-{3,}\s*", text):
                text = ""
            if text:
                events.append(("text", text))
        self._state = "body"
        return events


# --------------------------------------------------------------------------- bằng chứng lexical
@dataclass
class LexicalSummary:
    per_domain: Dict[str, List[TermMatch]] = field(default_factory=dict)

    @staticmethod
    def build(matches: Sequence[TermMatch]) -> "LexicalSummary":
        per: Dict[str, List[TermMatch]] = {}
        for m in matches:
            per.setdefault(m.entry.domain, []).append(m)
        return LexicalSummary(per)

    def score(self, domain: str) -> float:
        """Điểm bằng chứng: mỗi thuật ngữ khác nhau tính 1, thuật ngữ nhiều từ đặc hiệu hơn (tối đa 2)."""
        seen = set()
        total = 0.0
        for m in self.per_domain.get(domain, []):
            if m.entry.word in seen:
                continue
            seen.add(m.entry.word)
            total += min(2.0, 1.0 + 0.5 * (m.entry.n_words - 1))
        return total

    def ranking(self) -> List[tuple]:
        return sorted(((d, self.score(d)) for d in self.per_domain), key=lambda x: (-x[1], x[0]))

    @property
    def top_domain(self) -> Optional[str]:
        r = self.ranking()
        return r[0][0] if r else None

    @property
    def top_score(self) -> float:
        r = self.ranking()
        return r[0][1] if r else 0.0

    @property
    def second_score(self) -> float:
        r = self.ranking()
        return r[1][1] if len(r) > 1 else 0.0

    def terms(self, domain: Optional[str]) -> List[str]:
        if not domain:
            return []
        out: List[str] = []
        for m in self.per_domain.get(domain, []):
            if m.entry.word not in out:
                out.append(m.entry.word)
        return out


# --------------------------------------------------------------------------- quyết định cuối
@dataclass
class DomainDecision:
    status: str  # detected | unknown
    domain: Optional[str]
    confidence: float
    method: str  # llm | lexical_llm | none
    reason: Optional[str] = None


def match_domain_name(raw: str, valid_domains: Sequence[str]) -> Optional[str]:
    """Khớp tên domain model trả về với danh sách hợp lệ (không phân biệt hoa/thường, khoảng trắng)."""
    key = " ".join(str(raw).split()).casefold()
    for d in valid_domains:
        if " ".join(d.split()).casefold() == key:
            return d
    return None


def decide_domain(
    header: Optional[JointHeader],
    lexical: LexicalSummary,
    valid_domains: Sequence[str],
) -> DomainDecision:
    """Kết hợp lời khai của LLM với bằng chứng lexical.

    Quy tắc (xem DOMAIN_DETECTION.md, đã chỉnh trên bộ dev):
    - LLM không trả header hợp lệ / trả unknown / domain ngoài danh sách  -> unknown.
    - confidence thiếu hoặc không hợp lệ -> unknown (không tin).
    - confidence < ngưỡng -> unknown.
    - Từ điển cho domain KHÁC với bằng chứng mạnh hơn hẳn -> unknown (xung đột LLM/lexical).
    """
    if header is None:
        return DomainDecision("unknown", None, 0.0, "none", "format_error")
    if str(header.domain).strip().casefold() == UNKNOWN:
        return DomainDecision("unknown", None, header.confidence or 0.0, "llm", "llm_unknown")
    chosen = match_domain_name(header.domain, valid_domains)
    if chosen is None:
        return DomainDecision("unknown", None, 0.0, "llm", "llm_out_of_list")
    if header.confidence is None:
        return DomainDecision("unknown", None, 0.0, "llm", "invalid_confidence")
    conf = header.confidence
    if conf < min_confidence():
        return DomainDecision("unknown", None, conf, "llm", "low_confidence")
    own = lexical.score(chosen)
    top, top_score = lexical.top_domain, lexical.top_score
    if top and top != chosen and top_score >= own + 2.0:
        return DomainDecision("unknown", None, conf, "lexical_llm", "llm_lexical_conflict")
    method = "lexical_llm" if own > 0 else "llm"
    return DomainDecision("detected", chosen, conf, method)

"""Dịch theo chuyên ngành bằng LLM (domain thủ công và domain=auto), dùng chung cho /text và /stream.

Luồng (xem DOMAIN_DETECTION.md):
  1. Bóc HTML để quét từ điển. Từ/cụm ngắn khớp chính xác từ điển (EN->VI) thì trả bản dịch từ điển, không gọi LLM.
     Auto: một domain -> dùng luôn; nhiều domain -> `ambiguous` để UI cho người dùng chọn.
  2. Quét thuật ngữ từ điển (EN->VI) để tiêm glossary vào prompt.
  3. Một lời gọi LLM stream (Groq -> Gemini). Auto: dòng đầu là domain + confidence, rồi tới bản dịch.
  4. LLM hỏng hẳn: NLLB làm phao cứu sinh cuối, kèm cảnh báo FALLBACK_NLLB.

Sinh các sự kiện dict (cùng dạng với SSE của /stream):
  {"event": "domain", "domain": {...DomainDetails}}   - có thể phát 2 lần (sớm, rồi bản cuối có applied_terms)
  {"text": "..."}                                       - đoạn bản dịch
  {"warnings": [{code, severity, message, ...}]}        - cảnh báo có cấu trúc (gộp theo `code` ở client)
  {"error": "...", "code": "..."}                       - không dịch được bằng bất kỳ đường nào
  {"event": "reset"}                                    - xóa phần bản dịch đã stream (bản dịch hỏng, sắp thay bằng NLLB)
  {"_internal": "cache_hit"}                            - chỉ để /text biết là cache (không gửi ra client)
"""
from __future__ import annotations

import asyncio
import re
from typing import AsyncGenerator, List, Optional, Sequence

from app.schemas.translation import DomainCandidate, DomainDetails, TranslationWarning
from app.services import domain_llm
from app.services.cache_service import (
    get_cached_domain_result,
    get_domain_version,
    get_translation_text_hash,
    set_cached_domain_result,
)
from app.services.domain_detection import (
    JointStreamParser,
    LexicalSummary,
    DomainDecision,
    build_auto_system_prompt,
    build_manual_system_prompt,
    decide_domain,
)
from app.services.domain_index import TermEntry, get_index
from app.services.domain_service import _PREDEFINED_DOMAINS
from app.utils.logger import logger

LLM_TEMPERATURE = 0.2

# Câu hiển thị cho người dùng (xem MESSAGES_REVIEW.md). Chế độ auto chỉ báo bằng nhãn trong ô chọn lĩnh vực
# (event `domain`), không phát cảnh báo; lý do kỹ thuật (quota, timeout...) chỉ ghi log.
MSG_AMBIGUOUS = "Từ này có nghĩa ở nhiều lĩnh vực. Hãy chọn một lĩnh vực."
MSG_FALLBACK = "Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường."
MSG_INTERRUPTED = "Bản dịch bị ngắt giữa chừng, có thể chưa đầy đủ. Nhấn Ctrl+Enter để dịch lại."
MSG_UNAVAILABLE = "Không thể dịch lúc này. Vui lòng thử lại sau."


def _warning(code: str, severity: str, message: str, domain: Optional[str] = None,
             candidates: Optional[Sequence[DomainCandidate]] = None) -> dict:
    return TranslationWarning(
        code=code, severity=severity, message=message, domain=domain, candidates=list(candidates or [])
    ).model_dump()


def _domain_event(details: DomainDetails) -> dict:
    return {"event": "domain", "domain": details.model_dump()}


def _visible_text(text: str) -> str:
    from app.services.language_detection import _extract_visible_text

    return _extract_visible_text(text)


def _tokens(text: str) -> set:
    return set(re.findall(r"\w+", text.casefold()))


def is_untranslated(source: str, output: str, source_lang: str, target_lang: str) -> bool:
    """Bản dịch hỏng: rỗng, chỉ có dấu `---`, hoặc gần như sao chép nguyên văn nguồn.

    Đã gặp thật: gpt-oss-20b trả lại nguyên văn tiếng Anh (hoặc `---`) trong ~33% câu khi chọn `unknown`.
    Chỉ xét sao chép khi nguồn đủ dài (>= 4 từ) để không báo nhầm tên riêng, số, mã.
    """
    out = output.strip()
    if out in ("", "---"):
        return True
    if source_lang == target_lang:
        return False
    a, b = _tokens(source), _tokens(out)
    return len(source.split()) >= 4 and bool(a) and len(a & b) / len(a | b) >= 0.85


def _applied_terms(entries: Sequence[TermEntry], output: str) -> List[str]:
    low = output.casefold()
    applied = []
    for e in entries:
        options = [o.strip().casefold() for o in e.translation.split("/") if o.strip()]
        if any(o in low for o in options):
            applied.append(e.word)
    return applied


def _unique_entries(matches) -> List[TermEntry]:
    seen, out = set(), []
    for m in matches:
        key = (m.entry.domain, m.entry.word)
        if key not in seen:
            seen.add(key)
            out.append(m.entry)
    return out


def _cache_key(source_lang: str, target_lang: str, domain: str, version: int, text: str) -> str:
    model = f"{domain_llm.groq_domain_model()}|{domain_llm.gemini_domain_model()}"
    mode = "auto" if domain == "auto" else "manual"
    return (
        f"domain_v4_{source_lang}_{target_lang}_{mode}_{domain}_v{version}_"
        f"{get_translation_text_hash(model)[:8]}_{get_translation_text_hash(text)}"
    )


async def _nllb(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    from app.services.translation_service import run_nllb_only

    try:
        return await run_nllb_only(text, source_lang, target_lang)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"NLLB last-resort fallback failed: {exc}")
        return None


async def translate_with_domain(
    text: str, source_lang: str, target_lang: str, domain: str
) -> AsyncGenerator[dict, None]:
    is_auto = domain == "auto"
    glossary_ok = source_lang == "en" and target_lang == "vi"
    visible = _visible_text(text).strip()
    has_markup = visible != text.strip()

    if not visible:  # chỉ có thẻ/ảnh: không có gì để dịch
        yield {"event": "domain", "domain": DomainDetails(
            status="skipped" if is_auto else "selected", domain=None if is_auto else domain, method="none").model_dump()}
        yield {"text": text}
        return

    index = await get_index()
    valid_domains = index.domains or list(_PREDEFINED_DOMAINS)
    warnings: List[dict] = []

    # ---- cache (chỉ chứa kết quả LLM hoàn chỉnh)
    version = await asyncio.to_thread(get_domain_version, "auto" if is_auto else domain)
    key = _cache_key(source_lang, target_lang, domain, version, text)
    cached = await asyncio.to_thread(get_cached_domain_result, key)
    if cached and cached.get("text"):
        yield {"_internal": "cache_hit"}
        yield {"event": "domain", "domain": cached["domain"]}
        yield {"text": cached["text"]}
        if cached.get("warnings"):
            yield {"warnings": cached["warnings"]}
        return

    words = visible.split()

    # ---- 1. khớp chính xác từ điển cho từ/cụm ngắn (EN->VI), không phụ thuộc số ký tự
    if glossary_ok and not has_markup and 0 < len(words) <= index.max_words:
        hits = index.exact(visible)
        if hits and is_auto:
            domains_hit = list(dict.fromkeys(h.domain for h in hits))
            if len(domains_hit) == 1:
                hit = hits[0]
                yield _domain_event(DomainDetails(
                    status="detected", domain=hit.domain, confidence=1.0, method="exact",
                    matched_terms=[hit.word], applied_terms=[hit.word], translator="dictionary"))
                yield {"text": hit.translation}
                return
            candidates = [DomainCandidate(domain=h.domain, term=h.word, translation=h.translation) for h in hits]
            yield _domain_event(DomainDetails(
                status="ambiguous", method="exact", matched_terms=[hits[0].word],
                candidates=candidates, reason="multiple_domains", translator="dictionary"))
            yield {"warnings": [_warning("DOMAIN_AMBIGUOUS", "warning", MSG_AMBIGUOUS, candidates=candidates)]}
            return
        if hits:
            own = [h for h in hits if h.domain == domain]
            if own:
                hit = own[0]
                yield _domain_event(DomainDetails(
                    status="selected", domain=domain, confidence=1.0, method="manual",
                    matched_terms=[hit.word], applied_terms=[hit.word], translator="dictionary"))
                yield {"text": hit.translation}
                return

    # ---- 2. glossary từ từ điển
    matches = index.scan(visible) if glossary_ok else []
    lexical = LexicalSummary.build(matches)
    if is_auto:
        glossary = _unique_entries(matches)
    else:
        glossary = _unique_entries([m for m in matches if m.entry.domain == domain])

    # ---- 3. LLM
    if is_auto:
        system = build_auto_system_prompt(valid_domains, glossary, source_lang, target_lang)
        parser: Optional[JointStreamParser] = JointStreamParser()
    else:
        system = build_manual_system_prompt(domain, glossary, source_lang, target_lang)
        parser = None

    out_parts: List[str] = []
    provider: Optional[str] = None
    decision: Optional[DomainDecision] = None
    interrupted: Optional[str] = None
    unavailable: Optional[str] = None

    def manual_details(translator: str, applied: Optional[List[str]] = None) -> DomainDetails:
        return DomainDetails(
            status="selected", domain=domain, confidence=1.0, method="manual",
            matched_terms=[e.word for e in glossary], applied_terms=applied or [], translator=translator)

    def auto_details(dec: DomainDecision, translator: str, applied: Optional[List[str]] = None) -> DomainDetails:
        if dec.status == "detected":
            return DomainDetails(
                status="detected", domain=dec.domain, confidence=dec.confidence, method=dec.method,
                matched_terms=lexical.terms(dec.domain), applied_terms=applied or [], translator=translator)
        return DomainDetails(
            status="unknown", confidence=dec.confidence, method=dec.method, reason=dec.reason, translator=translator)

    def handle_parser_events(events) -> List[dict]:
        """Chuyển sự kiện của parser thành sự kiện đầu ra (cập nhật `decision`, `out_parts`)."""
        nonlocal decision
        emitted: List[dict] = []
        for ev, payload in events:
            if ev in ("header", "format_error"):
                # Lỗi định dạng chỉ làm domain = unknown (reason="format_error"); không phát cảnh báo.
                decision = decide_domain(payload if ev == "header" else None, lexical, valid_domains)
                emitted.append(_domain_event(auto_details(decision, f"llm:{provider}")))
            elif ev == "text":
                out_parts.append(payload)
                emitted.append({"text": payload})
        return emitted

    try:
        async for kind, value in domain_llm.stream_llm(system, text, LLM_TEMPERATURE):
            if kind == "provider":
                provider = value
                if not is_auto:
                    yield _domain_event(manual_details(f"llm:{provider}"))
            elif parser is None:
                out_parts.append(value)
                yield {"text": value}
            else:
                for emitted in handle_parser_events(parser.feed(value)):
                    yield emitted
        if parser is not None:
            for emitted in handle_parser_events(parser.finish()):
                yield emitted
        if not "".join(out_parts).strip():
            unavailable = "empty"
    except domain_llm.LLMUnavailable as exc:
        unavailable = exc.code
    except domain_llm.LLMInterrupted as exc:
        interrupted = exc.code

    output = "".join(out_parts)
    if interrupted and not output.strip():
        # Đứt ngay sau token đầu (mới chỉ có header, chưa có chữ nào): coi như LLM không dùng được.
        unavailable, interrupted = interrupted, None
    if unavailable is None and interrupted is None and is_untranslated(visible, output, source_lang, target_lang):
        unavailable = "bad_output"
        if out_parts:
            yield {"event": "reset"}  # client xóa phần đã stream (bản sao chép/rác)
        out_parts.clear()
        output = ""

    # ---- 4. LLM không dùng được: NLLB làm phao cứu sinh cuối
    if unavailable is not None and not output.strip():
        logger.warning("Domain translation fell back to NLLB", extra={"reason": unavailable, "mode": "auto" if is_auto else "manual"})
        fallback = await _nllb(text, source_lang, target_lang)
        if fallback is None:
            yield {"error": MSG_UNAVAILABLE, "code": "TRANSLATION_UNAVAILABLE"}
            return
        if is_auto:
            dec = DomainDecision("unknown", None, 0.0, "none", "llm_unavailable")
            yield _domain_event(auto_details(dec, "nllb"))
        else:
            yield _domain_event(manual_details("nllb"))
        yield {"text": fallback}
        yield {"warnings": [_warning("FALLBACK_NLLB", "warning", MSG_FALLBACK)]}
        return

    # ---- 5. hoàn tất: cảnh báo và domain cuối (có applied_terms)
    translator = f"llm:{provider}"
    if is_auto and decision is None:
        decision = DomainDecision("unknown", None, 0.0, "none", "format_error")
    final_domain = domain if not is_auto else (decision.domain if decision and decision.status == "detected" else None)
    applied = _applied_terms([e for e in glossary if final_domain and e.domain == final_domain], output)
    details = manual_details(translator, applied) if not is_auto else auto_details(decision, translator, applied)
    yield _domain_event(details)

    # Kết quả chọn/nhận diện lĩnh vực chỉ đi qua event `domain` (UI hiện nhãn trong ô chọn), không thành cảnh báo.
    if interrupted:
        logger.warning("Domain translation stream interrupted", extra={"reason": interrupted})
        warnings.append(_warning("TRANSLATION_INTERRUPTED", "warning", MSG_INTERRUPTED))

    if warnings:
        yield {"warnings": warnings}

    if interrupted is None and output.strip() and not (decision and decision.reason == "format_error"):
        await asyncio.to_thread(
            set_cached_domain_result, key,
            {"text": output, "domain": details.model_dump(), "warnings": warnings},
        )


async def collect_domain_translation(text: str, source_lang: str, target_lang: str, domain: str) -> dict:
    """Gom các sự kiện thành một kết quả cho /text."""
    out: List[str] = []
    details: Optional[dict] = None
    warnings: List[dict] = []
    cached = False
    error: Optional[dict] = None
    async for ev in translate_with_domain(text, source_lang, target_lang, domain):
        if ev.get("_internal") == "cache_hit":
            cached = True
        elif ev.get("event") == "reset":
            out.clear()
        elif ev.get("event") == "domain":
            details = ev["domain"]
        elif "text" in ev:
            out.append(ev["text"])
        elif "warnings" in ev:
            warnings.extend(ev["warnings"])
        elif "error" in ev:
            error = ev
    return {"text": "".join(out), "domain": details, "warnings": warnings, "cached": cached, "error": error}

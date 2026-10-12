"""Test đơn vị cho các phần thuần của Domain Detection: parser stream, quyết định domain, chỉ mục từ điển."""
import math

import pytest

from app.services.domain_detection import (
    JointHeader,
    JointStreamParser,
    LexicalSummary,
    decide_domain,
    build_auto_system_prompt,
    build_manual_system_prompt,
)
from app.services.domain_index import DomainIndex, TermEntry

IT = "Công nghệ Thông tin (IT)"
MED = "Y khoa / Sức khỏe"
ECO = "Kinh tế / Tài chính"
DOMAINS = [IT, MED, ECO]

ROWS = [
    {"domain": IT, "word": "memory leak", "translation": "rò rỉ bộ nhớ"},
    {"domain": IT, "word": "network", "translation": "mạng"},
    {"domain": IT, "word": "neural network", "translation": "mạng nơ-ron"},
    {"domain": IT, "word": "race condition", "translation": "điều kiện tranh chấp"},
    {"domain": MED, "word": "side effect", "translation": "tác dụng phụ"},
    {"domain": MED, "word": "drug interaction", "translation": "tương tác thuốc"},
    {"domain": ECO, "word": "yield curve", "translation": "đường cong lợi suất"},
    {"domain": ECO, "word": "stock", "translation": "cổ phiếu"},
    {"domain": MED, "word": "stock", "translation": "kho thuốc"},
    {"domain": IT, "word": "technical debt", "translation": "nợ kỹ thuật"},
]


def run_parser(chunks):
    parser = JointStreamParser()
    events = []
    for c in chunks:
        events += parser.feed(c)
    events += parser.finish()
    return events, parser


def texts(events):
    return "".join(p for e, p in events if e == "text")


# --------------------------------------------------------------------------- parser
class TestJointStreamParser:
    def test_header_then_body(self):
        events, parser = run_parser(["DOMAIN: Marketing | CONF: 0.97\n---\nXin ", "chào"])
        assert events[0] == ("header", JointHeader("Marketing", 0.97))
        assert texts(events) == "Xin chào"
        assert not parser.format_error

    def test_header_split_across_tiny_chunks(self):
        chunks = list("DOMAIN: unknown | CONF: 0.8\n---\nBản dịch")
        events, _ = run_parser(chunks)
        assert events[0] == ("header", JointHeader("unknown", 0.8))
        assert texts(events) == "Bản dịch"

    def test_missing_header_is_format_error_and_keeps_translation(self):
        events, parser = run_parser(["Đây là bản dịch không có header, rất dài hơn mười ký tự"])
        assert events[0][0] == "format_error"
        assert texts(events) == "Đây là bản dịch không có header, rất dài hơn mười ký tự"
        assert parser.format_error

    def test_missing_separator_still_yields_translation(self):
        events, _ = run_parser(["DOMAIN: Marketing | CONF: 0.9\nKhông có dấu phân cách"])
        assert events[0][0] == "header"
        assert texts(events) == "Không có dấu phân cách"

    def test_markdown_fence_before_header_is_skipped(self):
        events, _ = run_parser(["```\nDOMAIN: Luật / Pháp lý | CONF: 0.9\n---\n", "a"])
        assert events[0] == ("header", JointHeader("Luật / Pháp lý", 0.9))
        assert texts(events) == "a"

    def test_header_without_trailing_newline_at_end_of_stream(self):
        events, _ = run_parser(["DOMAIN: Marketing | CONF: 0.97"])
        assert events == [("header", JointHeader("Marketing", 0.97))]

    @pytest.mark.parametrize("raw", ["abc", "nan", "inf", "1.5", "-0.2", "1e9"])
    def test_abnormal_confidence_becomes_none(self, raw):
        events, _ = run_parser([f"DOMAIN: {IT} | CONF: {raw}\n---\nx"])
        assert events[0][0] == "header"
        assert events[0][1].confidence is None

    def test_repeated_separator_line_is_swallowed(self):
        events, _ = run_parser(["DOMAIN: Marketing | CONF: 0.8\n---\n--- \nPhần yêu thích"])
        assert texts(events) == "Phần yêu thích"

    def test_separator_only_translation_is_empty(self):
        events, _ = run_parser(["DOMAIN: unknown | CONF: 0.5\n---\n---"])
        assert texts(events) == ""

    def test_translation_starting_with_dashes_is_not_swallowed_as_separator(self):
        events, _ = run_parser(["DOMAIN: Marketing | CONF: 0.9\n---\n- gạch đầu dòng"])
        assert texts(events) == "- gạch đầu dòng"


# --------------------------------------------------------------------------- quyết định
class TestDecideDomain:
    def lex(self, *words):
        idx = DomainIndex.build(ROWS)
        return LexicalSummary.build(idx.scan(" ".join(words)))

    def test_accepts_confident_domain(self):
        d = decide_domain(JointHeader(IT, 0.97), self.lex("a memory leak appeared"), DOMAINS)
        assert (d.status, d.domain, d.method) == ("detected", IT, "lexical_llm")

    def test_accepts_domain_without_lexical_evidence(self):
        d = decide_domain(JointHeader(IT, 0.97), self.lex("nothing here"), DOMAINS)
        assert (d.status, d.domain, d.method) == ("detected", IT, "llm")

    def test_name_match_is_case_and_space_insensitive(self):
        d = decide_domain(JointHeader("  công nghệ  thông tin (it) ", 0.9), self.lex(), DOMAINS)
        assert d.domain == IT

    def test_unknown_from_llm(self):
        d = decide_domain(JointHeader("unknown", 0.9), self.lex(), DOMAINS)
        assert (d.status, d.reason) == ("unknown", "llm_unknown")

    def test_domain_outside_list_is_rejected(self):
        d = decide_domain(JointHeader("Thể thao", 0.99), self.lex(), DOMAINS)
        assert (d.status, d.reason) == ("unknown", "llm_out_of_list")

    def test_no_header_is_format_error(self):
        d = decide_domain(None, self.lex(), DOMAINS)
        assert (d.status, d.reason) == ("unknown", "format_error")

    def test_missing_or_invalid_confidence_is_not_trusted(self):
        d = decide_domain(JointHeader(IT, None), self.lex(), DOMAINS)
        assert (d.status, d.reason) == ("unknown", "invalid_confidence")

    def test_low_confidence_abstains(self, monkeypatch):
        monkeypatch.setenv("AUTO_DOMAIN_MIN_CONFIDENCE", "0.8")
        d = decide_domain(JointHeader(IT, 0.7), self.lex(), DOMAINS)
        assert (d.status, d.reason) == ("unknown", "low_confidence")

    def test_threshold_env_garbage_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("AUTO_DOMAIN_MIN_CONFIDENCE", "không phải số")
        assert decide_domain(JointHeader(IT, 0.74), self.lex(), DOMAINS).reason == "low_confidence"
        assert decide_domain(JointHeader(IT, 0.76), self.lex(), DOMAINS).status == "detected"

    def test_strong_conflicting_lexical_evidence_abstains(self):
        # LLM nói IT, nhưng văn bản chứa hai thuật ngữ Y khoa và không có thuật ngữ IT nào.
        lex = self.lex("the side effect of a drug interaction")
        d = decide_domain(JointHeader(IT, 0.95), lex, DOMAINS)
        assert (d.status, d.reason) == ("unknown", "llm_lexical_conflict")

    def test_single_conflicting_term_is_not_enough_to_override(self):
        lex = self.lex("the side effect was small")
        d = decide_domain(JointHeader(IT, 0.95), lex, DOMAINS)
        assert d.status == "detected"


# --------------------------------------------------------------------------- chỉ mục
class TestDomainIndex:
    def setup_method(self):
        self.index = DomainIndex.build(ROWS)

    def test_build_stats(self):
        assert self.index.domains == sorted(DOMAINS)
        assert self.index.max_words == 2

    def test_build_skips_incomplete_and_duplicate_rows(self):
        idx = DomainIndex.build(ROWS + [ROWS[0], {"domain": IT, "word": "", "translation": "x"}, {"domain": "", "word": "a", "translation": "b"}])
        assert len(idx.entries) == len(ROWS)

    @pytest.mark.parametrize("query", ["memory leak", "MEMORY LEAK", "the memory leak", "a memory leak!", "memory leaks"])
    def test_exact_normalisation(self, query):
        assert [e.word for e in self.index.exact(query)] == ["memory leak"]

    def test_exact_handles_inflection_of_last_word(self):
        assert self.index.exact("technical debts")[0].word == "technical debt"
        assert self.index.exact("side effects")[0].word == "side effect"

    def test_exact_returns_every_domain_for_shared_term(self):
        assert {e.domain for e in self.index.exact("stock")} == {ECO, MED}

    def test_exact_does_not_match_partial_phrase(self):
        assert self.index.exact("memory") == []
        assert self.index.exact("") == []

    def test_scan_prefers_longest_term_and_does_not_double_count(self):
        words = [m.entry.word for m in self.index.scan("We trained a neural network on the data")]
        assert words == ["neural network"]

    def test_scan_matches_plural_and_reports_spans(self):
        matches = self.index.scan("Memory leaks and race conditions")
        assert [m.entry.word for m in matches] == ["memory leak", "race condition"]
        assert matches[0].start == 0

    def test_scan_can_restrict_domains(self):
        text = "the side effect and the memory leak"
        assert [m.entry.word for m in self.index.scan(text, [MED])] == ["side effect"]

    def test_lexical_score_prefers_more_and_longer_terms(self):
        lex = LexicalSummary.build(self.index.scan("a memory leak caused a race condition near the stock"))
        assert lex.top_domain == IT
        assert lex.score(IT) > lex.score(ECO)
        assert lex.terms(IT) == ["memory leak", "race condition"]


# --------------------------------------------------------------------------- prompt
class TestPrompts:
    def test_auto_prompt_lists_domains_glossary_and_protocol(self):
        entries = [TermEntry(IT, "memory leak", "rò rỉ bộ nhớ")]
        prompt = build_auto_system_prompt(DOMAINS, entries, "en", "vi")
        assert IT in prompt and "- memory leak -> rò rỉ bộ nhớ  [domain: " + IT + "]" in prompt
        assert "DOMAIN:" in prompt and "CONF:" in prompt and "---" in prompt
        assert "English to Vietnamese" in prompt

    def test_manual_prompt_without_glossary_has_no_glossary_block(self):
        prompt = build_manual_system_prompt(IT, [], "en", "vi")
        assert "glossary" not in prompt.lower()
        assert IT in prompt

    def test_manual_prompt_uses_language_names(self):
        prompt = build_manual_system_prompt(IT, [], "de", "ja")
        assert "German to Japanese" in prompt

    def test_confidence_helper_rejects_non_finite(self):
        assert JointStreamParser._parse_conf("0.5") == 0.5
        assert JointStreamParser._parse_conf(str(math.nan)) is None

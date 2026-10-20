"""Pipeline sinh từ vựng cho 9 ngôn ngữ (LLM giả): lời nhắc đúng ngôn ngữ, lọc từ sai hệ chữ, mạo từ, phiên âm, hạn mức token."""
import pytest

from app.schemas.vocabulary import GenerateVocabRequest
from app.services import vocab_pipeline as vp
from app.services.vocab_languages import LANGS
from fixtures.fake_llm import FakeLLM

WORDS = {
    "en": ["sustainable", "pollution", "recycle", "renewable", "conserve", "habitat"],
    "de": ["der Hund", "die Katze", "das Haus", "gehen", "schnell", "Straße"],
    "fr": ["le chat", "la maison", "l'école", "manger", "rapide", "œuf"],
    "es": ["el libro", "la casa", "comer", "rápido", "niño", "año"],
    "ru": ["дом", "книга", "читать", "быстрый", "друг", "окно"],
    "zh": ["和平", "学习", "朋友", "图书馆", "快乐", "天气"],
    "ja": ["食べる", "図書館", "きれい", "コーヒー", "学生", "天気"],
    "ko": ["먹다", "도서관", "친구", "학생", "날씨", "행복"],
    "th": ["สวัสดี", "หนังสือ", "เพื่อน", "โรงเรียน", "อาหาร", "ขอบคุณ"],
}
READING = {"zh": "hé píng", "ja": "たべる · taberu", "ko": "meokda", "th": "sawatdi"}  # ngôn ngữ không dùng IPA


def req(lang, **overrides):
    base = dict(mode="topic", topic="Daily life", level="B1", count=5, lang_code=lang)
    base.update(overrides)
    return GenerateVocabRequest(**base)


def fake(lang, **kw):
    def mutate(item):
        if lang in READING:
            item["ipa"] = READING[lang]
        return item

    return FakeLLM(words=WORDS[lang], mutate=mutate, **kw)


@pytest.mark.parametrize("lang", sorted(WORDS))
class TestEveryLanguage:
    async def test_runs_the_three_stages_and_returns_the_language(self, lang):
        llm = fake(lang)
        out = await vp.generate_vocabulary(req(lang), llm=llm)
        assert llm.stages == ["select", "enrich", "verify"]
        assert out["lang_code"] == lang and out["returned"] == 5
        assert [i["term"] for i in out["items"]] == WORDS[lang][:5]
        assert all(i["verified"] and i["warnings"] == [] for i in out["items"])

    async def test_prompts_name_the_target_language_in_every_stage(self, lang):
        llm = fake(lang)
        await vp.generate_vocabulary(req(lang), llm=llm)
        name = LANGS[lang].name
        assert all(name in c["system"] for c in llm.calls)
        assert f"Choose 6 {name} vocabulary items" in llm.calls[0]["user"]
        assert f"every item MUST be a genuine {name} word" in llm.calls[0]["user"]
        assert f"Language: {name}." in llm.calls[1]["user"] and LANGS[lang].reading_instruction in llm.calls[1]["user"]
        assert f"genuine {name} word or expression" in llm.calls[2]["user"]
        assert "reject any term that is English, Vietnamese or in another language" in llm.calls[2]["user"]

    async def test_definitions_stay_vietnamese(self, lang):
        llm = fake(lang)
        await vp.generate_vocabulary(req(lang), llm=llm)
        assert "Vietnamese only" in llm.calls[1]["user"] and "definition_vi" in llm.calls[1]["user"]

    async def test_text_mode_and_no_content_message_use_the_language(self, lang):
        llm = FakeLLM(reason="no_content")
        with pytest.raises(vp.VocabError) as exc:
            await vp.generate_vocabulary(req(lang, mode="text", text="x" * 40, topic=None), llm=llm)
        assert exc.value.status == 422 and "tiếng" in exc.value.message
        assert LANGS[lang].vi_name.split(" ", 1)[1] in exc.value.message
        assert f"not {LANGS[lang].name}" in llm.calls[0]["user"]


class TestScriptFiltering:
    async def test_chinese_characters_never_reach_a_german_deck(self):
        llm = FakeLLM(words=["狗", "der Hund", "дом", "gehen", "Hund1", "die Katze", "schnell", "das Haus"],
                      mutate=lambda i: i)
        out = await vp.generate_vocabulary(req("de", count=5), llm=llm)
        terms = {i["term"] for i in out["items"]}
        assert {"der Hund", "gehen", "die Katze"} <= terms  # từ hợp lệ vẫn được giữ
        assert not ({"狗", "дом", "Hund1"} & terms)  # chữ Hán, Cyrillic và từ chứa chữ số bị loại ngay ở bước chọn từ

    async def test_latin_words_are_not_accepted_for_chinese_or_russian(self):
        llm = FakeLLM(words=["peace", "和平", "dom", "学习", "朋友", "天气", "快乐"], mutate=lambda i: {**i, "ipa": "hé píng"})
        out = await vp.generate_vocabulary(req("zh", count=5), llm=llm)
        assert {i["term"] for i in out["items"]} == {"和平", "学习", "朋友", "天气"}  # "peace", "dom" (chữ Latin) bị loại
        out_ru = await vp.generate_vocabulary(req("ru", count=5), llm=FakeLLM(words=["dom", "дом", "книга", "читать", "друг", "окно"]))
        assert "dom" not in {i["term"] for i in out_ru["items"]}


class TestArticleAwareDedupe:
    async def test_known_headword_excludes_the_same_noun_with_article(self):
        out = await vp.generate_vocabulary(req("de", count=5), llm=fake("de"), existing_terms=["Hund"])
        assert "der Hund" not in {i["term"] for i in out["items"]}
        assert any(d["term"] == "der Hund" and d["reason"] == "duplicate_or_known" for d in out["dropped"])

    async def test_same_noun_with_and_without_article_in_one_answer_is_kept_once(self):
        llm = FakeLLM(words=["der Hund", "Hund", "die Katze", "das Haus", "gehen", "schnell", "Straße"])
        out = await vp.generate_vocabulary(req("de", count=5), llm=llm)
        keys = [vp._term_key(LANGS["de"], i["term"]) for i in out["items"]]
        assert len(keys) == len(set(keys))

    async def test_noun_with_article_is_a_noun_not_a_phrase(self):
        llm = FakeLLM(words=["der Hund", "auf Wiedersehen"], mutate=lambda i: {**i, "pos": ""})
        cand = [vp.sanitize_candidate("der Hund", LANGS["de"]), vp.sanitize_candidate("auf Wiedersehen", LANGS["de"])]
        assert cand[0]["pos"] == "" and cand[1]["pos"] == "phrase"
        item, _ = vp.validate_enriched({"definition_vi": "con chó", "pos": ""}, cand[0], "B1", LANGS["de"])
        assert item["part_of_speech"] == "noun"
        assert llm.words == ["der Hund", "auf Wiedersehen"]


class TestReadingsAndExamples:
    async def test_pinyin_language_with_ipa_answer_gets_a_warning_not_a_crash(self):
        llm = FakeLLM(words=WORDS["zh"], mutate=lambda i: {**i, "ipa": "/ˈtɛst/"})
        out = await vp.generate_vocabulary(req("zh"), llm=llm)
        assert out["returned"] == 5 and all(i["ipa"] == "" and "ipa_invalid" in i["warnings"] for i in out["items"])

    async def test_example_must_contain_the_term_even_in_scripts_without_spaces(self):
        llm = FakeLLM(words=WORDS["ja"], mutate=lambda i: {**i, "ipa": "たべる · taberu", "example": "毎日りんごを食べます。"})
        out = await vp.generate_vocabulary(req("ja"), llm=llm)
        by_term = {i["term"]: i for i in out["items"]}
        assert "example_missing_term" not in by_term["食べる"]["warnings"]
        assert "example_missing_term" in by_term["図書館"]["warnings"]

    async def test_german_inflected_form_with_dropped_article_counts_as_containing_the_term(self):
        llm = FakeLLM(words=["der Hund", "gehen", "schnell", "das Haus", "die Katze"],
                      mutate=lambda i: {**i, "example": "Ich sehe zwei Hunde im Garten."})
        out = await vp.generate_vocabulary(req("de"), llm=llm)
        hund = next(i for i in out["items"] if i["term"] == "der Hund")
        assert "example_missing_term" not in hund["warnings"]


class TestPromptDetails:
    async def test_exam_purposes_do_not_leak_into_other_languages(self):
        llm = fake("de")
        await vp.generate_vocabulary(req("de", purpose="ielts"), llm=llm)
        select = llm.calls[0]["user"]
        assert "IELTS" not in select and "everyday communication" in select

    async def test_english_keeps_exam_purposes(self):
        llm = fake("en")
        await vp.generate_vocabulary(req("en", purpose="ielts"), llm=llm)
        assert "IELTS" in llm.calls[0]["user"]

    async def test_academic_purpose_names_the_language(self):
        llm = fake("fr")
        await vp.generate_vocabulary(req("fr", purpose="academic"), llm=llm)
        assert "academic texts in French" in llm.calls[0]["user"]

    async def test_non_latin_scripts_get_a_larger_token_budget(self):
        en, zh = fake("en"), fake("zh")
        await vp.generate_vocabulary(req("en", count=10), llm=en)
        await vp.generate_vocabulary(req("zh", count=10), llm=zh)
        for stage in range(3):
            assert zh.calls[stage]["max_tokens"] > en.calls[stage]["max_tokens"]

    async def test_exclusion_list_only_shows_words_valid_for_the_language(self):
        llm = fake("de")
        await vp.generate_vocabulary(req("de", exclude_terms=["Hund", "狗", "bad<tag>"]), llm=llm)
        shown = llm.calls[0]["user"].split("already-known words:")[1].split("\n")[0]
        assert "Hund" in shown and "狗" not in shown and "bad<tag>" not in shown

    @pytest.mark.parametrize("lang", ["de", "zh", "ru"])
    async def test_other_languages_ask_for_a_short_equivalent_not_an_explanation(self, lang):
        llm = fake(lang)
        await vp.generate_vocabulary(req(lang), llm=llm)
        assert "EQUIVALENT" in llm.calls[1]["user"] and "NOT a long explanation" in llm.calls[1]["user"]
        assert "never replace it with a longer explanation" in llm.calls[2]["user"]

    async def test_english_prompts_keep_their_original_definition_rule(self):
        llm = fake("en")
        await vp.generate_vocabulary(req("en"), llm=llm)
        assert "EQUIVALENT" not in llm.calls[1]["user"] and "concise, natural Vietnamese meaning" in llm.calls[1]["user"]
        assert "never replace it" not in llm.calls[2]["user"]

    async def test_default_language_is_english_and_unchanged(self):
        out = await vp.generate_vocabulary(GenerateVocabRequest(mode="topic", topic="Environment", count=5), llm=FakeLLM())
        assert out["lang_code"] == "en"

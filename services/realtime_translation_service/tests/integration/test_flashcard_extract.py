"""POST /translate/flashcard: trích xuất thẻ theo ngôn ngữ nguồn (nghĩa tiếng Việt, phiên âm theo quy ước từng ngôn ngữ)."""
from unittest.mock import AsyncMock, patch

import pytest

from app.services.flashcard_extract import LEARNABLE, PHONETIC_RULES, build_prompt, clean_lang, normalize_result

URL = "/api/v1/translate/flashcard"


class TestPromptBuilder:
    @pytest.mark.parametrize("lang", LEARNABLE)
    def test_each_learnable_language_has_a_phonetic_rule_and_asks_for_vietnamese(self, lang):
        system, user = build_prompt("word", "context", "", lang)
        assert PHONETIC_RULES[lang] in system and "Vietnamese" in system and "example_translation" in system
        assert "'word'" in user

    @pytest.mark.parametrize("lang,keyword", [("zh", "Pinyin"), ("ja", "romaji"), ("ko", "Romanization"), ("th", "RTGS"), ("de", "IPA")])
    def test_phonetic_convention_differs_per_language(self, lang, keyword):
        assert keyword in build_prompt("w", "c", "", lang)[0]

    def test_without_source_language_the_legacy_prompt_is_used(self):
        system, _ = build_prompt("w", "c", "", None)
        assert "example_translation" not in system and "meaning" in system

    @pytest.mark.parametrize("raw,expected", [("DE", "de"), ("en-US", "en"), ("vi", None), ("auto", None), ("", None), (None, None), ("xx", None)])
    def test_clean_lang_never_guesses(self, raw, expected):
        assert clean_lang(raw) == expected


class TestNormalizeResult:
    def test_fills_missing_keys_and_drops_unknown_ones(self):
        out = normalize_result({"phonetic": " /x/ ", "meaning": "nghĩa", "junk": 1, "example": 5}, "Haus")
        assert out == {"word": "Haus", "phonetic": "/x/", "part_of_speech": "", "meaning": "nghĩa", "example": "", "example_translation": ""}

    @pytest.mark.parametrize("raw", [None, [], "text", 3])
    def test_garbage_gives_an_empty_card_shell(self, raw):
        assert normalize_result(raw, "w")["meaning"] == "" and normalize_result(raw, "w")["word"] == "w"


class TestEndpoint:
    def post(self, client, **body):
        return client.post(URL, json={"word": "Guten Morgen", "context": "Guten Morgen, Anna!", **body})

    def test_source_language_is_forwarded_and_german_gets_dictionary_phonetic(self, client):
        with patch("app.routers.translation.extract_flashcard", new_callable=AsyncMock) as llm, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as dictionary:
            llm.return_value = {"word": "Guten Morgen", "phonetic": "", "meaning": "Chào buổi sáng"}
            dictionary.return_value = {"phonetic": "/ˈɡuːtn̩ ˈmɔʁɡn̩/"}
            res = self.post(client, source_lang="de", target_lang="vi")
        assert res.status_code == 200
        assert llm.await_args.kwargs["source_lang"] == "de"
        assert dictionary.await_args.kwargs["lang"] == "de"
        assert res.json()["data"]["meaning"] == "Chào buổi sáng" and res.json()["data"]["phonetic"].startswith("/ˈɡuː")

    @pytest.mark.parametrize("lang", ["zh", "ja", "ko", "fr", "es", "ru", "th"])
    def test_no_english_dictionary_lookup_for_other_languages(self, client, lang):
        with patch("app.routers.translation.extract_flashcard", new_callable=AsyncMock) as llm, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as dictionary:
            llm.return_value = {"word": "x", "phonetic": "", "meaning": "y"}
            res = self.post(client, source_lang=lang)
        assert res.status_code == 200 and dictionary.await_count == 0
        assert res.json()["data"]["phonetic"] == ""  # không bịa phiên âm bằng từ điển tiếng Anh

    def test_llm_phonetic_is_not_overwritten_by_the_dictionary(self, client):
        with patch("app.routers.translation.extract_flashcard", new_callable=AsyncMock) as llm, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as dictionary:
            llm.return_value = {"phonetic": "/llm/", "meaning": "m"}
            dictionary.return_value = {"phonetic": "/dict/"}
            assert self.post(client, source_lang="en").json()["data"]["phonetic"] == "/llm/"

    def test_legacy_request_without_language_still_works_as_english(self, client):
        with patch("app.routers.translation.extract_flashcard", new_callable=AsyncMock) as llm, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as dictionary:
            llm.return_value = {"meaning": "m"}
            dictionary.return_value = {"phonetic": "/p/"}
            res = self.post(client)
        assert res.status_code == 200 and llm.await_args.kwargs["source_lang"] is None
        assert dictionary.await_args.kwargs["lang"] == "en" and res.json()["data"]["phonetic"] == "/p/"

    def test_dictionary_failure_does_not_fail_the_request(self, client):
        with patch("app.routers.translation.extract_flashcard", new_callable=AsyncMock) as llm, \
             patch("app.routers.translation.get_word_audio", new_callable=AsyncMock) as dictionary:
            llm.return_value = {"meaning": "m"}
            dictionary.side_effect = RuntimeError("down")
            assert self.post(client, source_lang="en").status_code == 200

    @pytest.mark.parametrize("body", [{"source_lang": "auto"}, {"source_lang": "vi"}, {"source_lang": "xx"}, {"target_lang": "en"}])
    def test_unknown_auto_or_vietnamese_source_is_rejected(self, client, body):
        assert self.post(client, **body).status_code == 422


class TestExtractFlashcardFunction:
    @staticmethod
    def groq_returning(content):
        from unittest.mock import MagicMock
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[MagicMock(message=MagicMock(content=content))]))
        return client

    async def test_with_language_result_is_normalised(self):
        from app.services import llm_service
        client = self.groq_returning('{"phonetic": "zǎo shang hǎo", "meaning": "Chào buổi sáng", "extra": 1}')
        with patch.object(llm_service, "get_groq_client", return_value=client):
            out = await llm_service.extract_flashcard("早上好", "早上好!", "", "zh")
        assert out["meaning"] == "Chào buổi sáng" and out["word"] == "早上好" and out["example"] == "" and "extra" not in out
        assert "Pinyin" in client.chat.completions.create.await_args.kwargs["messages"][0]["content"]

    async def test_without_language_result_is_returned_as_is(self):
        from app.services import llm_service
        with patch.object(llm_service, "get_groq_client", return_value=self.groq_returning('{"meaning": "m", "extra": 1}')):
            assert await llm_service.extract_flashcard("w", "c") == {"meaning": "m", "extra": 1}

    async def test_total_failure_returns_empty_dict(self):
        from app.services import llm_service
        with patch.object(llm_service, "get_groq_client", return_value=None), patch.object(llm_service, "get_gemini_client", return_value=None):
            assert await llm_service.extract_flashcard("w", "c", "", "de") == {}

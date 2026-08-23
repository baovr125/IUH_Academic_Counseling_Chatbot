import hashlib
import pytest
from app.routers.translation import resolve_voice


def generate_audio_cas_key(text: str, voice: str) -> str:
    """
    Computes the Content-Addressable Storage (CAS) Hash for audio caching:
    hashlib.md5(f"{clean_text.lower()}_{voice}".encode('utf-8')).hexdigest()
    """
    clean_text = text.strip()
    return hashlib.md5(f"{clean_text.lower()}_{voice}".encode('utf-8')).hexdigest()


class TestContentAddressableStorageDeduplication:
    def test_identical_text_and_voice_generates_identical_hash(self):
        text = "Hello world"
        voice = "en-US-AriaNeural"
        hash1 = generate_audio_cas_key(text, voice)
        hash2 = generate_audio_cas_key(text, voice)
        assert hash1 == hash2
        assert len(hash1) == 32

    def test_case_insensitivity_and_whitespace_trimming(self):
        voice = "en-US-AriaNeural"
        hash_clean = generate_audio_cas_key("Artificial Intelligence", voice)
        hash_upper = generate_audio_cas_key("ARTIFICIAL INTELLIGENCE", voice)
        hash_padded = generate_audio_cas_key("  Artificial Intelligence  \n", voice)
        assert hash_clean == hash_upper
        assert hash_clean == hash_padded

    def test_different_voices_generate_distinct_hashes(self):
        text = "Guten Tag"
        hash_de = generate_audio_cas_key(text, "de-DE-KillianNeural")
        hash_en = generate_audio_cas_key(text, "en-US-AriaNeural")
        assert hash_de != hash_en

    def test_different_languages_generate_distinct_hashes(self):
        voice_vi = resolve_voice("vi")
        voice_en = resolve_voice("en")
        hash_vi = generate_audio_cas_key("Xin chào", voice_vi)
        hash_en = generate_audio_cas_key("Hello", voice_en)
        assert hash_vi != hash_en

    def test_object_name_path_structure(self):
        text = "Spaced Repetition"
        voice = "en-US-AriaNeural"
        cas_key = generate_audio_cas_key(text, voice)
        object_name = f"tts/{cas_key}.mp3"
        assert object_name.startswith("tts/")
        assert object_name.endswith(".mp3")
        assert len(object_name) == len("tts/") + 32 + len(".mp3")

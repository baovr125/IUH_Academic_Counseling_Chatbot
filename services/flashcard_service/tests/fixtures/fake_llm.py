"""LLM giả cho pipeline sinh từ vựng: nhận diện từng bước (SELECT/ENRICH/VERIFY) qua system prompt."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from app.services.llm_client import LLMBadOutput, LLMResult, LLMUnavailable

DEFAULT_WORDS = [
    "sustainable", "pollution", "recycle", "renewable", "conserve", "habitat", "ecosystem", "landfill",
    "emission", "biodiversity", "drought", "erosion", "fossil fuel", "wildlife", "deforestation",
    "contaminate", "ozone", "organic", "compost", "carbon footprint",
]


def stage_of(system: str) -> str:
    if "curriculum designer" in system:
        return "select"
    if "lexicographer" in system:
        return "enrich"
    if "strict reviewer" in system:
        return "verify"
    raise AssertionError(f"system prompt không nhận diện được: {system[:60]}")


class FakeLLM:
    """
    words:        danh sách từ ở bước SELECT.
    reject/fix:   {term: ...} cho bước VERIFY ("reject" -> bị loại, "fix" -> dict các trường sửa).
    fail:         {stage: Exception} làm bước đó ném lỗi (ví dụ LLMUnavailable).
    reason:       trả {"words": [], "reason": ...} ở bước SELECT.
    mutate:       hàm sửa item ở bước ENRICH để dựng dữ liệu lỗi (nhận dict item, trả dict item hoặc None để bỏ).
    """

    def __init__(
        self,
        words: Optional[List[str]] = None,
        reject: Optional[Dict[str, str]] = None,
        fix: Optional[Dict[str, Dict[str, str]]] = None,
        fail: Optional[Dict[str, Exception]] = None,
        reason: Optional[str] = None,
        mutate: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
        provider: str = "fake:model",
    ):
        self.words = list(words) if words is not None else list(DEFAULT_WORDS)
        self.reject = reject or {}
        self.fix = fix or {}
        self.fail = fail or {}
        self.reason = reason
        self.mutate = mutate
        self.provider = provider
        self.calls: List[Dict[str, Any]] = []

    @property
    def stages(self) -> List[str]:
        return [c["stage"] for c in self.calls]

    async def __call__(self, system: str, user: str, **kwargs: Any) -> LLMResult:
        stage = stage_of(system)
        self.calls.append({"stage": stage, "system": system, "user": user, **kwargs})
        if stage in self.fail:
            raise self.fail[stage]

        if stage == "select":
            if self.reason:
                return LLMResult({"words": [], "reason": self.reason}, self.provider, 50, 10)
            n = int(user.split("Choose ")[1].split(" ")[0]) if user.startswith("Choose ") else int(user.split("up to ")[1].split(" ")[0])
            excluded = user.split("already-known words:")[1].split("\n")[0] if "already-known words:" in user else ""
            pool = [w for w in self.words if w.lower() not in excluded.lower()]
            return LLMResult({"words": [{"term": w, "pos": "noun"} for w in pool[:n]]}, self.provider, 100, 60)

        if stage == "enrich":
            entries = json.loads(user.split("Entries (JSON): ")[1].split("\nFor each")[0])
            items: List[Optional[Dict[str, Any]]] = []
            for e in entries:
                term = e["term"]
                item = {
                    "term": term, "pos": e.get("pos") or "noun", "ipa": "/ˈtɛst/",
                    "definition_vi": f"nghĩa của {term}", "example": f"This {term} is a clear example.",
                    "example_vi": f"Đây là ví dụ về {term}.",
                }
                items.append(self.mutate(item) if self.mutate else item)
            return LLMResult({"items": [i for i in items if i is not None]}, self.provider, 200, 300)

        cards = json.loads(user.split("Cards (JSON): ")[1].split("\nOutput:")[0])
        verdicts = []
        for c in cards:
            t = c["term"]
            if t in self.reject:
                verdicts.append({"term": t, "verdict": "reject", "issues": [self.reject[t]]})
            elif t in self.fix:
                verdicts.append({"term": t, "verdict": "fix", "issues": ["fixed"], "fixed": self.fix[t]})
            else:
                verdicts.append({"term": t, "verdict": "ok", "issues": []})
        return LLMResult({"verdicts": verdicts}, self.provider, 100, 80)


__all__ = ["FakeLLM", "DEFAULT_WORDS", "LLMBadOutput", "LLMUnavailable", "stage_of"]

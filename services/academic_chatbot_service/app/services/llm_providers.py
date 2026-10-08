import os
import json
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List
from google.genai import types

from app.utils.logger import logger
from app.services.rag_service import get_gemini, GEMINI_MODELS

class BaseLLMProvider(ABC):
    def __init__(self):
        self.last_used_model = "Unknown"

    @abstractmethod
    async def generate_stream(self, system_instruction: str, history_dicts: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        pass
        
    @abstractmethod
    async def generate_text(self, prompt: str, system_instruction: str = "", temperature: float = 0.0, max_tokens: int = 2048) -> str:
        pass

class GeminiProvider(BaseLLMProvider):
    async def generate_stream(self, system_instruction: str, history_dicts: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        gemini_client = get_gemini()
        if not gemini_client:
            yield {"text": "⚠️ Lỗi AI: Gemini client chưa khởi tạo"}
            return

        chat_history = []
        for msg in history_dicts[:-1]:
            chat_history.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["content"])]))
        last_msg = history_dicts[-1]["content"] if history_dicts else ""

        stream_iter = None
        first_chunk = None
        last_err = None

        for model_name in GEMINI_MODELS:
            try:
                cfg_kwargs = {
                    "system_instruction": system_instruction,
                    "temperature": 0.2,
                }
                def _start_stream(m_name=model_name, c_kwargs=cfg_kwargs):
                    chat_session = gemini_client.chats.create(
                        model=m_name,
                        config=types.GenerateContentConfig(**c_kwargs),
                        history=chat_history
                    )
                    st = chat_session.send_message_stream(last_msg)
                    it = iter(st)
                    fc = next(it, None)
                    return it, fc

                stream_iter, first_chunk = await asyncio.to_thread(_start_stream)
                self.last_used_model = model_name
                break
            except Exception as e:
                logger.warning(f"Error streaming content with model {model_name}: {e}")
                last_err = e
                continue

        if not stream_iter:
            err_str = str(last_err) if last_err else "All Gemini models failed."
            yield {"text": f"⚠️ Lỗi AI: {err_str}"}
            return

        if first_chunk and first_chunk.text:
            yield {"text": first_chunk.text}

        while True:
            chunk = await asyncio.to_thread(lambda: next(stream_iter, None))
            if chunk is None:
                break
            
            chunk_data = {"text": chunk.text if chunk.text else ""}
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                chunk_data["prompt_tokens"] = getattr(chunk.usage_metadata, 'prompt_token_count', 0)
                chunk_data["completion_tokens"] = getattr(chunk.usage_metadata, 'candidates_token_count', 0)
            
            if chunk_data["text"] or "prompt_tokens" in chunk_data:
                yield chunk_data
    async def generate_text(self, prompt: str, system_instruction: str = "", temperature: float = 0.0, max_tokens: int = 2048) -> str:
        gemini_client = get_gemini()
        if not gemini_client:
            return prompt
        
        for model_name in GEMINI_MODELS:
            try:
                cfg_kwargs = {"temperature": temperature}
                if system_instruction:
                    cfg_kwargs["system_instruction"] = system_instruction
                
                def _generate():
                    return gemini_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(**cfg_kwargs)
                    )
                response = await asyncio.to_thread(_generate)
                self.last_used_model = model_name
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini generate_text failed for model {model_name}: {e}")
                continue
        return prompt


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, base_url: str, api_key: str, model_name: str, fallback_provider: BaseLLMProvider = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_provider = fallback_provider
        self.last_used_model = model_name

    async def generate_stream(self, system_instruction: str, history_dicts: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        messages = [{"role": "system", "content": system_instruction}]
        for msg in history_dicts:
            role = "assistant" if msg["role"] == "model" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            "top_p": 0.8,
            "chat_template_kwargs": {"enable_thinking": False}
        }

        fallback_triggered = False
        buffer_str = ""
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            if not data_str:
                                continue
                            try:
                                data = json.loads(data_str)
                                chunk_data = {"text": ""}
                                
                                if "usage" in data and data["usage"]:
                                    chunk_data["prompt_tokens"] = data["usage"].get("prompt_tokens", 0)
                                    chunk_data["completion_tokens"] = data["usage"].get("completion_tokens", 0)
                                    
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        buffer_str += content
                                        
                                        if len(buffer_str) > 0:
                                            chunk_data["text"] = buffer_str
                                            buffer_str = ""
                                            yield chunk_data
                                            continue
                                            
                                if "prompt_tokens" in chunk_data and "text" not in chunk_data:
                                    yield chunk_data
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE JSON: {data_str}")
                                
                    if buffer_str:
                        yield {"text": buffer_str}
        except Exception as e:
            logger.warning(f"Local LLM stream failed: {e}. Falling back to Gemini...")
            fallback_triggered = True
            
        if fallback_triggered and self.fallback_provider:
            async for chunk in self.fallback_provider.generate_stream(system_instruction, history_dicts):
                self.last_used_model = getattr(self.fallback_provider, "last_used_model", "Gemini-Fallback")
                yield chunk
        elif fallback_triggered:
            yield {"text": f"⚠️ Lỗi AI Local và không có Fallback: {str(e)}"}

    async def generate_text(self, prompt: str, system_instruction: str = "", temperature: float = 0.0, max_tokens: int = 2048) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": temperature if temperature > 0 else 0.2,
            "top_p": 0.8,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False}
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    text = data["choices"][0]["message"]["content"].strip()
                    import re
                    text = re.sub(r'<think[\s\S]*?</think>\n*', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'<thinking[\s\S]*?</thinking>\n*', '', text, flags=re.IGNORECASE)
                    return text.strip()
        except Exception as e:
            logger.warning(f"Local LLM generate_text failed: {e}. Falling back to Gemini...")
            if self.fallback_provider:
                res = await self.fallback_provider.generate_text(prompt, system_instruction, temperature)
                self.last_used_model = getattr(self.fallback_provider, "last_used_model", "Gemini-Fallback")
                return res
        
        return prompt

def get_llm_provider() -> BaseLLMProvider:
    provider = os.getenv("LLM_PROVIDER", "openai").lower() # Default to openai as requested
    if provider == "openai":
        return OpenAICompatibleProvider(
            base_url=os.getenv("OPENAI_BASE_URL", "http://host.docker.internal:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            model_name=os.getenv("OPENAI_MODEL_NAME", "qwen2.5:7b"),
            fallback_provider=GeminiProvider()
        )
    return GeminiProvider()

def get_rewriter_provider() -> BaseLLMProvider:
    provider = os.getenv("REWRITER_PROVIDER", "openai").lower()
    if provider == "openai":
        return OpenAICompatibleProvider(
            base_url=os.getenv("OPENAI_BASE_URL", "http://host.docker.internal:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            model_name=os.getenv("OLLAMA_REWRITER_MODEL", "qwen2.5:7b"),
            fallback_provider=GeminiProvider()
        )
    return GeminiProvider()

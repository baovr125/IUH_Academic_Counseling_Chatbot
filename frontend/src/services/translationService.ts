import type { ApiResult, TranslateRequest, TranslateResponse, TranslationHistoryItem } from "../types";
import { MOCK_TRANSLATION_HISTORY, mockTranslate } from "../mock/mockData";
import { generateId } from "./utils";
import { getToken } from "./authService";

let historyStore: TranslationHistoryItem[] = [...MOCK_TRANSLATION_HISTORY];

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "http://localhost:8000").replace(/\/+$/, "");
  if (!base) return endpoint;
  return `${base}${endpoint}`;
};

export async function translateText(req: TranslateRequest): Promise<ApiResult<TranslateResponse>> {
  if (!req.sourceText.trim()) {
    return { ok: false, error: { message: "Vui lòng nhập văn bản cần dịch." } };
  }

  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/text"), {
      method: "POST",
      headers,
      body: JSON.stringify({
        text: req.sourceText,
        source_lang: req.sourceLang || "en",
        target_lang: req.targetLang || "vi"
      }),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.ok && data.data?.translated_text) {
        return {
          ok: true,
          data: {
            translatedText: data.data.translated_text,
            detectedSourceLang: req.sourceLang
          }
        };
      }
    }
  } catch (e) {
    // Fallback to local mock if gateway not running locally
  }

  const translatedText = mockTranslate(req.sourceText, req.targetLang);
  return { ok: true, data: { translatedText, detectedSourceLang: req.sourceLang } };
}

export async function streamTranslation(
  req: TranslateRequest,
  onChunk: (text: string) => void,
  onError: (error: string) => void,
  onComplete: () => void,
  signal?: AbortSignal
): Promise<void> {
  if (!req.sourceText.trim()) {
    onError("Vui lòng nhập văn bản cần dịch.");
    return;
  }

  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/stream"), {
      method: "POST",
      headers,
      body: JSON.stringify({
        text: req.sourceText,
        source_lang: req.sourceLang || "en",
        target_lang: req.targetLang || "vi",
        domain: req.domain || ""
      }),
      signal,
    });

    if (!res.ok || !res.body) {
      if (res.status === 429) {
        throw new Error("Hệ thống đang bận, vui lòng thử lại sau giây lát (429).");
      }
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim();
          if (dataStr) {
            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                onChunk(data.text);
              } else if (data.error) {
                onError(data.error);
              }
            } catch (err) {
              console.error("Failed to parse SSE data:", err);
            }
          }
        }
      }
    }
    onComplete();
  } catch (error: any) {
    if (error?.name === "AbortError") {
      // Ignored: request was cancelled intentionally by new user keystroke
      return;
    }
    console.error("Stream translation error:", error);
    onError(error?.message || "Không thể kết nối đến dịch vụ dịch thuật.");
  }
}

export async function extractFlashcard(
  word: string,
  context: string,
  domain: string = ""
): Promise<ApiResult<any>> {
  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/flashcard"), {
      method: "POST",
      headers,
      body: JSON.stringify({ word, context, domain }),
    });

    if (res.ok) {
      const data = await res.json();
      return { ok: true, data: data.data };
    }
    return { ok: false, error: { message: "Failed to extract flashcard" } };
  } catch (error) {
    return { ok: false, error: { message: "Network error" } };
  }
}

export async function saveTranslation(item: {
  sourceLang: TranslateRequest["sourceLang"];
  targetLang: TranslateRequest["targetLang"];
  sourceText: string;
  translatedText: string;
}): Promise<ApiResult<TranslationHistoryItem>> {
  const record: TranslationHistoryItem = {
    id: generateId("t"),
    sourceLang: item.sourceLang,
    targetLang: item.targetLang,
    title: item.sourceText.slice(0, 48),
    preview: item.sourceText.slice(0, 120),
    sourceText: item.sourceText,
    translatedText: item.translatedText,
    createdAt: "Just now",
  };
  historyStore = [record, ...historyStore];
  return { ok: true, data: record };
}

export async function fetchTranslationHistory(): Promise<ApiResult<TranslationHistoryItem[]>> {
  return { ok: true, data: historyStore };
}

export async function deleteTranslationHistoryItem(id: string): Promise<ApiResult<null>> {
  historyStore = historyStore.filter((h) => h.id !== id);
  return { ok: true, data: null };
}

export async function clearTranslationHistory(): Promise<ApiResult<null>> {
  historyStore = [];
  return { ok: true, data: null };
}

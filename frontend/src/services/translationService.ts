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

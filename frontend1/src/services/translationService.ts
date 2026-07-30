import type { ApiResult, TranslateRequest, TranslateResponse, TranslationHistoryItem } from "../types";
import { MOCK_TRANSLATION_HISTORY, mockTranslate } from "../mock/mockData";
import { delay, generateId } from "./utils";

let historyStore: TranslationHistoryItem[] = [...MOCK_TRANSLATION_HISTORY];

export async function translateText(req: TranslateRequest): Promise<ApiResult<TranslateResponse>> {
  await delay(1500); // matches the ~1.5s delay requested for the demo

  if (!req.sourceText.trim()) {
    return { ok: false, error: { message: "Vui lòng nhập văn bản cần dịch." } };
  }

  const translatedText = mockTranslate(req.sourceText, req.targetLang as "de" | "en" | "vi");
  return { ok: true, data: { translatedText, detectedSourceLang: req.sourceLang } };
}

export async function saveTranslation(item: {
  sourceLang: TranslateRequest["sourceLang"];
  targetLang: TranslateRequest["targetLang"];
  sourceText: string;
  translatedText: string;
}): Promise<ApiResult<TranslationHistoryItem>> {
  await delay(500);
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
  await delay(600);
  return { ok: true, data: historyStore };
}

export async function deleteTranslationHistoryItem(id: string): Promise<ApiResult<null>> {
  await delay(400);
  historyStore = historyStore.filter((h) => h.id !== id);
  return { ok: true, data: null };
}

export async function clearTranslationHistory(): Promise<ApiResult<null>> {
  await delay(400);
  historyStore = [];
  return { ok: true, data: null };
}

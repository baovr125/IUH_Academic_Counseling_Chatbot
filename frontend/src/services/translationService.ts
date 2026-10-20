import type {
  ApiResult, TranslateRequest, TranslateResponse, TranslationHistoryItem, LanguageDetectionDetails,
  DomainDetails, TranslationWarning,
} from "../types";
import { MOCK_TRANSLATION_HISTORY } from "../mock/mockData";
import { generateId } from "./utils";
import { getToken } from "./authService";

let historyStore: TranslationHistoryItem[] = [...MOCK_TRANSLATION_HISTORY];

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "").replace(/\/+$/, "");
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
        target_lang: req.targetLang || "vi",
        domain: req.domain || "",
        ...(req.sourceLang === "auto" && req.sourceLangHint ? { source_lang_hint: req.sourceLangHint } : {}),
      }),
    });

    // Lỗi thật của backend (gồm các mã LANG_* khi chưa xác định được ngôn ngữ nguồn) phải hiện ra,
    // không được thay bằng bản dịch giả.
    let body: any = null;
    try {
      body = await res.json();
    } catch {
      body = null;
    }

    if (res.ok && body?.ok && body.data?.translated_text) {
      return {
        ok: true,
        data: {
          translatedText: body.data.translated_text,
          detectedSourceLang: body.data.resolved_source_lang || req.sourceLang,
          detection: body.data.detection,
          domainDetails: body.data.domain ?? undefined,
          warnings: body.data.warnings ?? [],
        }
      };
    }

    const message =
      body?.error?.message ||
      (typeof body?.detail === "string" ? body.detail : "") ||
      `Dịch vụ dịch thuật trả về lỗi (HTTP ${res.status}).`;
    return {
      ok: false,
      error: { message, code: body?.error?.code, detection: body?.error?.detection },
    };
  } catch (e) {
    return { ok: false, error: { message: "Không thể kết nối đến dịch vụ dịch thuật." } };
  }
}

export async function streamTranslation(
  req: TranslateRequest,
  onChunk: (text: string) => void,
  /** `code` có giá trị (LANG_UNCERTAIN, LANG_UNSUPPORTED, LANG_UNKNOWN, INVALID_INPUT) khi dừng vì ngôn ngữ nguồn. */
  onError: (error: string, code?: string) => void,
  onWarning: (warning: string) => void,
  onComplete: () => void,
  signal?: AbortSignal,
  onDetectedLanguage?: (lang: string, details?: LanguageDetectionDetails) => void,
  onDetectionDetails?: (details: LanguageDetectionDetails) => void,
  /** Kết quả chọn/nhận diện chuyên ngành; có thể được gọi 2 lần (sớm, rồi bản cuối kèm applied_terms). */
  onDomain?: (details: DomainDetails) => void,
  /** Cảnh báo có cấu trúc (chế độ chuyên ngành). */
  onWarnings?: (warnings: TranslationWarning[]) => void,
  /** Backend yêu cầu xóa phần bản dịch đã stream (bản dịch của LLM bị hỏng, sắp thay bằng bản khác). */
  onReset?: () => void
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
        domain: req.domain || "",
        ...(req.sourceLang === "auto" && req.sourceLangHint ? { source_lang_hint: req.sourceLangHint } : {}),
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
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || "";
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('data: ')) {
          const dataStr = trimmedLine.replace('data: ', '').trim();
          if (dataStr) {
            try {
              const data = JSON.parse(dataStr);
              if (data.event === "detection" || data.detection) {
                const details = data.detection || data;
                if (onDetectionDetails) {
                  onDetectionDetails(details);
                }
                if (details.resolved_source_lang && onDetectedLanguage) {
                  onDetectedLanguage(details.resolved_source_lang, details);
                }
              }
              if (data.event === "reset" && onReset) {
                onReset();
              }
              if (data.event === "domain" && data.domain && onDomain) {
                onDomain(data.domain as DomainDetails);
              }
              if (Array.isArray(data.warnings) && data.warnings.length > 0 && onWarnings) {
                onWarnings(data.warnings as TranslationWarning[]);
              }
              if (data.warning) {
                onWarning(data.warning);
              }
              if (data.resolved_source_lang && onDetectedLanguage) {
                onDetectedLanguage(data.resolved_source_lang, data.detection);
              }
              if (data.text) {
                onChunk(data.text);
              } else if (data.error) {
                onError(data.error, data.code);
              }
            } catch (err) {
              console.error("Failed to parse SSE data:", err, dataStr);
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

/** Thông tin thẻ do AI trích xuất; `meaning` là nghĩa tiếng Việt (khi truyền sourceLang). */
export interface ExtractedFlashcard {
  word?: string;
  phonetic?: string;
  part_of_speech?: string;
  meaning?: string;
  example?: string;
  example_translation?: string;
}

export async function extractFlashcard(
  word: string,
  context: string,
  domain: string = "",
  sourceLang?: string,
  signal?: AbortSignal
): Promise<ApiResult<ExtractedFlashcard>> {
  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/flashcard"), {
      method: "POST",
      headers,
      signal,
      // Chỉ gửi source_lang khi đã biết chắc (không gửi "auto"): backend sẽ từ chối giá trị lạ.
      body: JSON.stringify({
        word,
        context: context || word,
        domain,
        ...(sourceLang ? { source_lang: sourceLang, target_lang: "vi" } : {}),
      }),
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

export async function analyzeWord(
  request: {
    text: string;
    selected_text: string;
    source_lang: string;
    target_lang: string;
  },
  signal?: AbortSignal
): Promise<ApiResult<any>> {
  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/analyze_word"), {
      method: "POST",
      headers,
      body: JSON.stringify(request),
      signal,
    });

    if (res.ok) {
      const data = await res.json();
      return { ok: true, data: data.data };
    }
    let message = "Failed to analyze word";
    try {
      const errorData = await res.json();
      message = errorData?.detail || errorData?.error?.message || message;
    } catch {
      // Keep the generic message when the backend does not return JSON.
    }
    return { ok: false, error: { message } };
  } catch (error: any) {
    if (error?.name === "AbortError") {
      throw error; // Let the hook handle it
    }
    return { ok: false, error: { message: "Network error" } };
  }
}

export async function detectLanguage(text: string): Promise<ApiResult<LanguageDetectionDetails>> {
  if (!text.trim()) {
    return { ok: false, error: { message: "Vui lòng nhập văn bản để nhận diện ngôn ngữ." } };
  }
  try {
    const token = getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(getApiUrl("/api/v1/translate/detect"), {
      method: "POST",
      headers,
      body: JSON.stringify({ text }),
    });

    if (res.ok) {
      const data = await res.json();
      return { ok: true, data: data.data };
    }
    const err = await res.json().catch(() => ({}));
    return { ok: false, error: { message: err.detail || "Không thể nhận diện ngôn ngữ." } };
  } catch (e: any) {
    return { ok: false, error: { message: e?.message || "Lỗi mạng khi nhận diện ngôn ngữ." } };
  }
}


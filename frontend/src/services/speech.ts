/**
 * Phát âm: chọn ngôn ngữ giọng đọc và phương án dự phòng bằng giọng đọc của trình duyệt (speechSynthesis).
 * Nguyên tắc như phần Flashcard: không bao giờ đoán ngôn ngữ — chưa rõ thì trả null thay vì mặc định tiếng Anh.
 */

/** 10 ngôn ngữ của hệ thống -> mã locale (cùng giá trị backend/TTS và trình duyệt hiểu). */
export const SPEECH_LOCALES: Record<string, string> = {
  en: "en-US",
  de: "de-DE",
  zh: "zh-CN",
  ja: "ja-JP",
  ko: "ko-KR",
  fr: "fr-FR",
  es: "es-ES",
  ru: "ru-RU",
  th: "th-TH",
  vi: "vi-VN"
};

/** "de" | "de-AT" | "de_DE" -> "de-DE"; mã không thuộc 10 ngôn ngữ (kể cả "auto") -> null. */
export function toSpeechLocale(code?: string | null): string | null {
  const base = (code || "").trim().toLowerCase().replace("_", "-").split("-")[0];
  return SPEECH_LOCALES[base] ?? null;
}

export interface DetectionForSpeech {
  lang?: string | null;
  status?: string | null;
  /** true = kết quả nhận diện thuộc đúng văn bản đang hiển thị (không phải nhãn cũ còn sót lại). */
  fresh: boolean;
}

/**
 * Ngôn ngữ để đọc văn bản NGUỒN.
 * - Chọn tay: dùng đúng ngôn ngữ đó.
 * - "auto": chỉ dùng kết quả nhận diện chắc chắn (`detected`) và còn mới; ngược lại null (không đoán).
 */
export function resolveSpeechLang(sourceLang: string, detection?: DetectionForSpeech | null): string | null {
  if ((sourceLang || "").trim().toLowerCase() !== "auto") return toSpeechLocale(sourceLang);
  if (detection && detection.fresh && detection.status === "detected") return toSpeechLocale(detection.lang);
  return null;
}

// ---- Dự phòng: giọng đọc của trình duyệt ------------------------------------------------------

export function browserSpeechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";
}

/** Chọn giọng của trình duyệt khớp ngôn ngữ (ưu tiên đúng locale, sau đó cùng ngôn ngữ). */
export function pickBrowserVoice(voices: { lang: string }[], locale: string): { lang: string } | null {
  const norm = (s: string) => s.toLowerCase().replace("_", "-");
  const want = norm(locale);
  return voices.find((v) => norm(v.lang) === want) ?? voices.find((v) => norm(v.lang).startsWith(want.slice(0, 2))) ?? null;
}

export function hasBrowserVoice(locale: string): boolean {
  if (!browserSpeechSupported()) return false;
  return pickBrowserVoice(window.speechSynthesis.getVoices() as any, locale) !== null;
}

export interface BrowserSpeechHandlers {
  onEnd?: () => void;
  /** Gọi khi không phát được (không có giọng cho ngôn ngữ này hoặc trình duyệt báo lỗi). */
  onError?: (reason: "unsupported" | "no-voice" | "error") => void;
}

/**
 * Đọc bằng trình duyệt. Trả về true nếu đã bắt đầu đọc. Không có giọng cho ngôn ngữ (vd máy chưa cài giọng Thái)
 * thì báo `no-voice` thay vì đọc bằng giọng mặc định sai ngôn ngữ.
 */
export function speakWithBrowser(text: string, locale: string, handlers: BrowserSpeechHandlers = {}): boolean {
  if (!browserSpeechSupported()) {
    handlers.onError?.("unsupported");
    return false;
  }
  const synth = window.speechSynthesis;
  const voice = pickBrowserVoice(synth.getVoices() as any, locale) as SpeechSynthesisVoice | null;
  // getVoices() có thể rỗng ở lần gọi đầu (đang nạp): khi đó vẫn thử với `lang`, trình duyệt tự chọn giọng phù hợp.
  if (!voice && synth.getVoices().length > 0) {
    handlers.onError?.("no-voice");
    return false;
  }
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = locale;
  utterance.rate = 0.95;
  if (voice) utterance.voice = voice;
  utterance.onend = () => handlers.onEnd?.();
  utterance.onerror = (e: any) => {
    // "canceled"/"interrupted" là do chính ta gọi cancel() khi người dùng bấm tiếp: không phải lỗi.
    if (e?.error === "canceled" || e?.error === "interrupted") return;
    handlers.onError?.("error");
  };
  synth.speak(utterance);
  return true;
}

export function cancelBrowserSpeech(): void {
  if (browserSpeechSupported()) window.speechSynthesis.cancel();
}

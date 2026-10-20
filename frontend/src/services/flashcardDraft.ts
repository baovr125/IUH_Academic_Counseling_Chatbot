import { LANG_CONFIG, LEARNABLE_LANGS, isLearnableLang, normalizeLangCode } from "./deckStorage";

/**
 * Xác định NGÔN NGỮ và hai mặt (từ ngoại ngữ / nghĩa tiếng Việt) của thẻ khi lưu từ Realtime Translation.
 * Hàm thuần, không gọi mạng. Nguyên tắc: không bao giờ đoán ngôn ngữ — chưa chắc thì trả về yêu cầu người dùng chọn.
 */

/** Nguồn gốc của ngôn ngữ thẻ, dùng để giải thích cho người dùng. */
export type LanguageOrigin = "manual" | "detected" | "user" | "target";

export interface DetectionSnapshot {
  /** Ngôn ngữ nhận diện được cho CHÍNH văn bản đang hiển thị (người gọi phải tự đối chiếu, tránh kết quả cũ). */
  lang?: string | null;
  status?: string | null;
  engine?: string | null;
  confidence?: number | null;
  /** Ứng viên theo thứ tự khả năng giảm dần, dùng để gợi ý khi chưa chắc. */
  candidates?: string[];
}

export interface DraftInput {
  /** Ngôn ngữ nguồn người dùng chọn: mã ngôn ngữ hoặc "auto". */
  sourceLang: string;
  targetLang: string;
  sourceText: string;
  translatedText: string;
  detection?: DetectionSnapshot | null;
  /** Người dùng bôi đen một từ/cụm từ; `side` là khung chứa vùng chọn. */
  selection?: { text: string; side: "source" | "target"; context?: string } | null;
  /** Ngôn ngữ nguồn do người dùng chọn tay khi hệ thống không nhận diện chắc chắn. */
  userSource?: string | null;
}

export interface ReadyDraft {
  status: "ready";
  /** Ngôn ngữ của `term` — bộ sưu tập sẽ chứa thẻ. */
  langCode: string;
  origin: LanguageOrigin;
  term: string;
  /** Nghĩa tiếng Việt (có thể rỗng khi cần AI/dịch điền). */
  meaning: string;
  /** Câu ngữ cảnh (cùng ngôn ngữ với term); rỗng nếu không có. */
  example: string;
  /** Bôi đen một từ: nghĩa/phiên âm/ví dụ cần lấy từ AI. */
  needsExtraction: boolean;
  /** Cặp ngoại ngữ -> ngoại ngữ: nghĩa tiếng Việt phải dịch từ văn bản này. */
  translateMeaningFrom?: { text: string; lang: string };
  /** Mặt nào của bản dịch là `term`. */
  termSide: "source" | "target";
}

export interface ChooseSourceDraft {
  status: "choose-source";
  reason: "undetected" | "uncertain";
  /** Ngôn ngữ nguồn có thể chọn, gợi ý (nếu có) đứng đầu. */
  options: string[];
}

export interface LearnOption {
  langCode: string;
  term: string;
  /** Văn bản ở ngôn ngữ còn lại, dùng để dịch ra nghĩa tiếng Việt. */
  counterpart: { text: string; lang: string };
  termSide: "source" | "target";
}

export interface ChooseLearnDraft {
  status: "choose-learn";
  options: LearnOption[];
}

export interface UnsupportedDraft {
  status: "unsupported";
  code: "EMPTY" | "SAME_LANGUAGE" | "VI_SELECTION" | "LANG_UNSUPPORTED";
  message: string;
}

export type DraftOutcome = ReadyDraft | ChooseSourceDraft | ChooseLearnDraft | UnsupportedDraft;

function langName(code: string): string {
  return LANG_CONFIG[code]?.viName ?? code.toUpperCase();
}

function resolveSource(input: DraftInput): { lang: string; origin: LanguageOrigin } | { invalid: string } | null {
  if (input.userSource) {
    const lang = normalizeLangCode(input.userSource);
    return lang ? { lang, origin: "user" } : { invalid: input.userSource };
  }
  const chosen = (input.sourceLang || "").trim().toLowerCase();
  if (chosen && chosen !== "auto") {
    const lang = normalizeLangCode(chosen);
    return lang ? { lang, origin: "manual" } : { invalid: chosen };
  }
  const d = input.detection;
  if (d && d.status === "detected" && d.lang) {
    const lang = normalizeLangCode(d.lang);
    if (lang) return { lang, origin: "detected" };
  }
  return null;
}

function sourceOptions(input: DraftInput, target: string, d?: DetectionSnapshot | null): string[] {
  const suggested = (d?.candidates ?? []).map((c) => normalizeLangCode(c)).filter((c): c is string => !!c);
  const all = [...suggested, ...LEARNABLE_LANGS, "vi"];
  const seen = new Set<string>();
  // Nguồn không thể trùng đích; tiếng Việt chỉ là nguồn hợp lệ khi đích là ngoại ngữ.
  return all.filter((c) => c !== target && !seen.has(c) && !!seen.add(c));
}

export function buildFlashcardDraft(input: DraftInput): DraftOutcome {
  const sourceText = (input.sourceText || "").trim();
  const translated = (input.translatedText || "").trim();
  const selected = input.selection?.text?.trim() || "";
  const target = normalizeLangCode(input.targetLang);

  if (!selected && (!sourceText || !translated)) {
    return { status: "unsupported", code: "EMPTY", message: "Chưa có nội dung và bản dịch để lưu." };
  }
  if (!target) {
    return { status: "unsupported", code: "LANG_UNSUPPORTED", message: "Ngôn ngữ đích không được hỗ trợ." };
  }

  const resolved = resolveSource(input);
  if (resolved && "invalid" in resolved) {
    return { status: "unsupported", code: "LANG_UNSUPPORTED", message: `Ngôn ngữ "${resolved.invalid}" chưa được hỗ trợ.` };
  }
  if (!resolved && selected && input.selection!.side === "target") {
    // Từ bôi đen nằm ở khung bản dịch: ngôn ngữ của nó chính là ngôn ngữ đích đã biết, không cần nhận diện nguồn.
    if (target === "vi") {
      return {
        status: "unsupported",
        code: "VI_SELECTION",
        message: "Bạn đang bôi đen từ tiếng Việt. Hãy bôi đen từ ngoại ngữ để lưu (nghĩa tiếng Việt sẽ được tự điền).",
      };
    }
    return {
      status: "ready", langCode: target, origin: "target", term: selected, meaning: "",
      example: (input.selection!.context || "").trim(), needsExtraction: true, termSide: "target",
    };
  }
  if (!resolved) {
    const uncertain = input.detection?.status === "uncertain";
    return {
      status: "choose-source",
      reason: uncertain ? "uncertain" : "undetected",
      options: sourceOptions(input, target, input.detection),
    };
  }

  const source = resolved.lang;
  if (source === target) {
    return {
      status: "unsupported",
      code: "SAME_LANGUAGE",
      message: "Ngôn ngữ nguồn và ngôn ngữ đích giống nhau nên không có nghĩa để lưu.",
    };
  }

  // ---- Bôi đen một từ/cụm từ -------------------------------------------------
  if (selected) {
    const side = input.selection!.side;
    const lang = side === "source" ? source : target;
    if (lang === "vi") {
      return {
        status: "unsupported",
        code: "VI_SELECTION",
        message: "Bạn đang bôi đen từ tiếng Việt. Hãy bôi đen từ ngoại ngữ để lưu (nghĩa tiếng Việt sẽ được tự điền).",
      };
    }
    return {
      status: "ready",
      langCode: lang,
      origin: side === "source" ? resolved.origin : "target",
      term: selected,
      meaning: "",
      example: (input.selection!.context || "").trim(),
      needsExtraction: true,
      termSide: side,
    };
  }

  // ---- Cả đoạn văn bản --------------------------------------------------------
  if (target === "vi") {
    // ngoại ngữ -> Việt: term là văn bản nguồn, nghĩa là bản dịch.
    return {
      status: "ready", langCode: source, origin: resolved.origin, term: sourceText, meaning: translated,
      example: "", needsExtraction: false, termSide: "source",
    };
  }
  if (source === "vi") {
    // Việt -> ngoại ngữ: term là bản dịch, nghĩa là văn bản tiếng Việt gốc.
    return {
      status: "ready", langCode: target, origin: "target", term: translated, meaning: sourceText,
      example: "", needsExtraction: false, termSide: "target",
    };
  }
  // ngoại ngữ -> ngoại ngữ khác: người dùng chọn ngôn ngữ muốn học, nghĩa tiếng Việt được dịch tự động.
  return {
    status: "choose-learn",
    options: [
      { langCode: source, term: sourceText, counterpart: { text: translated, lang: target }, termSide: "source" },
      { langCode: target, term: translated, counterpart: { text: sourceText, lang: source }, termSide: "target" },
    ],
  };
}

/** Chốt lựa chọn "học ngôn ngữ nào" của cặp ngoại ngữ -> ngoại ngữ. */
export function resolveLearnChoice(draft: ChooseLearnDraft, langCode: string): ReadyDraft | null {
  const option = draft.options.find((o) => o.langCode === langCode);
  if (!option || !isLearnableLang(option.langCode)) return null;
  return {
    status: "ready",
    langCode: option.langCode,
    origin: "user",
    term: option.term,
    meaning: "",
    example: "",
    needsExtraction: false,
    translateMeaningFrom: option.counterpart,
    termSide: option.termSide,
  };
}

/** Tên ngôn ngữ để hiển thị trong thông báo. */
export function languageLabel(code: string): string {
  return `${LANG_CONFIG[code]?.flag ?? "🌐"} ${langName(code)}`;
}

/** Lý do (tiếng Việt) của việc ngôn ngữ thẻ được xác định như vậy. */
export function describeOrigin(origin: LanguageOrigin): string {
  switch (origin) {
    case "manual":
      return "Theo ngôn ngữ nguồn bạn đã chọn";
    case "detected":
      return "Hệ thống đã nhận diện ngôn ngữ nguồn";
    case "user":
      return "Theo lựa chọn của bạn";
    case "target":
      return "Theo ngôn ngữ bản dịch";
  }
}

import { describe, it, expect } from "vitest";
import { buildFlashcardDraft, resolveLearnChoice, type DraftInput } from "../src/services/flashcardDraft";
import { LANG_CONFIG, LANG_CODES, LEARNABLE_LANGS, normalizeLangCode } from "../src/services/deckStorage";

const base = (over: Partial<DraftInput>): DraftInput => ({
  sourceLang: "de",
  targetLang: "vi",
  sourceText: "Guten Morgen",
  translatedText: "Chào buổi sáng",
  ...over,
});

describe("LANG_CONFIG — 10 ngôn ngữ", () => {
  it("dùng mã ISO, đúng thứ tự, tiếng Việt không học được", () => {
    expect(LANG_CODES).toEqual(["en", "de", "zh", "ja", "ko", "fr", "es", "ru", "th", "vi"]);
    expect(LEARNABLE_LANGS).toHaveLength(9);
    expect(LANG_CONFIG.vi.learnable).toBe(false);
  });

  it.each([["en-US", "en"], ["ZH_cn", "zh"], [" ja ", "ja"], ["vi", "vi"]])("chuẩn hóa %s -> %s", (raw, expected) => {
    expect(normalizeLangCode(raw)).toBe(expected);
  });

  it.each(["auto", "", null, undefined, "gb", "cn", "jp", "kr", "vn", "xx"])("không đoán/không nhận mã cờ quốc gia: %s", (raw) => {
    expect(normalizeLangCode(raw as any)).toBeNull();
  });
});

describe("buildFlashcardDraft — toàn bộ văn bản", () => {
  it("Đức -> Việt (ví dụ 'Guten Morgen'): thẻ thuộc tiếng Đức, nghĩa tiếng Việt", () => {
    const out = buildFlashcardDraft(base({}));
    expect(out).toMatchObject({ status: "ready", langCode: "de", origin: "manual", term: "Guten Morgen", meaning: "Chào buổi sáng", termSide: "source" });
  });

  it.each(LEARNABLE_LANGS)("ngôn ngữ nguồn chọn tay %s -> bộ sưu tập %s", (lang) => {
    const out = buildFlashcardDraft(base({ sourceLang: lang }));
    expect(out.status).toBe("ready");
    expect((out as any).langCode).toBe(lang);
  });

  it("auto + đã nhận diện chắc chắn -> dùng ngôn ngữ nhận diện", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", detection: { lang: "de", status: "detected" } }));
    expect(out).toMatchObject({ status: "ready", langCode: "de", origin: "detected" });
  });

  it.each(["uncertain", "unknown", "unsupported", "system_error", undefined])("auto + nhận diện '%s' -> phải hỏi, không đoán", (status) => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", detection: { lang: "de", status: status as any, candidates: ["de", "en"] } }));
    expect(out.status).toBe("choose-source");
  });

  it("auto + không có kết quả nhận diện -> hỏi, gợi ý ứng viên trước, không gồm tiếng Việt khi đích là tiếng Việt", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", detection: { status: "uncertain", candidates: ["fr", "es"] } }));
    expect(out).toMatchObject({ status: "choose-source", reason: "uncertain" });
    const options = (out as any).options as string[];
    expect(options.slice(0, 2)).toEqual(["fr", "es"]);
    expect(options).not.toContain("vi");
    expect(new Set(options).size).toBe(options.length);
  });

  it("người dùng chọn nguồn sau khi được hỏi -> thẻ vào đúng ngôn ngữ đã chọn", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", userSource: "fr" }));
    expect(out).toMatchObject({ status: "ready", langCode: "fr", origin: "user" });
  });

  it("Việt -> ngoại ngữ: thẻ thuộc ngôn ngữ ĐÍCH, term là bản dịch, nghĩa là câu tiếng Việt", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "vi", targetLang: "ja", sourceText: "Xin chào", translatedText: "こんにちは" }));
    expect(out).toMatchObject({ status: "ready", langCode: "ja", term: "こんにちは", meaning: "Xin chào", termSide: "target" });
  });

  it("auto + đích ngoại ngữ + nguồn chưa rõ -> hỏi và cho phép chọn tiếng Việt", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", targetLang: "ja" }));
    expect(out.status).toBe("choose-source");
    expect((out as any).options).toContain("vi");
    expect((out as any).options).not.toContain("ja");
  });

  it("ngoại ngữ -> ngoại ngữ: người dùng chọn ngôn ngữ muốn học, nghĩa tiếng Việt sẽ dịch tự động", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "en", targetLang: "de", sourceText: "Good morning", translatedText: "Guten Morgen" }));
    expect(out.status).toBe("choose-learn");
    const learnDe = resolveLearnChoice(out as any, "de")!;
    expect(learnDe).toMatchObject({ langCode: "de", term: "Guten Morgen", meaning: "", translateMeaningFrom: { text: "Good morning", lang: "en" }, termSide: "target" });
    const learnEn = resolveLearnChoice(out as any, "en")!;
    expect(learnEn).toMatchObject({ langCode: "en", term: "Good morning", translateMeaningFrom: { text: "Guten Morgen", lang: "de" } });
    expect(resolveLearnChoice(out as any, "fr")).toBeNull();
  });

  it("nguồn trùng đích -> không lưu", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "en", targetLang: "en" }));
    expect(out).toMatchObject({ status: "unsupported", code: "SAME_LANGUAGE" });
  });

  it("chưa có văn bản hoặc bản dịch -> không lưu", () => {
    expect(buildFlashcardDraft(base({ translatedText: "  " }))).toMatchObject({ status: "unsupported", code: "EMPTY" });
    expect(buildFlashcardDraft(base({ sourceText: "" }))).toMatchObject({ status: "unsupported", code: "EMPTY" });
  });

  it("mã ngôn ngữ ngoài 10 ngôn ngữ (kể cả mã cờ 'jp') -> bị từ chối", () => {
    expect(buildFlashcardDraft(base({ sourceLang: "jp" }))).toMatchObject({ status: "unsupported", code: "LANG_UNSUPPORTED" });
    expect(buildFlashcardDraft(base({ targetLang: "xx" }))).toMatchObject({ status: "unsupported", code: "LANG_UNSUPPORTED" });
  });

  it("cắt khoảng trắng hai đầu", () => {
    const out = buildFlashcardDraft(base({ sourceText: "  Hallo  ", translatedText: "  Xin chào " }));
    expect(out).toMatchObject({ term: "Hallo", meaning: "Xin chào" });
  });
});

describe("buildFlashcardDraft — bôi đen từ", () => {
  it("từ ở khung nguồn (ngoại ngữ) -> ngôn ngữ nguồn, cần AI điền nghĩa", () => {
    const out = buildFlashcardDraft(base({ selection: { text: "Morgen", side: "source", context: "Guten Morgen, Anna!" } }));
    expect(out).toMatchObject({ status: "ready", langCode: "de", term: "Morgen", meaning: "", example: "Guten Morgen, Anna!", needsExtraction: true });
  });

  it("từ ở khung bản dịch (đích ngoại ngữ) -> ngôn ngữ ĐÍCH", () => {
    const out = buildFlashcardDraft(
      base({ sourceLang: "vi", targetLang: "de", sourceText: "Chào buổi sáng", translatedText: "Guten Morgen", selection: { text: "Morgen", side: "target" } })
    );
    expect(out).toMatchObject({ status: "ready", langCode: "de", origin: "target", termSide: "target" });
  });

  it("từ ở khung bản dịch vẫn lưu được dù ngôn ngữ nguồn (auto) chưa nhận diện", () => {
    const out = buildFlashcardDraft(
      base({ sourceLang: "auto", targetLang: "de", sourceText: "???", translatedText: "Guten Morgen", selection: { text: "Morgen", side: "target" } })
    );
    expect(out).toMatchObject({ status: "ready", langCode: "de" });
  });

  it("bôi đen từ tiếng Việt (khung bản dịch, đích = vi) -> từ chối kèm hướng dẫn, không lưu bừa", () => {
    const out = buildFlashcardDraft(base({ selection: { text: "buổi sáng", side: "target" } }));
    expect(out).toMatchObject({ status: "unsupported", code: "VI_SELECTION" });
  });

  it("bôi đen từ tiếng Việt ở khung nguồn -> từ chối", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "vi", targetLang: "en", selection: { text: "xin chào", side: "source" } }));
    expect(out).toMatchObject({ status: "unsupported", code: "VI_SELECTION" });
  });

  it("auto + khung nguồn + chưa nhận diện -> hỏi ngôn ngữ", () => {
    const out = buildFlashcardDraft(base({ sourceLang: "auto", selection: { text: "Morgen", side: "source" } }));
    expect(out.status).toBe("choose-source");
  });

  it("chỉ cần có vùng chọn, không cần bản dịch hoàn chỉnh", () => {
    const out = buildFlashcardDraft(base({ translatedText: "", selection: { text: "Morgen", side: "source" } }));
    expect(out.status).toBe("ready");
  });
});

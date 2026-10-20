import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { pickBrowserVoice, resolveSpeechLang, speakWithBrowser, SPEECH_LOCALES, toSpeechLocale } from "../src/services/speech";
import { LANG_CODES } from "../src/services/deckStorage";

describe("toSpeechLocale", () => {
  it("phủ đủ 10 ngôn ngữ của hệ thống, cùng danh sách với LANG_CONFIG", () => {
    expect(Object.keys(SPEECH_LOCALES)).toEqual(LANG_CODES);
  });

  it.each([["de", "de-DE"], ["de-AT", "de-DE"], ["ZH_cn", "zh-CN"], ["ja", "ja-JP"], ["th", "th-TH"], ["vi", "vi-VN"], ["EN-gb", "en-US"]])(
    "%s -> %s", (raw, expected) => expect(toSpeechLocale(raw)).toBe(expected)
  );

  it.each(["auto", "", null, undefined, "xx", "jp", "gb"])("%s -> null (không đoán, không mặc định tiếng Anh)", (raw) => {
    expect(toSpeechLocale(raw as any)).toBeNull();
  });
});

describe("resolveSpeechLang — ngôn ngữ đọc văn bản nguồn", () => {
  it("chọn tay: dùng thẳng, bỏ qua kết quả nhận diện", () => {
    expect(resolveSpeechLang("ja", { lang: "de", status: "detected", fresh: true })).toBe("ja-JP");
  });

  it("auto + nhận diện chắc chắn và còn mới -> dùng ngôn ngữ nhận diện", () => {
    expect(resolveSpeechLang("auto", { lang: "de", status: "detected", fresh: true })).toBe("de-DE");
  });

  it.each(["uncertain", "unknown", "unsupported", "system_error", null, undefined])("auto + trạng thái '%s' -> null", (status) => {
    expect(resolveSpeechLang("auto", { lang: "de", status, fresh: true })).toBeNull();
  });

  it("auto + nhãn cũ của văn bản trước (fresh=false) -> null", () => {
    expect(resolveSpeechLang("auto", { lang: "de", status: "detected", fresh: false })).toBeNull();
  });

  it("auto + chưa có nhận diện -> null (trước đây bị đọc bằng giọng tiếng Anh)", () => {
    expect(resolveSpeechLang("auto", null)).toBeNull();
    expect(resolveSpeechLang("auto", { lang: null, status: null, fresh: true })).toBeNull();
  });

  it.each(LANG_CODES)("chọn tay %s", (code) => expect(resolveSpeechLang(code)).toBe(SPEECH_LOCALES[code]));
});

describe("pickBrowserVoice", () => {
  const voices = [{ lang: "en_US" }, { lang: "de-AT" }, { lang: "de-DE" }, { lang: "ja-JP" }];
  it("ưu tiên đúng locale, sau đó cùng ngôn ngữ, không có thì null", () => {
    expect(pickBrowserVoice(voices, "de-DE")).toBe(voices[2]);
    expect(pickBrowserVoice([voices[1]], "de-DE")).toBe(voices[1]);
    expect(pickBrowserVoice(voices, "th-TH")).toBeNull();
  });
});

describe("speakWithBrowser — dự phòng khi máy chủ TTS lỗi", () => {
  let utterances: any[];
  let synth: { speak: any; cancel: any; getVoices: any };

  beforeEach(() => {
    utterances = [];
    synth = { speak: vi.fn((u) => utterances.push(u)), cancel: vi.fn(), getVoices: vi.fn(() => [{ lang: "de-DE", name: "Anna" }]) };
    vi.stubGlobal("SpeechSynthesisUtterance", function (this: any, text: string) { this.text = text; });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: synth });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    delete (window as any).speechSynthesis;
  });

  it("đọc với đúng locale và giọng khớp", () => {
    const onEnd = vi.fn();
    expect(speakWithBrowser("Guten Morgen", "de-DE", { onEnd })).toBe(true);
    expect(utterances[0]).toMatchObject({ text: "Guten Morgen", lang: "de-DE", voice: { name: "Anna" } });
    utterances[0].onend();
    expect(onEnd).toHaveBeenCalled();
  });

  it("máy có giọng nhưng không có cho ngôn ngữ này -> báo no-voice, không đọc bằng giọng sai", () => {
    const onError = vi.fn();
    expect(speakWithBrowser("สวัสดี", "th-TH", { onError })).toBe(false);
    expect(onError).toHaveBeenCalledWith("no-voice");
    expect(synth.speak).not.toHaveBeenCalled();
  });

  it("danh sách giọng chưa nạp (rỗng) -> vẫn thử đọc với lang", () => {
    synth.getVoices.mockReturnValue([]);
    expect(speakWithBrowser("สวัสดี", "th-TH")).toBe(true);
    expect(utterances[0].lang).toBe("th-TH");
  });

  it("trình duyệt báo lỗi thật -> onError('error'); bị hủy do bấm tiếp thì không tính là lỗi", () => {
    const onError = vi.fn();
    speakWithBrowser("Hallo", "de-DE", { onError });
    utterances[0].onerror({ error: "interrupted" });
    expect(onError).not.toHaveBeenCalled();
    utterances[0].onerror({ error: "synthesis-failed" });
    expect(onError).toHaveBeenCalledWith("error");
  });

  it("trình duyệt không hỗ trợ -> onError('unsupported')", () => {
    delete (window as any).speechSynthesis;
    const onError = vi.fn();
    expect(speakWithBrowser("Hallo", "de-DE", { onError })).toBe(false);
    expect(onError).toHaveBeenCalledWith("unsupported");
  });
});

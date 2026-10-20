import React, { useState } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const streamMock = vi.fn();
vi.mock("../src/services/translationService", () => ({
  streamTranslation: (...args: unknown[]) => streamMock(...args),
  extractFlashcard: vi.fn(),
  translateText: vi.fn()
}));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "u1" } }) }));
vi.mock("../src/components/translation/FloatingMenu", () => ({ FloatingMenu: () => null }));
vi.mock("../src/components/translation/SaveFlashcardModal", () => ({ SaveFlashcardModal: () => null }));
vi.mock("../src/components/translation/WordAnalysisPopup", () => ({ WordAnalysisPopup: () => null }));
vi.mock("../src/hooks/useWordAnalysis", () => ({ useWordAnalysis: () => ({ analyze: vi.fn(), reset: vi.fn(), state: null, close: vi.fn() }) }));

import { TranslationBox } from "../src/components/translation/TranslationBox";

function Harness({ sourceLang, targetLang = "vi" }: { sourceLang: string; targetLang?: string }) {
  const [text, setText] = useState("");
  return (
    <TranslationBox
      sourceLang={sourceLang}
      targetLang={targetLang}
      sourceText={text}
      setSourceLang={() => {}}
      setTargetLang={() => {}}
      setSourceText={setText}
      swapLanguages={() => {}}
      targetLangMeta={{ flag: "🇻🇳", label: "Tiếng Việt", defaultTitle: "Bản dịch" }}
    />
  );
}

const last = () => {
  const a = streamMock.mock.calls[streamMock.mock.calls.length - 1];
  return { onChunk: a[1] as (t: string) => void, onComplete: a[4] as () => void, onDetected: a[6] as (l: string, d?: unknown) => void };
};

async function translate(text: string, translated: string, detect?: { lang: string; status?: string }) {
  fireEvent.change(screen.getByPlaceholderText(/Nhập văn bản/), { target: { value: text } });
  await waitFor(() => expect(streamMock).toHaveBeenCalled(), { timeout: 3000 });
  await act(async () => {
    const cb = last();
    if (detect) cb.onDetected(detect.lang, { status: detect.status ?? "detected", engine: "fusion", confidence: 0.99, candidates: [] });
    cb.onChunk(translated);
    cb.onComplete();
  });
}

/** Audio giả: ghi lại URL và cho test chủ động gây lỗi / thành công. */
let audios: { src: string; onerror: (() => void) | null; onended: (() => void) | null; play: ReturnType<typeof vi.fn> }[];
let playResult: () => Promise<void>;

beforeEach(() => {
  streamMock.mockReset();
  streamMock.mockResolvedValue(undefined);
  audios = [];
  playResult = () => Promise.resolve();
  vi.stubGlobal(
    "Audio",
    function (this: any, src: string) {
      this.src = src;
      this.onerror = null;
      this.onended = null;
      this.play = vi.fn(() => playResult());
      this.pause = vi.fn();
      this.load = vi.fn();
      this.removeAttribute = vi.fn();
      audios.push(this);
    }
  );
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false })));
});
afterEach(() => {
  vi.unstubAllGlobals();
  delete (window as any).speechSynthesis;
});

const readSource = () => screen.getByRole("button", { name: "Đọc văn bản" });
const audioLang = () => new URL(audios[audios.length - 1].src, "http://x").searchParams.get("lang");

describe("TranslationBox — phát âm văn bản nguồn", () => {
  it("auto + chưa nhận diện: nút đọc bị tắt và giải thích lý do (không đọc bằng giọng tiếng Anh)", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Guten Morgen", "Chào buổi sáng");
    expect(readSource()).toBeDisabled();
    expect(readSource()).toHaveAttribute("title", expect.stringMatching(/Chưa xác định được ngôn ngữ/));
    fireEvent.click(readSource());
    expect(audios).toHaveLength(0);
  });

  it.each([["de", "de-DE"], ["ja", "ja-JP"], ["th", "th-TH"], ["ko", "ko-KR"], ["fr", "fr-FR"], ["es", "es-ES"], ["ru", "ru-RU"], ["zh", "zh-CN"]])(
    "auto + nhận diện %s -> yêu cầu giọng %s", async (detected, locale) => {
      render(<Harness sourceLang="auto" />);
      await translate("Xin chào thế giới", "Hello", { lang: detected });
      expect(readSource()).toBeEnabled();
      fireEvent.click(readSource());
      expect(audioLang()).toBe(locale);
    }
  );

  it("auto + nhận diện chưa chắc (uncertain): không đọc", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Bonjour", "Xin chào", { lang: "fr", status: "uncertain" });
    expect(readSource()).toBeDisabled();
  });

  it("nhãn nhận diện cũ của văn bản trước không được dùng cho văn bản mới", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Guten Morgen", "Chào buổi sáng", { lang: "de" });
    expect(readSource()).toBeEnabled();
    streamMock.mockClear();
    await translate("Good morning", "Chào buổi sáng"); // lượt mới không có kết quả nhận diện
    expect(readSource()).toBeDisabled();
  });

  it("chọn tay ngôn ngữ nguồn: dùng ngôn ngữ đó", async () => {
    render(<Harness sourceLang="ja" />);
    await translate("おはよう", "Chào buổi sáng");
    fireEvent.click(readSource());
    expect(audioLang()).toBe("ja-JP");
  });

  it("bản dịch đọc bằng giọng của ngôn ngữ đích", async () => {
    render(<Harness sourceLang="vi" targetLang="de" />);
    await translate("Chào buổi sáng", "Guten Morgen");
    fireEvent.click(screen.getByTitle("Đọc bản dịch"));
    expect(audioLang()).toBe("de-DE");
  });
});

describe("TranslationBox — dự phòng khi máy chủ giọng đọc lỗi", () => {
  const installSynth = (voices: { lang: string }[]) => {
    const spoken: any[] = [];
    vi.stubGlobal("SpeechSynthesisUtterance", function (this: any, text: string) { this.text = text; });
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: { speak: vi.fn((u) => spoken.push(u)), cancel: vi.fn(), getVoices: () => voices }
    });
    return spoken;
  };

  it("audio lỗi (503) -> chuyển sang giọng đọc của trình duyệt với đúng ngôn ngữ", async () => {
    const spoken = installSynth([{ lang: "de-DE" }]);
    render(<Harness sourceLang="de" />);
    await translate("Guten Morgen", "Chào buổi sáng");
    fireEvent.click(readSource());
    act(() => audios[audios.length - 1].onerror?.());
    expect(spoken).toHaveLength(1);
    expect(spoken[0]).toMatchObject({ text: "Guten Morgen", lang: "de-DE" });
  });

  it("play() bị từ chối -> cũng chuyển sang trình duyệt", async () => {
    const spoken = installSynth([{ lang: "ja-JP" }]);
    playResult = () => Promise.reject(Object.assign(new Error("not supported"), { name: "NotSupportedError" }));
    render(<Harness sourceLang="ja" />);
    await translate("おはよう", "Chào buổi sáng");
    fireEvent.click(readSource());
    await waitFor(() => expect(spoken).toHaveLength(1));
  });

  it("người dùng bấm dừng (AbortError) -> không kích hoạt dự phòng", async () => {
    const spoken = installSynth([{ lang: "de-DE" }]);
    playResult = () => Promise.reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
    render(<Harness sourceLang="de" />);
    await translate("Guten Morgen", "Chào buổi sáng");
    fireEvent.click(readSource());
    await act(async () => {});
    expect(spoken).toHaveLength(0);
  });

  it("máy chưa cài giọng cho ngôn ngữ -> báo rõ, không đọc bằng giọng sai", async () => {
    const spoken = installSynth([{ lang: "en-US" }]);
    render(<Harness sourceLang="th" />);
    await translate("สวัสดี", "Xin chào");
    fireEvent.click(readSource());
    act(() => audios[audios.length - 1].onerror?.());
    expect(spoken).toHaveLength(0);
    expect(await screen.findByText(/chưa cài giọng đọc cho ngôn ngữ này/i)).toBeInTheDocument();
  });

  it("trình duyệt không hỗ trợ speechSynthesis -> báo lỗi thay vì im lặng", async () => {
    render(<Harness sourceLang="de" />);
    await translate("Guten Morgen", "Chào buổi sáng");
    fireEvent.click(readSource());
    act(() => audios[audios.length - 1].onerror?.());
    expect(await screen.findByText(/Không phát được âm thanh/i)).toBeInTheDocument();
  });
});

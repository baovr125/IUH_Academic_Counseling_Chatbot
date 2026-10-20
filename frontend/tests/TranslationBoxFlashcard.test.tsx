import React, { useState } from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const streamMock = vi.fn();
const tr = vi.hoisted(() => ({ extractFlashcard: vi.fn(), translateText: vi.fn() }));
const svc = vi.hoisted(() => ({ fetchBackendDecks: vi.fn(), createBackendDeck: vi.fn(), saveCardFromTranslation: vi.fn() }));

vi.mock("../src/services/translationService", () => ({
  streamTranslation: (...args: unknown[]) => streamMock(...args),
  extractFlashcard: tr.extractFlashcard,
  translateText: tr.translateText
}));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "user-1" } }) }));
vi.mock("../src/components/translation/FloatingMenu", () => ({ FloatingMenu: () => null }));
vi.mock("../src/components/translation/WordAnalysisPopup", () => ({ WordAnalysisPopup: () => null }));
vi.mock("../src/hooks/useWordAnalysis", () => ({
  useWordAnalysis: () => ({ analyze: vi.fn(), reset: vi.fn(), state: null, close: vi.fn() })
}));

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

/** Callback của lần streamTranslation gần nhất (thứ tự khớp translationService). */
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

const openSave = () => fireEvent.click(screen.getByRole("button", { name: /Lưu Flashcard/ }));

beforeEach(() => {
  streamMock.mockReset();
  streamMock.mockResolvedValue(undefined);
  Object.values(tr).forEach((m) => m.mockReset());
  Object.values(svc).forEach((m) => m.mockReset());
  tr.extractFlashcard.mockResolvedValue({ ok: true, data: {} });
  svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [] });
  localStorage.clear();
});

describe("TranslationBox -> Lưu Flashcard: xác định ngôn ngữ thẻ", () => {
  it("nguồn chọn tay = Đức: Guten Morgen -> Chào buổi sáng vào bộ sưu tập tiếng Đức", async () => {
    render(<Harness sourceLang="de" />);
    await translate("Guten Morgen", "Chào buổi sáng");
    openSave();
    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Đức");
    const dialog = within(screen.getByRole("dialog"));
    expect(dialog.getByDisplayValue("Guten Morgen")).toBeInTheDocument();
    expect(dialog.getByDisplayValue("Chào buổi sáng")).toBeInTheDocument();
  });

  it("nguồn tự nhận diện: dùng ngôn ngữ vừa nhận diện cho đúng văn bản này", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Guten Morgen", "Chào buổi sáng", { lang: "de" });
    openSave();
    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Đức");
  });

  it("nguồn tự nhận diện nhưng không có kết quả: hỏi người dùng, không đoán", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Bonjour", "Xin chào");
    openSave();
    expect(await screen.findByRole("group", { name: /Chọn ngôn ngữ nguồn/ })).toBeInTheDocument();
    expect(screen.queryByTestId("draft-language")).not.toBeInTheDocument();
  });

  it("nhận diện chưa chắc (uncertain): hỏi người dùng", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Bonjour", "Xin chào", { lang: "fr", status: "uncertain" });
    openSave();
    expect(await screen.findByText(/chưa chắc chắn về ngôn ngữ/i)).toBeInTheDocument();
  });

  it("nhãn nhận diện cũ của văn bản trước KHÔNG được dùng cho văn bản mới", async () => {
    render(<Harness sourceLang="auto" />);
    await translate("Guten Morgen", "Chào buổi sáng", { lang: "de" });
    streamMock.mockClear();
    // Đổi sang văn bản khác; lượt dịch mới không trả kết quả nhận diện.
    await translate("Good morning", "Chào buổi sáng");
    openSave();
    expect(await screen.findByRole("group", { name: /Chọn ngôn ngữ nguồn/ })).toBeInTheDocument();
    expect(screen.queryByTestId("draft-language")).not.toBeInTheDocument();
  });

  it("Việt -> Nhật: thẻ thuộc bộ sưu tập tiếng Nhật", async () => {
    render(<Harness sourceLang="vi" targetLang="ja" />);
    await translate("Xin chào", "こんにちは");
    openSave();
    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Nhật");
    expect(within(screen.getByRole("dialog")).getByDisplayValue("こんにちは")).toBeInTheDocument();
  });

  it("Anh -> Đức (hai ngoại ngữ): hỏi muốn học ngôn ngữ nào", async () => {
    render(<Harness sourceLang="en" targetLang="de" />);
    await translate("Good morning", "Guten Morgen");
    openSave();
    expect(await screen.findByRole("radiogroup", { name: /Chọn ngôn ngữ muốn học/ })).toBeInTheDocument();
  });
});

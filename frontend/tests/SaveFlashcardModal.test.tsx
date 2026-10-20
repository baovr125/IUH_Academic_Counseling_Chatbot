import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { DraftInput } from "../src/services/flashcardDraft";

const svc = vi.hoisted(() => ({
  fetchBackendDecks: vi.fn(),
  createBackendDeck: vi.fn(),
  saveCardFromTranslation: vi.fn()
}));
const tr = vi.hoisted(() => ({ extractFlashcard: vi.fn(), translateText: vi.fn() }));

vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/services/translationService", async (orig) => ({ ...(await orig<object>()), ...tr }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "user-1" } }) }));

import { SaveFlashcardModal } from "../src/components/translation/SaveFlashcardModal";

const input = (over: Partial<DraftInput> = {}): DraftInput => ({
  sourceLang: "de",
  targetLang: "vi",
  sourceText: "Guten Morgen",
  translatedText: "Chào buổi sáng",
  detection: null,
  selection: null,
  ...over
});

const saved = (lang = "de", over: Record<string, unknown> = {}) => ({
  ok: true,
  data: {
    created: true,
    card: { id: "c1", term: "Guten Morgen", definition: "Chào buổi sáng", lang_code: lang },
    deck: { id: "d1", title: "Từ vựng Tiếng Đức", lang_code: lang },
    ...over
  }
});

function renderModal(inp: DraftInput | null, extra: Record<string, unknown> = {}) {
  const onClose = vi.fn();
  const onSaved = vi.fn();
  render(<SaveFlashcardModal isOpen onClose={onClose} input={inp} onSaved={onSaved} {...extra} />);
  return { onClose, onSaved };
}

const clickSave = () => fireEvent.click(screen.getByRole("button", { name: /Lưu vào sổ thẻ/i }));
const lastSave = () => svc.saveCardFromTranslation.mock.calls[svc.saveCardFromTranslation.mock.calls.length - 1][0];

beforeEach(() => {
  Object.values(svc).forEach((m) => m.mockReset());
  Object.values(tr).forEach((m) => m.mockReset());
  localStorage.clear();
  svc.fetchBackendDecks.mockResolvedValue({ ok: true, data: [] });
  tr.extractFlashcard.mockResolvedValue({ ok: true, data: {} });
  tr.translateText.mockResolvedValue({ ok: true, data: { translatedText: "Chào buổi sáng" } });
});

describe("SaveFlashcardModal — lưu từ Realtime Translation", () => {
  it("Guten Morgen -> Chào buổi sáng: lưu vào bộ sưu tập tiếng Đức, nguồn DE, đích VI", async () => {
    svc.saveCardFromTranslation.mockResolvedValue(saved());
    const { onSaved, onClose } = renderModal(input());

    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Đức");
    expect(screen.getByDisplayValue("Guten Morgen")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Chào buổi sáng")).toBeInTheDocument();
    await waitFor(() => expect(svc.fetchBackendDecks).toHaveBeenCalledWith("de")); // chỉ tải sổ cùng ngôn ngữ

    clickSave();
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: "de", term: "Guten Morgen", translation: "Chào buổi sáng", onDuplicate: "reject" });
    expect(lastSave().deckId).toBeUndefined(); // sổ mặc định
    expect(lastSave().clientRequestId).toMatch(/^fc-/);
    expect(onSaved.mock.calls[0][0]).toMatchObject({ langCode: "de", deckTitle: "Từ vựng Tiếng Đức", pending: false, created: true });
    expect(onClose).toHaveBeenCalled();
  });

  it.each([
    ["en", "Good morning"], ["zh", "早上好"], ["ja", "おはよう"], ["ko", "좋은 아침"],
    ["fr", "Bonjour"], ["es", "Buenos días"], ["ru", "Доброе утро"], ["th", "สวัสดีตอนเช้า"]
  ])("ngôn ngữ nguồn %s được gửi đúng mã ISO", async (lang, text) => {
    svc.saveCardFromTranslation.mockResolvedValue(saved(lang));
    renderModal(input({ sourceLang: lang, sourceText: text }));
    await screen.findByTestId("draft-language");
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: lang, term: text });
  });

  it("nguồn 'auto' chưa nhận diện: bắt buộc hỏi, KHÔNG gọi API khi chưa chọn", async () => {
    svc.saveCardFromTranslation.mockResolvedValue(saved("fr"));
    renderModal(input({ sourceLang: "auto", sourceText: "Bonjour", detection: { lang: null, status: "uncertain", candidates: ["fr", "es"] } }));

    expect(await screen.findByText(/chưa chắc chắn về ngôn ngữ/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Lưu vào sổ thẻ/i })).not.toBeInTheDocument();
    expect(svc.saveCardFromTranslation).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /Tiếng Pháp/ }));
    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Pháp");
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave().sourceLang).toBe("fr");
  });

  it("auto + đã nhận diện chắc chắn: dùng ngôn ngữ nhận diện, gửi kèm thông tin nhận diện", async () => {
    svc.saveCardFromTranslation.mockResolvedValue(saved());
    renderModal(input({ sourceLang: "auto", detection: { lang: "de", status: "detected", engine: "fusion", confidence: 0.98 } }));
    await screen.findByTestId("draft-language");
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: "de", detection: { status: "detected", engine: "fusion", confidence: 0.98 } });
  });

  it("Việt -> ngoại ngữ: thẻ thuộc ngôn ngữ đích, mặt trước là bản dịch", async () => {
    svc.saveCardFromTranslation.mockResolvedValue(saved("ja"));
    renderModal(input({ sourceLang: "vi", targetLang: "ja", sourceText: "Xin chào", translatedText: "こんにちは" }));
    expect(await screen.findByTestId("draft-language")).toHaveTextContent("Tiếng Nhật");
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: "ja", term: "こんにちは", translation: "Xin chào" });
  });

  it("ngoại ngữ -> ngoại ngữ: hỏi ngôn ngữ muốn học rồi tự dịch nghĩa tiếng Việt", async () => {
    svc.saveCardFromTranslation.mockResolvedValue(saved("de"));
    tr.translateText.mockResolvedValue({ ok: true, data: { translatedText: "Chào buổi sáng" } });
    renderModal(input({ sourceLang: "en", targetLang: "de", sourceText: "Good morning", translatedText: "Guten Morgen" }));

    expect(await screen.findByRole("radiogroup", { name: /Chọn ngôn ngữ muốn học/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: /Tiếng Đức/ }));

    expect(await screen.findByDisplayValue("Chào buổi sáng")).toBeInTheDocument(); // nghĩa Việt được dịch tự động
    expect(tr.translateText).toHaveBeenCalledWith(expect.objectContaining({ sourceText: "Good morning", sourceLang: "en", targetLang: "vi" }));
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: "de", term: "Guten Morgen", translation: "Chào buổi sáng" });
  });

  it("bôi đen một từ: AI điền nghĩa tiếng Việt + phiên âm theo ngôn ngữ", async () => {
    tr.extractFlashcard.mockResolvedValue({ ok: true, data: { meaning: "buổi sáng", phonetic: "/ˈmɔʁɡn̩/", part_of_speech: "noun" } });
    svc.saveCardFromTranslation.mockResolvedValue(saved());
    renderModal(input({ selection: { text: "Morgen", side: "source", context: "Guten Morgen, Anna!" } }));

    expect(await screen.findByDisplayValue("buổi sáng")).toBeInTheDocument();
    expect(tr.extractFlashcard).toHaveBeenCalledWith("Morgen", "Guten Morgen, Anna!", "", "de", expect.anything());
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave()).toMatchObject({ sourceLang: "de", term: "Morgen", translation: "buổi sáng", phonetic: "/ˈmɔʁɡn̩/", example: "Guten Morgen, Anna!" });
  });

  it("bôi đen từ tiếng Việt: không cho lưu, giải thích lý do", async () => {
    renderModal(input({ selection: { text: "buổi sáng", side: "target" } }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/bôi đen từ tiếng Việt/i);
    expect(screen.queryByRole("button", { name: /Lưu vào sổ thẻ/i })).not.toBeInTheDocument();
  });

  it("trùng thẻ: báo rõ, mặc định không ghi đè; 'Cập nhật nghĩa mới' gửi on_duplicate=update", async () => {
    svc.saveCardFromTranslation
      .mockResolvedValueOnce({
        ok: false,
        error: {
          code: "DUPLICATE_CARD", message: "dup",
          data: { card: { id: "c0", term: "Guten Morgen", definition: "Chào" }, deck: { id: "d1", title: "Từ vựng Tiếng Đức" } }
        }
      })
      .mockResolvedValueOnce(saved("de", { created: false, updated: true }));
    const { onSaved } = renderModal(input());
    await screen.findByTestId("draft-language");
    clickSave();

    const alert = await screen.findByText(/đã có trong sổ/i);
    expect(alert.closest("[role=alert]")).toHaveTextContent("Từ vựng Tiếng Đức");
    expect(alert.closest("[role=alert]")).toHaveTextContent("Chào");
    expect(onSaved).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /Cập nhật nghĩa mới/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(lastSave().onDuplicate).toBe("update");
    expect(onSaved.mock.calls[0][0]).toMatchObject({ created: false });
  });

  it("lỗi nghiệp vụ từ máy chủ được hiển thị, modal giữ nguyên và KHÔNG ghi LocalStorage", async () => {
    svc.saveCardFromTranslation.mockResolvedValue({ ok: false, error: { code: "LANG_MISMATCH", message: "x" } });
    const { onSaved, onClose } = renderModal(input());
    await screen.findByTestId("draft-language");
    clickSave();
    expect(await screen.findByRole("alert")).toHaveTextContent(/thuộc ngôn ngữ khác/i);
    expect(onSaved).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(Object.keys(localStorage)).toHaveLength(0);
  });

  it("mất kết nối máy chủ: lưu tạm LocalStorage (đánh dấu pendingSync) và báo chưa đồng bộ", async () => {
    svc.saveCardFromTranslation.mockResolvedValue({ ok: false, error: { message: "Failed to fetch", network: true } });
    const { onSaved, onClose } = renderModal(input());
    await screen.findByTestId("draft-language");
    clickSave();
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(onSaved.mock.calls[0][0]).toMatchObject({ pending: true, langCode: "de" });
    expect(onClose).toHaveBeenCalled();
    const key = Object.keys(localStorage).find((k) => k.startsWith("iuh_portal_ai_decks_"))!;
    const decks = JSON.parse(localStorage.getItem(key)!);
    expect(decks[0]).toMatchObject({ langCode: "de" });
    expect(decks[0].cards[0]).toMatchObject({ term: "Guten Morgen", definition: "Chào buổi sáng", pendingSync: true });
  });

  it("chỉ liệt kê sổ cùng ngôn ngữ đã xác nhận và chuyển deck_id đã chọn", async () => {
    svc.fetchBackendDecks.mockResolvedValue({
      ok: true,
      data: [
        { id: "d-ok", title: "Bài học 1", lang_code: "de", lang_confirmed: true, cards_count: 3 },
        { id: "d-legacy", title: "Sổ cũ", lang_code: "de", lang_confirmed: false }
      ]
    });
    svc.saveCardFromTranslation.mockResolvedValue(saved());
    renderModal(input());
    expect(await screen.findByRole("option", { name: /Bài học 1/ })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /Sổ cũ/ })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Lưu vào sổ/i), { target: { value: "d-ok" } });
    clickSave();
    await waitFor(() => expect(svc.saveCardFromTranslation).toHaveBeenCalled());
    expect(lastSave().deckId).toBe("d-ok");
  });

  it("không cho lưu khi thiếu nghĩa", async () => {
    renderModal(input({ translatedText: "Chào" }));
    await screen.findByTestId("draft-language");
    fireEvent.change(screen.getByLabelText(/Nghĩa tiếng Việt/i), { target: { value: "  " } });
    expect(screen.getByRole("button", { name: /Lưu vào sổ thẻ/i })).toBeDisabled();
  });
});

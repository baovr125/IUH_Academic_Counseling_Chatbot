import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const svc = vi.hoisted(() => ({
  fetchVocabQuota: vi.fn(),
  generateVocabulary: vi.fn(),
  generateVocabularyFromImage: vi.fn(),
  commitGeneratedVocabulary: vi.fn()
}));

vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));

import { GenerateVocabModal } from "../src/components/flashcards/modals/GenerateVocabModal";
import type { BackendDeck } from "../src/services/flashcardService";

const quota = { tier: "student", tier_label: "SINH VIÊN IUH", limit: 10, used: 0, remaining: 10, resets_at: "" };
const item = (term: string, ipa: string) => ({
  temp_id: "g1", term, part_of_speech: "noun", ipa, definition: "nghĩa", example: `${term} Beispiel`, example_translation: "ví dụ",
  level: "B1", warnings: [] as string[], verified: true
});
const generated = (lang: string, term: string, ipa: string, warnings: string[] = []) => ({
  ok: true,
  data: { generation_id: "g", mode: "topic", lang_code: lang, topic: "Reisen", level: "B1", requested: 1, returned: 1,
          items: [{ ...item(term, ipa), warnings }], dropped: [], providers: ["x"], latency_ms: 1, quota }
});
const deckOf = (lang: string): BackendDeck => ({ id: "d1", title: `Sổ ${lang}`, lang_code: lang, lang_confirmed: true, cards_count: 3 });

function renderModal(props: Partial<React.ComponentProps<typeof GenerateVocabModal>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const ui = (p: Partial<React.ComponentProps<typeof GenerateVocabModal>>) => (
    <QueryClientProvider client={qc}>
      <GenerateVocabModal isOpen onClose={vi.fn()} onStartLearning={vi.fn()} {...p} />
    </QueryClientProvider>
  );
  const view = render(ui(props));
  return { rerender: (p: Partial<React.ComponentProps<typeof GenerateVocabModal>>) => view.rerender(ui(p)) };
}

const type = (text: string) => fireEvent.change(screen.getByPlaceholderText(/Nhập chủ đề/i), { target: { value: text } });
const generate = () => fireEvent.click(screen.getByRole("button", { name: /Tạo từ vựng với AI/i }));
const openAdvanced = () => fireEvent.click(screen.getByRole("button", { name: /Tùy chọn thêm/ }));

beforeEach(() => {
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchVocabQuota.mockResolvedValue({ ok: true, data: quota });
});

describe("GenerateVocabModal — nhiều ngôn ngữ", () => {
  it("hiển thị rõ ngôn ngữ sẽ được sinh (cờ + tên) và mặc định là tiếng Anh", async () => {
    const { rerender } = renderModal();
    await screen.findByText(/Còn 10\/10/);
    expect(screen.getByTestId("generate-language")).toHaveTextContent("Tiếng Anh");
    rerender({ lang: "de" });
    expect(screen.getByTestId("generate-language")).toHaveTextContent("Tiếng Đức");
    expect(within(screen.getByTestId("generate-language")).getByTestId("lang-flag-de")).toBeInTheDocument();
  });

  it("gửi ngôn ngữ lên máy chủ khi sinh theo chủ đề", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("de", "der Hund", "/hʊnt/"));
    renderModal({ lang: "de" });
    await screen.findByText(/Còn 10\/10/);
    type("Reisen");
    generate();
    await screen.findByDisplayValue("der Hund");
    expect(svc.generateVocabulary.mock.calls[0][0]).toMatchObject({ mode: "topic", topic: "Reisen", langCode: "de" });
  });

  it("sổ đích quyết định ngôn ngữ, bất kể prop lang", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("ja", "食べる", "たべる · taberu"));
    renderModal({ lang: "en", targetDeck: deckOf("ja") });
    await screen.findByText(/Còn 10\/10/);
    expect(screen.getByTestId("generate-language")).toHaveTextContent("Tiếng Nhật");
    type("Du lịch");
    generate();
    await screen.findByDisplayValue("食べる");
    expect(svc.generateVocabulary.mock.calls[0][0]).toMatchObject({ langCode: "ja", deckId: "d1" });
  });

  it("sinh từ ảnh cũng gửi ngôn ngữ", async () => {
    svc.generateVocabularyFromImage.mockResolvedValue(generated("fr", "le chat", "/ʃa/"));
    renderModal({ lang: "fr" });
    await screen.findByText(/Còn 10\/10/);
    fireEvent.click(screen.getByRole("tab", { name: "Hình ảnh" }));
    const file = new File(["x"], "a.png", { type: "image/png" });
    fireEvent.change(document.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [file] } });
    generate();
    await screen.findByDisplayValue("le chat");
    expect(svc.generateVocabularyFromImage.mock.calls[0][1]).toMatchObject({ langCode: "fr" });
  });

  it("lưu sổ mới: sổ và nguồn cùng mang ngôn ngữ của lượt sinh", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("es", "el libro", "/el ˈliβɾo/"));
    svc.commitGeneratedVocabulary.mockResolvedValue({ ok: true, data: { deck: { id: "n1", title: "Reisen (B1)" }, inserted: 1, skipped_duplicates: 0, total_in_file: 1, cards: [] } });
    renderModal({ lang: "es" });
    await screen.findByText(/Còn 10\/10/);
    type("Reisen");
    generate();
    await screen.findByDisplayValue("el libro");
    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    await screen.findByText(/Đã lưu bộ từ vựng/);
    const payload = svc.commitGeneratedVocabulary.mock.calls[0][0];
    expect(payload.deck).toMatchObject({ langCode: "es" });
    expect(payload.source).toMatchObject({ mode: "topic", langCode: "es" });
  });

  it("thêm vào sổ có sẵn: không tạo sổ mới, nguồn mang ngôn ngữ của sổ", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("de", "die Katze", "/ˈkatsə/"));
    svc.commitGeneratedVocabulary.mockResolvedValue({ ok: true, data: { deck: { id: "d1", title: "Sổ de" }, inserted: 1, skipped_duplicates: 0, total_in_file: 1, cards: [] } });
    renderModal({ targetDeck: deckOf("de") });
    await screen.findByText(/Còn 10\/10/);
    type("Tiere");
    generate();
    await screen.findByDisplayValue("die Katze");
    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    await screen.findByText(/Đã lưu bộ từ vựng/);
    const payload = svc.commitGeneratedVocabulary.mock.calls[0][0];
    expect(payload.deckId).toBe("d1");
    expect(payload.deck).toBeUndefined();
    expect(payload.source.langCode).toBe("de");
  });

  it("lỗi 409 lệch ngôn ngữ của máy chủ được hiện nguyên văn và quay về bước nhập", async () => {
    svc.generateVocabulary.mockResolvedValue({ ok: false, error: { code: "LANG_MISMATCH", message: "Sổ này là sổ Tiếng Anh, không thể thêm từ vựng Tiếng Đức." } });
    renderModal({ lang: "de" });
    await screen.findByText(/Còn 10\/10/);
    type("Reisen");
    generate();
    expect(await screen.findByRole("alert")).toHaveTextContent("Sổ này là sổ Tiếng Anh");
    expect(screen.getByPlaceholderText(/Nhập chủ đề/i)).toBeInTheDocument();
  });

  it("chữ hướng dẫn nêu đúng ngôn ngữ (không còn cố định tiếng Anh)", async () => {
    renderModal({ lang: "ko" });
    await screen.findByText(/Còn 10\/10/);
    expect(screen.getByPlaceholderText(/đoạn văn tiếng Hàn/)).toBeInTheDocument();
    expect(screen.getByText(/dán một đoạn văn tiếng Hàn để AI trích xuất/)).toBeInTheDocument();
    generate();
    expect(await screen.findByRole("alert")).toHaveTextContent("tiếng Hàn");
  });

  it("IELTS/TOEIC chỉ có khi sinh tiếng Anh", async () => {
    const { rerender } = renderModal({ lang: "en" });
    await screen.findByText(/Còn 10\/10/);
    openAdvanced();
    const options = () => within(screen.getByLabelText(/Mục đích học/)).getAllByRole("option").map((o) => o.textContent);
    expect(options()).toEqual(expect.arrayContaining(["IELTS", "TOEIC", "Học thuật"]));
    rerender({ lang: "zh" });  // phần tùy chọn thêm vẫn đang mở
    expect(options()).not.toContain("IELTS");
    expect(options()).not.toContain("TOEIC");
    expect(options()).toContain("Học thuật");
  });

  it.each([
    ["en", "Phiên âm IPA", "/IPA/"],
    ["de", "Phiên âm IPA", "/IPA/"],
    ["zh", "Phiên âm pinyin", "pinyin"],
    ["ja", "Cách đọc (kana · romaji)", "かな · romaji"],
    ["ko", "Phiên âm romaja", "romaja"],
    ["th", "Phiên âm (RTGS)", "romanization"]
  ])("ô phiên âm của %s dùng nhãn %s", async (lang, label, placeholder) => {
    svc.generateVocabulary.mockResolvedValue(generated(lang, "từ", "x"));
    renderModal({ lang });
    await screen.findByText(/Còn 10\/10/);
    type("Chủ đề");
    generate();
    const field = await screen.findByLabelText(label);
    expect(field).toHaveAttribute("placeholder", placeholder);
  });

  it("từ và câu ví dụ được đánh dấu đúng ngôn ngữ (trình đọc màn hình đọc đúng giọng)", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("de", "der Hund", "/hʊnt/"));
    renderModal({ lang: "de" });
    await screen.findByText(/Còn 10\/10/);
    type("Reisen");
    generate();
    expect(await screen.findByLabelText("Từ vựng")).toHaveAttribute("lang", "de");
    expect(screen.getByLabelText("Câu ví dụ")).toHaveAttribute("lang", "de");
  });

  it("cảnh báo phiên âm không còn nói riêng về IPA", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("zh", "和平", "", ["ipa_invalid"]));
    renderModal({ lang: "zh" });
    await screen.findByText(/Còn 10\/10/);
    type("Chủ đề");
    generate();
    expect(await screen.findByText(/Phiên âm chưa hợp lệ/)).toBeInTheDocument();
  });

  it("đổi ngôn ngữ thì hộp được đặt lại: không giữ kết quả của ngôn ngữ trước", async () => {
    svc.generateVocabulary.mockResolvedValue(generated("de", "der Hund", "/hʊnt/"));
    const { rerender } = renderModal({ lang: "de" });
    await screen.findByText(/Còn 10\/10/);
    type("Reisen");
    generate();
    await screen.findByDisplayValue("der Hund");
    rerender({ lang: "fr" });
    expect(screen.queryByDisplayValue("der Hund")).toBeNull();
    expect(screen.getByPlaceholderText(/Nhập chủ đề/i)).toBeInTheDocument();
  });

  it("lang lạ hoặc tiếng Việt (ngôn ngữ giải nghĩa) rơi về tiếng Anh", async () => {
    const { rerender } = renderModal({ lang: "vi" });
    await screen.findByText(/Còn 10\/10/);
    expect(screen.getByTestId("generate-language")).toHaveTextContent("Tiếng Anh");
    rerender({ lang: "xx" });
    expect(screen.getByTestId("generate-language")).toHaveTextContent("Tiếng Anh");
  });
});

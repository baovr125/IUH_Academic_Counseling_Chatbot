import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const svc = vi.hoisted(() => ({
  fetchVocabQuota: vi.fn(),
  generateVocabulary: vi.fn(),
  generateVocabularyFromImage: vi.fn(),
  commitGeneratedVocabulary: vi.fn()
}));

vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));

import { GenerateVocabModal, detectInputMode } from "../src/components/flashcards/modals/GenerateVocabModal";

const quota = (used: number, limit = 3) => ({ tier: "normal", tier_label: "THƯỜNG", limit, used, remaining: limit - used, resets_at: "" });

const item = (n: number, extra: Record<string, unknown> = {}) => ({
  temp_id: `g${n}`, term: `word${n}`, part_of_speech: "noun", ipa: "/ˈwɜːd/", definition: `nghĩa ${n}`,
  example: `The word${n} is used here.`, example_translation: `Dịch ${n}`, level: "B1", warnings: [], verified: true, ...extra
});

const generated = (items: ReturnType<typeof item>[], extra: Record<string, unknown> = {}) => ({
  ok: true,
  data: { generation_id: "g", mode: "topic", topic: "Environment", level: "B1", requested: items.length, returned: items.length,
          items, dropped: [], providers: ["x"], latency_ms: 1, quota: quota(1), ...extra }
});

function renderModal(props: Partial<React.ComponentProps<typeof GenerateVocabModal>> = {}) {
  const onClose = vi.fn();
  const onStartLearning = vi.fn();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const invalidate = vi.spyOn(qc, "invalidateQueries");
  render(
    <QueryClientProvider client={qc}>
      <GenerateVocabModal isOpen onClose={onClose} onStartLearning={onStartLearning} {...props} />
    </QueryClientProvider>
  );
  return { onClose, onStartLearning, invalidate };
}

const typeInput = (text: string) =>
  fireEvent.change(screen.getByPlaceholderText(/Nhập chủ đề/i), { target: { value: text } });
const clickGenerate = () => fireEvent.click(screen.getByRole("button", { name: /Tạo từ vựng với AI/i }));

beforeEach(() => {
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchVocabQuota.mockResolvedValue({ ok: true, data: quota(0) });
});

describe("detectInputMode", () => {
  it.each([
    ["Environment", "topic"],
    ["Environmental Protection and climate", "topic"],
    ["one two three four five six seven eight nine", "text"],
    ["x".repeat(101), "text"],
    ["  Travel  ", "topic"]
  ])("%s -> %s", (input, expected) => expect(detectInputMode(input)).toBe(expected));
});

describe("GenerateVocabModal", () => {
  it("shows the quota badges", async () => {
    svc.fetchVocabQuota.mockResolvedValue({ ok: true, data: quota(1) });
    renderModal();
    expect(await screen.findByText(/Còn 2\/3 lượt hôm nay/i)).toBeInTheDocument();
    expect(screen.getByText("THƯỜNG")).toBeInTheDocument();
    expect(screen.getByText(/Đã dùng 1/i)).toBeInTheDocument();
  });

  it("blocks generation when the quota is exhausted", async () => {
    svc.fetchVocabQuota.mockResolvedValue({ ok: true, data: quota(3) });
    renderModal();
    const button = await screen.findByRole("button", { name: /Đã hết lượt hôm nay/i });
    expect(button).toBeDisabled();
    expect(svc.generateVocabulary).not.toHaveBeenCalled();
  });

  it("validates the input before calling the API", async () => {
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    clickGenerate();
    expect(await screen.findByRole("alert")).toHaveTextContent(/nhập chủ đề/i);
    typeInput("one two three four five six seven eight nine ten");
    typeInput("one two three four five six seven eight nine");
    expect(svc.generateVocabulary).not.toHaveBeenCalled();
  });

  it("topic flow: generate -> edit -> delete -> save -> start learning", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1), item(2, { warnings: ["no_example_translation"], verified: false }), item(3)]));
    svc.commitGeneratedVocabulary.mockResolvedValue({ ok: true, data: { deck: { id: "d1", title: "Environment (B1)" }, inserted: 2, skipped_duplicates: 0, total_in_file: 2, cards: [] } });
    const { onStartLearning, invalidate } = renderModal();
    await screen.findByText(/Còn 3\/3/);

    typeInput("Environment");
    expect(screen.getByText(/Đang nhận diện: chủ đề/)).toBeInTheDocument();
    clickGenerate();

    await screen.findByDisplayValue("word1");
    expect(svc.generateVocabulary.mock.calls[0][0]).toMatchObject({ mode: "topic", topic: "Environment", level: "B1", count: 20 });
    expect(screen.getByText(/Chưa có bản dịch câu ví dụ/)).toBeInTheDocument();
    expect(screen.getByText(/Còn 2\/3 lượt hôm nay/)).toBeInTheDocument(); // hạn mức cập nhật từ phản hồi

    fireEvent.change(screen.getAllByLabelText("Nghĩa tiếng Việt")[0], { target: { value: "nghĩa đã sửa" } });
    fireEvent.click(screen.getByLabelText("Xóa từ word3"));
    expect(screen.queryByDisplayValue("word3")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Giữ từ word2")); // bỏ chọn word2
    expect(screen.getByRole("button", { name: /Lưu 1 từ/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    await screen.findByText(/Đã lưu bộ từ vựng/);

    const payload = svc.commitGeneratedVocabulary.mock.calls[0][0];
    expect(payload.deck).toMatchObject({ title: "Environment (B1)", langCode: "en" });
    expect(payload.deckId).toBeUndefined();
    expect(payload.cards).toHaveLength(1);
    expect(payload.cards[0]).toMatchObject({ term: "word1", definition: "nghĩa đã sửa", partOfSpeech: "noun", exampleTranslation: "Dịch 1", level: "B1" });
    expect(payload.source).toEqual({ mode: "topic", topic: "Environment", level: "B1", langCode: "en" });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["flashcard_decks"] });

    fireEvent.click(screen.getByRole("button", { name: /Bắt đầu học ngay/ }));
    expect(onStartLearning).toHaveBeenCalledTimes(1);
  });

  it("text mode is chosen automatically for long input", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1)], { mode: "text", topic: null }));
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    const passage = "Many companies are adopting renewable energy to reduce their carbon footprint today.";
    typeInput(passage);
    expect(screen.getByText(/Đang nhận diện: đoạn văn/)).toBeInTheDocument();
    clickGenerate();
    await screen.findByDisplayValue("word1");
    expect(svc.generateVocabulary.mock.calls[0][0]).toMatchObject({ mode: "text", text: passage });
    expect(screen.getByDisplayValue("Từ vựng từ đoạn văn")).toBeInTheDocument();
  });

  it("shows the backend error and returns to the form without losing the input", async () => {
    svc.generateVocabulary.mockResolvedValue({ ok: false, error: { message: "Dịch vụ AI tạm thời không khả dụng.", code: "LLM_UNAVAILABLE" } });
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    typeInput("Environment");
    clickGenerate();
    expect(await screen.findByRole("alert")).toHaveTextContent(/tạm thời không khả dụng/);
    expect(screen.getByPlaceholderText(/Nhập chủ đề/i)).toHaveValue("Environment");
  });

  it("'add more' sends the current terms as exclusions and appends only new, uniquely keyed items", async () => {
    svc.generateVocabulary
      .mockResolvedValueOnce(generated([item(1), item(2)]))
      .mockResolvedValueOnce(generated([item(2), item(3), item(4)], { quota: quota(2) })); // word2 trùng
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    typeInput("Environment");
    clickGenerate();
    await screen.findByDisplayValue("word1");

    fireEvent.click(screen.getByRole("button", { name: /Thêm 10 từ nữa/ }));
    await screen.findByDisplayValue("word4");
    expect(svc.generateVocabulary.mock.calls[1][0]).toMatchObject({ count: 10, excludeTerms: ["word1", "word2"] });
    expect(screen.getAllByLabelText("Từ vựng")).toHaveLength(4); // 1,2 + 3,4 (không nhân đôi word2)
    expect(screen.getByText(/Còn 1\/3 lượt hôm nay/)).toBeInTheDocument();
  });

  it("adding to an existing deck skips the title field and sends deckId", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1)]));
    svc.commitGeneratedVocabulary.mockResolvedValue({ ok: true, data: { deck: { id: "d7", title: "Có sẵn" }, inserted: 1, skipped_duplicates: 0, total_in_file: 1, cards: [] } });
    renderModal({ targetDeck: { id: "d7", title: "Có sẵn" } as any });
    await screen.findByText(/Thêm vào sổ: Có sẵn/);
    typeInput("Environment");
    clickGenerate();
    await screen.findByDisplayValue("word1");
    expect(svc.generateVocabulary.mock.calls[0][0]).toMatchObject({ deckId: "d7" });
    expect(screen.queryByText(/Tên sổ thẻ mới/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    await screen.findByText(/Đã lưu bộ từ vựng/);
    expect(svc.commitGeneratedVocabulary.mock.calls[0][0]).toMatchObject({ deckId: "d7", deck: undefined });
  });

  it("a failed save keeps the review list and retries with the same request id", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1)]));
    svc.commitGeneratedVocabulary
      .mockResolvedValueOnce({ ok: false, error: { message: "Không thể lưu do lỗi cơ sở dữ liệu.", code: "503" } })
      .mockResolvedValueOnce({ ok: true, data: { deck: { id: "d1", title: "T" }, inserted: 1, skipped_duplicates: 0, total_in_file: 1, cards: [] } });
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    typeInput("Environment");
    clickGenerate();
    await screen.findByDisplayValue("word1");

    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/lỗi cơ sở dữ liệu/);
    expect(screen.getByDisplayValue("word1")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    await screen.findByText(/Đã lưu bộ từ vựng/);
    const [first, second] = svc.commitGeneratedVocabulary.mock.calls.map((c) => c[0].clientRequestId);
    expect(first).toBe(second); // idempotent: thử lại không tạo deck trùng
  });

  it("refuses to save when every word is unchecked or the deck name is empty", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1)]));
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    typeInput("Environment");
    clickGenerate();
    await screen.findByDisplayValue("word1");
    fireEvent.change(screen.getByDisplayValue("Environment (B1)"), { target: { value: "  " } });
    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/đặt tên/);
    fireEvent.click(screen.getByLabelText("Giữ từ word1"));
    expect(screen.getByRole("button", { name: /Lưu 0 từ/ })).toBeDisabled();
    expect(svc.commitGeneratedVocabulary).not.toHaveBeenCalled();
  });

  it("surfaces the migration warning when extended columns were not saved", async () => {
    svc.generateVocabulary.mockResolvedValue(generated([item(1)]));
    svc.commitGeneratedVocabulary.mockResolvedValue({ ok: true, data: { deck: { id: "d1", title: "T" }, inserted: 1, skipped_duplicates: 2, extended_saved: false, total_in_file: 3, cards: [] } });
    renderModal();
    await screen.findByText(/Còn 3\/3/);
    typeInput("Environment");
    clickGenerate();
    await screen.findByDisplayValue("word1");
    fireEvent.click(screen.getByRole("button", { name: /Lưu 1 từ/ }));
    expect(await screen.findByText(/migration 003/)).toBeInTheDocument();
    expect(screen.getByText(/bỏ qua 2 thẻ trùng/)).toBeInTheDocument();
  });

  it("closes on Hủy and on the backdrop", async () => {
    const { onClose } = renderModal();
    await screen.findByText(/Còn 3\/3/);
    fireEvent.click(screen.getByRole("button", { name: "Hủy" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  describe("image tab", () => {
    const png = (size = 10, type = "image/png") => new File([new Uint8Array(size)], "pic.png", { type });
    const pick = (file: File) => {
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
    };

    it("rejects unsupported types and oversize files client-side", async () => {
      renderModal();
      await screen.findByText(/Còn 3\/3/);
      fireEvent.click(screen.getByRole("tab", { name: "Hình ảnh" }));
      pick(png(10, "image/gif"));
      expect(await screen.findByRole("alert")).toHaveTextContent(/JPG, PNG hoặc WEBP/);
      pick(png(5 * 1024 * 1024 + 1));
      expect(await screen.findByRole("alert")).toHaveTextContent(/5MB/);
      clickGenerate();
      expect(svc.generateVocabularyFromImage).not.toHaveBeenCalled();
    });

    it("requires an image, then sends it and hides 'add more' (không áp dụng cho ảnh)", async () => {
      URL.createObjectURL = vi.fn(() => "blob:preview");
      URL.revokeObjectURL = vi.fn();
      svc.generateVocabularyFromImage.mockResolvedValue(generated([item(1)], { mode: "image", topic: null }));
      renderModal();
      await screen.findByText(/Còn 3\/3/);
      fireEvent.click(screen.getByRole("tab", { name: "Hình ảnh" }));
      clickGenerate();
      expect(await screen.findByRole("alert")).toHaveTextContent(/chọn hoặc dán/);

      const file = png();
      pick(file);
      clickGenerate();
      await screen.findByDisplayValue("word1");
      expect(svc.generateVocabularyFromImage.mock.calls[0][0]).toBe(file);
      expect(screen.queryByRole("button", { name: /Thêm 10 từ nữa/ })).not.toBeInTheDocument();
      expect(screen.getByDisplayValue("Từ vựng từ hình ảnh")).toBeInTheDocument();
    });

    it("accepts an image pasted with Ctrl+V", async () => {
      URL.createObjectURL = vi.fn(() => "blob:preview");
      URL.revokeObjectURL = vi.fn();
      renderModal();
      await screen.findByText(/Còn 3\/3/);
      fireEvent.click(screen.getByRole("tab", { name: "Hình ảnh" }));
      const event = new Event("paste", { bubbles: true, cancelable: true }) as any;
      event.clipboardData = { files: [png()] };
      window.dispatchEvent(event);
      expect(await screen.findByAltText("Ảnh đã chọn")).toBeInTheDocument();
    });
  });
});

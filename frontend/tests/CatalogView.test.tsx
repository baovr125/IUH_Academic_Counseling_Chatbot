import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const svc = vi.hoisted(() => ({ fetchCatalogDecks: vi.fn(), fetchCatalogPreview: vi.fn(), cloneCatalogDeck: vi.fn() }));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));

import { CatalogView, categoryLabel } from "../src/components/flashcards/CatalogView";

const deck = (id: string, over: Record<string, unknown> = {}) => ({
  id, title: `Bộ ${id}`, description: `Mô tả ${id}`, lang_code: "en", category: "food", level: "A2", cards_count: 25, added_deck_id: null, ...over
});

function setup() {
  const onBack = vi.fn();
  const onOpenDeck = vi.fn();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const invalidate = vi.spyOn(qc, "invalidateQueries");
  render(<QueryClientProvider client={qc}><CatalogView onBack={onBack} onOpenDeck={onOpenDeck} /></QueryClientProvider>);
  return { onBack, onOpenDeck, invalidate };
}

beforeEach(() => {
  Object.values(svc).forEach((m) => m.mockReset());
  svc.fetchCatalogDecks.mockResolvedValue({
    ok: true, data: [deck("a", { category: "communication", level: "A1" }), deck("b"), deck("c", { added_deck_id: "mine-1" })]
  });
});

describe("categoryLabel", () => {
  it("maps known codes and falls back", () => {
    expect(categoryLabel("food")).toBe("Ăn uống");
    expect(categoryLabel("going_out")).toBe("Đi chơi & du lịch");
    expect(categoryLabel("custom")).toBe("custom");
    expect(categoryLabel(null)).toBe("Khác");
  });
});

describe("CatalogView", () => {
  it("lists decks with level, count and Vietnamese category labels", async () => {
    setup();
    expect(await screen.findByText("Bộ a")).toBeInTheDocument();
    expect(screen.getAllByText("25 từ")).toHaveLength(3);
    expect(screen.getAllByText("Ăn uống").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Tất cả" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Giao tiếp cơ bản" })).toBeInTheDocument(); // chip suy ra từ dữ liệu
  });

  it("filters by category and level through the API", async () => {
    setup();
    await screen.findByText("Bộ a");
    fireEvent.click(screen.getByRole("button", { name: "Ăn uống" }));
    await waitFor(() => expect(svc.fetchCatalogDecks).toHaveBeenCalledWith({ category: "food", level: undefined, q: undefined }));
    fireEvent.change(screen.getByLabelText("Lọc theo trình độ"), { target: { value: "B1" } });
    await waitFor(() => expect(svc.fetchCatalogDecks).toHaveBeenCalledWith({ category: "food", level: "B1", q: undefined }));
  });

  it("debounces the search box", async () => {
    setup();
    await screen.findByText("Bộ a");
    fireEvent.change(screen.getByLabelText("Tìm bộ từ"), { target: { value: "nhà" } });
    expect(svc.fetchCatalogDecks).not.toHaveBeenCalledWith(expect.objectContaining({ q: "nhà" }));
    await waitFor(() => expect(svc.fetchCatalogDecks).toHaveBeenCalledWith({ category: undefined, level: undefined, q: "nhà" }));
  });

  it("adds a deck to my decks and opens it", async () => {
    svc.cloneCatalogDeck.mockResolvedValue({ ok: true, data: { created: true, inserted: 25, skipped_duplicates: 0, deck: { id: "new-1", title: "Bộ a" } } });
    const { onOpenDeck, invalidate } = setup();
    await screen.findByText("Bộ a");
    fireEvent.click(screen.getAllByRole("button", { name: /Thêm vào sổ của tôi/ })[0]);
    await waitFor(() => expect(onOpenDeck).toHaveBeenCalledWith({ id: "new-1", title: "Bộ a" }));
    expect(svc.cloneCatalogDeck).toHaveBeenCalledWith("a");
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["flashcard_decks"] });
  });

  it("an already-added deck opens the existing deck without cloning again", async () => {
    const { onOpenDeck } = setup();
    await screen.findByText("Bộ c");
    fireEvent.click(screen.getByRole("button", { name: /Đã thêm - Mở sổ/ }));
    expect(svc.cloneCatalogDeck).not.toHaveBeenCalled();
    expect(onOpenDeck).toHaveBeenCalledWith(expect.objectContaining({ id: "mine-1" }));
  });

  it("shows clone errors and does not navigate", async () => {
    svc.cloneCatalogDeck.mockResolvedValue({ ok: false, error: { message: "Bộ từ này chưa có thẻ nào." } });
    const { onOpenDeck } = setup();
    await screen.findByText("Bộ a");
    fireEvent.click(screen.getAllByRole("button", { name: /Thêm vào sổ của tôi/ })[0]);
    expect(await screen.findByRole("alert")).toHaveTextContent(/chưa có thẻ nào/);
    expect(onOpenDeck).not.toHaveBeenCalled();
  });

  it("previews the first cards", async () => {
    svc.fetchCatalogPreview.mockResolvedValue({
      ok: true,
      data: { deck: deck("a"), cards: [{ term: "hello", definition: "xin chào", phonetic: "/həˈloʊ/", part_of_speech: "interjection", example: "Hello!", example_translation: "Chào!" }] }
    });
    setup();
    await screen.findByText("Bộ a");
    fireEvent.click(screen.getAllByRole("button", { name: /Xem trước/ })[0]);
    const dialog = await screen.findByRole("dialog", { name: "Xem trước bộ từ" });
    expect(await within(dialog).findByText("hello")).toBeInTheDocument();
    expect(within(dialog).getByText("xin chào")).toBeInTheDocument();
    expect(within(dialog).getByText("Chào!")).toBeInTheDocument();
    expect(svc.fetchCatalogPreview).toHaveBeenCalledWith("a", 12);
    fireEvent.click(within(dialog).getByLabelText("Đóng"));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("shows the server error (e.g. migration missing) instead of an empty page", async () => {
    svc.fetchCatalogDecks.mockResolvedValue({ ok: false, error: { message: "Thư viện bộ từ chưa sẵn sàng: chưa chạy migration 004" } });
    setup();
    expect(await screen.findByRole("alert")).toHaveTextContent(/migration 004/);
  });

  it("shows an empty state", async () => {
    svc.fetchCatalogDecks.mockResolvedValue({ ok: true, data: [] });
    setup();
    expect(await screen.findByText(/Chưa có bộ từ phù hợp/)).toBeInTheDocument();
  });

  it("goes back", async () => {
    const { onBack } = setup();
    await screen.findByText("Bộ a");
    fireEvent.click(screen.getByRole("button", { name: /Quay lại Sổ thẻ/ }));
    expect(onBack).toHaveBeenCalled();
  });
});

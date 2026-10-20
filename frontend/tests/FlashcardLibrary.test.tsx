import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "user-1" } }) }));

import { DeckDashboard } from "../src/components/flashcards/DeckDashboard";
import { LanguageLibrary } from "../src/components/flashcards/LanguageLibrary";
import { FcMenu } from "../src/components/flashcards/ui";
import type { BackendDeck } from "../src/services/flashcardService";

const deck = (over: Partial<BackendDeck> = {}): BackendDeck => ({
  id: "d1", title: "Từ vựng IELTS", description: "Từ học thuật", lang_code: "en", cards_count: 12, lang_confirmed: true, ...over
});

describe("FcMenu", () => {
  const renderMenu = (items = [
    { key: "a", label: "Mục A", onClick: vi.fn() },
    { key: "b", label: "Mục B", onClick: vi.fn() },
    { key: "c", label: "Xóa", onClick: vi.fn(), tone: "danger" as const }
  ]) => {
    render(
      <div>
        <button>ngoài</button>
        <FcMenu label="Tùy chọn" items={items} />
      </div>
    );
    return items;
  };

  it("đóng khi mới vào; bấm nút mở menu và focus mục đầu tiên", () => {
    renderMenu();
    expect(screen.queryByRole("menu")).toBeNull();
    const trigger = screen.getByRole("button", { name: "Tùy chọn" });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(trigger);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menuitem", { name: "Mục A" })).toHaveFocus();
  });

  it("bấm một mục: gọi hành động đúng và đóng menu", () => {
    const items = renderMenu();
    fireEvent.click(screen.getByRole("button", { name: "Tùy chọn" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Mục B" }));
    expect(items[1].onClick).toHaveBeenCalledTimes(1);
    expect(items[0].onClick).not.toHaveBeenCalled();
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("phím ↓ ↑ Home End di chuyển quay vòng; Esc đóng và trả focus về nút", () => {
    renderMenu();
    const trigger = screen.getByRole("button", { name: "Tùy chọn" });
    fireEvent.click(trigger);
    const menu = screen.getByRole("menu");
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(screen.getByRole("menuitem", { name: "Mục B" })).toHaveFocus();
    fireEvent.keyDown(menu, { key: "End" });
    expect(screen.getByRole("menuitem", { name: "Xóa" })).toHaveFocus();
    fireEvent.keyDown(menu, { key: "ArrowDown" }); // quay vòng về đầu
    expect(screen.getByRole("menuitem", { name: "Mục A" })).toHaveFocus();
    fireEvent.keyDown(menu, { key: "ArrowUp" }); // quay vòng về cuối
    expect(screen.getByRole("menuitem", { name: "Xóa" })).toHaveFocus();
    fireEvent.keyDown(menu, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(trigger).toHaveFocus();
  });

  it("bấm ra ngoài thì đóng", () => {
    renderMenu();
    fireEvent.click(screen.getByRole("button", { name: "Tùy chọn" }));
    fireEvent.mouseDown(screen.getByRole("button", { name: "ngoài" }));
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("mục hidden bị ẩn; không còn mục nào thì không hiện nút", () => {
    const { unmount } = render(<FcMenu label="M1" items={[{ key: "a", label: "A", onClick: vi.fn() }, { key: "b", label: "B", onClick: vi.fn(), hidden: true }]} />);
    fireEvent.click(screen.getByRole("button", { name: "M1" }));
    expect(screen.queryByRole("menuitem", { name: "B" })).toBeNull();
    expect(screen.getAllByRole("menuitem")).toHaveLength(1);
    unmount();
    const { container } = render(<FcMenu label="M2" items={[{ key: "a", label: "A", onClick: vi.fn(), hidden: true }]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("click trong menu không nổi bọt ra phần tử cha (đặt được trong thẻ bấm được)", () => {
    const parent = vi.fn();
    render(
      <div onClick={parent}>
        <FcMenu label="Tùy chọn" items={[{ key: "a", label: "Mục A", onClick: vi.fn() }]} />
      </div>
    );
    fireEvent.click(screen.getByRole("button", { name: "Tùy chọn" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Mục A" }));
    expect(parent).not.toHaveBeenCalled();
  });
});

describe("DeckDashboard — thẻ sổ", () => {
  const handlers = () => ({
    onSelectDeck: vi.fn(), onOpenCreateDeck: vi.fn(), onOpenGenerate: vi.fn(), onOpenCatalog: vi.fn(),
    onOpenEditDeck: vi.fn(), onOpenDeleteDeck: vi.fn(), onOpenImportExcel: vi.fn()
  });
  const renderDecks = (decks: BackendDeck[], lang = "en", isLoading = false) => {
    const h = handlers();
    render(<DeckDashboard decks={decks} isLoading={isLoading} lang={lang} {...h} />);
    return h;
  };

  it("hiện tiêu đề h3, số thẻ, huy hiệu Mặc định/Trống và cờ SVG theo ngôn ngữ của sổ", () => {
    renderDecks([deck({ is_default: true }), deck({ id: "d2", title: "Sổ rỗng", cards_count: 0, lang_code: "de" })]);
    expect(screen.getByText("Từ vựng IELTS", { selector: "h3" })).toBeInTheDocument();
    expect(screen.getByText("12 thẻ")).toBeInTheDocument();
    expect(screen.getByText("Mặc định")).toBeInTheDocument();
    expect(screen.getByText("Trống")).toBeInTheDocument();
    expect(screen.getByText("Mở sổ để thêm từ")).toBeInTheDocument();
    expect(screen.getByTestId("lang-flag-en")).toBeInTheDocument();
    expect(screen.getByTestId("lang-flag-de")).toBeInTheDocument();
  });

  it("bấm vào thẻ (hoặc nút Mở sổ) mở đúng sổ, đúng một lần", () => {
    const h = renderDecks([deck()]);
    fireEvent.click(screen.getByText("Từ vựng IELTS", { selector: "h3" }));
    expect(h.onSelectDeck).toHaveBeenCalledTimes(1);
    expect(h.onSelectDeck).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }));
    fireEvent.click(screen.getByRole("button", { name: "Mở sổ Từ vựng IELTS" }));
    expect(h.onSelectDeck).toHaveBeenCalledTimes(2);
  });

  it("menu ⋯ chứa 4 thao tác ở tiếng Anh và gọi đúng sổ; thao tác không làm mở sổ", () => {
    const h = renderDecks([deck()]);
    const open = () => fireEvent.click(screen.getByRole("button", { name: "Tùy chọn sổ Từ vựng IELTS" }));

    open();
    expect(screen.getAllByRole("menuitem").map((i) => i.textContent)).toEqual([
      "Thêm từ vựng bằng AI", "Nhập từ Excel / CSV", "Chỉnh sửa sổ thẻ", "Xóa sổ thẻ"
    ]);
    fireEvent.click(screen.getByRole("menuitem", { name: "Thêm từ vựng bằng AI" }));
    expect(h.onOpenGenerate).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }));

    open();
    fireEvent.click(screen.getByRole("menuitem", { name: "Nhập từ Excel / CSV" }));
    expect(h.onOpenImportExcel).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }));

    open();
    fireEvent.click(screen.getByRole("menuitem", { name: "Chỉnh sửa sổ thẻ" }));
    expect(h.onOpenEditDeck).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }));

    open();
    fireEvent.click(screen.getByRole("menuitem", { name: "Xóa sổ thẻ" }));
    expect(h.onOpenDeleteDeck).toHaveBeenCalledWith(expect.objectContaining({ id: "d1" }));

    expect(h.onSelectDeck).not.toHaveBeenCalled();
  });

  it("tiếng Đức: có AI (thanh công cụ và menu) nhưng không có Thư viện bộ từ (chỉ tiếng Anh)", () => {
    const h = renderDecks([deck({ lang_code: "de" })], "de");
    expect(screen.queryByRole("button", { name: /Thư viện bộ từ/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Tạo sổ Tiếng Đức mới" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tạo từ vựng với AI" }));
    expect(h.onOpenGenerate).toHaveBeenCalledWith();  // không kèm sổ: tạo sổ mới theo ngôn ngữ của bộ sưu tập
    fireEvent.click(screen.getByRole("button", { name: "Tùy chọn sổ Từ vựng IELTS" }));
    expect(screen.getAllByRole("menuitem")).toHaveLength(4);
    fireEvent.click(screen.getByRole("menuitem", { name: "Thêm từ vựng bằng AI" }));
    expect(h.onOpenGenerate).toHaveBeenLastCalledWith(expect.objectContaining({ id: "d1" }));
  });

  it("bộ sưu tập tiếng Việt cũ (không học được): không có AI", () => {
    renderDecks([deck({ lang_code: "vi" })], "vi");
    expect(screen.queryByRole("button", { name: /Tạo từ vựng với AI/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Tùy chọn sổ Từ vựng IELTS" }));
    expect(screen.queryByRole("menuitem", { name: "Thêm từ vựng bằng AI" })).toBeNull();
  });

  it("trạng thái trống của ngôn ngữ khác tiếng Anh vẫn mời nhờ AI tạo bộ từ đầu tiên", () => {
    const h = renderDecks([], "ko");
    fireEvent.click(screen.getByRole("button", { name: "Nhờ AI tạo bộ từ vựng đầu tiên" }));
    expect(h.onOpenGenerate).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: /Khám phá thư viện bộ từ/ })).toBeNull();
  });

  it("đang tải hiện trạng thái cho trình đọc màn hình; chưa có sổ hiện trạng thái trống có nút tạo sổ", () => {
    const { unmount } = render(<DeckDashboard decks={[]} isLoading lang="en" {...handlers()} />);
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải sổ thẻ");
    unmount();
    const h = renderDecks([], "ja");
    expect(screen.getByRole("heading", { name: "Chưa có sổ Tiếng Nhật nào" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tạo sổ thẻ trống" }));
    expect(h.onOpenCreateDeck).toHaveBeenCalledTimes(1);
  });
});

describe("LanguageLibrary — header", () => {
  const renderLibrary = (props: Partial<React.ComponentProps<typeof LanguageLibrary>> = {}) => {
    const onBack = vi.fn();
    const onTabChange = vi.fn();
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <LanguageLibrary
          lang="de"
          tab="decks"
          onTabChange={onTabChange}
          onBack={onBack}
          stats={{ code: "de", learnable: true, decks: 2, cards: 34, new: 6, due: 4, weak: 1 }}
          onPlayAudio={vi.fn()}
          onOpenTranslation={vi.fn()}
          {...props}
        >
          <p>NỘI DUNG SỔ</p>
        </LanguageLibrary>
      </QueryClientProvider>
    );
    return { onBack, onTabChange };
  };

  it("breadcrumb quay về màn chọn ngôn ngữ, mục hiện tại có aria-current", () => {
    const { onBack } = renderLibrary();
    const nav = screen.getByRole("navigation", { name: "Đường dẫn" });
    fireEvent.click(within(nav).getByRole("button", { name: /Tất cả ngôn ngữ/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
    expect(within(nav).getByText("Tiếng Đức")).toHaveAttribute("aria-current", "page");
  });

  it("h1 là tên ngôn ngữ, kèm tên bản ngữ, cờ và các huy hiệu thống kê", () => {
    renderLibrary();
    expect(screen.getByRole("heading", { level: 1, name: "Tiếng Đức" })).toBeInTheDocument();
    expect(screen.getByText("Deutsch")).toBeInTheDocument();
    expect(screen.getAllByTestId("lang-flag-de").length).toBeGreaterThan(0);
    const stats = screen.getByRole("list", { name: "Thống kê ngôn ngữ" });
    expect(stats).toHaveTextContent("34 từ");
    expect(stats).toHaveTextContent("2 sổ");
    expect(stats).toHaveTextContent("4 cần ôn");
    expect(stats).toHaveTextContent("1 hay quên");
  });

  it("không có thẻ đến hạn/hay quên thì ẩn huy hiệu đó; chưa có stats thì không hiện danh sách", () => {
    renderLibrary({ stats: { code: "de", learnable: true, decks: 1, cards: 5, new: 5, due: 0, weak: 0 } });
    const stats = screen.getByRole("list", { name: "Thống kê ngôn ngữ" });
    expect(stats).not.toHaveTextContent("cần ôn");
    expect(stats).not.toHaveTextContent("hay quên");
  });

  it("tab Sổ thẻ hiện nội dung; bấm Tất cả từ vựng gọi onTabChange", () => {
    const { onTabChange } = renderLibrary();
    expect(screen.getByText("NỘI DUNG SỔ")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Sổ thẻ" })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: "Tất cả từ vựng" }));
    expect(onTabChange).toHaveBeenCalledWith("words");
  });
});

import React, { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import { FcInput, FcModal, FcSelect } from "../src/components/flashcards/ui";
import { AddCardModal } from "../src/components/flashcards/modals/AddCardModal";
import { EditCardModal } from "../src/components/flashcards/modals/EditCardModal";
import { CreateDeckModal } from "../src/components/flashcards/modals/CreateDeckModal";
import { EditDeckModal } from "../src/components/flashcards/modals/EditDeckModal";
import { DeleteDeckModal } from "../src/components/flashcards/modals/DeleteDeckModal";
import type { BackendCardItem, BackendDeck } from "../src/services/flashcardService";

const deck: BackendDeck = { id: "d1", title: "Sổ IELTS", description: "mô tả", lang_code: "de", lang_confirmed: true, cards_count: 3 };

// ---------------------------------------------------------------------------------------------------------------
describe("FcModal", () => {
  const renderModal = (props: Partial<React.ComponentProps<typeof FcModal>> = {}) => {
    const onClose = vi.fn();
    render(
      <div>
        <button>mở hộp</button>
        <FcModal title="Hộp thử" onClose={onClose} footer={<button>Lưu</button>} {...props}>
          <input aria-label="ô một" />
          <input aria-label="ô hai" />
        </FcModal>
      </div>
    );
    return onClose;
  };

  it("là hộp thoại aria-modal có tên lấy từ tiêu đề; có nút Đóng", () => {
    const onClose = renderModal();
    const dialog = screen.getByRole("dialog", { name: "Hộp thử" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    fireEvent.click(within(dialog).getByRole("button", { name: "Đóng" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("khi mở, focus vào ô nhập đầu tiên của nội dung (không phải nút Đóng)", () => {
    renderModal();
    expect(screen.getByLabelText("ô một")).toHaveFocus();
  });

  it("Esc đóng hộp và không lọt xuống phím tắt của màn phía sau", () => {
    const behind = vi.fn();
    window.addEventListener("keydown", behind);
    const onClose = renderModal();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(behind).not.toHaveBeenCalled();
    window.removeEventListener("keydown", behind);
  });

  it("bấm nền ngoài hộp thì đóng, bấm bên trong hộp thì không", () => {
    const onClose = renderModal();
    fireEvent.mouseDown(screen.getByRole("dialog"));
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.mouseDown(screen.getByRole("dialog").parentElement as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("dismissible=false: Esc, bấm nền và nút Đóng đều không đóng", () => {
    const onClose = renderModal({ dismissible: false });
    fireEvent.keyDown(document.body, { key: "Escape" });
    fireEvent.mouseDown(screen.getByRole("dialog").parentElement as HTMLElement);
    expect(screen.getByRole("button", { name: "Đóng" })).toBeDisabled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("Tab ở phần tử cuối quay về đầu, Shift+Tab ở đầu nhảy về cuối (giữ focus trong hộp)", () => {
    renderModal();
    const panel = screen.getByRole("dialog");
    const focusables = Array.from(panel.querySelectorAll<HTMLElement>("button:not([disabled]), input"));
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(first).toHaveFocus();
    first.focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();
  });

  it("đóng hộp thì trả focus về nút đã mở nó", () => {
    function Harness() {
      const [open, setOpen] = useState(false);
      return (
        <>
          <button onClick={() => setOpen(true)}>mở</button>
          {open && <FcModal title="T" onClose={() => setOpen(false)}><input aria-label="x" /></FcModal>}
        </>
      );
    }
    render(<Harness />);
    const opener = screen.getByRole("button", { name: "mở" });
    opener.focus();
    fireEvent.click(opener);
    expect(screen.getByLabelText("x")).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "Đóng" }));
    expect(opener).toHaveFocus();
  });
});

describe("FcInput / FcSelect", () => {
  it("nhãn liên kết đúng với ô nhập (getByLabelText), hint hiện khi không có lỗi", () => {
    render(<FcInput label="Tên sổ" hint="Tối đa 60 ký tự" defaultValue="a" />);
    const input = screen.getByLabelText("Tên sổ");
    expect(input).toHaveAttribute("aria-describedby");
    expect(screen.getByText("Tối đa 60 ký tự")).toBeInTheDocument();
  });

  it("có lỗi: role=alert, aria-invalid và đọc kèm ô nhập; ẩn hint", () => {
    render(<FcInput label="Tên sổ" hint="gợi ý" error="Không được để trống" />);
    const input = screen.getByLabelText("Tên sổ");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Không được để trống");
    expect(input.getAttribute("aria-describedby")).toBe(screen.getByRole("alert").id);
    expect(screen.queryByText("gợi ý")).toBeNull();
  });

  it("hai ô nhập khác nhau có id khác nhau; FcSelect cũng có nhãn liên kết", () => {
    render(
      <>
        <FcInput label="A" />
        <FcInput label="B" />
        <FcSelect label="C"><option>x</option></FcSelect>
      </>
    );
    const ids = ["A", "B", "C"].map((l) => screen.getByLabelText(l).id);
    expect(new Set(ids).size).toBe(3);
  });
});

// ---------------------------------------------------------------------------------------------------------------
describe("AddCardModal", () => {
  const setup = () => {
    const onSubmit = vi.fn(async () => {});
    const onClose = vi.fn();
    render(<AddCardModal isOpen deck={deck} onClose={onClose} onSubmit={onSubmit} />);
    return { onSubmit, onClose };
  };

  it("không hiện khi isOpen=false", () => {
    render(<AddCardModal isOpen={false} deck={deck} onClose={vi.fn()} onSubmit={vi.fn()} />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("nút Lưu thẻ bị khóa đến khi có từ và nghĩa", () => {
    setup();
    expect(screen.getByRole("button", { name: "Lưu thẻ" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Từ \/ Cụm từ ngoại ngữ/), { target: { value: "Haus" } });
    expect(screen.getByRole("button", { name: "Lưu thẻ" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Nghĩa tiếng Việt/), { target: { value: "ngôi nhà" } });
    expect(screen.getByRole("button", { name: "Lưu thẻ" })).toBeEnabled();
  });

  it("gửi dữ liệu đã cắt khoảng trắng kèm mã ngôn ngữ của sổ rồi đóng hộp", async () => {
    const { onSubmit, onClose } = setup();
    fireEvent.change(screen.getByLabelText(/Từ \/ Cụm từ ngoại ngữ/), { target: { value: "  Haus " } });
    fireEvent.change(screen.getByLabelText(/Nghĩa tiếng Việt/), { target: { value: " ngôi nhà " } });
    fireEvent.change(screen.getByLabelText("Từ loại"), { target: { value: "verb" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thẻ" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith({
      deckId: "d1", term: "Haus", definition: "ngôi nhà", phonetic: undefined, example: undefined, partOfSpeech: "verb", langCode: "de"
    });
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("ô từ đánh dấu đúng ngôn ngữ của sổ (lang) và Enter trong ô nhập cũng gửi được", async () => {
    const { onSubmit } = setup();
    const term = screen.getByLabelText(/Từ \/ Cụm từ ngoại ngữ/);
    expect(term).toHaveAttribute("lang", "de");
    fireEvent.change(term, { target: { value: "Baum" } });
    fireEvent.change(screen.getByLabelText(/Nghĩa tiếng Việt/), { target: { value: "cây" } });
    fireEvent.submit(term.closest("form") as HTMLFormElement);
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
  });
});

describe("EditCardModal", () => {
  const card: BackendCardItem = {
    id: "c1", deck_id: "d1", term: "Haus", definition: "nhà", phonetic: "/haus/", example_sentence: "Das Haus.", part_of_speech: "noun", lang_code: "de"
  };

  it("điền sẵn dữ liệu của thẻ và gửi bản cập nhật đúng thẻ", async () => {
    const onSubmit = vi.fn(async () => {});
    const onClose = vi.fn();
    render(<EditCardModal card={card} deckLang="de" onClose={onClose} onSubmit={onSubmit} />);
    expect(screen.getByLabelText(/Từ \/ Cụm từ ngoại ngữ/)).toHaveValue("Haus");
    expect(screen.getByLabelText("Phiên âm IPA")).toHaveValue("/haus/");
    fireEvent.change(screen.getByLabelText(/Nghĩa tiếng Việt/), { target: { value: "ngôi nhà" } });
    fireEvent.click(screen.getByRole("button", { name: "Cập nhật thẻ" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ cardId: "c1", deckId: "d1", definition: "ngôi nhà", langCode: "de" })));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("card=null thì không hiện", () => {
    render(<EditCardModal card={null} onClose={vi.fn()} onSubmit={vi.fn()} />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("CreateDeckModal", () => {
  it("trong bộ sưu tập ngôn ngữ: ngôn ngữ bị khóa, có cờ SVG, không có ô chọn", () => {
    render(<CreateDeckModal isOpen fixedLang="ja" onClose={vi.fn()} onSubmit={vi.fn()} />);
    const locked = screen.getByTestId("locked-language");
    expect(locked).toHaveTextContent("Tiếng Nhật");
    expect(within(locked).getByTestId("lang-flag-ja")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).toBeNull();
  });

  it("không khóa: chỉ liệt kê 9 ngôn ngữ học được (không có tiếng Việt), tùy chọn không dùng emoji cờ", () => {
    render(<CreateDeckModal isOpen onClose={vi.fn()} onSubmit={vi.fn()} />);
    const options = within(screen.getByLabelText(/Ngôn ngữ sổ thẻ/)).getAllByRole("option");
    expect(options).toHaveLength(9);
    expect(options.some((o) => /Vietnamese/.test(o.textContent ?? ""))).toBe(false);
    expect(options.every((o) => !/[\u{1F1E6}-\u{1F1FF}]/u.test(o.textContent ?? ""))).toBe(true);
  });

  it("lỗi từ máy chủ: giữ hộp mở và báo lỗi; thành công thì đóng", async () => {
    const onClose = vi.fn();
    const onSubmit = vi.fn().mockRejectedValueOnce(new Error("Tên sổ đã tồn tại")).mockResolvedValueOnce(undefined);
    render(<CreateDeckModal isOpen fixedLang="de" onClose={onClose} onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("Tên sổ thẻ"), { target: { value: "Sổ A" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo Sổ Thẻ" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Tên sổ đã tồn tại");
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Tạo Sổ Thẻ" }));
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenLastCalledWith({ title: "Sổ A", description: "", langCode: "de" });
  });

  it("đang tạo: nút đổi chữ, khóa lại và không đóng được", () => {
    const onClose = vi.fn();
    render(<CreateDeckModal isOpen fixedLang="de" isLoading onClose={onClose} onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Đang tạo..." })).toBeDisabled();
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe("EditDeckModal", () => {
  it("điền sẵn, đổi ngôn ngữ thì có ghi chú cảnh báo chuyển bộ sưu tập", async () => {
    const onSubmit = vi.fn(async () => {});
    render(<EditDeckModal deck={deck} onClose={vi.fn()} onSubmit={onSubmit} />);
    expect(screen.getByLabelText(/Tên sổ thẻ/)).toHaveValue("Sổ IELTS");
    expect(screen.queryByRole("note")).toBeNull();
    fireEvent.change(screen.getByLabelText(/Ngôn ngữ sổ thẻ/), { target: { value: "fr" } });
    expect(screen.getByRole("note")).toHaveTextContent("bộ sưu tập Tiếng Pháp");
    fireEvent.click(screen.getByRole("button", { name: "Cập nhật Sổ Thẻ" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ id: "d1", title: "Sổ IELTS", description: "mô tả", langCode: "fr" }));
  });

  it("xóa hết tên thì không lưu được", () => {
    render(<EditDeckModal deck={deck} onClose={vi.fn()} onSubmit={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Tên sổ thẻ/), { target: { value: "  " } });
    expect(screen.getByRole("button", { name: "Cập nhật Sổ Thẻ" })).toBeDisabled();
  });
});

describe("DeleteDeckModal", () => {
  it("hỏi xác nhận kèm tên sổ; xác nhận và hủy gọi đúng hàm", () => {
    const onConfirm = vi.fn(async () => {});
    const onClose = vi.fn();
    render(<DeleteDeckModal deck={deck} onClose={onClose} onConfirm={onConfirm} />);
    const dialog = screen.getByRole("dialog", { name: "Xác nhận xóa sổ thẻ?" });
    expect(dialog).toHaveTextContent('"Sổ IELTS"');
    fireEvent.click(within(dialog).getByRole("button", { name: "Xác nhận xóa" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    fireEvent.click(within(dialog).getByRole("button", { name: "Hủy" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("đang xóa: nút đổi chữ và khóa; deck=null thì không hiện", () => {
    const { unmount } = render(<DeleteDeckModal deck={deck} isLoading onClose={vi.fn()} onConfirm={vi.fn(async () => {})} />);
    expect(screen.getByRole("button", { name: "Đang xóa..." })).toBeDisabled();
    unmount();
    render(<DeleteDeckModal deck={null} onClose={vi.fn()} onConfirm={vi.fn(async () => {})} />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

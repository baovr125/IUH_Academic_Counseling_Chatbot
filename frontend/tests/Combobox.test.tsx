import React, { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Combobox } from "../src/components/ui/Combobox";
import { SettingsProvider } from "../src/context/SettingsContext";
import { OTHER } from "../src/data/iuhCatalog";

vi.mock("../src/services/settingsService", () => ({
  fetchUserSettings: vi.fn(async () => ({ ok: false, error: { message: "x" } })),
  updateUserSettings: vi.fn(async () => ({ ok: true, data: {} })),
}));

const OPTIONS = ["Khoa Công nghệ Thông tin", "Khoa Ngoại ngữ", "Viện Tài chính - Kế toán"];

function Harness({ initial = "", disabled = false, error }: { initial?: string; disabled?: boolean; error?: string }) {
  const [value, setValue] = useState(initial);
  return (
    <SettingsProvider>
      <form onSubmit={(e) => e.preventDefault()}>
        <Combobox
          label="Khoa / Viện"
          value={value}
          onChange={setValue}
          options={OPTIONS}
          otherLabel="Khác…"
          required
          disabled={disabled}
          error={error}
          hint="Gợi ý"
        />
        <output data-testid="value">{value}</output>
      </form>
    </SettingsProvider>
  );
}

const input = () => screen.getByRole("combobox", { name: /Khoa \/ Viện/ }) as HTMLInputElement;
const value = () => screen.getByTestId("value").textContent;

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("app_language", "vi");
});

describe("Combobox — ARIA", () => {
  it("có role combobox gắn nhãn, đóng mặc định, mở bằng click", () => {
    render(<Harness />);
    expect(input()).toHaveAttribute("aria-expanded", "false");
    expect(input()).toHaveAttribute("aria-autocomplete", "list");
    expect(screen.queryByRole("listbox")).toBeNull();
    fireEvent.click(input());
    expect(input()).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(OPTIONS.length + 1); // + "Khác…"
  });

  it("aria-activedescendant trỏ tới mục đang active và aria-selected đánh dấu mục đã chọn", () => {
    render(<Harness initial="Khoa Ngoại ngữ" />);
    fireEvent.click(input());
    const active = input().getAttribute("aria-activedescendant");
    expect(active).toBeTruthy();
    expect(document.getElementById(active!)).toBe(screen.getAllByRole("option")[0]);
    expect(screen.getByRole("option", { name: "Khoa Ngoại ngữ" })).toHaveAttribute("aria-selected", "true");
  });

  it("lỗi và gợi ý được liên kết bằng aria-describedby, aria-invalid khi có lỗi", () => {
    render(<Harness error="Bắt buộc" />);
    expect(input()).toHaveAttribute("aria-invalid", "true");
    const describedBy = input().getAttribute("aria-describedby")!;
    expect(document.getElementById(describedBy)).toHaveTextContent("Bắt buộc");
  });
});

describe("Combobox — tìm kiếm", () => {
  it("lọc không phân biệt dấu và hoa thường, khớp ở bất kỳ vị trí", () => {
    render(<Harness />);
    fireEvent.change(input(), { target: { value: "CONG NGHE" } });
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual(["Khoa Công nghệ Thông tin", "Khác…"]);
    fireEvent.change(input(), { target: { value: "ke toan" } });
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual(["Viện Tài chính - Kế toán", "Khác…"]);
    fireEvent.change(input(), { target: { value: "đại" } });
    expect(screen.queryByRole("option", { name: "Khoa Ngoại ngữ" })).toBeNull();
  });

  it('không có kết quả: báo "Không tìm thấy" nhưng vẫn cho chọn "Khác…"', () => {
    render(<Harness />);
    fireEvent.change(input(), { target: { value: "zzzz" } });
    expect(screen.getAllByText("Không tìm thấy kết quả phù hợp.").length).toBeGreaterThan(0);
    expect(screen.getByRole("option", { name: "Khác…" })).toBeInTheDocument();
  });
});

describe("Combobox — bàn phím và chuột", () => {
  it("↓ mở danh sách, ↓/↑ di chuyển, Enter chọn (không submit form), giá trị hiện trong ô", () => {
    render(<Harness />);
    input().focus();
    fireEvent.keyDown(input(), { key: "ArrowDown" });
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    fireEvent.keyDown(input(), { key: "ArrowDown" });
    fireEvent.keyDown(input(), { key: "ArrowDown" });
    fireEvent.keyDown(input(), { key: "ArrowUp" });
    fireEvent.keyDown(input(), { key: "Enter" });
    expect(value()).toBe("Khoa Ngoại ngữ");
    expect(input()).toHaveValue("Khoa Ngoại ngữ");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("Esc đóng và giữ nguyên lựa chọn cũ; gõ dở rồi bỏ ra ngoài thì khôi phục giá trị đã chọn", () => {
    render(<Harness initial="Khoa Ngoại ngữ" />);
    fireEvent.change(input(), { target: { value: "xyz" } });
    expect(input()).toHaveValue("xyz");
    fireEvent.keyDown(input(), { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(input()).toHaveValue("Khoa Ngoại ngữ");

    fireEvent.change(input(), { target: { value: "abc" } });
    fireEvent.blur(input());
    expect(input()).toHaveValue("Khoa Ngoại ngữ");
    expect(value()).toBe("Khoa Ngoại ngữ");
  });

  it("click chọn một mục; nút ✕ xóa lựa chọn", () => {
    render(<Harness />);
    fireEvent.click(input());
    fireEvent.click(screen.getByRole("option", { name: "Viện Tài chính - Kế toán" }));
    expect(value()).toBe("Viện Tài chính - Kế toán");
    fireEvent.click(screen.getByRole("button", { name: /Xóa lựa chọn/ }));
    expect(value()).toBe("");
    expect(input()).toHaveValue("");
  });

  it('chọn "Khác…" trả về giá trị đặc biệt OTHER và hiển thị chữ "Khác…"', () => {
    render(<Harness />);
    fireEvent.click(input());
    fireEvent.click(screen.getByRole("option", { name: "Khác…" }));
    expect(value()).toBe(OTHER);
    expect(input()).toHaveValue("Khác…");
  });

  it("disabled: không mở được danh sách", () => {
    render(<Harness disabled />);
    expect(input()).toBeDisabled();
    fireEvent.click(input());
    expect(screen.queryByRole("listbox")).toBeNull();
  });
});

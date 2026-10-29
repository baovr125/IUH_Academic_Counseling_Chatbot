import React, { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  FcBadge,
  FcButton,
  FcCard,
  FcEmpty,
  FcLoading,
  FcPage,
  FcSkeleton,
  FcStat,
  FcTabs,
  LangFlag
} from "../src/components/flashcards/ui";
import { LANG_CODES } from "../src/services/deckStorage";

describe("LangFlag", () => {
  it("có cờ SVG cho đủ mọi ngôn ngữ trong LANG_CONFIG", () => {
    for (const code of LANG_CODES) {
      const { unmount } = render(<LangFlag lang={code} />);
      expect(screen.getByTestId(`lang-flag-${code}`), code).toBeInTheDocument();
      unmount();
    }
  });

  it("mã lạ hoặc rỗng rơi về biểu tượng quả địa cầu, không báo lỗi", () => {
    const { unmount } = render(<LangFlag lang="xx" />);
    expect(screen.getByTestId("lang-flag-fallback")).toBeInTheDocument();
    unmount();
    render(<LangFlag lang={null} />);
    expect(screen.getByTestId("lang-flag-fallback")).toBeInTheDocument();
  });

  it("mặc định chỉ trang trí (aria-hidden), có title thì là hình có nhãn", () => {
    const { rerender } = render(<LangFlag lang="de" />);
    expect(screen.getByTestId("lang-flag-de")).toHaveAttribute("aria-hidden", "true");
    rerender(<LangFlag lang="de" title="Cờ Đức" />);
    expect(screen.getByRole("img", { name: "Cờ Đức" })).toBeInTheDocument();
  });
});

describe("FcButton", () => {
  it("mặc định type=button để không vô tình submit form", () => {
    render(<FcButton>Lưu</FcButton>);
    expect(screen.getByRole("button", { name: "Lưu" })).toHaveAttribute("type", "button");
  });

  it("loading khóa nút, báo aria-busy và không gọi onClick", () => {
    const onClick = vi.fn();
    render(<FcButton loading onClick={onClick}>Đang lưu</FcButton>);
    const btn = screen.getByRole("button", { name: "Đang lưu" });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("cả 5 biến thể đều có lớp dark: để không chói ở chế độ tối (trừ primary/danger dùng nền đặc)", () => {
    for (const variant of ["soft", "secondary", "ghost"] as const) {
      const { unmount } = render(<FcButton variant={variant}>x</FcButton>);
      expect(screen.getByRole("button").className, variant).toContain("dark:");
      unmount();
    }
  });
});

describe("FcBadge / FcCard / FcStat", () => {
  it("huy hiệu có biến thể tối cho từng tông", () => {
    for (const tone of ["slate", "blue", "orange", "emerald", "rose", "sky", "amber"] as const) {
      const { unmount } = render(<FcBadge tone={tone}>n</FcBadge>);
      expect(screen.getByText("n").className, tone).toContain("dark:");
      unmount();
    }
  });

  it("FcCard hiển thị đúng thẻ HTML được chọn và nhận data-testid", () => {
    render(<ul><FcCard as="li" data-testid="card">nội dung</FcCard></ul>);
    expect(screen.getByTestId("card").tagName).toBe("LI");
    expect(screen.getByTestId("card").className).toContain("dark:bg-slate-800");
  });

  it("FcCard interactive có hiệu ứng hover, thường thì không", () => {
    const { rerender } = render(<FcCard data-testid="c">a</FcCard>);
    expect(screen.getByTestId("c").className).not.toContain("hover:-translate-y");
    rerender(<FcCard data-testid="c" interactive>a</FcCard>);
    expect(screen.getByTestId("c").className).toContain("hover:-translate-y");
  });

  it("FcStat hiện nhãn và con số", () => {
    render(<FcStat label="Cần ôn hôm nay" value={18} />);
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("Cần ôn hôm nay")).toBeInTheDocument();
  });
});

describe("FcTabs", () => {
  function Harness() {
    const [v, setV] = useState<"a" | "b" | "c">("a");
    return (
      <FcTabs
        ariaLabel="Chế độ xem"
        value={v}
        onChange={setV}
        tabs={[
          { value: "a", label: "Ôn tập" },
          { value: "b", label: "Danh sách", count: 8 },
          { value: "c", label: "Trò chơi" }
        ]}
      />
    );
  }

  it("có role tablist/tab và aria-selected đúng", () => {
    render(<Harness />);
    expect(screen.getByRole("tablist", { name: "Chế độ xem" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Ôn tập" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: /Danh sách/ })).toHaveAttribute("aria-selected", "false");
  });

  it("bấm chuyển tab và hiện số đếm", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("tab", { name: /Danh sách/ }));
    expect(screen.getByRole("tab", { name: /Danh sách/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("phím mũi tên, Home, End di chuyển và quay vòng; chỉ tab đang chọn nằm trong thứ tự Tab", () => {
    render(<Harness />);
    const tabs = () => screen.getAllByRole("tab");
    expect(tabs().map((t) => t.getAttribute("tabindex"))).toEqual(["0", "-1", "-1"]);
    fireEvent.keyDown(tabs()[0], { key: "ArrowLeft" }); // quay vòng về cuối
    expect(tabs()[2]).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(tabs()[2], { key: "ArrowRight" }); // quay vòng về đầu
    expect(tabs()[0]).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(tabs()[0], { key: "End" });
    expect(tabs()[2]).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(tabs()[2], { key: "Home" });
    expect(tabs()[0]).toHaveAttribute("aria-selected", "true");
  });
});

describe("FcEmpty / FcSkeleton / FcPage", () => {
  it("FcEmpty hiện tiêu đề, mô tả và nút hành động", () => {
    const onClick = vi.fn();
    render(
      <FcEmpty title="Chưa có sổ nào" description="Hãy tạo sổ đầu tiên" data-testid="empty">
        <FcButton variant="primary" onClick={onClick}>Tạo sổ</FcButton>
      </FcEmpty>
    );
    expect(screen.getByRole("heading", { name: "Chưa có sổ nào" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tạo sổ" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("FcLoading báo trạng thái cho trình đọc màn hình, còn FcSkeleton thì ẩn", () => {
    render(
      <FcLoading label="Đang tải sổ thẻ">
        <FcSkeleton className="h-4 w-10" />
      </FcLoading>
    );
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải sổ thẻ");
  });

  it("FcPage dùng nền khung chung (không tự tô nền) và nhận độ rộng", () => {
    const { container } = render(<FcPage width="md"><p>x</p></FcPage>);
    expect((container.firstChild as HTMLElement).className).not.toMatch(/bg-/);
    expect(container.querySelector(".max-w-4xl")).not.toBeNull();
  });
});

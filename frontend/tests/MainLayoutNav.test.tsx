import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../src/context/SettingsContext", () => ({
  useSettings: () => ({ language: "vi", t: (k: string) => k }),
}));
const auth = vi.hoisted(() => ({ user: { id: "u1", fullName: "Nguyễn Văn A", email: "a@iuh.edu.vn", role: "student" } as any }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: auth.user, logout: vi.fn() }) }));

import { MainLayout } from "../src/components/layout/MainLayout";

const renderLayout = (path = "/dashboard") =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<div>Trang tổng quan</div>} />
          <Route path="/chat" element={<div>Trang chat</div>} />
          <Route path="/translation" element={<div>Trang dịch</div>} />
          <Route path="/flashcards" element={<div>Trang thẻ</div>} />
          <Route path="/admin" element={<div>Trang quản trị</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );

const openDrawer = () => fireEvent.click(screen.getByRole("button", { name: "topbar.openMenu" }));

describe("MainLayout — điều hướng trên màn hình nhỏ", () => {
  beforeEach(() => {
    auth.user = { id: "u1", fullName: "Nguyễn Văn A", email: "a@iuh.edu.vn", role: "student" };
  });

  it("mặc định đóng ngăn kéo; bấm hamburger thì mở, có đủ mục điều hướng", () => {
    renderLayout();
    expect(screen.queryByRole("dialog")).toBeNull();
    openDrawer();
    const drawer = screen.getByRole("dialog");
    expect(within(drawer).getByRole("link", { name: "sidebar.personalHub" })).toBeInTheDocument();
    expect(within(drawer).getByRole("link", { name: "sidebar.knowledgeHub" })).toBeInTheDocument();
    expect(within(drawer).getByRole("link", { name: "sidebar.translationStudio" })).toBeInTheDocument();
    expect(within(drawer).getByRole("link", { name: "sidebar.languageLab" })).toBeInTheDocument();
  });

  it("đóng bằng nút X, bấm nền mờ và phím Esc", () => {
    renderLayout();

    openDrawer();
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "common.close" }));
    expect(screen.queryByRole("dialog")).toBeNull();

    openDrawer();
    fireEvent.click(screen.getByTestId("mobile-nav-drawer").firstElementChild as HTMLElement);
    expect(screen.queryByRole("dialog")).toBeNull();

    openDrawer();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("chọn một mục thì chuyển trang và tự đóng ngăn kéo", () => {
    renderLayout("/dashboard");
    openDrawer();
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("link", { name: "sidebar.knowledgeHub" }));
    expect(screen.getByText("Trang chat")).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("mục Quản trị chỉ hiện với admin", () => {
    renderLayout();
    openDrawer();
    expect(within(screen.getByRole("dialog")).queryByRole("link", { name: "sidebar.admin" })).toBeNull();
  });

  it("admin thấy mục Quản trị trong ngăn kéo", () => {
    auth.user = { ...auth.user, role: "admin" };
    renderLayout();
    openDrawer();
    expect(within(screen.getByRole("dialog")).getByRole("link", { name: "sidebar.admin" })).toBeInTheDocument();
  });

  it("thanh icon cố định vẫn được render (CSS md:flex quyết định hiển thị) và ngăn kéo chỉ hiện dưới md", () => {
    renderLayout();
    const aside = document.querySelector("aside");
    expect(aside).not.toBeNull();
    expect(aside!.className).toContain("hidden");
    expect(aside!.className).toContain("md:flex");
    openDrawer();
    expect(screen.getByTestId("mobile-nav-drawer").className).toContain("md:hidden");
  });
});

describe("MainLayout — thanh trên: tên thương hiệu nhỏ + tên trang", () => {
  const renderAt = (path: string) =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/dashboard" element={<div>tổng quan</div>} />
            <Route path="/chat" element={<div>chat</div>} />
            <Route path="/translation" element={<div>dịch</div>} />
            <Route path="/translation-doc" element={<div>dịch tài liệu</div>} />
            <Route path="/flashcards/:lang" element={<div>thẻ</div>} />
            <Route path="/khac" element={<div>khác</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

  it("luôn có tên thương hiệu nhỏ phía trên", () => {
    renderAt("/chat");
    expect(screen.getByRole("button", { name: "topbar.title" })).toBeInTheDocument();
  });

  it.each([
    ["/chat", "pageTitle.chat"],
    ["/translation", "pageTitle.translation"],
    ["/translation-doc", "pageTitle.translationDoc"],
    ["/flashcards/en", "pageTitle.flashcards"],
  ])("đường dẫn %s hiện tên trang %s", (path, key) => {
    renderAt(path);
    expect(screen.getByTestId("page-title")).toHaveTextContent(key);
  });

  it("đường dẫn lạ không hiện tên trang", () => {
    renderAt("/khac");
    expect(screen.queryByTestId("page-title")).toBeNull();
  });

  it("bấm logo (thanh bên) hoặc tên thương hiệu (thanh trên) đều về Dashboard", () => {
    const { unmount } = renderAt("/chat");
    const aside = document.querySelector("aside") as HTMLElement;
    fireEvent.click(within(aside).getByRole("link", { name: "IUH Portal AI" }));
    expect(screen.getByText("tổng quan")).toBeInTheDocument();
    expect(screen.getByTestId("page-title")).toHaveTextContent("pageTitle.dashboard");
    unmount();

    renderAt("/chat");
    fireEvent.click(screen.getByRole("button", { name: "topbar.title" }));
    expect(screen.getByText("tổng quan")).toBeInTheDocument();
    expect(screen.getByTestId("page-title")).toHaveTextContent("pageTitle.dashboard");
  });

  it("logo trên thanh trên (điện thoại) cũng về Dashboard", () => {
    renderAt("/translation");
    fireEvent.click(screen.getByRole("button", { name: "topbar.goToDashboard" }));
    expect(screen.getByText("tổng quan")).toBeInTheDocument();
  });

  it("logo ở góc thanh bên là liên kết về Dashboard, không nằm trong ô riêng", () => {
    renderAt("/chat");
    const aside = document.querySelector("aside") as HTMLElement;
    const link = within(aside).getByRole("link", { name: "IUH Portal AI" });
    expect(link).toHaveAttribute("href", "/dashboard");
    expect(link.querySelector("img")).not.toBeNull();
    expect(aside.className).not.toMatch(/\bbg-/);
    // chỉ một đường dọc mảnh ở mép phải để ngăn vùng điều hướng với vùng làm việc
    expect(aside.className).toContain("border-r");
    expect(aside.className).not.toMatch(/\bborder-[tbl]\b/);
  });
});

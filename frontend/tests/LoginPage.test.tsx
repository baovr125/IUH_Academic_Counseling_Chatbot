import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "../src/pages/LoginPage";
import { AuthContext } from "../src/hooks/useAuth";
import { SettingsProvider } from "../src/context/SettingsContext";

vi.mock("../src/services/settingsService", () => ({
  fetchUserSettings: vi.fn(async () => ({ ok: false, error: { message: "x" } })),
  updateUserSettings: vi.fn(async () => ({ ok: true, data: {} })),
}));

type RegisterResult = { ok: boolean; message?: string; field?: string; details?: { field: string; message: string }[] };

function renderPage(overrides: Partial<Record<string, unknown>> = {}) {
  const auth = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: vi.fn(async () => false),
    register: vi.fn(async (): Promise<RegisterResult> => ({ ok: true })),
    logout: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    updateUser: vi.fn(),
    ...overrides,
  };
  render(
    <MemoryRouter>
      <AuthContext.Provider value={auth as never}>
        <SettingsProvider>
          <LoginPage />
        </SettingsProvider>
      </AuthContext.Provider>
    </MemoryRouter>
  );
  return auth;
}

/** Chọn một mục trong Combobox: gõ để lọc rồi bấm vào mục tương ứng. */
function pick(labelPattern: RegExp, typed: string, optionName: string | RegExp) {
  const input = screen.getByRole("combobox", { name: labelPattern });
  if (typed) fireEvent.change(input, { target: { value: typed } });
  else fireEvent.click(input);
  fireEvent.click(screen.getByRole("option", { name: optionName }));
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  localStorage.setItem("app_language", "vi");
});

describe("LoginPage — đăng nhập", () => {
  it("nhãn được gắn đúng với ô nhập (truy cập được bằng trình đọc màn hình)", () => {
    renderPage();
    expect(screen.getByLabelText(/Mã số sinh viên hoặc Email/)).toBeInstanceOf(HTMLInputElement);
    const pw = screen.getByLabelText(/^Mật khẩu/);
    expect(pw).toHaveAttribute("type", "password");
    expect(pw).toHaveAttribute("autocomplete", "current-password");
  });

  it("nút hiện/ẩn mật khẩu có tên và trạng thái", () => {
    renderPage();
    const toggle = screen.getByRole("button", { name: "Hiện mật khẩu" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(toggle);
    expect(screen.getByLabelText(/^Mật khẩu/)).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: "Ẩn mật khẩu" })).toHaveAttribute("aria-pressed", "true");
  });

  it("để trống thì báo lỗi theo từng ô, có role=alert và đánh dấu aria-invalid", () => {
    const auth = renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Vui lòng nhập đầy đủ tài khoản và mật khẩu.");
    expect(screen.getByLabelText(/Mã số sinh viên hoặc Email/)).toHaveAttribute("aria-invalid", "true");
    expect(auth.login).not.toHaveBeenCalled();
  });

  it("gửi thông tin đăng nhập kèm tuỳ chọn ghi nhớ", async () => {
    const auth = renderPage({ login: vi.fn(async () => true) });
    fireEvent.change(screen.getByLabelText(/Mã số sinh viên hoặc Email/), { target: { value: "  20012345 " } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/), { target: { value: "Secret123" } });
    fireEvent.click(screen.getByLabelText("Ghi nhớ đăng nhập trên thiết bị này"));
    fireEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    await waitFor(() => expect(auth.login).toHaveBeenCalledWith({ identifier: "20012345", password: "Secret123", rememberMe: true }));
  });

  it("hiển thị lỗi của server (ví dụ bị khóa tạm) dưới dạng alert", () => {
    renderPage({ error: "Quá nhiều lần thử không thành công. Vui lòng thử lại sau 15 phút." });
    expect(screen.getByRole("alert")).toHaveTextContent("Quá nhiều lần thử");
  });

  it("không còn luồng quên mật khẩu giả: chỉ có thông báo hướng dẫn, không có nút gọi API 404", () => {
    renderPage();
    expect(screen.queryByRole("button", { name: /Quên mật khẩu/ })).toBeNull();
    expect(screen.getByText(/đang được phát triển/)).toBeInTheDocument();
  });

  it("đổi ngôn ngữ sang English cập nhật chữ trên trang", () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "English" }));
    expect(screen.getByRole("heading", { name: "Welcome to IUH Portal AI" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Student ID or email/)).toBeInTheDocument();
  });
});

describe("LoginPage — đăng ký", () => {
  const openRegister = () => fireEvent.click(screen.getAllByRole("tab", { name: "Đăng ký tài khoản" })[0]);

  it("không còn ô MSSV ở form đăng ký sinh viên", () => {
    renderPage();
    openRegister();
    expect(screen.queryByLabelText(/Mã số sinh viên/)).toBeNull();
    expect(screen.getByText(/lấy từ email/)).toBeInTheDocument();
  });

  it("kiểm tra phía client khớp luật server: đuôi email IUH, khoa/ngành, mật khẩu", () => {
    const auth = renderPage();
    openRegister();
    fireEvent.change(screen.getByLabelText(/Họ và tên/), { target: { value: "Nguyễn Văn Bảo" } });
    fireEvent.change(screen.getByLabelText(/Email sinh viên/), { target: { value: "bao@gmail.com" } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/), { target: { value: "abcdefgh" } });
    fireEvent.click(screen.getByRole("button", { name: "Đăng ký tài khoản" }));

    expect(screen.getByText(/phải có đuôi @student\.iuh\.edu\.vn/)).toBeInTheDocument();
    expect(screen.getByText("Mật khẩu phải có ít nhất một chữ số.")).toBeInTheDocument();
    expect(screen.getByText("Khoa / Viện không được để trống.")).toBeInTheDocument();
    expect(screen.getByText("Ngành học không được để trống.")).toBeInTheDocument();
    expect(auth.register).not.toHaveBeenCalled();
  });

  it("người dùng công cộng không phải nhập MSSV/Khoa/Ngành", () => {
    renderPage();
    openRegister();
    fireEvent.click(screen.getByRole("button", { name: /Người dùng công cộng/ }));
    expect(screen.queryByLabelText(/Khoa/)).toBeNull();
    expect(screen.queryByLabelText(/Ngành học/)).toBeNull();
    expect(screen.getByLabelText(/^Email/)).toBeInTheDocument();
  });

  it("Ngành bị khóa tới khi chọn Khoa/Viện, rồi chỉ hiện các ngành của khoa đó (tìm không dấu)", () => {
    renderPage();
    openRegister();
    expect(screen.getByRole("combobox", { name: /Ngành học/ })).toBeDisabled();

    pick(/Khoa \/ Viện/, "cong nghe thong tin", "Khoa Công nghệ Thông tin");
    const major = screen.getByRole("combobox", { name: /Ngành học/ });
    expect(major).toBeEnabled();
    fireEvent.click(major);
    const names = screen.getAllByRole("option").map((o) => o.textContent);
    expect(names).toEqual(expect.arrayContaining(["Kỹ thuật phần mềm", "Hệ thống thông tin", "Khác…"]));
    expect(names).not.toContain("Kế toán");
  });

  it("đổi Khoa thì xóa Ngành đã chọn", () => {
    renderPage();
    openRegister();
    pick(/Khoa \/ Viện/, "cong nghe thong tin", "Khoa Công nghệ Thông tin");
    pick(/Ngành học/, "phan mem", "Kỹ thuật phần mềm");
    expect(screen.getByRole("combobox", { name: /Ngành học/ })).toHaveValue("Kỹ thuật phần mềm");
    pick(/Khoa \/ Viện/, "ngoai ngu", "Khoa Ngoại ngữ");
    expect(screen.getByRole("combobox", { name: /Ngành học/ })).toHaveValue("");
  });

  it('chọn "Khác…" thì hiện ô nhập tay cho Khoa và Ngành', () => {
    renderPage();
    openRegister();
    pick(/Khoa \/ Viện/, "", "Khác…");
    expect(screen.getByLabelText(/Tên Khoa \/ Viện của bạn/)).toBeInTheDocument();
    // Ngành tự chuyển sang "Khác…" vì khoa nhập tay không có danh mục ngành
    expect(screen.getByLabelText(/Tên ngành học của bạn/)).toBeInTheDocument();
  });

  it("gửi đúng tên khoa/ngành (không có MSSV) và lỗi trùng MSSV từ server hiện ở ô email", async () => {
    const auth = renderPage({
      register: vi.fn(async (): Promise<RegisterResult> => ({
        ok: false,
        message: "Mã số sinh viên đã tồn tại",
        field: "email",
        details: [],
      })),
    });
    openRegister();
    fireEvent.change(screen.getByLabelText(/Họ và tên/), { target: { value: "Nguyễn Văn Bảo" } });
    fireEvent.change(screen.getByLabelText(/Email sinh viên/), { target: { value: "20012345@student.iuh.edu.vn" } });
    pick(/Khoa \/ Viện/, "cong nghe thong tin", "Khoa Công nghệ Thông tin");
    pick(/Ngành học/, "phan mem", "Kỹ thuật phần mềm");
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/), { target: { value: "Str0ngPass-2026" } });
    fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/), { target: { value: "Str0ngPass-2026" } });
    fireEvent.click(screen.getByRole("button", { name: "Đăng ký tài khoản" }));

    await waitFor(() => expect(auth.register).toHaveBeenCalled());
    const payload = (auth.register.mock.calls[0] as unknown as [Record<string, unknown>])[0];
    expect(payload).toMatchObject({
      identifier: "20012345@student.iuh.edu.vn",
      userType: "student",
      department: "Khoa Công nghệ Thông tin",
      major: "Kỹ thuật phần mềm",
    });
    expect(payload).not.toHaveProperty("studentCode");
    await waitFor(() => expect(screen.getByLabelText(/Email sinh viên/)).toHaveAttribute("aria-invalid", "true"));
    expect(screen.getAllByText("Mã số sinh viên đã tồn tại").length).toBeGreaterThan(0);
  });

  it("hiển thị logo trường (có văn bản thay thế)", () => {
    renderPage();
    expect(screen.getAllByAltText("Logo Trường Đại học Công nghiệp TP. Hồ Chí Minh").length).toBeGreaterThanOrEqual(1);
  });

  it("đăng ký thành công chuyển về tab đăng nhập và báo bằng role=status", async () => {
    renderPage();
    openRegister();
    fireEvent.click(screen.getByRole("button", { name: /Người dùng công cộng/ }));
    fireEvent.change(screen.getByLabelText(/Họ và tên/), { target: { value: "Guest User" } });
    fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: "guest@gmail.com" } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/), { target: { value: "Str0ngPass-2026" } });
    fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu/), { target: { value: "Str0ngPass-2026" } });
    fireEvent.click(screen.getByRole("button", { name: "Đăng ký tài khoản" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Đăng ký tài khoản thành công"));
    expect(screen.getByLabelText(/Mã số sinh viên hoặc Email/)).toHaveValue("guest@gmail.com");
  });
});

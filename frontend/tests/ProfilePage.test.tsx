import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProfilePage from "../src/pages/ProfilePage";
import { AuthContext } from "../src/hooks/useAuth";
import { SettingsProvider } from "../src/context/SettingsContext";

vi.mock("../src/services/settingsService", () => ({
  fetchUserSettings: vi.fn(async () => ({ ok: false, error: { message: "x" } })),
  updateUserSettings: vi.fn(async () => ({ ok: true, data: {} })),
}));

const student = {
  id: "u1",
  fullName: "Nguyễn Văn Bảo",
  email: "20012345@student.iuh.edu.vn",
  role: "student" as const,
  studentCode: "20012345",
  department: "Khoa CNTT",
  major: "KTPM",
  phoneNumber: null,
  avatarUrl: null,
  hasPassword: true,
};

function renderPage(user: Record<string, unknown> = student, overrides: Record<string, unknown> = {}) {
  const auth = {
    user,
    isAuthenticated: true,
    isLoading: false,
    error: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateProfile: vi.fn(async () => ({ ok: true })),
    changePassword: vi.fn(async () => ({ ok: true })),
    updateUser: vi.fn(),
    ...overrides,
  };
  render(
    <AuthContext.Provider value={auth as never}>
      <SettingsProvider>
        <ProfilePage />
      </SettingsProvider>
    </AuthContext.Provider>
  );
  return auth;
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  localStorage.setItem("app_language", "vi");
});

describe("ProfilePage — thông tin cá nhân", () => {
  it("email và MSSV chỉ đọc (không thể tự đổi danh tính)", () => {
    renderPage();
    expect(screen.getByLabelText("Email hệ thống")).toBeDisabled();
    expect(screen.getByLabelText("Mã số sinh viên (MSSV)")).toBeDisabled();
  });

  it("chỉ gửi các trường được phép sửa", async () => {
    const auth = renderPage();
    fireEvent.change(screen.getByLabelText(/Họ và tên/), { target: { value: "Nguyễn Bảo" } });
    fireEvent.change(screen.getByLabelText("Số điện thoại liên hệ"), { target: { value: "0901234567" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(auth.updateProfile).toHaveBeenCalled());
    expect(auth.updateProfile).toHaveBeenCalledWith({
      fullName: "Nguyễn Bảo",
      phoneNumber: "0901234567",
      department: "Khoa CNTT",
      major: "KTPM",
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Đã lưu thông tin thành công.");
  });

  it("Khoa/Ngành nằm trong danh mục được chọn sẵn; giá trị cũ ngoài danh mục giữ nguyên trong ô 'Khác…'", () => {
    const { unmount } = (() => {
      renderPage({ ...student, department: "Khoa Ngoại ngữ", major: "Ngôn ngữ Anh" });
      return { unmount: () => undefined };
    })();
    expect(screen.getByRole("combobox", { name: /Khoa \/ Viện/ })).toHaveValue("Khoa Ngoại ngữ");
    expect(screen.getByRole("combobox", { name: /Ngành học/ })).toHaveValue("Ngôn ngữ Anh");
    unmount();
  });

  it("giá trị Khoa cũ không có trong danh mục không bị mất", () => {
    renderPage(); // student.department = "Khoa CNTT" (không phải tên chính thức)
    expect(screen.getByRole("combobox", { name: /Khoa \/ Viện/ })).toHaveValue("Khác…");
    expect(screen.getByLabelText(/Tên Khoa \/ Viện của bạn/)).toHaveValue("Khoa CNTT");
    expect(screen.getByLabelText(/Tên ngành học của bạn/)).toHaveValue("KTPM");
  });

  it("tài khoản công cộng không thấy MSSV/Khoa/Ngành", () => {
    renderPage({ ...student, role: "public", studentCode: null, department: null, major: null });
    expect(screen.queryByLabelText("Mã số sinh viên (MSSV)")).toBeNull();
    expect(screen.queryByLabelText(/Ngành học/)).toBeNull();
  });

  it("số điện thoại sai bị chặn ở client", () => {
    const auth = renderPage();
    fireEvent.change(screen.getByLabelText("Số điện thoại liên hệ"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(screen.getByText("Số điện thoại không hợp lệ.")).toBeInTheDocument();
    expect(auth.updateProfile).not.toHaveBeenCalled();
  });
});

describe("ProfilePage — đổi mật khẩu", () => {
  const openSecurity = () => fireEvent.click(screen.getByRole("tab", { name: /Bảo mật/ }));

  it("bắt buộc nhập mật khẩu hiện tại và gửi cả ba trường lên server", async () => {
    const auth = renderPage();
    openSecurity();
    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));
    expect(screen.getByText("Vui lòng nhập mật khẩu hiện tại.")).toBeInTheDocument();
    expect(auth.changePassword).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/Mật khẩu hiện tại/), { target: { value: "OldPass123" } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/), { target: { value: "NewStr0ng-Pass9" } });
    fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu mới/), { target: { value: "NewStr0ng-Pass9" } });
    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));
    await waitFor(() =>
      expect(auth.changePassword).toHaveBeenCalledWith({
        currentPassword: "OldPass123",
        newPassword: "NewStr0ng-Pass9",
        confirmPassword: "NewStr0ng-Pass9",
      })
    );
    expect(await screen.findByRole("status")).toHaveTextContent("Đổi mật khẩu thành công");
  });

  it("áp cùng quy tắc với server: không chấp nhận 6 ký tự", () => {
    const auth = renderPage();
    openSecurity();
    fireEvent.change(screen.getByLabelText(/Mật khẩu hiện tại/), { target: { value: "OldPass123" } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/), { target: { value: "abc123" } });
    fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu mới/), { target: { value: "abc123" } });
    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));
    expect(screen.getByText("Mật khẩu phải có tối thiểu 8 ký tự.")).toBeInTheDocument();
    expect(auth.changePassword).not.toHaveBeenCalled();
  });

  it("mật khẩu hiện tại sai (400 field=current_password) hiện ngay dưới ô đó", async () => {
    renderPage(student, {
      changePassword: vi.fn(async () => ({ ok: false, message: "Mật khẩu hiện tại không chính xác", field: "current_password" })),
    });
    openSecurity();
    fireEvent.change(screen.getByLabelText(/Mật khẩu hiện tại/), { target: { value: "WrongOld123" } });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/), { target: { value: "NewStr0ng-Pass9" } });
    fireEvent.change(screen.getByLabelText(/Xác nhận mật khẩu mới/), { target: { value: "NewStr0ng-Pass9" } });
    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));
    await waitFor(() => expect(screen.getByLabelText(/Mật khẩu hiện tại/)).toHaveAttribute("aria-invalid", "true"));
  });

  it("hiển thị độ mạnh và danh sách tiêu chí", () => {
    renderPage();
    openSecurity();
    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/), { target: { value: "abcdefg1" } });
    expect(screen.getByText("Trung bình")).toBeInTheDocument();
    expect(screen.getByText("Ít nhất 8 ký tự")).toBeInTheDocument();
  });
});

describe("ProfilePage — ảnh đại diện", () => {
  it("hộp thoại có role=dialog, đóng bằng phím Esc và trả focus", async () => {
    renderPage();
    const trigger = screen.getByRole("button", { name: "Thay đổi ảnh đại diện" });
    trigger.focus();
    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Cập nhật ảnh đại diện" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(trigger).toHaveFocus();
  });
});

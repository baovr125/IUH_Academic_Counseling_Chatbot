import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("../src/context/SettingsContext", () => ({
  useSettings: () => ({ language: "vi", t: (k: string) => k }),
}));

const chat = vi.hoisted(() => ({
  startNewSession: vi.fn(),
  selectSession: vi.fn(),
}));
vi.mock("../src/hooks/useChat", () => ({
  RESET_CHAT_EVENT_NAME: "reset-chat",
  useChat: () => ({
    sessions: [{ id: "s1", title: "Quy chế đào tạo", updatedAt: new Date().toISOString(), messages: [] }],
    activeSessionId: "s1",
    messages: [],
    isSending: false,
    isLoadingSessions: false,
    error: null,
    streamingSessionIds: new Set<string>(),
    selectSession: chat.selectSession,
    startNewSession: chat.startNewSession,
    sendMessage: vi.fn(),
    renameSession: vi.fn(),
    deleteSession: vi.fn(),
    abortStream: vi.fn(),
    hasMoreSessions: false,
    isLoadingMoreSessions: false,
    loadMoreSessions: vi.fn(),
    hasMoreMessages: false,
    isLoadingMoreMessages: false,
    loadMoreMessages: vi.fn(),
  }),
}));

const media = vi.hoisted(() => ({ desktop: false }));
vi.mock("../src/hooks/useMediaQuery", () => ({ useMediaQuery: () => media.desktop }));

import ChatPage from "../src/pages/ChatPage";

beforeEach(() => {
  chat.startNewSession.mockClear();
  chat.selectSession.mockClear();
  localStorage.clear();
  // jsdom không cài scrollIntoView
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

describe("ChatPage — điện thoại/máy tính bảng (< lg)", () => {
  beforeEach(() => {
    media.desktop = false;
  });

  it("chỉ có một icon nhỏ để mở lịch sử, không hiện danh sách ngay", () => {
    render(<ChatPage />);
    expect(screen.getByRole("button", { name: "Mở lịch sử trò chuyện" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("Hôm nay")).toBeNull();
  });

  it("bấm icon mở ngăn kéo có nút cuộc trò chuyện mới; chọn xong ngăn kéo tự đóng", () => {
    render(<ChatPage />);
    fireEvent.click(screen.getByRole("button", { name: "Mở lịch sử trò chuyện" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();

    fireEvent.click(screen.getByText("Quy chế đào tạo"));
    expect(chat.selectSession).toHaveBeenCalledWith("s1");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("Cuộc trò chuyện mới trong ngăn kéo tạo phiên mới và đóng ngăn kéo", () => {
    render(<ChatPage />);
    fireEvent.click(screen.getByRole("button", { name: "Mở lịch sử trò chuyện" }));
    fireEvent.click(screen.getByRole("button", { name: /Cuộc trò chuyện mới/ }));
    expect(chat.startNewSession).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("ChatPage — máy tính (>= lg)", () => {
  beforeEach(() => {
    media.desktop = true;
  });

  it("mặc định mở rộng; thu gọn thành thanh icon và nhớ trạng thái", () => {
    render(<ChatPage />);
    expect(screen.getByText("Hôm nay")).toBeInTheDocument();
    // không còn icon nổi dành cho điện thoại
    expect(screen.queryByTitle("Lịch sử trò chuyện")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Thu gọn lịch sử trò chuyện" }));
    expect(screen.queryByText("Hôm nay")).toBeNull();
    expect(screen.getByRole("button", { name: "Mở lịch sử trò chuyện" })).toBeInTheDocument();
    expect(localStorage.getItem("chat_history_panel_open")).toBe("false");

    fireEvent.click(screen.getByRole("button", { name: "Mở lịch sử trò chuyện" }));
    expect(screen.getByText("Hôm nay")).toBeInTheDocument();
    expect(localStorage.getItem("chat_history_panel_open")).toBe("true");
  });

  it("khởi động ở trạng thái thu gọn nếu lần trước đã thu gọn", () => {
    localStorage.setItem("chat_history_panel_open", "false");
    render(<ChatPage />);
    expect(screen.queryByText("Hôm nay")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Cuộc trò chuyện mới" }));
    expect(chat.startNewSession).toHaveBeenCalledTimes(1);
  });

  it("phím tắt: Ctrl+Shift+O tạo cuộc trò chuyện mới, Ctrl+\\ mở/thu gọn lịch sử", () => {
    render(<ChatPage />);
    fireEvent.keyDown(window, { key: "O", ctrlKey: true, shiftKey: true });
    expect(chat.startNewSession).toHaveBeenCalledTimes(1);

    expect(screen.getByText("Hôm nay")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "\\", ctrlKey: true });
    expect(screen.queryByText("Hôm nay")).toBeNull();
    fireEvent.keyDown(window, { key: "\\", ctrlKey: true });
    expect(screen.getByText("Hôm nay")).toBeInTheDocument();
  });
});

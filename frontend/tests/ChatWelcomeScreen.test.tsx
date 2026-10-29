import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("../src/context/SettingsContext", () => ({
  useSettings: () => ({ language: "vi", t: (k: string) => k }),
}));

import { ChatWelcomeScreen } from "../src/components/chat/ChatWelcomeScreen";

describe("ChatWelcomeScreen — nền đồng bộ với khung chung", () => {
  it("khung ngoài không cắt (overflow-hidden) nên không tạo viền chữ nhật lệch màu", () => {
    const { container } = render(<ChatWelcomeScreen onSelectPrompt={vi.fn()} />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).not.toContain("overflow-hidden");
  });

  it("ánh sáng nền là một lớp radial-gradient, không còn các quầng blur lớn dễ bị cắt cạnh", () => {
    const { container } = render(<ChatWelcomeScreen onSelectPrompt={vi.fn()} />);
    const glow = container.querySelector('[aria-hidden="true"][class*="radial-gradient"]');
    expect(glow).not.toBeNull();
    expect(container.querySelector('[class*="blur-3xl"]')).toBeNull();
  });

  it("vẫn gửi câu hỏi gợi ý khi bấm", () => {
    const onSelectPrompt = vi.fn();
    render(<ChatWelcomeScreen onSelectPrompt={onSelectPrompt} />);
    fireEvent.click(screen.getByText("Học bổng & Khen thưởng"));
    expect(onSelectPrompt).toHaveBeenCalledTimes(1);
  });
});

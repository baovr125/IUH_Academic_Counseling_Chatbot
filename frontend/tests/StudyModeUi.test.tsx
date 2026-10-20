import React from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { StudyMode } from "../src/components/flashcards/StudyMode";
import type { BackendCardItem } from "../src/services/flashcardService";

const deck = { id: "d", title: "Deck", lang_code: "en" } as any;
const card = (n: number): BackendCardItem => ({
  id: `c${n}`, deck_id: "d", term: `term${n}`, definition: `nghĩa ${n}`, lang_code: "en", recommended_mode: "flip", part_of_speech: "noun"
});

function setup(queue: BackendCardItem[]) {
  const props = {
    deck, studyQueue: queue, stats: { total: 4, new: 2, due: 1, learning: 1, mastered: 0, weak: 0 },
    onRateFSRS: vi.fn(async () => {}), onVerifySpelling: vi.fn(), onPlayAudio: vi.fn(), onPrefetchAudio: vi.fn(),
    isPlayingAudio: false, onOpenAddCard: vi.fn(), onBackToDecks: vi.fn(), onNextSession: vi.fn()
  };
  render(<MemoryRouter><StudyMode {...(props as any)} /></MemoryRouter>);
  return props;
}

describe("StudyMode — giao diện", () => {
  it("nhóm chế độ ôn tập: nút đang chọn có aria-pressed, đổi chế độ cập nhật trạng thái", () => {
    setup([card(1)]);
    const group = screen.getByRole("group", { name: "Chế độ ôn tập" });
    expect(within(group).getByRole("button", { name: "Tự động" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(within(group).getByRole("button", { name: "Gõ từ" }));
    expect(within(group).getByRole("button", { name: "Gõ từ" })).toHaveAttribute("aria-pressed", "true");
    expect(within(group).getByRole("button", { name: "Tự động" })).toHaveAttribute("aria-pressed", "false");
  });

  it("thanh tiến độ phiên báo đúng vị trí thẻ cho trình đọc màn hình", async () => {
    setup([card(1), card(2)]);
    const bar = screen.getByRole("progressbar", { name: "Tiến độ phiên ôn tập" });
    expect(bar).toHaveAttribute("aria-valuenow", "1");
    expect(bar).toHaveAttribute("aria-valuemax", "2");
    fireEvent.click(screen.getByText(/Bấm vào thẻ/));
    fireEvent.click(screen.getByRole("button", { name: /Tốt/ }));
    await waitFor(() => expect(screen.getByRole("progressbar", { name: "Tiến độ phiên ôn tập" })).toHaveAttribute("aria-valuenow", "2"));
  });

  it("mặt trước chỉ có từ; lật thẻ hiện mặt sau và đủ 4 nút chấm điểm có phím tắt", () => {
    setup([card(1)]);
    expect(screen.getByText("term1")).toBeInTheDocument();
    expect(screen.queryByText("nghĩa 1")).toBeNull();
    expect(screen.queryByRole("button", { name: /Quên/ })).toBeNull();

    fireEvent.click(screen.getByText(/Bấm vào thẻ/));
    expect(screen.getByText("nghĩa 1")).toBeInTheDocument();
    for (const [grade, label] of [[1, "Quên"], [2, "Khó"], [3, "Tốt"], [4, "Dễ"]] as const) {
      const btn = screen.getByRole("button", { name: new RegExp(label) });
      expect(btn).toHaveAttribute("title", `Phím tắt: ${grade}`);
    }
  });

  it("mỗi mặt thẻ có hiệu ứng lật và tắt được khi người dùng chọn giảm chuyển động", () => {
    setup([card(1)]);
    const front = screen.getByText("term1").closest("div");
    expect(front?.className).toContain("animate-flip-in");
    expect(front?.className).toContain("motion-reduce:animate-none");
  });

  it("phím tắt vẫn hoạt động: Space lật, 1-4 chấm điểm", async () => {
    const p = setup([card(1)]);
    fireEvent.keyDown(window, { code: "Space", key: " " });
    expect(await screen.findByText("nghĩa 1")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "4" });
    await waitFor(() => expect(p.onRateFSRS).toHaveBeenCalledWith("c1", 4));
  });
});

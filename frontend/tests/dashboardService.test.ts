import { beforeEach, describe, expect, it, vi } from "vitest";

const svc = vi.hoisted(() => ({ fetchReviewStreak: vi.fn() }));
vi.mock("../src/services/flashcardService", () => svc);
vi.mock("../src/services/utils", () => ({ delay: async () => {} }));

import { fetchDashboardStats } from "../src/services/dashboardService";
import { getMockDashboardStats } from "../src/mock/mockData";

const user = { id: "u1", email: "a@b.c", name: "A", role: "student" } as any;
const days = (n = 84) => Array.from({ length: n }, (_, i) => ({ date: `2026-01-${String((i % 28) + 1).padStart(2, "0")}`, count: i % 3, intensity: (i % 3) as 0 | 1 | 2 }));

beforeEach(() => {
  svc.fetchReviewStreak.mockReset(); // chú ý: không trả về mock từ beforeEach (Vitest coi hàm trả về là cleanup và gọi nó)
});

describe("fetchDashboardStats", () => {
  it("uses real review activity for the heatmap and the streak", async () => {
    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: { days: days(), current_streak: 5, longest_streak: 9, today_reviews: 17, total_reviews: 100 } });
    const res = await fetchDashboardStats(user);
    expect(res.ok).toBe(true);
    if (!res.ok) return;
    expect(res.data.streakDays).toBe(5);
    expect(res.data.streakSource).toBe("live");
    expect("flashcardSummary" in res.data).toBe(false); // số liệu Flashcard do useFlashcardOverview lấy, không còn dữ liệu mẫu ở đây
    expect(res.data.streak).toHaveLength(84);
    expect(res.data.gpaScore).toBe(getMockDashboardStats(user).gpaScore); // phần chưa có nguồn dữ liệu vẫn là dữ liệu mẫu
  });

  it("keeps the sample data when the request fails or returns the wrong shape", async () => {
    const sample = getMockDashboardStats(user);
    svc.fetchReviewStreak.mockResolvedValue({ ok: false, error: { message: "x" } });
    const failed = await fetchDashboardStats(user);
    expect(failed.ok && failed.data.streakDays).toBe(sample.streakDays);
    expect(failed.ok && failed.data.streakSource).toBe("sample");

    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: { days: days(10), current_streak: 1, longest_streak: 1, today_reviews: 1, total_reviews: 1 } });
    const short = await fetchDashboardStats(user);
    expect(short.ok && short.data.streak).toHaveLength(84); // không nhận mảng sai độ dài
  });

  it("survives a thrown error", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    svc.fetchReviewStreak.mockImplementation(() => {
      throw new Error("network");
    });
    const res = await fetchDashboardStats(user);
    expect(res.ok).toBe(true);
    expect(res.ok && res.data.streakDays).toBe(getMockDashboardStats(user).streakDays);
    expect(res.ok && res.data.streakSource).toBe("sample");
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("does not call the API for guests", async () => {
    const res = await fetchDashboardStats(null);
    expect(res.ok).toBe(true);
    expect(svc.fetchReviewStreak).not.toHaveBeenCalled();
    expect(res.ok && res.data.streakSource).toBe("sample");
  });
});

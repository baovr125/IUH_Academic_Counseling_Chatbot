import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

const svc = vi.hoisted(() => ({ fetchLanguageSummary: vi.fn(), fetchReviewStreak: vi.fn() }));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
const auth = vi.hoisted(() => ({ user: null as any }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: auth.user }) }));

import { getMockDashboardStats } from "../src/mock/mockData";
vi.mock("../src/hooks/useDashboard", () => ({
  useDashboard: () => ({ stats: getMockDashboardStats(auth.user), isLoading: false, error: null, refresh: () => {} })
}));
// Các khối không liên quan đến Flashcard được thay bằng chỗ giữ chỗ để test chỉ tập trung vào việc phân vai trò.
for (const name of ["QuickTranslateWidget", "RecentWorkspaceTabs", "StudentAcademicKpiCard", "PublicLearningProductivityCard", "LearningStreakHeatmap", "IuhAcademicCalendarWidget", "AdmissionAndEventsWidget", "DashboardHeroBanner"]) {
  vi.mock(`../src/components/dashboard/${name}`, () => ({ [name]: () => null }));
}

import DashboardPage from "../src/pages/DashboardPage";
import { LANG_CODES } from "../src/services/deckStorage";

const summary = {
  languages: LANG_CODES.map((c) => ({ code: c, learnable: c !== "vi", decks: 0, cards: c === "en" ? 5 : 0, new: 0, due: c === "en" ? 3 : 0, mastered: 0, weak: 0 })),
  unconfirmed: { decks: [], cards: 0 }
};

const renderPage = () =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("DashboardPage — mọi vai trò đều có thẻ ôn tập từ vựng", () => {
  beforeEach(() => {
    svc.fetchLanguageSummary.mockResolvedValue({ ok: true, data: summary });
    svc.fetchReviewStreak.mockResolvedValue({ ok: true, data: { days: [], current_streak: 1, longest_streak: 1, today_reviews: 2, today_cards: 2, total_reviews: 2 } });
  });

  it.each(["student", "public", "admin"])("vai trò %s có đúng một thẻ ôn tập với số liệu thật", async (role) => {
    auth.user = { id: "u1", role, studentCode: role === "student" ? "20045211" : undefined };
    renderPage();
    const card = await screen.findAllByTestId("flashcard-due-card");
    expect(card).toHaveLength(1);
    expect(await screen.findByRole("button", { name: /Bắt đầu Ôn tập Ngay/ })).toHaveTextContent("Tiếng Anh");
    expect(card[0]).toHaveTextContent("3 từ cần ôn");
    // Vai trò không phải sinh viên: thẻ Dịch thuật PDF cũ đã được thay bằng thẻ ôn tập, thẻ Tư vấn Tuyển sinh bên phải vẫn còn.
    if (role !== "student") {
      expect(screen.queryByText("Dịch thuật PDF & Document RAG")).toBeNull();
      expect(screen.getByText("Tư vấn Tuyển sinh & Khám phá IUH")).toBeInTheDocument();
    }
  });
});

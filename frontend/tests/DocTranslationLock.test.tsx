import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { getMockDashboardStats } from "../src/mock/mockData";
import { RecentWorkspaceTabs } from "../src/components/dashboard/RecentWorkspaceTabs";
import { DashboardHeroBanner } from "../src/components/dashboard/DashboardHeroBanner";
import TranslationPage from "../src/pages/TranslationPage";
import { AppRouter } from "../src/router/AppRouter";

// Các phần nặng không liên quan đến việc khóa được thay bằng chỗ giữ chỗ.
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ isAuthenticated: true, isLoading: false, user: null }) }));
vi.mock("../src/components/layout/MainLayout", () => ({ MainLayout: () => <Outlet /> }));
vi.mock("../src/components/translation/TranslationBox", () => ({ TranslationBox: () => null }));
vi.mock("../src/hooks/useTranslation", () => ({
  useTranslation: () => ({
    sourceLang: "en",
    targetLang: "vi",
    sourceText: "",
    setSourceLang: () => {},
    setTargetLang: () => {},
    setSourceText: () => {},
    swapLanguages: () => {},
  }),
}));
vi.mock("../src/pages/DocumentTranslationPage", () => ({ default: () => <div>TRANG-DICH-TAI-LIEU</div> }));
vi.mock("../src/pages/ChatPage", () => ({ default: () => null }));
vi.mock("../src/pages/DashboardPage", () => ({ default: () => null }));
vi.mock("../src/pages/FlashcardPage", () => ({ default: () => null }));
vi.mock("../src/pages/LoginPage", () => ({ default: () => null }));
vi.mock("../src/pages/ProfilePage", () => ({ default: () => null }));
vi.mock("../src/pages/SettingsPage", () => ({ default: () => null }));
vi.mock("../src/pages/AdminPage", () => ({ default: () => null }));

const stats = getMockDashboardStats(null);
const lockDocs = () => vi.stubEnv("VITE_FEATURE_DOC_TRANSLATION", "false");

function Where() {
  return <div data-testid="where">{useLocation().pathname}</div>;
}

describe("Khóa tính năng Dịch tài liệu", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("mặc định (chưa đặt cờ): vẫn hiện tab và nút Dịch tài liệu", () => {
    render(
      <MemoryRouter>
        <RecentWorkspaceTabs stats={stats} isStudent={false} />
        <DashboardHeroBanner user={null} stats={stats} isStudent={false} />
        <TranslationPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/Tài liệu Dịch gần đây/)).toBeInTheDocument();
    expect(screen.getByText("Dịch tài liệu PDF")).toBeInTheDocument();
    expect(screen.getByText("Dịch Tài Liệu")).toBeInTheDocument();
  });

  it("khi khóa: Dashboard chỉ còn tab Chat và không còn nút dịch PDF", () => {
    lockDocs();
    render(
      <MemoryRouter>
        <RecentWorkspaceTabs stats={stats} isStudent={false} />
        <DashboardHeroBanner user={null} stats={stats} isStudent={false} />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Tài liệu Dịch gần đây/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Xem tất cả tài liệu/)).not.toBeInTheDocument();
    expect(screen.queryByText("Dịch tài liệu PDF")).not.toBeInTheDocument();
    expect(screen.getByText(/Phiên Tư vấn Chat/)).toBeInTheDocument();
  });

  it("khi khóa: trang Translation không còn nút Dịch Tài Liệu", () => {
    lockDocs();
    render(
      <MemoryRouter>
        <TranslationPage />
      </MemoryRouter>
    );
    expect(screen.queryByText("Dịch Tài Liệu")).not.toBeInTheDocument();
    expect(screen.getByText("Sổ Thẻ Flashcard")).toBeInTheDocument();
  });

  it("khi khóa: vào thẳng /translation-doc bị chuyển về /translation", () => {
    lockDocs();
    render(
      <MemoryRouter initialEntries={["/translation-doc"]}>
        <AppRouter />
        <Routes>
          <Route path="*" element={<Where />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.queryByText("TRANG-DICH-TAI-LIEU")).not.toBeInTheDocument();
    expect(screen.getByTestId("where")).toHaveTextContent("/translation");
    expect(screen.getByTestId("where")).not.toHaveTextContent("/translation-doc");
  });

  it("mặc định: /translation-doc vẫn mở trang Dịch tài liệu", () => {
    render(
      <MemoryRouter initialEntries={["/translation-doc"]}>
        <AppRouter />
      </MemoryRouter>
    );
    expect(screen.getByText("TRANG-DICH-TAI-LIEU")).toBeInTheDocument();
  });
});

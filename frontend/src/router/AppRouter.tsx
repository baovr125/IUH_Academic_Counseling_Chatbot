import { Navigate, Route, Routes } from "react-router-dom";
import { MainLayout } from "../components/layout/MainLayout";
import ChatPage from "../pages/ChatPage";
import DashboardPage from "../pages/DashboardPage";
import TranslationPage from "../pages/TranslationPage";
import DocumentTranslationPage from "../pages/DocumentTranslationPage";
import FlashcardPage from "../pages/FlashcardPage";
import LoginPage from "../pages/LoginPage";
import ProfilePage from "../pages/ProfilePage";
import SettingsPage from "../pages/SettingsPage";
import AnalyticsPage from "../pages/AnalyticsPage";
import { useAuth } from "../hooks/useAuth";

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <MainLayout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/translation" element={<TranslationPage />} />
        <Route path="/translation-doc" element={<DocumentTranslationPage />} />
        <Route path="/flashcards" element={<FlashcardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}



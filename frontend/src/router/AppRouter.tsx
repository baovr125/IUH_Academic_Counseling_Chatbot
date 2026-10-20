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
import AdminPage from "../pages/AdminPage";
import { useAuth } from "../hooks/useAuth";

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  // Tránh việc điều hướng khi vẫn đang kiểm tra token
  if (isLoading) return null; // Hoặc một component Loading spinner nhỏ nếu cần

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

/** Chỉ cho vai trò admin vào route con. Đây chỉ là tiện ích giao diện — quyền thật được server kiểm tra. */
function RequireAdmin({ children }: { children: React.ReactElement }) {
  const { user } = useAuth();
  if (user?.role !== "admin") return <Navigate to="/dashboard" replace />;
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
        {/* /flashcards -> chọn ngôn ngữ; /flashcards/:lang -> bộ sưu tập; /flashcards/:lang/decks/:deckId -> chi tiết sổ */}
        <Route path="/flashcards" element={<FlashcardPage />} />
        <Route path="/flashcards/:lang" element={<FlashcardPage />} />
        <Route path="/flashcards/:lang/decks/:deckId" element={<FlashcardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminPage />
            </RequireAdmin>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}



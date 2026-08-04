import { BrowserRouter } from "react-router-dom";
import { AuthContext, useAuthState } from "./hooks/useAuth";
import { SettingsProvider } from "./context/SettingsContext";
import { AppRouter } from "./router/AppRouter";

export default function App() {
  const auth = useAuthState();

  return (
    <AuthContext.Provider value={auth}>
      <SettingsProvider>
        <BrowserRouter>
          <AppRouter />
        </BrowserRouter>
      </SettingsProvider>
    </AuthContext.Provider>
  );
}


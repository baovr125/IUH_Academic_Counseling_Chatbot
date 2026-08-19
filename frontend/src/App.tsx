import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext, useAuthState } from "./hooks/useAuth";
import { SettingsProvider } from "./context/SettingsContext";
import { AppRouter } from "./router/AppRouter";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  const auth = useAuthState();

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={auth}>
        <SettingsProvider>
          <BrowserRouter>
            <AppRouter />
          </BrowserRouter>
        </SettingsProvider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}



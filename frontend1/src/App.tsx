import { BrowserRouter } from "react-router-dom";
import { AuthContext, useAuthState } from "./hooks/useAuth";
import { AppRouter } from "./router/AppRouter";

export default function App() {
  const auth = useAuthState();

  return (
    <AuthContext.Provider value={auth}>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

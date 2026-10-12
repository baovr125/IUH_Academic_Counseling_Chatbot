import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { applyAppTheme } from "./pages/SettingsPage";
import { installAuthFetchInterceptor } from "./services/apiClient";

// Nạp cài đặt giao diện đã lưu từ localStorage khi khởi tạo trang
const savedTheme = (localStorage.getItem("app_theme") as "light" | "dark" | "system") || "light";
applyAppTheme(savedTheme);

// Mọi API trả 401 khi đang có token (hết hạn/bị thu hồi) sẽ đưa ứng dụng về trạng thái đăng xuất.
installAuthFetchInterceptor();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

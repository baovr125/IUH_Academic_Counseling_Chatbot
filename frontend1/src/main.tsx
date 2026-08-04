import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { applyAppTheme } from "./pages/SettingsPage";

// Nạp cài đặt giao diện đã lưu từ localStorage khi khởi tạo trang
const savedTheme = (localStorage.getItem("app_theme") as "light" | "dark" | "system") || "light";
applyAppTheme(savedTheme);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

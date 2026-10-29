import { GraduationCap, LayoutDashboard, MessageSquare, Languages, Settings, HelpCircle, Database } from "lucide-react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useSettings } from "../../context/SettingsContext";
import { useAuth } from "../../hooks/useAuth";
import { RESET_CHAT_EVENT_NAME } from "../../hooks/useChat";
import { BrandLogo } from "../ui/BrandLogo";

export interface NavItem {
  to: string;
  icon: React.ElementType;
  key: string;
  label: string;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, key: "sidebar.personalHub", label: "Tổng quan Dashboard" },
  { to: "/chat", icon: MessageSquare, key: "sidebar.knowledgeHub", label: "Trợ lý Tư vấn IUH" },
  { to: "/translation", icon: Languages, key: "sidebar.translationStudio", label: "Dịch thuật Đa ngôn ngữ" },
  { to: "/flashcards", icon: GraduationCap, key: "sidebar.languageLab", label: "Sổ thẻ Từ vựng Flashcard" },
  { to: "/admin", icon: Database, key: "sidebar.admin", label: "Quản trị Dữ liệu (Admin)" },
];

/** Dùng chung cho thanh icon (Sidebar) và ngăn kéo di động (MobileNavDrawer). */
export function handleNavClick(targetPath: string) {
  if (targetPath === "/flashcards") {
    window.dispatchEvent(new CustomEvent("reset-flashcard-view"));
  }
  if (targetPath === "/chat") {
    window.dispatchEvent(new CustomEvent(RESET_CHAT_EVENT_NAME));
  }
}

const itemBase = "flex h-12 w-12 cursor-pointer items-center justify-center rounded-2xl transition-all";
const itemActive = "bg-brand-600 text-white shadow-md shadow-brand-600/25";
const itemIdle =
  "text-slate-500 hover:bg-white hover:text-brand-700 hover:shadow-sm dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100";

/**
 * Thanh icon cố định từ `md` trở lên; dưới `md` được thay bằng MobileNavDrawer (mở từ TopBar).
 * Không có nền riêng: dùng chung nền khung với TopBar và trang (xem MainLayout); chỉ có một đường dọc mảnh ở mép phải để ngăn "vùng điều hướng" với "vùng làm việc". Hàng đầu cao 64px (bằng TopBar)
 * chứa logo trơn để logo và tên thương hiệu ở TopBar đọc thành một cụm; bấm logo về trang tổng quan (Dashboard).
 */
export function Sidebar() {
  const { t } = useSettings();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <aside className="hidden h-full w-[72px] flex-shrink-0 select-none flex-col items-center justify-between border-r border-brand-200 pb-4 dark:border-slate-700 md:flex">
      <div className="flex w-full flex-col items-center">
        <NavLink
          to="/dashboard"
          title="IUH Portal AI - Trang tổng quan"
          aria-label="IUH Portal AI"
          className="mb-2 flex h-16 w-full flex-shrink-0 items-center justify-center transition-transform hover:scale-105"
        >
          <BrandLogo className="h-11" alt="IUH" />
        </NavLink>
        <nav className="flex flex-col gap-1.5">
          {NAV_ITEMS.filter((item) => item.to !== "/admin" || user?.role === "admin").map(({ to, icon: Icon, key, label }) => {
            const isCurrentActive = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                title={t(key) || label}
                onClick={() => handleNavClick(to)}
                className={`${itemBase} ${isCurrentActive ? itemActive : itemIdle}`}
              >
                <Icon size={22} strokeWidth={2} />
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="flex flex-col gap-1.5">
        <NavLink
          to="/settings"
          title={t("sidebar.systemSettings") || "Cài đặt hệ thống"}
          className={({ isActive }) => `${itemBase} ${isActive ? itemActive : itemIdle}`}
        >
          <Settings size={22} />
        </NavLink>
        <button
          type="button"
          onClick={() => navigate("/chat")}
          title={t("sidebar.help") || "Trung tâm trợ giúp"}
          className={`${itemBase} ${itemIdle}`}
        >
          <HelpCircle size={22} />
        </button>
      </div>
    </aside>
  );
}

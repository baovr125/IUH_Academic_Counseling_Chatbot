import { GraduationCap, LayoutDashboard, MessageSquare, Languages, Settings, HelpCircle, BarChart2 } from "lucide-react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useSettings } from "../../context/SettingsContext";

interface NavItem {
  to: string;
  icon: React.ElementType;
  key: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, key: "sidebar.personalHub", label: "Tổng quan Dashboard" },
  { to: "/chat", icon: MessageSquare, key: "sidebar.knowledgeHub", label: "Trợ lý Tư vấn IUH" },
  { to: "/translation", icon: Languages, key: "sidebar.translationStudio", label: "Dịch thuật Đa ngôn ngữ" },
  { to: "/flashcards", icon: GraduationCap, key: "sidebar.languageLab", label: "Sổ thẻ Từ vựng Flashcard" },
  { to: "/analytics", icon: BarChart2, key: "sidebar.analytics", label: "Thống kê Học tập" },
];

export function Sidebar() {
  const { t } = useSettings();
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavClick = (targetPath: string) => {
    if (targetPath === "/flashcards") {
      window.dispatchEvent(new CustomEvent("reset-flashcard-view"));
    }
  };

  return (
    <aside className="relative z-30 flex h-full w-16 flex-col items-center justify-between bg-[#152a6e] dark:bg-slate-950 py-4 transition-colors select-none shadow-md flex-shrink-0">
      <div className="flex flex-col items-center gap-2">
        <NavLink
          to="/chat"
          title="IUH Portal AI - Trợ lý Sinh viên"
          className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 font-bold text-white hover:bg-white/20 transition-all hover:scale-105 cursor-pointer shadow-sm"
        >
          E
        </NavLink>
        <nav className="flex flex-col gap-1.5">
          {NAV_ITEMS.map(({ to, icon: Icon, key, label }) => {
            const isCurrentActive = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                title={t(key) || label}
                onClick={() => handleNavClick(to)}
                className={`flex h-11 w-11 items-center justify-center rounded-xl transition-all cursor-pointer ${
                  isCurrentActive
                    ? "bg-orange-500 text-white shadow-md shadow-orange-500/30 scale-105"
                    : "text-blue-200/70 hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100"
                }`}
              >
                <Icon size={20} strokeWidth={2} />
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="flex flex-col gap-1.5">
        <NavLink
          to="/settings"
          title={t("sidebar.systemSettings") || "Cài đặt hệ thống"}
          className={({ isActive }) =>
            `flex h-11 w-11 items-center justify-center rounded-xl transition-all cursor-pointer ${
              isActive
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/30 scale-105"
                : "text-blue-200/70 hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100"
            }`
          }
        >
          <Settings size={20} />
        </NavLink>
        <button
          type="button"
          onClick={() => navigate("/chat")}
          title={t("sidebar.help") || "Trung tâm trợ giúp"}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-blue-200/70 transition-all hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100 cursor-pointer"
        >
          <HelpCircle size={20} />
        </button>
      </div>
    </aside>
  );
}



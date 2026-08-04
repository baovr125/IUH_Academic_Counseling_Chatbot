import { GraduationCap, LayoutDashboard, MessageSquare, Languages, Settings, HelpCircle } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useSettings } from "../../context/SettingsContext";

interface NavItem {
  to: string;
  icon: React.ElementType;
  key: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, key: "sidebar.personalHub" },
  { to: "/chat", icon: MessageSquare, key: "sidebar.knowledgeHub" },
  { to: "/translation", icon: Languages, key: "sidebar.translationStudio" },
  { to: "/flashcards", icon: GraduationCap, key: "sidebar.languageLab" },
];

export function Sidebar() {
  const { t } = useSettings();

  return (
    <aside className="flex h-full w-16 flex-col items-center justify-between bg-[#152a6e] dark:bg-slate-950 py-4 transition-colors">
      <div className="flex flex-col items-center gap-2">
        <NavLink
          to="/chat"
          title={t("sidebar.goToChat")}
          className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 font-bold text-white hover:bg-white/20 transition-colors"
        >
          E
        </NavLink>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, icon: Icon, key }) => (
            <NavLink
              key={to}
              to={to}
              title={t(key)}
              className={({ isActive }) =>
                `flex h-11 w-11 items-center justify-center rounded-xl transition-colors ${
                  isActive
                    ? "bg-orange-500 text-white shadow-md shadow-orange-500/30"
                    : "text-blue-200/70 hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100"
                }`
              }
            >
              <Icon size={20} strokeWidth={2} />
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="flex flex-col gap-1">
        <NavLink
          to="/settings"
          title={t("sidebar.systemSettings")}
          className={({ isActive }) =>
            `flex h-11 w-11 items-center justify-center rounded-xl transition-colors ${
              isActive
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/30"
                : "text-blue-200/70 hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100"
            }`
          }
        >
          <Settings size={20} />
        </NavLink>
        <button
          title={t("sidebar.help")}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-blue-200/70 transition-colors hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:text-slate-100"
        >
          <HelpCircle size={20} />
        </button>
      </div>
    </aside>
  );
}


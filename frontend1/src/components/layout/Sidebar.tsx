import { GraduationCap, LayoutDashboard, MessageSquare, Languages, Settings, HelpCircle } from "lucide-react";
import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Personal Hub" },
  { to: "/chat", icon: MessageSquare, label: "Knowledge Hub" },
  { to: "/translation", icon: Languages, label: "Translation Studio" },
  { to: "/flashcards", icon: GraduationCap, label: "Language Lab" },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-16 flex-col items-center justify-between bg-[#152a6e] py-4">
      <div className="flex flex-col items-center gap-2">
        <NavLink
          to="/chat"
          title="Đến trang Chatbot"
          className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 font-bold text-white hover:bg-white/20 transition-colors"
        >
          E
        </NavLink>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              title={label}
              className={({ isActive }) =>
                `flex h-11 w-11 items-center justify-center rounded-xl transition-colors ${
                  isActive
                    ? "bg-orange-500 text-white shadow-md shadow-orange-500/30"
                    : "text-blue-200/70 hover:bg-white/10 hover:text-white"
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
          title="Cài đặt hệ thống"
          className={({ isActive }) =>
            `flex h-11 w-11 items-center justify-center rounded-xl transition-colors ${
              isActive
                ? "bg-orange-500 text-white shadow-md shadow-orange-500/30"
                : "text-blue-200/70 hover:bg-white/10 hover:text-white"
            }`
          }
        >
          <Settings size={20} />
        </NavLink>
        <button
          title="Help"
          className="flex h-11 w-11 items-center justify-center rounded-xl text-blue-200/70 transition-colors hover:bg-white/10 hover:text-white"
        >
          <HelpCircle size={20} />
        </button>
      </div>
    </aside>
  );
}

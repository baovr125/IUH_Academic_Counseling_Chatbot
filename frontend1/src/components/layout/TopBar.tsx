import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Grid3x3, LogOut, User, Settings, ChevronDown } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

interface TopBarProps {
  title?: string;
}

export function TopBar({ title = "IUH Portal AI" }: TopBarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsMenuOpen(false);
    await logout();
    navigate("/login");
  };

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5">
      <button
        type="button"
        onClick={() => navigate("/chat")}
        className="text-base font-semibold text-[#152a6e] hover:text-blue-700 transition-colors cursor-pointer"
        title="Đến trang Chatbot"
      >
        {title}
      </button>

      <div className="flex items-center gap-3">
        <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Notifications">
          <Bell size={18} />
        </button>
        <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Apps">
          <Grid3x3 size={18} />
        </button>

        {/* User Info & Logout dropdown - click only */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setIsMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 py-1 pl-1 pr-3 transition-colors hover:bg-slate-100"
          >
            <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-blue-600 text-xs font-bold text-white shadow-sm">
              {user?.avatarUrl ? (
                <img src={user.avatarUrl} alt={user.fullName} className="h-full w-full object-cover" />
              ) : (
                <span>{user?.fullName?.charAt(0) ?? "U"}</span>
              )}
            </div>
            <div className="hidden text-left sm:block">
              <div className="text-xs font-semibold leading-none text-slate-800">
                {user?.fullName || "Nguyễn Văn A"}
              </div>
            </div>
            <ChevronDown
              size={14}
              className={`text-slate-400 transition-transform duration-200 ${isMenuOpen ? "rotate-180" : ""}`}
            />
          </button>

          {isMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-1.5 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-xl ring-1 ring-black/5 animate-in fade-in zoom-in-95 duration-150">
              <div className="border-b border-slate-100 px-3 py-2.5">
                <p className="text-xs font-semibold text-slate-800">{user?.fullName || "Nguyễn Văn A"}</p>
                <p className="truncate text-[11px] text-slate-500">{user?.email || "nguyenvana@iuh.edu.vn"}</p>
              </div>

              <div className="py-1">
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate("/profile");
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-slate-700 hover:bg-slate-100"
                >
                  <User size={15} className="text-slate-500" />
                  <span>Thông tin tài khoản</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate("/settings");
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-slate-700 hover:bg-slate-100"
                >
                  <Settings size={15} className="text-slate-500" />
                  <span>Cài đặt hệ thống</span>
                </button>
              </div>

              <div className="border-t border-slate-100 pt-1">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50"
                >
                  <LogOut size={15} className="text-red-500" />
                  <span>Đăng xuất</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

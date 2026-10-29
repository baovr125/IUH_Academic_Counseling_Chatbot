import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bell, Grid3x3, LogOut, Menu, User, Settings, ChevronDown } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { useSettings } from "../../context/SettingsContext";
import { BrandLogo } from "../ui/BrandLogo";

/** Tên trang hiển thị ở thanh trên theo đường dẫn (khóa dịch pageTitle.*). */
const PAGE_TITLE_KEYS: Array<[string, string]> = [
  ["/dashboard", "pageTitle.dashboard"],
  ["/chat", "pageTitle.chat"],
  ["/translation-doc", "pageTitle.translationDoc"],
  ["/translation", "pageTitle.translation"],
  ["/flashcards", "pageTitle.flashcards"],
  ["/profile", "pageTitle.profile"],
  ["/settings", "pageTitle.settings"],
  ["/admin", "pageTitle.admin"],
];

interface TopBarProps {
  title?: string;
  /** Mở ngăn kéo điều hướng (chỉ hiện nút hamburger dưới `md`, nơi thanh icon bị ẩn). */
  onOpenNav?: () => void;
}

export function TopBar({ title, onOpenNav }: TopBarProps) {
  const { user, logout } = useAuth();
  const { t } = useSettings();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const { pathname } = useLocation();
  const titleKey = PAGE_TITLE_KEYS.find(([prefix]) => pathname === prefix || pathname.startsWith(`${prefix}/`))?.[1];
  const pageTitle = title ?? (titleKey ? t(titleKey) : null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    // pointerdown phủ cả chuột lẫn cảm ứng (mousedown chỉ được giả lập sau khi nhả tay trên một số trình duyệt di động).
    document.addEventListener("pointerdown", handleClickOutside);
    return () => document.removeEventListener("pointerdown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsMenuOpen(false);
    await logout();
    navigate("/login");
  };

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between gap-2 px-3 dark:text-slate-100 sm:px-5 md:h-16 md:px-4">
      <div className="flex min-w-0 items-center gap-1">
        {onOpenNav && (
          <button
            type="button"
            onClick={onOpenNav}
            aria-label={t("topbar.openMenu")}
            className="-ml-1 flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-800 md:hidden"
          >
            <Menu size={22} aria-hidden="true" />
          </button>
        )}
        {/* Điện thoại: thanh icon bị ẩn nên logo nằm ở đây; từ md logo nằm ở góc trái của Sidebar. */}
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          aria-label={t("topbar.goToDashboard")}
          className="flex-shrink-0 md:hidden"
        >
          <BrandLogo className="h-8" alt="IUH" />
        </button>
        <div className="min-w-0 pl-1 md:pl-0">
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            title={t("topbar.goToDashboard")}
            className="block max-w-full truncate text-left text-xs font-bold uppercase tracking-wider text-brand-600 transition-colors hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
          >
            {t("topbar.title")}
          </button>
          {pageTitle && (
            <div data-testid="page-title" className="truncate text-base font-bold leading-tight text-slate-900 dark:text-white sm:text-lg md:text-xl">
              {pageTitle}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-shrink-0 items-center gap-3">
        {/* Chuông và lưới ứng dụng chưa có chức năng: ẩn trên màn hình nhỏ cho thanh trên gọn. */}
        <button
          className="hidden rounded-xl p-2 text-slate-500 hover:bg-white dark:text-slate-400 dark:hover:bg-slate-800 transition-colors md:block"
          title={t("topbar.notifications")}
        >
          <Bell size={18} />
        </button>
        <button
          className="hidden rounded-xl p-2 text-slate-500 hover:bg-white dark:text-slate-400 dark:hover:bg-slate-800 transition-colors md:block"
          title={t("topbar.apps")}
        >
          <Grid3x3 size={18} />
        </button>

        {/* User Info & Logout dropdown - click only */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setIsMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-brand-100 bg-white py-1 pl-1 pr-3 shadow-sm [@media(pointer:coarse)]:py-1.5 transition-colors hover:bg-brand-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
          >
            <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-brand-600 text-xs font-bold text-white shadow-sm">
              {user?.avatarUrl ? (
                <img src={user.avatarUrl} alt={user.fullName} className="h-full w-full object-cover" />
              ) : (
                <span>{user?.fullName?.charAt(0) ?? "U"}</span>
              )}
            </div>
            <div className="hidden text-left sm:block">
              <div className="text-xs font-semibold leading-none text-slate-800 dark:text-slate-200">
                {user?.fullName || "Nguyễn Văn A"}
              </div>
            </div>
            <ChevronDown
              size={14}
              className={`text-slate-400 transition-transform duration-200 ${isMenuOpen ? "rotate-180" : ""}`}
            />
          </button>

          {isMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-1.5 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-xl ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-150">
              <div className="border-b border-slate-100 px-3 py-2.5 dark:border-slate-700/60">
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">{user?.fullName || "Nguyễn Văn A"}</p>
                <p className="truncate text-xs sm:text-[11px] text-slate-500 dark:text-slate-400">{user?.email || "nguyenvana@iuh.edu.vn"}</p>
              </div>

              <div className="py-1">
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate("/profile");
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs [@media(pointer:coarse)]:py-3 text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  <User size={15} className="text-slate-500 dark:text-slate-400" />
                  <span>{t("topbar.accountInfo")}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate("/settings");
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs [@media(pointer:coarse)]:py-3 text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  <Settings size={15} className="text-slate-500 dark:text-slate-400" />
                  <span>{t("topbar.systemSettings")}</span>
                </button>
              </div>

              <div className="border-t border-slate-100 pt-1 dark:border-slate-700/60">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs [@media(pointer:coarse)]:py-3 font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                >
                  <LogOut size={15} className="text-red-500 dark:text-red-400" />
                  <span>{t("topbar.logout")}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}


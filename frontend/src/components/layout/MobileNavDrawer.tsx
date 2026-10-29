import { useEffect, useId, useRef } from "react";
import { HelpCircle, Settings, X } from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useSettings } from "../../context/SettingsContext";
import { useAuth } from "../../hooks/useAuth";
import { BrandLogo } from "../ui/BrandLogo";
import { NAV_ITEMS, handleNavClick } from "./Sidebar";

interface MobileNavDrawerProps {
  onClose: () => void;
}

const itemBase = "flex min-h-[44px] items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-colors";
const itemActive = "bg-brand-600 text-white shadow-md shadow-brand-600/25";
const itemIdle =
  "text-slate-600 hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100";

/**
 * Ngăn kéo điều hướng cho màn hình nhỏ (< md), thay cho thanh icon `Sidebar`.
 * Chỉ được render khi đang mở: đóng bằng nút X, bấm nền mờ, phím Esc hoặc khi đổi trang.
 */
export function MobileNavDrawer({ onClose }: MobileNavDrawerProps) {
  const { t } = useSettings();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  // Đổi trang (bấm mục điều hướng, nút Back của trình duyệt...) thì đóng ngăn kéo.
  const initialPath = useRef(location.pathname);
  useEffect(() => {
    if (location.pathname !== initialPath.current) closeRef.current();
  }, [location.pathname]);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    panelRef.current?.querySelector<HTMLElement>("a, button")?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeRef.current();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus?.();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 md:hidden" data-testid="mobile-nav-drawer">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-slate-200 bg-white px-3 py-4 shadow-2xl dark:border-slate-800 dark:bg-slate-950"
      >
        <div className="mb-4 flex items-center justify-between gap-2 px-1">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="flex-shrink-0">
              <BrandLogo className="h-9" />
            </span>
            <span id={titleId} className="truncate text-sm font-extrabold tracking-tight text-brand-800 dark:text-brand-300">
              IUH Portal AI
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.close") || "Đóng"}
            className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-1.5 overflow-y-auto" aria-label="Điều hướng chính">
          {NAV_ITEMS.filter((item) => item.to !== "/admin" || user?.role === "admin").map(({ to, icon: Icon, key, label }) => {
            const isActive = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                onClick={() => handleNavClick(to)}
                aria-current={isActive ? "page" : undefined}
                className={`${itemBase} ${isActive ? itemActive : itemIdle}`}
              >
                <Icon size={20} strokeWidth={2} aria-hidden="true" className="flex-shrink-0" />
                <span className="min-w-0 truncate">{t(key) || label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-3 flex flex-col gap-1.5 border-t border-slate-200 pt-3 dark:border-slate-800">
          <NavLink
            to="/settings"
            className={({ isActive }) => `${itemBase} ${isActive ? itemActive : itemIdle}`}
          >
            <Settings size={20} aria-hidden="true" className="flex-shrink-0" />
            <span className="min-w-0 truncate">{t("sidebar.systemSettings") || "Cài đặt hệ thống"}</span>
          </NavLink>
          <button
            type="button"
            onClick={() => navigate("/chat")}
            className={`${itemBase} ${itemIdle} w-full text-left`}
          >
            <HelpCircle size={20} aria-hidden="true" className="flex-shrink-0" />
            <span className="min-w-0 truncate">{t("sidebar.help") || "Trung tâm trợ giúp"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

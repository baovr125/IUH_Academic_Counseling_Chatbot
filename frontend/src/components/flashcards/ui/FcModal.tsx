import React, { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export type FcModalSize = "sm" | "md" | "lg" | "xl";

const SIZE: Record<FcModalSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-3xl"
};

interface FcModalProps {
  title: React.ReactNode;
  /** Dòng mô tả nhỏ dưới tiêu đề. */
  description?: React.ReactNode;
  /** Ô biểu tượng bên trái tiêu đề (đã có sẵn khung màu, chỉ truyền biểu tượng). */
  icon?: React.ReactNode;
  /** Vùng thêm trong phần đầu, dưới tiêu đề (ví dụ các huy hiệu hạn mức). */
  headerExtra?: React.ReactNode;
  size?: FcModalSize;
  onClose: () => void;
  /**
   * false = đang xử lý, không cho đóng bằng Esc / bấm nền / nút X (tránh bỏ dở một thao tác ghi dữ liệu).
   * Mặc định true.
   */
  dismissible?: boolean;
  /** Nút hành động cố định ở đáy hộp (căn phải). */
  footer?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * Vỏ hộp thoại chung của Flashcard (thay cho 7 hộp tự dựng): role=dialog + aria-modal + aria-labelledby,
 * đóng bằng Esc / bấm nền / nút X, giữ focus trong hộp và trả focus về nơi mở, có dark mode.
 * Khi mở, focus rơi vào ô nhập đầu tiên của nội dung (không phải nút Đóng) để gõ được ngay.
 * Không phụ thuộc SettingsProvider nên dùng được ở mọi nơi (kể cả trong test).
 */
export const FcModal: React.FC<FcModalProps> = ({
  title,
  description,
  icon,
  headerExtra,
  size = "md",
  onClose,
  dismissible = true,
  footer,
  children
}) => {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const dismissibleRef = useRef(dismissible);
  dismissibleRef.current = dismissible;

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    (bodyRef.current?.querySelector<HTMLElement>(FOCUSABLE) ?? panel?.querySelector<HTMLElement>(FOCUSABLE))?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        // Chặn nổi bọt để phím tắt của màn phía sau (ví dụ Esc = quay lại trong chế độ học) không chạy.
        e.stopPropagation();
        if (dismissibleRef.current) onCloseRef.current();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus?.();
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-3 backdrop-blur-sm sm:p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && dismissible) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`flex max-h-[94vh] [@supports(height:100dvh)]:max-h-[94dvh] w-full flex-col rounded-3xl border border-slate-100 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800 ${SIZE[size]}`}
      >
        <div className="border-b border-slate-100 px-5 pb-3 pt-5 dark:border-slate-700 sm:px-6">
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              {icon && (
                <span
                  aria-hidden="true"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300"
                >
                  {icon}
                </span>
              )}
              <div className="min-w-0">
                <h3 id={titleId} className="text-base font-bold text-slate-800 dark:text-slate-100">
                  {title}
                </h3>
                {description && <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{description}</p>}
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              disabled={!dismissible}
              aria-label="Đóng"
              className="shrink-0 rounded-full p-1.5 [@media(pointer:coarse)]:p-3 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-40 dark:hover:bg-slate-700 dark:hover:text-slate-200 dark:text-slate-400"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          {headerExtra && <div className="mt-2.5">{headerExtra}</div>}
        </div>

        <div ref={bodyRef} className="flex-1 overflow-y-auto px-5 py-4 sm:px-6">
          {children}
        </div>

        {footer && (
          <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3.5 dark:border-slate-700 sm:px-6">{footer}</div>
        )}
      </div>
    </div>
  );
};

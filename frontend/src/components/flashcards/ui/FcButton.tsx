import React from "react";
import { Loader2 } from "lucide-react";

/**
 * Nút chuẩn của Flashcard. Một kích cỡ chữ tối thiểu 12 px, bo `rounded-xl`, có sẵn dark mode và vòng focus.
 * - primary: hành động chính của màn hình (mỗi màn nên có một nút primary).
 * - soft: hành động phụ nổi bật nhẹ (ví dụ "Thêm bằng AI").
 * - secondary: viền trắng, dùng cho hành động trung tính / quay lại.
 * - ghost: không viền, dùng trong thanh công cụ và menu.
 * - success: trạng thái đã hoàn tất nhưng vẫn bấm được (ví dụ "Đã thêm - Mở sổ").
 * - softDanger: gợi ý cần chú ý nhưng không hủy hoại (ví dụ "Ôn lại các từ hay quên").
 * - danger: hành động hủy hoại (xóa).
 */
export type FcButtonVariant = "primary" | "soft" | "success" | "softDanger" | "secondary" | "ghost" | "danger";
export type FcButtonSize = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all select-none " +
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 " +
  "disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98] disabled:active:scale-100";

export const FC_BUTTON_VARIANTS: Record<FcButtonVariant, string> = {
  primary: "bg-blue-600 text-white shadow-sm hover:bg-blue-700",
  soft:
    "border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 " +
    "dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50",
  success:
    "border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 " +
    "dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 dark:hover:bg-emerald-900/50",
  softDanger:
    "border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 " +
    "dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-950/70",
  secondary:
    "border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 " +
    "dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
  ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white",
  danger: "bg-rose-600 text-white shadow-sm hover:bg-rose-700"
};

const SIZES: Record<FcButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm"
};

export interface FcButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: FcButtonVariant;
  size?: FcButtonSize;
  /** Biểu tượng đứng trước nhãn. */
  icon?: React.ReactNode;
  /** Đang xử lý: hiện vòng xoay và khóa nút. */
  loading?: boolean;
}

export const FcButton = React.forwardRef<HTMLButtonElement, FcButtonProps>(function FcButton(
  { variant = "secondary", size = "md", icon, loading = false, disabled, className = "", children, type = "button", ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`${BASE} ${FC_BUTTON_VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {loading ? <Loader2 size={size === "sm" ? 14 : 16} className="animate-spin" aria-hidden="true" /> : icon}
      {children}
    </button>
  );
});

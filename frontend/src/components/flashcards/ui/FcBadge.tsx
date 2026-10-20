import React from "react";

/**
 * Quy ước màu theo ý nghĩa (dùng thống nhất trong toàn bộ Flashcard):
 * - blue: thông tin chung / hành động chính
 * - orange: cần ôn, đến hạn (cùng tông với mục đang chọn ở thanh bên)
 * - emerald: đã thuộc, thành công
 * - rose: hay quên, lỗi
 * - sky: từ mới
 * - violet: chỉ dùng cho Trò chơi
 * - amber: cảnh báo, kỷ lục
 * - slate: trung tính
 */
export type FcTone = "slate" | "blue" | "orange" | "emerald" | "rose" | "sky" | "violet" | "amber";

export const FC_TONE_CLASSES: Record<FcTone, string> = {
  slate: "border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300",
  blue: "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300",
  orange: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-800 dark:bg-orange-950/40 dark:text-orange-300",
  emerald: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300",
  rose: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300",
  sky: "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-300",
  violet: "border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-800 dark:bg-violet-950/40 dark:text-violet-300",
  amber: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
};

interface FcBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: FcTone;
  icon?: React.ReactNode;
}

/** Huy hiệu nhỏ dạng viên thuốc. Chữ tối thiểu 12 px để đọc được trên màn hình nhỏ. */
export const FcBadge: React.FC<FcBadgeProps> = ({ tone = "slate", icon, className = "", children, ...rest }) => (
  <span
    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold leading-5 ${FC_TONE_CLASSES[tone]} ${className}`}
    {...rest}
  >
    {icon}
    {children}
  </span>
);

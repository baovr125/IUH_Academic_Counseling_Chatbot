import React from "react";

/**
 * Quy ước màu theo ý nghĩa (dùng thống nhất trong toàn bộ Flashcard):
 * - blue: thông tin chung / hành động chính (màu chủ đạo, token `brand`)
 * - orange: CHỈ cho tín hiệu đặc biệt: cần ôn, đến hạn, streak
 * - emerald: đã thuộc, thành công
 * - rose: hay quên, lỗi
 * - sky: từ mới
 * - amber: cảnh báo, kỷ lục
 * - slate: trung tính
 */
export type FcTone = "slate" | "blue" | "orange" | "emerald" | "rose" | "sky" | "amber";

export const FC_TONE_CLASSES: Record<FcTone, string> = {
  slate: "border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300",
  blue: "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-300",
  orange: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-800 dark:bg-orange-950/40 dark:text-orange-300",
  emerald: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300",
  rose: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300",
  sky: "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-300",
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

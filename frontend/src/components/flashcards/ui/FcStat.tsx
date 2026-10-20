import React from "react";
import type { FcTone } from "./FcBadge";

const ICON_TONE: Record<FcTone, string> = {
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
  blue: "bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-300",
  orange: "bg-orange-50 text-orange-600 dark:bg-orange-950/50 dark:text-orange-300",
  emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-300",
  rose: "bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300",
  sky: "bg-sky-50 text-sky-600 dark:bg-sky-950/50 dark:text-sky-300",
  violet: "bg-violet-50 text-violet-600 dark:bg-violet-950/50 dark:text-violet-300",
  amber: "bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-300"
};

interface FcStatProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  tone?: FcTone;
  hint?: string;
  /** card: ô số liệu trên nền sáng/tối; onDark: ô kính mờ đặt trên banner gradient navy. */
  variant?: "card" | "onDark";
}

/** Ô số liệu: nhãn nhỏ, con số lớn, biểu tượng tùy chọn. */
export const FcStat: React.FC<FcStatProps> = ({ label, value, icon, tone = "blue", hint, variant = "card", className = "", ...rest }) => {
  const onDark = variant === "onDark";
  return (
    <div
      className={
        (onDark
          ? "rounded-2xl bg-white/10 p-4 text-white backdrop-blur-md "
          : "rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-800 ") + className
      }
      {...rest}
    >
      <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-3">
        {icon && (
          <span
            aria-hidden="true"
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${onDark ? "bg-white/15 text-white" : ICON_TONE[tone]}`}
          >
            {icon}
          </span>
        )}
        <div className="min-w-0">
          <p className={`text-2xl font-extrabold leading-none tracking-tight ${onDark ? "text-white" : "text-slate-900 dark:text-slate-100"}`}>{value}</p>
          <p className={`mt-1 text-xs font-semibold ${onDark ? "text-blue-100" : "text-slate-500 dark:text-slate-400"}`}>{label}</p>
        </div>
      </div>
      {hint && <p className={`mt-2 text-xs ${onDark ? "text-blue-100" : "text-slate-500 dark:text-slate-400"}`}>{hint}</p>}
    </div>
  );
};

import React from "react";
import type { FcTone } from "./FcBadge";

const ICON_TONE: Record<FcTone, string> = {
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
  blue: "bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300",
  orange: "bg-orange-50 text-orange-600 dark:bg-orange-950/50 dark:text-orange-300",
  emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-300",
  rose: "bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300",
  sky: "bg-sky-50 text-sky-600 dark:bg-sky-950/50 dark:text-sky-300",
  amber: "bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-300"
};

interface FcStatProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  tone?: FcTone;
  hint?: string;
}

/** Ô số liệu: nhãn nhỏ, con số lớn, biểu tượng tùy chọn. */
export const FcStat: React.FC<FcStatProps> = ({ label, value, icon, tone = "blue", hint, className = "", ...rest }) => {
  return (
    <div
      className={"rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-800 " + className}
      {...rest}
    >
      <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:gap-3">
        {icon && (
          <span
            aria-hidden="true"
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${ICON_TONE[tone]}`}
          >
            {icon}
          </span>
        )}
        <div className="min-w-0">
          <p className="text-2xl font-extrabold leading-none tracking-tight text-slate-900 dark:text-slate-100">{value}</p>
          <p className="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">{label}</p>
        </div>
      </div>
      {hint && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{hint}</p>}
    </div>
  );
};

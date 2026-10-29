import React from "react";

interface FcEmptyProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  /** Biểu tượng lớn (lucide hoặc cờ). */
  icon?: React.ReactNode;
  title: string;
  description?: React.ReactNode;
  /** Các nút hành động; mỗi trạng thái trống chỉ nên có một nút primary. */
  children?: React.ReactNode;
}

/** Trạng thái trống: khung nét đứt, biểu tượng trong ô bo tròn, tiêu đề, mô tả ngắn và nút hành động. */
export const FcEmpty: React.FC<FcEmptyProps> = ({ icon, title, description, children, className = "", ...rest }) => (
  <div
    className={`flex min-h-[260px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center dark:border-slate-600 dark:bg-slate-800/60 sm:p-10 ${className}`}
    {...rest}
  >
    {icon && (
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-300" aria-hidden="true">
        {icon}
      </div>
    )}
    <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">{title}</h3>
    {description && <p className="mt-1.5 max-w-md text-sm text-slate-500 dark:text-slate-400">{description}</p>}
    {children && <div className="mt-5 flex flex-wrap items-center justify-center gap-3">{children}</div>}
  </div>
);

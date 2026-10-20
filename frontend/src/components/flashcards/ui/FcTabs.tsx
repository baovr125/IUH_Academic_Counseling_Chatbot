import React, { useRef } from "react";

export interface FcTabItem<T extends string> {
  value: T;
  label: string;
  icon?: React.ReactNode;
  /** Số hiển thị cạnh nhãn, ví dụ số thẻ trong danh sách. */
  count?: number;
}

interface FcTabsProps<T extends string> {
  tabs: FcTabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
  /** underline: thanh tab gạch chân (điều hướng chính của một màn); pill: nhóm nút nhỏ gọn. */
  variant?: "underline" | "pill";
  className?: string;
}

/** Thanh tab có role=tablist, chọn bằng chuột hoặc phím ← → Home End (roving tabindex). */
export function FcTabs<T extends string>({ tabs, value, onChange, ariaLabel, variant = "underline", className = "" }: FcTabsProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const move = (index: number) => {
    const next = (index + tabs.length) % tabs.length;
    onChange(tabs[next].value);
    refs.current[next]?.focus();
  };

  const onKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === "ArrowRight") move(index + 1);
    else if (e.key === "ArrowLeft") move(index - 1);
    else if (e.key === "Home") move(0);
    else if (e.key === "End") move(tabs.length - 1);
    else return;
    e.preventDefault();
  };

  const underline = variant === "underline";
  const wrapper = underline
    ? "flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-700"
    : "inline-flex rounded-xl bg-slate-100 p-1 dark:bg-slate-900";

  return (
    <div role="tablist" aria-label={ariaLabel} className={`${wrapper} ${className}`}>
      {tabs.map((tab, i) => {
        const active = tab.value === value;
        const style = underline
          ? `-mb-px border-b-2 px-2.5 py-2.5 text-sm sm:px-4 ${
              active
                ? "border-blue-600 text-blue-700 dark:border-blue-400 dark:text-blue-300"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
            }`
          : `rounded-lg px-4 py-1.5 text-xs ${
              active
                ? "bg-white text-blue-600 shadow-sm dark:bg-slate-700 dark:text-blue-300"
                : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
            }`;
        return (
          <button
            key={tab.value}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(tab.value)}
            onKeyDown={(e) => onKeyDown(e, i)}
            className={`flex items-center gap-1.5 whitespace-nowrap font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${style}`}
          >
            {tab.icon && <span className="hidden sm:inline-flex">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`rounded-full px-1.5 text-xs font-bold ${
                  active ? "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-200" : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

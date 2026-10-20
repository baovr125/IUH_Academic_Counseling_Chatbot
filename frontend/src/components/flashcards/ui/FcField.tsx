import React, { useId } from "react";

const CONTROL =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 placeholder-slate-400 transition-colors " +
  "focus:border-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 disabled:opacity-60 " +
  "dark:border-slate-600 dark:bg-slate-900/50 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-blue-400";

interface BaseProps {
  label: string;
  /** Dòng gợi ý nhỏ dưới ô nhập. */
  hint?: React.ReactNode;
  /** Thông báo lỗi của ô nhập (đọc kèm ô nhập bằng aria-describedby). */
  error?: string | null;
}

function Wrapper({ id, label, hint, error, children }: BaseProps & { id: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
        {label}
      </label>
      {children}
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1 text-xs font-semibold text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}
    </div>
  );
}

export interface FcInputProps extends BaseProps, Omit<React.InputHTMLAttributes<HTMLInputElement>, "id"> {
  /** Dùng phông monospace (phiên âm IPA...). */
  mono?: boolean;
}

/** Ô nhập một dòng có nhãn liên kết đúng (htmlFor/id), hỗ trợ hint/lỗi và dark mode. */
export const FcInput = React.forwardRef<HTMLInputElement, FcInputProps>(function FcInput(
  { label, hint, error, mono = false, className = "", ...rest },
  ref
) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <input
        ref={ref}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={`${CONTROL} ${mono ? "font-mono text-xs" : ""} ${className}`}
        {...rest}
      />
    </Wrapper>
  );
});

export interface FcSelectProps extends BaseProps, Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "id"> {}

/** Ô chọn có nhãn liên kết đúng, cùng kiểu với FcInput. */
export const FcSelect = React.forwardRef<HTMLSelectElement, FcSelectProps>(function FcSelect(
  { label, hint, error, className = "", children, ...rest },
  ref
) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} hint={hint} error={error}>
      <select
        ref={ref}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={`${CONTROL} ${className}`}
        {...rest}
      >
        {children}
      </select>
    </Wrapper>
  );
});

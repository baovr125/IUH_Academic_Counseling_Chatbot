import { useId, useState } from "react";
import { AlertCircle, Eye, EyeOff } from "lucide-react";
import { useSettings } from "../../context/SettingsContext";

interface FormFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email" | "tel" | "password";
  required?: boolean;
  error?: string;
  hint?: string;
  placeholder?: string;
  autoComplete?: string;
  inputMode?: "text" | "numeric" | "tel" | "email";
  maxLength?: number;
  disabled?: boolean;
  autoFocus?: boolean;
}

export const inputBase =
  "w-full rounded-lg border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 " +
  "bg-white text-slate-800 placeholder:text-slate-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 " +
  "dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-400 dark:disabled:bg-slate-800 dark:disabled:text-slate-400";
export const inputOk =
  "border-slate-300 focus:border-blue-500 focus:ring-blue-100 dark:border-slate-600 dark:focus:ring-blue-900";
export const inputErr =
  "border-red-500 focus:border-red-500 focus:ring-red-100 dark:border-red-400 dark:focus:ring-red-900";

/**
 * Ô nhập có nhãn gắn đúng với input (htmlFor/id), lỗi được đọc bởi trình đọc màn hình
 * (aria-invalid + aria-describedby) và hỗ trợ chế độ tối. Với type="password" có nút hiện/ẩn.
 */
export function FormField({
  label,
  value,
  onChange,
  type = "text",
  required,
  error,
  hint,
  placeholder,
  autoComplete,
  inputMode,
  maxLength,
  disabled,
  autoFocus,
}: FormFieldProps) {
  const { t } = useSettings();
  const id = useId();
  const [reveal, setReveal] = useState(false);
  const isPassword = type === "password";
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ") || undefined;

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
        {label}
        {required && (
          <span className="ml-0.5 text-red-600 dark:text-red-400" aria-hidden="true">
            *
          </span>
        )}
      </label>
      <div className="relative">
        <input
          id={id}
          type={isPassword && reveal ? "text" : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          inputMode={inputMode}
          maxLength={maxLength}
          disabled={disabled}
          autoFocus={autoFocus}
          required={required}
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`${inputBase} ${error ? inputErr : inputOk} ${isPassword ? "pr-10" : ""}`}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setReveal((prev) => !prev)}
            aria-label={reveal ? t("auth.hidePassword") : t("auth.showPassword")}
            aria-pressed={reveal}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-600 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-slate-300 dark:hover:text-white"
          >
            {reveal ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
          </button>
        )}
      </div>
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1 text-xs text-slate-600 dark:text-slate-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="mt-1 flex items-start gap-1 text-xs font-medium text-red-700 dark:text-red-300">
          <AlertCircle size={14} className="mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </div>
  );
}

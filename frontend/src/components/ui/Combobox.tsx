import { useEffect, useId, useMemo, useRef, useState } from "react";
import { AlertCircle, ChevronDown, X } from "lucide-react";
import { useSettings } from "../../context/SettingsContext";
import { searchNormalize, OTHER } from "../../data/iuhCatalog";
import { inputBase, inputErr, inputOk } from "../auth/FormField";

interface ComboboxProps {
  label: string;
  /** Giá trị đang chọn: một phần tử của `options`, hoặc `OTHER`, hoặc "" (chưa chọn). */
  value: string;
  onChange: (value: string) => void;
  options: string[];
  /** Nếu có, thêm mục cuối danh sách (giá trị trả về là `OTHER`) để người dùng nhập tay. */
  otherLabel?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  hint?: string;
}

/**
 * Dropdown có ô tìm kiếm (mẫu ARIA 1.2 "select-only/editable combobox with list autocomplete").
 * - Gõ để lọc, không phân biệt dấu tiếng Việt/hoa thường ("cong nghe" khớp "Công nghệ").
 * - ↑ ↓ di chuyển, Enter chọn, Esc đóng, Tab/click ra ngoài đóng và giữ lựa chọn cũ.
 */
export function Combobox({
  label,
  value,
  onChange,
  options,
  otherLabel,
  placeholder,
  required,
  disabled,
  error,
  hint,
}: ComboboxProps) {
  const { t } = useSettings();
  const id = useId();
  const listId = `${id}-list`;
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState<string | null>(null); // null = không đang gõ, hiển thị lựa chọn hiện tại
  const [active, setActive] = useState(0);

  const selectedLabel = value === OTHER ? otherLabel ?? "" : value;
  const inputValue = query ?? selectedLabel;

  const items = useMemo(() => {
    const q = query ? searchNormalize(query) : "";
    const matches = q ? options.filter((o) => searchNormalize(o).includes(q)) : options;
    const list = matches.map((o) => ({ key: o, text: o }));
    if (otherLabel) list.push({ key: OTHER, text: otherLabel });
    return list;
  }, [options, query, otherLabel]);
  const matchCount = otherLabel ? items.length - 1 : items.length;

  // Khi danh sách đổi (do gõ), đưa mục active về đầu; mở lại danh sách khi người dùng đang gõ.
  useEffect(() => {
    setActive(0);
  }, [query, options]);

  useEffect(() => {
    if (!open) return;
    document.getElementById(`${id}-opt-${active}`)?.scrollIntoView?.({ block: "nearest" });
  }, [active, open, id]);

  const close = () => {
    setOpen(false);
    setQuery(null);
  };

  const choose = (key: string) => {
    onChange(key);
    close();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (!open) setOpen(true);
        else setActive((i) => Math.min(i + 1, items.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        if (!open) setOpen(true);
        else setActive((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
        // Danh sách đang mở: Enter chọn mục (không submit form). Đang đóng: để form xử lý bình thường.
        if (open && items[active]) {
          e.preventDefault();
          choose(items[active].key);
        }
        break;
      case "Escape":
        if (open) {
          e.preventDefault();
          e.stopPropagation();
          close();
        }
        break;
      case "Tab":
        close();
        break;
      default:
    }
  };

  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined; // hint chỉ hiển thị khi không có lỗi
  const showClear = Boolean(value) && !disabled;

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
          ref={inputRef}
          id={id}
          role="combobox"
          type="text"
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={open && items[active] ? `${id}-opt-${active}` : undefined}
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          value={inputValue}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={(e) => e.currentTarget.select()}
          onClick={() => !disabled && setOpen(true)}
          onBlur={close}
          onKeyDown={onKeyDown}
          className={`${inputBase} ${error ? inputErr : inputOk} pr-16`}
        />
        <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
          {showClear && (
            <button
              type="button"
              aria-label={`${t("common.clear")}: ${label}`}
              // mousedown + preventDefault để ô nhập không mất focus (tránh đóng/mở nhấp nháy)
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onChange("");
                setQuery(null);
                inputRef.current?.focus();
              }}
              className="rounded p-1 text-slate-600 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-300 dark:hover:text-white"
            >
              <X size={14} aria-hidden="true" />
            </button>
          )}
          <ChevronDown size={16} aria-hidden="true" className="pointer-events-none text-slate-600 dark:text-slate-300" />
        </div>

        {open && !disabled && (
          <ul
            id={listId}
            role="listbox"
            aria-label={label}
            className="absolute z-30 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-slate-300 bg-white py-1 text-sm shadow-lg dark:border-slate-600 dark:bg-slate-800"
          >
            {matchCount === 0 && query && (
              <li role="presentation" className="px-3 py-2 text-slate-600 dark:text-slate-300">
                {t("common.noResults")}
              </li>
            )}
            {items.map((item, index) => {
              const selected = item.key === value;
              const isActive = index === active;
              return (
                <li
                  key={item.key}
                  id={`${id}-opt-${index}`}
                  role="option"
                  aria-selected={selected}
                  // mousedown + preventDefault: giữ focus ở ô nhập để onBlur không đóng danh sách trước khi click kịp xử lý
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => choose(item.key)}
                  onMouseEnter={() => setActive(index)}
                  className={`cursor-pointer px-3 py-2 ${
                    item.key === OTHER ? "border-t border-slate-200 italic dark:border-slate-700" : ""
                  } ${
                    isActive
                      ? "bg-brand-100 text-brand-900 dark:bg-brand-900/50 dark:text-brand-100"
                      : "text-slate-800 dark:text-slate-100"
                  } ${selected ? "font-semibold" : ""}`}
                >
                  {item.text}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Thông báo số kết quả cho trình đọc màn hình khi đang gõ */}
      <div aria-live="polite" className="sr-only">
        {open && query ? (matchCount === 0 ? t("common.noResults") : t("common.resultsCount").replace("{n}", String(matchCount))) : ""}
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

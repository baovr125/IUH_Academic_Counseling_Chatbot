import React, { useEffect, useId, useRef, useState } from "react";
import { ChevronDown, MoreHorizontal } from "lucide-react";
import { FcButton, type FcButtonVariant } from "./FcButton";

export interface FcMenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  /** danger: hành động hủy hoại (xóa), tô đỏ. */
  tone?: "default" | "danger";
  /** Ẩn mục (ví dụ thư viện bộ từ chỉ có ở tiếng Anh) mà không phải lọc mảng ở nơi gọi. */
  hidden?: boolean;
}

interface FcMenuProps {
  items: FcMenuItem[];
  /** Nhãn của nút ba chấm cho trình đọc màn hình, ví dụ "Tùy chọn sổ Từ vựng IELTS". Khi có `buttonLabel`, nhãn nhìn thấy được dùng làm tên nút. */
  label: string;
  className?: string;
  /** Có giá trị = nút mở menu là nút chữ có mũi tên ▾ (ví dụ "Thêm từ vựng") thay vì nút ba chấm. */
  buttonLabel?: string;
  buttonIcon?: React.ReactNode;
  buttonVariant?: FcButtonVariant;
}

/**
 * Menu thao tác `⋯`: role=menu / menuitem, mở bằng chuột hoặc phím, di chuyển ↑ ↓ Home End,
 * đóng bằng Esc (trả focus về nút), Tab hoặc bấm ra ngoài. Chặn nổi bọt click để đặt được trong thẻ bấm được.
 */
export const FcMenu: React.FC<FcMenuProps> = ({ items, label, className = "", buttonLabel, buttonIcon, buttonVariant = "primary" }) => {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const menuId = useId();
  const visible = items.filter((i) => !i.hidden);

  useEffect(() => {
    if (!open) return;
    itemRefs.current[0]?.focus();
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  if (visible.length === 0) return null;

  const focusItem = (index: number) => itemRefs.current[(index + visible.length) % visible.length]?.focus();

  const onTriggerKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown" && !open) {
      e.preventDefault();
      setOpen(true);
    }
  };

  const onMenuKeyDown = (e: React.KeyboardEvent) => {
    const current = itemRefs.current.findIndex((el) => el === document.activeElement);
    if (e.key === "ArrowDown") focusItem(current + 1);
    else if (e.key === "ArrowUp") focusItem(current - 1);
    else if (e.key === "Home") focusItem(0);
    else if (e.key === "End") focusItem(visible.length - 1);
    else if (e.key === "Escape") {
      setOpen(false);
      triggerRef.current?.focus();
    } else if (e.key === "Tab") {
      setOpen(false);
      return;
    } else return;
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div ref={rootRef} className={`relative ${className}`} onClick={(e) => e.stopPropagation()}>
      {buttonLabel ? (
        <FcButton
          ref={triggerRef}
          variant={buttonVariant}
          icon={buttonIcon}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-controls={open ? menuId : undefined}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={onTriggerKeyDown}
        >
          {buttonLabel}
          <ChevronDown size={16} aria-hidden="true" className={`transition-transform ${open ? "rotate-180" : ""}`} />
        </FcButton>
      ) : (
        <button
          ref={triggerRef}
          type="button"
          aria-label={label}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-controls={open ? menuId : undefined}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={onTriggerKeyDown}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100"
        >
          <MoreHorizontal size={18} aria-hidden="true" />
        </button>
      )}

      {open && (
        <div
          id={menuId}
          role="menu"
          aria-label={label}
          onKeyDown={onMenuKeyDown}
          className="absolute right-0 top-full z-30 mt-1 min-w-[220px] rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-700 dark:bg-slate-800"
        >
          {visible.map((item, i) => (
            <button
              key={item.key}
              ref={(el) => {
                itemRefs.current[i] = el;
              }}
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                item.onClick();
              }}
              className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm font-medium transition-colors focus:outline-none ${
                item.tone === "danger"
                  ? "text-rose-600 hover:bg-rose-50 focus-visible:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40 dark:focus-visible:bg-rose-950/40"
                  : "text-slate-700 hover:bg-slate-100 focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700 dark:focus-visible:bg-slate-700"
              }`}
            >
              {item.icon && <span aria-hidden="true" className="shrink-0">{item.icon}</span>}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

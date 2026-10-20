import React from "react";
import { AlertTriangle } from "lucide-react";
import { FcButton, FcModal } from "./ui";

interface ConfirmDialogProps {
  title: string;
  /** Nội dung giải thích hậu quả của hành động. */
  message: React.ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  /** danger: hành động hủy hoại (nút xác nhận màu đỏ). */
  tone?: "danger" | "primary";
  isLoading?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

/**
 * Hộp thoại xác nhận trong ứng dụng, thay cho `window.confirm()` của trình duyệt (không đồng bộ giao diện,
 * không có dark mode). Dựa trên `FcModal`: role=dialog, đóng bằng Esc, giữ focus trong hộp.
 * Đang xử lý (`isLoading`) thì không đóng được để không bỏ dở thao tác.
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  confirmLabel,
  cancelLabel = "Hủy",
  tone = "danger",
  isLoading = false,
  onConfirm,
  onCancel
}) => (
  <FcModal
    title={title}
    size="sm"
    onClose={onCancel}
    dismissible={!isLoading}
    footer={
      <>
        <FcButton variant="secondary" onClick={onCancel} disabled={isLoading}>
          {cancelLabel}
        </FcButton>
        <FcButton variant={tone === "danger" ? "danger" : "primary"} loading={isLoading} onClick={() => void onConfirm()}>
          {confirmLabel}
        </FcButton>
      </>
    }
  >
    <div className="flex items-start gap-3">
      {tone === "danger" && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300" aria-hidden="true">
          <AlertTriangle size={20} />
        </span>
      )}
      <div className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">{message}</div>
    </div>
  </FcModal>
);

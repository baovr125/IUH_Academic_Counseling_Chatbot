import React from "react";
import type { BackendDeck } from "../../../services/flashcardService";
import { ConfirmDialog } from "../ConfirmDialog";

interface DeleteDeckModalProps {
  deck: BackendDeck | null;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isLoading?: boolean;
}

export const DeleteDeckModal: React.FC<DeleteDeckModalProps> = ({
  deck,
  onClose,
  onConfirm,
  isLoading = false
}) => {
  if (!deck) return null;

  return (
    <ConfirmDialog
      title="Xác nhận xóa sổ thẻ?"
      message={
        <>
          Bạn có chắc chắn muốn xóa sổ thẻ <strong className="text-slate-800 dark:text-slate-100">"{deck.title}"</strong> cùng toàn bộ thẻ từ vựng bên trong không? Thao tác này không thể hoàn tác.
        </>
      }
      confirmLabel={isLoading ? "Đang xóa..." : "Xác nhận xóa"}
      isLoading={isLoading}
      onConfirm={onConfirm}
      onCancel={onClose}
    />
  );
};

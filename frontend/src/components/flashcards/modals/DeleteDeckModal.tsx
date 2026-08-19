import React from "react";
import { Trash2 } from "lucide-react";
import type { BackendDeck } from "../../../services/flashcardService";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-xl animate-in zoom-in-95 duration-200 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-600 mb-3">
          <Trash2 size={24} />
        </div>
        <h3 className="text-base font-bold text-slate-800">Xác nhận xóa sổ thẻ?</h3>
        <p className="mt-1.5 text-xs text-slate-500">
          Bạn có chắc chắn muốn xóa sổ thẻ <strong className="text-slate-700">"{deck.title}"</strong> cùng toàn bộ thẻ từ vựng bên trong không? Thao tác này không thể hoàn tác.
        </p>
        <div className="mt-5 flex justify-center gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Hủy
          </button>
          <button
            type="button"
            disabled={isLoading}
            onClick={onConfirm}
            className="rounded-xl bg-rose-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-rose-700 shadow-sm disabled:opacity-50 transition-all"
          >
            {isLoading ? "Đang xóa..." : "Xác nhận xóa"}
          </button>
        </div>
      </div>
    </div>
  );
};

import React, { useState } from "react";
import { X } from "lucide-react";
import { LANG_CONFIG } from "../../../services/deckStorage";

interface CreateDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; description?: string; langCode: string }) => Promise<void>;
  isLoading?: boolean;
}

export const CreateDeckModal: React.FC<CreateDeckModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [langCode, setLangCode] = useState("en");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({ title, description: desc, langCode });
    setTitle("");
    setDesc("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-800">Tạo Sổ Từ Vựng Mới</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Ngôn ngữ sổ thẻ (*)</label>
            <select
              value={langCode}
              onChange={(e) => setLangCode(e.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm focus:border-blue-500 focus:bg-white focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Tên sổ thẻ</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={LANG_CONFIG[langCode]?.defaultTitle || "Sổ từ vựng chuyên ngành"}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Mô tả sổ thẻ</label>
            <input
              type="text"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="ví dụ: Từ vựng đọc báo IEEE về Trí tuệ nhân tạo"
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-2xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 shadow-sm disabled:opacity-50 transition-all"
            >
              {isLoading ? "Đang tạo..." : "Tạo Sổ Thẻ"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

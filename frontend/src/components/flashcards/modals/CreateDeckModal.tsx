import React, { useId, useState } from "react";
import { LANG_CONFIG } from "../../../services/deckStorage";
import { FcButton, FcInput, FcModal, FcSelect, LangFlag } from "../ui";

interface CreateDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { title: string; description?: string; langCode: string }) => Promise<void>;
  isLoading?: boolean;
  /** Tạo sổ bên trong một bộ sưu tập ngôn ngữ: ngôn ngữ bị khóa theo bộ sưu tập đó. */
  fixedLang?: string;
}

export const CreateDeckModal: React.FC<CreateDeckModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  fixedLang
}) => {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [pickedLang, setLangCode] = useState("en");
  const [error, setError] = useState<string | null>(null);
  const formId = useId();
  const langCode = fixedLang || pickedLang;

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await onSubmit({ title, description: desc, langCode });
    } catch (err: any) {
      // Giữ hộp thoại mở và báo lỗi thật thay vì im lặng tạo sổ giả.
      setError(err?.message || "Không thể tạo sổ thẻ.");
      return;
    }
    setTitle("");
    setDesc("");
    onClose();
  };

  return (
    <FcModal
      title="Tạo Sổ Từ Vựng Mới"
      onClose={onClose}
      dismissible={!isLoading}
      footer={
        <>
          <FcButton variant="ghost" onClick={onClose} disabled={isLoading}>
            Hủy
          </FcButton>
          <FcButton type="submit" form={formId} variant="primary" loading={isLoading}>
            {isLoading ? "Đang tạo..." : "Tạo Sổ Thẻ"}
          </FcButton>
        </>
      }
    >
      <form id={formId} onSubmit={handleSubmit} className="flex flex-col gap-4">
        {fixedLang ? (
          <div>
            <span id="create-deck-lang-label" className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Ngôn ngữ sổ thẻ (*)
            </span>
            <div
              id="create-deck-lang"
              data-testid="locked-language"
              aria-labelledby="create-deck-lang-label"
              className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-100 px-3.5 py-2.5 text-sm font-semibold text-slate-700 dark:border-slate-600 dark:bg-slate-700/50 dark:text-slate-200"
            >
              <LangFlag lang={fixedLang} size="sm" />
              <span>{LANG_CONFIG[fixedLang]?.label}</span>
              <span className="ml-auto text-xs font-medium text-slate-600 dark:text-slate-300">Theo bộ sưu tập hiện tại</span>
            </div>
          </div>
        ) : (
          <FcSelect label="Ngôn ngữ sổ thẻ (*)" value={langCode} onChange={(e) => setLangCode(e.target.value)}>
            {Object.entries(LANG_CONFIG).filter(([, meta]) => meta.learnable).map(([code, meta]) => (
              <option key={code} value={code}>
                {meta.label}
              </option>
            ))}
          </FcSelect>
        )}

        <FcInput
          label="Tên sổ thẻ"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={LANG_CONFIG[langCode]?.defaultTitle || "Sổ từ vựng chuyên ngành"}
        />
        <FcInput
          label="Mô tả sổ thẻ"
          type="text"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          placeholder="ví dụ: Từ vựng đọc báo IEEE về Trí tuệ nhân tạo"
        />

        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs font-semibold text-red-600 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}
      </form>
    </FcModal>
  );
};

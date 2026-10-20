import React, { useId, useState, useEffect } from "react";
import { LANG_CONFIG } from "../../../services/deckStorage";
import type { BackendDeck } from "../../../services/flashcardService";
import { FcButton, FcInput, FcModal, FcSelect } from "../ui";

interface EditDeckModalProps {
  deck: BackendDeck | null;
  onClose: () => void;
  onSubmit: (data: { id: string; title: string; description?: string; langCode: string }) => Promise<void>;
  isLoading?: boolean;
}

export const EditDeckModal: React.FC<EditDeckModalProps> = ({
  deck,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [langCode, setLangCode] = useState("en");
  const formId = useId();

  useEffect(() => {
    if (deck) {
      setTitle(deck.title || "");
      setDesc(deck.description || "");
      setLangCode(deck.lang_code || deck.langCode || "en");
    }
  }, [deck]);

  if (!deck) return null;

  const originalLang = deck.lang_code || deck.langCode || "en";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    await onSubmit({ id: deck.id, title, description: desc, langCode });
    onClose();
  };

  return (
    <FcModal
      title="Chỉnh Sửa Sổ Thẻ"
      onClose={onClose}
      dismissible={!isLoading}
      footer={
        <>
          <FcButton variant="ghost" onClick={onClose} disabled={isLoading}>
            Hủy
          </FcButton>
          <FcButton type="submit" form={formId} variant="primary" disabled={!title.trim()} loading={isLoading}>
            {isLoading ? "Đang lưu..." : "Cập nhật Sổ Thẻ"}
          </FcButton>
        </>
      }
    >
      <form id={formId} onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <FcSelect label="Ngôn ngữ sổ thẻ (*)" value={langCode} onChange={(e) => setLangCode(e.target.value)}>
            {Object.entries(LANG_CONFIG)
              .filter(([code, meta]) => meta.learnable || code === (deck.lang_code || deck.langCode))
              .map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.label}
                </option>
              ))}
          </FcSelect>
          {langCode !== originalLang && (
            <p role="note" className="mt-1.5 text-xs font-medium text-amber-700 dark:text-amber-300">
              Đổi ngôn ngữ sẽ chuyển toàn bộ thẻ của sổ này sang bộ sưu tập {LANG_CONFIG[langCode]?.viName}.
            </p>
          )}
        </div>

        <FcInput label="Tên sổ thẻ (*)" type="text" required value={title} onChange={(e) => setTitle(e.target.value)} />
        <FcInput label="Mô tả sổ thẻ" type="text" value={desc} onChange={(e) => setDesc(e.target.value)} />
      </form>
    </FcModal>
  );
};

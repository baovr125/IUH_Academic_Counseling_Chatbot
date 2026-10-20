import React, { useId, useState } from "react";
import type { BackendDeck } from "../../../services/flashcardService";
import { FcButton, FcModal } from "../ui";
import { CardFormFields, type CardFormValues } from "./CardFormFields";

interface AddCardModalProps {
  isOpen: boolean;
  deck: BackendDeck;
  onClose: () => void;
  onSubmit: (cardData: {
    deckId: string;
    term: string;
    definition: string;
    phonetic?: string;
    example?: string;
    partOfSpeech: string;
    langCode: string;
  }) => Promise<void>;
  isLoading?: boolean;
}

const EMPTY: CardFormValues = { term: "", definition: "", phonetic: "", example: "", partOfSpeech: "noun" };

export const AddCardModal: React.FC<AddCardModalProps> = ({
  isOpen,
  deck,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [values, setValues] = useState<CardFormValues>(EMPTY);
  const formId = useId();

  if (!isOpen) return null;

  const deckLang = deck.lang_code || deck.langCode || "en";
  const canSubmit = !!values.term.trim() && !!values.definition.trim();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    await onSubmit({
      deckId: deck.id,
      term: values.term.trim(),
      definition: values.definition.trim(),
      phonetic: values.phonetic.trim() || undefined,
      example: values.example.trim() || undefined,
      partOfSpeech: values.partOfSpeech,
      langCode: deckLang
    });

    setValues(EMPTY);
    onClose();
  };

  return (
    <FcModal
      title={`Thêm thẻ mới vào ${deck.title}`}
      onClose={onClose}
      dismissible={!isLoading}
      footer={
        <>
          <FcButton variant="ghost" onClick={onClose} disabled={isLoading}>
            Hủy
          </FcButton>
          <FcButton type="submit" form={formId} variant="primary" disabled={!canSubmit} loading={isLoading}>
            {isLoading ? "Đang lưu..." : "Lưu thẻ"}
          </FcButton>
        </>
      }
    >
      <form id={formId} onSubmit={handleSubmit}>
        <CardFormFields values={values} onChange={(patch) => setValues((v) => ({ ...v, ...patch }))} lang={deckLang} showExamples />
      </form>
    </FcModal>
  );
};

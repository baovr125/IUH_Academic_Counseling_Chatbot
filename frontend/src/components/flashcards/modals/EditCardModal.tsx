import React, { useId, useState, useEffect } from "react";
import type { BackendCardItem } from "../../../services/flashcardService";
import { FcButton, FcModal } from "../ui";
import { CardFormFields, type CardFormValues } from "./CardFormFields";

interface EditCardModalProps {
  card: BackendCardItem | null;
  deckLang?: string;
  onClose: () => void;
  onSubmit: (data: {
    cardId: string;
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

export const EditCardModal: React.FC<EditCardModalProps> = ({
  card,
  deckLang = "en",
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [values, setValues] = useState<CardFormValues>(EMPTY);
  const [cardLang, setCardLang] = useState("en");
  const formId = useId();

  useEffect(() => {
    if (card) {
      setValues({
        term: card.term || "",
        definition: card.definition || "",
        phonetic: card.phonetic || "",
        example: card.example_sentence || card.example || "",
        partOfSpeech: card.part_of_speech || card.partOfSpeech || "noun"
      });
      setCardLang(card.lang_code || card.langCode || deckLang);
    }
  }, [card, deckLang]);

  if (!card) return null;

  const canSubmit = !!values.term.trim() && !!values.definition.trim();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    await onSubmit({
      cardId: card.id,
      deckId: card.deck_id,
      term: values.term.trim(),
      definition: values.definition.trim(),
      phonetic: values.phonetic.trim() || undefined,
      example: values.example.trim() || undefined,
      partOfSpeech: values.partOfSpeech,
      langCode: cardLang
    });

    onClose();
  };

  return (
    <FcModal
      title="Chỉnh sửa thẻ từ vựng"
      onClose={onClose}
      dismissible={!isLoading}
      footer={
        <>
          <FcButton variant="ghost" onClick={onClose} disabled={isLoading}>
            Hủy
          </FcButton>
          <FcButton type="submit" form={formId} variant="primary" disabled={!canSubmit} loading={isLoading}>
            {isLoading ? "Đang cập nhật..." : "Cập nhật thẻ"}
          </FcButton>
        </>
      }
    >
      <form id={formId} onSubmit={handleSubmit}>
        <CardFormFields values={values} onChange={(patch) => setValues((v) => ({ ...v, ...patch }))} lang={cardLang} />
      </form>
    </FcModal>
  );
};

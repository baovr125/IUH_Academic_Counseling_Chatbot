import React, { useState } from "react";
import { X } from "lucide-react";
import type { BackendDeck } from "../../../services/flashcardService";

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

export const AddCardModal: React.FC<AddCardModalProps> = ({
  isOpen,
  deck,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [phonetic, setPhonetic] = useState("");
  const [example, setExample] = useState("");
  const [partOfSpeech, setPartOfSpeech] = useState("noun");

  if (!isOpen) return null;

  const deckLang = deck.lang_code || deck.langCode || "en";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!term.trim() || !definition.trim()) return;

    await onSubmit({
      deckId: deck.id,
      term: term.trim(),
      definition: definition.trim(),
      phonetic: phonetic.trim() || undefined,
      example: example.trim() || undefined,
      partOfSpeech,
      langCode: deckLang
    });

    setTerm("");
    setDefinition("");
    setPhonetic("");
    setExample("");
    setPartOfSpeech("noun");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-xl animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-800">Thêm thẻ mới vào {deck.title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Từ / Cụm từ ngoại ngữ (*)</label>
            <input
              type="text"
              required
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="ví dụ: Implementation"
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nghĩa tiếng Việt (*)</label>
            <input
              type="text"
              required
              value={definition}
              onChange={(e) => setDefinition(e.target.value)}
              placeholder="ví dụ: Sự triển khai, thực hiện"
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Phiên âm IPA</label>
              <input
                type="text"
                value={phonetic}
                onChange={(e) => setPhonetic(e.target.value)}
                placeholder="/ˌɪm.plə.menˈteɪ.ʃən/"
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Từ loại</label>
              <select
                value={partOfSpeech}
                onChange={(e) => setPartOfSpeech(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-xs focus:border-blue-500 focus:outline-none bg-white"
              >
                <option value="noun">Danh từ (Noun)</option>
                <option value="verb">Động từ (Verb)</option>
                <option value="adjective">Tính từ (Adj)</option>
                <option value="phrase">Cụm từ (Phrase)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Câu ví dụ ngữ cảnh</label>
            <input
              type="text"
              value={example}
              onChange={(e) => setExample(e.target.value)}
              placeholder="ví dụ: The implementation of AI in education."
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isLoading || !term.trim() || !definition.trim()}
              className="rounded-xl bg-blue-600 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-700 shadow-sm disabled:opacity-50 transition-all"
            >
              {isLoading ? "Đang lưu..." : "Lưu thẻ"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from "react";
import { X, BookmarkPlus, Plus, Sparkles, Loader2, CheckCircle2, BookOpen } from "lucide-react";
import {
  fetchBackendDecks,
  createBackendDeck,
  createBackendCard,
  type BackendDeck
} from "../../services/flashcardService";
import {
  LANG_CONFIG,
  getDecks,
  createCustomDeck,
  addCardToDeck
} from "../../services/deckStorage";

interface SaveFlashcardModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTerm: string;
  initialDefinition: string;
  initialLangCode: string;
  initialContext?: string;
  initialPhonetic?: string;
  onSuccess?: (deckTitle: string, term: string) => void;
}

export const SaveFlashcardModal: React.FC<SaveFlashcardModalProps> = ({
  isOpen,
  onClose,
  initialTerm,
  initialDefinition,
  initialLangCode,
  initialContext,
  initialPhonetic,
  onSuccess
}) => {
  const [term, setTerm] = useState(initialTerm);
  const [definition, setDefinition] = useState(initialDefinition);
  const [langCode, setLangCode] = useState(initialLangCode || "en");
  const [phonetic, setPhonetic] = useState(initialPhonetic || "");
  const [example, setExample] = useState(initialContext || "");
  
  // Decks list state
  const [decks, setDecks] = useState<BackendDeck[]>([]);
  const [isLoadingDecks, setIsLoadingDecks] = useState(false);
  const [selectedDeckId, setSelectedDeckId] = useState<string>("new");
  
  // New deck fields
  const [newDeckTitle, setNewDeckTitle] = useState("");
  const [newDeckDesc, setNewDeckDesc] = useState("");
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync props when modal opens
  useEffect(() => {
    if (isOpen) {
      setTerm(initialTerm);
      setDefinition(initialDefinition);
      setLangCode(initialLangCode || "en");
      setPhonetic(initialPhonetic || "");
      setExample(initialContext || "");
      setErrorMessage(null);
      loadDecks();
    }
  }, [isOpen, initialTerm, initialDefinition, initialLangCode, initialContext, initialPhonetic]);

  const loadDecks = async () => {
    setIsLoadingDecks(true);
    let availableDecks: BackendDeck[] = [];

    try {
      const res = await fetchBackendDecks();
      if (res.ok && res.data && res.data.length > 0) {
        availableDecks = [...res.data];
      }
    } catch (e) {
      console.warn("fetchBackendDecks failed in modal:", e);
    }

    // Merge with local storage decks so existing decks are ALWAYS available
    const localDecks = getDecks();
    for (const ld of localDecks) {
      if (!availableDecks.some((d) => d.id === ld.id)) {
        availableDecks.push({
          id: ld.id,
          title: ld.title,
          description: ld.description,
          lang_code: ld.langCode,
          langCode: ld.langCode,
          icon_flag: ld.iconFlag,
          cards_count: ld.cards ? ld.cards.length : 0
        });
      }
    }

    setDecks(availableDecks);

    if (availableDecks.length > 0) {
      // Auto-select deck matching language if available, else first deck
      const matchingDeck = availableDecks.find(
        (d) => (d.lang_code || d.langCode) === initialLangCode
      );
      if (matchingDeck) {
        setSelectedDeckId(matchingDeck.id);
      } else {
        setSelectedDeckId(availableDecks[0].id);
      }
    } else {
      setSelectedDeckId("new");
      const meta = LANG_CONFIG[initialLangCode] || { defaultTitle: `Sổ từ vựng ${initialLangCode.toUpperCase()}` };
      setNewDeckTitle(meta.defaultTitle);
    }
    setIsLoadingDecks(false);
  };

  // Update default new deck title when language changes
  const handleLangChange = (newLang: string) => {
    setLangCode(newLang);
    const meta = LANG_CONFIG[newLang] || { defaultTitle: `Sổ từ vựng ${newLang.toUpperCase()}` };
    if (selectedDeckId === "new" || !newDeckTitle) {
      setNewDeckTitle(meta.defaultTitle);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!term.trim() || !definition.trim()) {
      setErrorMessage("Vui lòng nhập đầy đủ Từ vựng và Định nghĩa.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      let targetDeckId = selectedDeckId;
      let targetDeckTitle = "";

      // 1. If creating new deck
      if (selectedDeckId === "new") {
        const meta = LANG_CONFIG[langCode] || { defaultTitle: `Sổ từ vựng ${langCode.toUpperCase()}` };
        const title = newDeckTitle.trim() || meta.defaultTitle;
        const desc = newDeckDesc.trim() || `Sổ thẻ từ vựng ${meta.label || langCode.toUpperCase()}`;

        try {
          const deckRes = await createBackendDeck(title, desc, langCode);
          if (deckRes.ok && deckRes.data) {
            targetDeckId = deckRes.data.id;
            targetDeckTitle = deckRes.data.title;
            // Also register in local storage with the exact same ID
            const localDecks = getDecks();
            if (!localDecks.some((d) => d.id === targetDeckId)) {
              createCustomDeck(langCode, targetDeckTitle, desc, targetDeckId);
            }
          } else {
            const localDeck = createCustomDeck(langCode, title, desc);
            targetDeckId = localDeck.id;
            targetDeckTitle = localDeck.title;
          }
        } catch {
          const localDeck = createCustomDeck(langCode, title, desc);
          targetDeckId = localDeck.id;
          targetDeckTitle = localDeck.title;
        }
      } else {
        const currentDeck = decks.find((d) => d.id === selectedDeckId);
        targetDeckId = selectedDeckId;
        targetDeckTitle = currentDeck?.title || "Sổ thẻ";
      }

      // 2. Create card in target deck (Backend)
      try {
        await createBackendCard({
          deckId: targetDeckId,
          term: term.trim(),
          definition: definition.trim(),
          phonetic: phonetic.trim() || undefined,
          exampleSentence: example.trim() || undefined,
          partOfSpeech: "phrase",
          langCode: langCode
        });
      } catch (e) {
        console.warn("createBackendCard fallback to local storage:", e);
      }

      // 3. Always save to LocalStorage as well to guarantee immediate availability
      addCardToDeck(
        langCode,
        term.trim(),
        definition.trim(),
        example.trim() || undefined,
        "phrase",
        targetDeckId
      );

      // Success
      if (onSuccess) {
        onSuccess(targetDeckTitle, term.trim());
      }
      onClose();
    } catch (err: any) {
      setErrorMessage(err?.message || "Đã xảy ra lỗi khi lưu thẻ.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl bg-white shadow-2xl border border-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-blue-50/80 via-indigo-50/40 to-white px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <BookmarkPlus size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Lưu Từ Vựng Vào Sổ Thẻ</h3>
              <p className="text-xs text-slate-500 font-medium">Tự động phát âm chuẩn AI & học ngắt quãng FSRS</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 flex flex-col gap-4 max-h-[80vh] overflow-y-auto">
          {errorMessage && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-xs font-semibold text-red-600">
              {errorMessage}
            </div>
          )}

          {/* Language Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Ngôn ngữ từ vựng
            </label>
            <select
              value={langCode}
              onChange={(e) => handleLangChange(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/60 px-3.5 py-2.5 text-sm font-semibold text-slate-700 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>

          {/* Term (Front) */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Từ vựng / Cụm từ gốc <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="VD: Artificial Intelligence, Implementation..."
              className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Definition (Back) */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Nghĩa Tiếng Việt <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={2}
              value={definition}
              onChange={(e) => setDefinition(e.target.value)}
              placeholder="VD: Trí tuệ nhân tạo, Sự triển khai..."
              className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none resize-none transition-colors"
            />
          </div>

          {/* Optional: Phonetic & Example */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                Phiên âm IPA (Tùy chọn)
              </label>
              <input
                type="text"
                value={phonetic}
                onChange={(e) => setPhonetic(e.target.value)}
                placeholder="/ˌɪmpləmənˈteɪʃn/"
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-mono text-slate-700 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                Câu ví dụ / Ngữ cảnh (Tùy chọn)
              </label>
              <input
                type="text"
                value={example}
                onChange={(e) => setExample(e.target.value)}
                placeholder="Câu ví dụ thực tế..."
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Target Deck Selection */}
          <div className="mt-2 pt-3 border-t border-slate-100">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Lưu vào Sổ Thẻ</span>
              {isLoadingDecks && <Loader2 size={13} className="animate-spin text-blue-600" />}
            </label>

            <div className="flex flex-col gap-2">
              <select
                value={selectedDeckId}
                onChange={(e) => {
                  setSelectedDeckId(e.target.value);
                  if (e.target.value === "new" && !newDeckTitle) {
                    const meta = LANG_CONFIG[langCode] || { defaultTitle: `Sổ từ vựng ${langCode.toUpperCase()}` };
                    setNewDeckTitle(meta.defaultTitle);
                  }
                }}
                className="w-full rounded-xl border-2 border-blue-100 bg-blue-50/40 px-3.5 py-2.5 text-sm font-bold text-blue-900 focus:border-blue-500 focus:bg-white focus:outline-none cursor-pointer"
              >
                {decks.map((d) => (
                  <option key={d.id} value={d.id}>
                    📁 {d.title} ({(d as any).cards_count || (d as any).cards?.length || 0} từ)
                  </option>
                ))}
                <option value="new">✨ + Tạo Sổ Thẻ Mới Ngay...</option>
              </select>

              {/* If New Deck is selected, show inputs */}
              {selectedDeckId === "new" && (
                <div className="mt-2 rounded-2xl bg-slate-50 p-3.5 border border-slate-200 flex flex-col gap-2.5 animate-in fade-in duration-150">
                  <span className="text-[11px] font-bold text-blue-600 uppercase">Thông tin Sổ thẻ mới</span>
                  <input
                    type="text"
                    required={selectedDeckId === "new"}
                    value={newDeckTitle}
                    onChange={(e) => setNewDeckTitle(e.target.value)}
                    placeholder="Tên sổ thẻ mới..."
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={newDeckDesc}
                    onChange={(e) => setNewDeckDesc(e.target.value)}
                    placeholder="Mô tả sổ thẻ (tùy chọn)..."
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 placeholder-slate-400 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-4 flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !term.trim() || !definition.trim()}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/20 hover:bg-blue-700 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Đang lưu vào Database...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={15} />
                  <span>Lưu vào Sổ Thẻ</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

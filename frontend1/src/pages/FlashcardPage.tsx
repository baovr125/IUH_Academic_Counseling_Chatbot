import { useState, useEffect } from "react";
import { Check, RotateCcw, Plus, ArrowLeft, BookOpen, Trash2, Languages, Sparkles, X, BookmarkPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  getDecks,
  addCardToDeck,
  createCustomDeck,
  deleteDeck,
  LANG_CONFIG,
  type FlashcardDeck,
} from "../services/deckStorage";
import type { Flashcard, FlashcardRating } from "../types";

export default function FlashcardPage() {
  const navigate = useNavigate();
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [selectedDeck, setSelectedDeck] = useState<FlashcardDeck | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  // Modal to add a new card to a specific deck
  const [showAddCardModal, setShowAddCardModal] = useState(false);
  const [addCardLangCode, setAddCardLangCode] = useState("en");
  const [newTerm, setNewTerm] = useState("");
  const [newDef, setNewDef] = useState("");
  const [newExample, setNewExample] = useState("");

  // Modal to create a new deck
  const [showCreateDeckModal, setShowCreateDeckModal] = useState(false);
  const [newDeckLang, setNewDeckLang] = useState("fr");
  const [newDeckTitle, setNewDeckTitle] = useState("");

  const refreshDecks = () => {
    const loaded = getDecks();
    setDecks(loaded);
    if (selectedDeck) {
      const updated = loaded.find((d) => d.id === selectedDeck.id);
      if (updated) setSelectedDeck(updated);
    }
  };

  useEffect(() => {
    refreshDecks();
  }, []);

  // When clicking on a specific Deck
  const handleSelectDeck = (deck: FlashcardDeck) => {
    setSelectedDeck(deck);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const handleBackToDecks = () => {
    setSelectedDeck(null);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const handleFlip = () => {
    setIsFlipped((f) => !f);
  };

  const handleRateCard = (_rating: FlashcardRating) => {
    if (!selectedDeck || selectedDeck.cards.length === 0) return;
    setIsFlipped(false);
    setCurrentIndex((i) => (i + 1) % selectedDeck.cards.length);
  };

  const handleCreateNewCard = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTerm.trim() || !newDef.trim()) return;

    addCardToDeck(
      addCardLangCode,
      newTerm,
      newDef,
      newExample || `Thẻ tự tạo (${LANG_CONFIG[addCardLangCode]?.label || addCardLangCode})`
    );

    setNewTerm("");
    setNewDef("");
    setNewExample("");
    setShowAddCardModal(false);
    refreshDecks();
  };

  const handleCreateNewDeck = (e: React.FormEvent) => {
    e.preventDefault();
    const meta = LANG_CONFIG[newDeckLang] || {
      defaultTitle: `Sổ từ vựng (${newDeckLang.toUpperCase()})`,
    };
    createCustomDeck(
      newDeckLang,
      newDeckTitle || meta.defaultTitle,
      `Sổ thẻ từ vựng ${newDeckLang}`
    );
    setNewDeckTitle("");
    setShowCreateDeckModal(false);
    refreshDecks();
  };

  const handleDeleteDeck = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm("Bạn có chắc muốn xóa sổ thẻ này không?")) {
      deleteDeck(id);
      refreshDecks();
      if (selectedDeck?.id === id) {
        setSelectedDeck(null);
      }
    }
  };

  // ==========================================
  // VIEW 1: STUDY MODE (When a Deck is selected)
  // ==========================================
  if (selectedDeck) {
    const currentCard: Flashcard | undefined =
      selectedDeck.cards[currentIndex % (selectedDeck.cards.length || 1)];

    return (
      <div className="mx-auto flex h-full max-w-2xl flex-col justify-between p-6">
        {/* Study Top Bar */}
        <div className="mb-4 flex items-center justify-between">
          <button
            type="button"
            onClick={handleBackToDecks}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft size={16} />
            <span>Quay lại Sổ thẻ</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-lg">{selectedDeck.iconFlag}</span>
            <h2 className="text-base font-bold text-slate-800">{selectedDeck.title}</h2>
          </div>

          <button
            type="button"
            onClick={() => {
              setAddCardLangCode(selectedDeck.langCode);
              setShowAddCardModal(true);
            }}
            className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
          >
            <Plus size={15} />
            <span>Thêm thẻ mới</span>
          </button>
        </div>

        {/* Study Card Area */}
        {selectedDeck.cards.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <BookOpen size={48} className="mb-3 text-slate-300" />
            <h3 className="text-base font-bold text-slate-700">Sổ thẻ này chưa có từ vựng nào</h3>
            <p className="mt-1 max-w-sm text-xs text-slate-500">
              Bạn có thể thêm từ vựng thủ công vào sổ thẻ này hoặc sang trang Dịch thuật để lưu từ vừa dịch.
            </p>
            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setAddCardLangCode(selectedDeck.langCode);
                  setShowAddCardModal(true);
                }}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700"
              >
                <Plus size={15} />
                <span>Thêm thẻ mới ngay</span>
              </button>
              <button
                type="button"
                onClick={() => navigate("/translation")}
                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                <Languages size={15} />
                <span>Đến Trang Dịch thuật</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-6">
            <div className="w-full">
              <div className="mb-1 flex justify-between text-xs font-medium text-slate-400">
                <span>{selectedDeck.title}</span>
                <span>
                  Thẻ {currentIndex + 1} / {selectedDeck.cards.length}
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-200">
                <div
                  className="h-1.5 rounded-full bg-blue-600 transition-all duration-300"
                  style={{
                    width: `${((currentIndex + 1) / selectedDeck.cards.length) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Interactive Flashcard */}
            {currentCard && (
              <button
                type="button"
                onClick={handleFlip}
                className="flex h-72 w-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 shadow-md transition-all duration-200 hover:shadow-lg active:scale-[0.99]"
              >
                {!isFlipped ? (
                  <div className="flex flex-col items-center text-center">
                    <span className="mb-2 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-semibold text-blue-700">
                      Mặt trước (Nhấp để lật)
                    </span>
                    <span className="text-2xl font-bold text-slate-800">{currentCard.term}</span>
                    {currentCard.partOfSpeech && (
                      <span className="mt-2 text-xs italic text-slate-400">
                        ({currentCard.partOfSpeech})
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center text-center">
                    <span className="mb-2 rounded-full bg-green-50 px-3 py-1 text-[11px] font-semibold text-green-700">
                      Mặt sau (Ý nghĩa)
                    </span>
                    <p className="text-lg font-semibold text-slate-800">{currentCard.definition}</p>
                    {currentCard.example && (
                      <p className="mt-3 max-w-md text-xs italic text-slate-500">
                        "{currentCard.example}"
                      </p>
                    )}
                  </div>
                )}
              </button>
            )}

            {/* Action Buttons */}
            <div className="flex w-full justify-center gap-4">
              <button
                type="button"
                onClick={() => handleRateCard("review_later")}
                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
              >
                <RotateCcw size={16} className="text-amber-500" />
                <span>Học lại sau (Review Later)</span>
              </button>
              <button
                type="button"
                onClick={() => handleRateCard("mastered")}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
              >
                <Check size={16} />
                <span>Đã thuộc (Mastered)</span>
              </button>
            </div>
          </div>
        )}

        {/* Modal: Add card to deck */}
        {showAddCardModal && (
          <AddCardModal
            langCode={addCardLangCode}
            setLangCode={setAddCardLangCode}
            term={newTerm}
            setTerm={setNewTerm}
            def={newDef}
            setDef={setNewDef}
            example={newExample}
            setExample={setNewExample}
            onClose={() => setShowAddCardModal(false)}
            onSubmit={handleCreateNewCard}
          />
        )}
      </div>
    );
  }

  // ==========================================
  // VIEW 2: DECK LIST OVERVIEW (Default)
  // ==========================================
  return (
    <div className="mx-auto max-w-5xl p-6">
      {/* Header */}
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Sổ Thẻ Từ Vựng & Luyện Tập (Flashcard Decks)</h1>
          <p className="mt-1 text-xs text-slate-500">
            Mỗi ngôn ngữ dịch được lưu trữ trong một sổ thẻ riêng biệt. Nhấp chọn từng sổ thẻ để bắt đầu tạo hoặc học flashcards tương ứng.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => {
              setAddCardLangCode("en");
              setShowAddCardModal(true);
            }}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <BookmarkPlus size={16} className="text-blue-600" />
            <span>Thêm từ vựng nhanh</span>
          </button>

          <button
            type="button"
            onClick={() => setShowCreateDeckModal(true)}
            className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            <span>Tạo Sổ thẻ mới</span>
          </button>
        </div>
      </div>

      {/* Grid of Decks */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {decks.map((deck) => (
          <div
            key={deck.id}
            onClick={() => handleSelectDeck(deck)}
            className="group relative flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-blue-300 hover:shadow-md cursor-pointer"
          >
            <div>
              <div className="mb-3 flex items-start justify-between">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-2xl shadow-inner border border-blue-100">
                  {deck.iconFlag}
                </span>

                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                    {deck.cards.length} thẻ
                  </span>
                  {decks.length > 3 && (
                    <button
                      type="button"
                      onClick={(e) => handleDeleteDeck(e, deck.id)}
                      title="Xóa sổ thẻ này"
                      className="rounded-lg p-1 text-slate-300 hover:bg-red-50 hover:text-red-600 transition-colors"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              </div>

              <h3 className="text-base font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                {deck.title}
              </h3>
              <p className="mt-1 text-xs text-slate-500 line-clamp-2">
                {deck.description}
              </p>
            </div>

            <div className="mt-5 border-t border-slate-100 pt-3.5 flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-600 group-hover:underline">
                Học sổ thẻ này →
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setAddCardLangCode(deck.langCode);
                  setShowAddCardModal(true);
                }}
                className="rounded-lg bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:bg-blue-600 hover:text-white transition-colors"
              >
                + Thêm thẻ
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal: Add Card */}
      {showAddCardModal && (
        <AddCardModal
          langCode={addCardLangCode}
          setLangCode={setAddCardLangCode}
          term={newTerm}
          setTerm={setNewTerm}
          def={newDef}
          setDef={setNewDef}
          example={newExample}
          setExample={setNewExample}
          onClose={() => setShowAddCardModal(false)}
          onSubmit={handleCreateNewCard}
        />
      )}

      {/* Modal: Create Deck */}
      {showCreateDeckModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-800">Tạo Sổ thẻ Flashcard mới</h3>
              <button
                type="button"
                onClick={() => setShowCreateDeckModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateNewDeck} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                  Chọn Ngôn Ngữ Sổ Thẻ
                </label>
                <select
                  value={newDeckLang}
                  onChange={(e) => setNewDeckLang(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
                >
                  {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                    <option key={code} value={code}>
                      {meta.flag} {meta.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                  Tên Sổ Thẻ (Tùy chọn)
                </label>
                <input
                  type="text"
                  value={newDeckTitle}
                  onChange={(e) => setNewDeckTitle(e.target.value)}
                  placeholder={LANG_CONFIG[newDeckLang]?.defaultTitle || "Sổ từ vựng"}
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateDeckModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-blue-600 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-700"
                >
                  Tạo Sổ thẻ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Sub-component Modal for Adding Card
function AddCardModal({
  langCode,
  setLangCode,
  term,
  setTerm,
  def,
  setDef,
  example,
  setExample,
  onClose,
  onSubmit,
}: {
  langCode: string;
  setLangCode: (c: string) => void;
  term: string;
  setTerm: (v: string) => void;
  def: string;
  setDef: (v: string) => void;
  example: string;
  setExample: (v: string) => void;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
}) {
  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-800">Thêm từ vựng mới vào Sổ thẻ</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700">
              Ngôn Ngữ Sổ Thẻ Đích
            </label>
            <select
              value={langCode}
              onChange={(e) => setLangCode(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700">
              Từ / Mẫu câu gốc (Mặt trước) *
            </label>
            <input
              type="text"
              required
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Ví dụ: Implementation, 単位登録, Ich möchte..."
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700">
              Ý nghĩa / Bản dịch (Mặt sau) *
            </label>
            <input
              type="text"
              required
              value={def}
              onChange={(e) => setDef(e.target.value)}
              placeholder="Ví dụ: Sự triển khai, Tôi muốn đăng ký tín chỉ..."
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-slate-700">
              Ví dụ ghi chú (Tùy chọn)
            </label>
            <input
              type="text"
              value={example}
              onChange={(e) => setExample(e.target.value)}
              placeholder="Ví dụ câu sử dụng từ này..."
              className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Hủy
            </button>
            <button
              type="submit"
              className="rounded-xl bg-blue-600 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-700"
            >
              Lưu Thẻ
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

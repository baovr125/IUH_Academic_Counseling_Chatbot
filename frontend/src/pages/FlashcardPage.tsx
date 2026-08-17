import { useState } from "react";
import { ArrowLeft, Sparkles, List, Plus } from "lucide-react";
import { LANG_CONFIG } from "../services/deckStorage";
import type { BackendDeck, BackendCardItem } from "../services/flashcardService";
import { useDecks } from "../hooks/flashcards/useDecks";
import { useCards } from "../hooks/flashcards/useCards";
import { useCardMutations } from "../hooks/flashcards/useCardMutations";
import { useFlashcardAudio } from "../hooks/flashcards/useFlashcardAudio";
import { DeckDashboard } from "../components/flashcards/DeckDashboard";
import { StudyMode } from "../components/flashcards/StudyMode";
import { CardListView } from "../components/flashcards/CardListView";
import { CreateDeckModal } from "../components/flashcards/modals/CreateDeckModal";
import { EditDeckModal } from "../components/flashcards/modals/EditDeckModal";
import { DeleteDeckModal } from "../components/flashcards/modals/DeleteDeckModal";
import { AddCardModal } from "../components/flashcards/modals/AddCardModal";
import { EditCardModal } from "../components/flashcards/modals/EditCardModal";

export default function FlashcardPage() {
  // 1. Core State
  const [selectedDeck, setSelectedDeck] = useState<BackendDeck | null>(null);
  const [deckViewTab, setDeckViewTab] = useState<"study" | "list">("study");

  // 2. Modals State
  const [showCreateDeckModal, setShowCreateDeckModal] = useState(false);
  const [editingDeck, setEditingDeck] = useState<BackendDeck | null>(null);
  const [deletingDeck, setDeletingDeck] = useState<BackendDeck | null>(null);
  const [showAddCardModal, setShowAddCardModal] = useState(false);
  const [editingCard, setEditingCard] = useState<BackendCardItem | null>(null);

  // 3. Custom Hooks
  const {
    decks,
    isLoadingDecks,
    createDeck,
    isCreatingDeck,
    updateDeck,
    isUpdatingDeck,
    deleteDeck,
    isDeletingDeck
  } = useDecks();

  const {
    cards,
    isLoadingCards
  } = useCards(selectedDeck?.id, selectedDeck?.lang_code || selectedDeck?.langCode || "en");

  const {
    createCard,
    isCreatingCard,
    updateCard,
    isUpdatingCard,
    deleteCard,
    rateFSRS,
    verifySpelling
  } = useCardMutations(selectedDeck?.id);

  const {
    isPlayingAudio,
    playAudio,
    stopAudio,
    prefetchAudio
  } = useFlashcardAudio();

  // 4. Handlers
  const handleSelectDeck = (deck: BackendDeck) => {
    setSelectedDeck(deck);
    setDeckViewTab("study");
  };

  const handleBackToDecks = () => {
    stopAudio();
    setSelectedDeck(null);
  };

  const handleConfirmDeleteDeck = async () => {
    if (!deletingDeck) return;
    await deleteDeck(deletingDeck.id);
    if (selectedDeck && selectedDeck.id === deletingDeck.id) {
      handleBackToDecks();
    }
    setDeletingDeck(null);
  };

  // =========================================================================
  // VIEW 1: DECK DETAIL (Study Mode & Card List View)
  // =========================================================================
  if (selectedDeck) {
    const langMeta = LANG_CONFIG[selectedDeck.lang_code || selectedDeck.langCode || "en"] || { flag: "🌐", label: "Ngoại ngữ" };

    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col p-6">
        {/* Top Control Bar */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <button
            type="button"
            onClick={handleBackToDecks}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft size={16} />
            <span>Quay lại Sổ thẻ</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-2xl">{selectedDeck.icon_flag || langMeta.flag}</span>
            <div>
              <h2 className="text-base font-bold text-slate-800">{selectedDeck.title}</h2>
              <p className="text-[11px] text-slate-400">{selectedDeck.description}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Tabs */}
            <div className="flex rounded-xl bg-slate-100 p-1 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setDeckViewTab("study")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
                  deckViewTab === "study" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Sparkles size={14} />
                <span>Ôn tập FSRS</span>
              </button>
              <button
                type="button"
                onClick={() => setDeckViewTab("list")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all ${
                  deckViewTab === "list" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <List size={14} />
                <span>Danh sách ({cards.length})</span>
              </button>
            </div>

            <button
              type="button"
              onClick={() => setShowAddCardModal(true)}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Plus size={15} />
              <span>Thêm từ</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Study Mode */}
        {deckViewTab === "study" ? (
          <StudyMode
            deck={selectedDeck}
            studyQueue={cards}
            isLoading={isLoadingCards}
            onRateFSRS={async (cardId, grade) => {
              await rateFSRS({ cardId, grade });
            }}
            onVerifySpelling={verifySpelling}
            onPlayAudio={playAudio}
            onPrefetchAudio={prefetchAudio}
            isPlayingAudio={isPlayingAudio}
            onOpenAddCard={() => setShowAddCardModal(true)}
            onBackToDecks={handleBackToDecks}
          />
        ) : (
          /* Tab 2: Virtualized Card List View */
          <CardListView
            deck={selectedDeck}
            cards={cards}
            isLoading={isLoadingCards}
            onPlayAudio={playAudio}
            onOpenEditCard={(card) => setEditingCard(card)}
            onDeleteCard={async (cardId) => {
              if (confirm("Bạn có chắc chắn muốn xóa thẻ từ vựng này không?")) {
                await deleteCard({ cardId, deckId: selectedDeck.id });
              }
            }}
            onOpenAddCard={() => setShowAddCardModal(true)}
          />
        )}

        {/* Add Card Modal */}
        <AddCardModal
          isOpen={showAddCardModal}
          deck={selectedDeck}
          onClose={() => setShowAddCardModal(false)}
          onSubmit={async (cardData) => {
            await createCard(cardData);
          }}
          isLoading={isCreatingCard}
        />

        {/* Edit Card Modal */}
        <EditCardModal
          card={editingCard}
          deckLang={selectedDeck.lang_code || selectedDeck.langCode || "en"}
          onClose={() => setEditingCard(null)}
          onSubmit={async (updateData) => {
            await updateCard(updateData);
          }}
          isLoading={isUpdatingCard}
        />
      </div>
    );
  }

  // =========================================================================
  // VIEW 2: ALL DECKS DASHBOARD
  // =========================================================================
  return (
    <>
      <DeckDashboard
        decks={decks}
        isLoading={isLoadingDecks}
        onSelectDeck={handleSelectDeck}
        onOpenCreateDeck={() => setShowCreateDeckModal(true)}
        onOpenEditDeck={(deck) => setEditingDeck(deck)}
        onOpenDeleteDeck={(deck) => setDeletingDeck(deck)}
      />

      {/* Create Deck Modal */}
      <CreateDeckModal
        isOpen={showCreateDeckModal}
        onClose={() => setShowCreateDeckModal(false)}
        onSubmit={async (deckData) => {
          await createDeck(deckData);
        }}
        isLoading={isCreatingDeck}
      />

      {/* Edit Deck Modal */}
      <EditDeckModal
        deck={editingDeck}
        onClose={() => setEditingDeck(null)}
        onSubmit={async (deckData) => {
          await updateDeck(deckData);
        }}
        isLoading={isUpdatingDeck}
      />

      {/* Delete Deck Modal */}
      <DeleteDeckModal
        deck={deletingDeck}
        onClose={() => setDeletingDeck(null)}
        onConfirm={handleConfirmDeleteDeck}
        isLoading={isDeletingDeck}
      />
    </>
  );
}

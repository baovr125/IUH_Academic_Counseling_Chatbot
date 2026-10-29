import { useState, useEffect } from "react";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Sparkles, List, Plus, FileSpreadsheet, Zap, AlertTriangle, Gamepad2, ChevronLeft, ChevronRight } from "lucide-react";
import { LANG_CONFIG, isLearnableLang, normalizeLangCode } from "../services/deckStorage";
import type { BackendDeck, BackendCardItem, CommitGeneratedResult, UnconfirmedDeck } from "../services/flashcardService";
import { useDecks } from "../hooks/flashcards/useDecks";
import { useCards } from "../hooks/flashcards/useCards";
import { useStudyQueue } from "../hooks/flashcards/useStudyQueue";
import { useCardMutations } from "../hooks/flashcards/useCardMutations";
import { useFlashcardAudio } from "../hooks/flashcards/useFlashcardAudio";
import { useLanguageSummary } from "../hooks/flashcards/useLanguageCollections";
import { useReviewStreak } from "../hooks/flashcards/useReviewStreak";
import { DeckDashboard } from "../components/flashcards/DeckDashboard";
import { StudyMode } from "../components/flashcards/StudyMode";
import { CardListView } from "../components/flashcards/CardListView";
import { GamesHub } from "../components/flashcards/games/GamesHub";
import { LanguageSelectionGrid } from "../components/flashcards/LanguageSelectionGrid";
import { LanguageLibrary, type LibraryTab } from "../components/flashcards/LanguageLibrary";
import { UnconfirmedDecks } from "../components/flashcards/UnconfirmedDecks";
import { FlashcardHero } from "../components/flashcards/FlashcardHero";
import { FcBadge, FcButton, FcEmpty, FcLoading, FcMenu, FcPage, FcSkeleton, FcTabs, LangFlag } from "../components/flashcards/ui";
import { ConfirmDialog } from "../components/flashcards/ConfirmDialog";
import { CreateDeckModal } from "../components/flashcards/modals/CreateDeckModal";
import { EditDeckModal } from "../components/flashcards/modals/EditDeckModal";
import { DeleteDeckModal } from "../components/flashcards/modals/DeleteDeckModal";
import { AddCardModal } from "../components/flashcards/modals/AddCardModal";
import { EditCardModal } from "../components/flashcards/modals/EditCardModal";
import { ImportExcelModal } from "../components/flashcards/modals/ImportExcelModal";
import { CatalogView } from "../components/flashcards/CatalogView";
import { GenerateVocabModal } from "../components/flashcards/modals/GenerateVocabModal";

/** Đường dẫn: /flashcards -> /flashcards/:lang -> /flashcards/:lang/decks/:deckId. `unconfirmed` chỉ dùng cho sổ cũ chưa rõ ngôn ngữ. */
const UNCONFIRMED = "unconfirmed";

function deckPath(deck: { id: string; lang_code?: string | null; langCode?: string | null; lang_confirmed?: boolean }): string {
  const lang = normalizeLangCode(deck.lang_code || deck.langCode);
  const segment = deck.lang_confirmed === false || !lang ? UNCONFIRMED : lang;
  return `/flashcards/${segment}/decks/${deck.id}`;
}

export default function FlashcardPage() {
  const { lang: langParam, deckId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const isUnconfirmedRoute = langParam === UNCONFIRMED;
  const lang = isUnconfirmedRoute ? null : normalizeLangCode(langParam);
  const invalidLang = !!langParam && !isUnconfirmedRoute && !lang;
  const inDeck = !!deckId;
  const libraryTab: LibraryTab = searchParams.get("tab") === "words" ? "words" : "decks";

  // 1. Modals State
  const [showCreateDeckModal, setShowCreateDeckModal] = useState(false);
  const [editingDeck, setEditingDeck] = useState<BackendDeck | null>(null);
  const [deletingDeck, setDeletingDeck] = useState<BackendDeck | null>(null);
  const [showAddCardModal, setShowAddCardModal] = useState(false);
  const [editingCard, setEditingCard] = useState<BackendCardItem | null>(null);
  const [importingDeck, setImportingDeck] = useState<BackendDeck | null>(null);
  const [showCatalog, setShowCatalog] = useState(false);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [generateTarget, setGenerateTarget] = useState<BackendDeck | null>(null);
  const [sessionId, setSessionId] = useState(0);
  const [deckViewTab, setDeckViewTab] = useState<"study" | "list" | "games">("study");
  const [deletingCard, setDeletingCard] = useState<BackendCardItem | null>(null);
  const [isDeletingCard, setIsDeletingCard] = useState(false);

  // 2. Data hooks. Màn chọn ngôn ngữ chỉ cần số liệu tổng hợp; sổ thẻ chỉ tải khi đã vào một ngôn ngữ.
  const languageSummary = useLanguageSummary();
  const reviewStreak = useReviewStreak();
  const {
    decks,
    isLoadingDecks,
    createDeck,
    isCreatingDeck,
    updateDeck,
    isUpdatingDeck,
    deleteDeck,
    isDeletingDeck
  } = useDecks(lang ?? undefined, !invalidLang && (!!lang || isUnconfirmedRoute));

  const selectedDeck = inDeck ? decks.find((d) => d.id === deckId) ?? null : null;
  const selectedLang = normalizeLangCode(selectedDeck?.lang_code || selectedDeck?.langCode) ?? lang ?? "en";

  const { cards, isLoadingCards } = useCards(selectedDeck?.id, selectedLang);
  const study = useStudyQueue(selectedDeck?.id, cards, isLoadingCards);

  const {
    createCard,
    isCreatingCard,
    updateCard,
    isUpdatingCard,
    deleteCard,
    rateFSRS,
    verifySpelling,
    importExcel,
    isImportingExcel
  } = useCardMutations(selectedDeck?.id);

  const { isPlayingAudio, playAudio, stopAudio, prefetchAudio } = useFlashcardAudio();

  // 3. Handlers
  const goHome = () => {
    stopAudio();
    navigate("/flashcards");
  };
  const goLanguage = (code: string, tab?: LibraryTab) =>
    navigate(`/flashcards/${code}${tab === "words" ? "?tab=words" : ""}`);
  const handleSelectDeck = (deck: BackendDeck) => {
    setDeckViewTab("study");
    navigate(deckPath(deck));
  };
  const handleBackFromDeck = () => {
    stopAudio();
    navigate(lang ? `/flashcards/${lang}` : "/flashcards");
  };

  const openGenerate = (deck?: BackendDeck | null) => {
    setGenerateTarget(deck ?? null);
    setGenerateOpen(true);
  };

  /** Sau khi lưu từ AI: vào học ngay (sổ mới) hoặc làm mới phiên học (thêm vào sổ đang mở). */
  const handleStartLearningFromGenerated = (result: CommitGeneratedResult) => {
    const created = result.deck;
    if (generateTarget) {
      if (selectedDeck?.id === generateTarget.id) {
        void study.refresh().then(() => setSessionId((s) => s + 1));
      } else {
        handleSelectDeck(generateTarget);
      }
      return;
    }
    handleSelectDeck({
      id: created.id,
      title: created.title,
      description: created.description,
      lang_code: created.lang_code || "en",
      icon_flag: created.icon_flag,
      cards_count: result.inserted,
      lang_confirmed: true
    });
  };

  const generateModal = (
    <GenerateVocabModal
      // key: đổi ngôn ngữ/sổ đích thì dựng lại hộp, không giữ kết quả của ngôn ngữ trước (tránh lưu nhầm sổ).
      key={`${generateTarget?.id ?? "new"}-${lang ?? selectedLang}`}
      isOpen={generateOpen}
      targetDeck={generateTarget}
      lang={lang ?? selectedLang}
      onClose={() => setGenerateOpen(false)}
      onStartLearning={handleStartLearningFromGenerated}
    />
  );

  const handleOpenFromCatalog = (deck: BackendDeck) => {
    setShowCatalog(false);
    handleSelectDeck(deck);
  };

  // Bấm biểu tượng Flashcard ở thanh bên: về màn chọn ngôn ngữ (kể cả khi đang ở trang con).
  useEffect(() => {
    const handleReset = () => {
      stopAudio();
      setShowCatalog(false);
      navigate("/flashcards");
    };
    window.addEventListener("reset-flashcard-view", handleReset);
    return () => window.removeEventListener("reset-flashcard-view", handleReset);
  }, [stopAudio, navigate]);

  // Đổi ngôn ngữ/sổ qua URL thì đóng các màn phụ của lần trước.
  useEffect(() => {
    setShowCatalog(false);
  }, [langParam, deckId]);

  const handleConfirmDeleteDeck = async () => {
    if (!deletingDeck) return;
    await deleteDeck(deletingDeck.id);
    if (selectedDeck && selectedDeck.id === deletingDeck.id) {
      handleBackFromDeck();
    }
    setDeletingDeck(null);
  };

  const handleConfirmDeleteCard = async () => {
    if (!deletingCard || !selectedDeck) return;
    setIsDeletingCard(true);
    try {
      await deleteCard({ cardId: deletingCard.id, deckId: selectedDeck.id });
    } finally {
      setIsDeletingCard(false);
      setDeletingCard(null);
    }
  };

  const importModal = importingDeck && (
    <ImportExcelModal
      isOpen={true}
      deck={importingDeck}
      onClose={() => setImportingDeck(null)}
      onImport={async (file) => {
        return await importExcel({
          deckId: importingDeck.id,
          file,
          langCode: normalizeLangCode(importingDeck.lang_code || importingDeck.langCode) ?? ""
        });
      }}
      isLoading={isImportingExcel}
    />
  );

  // =========================================================================
  // Đường dẫn không hợp lệ
  // =========================================================================
  if (invalidLang) return <Navigate to="/flashcards" replace />;
  if (isUnconfirmedRoute && !inDeck) return <Navigate to="/flashcards" replace />;

  // =========================================================================
  // VIEW 3: CHI TIẾT SỔ (học FSRS / danh sách thẻ / trò chơi)
  // =========================================================================
  if (inDeck) {
    if (isLoadingDecks) {
      return (
        <FcPage width="lg">
          <FcLoading label="Đang tải sổ thẻ" className="space-y-4">
            <FcSkeleton className="h-4 w-56" />
            <FcSkeleton className="h-14 w-2/3" />
            <FcSkeleton className="h-72 w-full !rounded-3xl" />
          </FcLoading>
        </FcPage>
      );
    }
    if (!selectedDeck) {
      return (
        <FcPage width="md">
          <FcEmpty
            icon={<AlertTriangle size={30} className="text-amber-500" />}
            title="Không tìm thấy sổ thẻ"
            description="Sổ này không tồn tại, đã bị xóa hoặc không thuộc ngôn ngữ trong đường dẫn."
          >
            <FcButton variant="primary" onClick={handleBackFromDeck}>
              Quay lại
            </FcButton>
          </FcEmpty>
        </FcPage>
      );
    }

    const unconfirmed = selectedDeck.lang_confirmed === false;
    const backLabel = lang ? `Sổ thẻ ${LANG_CONFIG[lang].viName}` : "Quay lại Sổ thẻ";
    const cardCount = isLoadingCards ? selectedDeck.cards_count ?? 0 : cards.length;

    return (
      <FcPage width="lg">
        {unconfirmed && (
          <div
            role="note"
            className="mb-4 flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200"
          >
            <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
            Ngôn ngữ của sổ này chưa được xác nhận, nên nó chưa nằm trong bộ sưu tập nào. Hãy xác nhận ở màn hình chọn ngôn ngữ.
          </div>
        )}

        {/* Tầng 1: đường dẫn + tiêu đề sổ + hành động thêm từ */}
        <nav aria-label="Đường dẫn" className="mb-4 flex min-w-0 items-center gap-1.5 text-sm">
          <button
            type="button"
            onClick={handleBackFromDeck}
            className="flex shrink-0 items-center gap-1 rounded-lg px-1.5 py-1 font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-brand-300"
          >
            <ChevronLeft size={16} aria-hidden="true" />
            {backLabel}
          </button>
          <ChevronRight size={14} className="shrink-0 text-slate-300 dark:text-slate-600" aria-hidden="true" />
          <span aria-current="page" className="truncate font-bold text-slate-800 dark:text-slate-100">
            {selectedDeck.title}
          </span>
        </nav>

        <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-4">
            <LangFlag lang={selectedLang} size="lg" />
            <div className="min-w-0">
              <h1 className="line-clamp-2 break-words text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">{selectedDeck.title}</h1>
              {selectedDeck.description && (
                <p className="mt-0.5 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">{selectedDeck.description}</p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <FcBadge tone="blue">{cardCount} thẻ</FcBadge>
                {selectedDeck.is_default && <FcBadge tone="slate">Mặc định</FcBadge>}
              </div>
            </div>
          </div>

          <FcMenu
            label="Thêm từ vào sổ"
            buttonLabel="Thêm từ vựng"
            buttonIcon={<Plus size={16} />}
            items={[
              { key: "add", label: "Thêm một từ", icon: <Plus size={16} />, onClick: () => setShowAddCardModal(true) },
              { key: "import", label: "Nhập từ Excel / CSV", icon: <FileSpreadsheet size={16} />, onClick: () => setImportingDeck(selectedDeck) },
              // Trình sinh từ bằng AI dùng được cho cả 9 ngôn ngữ học (theo ngôn ngữ của sổ), trừ tiếng Việt
              { key: "ai", label: "Tạo thêm bằng AI", icon: <Zap size={16} />, onClick: () => openGenerate(selectedDeck), hidden: !isLearnableLang(selectedLang) }
            ]}
          />
        </header>

        {/* Tầng 2: các chế độ xem của sổ */}
        <FcTabs
          ariaLabel="Chế độ xem sổ thẻ"
          value={deckViewTab}
          onChange={setDeckViewTab}
          className="mb-6"
          tabs={[
            { value: "study", label: "Ôn tập FSRS", icon: <Sparkles size={15} aria-hidden="true" /> },
            { value: "list", label: "Danh sách", icon: <List size={15} aria-hidden="true" />, count: cards.length },
            { value: "games", label: "Trò chơi", icon: <Gamepad2 size={15} aria-hidden="true" /> }
          ]}
        />

        {/* Tab 1: Study Mode */}
        {deckViewTab === "study" ? (
          study.isLoading ? (
            <FcLoading label="Đang chuẩn bị phiên ôn tập" className="mx-auto w-full max-w-2xl space-y-4">
              <FcSkeleton className="h-8 w-full" />
              <FcSkeleton className="h-72 w-full !rounded-3xl" />
            </FcLoading>
          ) : (
            <StudyMode
              key={`${selectedDeck.id}-${sessionId}`}
              deck={selectedDeck}
              studyQueue={study.queue}
              stats={study.stats}
              onRateFSRS={async (cardId, grade) => {
                await rateFSRS({ cardId, grade });
              }}
              onVerifySpelling={verifySpelling}
              onPlayAudio={playAudio}
              onPrefetchAudio={prefetchAudio}
              isPlayingAudio={isPlayingAudio}
              onOpenAddCard={() => setShowAddCardModal(true)}
              onOpenImportExcel={() => setImportingDeck(selectedDeck)}
              onOpenGenerate={() => openGenerate(selectedDeck)}
              onBackToDecks={handleBackFromDeck}
              onStudyWeak={async () => {
                const found = await study.loadWeak();
                if (found > 0) setSessionId((s) => s + 1);
                return found;
              }}
              onNextSession={async () => {
                await study.refresh();
                setSessionId((s) => s + 1);
              }}
              onSessionFinished={() => void study.refreshStats()}
            />
          )
        ) : deckViewTab === "games" ? (
          /* Tab 3: Trò chơi ôn từ vựng (Ghép cặp / Đua 60 giây / Xếp chữ / Bắn bóng nghĩa) */
          <GamesHub key={selectedDeck.id} deck={selectedDeck} onPlayAudio={playAudio} />
        ) : (
          /* Tab 2: Danh sách thẻ (ảo hóa) */
          <CardListView
            deck={selectedDeck}
            cards={cards}
            isLoading={isLoadingCards}
            onPlayAudio={playAudio}
            onOpenEditCard={(card) => setEditingCard(card)}
            onDeleteCard={(cardId) => setDeletingCard(cards.find((c) => c.id === cardId) ?? null)}
            onOpenAddCard={() => setShowAddCardModal(true)}
            onOpenImportExcel={() => setImportingDeck(selectedDeck)}
          />
        )}

        <AddCardModal
          isOpen={showAddCardModal}
          deck={selectedDeck}
          onClose={() => setShowAddCardModal(false)}
          onSubmit={async (cardData) => {
            await createCard(cardData);
          }}
          isLoading={isCreatingCard}
        />

        <EditCardModal
          card={editingCard}
          deckLang={selectedLang}
          onClose={() => setEditingCard(null)}
          onSubmit={async (updateData) => {
            await updateCard(updateData);
          }}
          isLoading={isUpdatingCard}
        />

        {deletingCard && (
          <ConfirmDialog
            title="Xóa thẻ từ vựng"
            message={
              <>
                Bạn có chắc chắn muốn xóa thẻ <strong className="text-slate-800 dark:text-slate-100">“{deletingCard.term}”</strong> không? Thao tác này không thể hoàn tác.
              </>
            }
            confirmLabel="Xóa thẻ"
            isLoading={isDeletingCard}
            onConfirm={handleConfirmDeleteCard}
            onCancel={() => setDeletingCard(null)}
          />
        )}

        {importModal}
        {generateModal}
      </FcPage>
    );
  }

  // =========================================================================
  // VIEW 2: BỘ SƯU TẬP CỦA MỘT NGÔN NGỮ
  // =========================================================================
  if (lang) {
    if (showCatalog && lang === "en") {
      return <CatalogView onBack={() => setShowCatalog(false)} onOpenDeck={handleOpenFromCatalog} />;
    }
    const stats = languageSummary.summary?.languages.find((l) => l.code === lang);

    return (
      <>
        <LanguageLibrary
          lang={lang}
          tab={libraryTab}
          onTabChange={(tab) => setSearchParams(tab === "words" ? { tab: "words" } : {}, { replace: true })}
          onBack={goHome}
          stats={stats}
          onPlayAudio={playAudio}
          onOpenTranslation={() => navigate("/translation")}
        >
          <DeckDashboard
            lang={lang}
            decks={decks}
            isLoading={isLoadingDecks}
            onSelectDeck={handleSelectDeck}
            onOpenCreateDeck={() => setShowCreateDeckModal(true)}
            onOpenGenerate={(deck) => openGenerate(deck)}
            onOpenCatalog={() => setShowCatalog(true)}
            onOpenEditDeck={(deck) => setEditingDeck(deck)}
            onOpenDeleteDeck={(deck) => setDeletingDeck(deck)}
            onOpenImportExcel={(deck) => setImportingDeck(deck)}
          />
        </LanguageLibrary>

        <CreateDeckModal
          isOpen={showCreateDeckModal}
          fixedLang={lang}
          onClose={() => setShowCreateDeckModal(false)}
          onSubmit={async (deckData) => {
            await createDeck(deckData);
          }}
          isLoading={isCreatingDeck}
        />
        <EditDeckModal
          deck={editingDeck}
          onClose={() => setEditingDeck(null)}
          onSubmit={async (deckData) => {
            await updateDeck(deckData);
          }}
          isLoading={isUpdatingDeck}
        />
        <DeleteDeckModal
          deck={deletingDeck}
          onClose={() => setDeletingDeck(null)}
          onConfirm={handleConfirmDeleteDeck}
          isLoading={isDeletingDeck}
        />
        {generateModal}
        {importModal}
      </>
    );
  }

  // =========================================================================
  // VIEW 1: CHỌN NGÔN NGỮ (10 ngôn ngữ)
  // =========================================================================
  const unconfirmedDecks = languageSummary.summary?.unconfirmed.decks ?? [];
  return (
    <FcPage width="lg">
      <FlashcardHero
        summary={languageSummary.summary}
        isLoading={languageSummary.isLoading}
        isError={languageSummary.isError}
        streak={reviewStreak.streak}
        onStudyLanguage={(code) => goLanguage(code)}
      />

      <LanguageSelectionGrid
        summary={languageSummary.summary}
        isLoading={languageSummary.isLoading}
        isError={languageSummary.isError}
        errorMessage={languageSummary.errorMessage}
        onRetry={() => void languageSummary.refetch()}
        onSelect={(code) => goLanguage(code)}
      />

      <UnconfirmedDecks
        decks={unconfirmedDecks}
        onOpenDeck={(deck: UnconfirmedDeck) => navigate(deckPath({ id: deck.id, lang_confirmed: false }))}
      />
    </FcPage>
  );
}

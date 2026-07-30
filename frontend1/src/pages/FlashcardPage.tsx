import { Check, RotateCcw } from "lucide-react";
import { useFlashcards } from "../hooks/useFlashcards";

export default function FlashcardPage() {
  const { currentCard, progress, isFlipped, isLoading, flip, rate } = useFlashcards();

  if (isLoading || !currentCard || !progress) {
    return <div className="p-6 text-sm text-slate-400">Loading flashcards...</div>;
  }

  return (
    <div className="mx-auto flex h-full max-w-lg flex-col items-center justify-center gap-6 p-6">
      <div className="w-full">
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>{progress.setTitle}</span>
          <span>
            {progress.currentIndex + 1} of {progress.totalCards}
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-slate-100">
          <div
            className="h-1.5 rounded-full bg-blue-600"
            style={{ width: `${((progress.currentIndex + 1) / progress.totalCards) * 100}%` }}
          />
        </div>
      </div>

      <button
        onClick={flip}
        className="flex h-64 w-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm"
      >
        {!isFlipped ? (
          <>
            <span className="text-2xl font-bold text-slate-800">{currentCard.term}</span>
            <span className="mt-1 text-sm italic text-slate-400">{currentCard.partOfSpeech}</span>
          </>
        ) : (
          <div className="px-8 text-center">
            <p className="text-base text-slate-700">{currentCard.definition}</p>
            {currentCard.example && <p className="mt-2 text-sm italic text-slate-400">"{currentCard.example}"</p>}
          </div>
        )}
      </button>

      <div className="flex gap-3">
        <button
          onClick={() => rate("review_later")}
          className="flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          <RotateCcw size={15} /> Review Later
        </button>
        <button
          onClick={() => rate("mastered")}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm text-white hover:bg-blue-700"
        >
          <Check size={15} /> Mastered
        </button>
      </div>
    </div>
  );
}

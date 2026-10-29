import React, { useEffect, useRef, useState } from "react";
import { Volume2, CheckCircle2, XCircle, ListChecks, Headphones } from "lucide-react";
import type { BackendCardItem } from "../../services/flashcardService";
import { FcBadge, FcButton, FcCard } from "./ui";

interface ChoiceQuestionProps {
  card: BackendCardItem;
  choices: string[];
  /** choice: hiện từ, chọn nghĩa. listening: ẩn từ, chỉ nghe rồi chọn nghĩa. */
  variant: "choice" | "listening";
  isPlayingAudio: boolean;
  onPlay: () => void;
  /** Gọi khi người học bấm "Tiếp tục" sau khi đã chọn đáp án. */
  onFinish: (correct: boolean) => void;
}

const normalize = (s: string) => s.trim().toLowerCase();

export const ChoiceQuestion: React.FC<ChoiceQuestionProps> = ({
  card,
  choices,
  variant,
  isPlayingAudio,
  onPlay,
  onFinish
}) => {
  const [selected, setSelected] = useState<string | null>(null);
  const answered = selected !== null;
  const correct = answered && normalize(selected) === normalize(card.definition);
  const playRef = useRef(onPlay);
  playRef.current = onPlay;

  // Thẻ nghe: phát âm ngay khi hiện câu hỏi.
  useEffect(() => {
    if (variant === "listening") {
      const timer = window.setTimeout(() => playRef.current(), 250);
      return () => window.clearTimeout(timer);
    }
  }, [variant, card.id]);

  // Phím 1-4 chọn đáp án, Enter/Space sang thẻ kế.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select") return;
      if (!answered) {
        const index = Number(e.key) - 1;
        if (index >= 0 && index < choices.length) {
          e.preventDefault();
          setSelected(choices[index]);
        }
      } else if (e.key === "Enter") {
        e.preventDefault();
        onFinish(correct);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [answered, choices, correct, onFinish]);

  const revealTerm = variant === "choice" || answered;

  return (
    <FcCard padding="lg" className="w-full">
      <div className="mb-4 flex items-center justify-between gap-2">
        <FcBadge tone="blue" icon={variant === "choice" ? <ListChecks size={13} aria-hidden="true" /> : <Headphones size={13} aria-hidden="true" />}>
          {variant === "choice" ? "Trắc nghiệm: chọn nghĩa đúng" : "Thử thách nghe: chọn nghĩa đúng"}
        </FcBadge>
        <FcButton variant="soft" size="sm" onClick={onPlay} title="Nghe phát âm (R)" icon={<Volume2 size={14} className={isPlayingAudio ? "animate-pulse" : ""} />}>
          Nghe (R)
        </FcButton>
      </div>

      <div className="my-5 text-center">
        {revealTerm ? (
          <>
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">{card.term}</h2>
            {card.phonetic && <p className="mt-1.5 font-mono text-sm text-brand-600 dark:text-brand-300">{card.phonetic}</p>}
            {card.part_of_speech && (
              <FcBadge tone="slate" className="mt-2 uppercase tracking-wider">
                {card.part_of_speech}
              </FcBadge>
            )}
          </>
        ) : (
          <button
            type="button"
            onClick={onPlay}
            aria-label="Phát lại âm thanh"
            className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-brand-600 text-white shadow-md transition-transform hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-800"
          >
            <Volume2 size={34} className={isPlayingAudio ? "animate-pulse" : ""} />
          </button>
        )}
      </div>

      <div className="grid gap-2.5" role="group" aria-label="Các đáp án">
        {choices.map((choice, index) => {
          const isAnswer = normalize(choice) === normalize(card.definition);
          const isPicked = selected === choice;
          let style = "border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:bg-brand-50/50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-brand-500 dark:hover:bg-slate-700";
          if (answered) {
            if (isAnswer) style = "border-emerald-400 bg-emerald-50 text-emerald-800 dark:border-emerald-500 dark:bg-emerald-950/40 dark:text-emerald-200";
            else if (isPicked) style = "border-rose-400 bg-rose-50 text-rose-800 animate-[shake_0.3s_ease-in-out] dark:border-rose-500 dark:bg-rose-950/40 dark:text-rose-200";
            else style = "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400";
          }
          return (
            <button
              key={`${index}-${choice}`}
              type="button"
              disabled={answered}
              onClick={() => setSelected(choice)}
              className={`flex items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left text-sm font-semibold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${style}`}
            >
              <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-slate-100 text-xs font-bold text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                {index + 1}
              </span>
              <span className="flex-1">{choice}</span>
              {answered && isAnswer && <CheckCircle2 size={18} className="text-emerald-600 dark:text-emerald-400" aria-hidden="true" />}
              {answered && isPicked && !isAnswer && <XCircle size={18} className="text-rose-600 dark:text-rose-400" aria-hidden="true" />}
            </button>
          );
        })}
      </div>

      {answered && (
        <div className="mt-4 flex flex-col gap-3">
          <p role="status" className={`text-center text-sm font-bold ${correct ? "text-emerald-700 dark:text-emerald-300" : "text-rose-700 dark:text-rose-300"}`}>
            {correct ? "Chính xác!" : `Chưa đúng. Đáp án: ${card.definition}`}
          </p>
          {card.example_sentence && (
            <p className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-center text-xs italic text-slate-600 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-300">
              "{card.example_sentence}"
              {card.example_translation && <span className="mt-1 block not-italic text-slate-500 dark:text-slate-400">{card.example_translation}</span>}
            </p>
          )}
          <FcButton variant="primary" autoFocus onClick={() => onFinish(correct)} className="w-full !rounded-2xl py-3">
            Tiếp tục (Enter)
          </FcButton>
        </div>
      )}
    </FcCard>
  );
};

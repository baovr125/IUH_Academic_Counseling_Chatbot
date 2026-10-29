import React, { useEffect, useMemo, useRef, useState } from "react";
import { X, BookmarkPlus, Loader2, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { createBackendDeck, fetchBackendDecks, type BackendDeck } from "../../services/flashcardService";
import { LANG_CONFIG } from "../../services/deckStorage";
import {
  buildFlashcardDraft,
  describeOrigin,
  languageLabel,
  resolveLearnChoice,
  type DraftInput,
  type ReadyDraft,
} from "../../services/flashcardDraft";
import { invalidateFlashcardQueries, newRequestId, saveWordToCollection } from "../../services/flashcardSave";
import { extractFlashcard, translateText } from "../../services/translationService";

export interface SavedInfo {
  term: string;
  langCode: string;
  deckTitle: string;
  /** true = chưa lên máy chủ, mới lưu tạm trên thiết bị. */
  pending: boolean;
  /** false = cập nhật thẻ đã có. */
  created: boolean;
}

interface SaveFlashcardModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Dữ liệu bản dịch hiện tại; ngôn ngữ và hai mặt của thẻ được suy ra bởi buildFlashcardDraft. */
  input: DraftInput | null;
  /** Lĩnh vực đang dùng (chỉ để AI chọn nghĩa đúng ngữ cảnh). */
  domain?: string;
  onSaved?: (info: SavedInfo) => void;
}

const NEW_DECK = "__new__";
const SHORT_TERM_MAX = 40;

export const SaveFlashcardModal: React.FC<SaveFlashcardModalProps> = ({ isOpen, onClose, input, domain = "", onSaved }) => {
  const { user } = useAuth();
  const userId = user?.id;

  const [userSource, setUserSource] = useState<string | null>(null);
  const [learnChoice, setLearnChoice] = useState<string | null>(null);

  const [term, setTerm] = useState("");
  const [meaning, setMeaning] = useState("");
  const [phonetic, setPhonetic] = useState("");
  const [example, setExample] = useState("");
  const [exampleTranslation, setExampleTranslation] = useState("");
  const [partOfSpeech, setPartOfSpeech] = useState("");
  const touched = useRef<Set<string>>(new Set());

  const [decks, setDecks] = useState<BackendDeck[]>([]);
  const [isLoadingDecks, setIsLoadingDecks] = useState(false);
  const [deckChoice, setDeckChoice] = useState<string>("");
  const [newDeckTitle, setNewDeckTitle] = useState("");

  const [isFilling, setIsFilling] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [duplicate, setDuplicate] = useState<{ deckTitle?: string; deckId?: string; definition: string } | null>(null);

  const outcome = useMemo(
    () => (input ? buildFlashcardDraft({ ...input, userSource }) : null),
    [input, userSource]
  );
  const ready: ReadyDraft | null = useMemo(() => {
    if (!outcome) return null;
    if (outcome.status === "ready") return outcome;
    if (outcome.status === "choose-learn" && learnChoice) return resolveLearnChoice(outcome, learnChoice);
    return null;
  }, [outcome, learnChoice]);
  const lang = ready?.langCode ?? null;
  const langMeta = lang ? LANG_CONFIG[lang] : null;

  // Mở modal mới (hoặc dữ liệu đầu vào đổi): bắt đầu lại, không giữ lựa chọn của lần trước.
  useEffect(() => {
    if (isOpen) {
      setUserSource(null);
      setLearnChoice(null);
      setErrorMessage(null);
      setDuplicate(null);
      setDeckChoice("");
      setNewDeckTitle("");
    }
  }, [isOpen, input]);

  // Mỗi khi chốt xong ngôn ngữ/thẻ: nạp các trường biểu mẫu và nhờ AI điền phần còn thiếu.
  const draftKey = ready ? `${ready.langCode}|${ready.termSide}|${ready.term}` : "";
  useEffect(() => {
    if (!isOpen || !ready) return;
    touched.current = new Set();
    setTerm(ready.term);
    setMeaning(ready.meaning);
    setPhonetic("");
    setExample(ready.example);
    setExampleTranslation("");
    setPartOfSpeech("");
    setErrorMessage(null);
    setDuplicate(null);

    const controller = new AbortController();
    const fillUnlessEdited = (field: string, value: string | undefined, set: (v: string) => void) => {
      if (value && value.trim() && !touched.current.has(field)) set(value.trim());
    };
    const run = async () => {
      setIsFilling(true);
      try {
        if (ready.translateMeaningFrom) {
          const res = await translateText({
            sourceText: ready.translateMeaningFrom.text,
            sourceLang: ready.translateMeaningFrom.lang as any,
            targetLang: "vi",
          } as any);
          if (controller.signal.aborted) return;
          if (res.ok && res.data?.translatedText) fillUnlessEdited("meaning", res.data.translatedText, setMeaning);
        }
        // AI: nghĩa (cho từ bôi đen) + phiên âm theo quy ước của ngôn ngữ. Bỏ qua với câu dài.
        if (ready.needsExtraction || ready.term.length <= SHORT_TERM_MAX) {
          const res = await extractFlashcard(ready.term, ready.example || ready.term, domain, ready.langCode, controller.signal);
          if (controller.signal.aborted) return;
          if (res.ok && res.data) {
            if (ready.needsExtraction) fillUnlessEdited("meaning", res.data.meaning, setMeaning);
            fillUnlessEdited("phonetic", res.data.phonetic, setPhonetic);
            fillUnlessEdited("partOfSpeech", res.data.part_of_speech, setPartOfSpeech);
            if (!ready.example) {
              fillUnlessEdited("example", res.data.example, setExample);
              fillUnlessEdited("exampleTranslation", res.data.example_translation, setExampleTranslation);
            }
          }
        }
      } catch {
        /* AI chỉ hỗ trợ điền sẵn; người dùng vẫn nhập tay được. */
      } finally {
        if (!controller.signal.aborted) setIsFilling(false);
      }
    };
    void run();
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, draftKey]);

  // Chỉ liệt kê sổ cùng ngôn ngữ (lọc ở máy chủ) và đã xác nhận ngôn ngữ.
  useEffect(() => {
    if (!isOpen || !lang) {
      setDecks([]);
      return;
    }
    let cancelled = false;
    setIsLoadingDecks(true);
    void fetchBackendDecks(lang).then((res) => {
      if (cancelled) return;
      setDecks(res.ok ? (res.data || []).filter((d) => d.lang_confirmed !== false && !d.is_system) : []);
      setDeckChoice("");
      setIsLoadingDecks(false);
    });
    return () => {
      cancelled = true;
    };
  }, [isOpen, lang]);

  const edit = (field: string, set: (v: string) => void) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    touched.current.add(field);
    set(e.target.value);
  };

  const submit = async (onDuplicate: "reject" | "update" = "reject") => {
    if (!ready || !lang) return;
    if (!term.trim() || !meaning.trim()) {
      setErrorMessage("Vui lòng nhập đầy đủ từ vựng và nghĩa tiếng Việt.");
      return;
    }
    setIsSaving(true);
    setErrorMessage(null);
    try {
      let deckId = deckChoice || undefined;
      if (deckChoice === NEW_DECK) {
        const title = newDeckTitle.trim() || LANG_CONFIG[lang].defaultTitle;
        const created = await createBackendDeck(title, undefined, lang);
        if (!created.ok) {
          setErrorMessage(created.error.message);
          return;
        }
        deckId = created.data.id;
      }

      const detection = input && ready.origin === "detected" ? input.detection : null;
      const result = await saveWordToCollection(
        {
          clientRequestId: newRequestId(),
          sourceLang: lang,
          term: term.trim(),
          translation: meaning.trim(),
          phonetic: phonetic.trim() || undefined,
          example: example.trim() || undefined,
          exampleTranslation: exampleTranslation.trim() || undefined,
          partOfSpeech: partOfSpeech.trim() || undefined,
          deckId,
          onDuplicate,
          detection: detection
            ? { status: detection.status ?? undefined, engine: detection.engine ?? undefined, confidence: detection.confidence ?? undefined }
            : undefined,
        },
        userId
      );

      if (result.kind === "saved") {
        onSaved?.({ term: term.trim(), langCode: lang, deckTitle: result.deckTitle, pending: false, created: result.created });
        onClose();
      } else if (result.kind === "pending") {
        invalidateFlashcardQueries();
        onSaved?.({ term: term.trim(), langCode: lang, deckTitle: result.deckTitle, pending: true, created: true });
        onClose();
      } else if (result.kind === "duplicate") {
        setDuplicate({ deckTitle: result.deckTitle, deckId: result.deckId, definition: result.existing.definition });
      } else {
        setErrorMessage(result.message);
      }
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const canSave = !!ready && !isSaving && term.trim() !== "" && meaning.trim() !== "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="save-flashcard-title"
        className="relative flex max-h-[calc(100vh-2rem)] [@supports(height:100dvh)]:max-h-[calc(100dvh-2rem)] w-full max-w-lg flex-col rounded-3xl bg-white shadow-2xl border border-slate-100 overflow-hidden dark:bg-slate-800 dark:border-slate-700"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-brand-50/80 via-brand-50/40 to-white px-6 py-4 dark:border-slate-700 dark:from-brand-950/40 dark:via-brand-950/20 dark:to-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-md shadow-brand-500/20">
              <BookmarkPlus size={20} />
            </div>
            <div>
              <h3 id="save-flashcard-title" className="text-base font-bold text-slate-800 dark:text-slate-100">Lưu từ vựng vào Flashcard</h3>
              <p className="text-xs text-slate-500 font-medium dark:text-slate-400">Từ ngoại ngữ → nghĩa tiếng Việt, lưu đúng bộ sưu tập ngôn ngữ</p>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Đóng" className="rounded-full p-2 [@media(pointer:coarse)]:p-3 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors dark:hover:bg-slate-700 dark:hover:text-slate-200">
            <X size={18} />
          </button>
        </div>

        <div className="p-4 sm:p-6 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto">
          {/* Không đủ điều kiện lưu */}
          {outcome?.status === "unsupported" && (
            <div role="alert" className="flex gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-semibold text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <span>{outcome.message}</span>
            </div>
          )}

          {/* Chưa rõ ngôn ngữ nguồn: bắt buộc hỏi, không đoán */}
          {outcome?.status === "choose-source" && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-800 dark:bg-amber-950/30">
              <p className="flex items-start gap-2 text-xs font-semibold text-amber-900 dark:text-amber-200">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>
                  {outcome.reason === "uncertain"
                    ? "Hệ thống chưa chắc chắn về ngôn ngữ của văn bản này."
                    : "Chưa xác định được ngôn ngữ của văn bản này."}{" "}
                  Hãy chọn ngôn ngữ của từ cần lưu để thẻ vào đúng bộ sưu tập:
                </span>
              </p>
              <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Chọn ngôn ngữ nguồn">
                {outcome.options.map((code) => (
                  <button
                    key={code}
                    type="button"
                    onClick={() => setUserSource(code)}
                    className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 hover:border-brand-400 hover:bg-brand-50 dark:border-amber-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-brand-950/50 dark:hover:border-brand-500"
                  >
                    {languageLabel(code)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Cặp ngoại ngữ -> ngoại ngữ: chọn ngôn ngữ muốn học */}
          {outcome?.status === "choose-learn" && (
            <div className="rounded-2xl border border-brand-200 bg-brand-50/60 p-4 dark:border-brand-800 dark:bg-brand-950/30">
              <p className="flex items-start gap-2 text-xs font-semibold text-brand-900 dark:text-brand-200">
                <Info size={16} className="mt-0.5 shrink-0" />
                <span>Bản dịch này giữa hai ngoại ngữ. Bạn muốn học từ vựng ở ngôn ngữ nào? Nghĩa tiếng Việt sẽ được dịch tự động.</span>
              </p>
              <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label="Chọn ngôn ngữ muốn học">
                {outcome.options.map((o) => (
                  <button
                    key={o.langCode}
                    type="button"
                    role="radio"
                    aria-checked={learnChoice === o.langCode}
                    onClick={() => setLearnChoice(o.langCode)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-bold ${
                      learnChoice === o.langCode ? "border-brand-500 bg-brand-600 text-white" : "border-brand-200 bg-white text-slate-700 hover:bg-brand-50 dark:border-brand-800 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-brand-950/50"
                    }`}
                  >
                    {languageLabel(o.langCode)} — “{o.term.length > 24 ? `${o.term.slice(0, 24)}…` : o.term}”
                  </button>
                ))}
              </div>
            </div>
          )}

          {errorMessage && (
            <div role="alert" className="rounded-xl bg-red-50 border border-red-200 p-3 text-xs font-semibold text-red-600 dark:bg-red-950/40 dark:border-red-800 dark:text-red-400">
              {errorMessage}
            </div>
          )}

          {/* Trùng thẻ */}
          {duplicate && (
            <div role="alert" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-200">
              <p className="font-bold">
                “{term.trim()}” đã có trong {duplicate.deckTitle ? `sổ “${duplicate.deckTitle}”` : "sổ này"}
                {duplicate.definition ? <> với nghĩa: <span className="italic">“{duplicate.definition}”</span></> : null}.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void submit("update")}
                  disabled={isSaving}
                  className="rounded-lg bg-amber-600 px-3 py-1.5 font-bold text-white hover:bg-amber-700 disabled:opacity-50"
                >
                  Cập nhật nghĩa mới
                </button>
                <button type="button" onClick={onClose} className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 font-bold text-amber-800 hover:bg-amber-100 dark:border-amber-700 dark:bg-slate-800 dark:text-amber-300 dark:hover:bg-amber-900/50">
                  Giữ thẻ cũ
                </button>
              </div>
            </div>
          )}

          {ready && langMeta && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void submit("reject");
              }}
              className="flex flex-col gap-4"
            >
              {/* Ngôn ngữ (chỉ đọc) */}
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-emerald-200 bg-emerald-50/70 px-4 py-2.5 dark:border-emerald-800 dark:bg-emerald-950/30">
                <div className="flex items-center gap-2">
                  <span className="text-2xl" aria-hidden>{langMeta.flag}</span>
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-100" data-testid="draft-language">
                      Sẽ lưu vào bộ sưu tập {langMeta.viName}
                    </p>
                    <p className="text-xs sm:text-[11px] text-slate-500 dark:text-slate-400">{describeOrigin(ready.origin)}</p>
                  </div>
                </div>
                {(outcome?.status === "choose-learn" || userSource) && (
                  <button
                    type="button"
                    onClick={() => {
                      setUserSource(null);
                      setLearnChoice(null);
                    }}
                    className="text-xs sm:text-[11px] font-semibold text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Đổi ngôn ngữ
                  </button>
                )}
              </div>

              <div>
                <label htmlFor="sf-term" className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 dark:text-slate-300">
                  Từ vựng / cụm từ ({langMeta.viName}) <span className="text-red-500 dark:text-red-400">*</span>
                </label>
                <input
                  id="sf-term"
                  type="text"
                  required
                  lang={lang ?? undefined}
                  value={term}
                  onChange={edit("term", setTerm)}
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-800 focus:border-brand-500 focus:outline-none transition-colors dark:border-slate-600 dark:text-slate-100"
                />
              </div>

              <div>
                <label htmlFor="sf-meaning" className="flex items-center justify-between text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 dark:text-slate-300">
                  <span>Nghĩa tiếng Việt <span className="text-red-500 dark:text-red-400">*</span></span>
                  {isFilling && (
                    <span className="flex items-center gap-1 text-xs sm:text-[11px] font-semibold normal-case text-brand-600 dark:text-brand-400">
                      <Loader2 size={12} className="animate-spin" /> AI đang điền gợi ý…
                    </span>
                  )}
                </label>
                <textarea
                  id="sf-meaning"
                  required
                  rows={2}
                  value={meaning}
                  onChange={edit("meaning", setMeaning)}
                  placeholder="VD: Chào buổi sáng"
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none resize-none transition-colors dark:border-slate-600 dark:text-slate-100 dark:placeholder-slate-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="sf-phonetic" className="block text-xs sm:text-[11px] font-semibold text-slate-500 mb-1 dark:text-slate-400">Phiên âm (tùy chọn)</label>
                  <input
                    id="sf-phonetic"
                    type="text"
                    value={phonetic}
                    onChange={edit("phonetic", setPhonetic)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-mono text-slate-700 focus:border-brand-500 focus:outline-none dark:border-slate-600 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label htmlFor="sf-example" className="block text-xs sm:text-[11px] font-semibold text-slate-500 mb-1 dark:text-slate-400">Câu ví dụ (tùy chọn)</label>
                  <input
                    id="sf-example"
                    type="text"
                    lang={lang ?? undefined}
                    value={example}
                    onChange={edit("example", setExample)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-brand-500 focus:outline-none dark:border-slate-600 dark:text-slate-200"
                  />
                </div>
              </div>

              {/* Sổ đích: chỉ sổ cùng ngôn ngữ */}
              <div className="mt-1 pt-3 border-t border-slate-100 dark:border-slate-700">
                <label htmlFor="sf-deck" className="flex items-center justify-between text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 dark:text-slate-200">
                  <span>Lưu vào sổ ({langMeta.viName})</span>
                  {isLoadingDecks && <Loader2 size={13} className="animate-spin text-brand-600 dark:text-brand-400" />}
                </label>
                <select
                  id="sf-deck"
                  value={deckChoice}
                  onChange={(e) => {
                    setDeckChoice(e.target.value);
                    setDuplicate(null);
                  }}
                  className="w-full rounded-xl border-2 border-brand-100 bg-brand-50/40 px-3.5 py-2.5 text-sm font-bold text-brand-900 focus:border-brand-500 focus:bg-white focus:outline-none cursor-pointer dark:border-brand-900/50 dark:bg-brand-950/30 dark:text-brand-200 dark:focus:bg-slate-900"
                >
                  <option value="">📁 {decks.find((d) => d.is_default)?.title ?? langMeta.defaultTitle} (sổ mặc định)</option>
                  {decks
                    .filter((d) => !d.is_default)
                    .map((d) => (
                      <option key={d.id} value={d.id}>📁 {d.title} ({d.cards_count ?? 0} từ)</option>
                    ))}
                  <option value={NEW_DECK}>✨ Tạo sổ {langMeta.viName} mới…</option>
                </select>
                {deckChoice === NEW_DECK && (
                  <input
                    type="text"
                    aria-label="Tên sổ mới"
                    value={newDeckTitle}
                    onChange={(e) => setNewDeckTitle(e.target.value)}
                    placeholder={langMeta.defaultTitle}
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-800 focus:border-brand-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                  />
                )}
              </div>

              <div className="mt-2 flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                <button type="button" onClick={onClose} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={!canSave}
                  className="flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-2.5 text-xs font-bold text-white shadow-md shadow-brand-500/20 hover:bg-brand-700 disabled:opacity-50 transition-all"
                >
                  {isSaving ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Đang lưu…</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={15} />
                      <span>Lưu vào sổ thẻ</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {!ready && (outcome?.status === "unsupported" || !outcome) && (
            <div className="flex justify-end">
              <button type="button" onClick={onClose} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
                Đóng
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

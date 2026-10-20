import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Zap,
  ImagePlus,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Plus,
  ShieldCheck,
  Volume2,
  ChevronDown
} from "lucide-react";
import {
  commitGeneratedVocabulary,
  fetchVocabQuota,
  generateVocabulary,
  generateVocabularyFromImage,
  type BackendDeck,
  type CefrLevel,
  type CommitGeneratedResult,
  type GenerateVocabResult,
  type GeneratedVocabItem,
  type VocabPurpose,
  type VocabQuota
} from "../../../services/flashcardService";
import { LANG_CONFIG, isLearnableLang, normalizeLangCode } from "../../../services/deckStorage";
import { FcModal, LangFlag } from "../ui";

interface GenerateVocabModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Có deck: thêm từ vào deck này (và dùng ngôn ngữ của deck). Không có: tạo sổ thẻ mới từ kết quả. */
  targetDeck?: BackendDeck | null;
  /** Ngôn ngữ của từ vựng cần sinh khi tạo sổ mới (en, de, zh, ja, ko, fr, es, ru, th). Mặc định tiếng Anh. */
  lang?: string;
  /** Gọi khi người dùng bấm "Bắt đầu học ngay" sau khi lưu thành công. */
  onStartLearning: (result: CommitGeneratedResult) => void;
}

type Step = "input" | "loading" | "review" | "saved";
type InputTab = "topic" | "image";
type EditableItem = GeneratedVocabItem & { keep: boolean };

const MAX_TEXT_CHARS = 2000;
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

const LEVELS: CefrLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];
const PURPOSES: { value: VocabPurpose | ""; label: string }[] = [
  { value: "", label: "Không chọn" },
  { value: "general", label: "Giao tiếp hằng ngày" },
  { value: "ielts", label: "IELTS" },
  { value: "toeic", label: "TOEIC" },
  { value: "academic", label: "Học thuật" },
  { value: "it", label: "Công nghệ thông tin" },
  { value: "business", label: "Kinh doanh" }
];
/** IELTS/TOEIC là kỳ thi tiếng Anh: chỉ hiện khi sinh từ tiếng Anh. */
const ENGLISH_ONLY_PURPOSES: (VocabPurpose | "")[] = ["ielts", "toeic"];

/** Loại phiên âm theo ngôn ngữ (trường `ipa` của thẻ chứa IPA, pinyin, kana + romaji hoặc romanization tùy ngôn ngữ). */
const PHONETIC_HINTS: Record<string, { label: string; placeholder: string }> = {
  zh: { label: "Phiên âm pinyin", placeholder: "pinyin" },
  ja: { label: "Cách đọc (kana · romaji)", placeholder: "かな · romaji" },
  ko: { label: "Phiên âm romaja", placeholder: "romaja" },
  th: { label: "Phiên âm (RTGS)", placeholder: "romanization" }
};
const DEFAULT_PHONETIC_HINT = { label: "Phiên âm IPA", placeholder: "/IPA/" };

const TOPIC_EXAMPLES: Record<string, string> = { en: "Environmental Protection, technology" };
const DEFAULT_TOPIC_EXAMPLE = "Du lịch, Môi trường, Công nghệ";

const POS_OPTIONS = [
  "noun",
  "verb",
  "adjective",
  "adverb",
  "preposition",
  "conjunction",
  "pronoun",
  "determiner",
  "interjection",
  "phrasal verb",
  "idiom",
  "phrase"
];

const WARNING_LABELS: Record<string, { text: string; tone: "warn" | "info" }> = {
  ipa_invalid: { text: "Phiên âm chưa hợp lệ - hãy kiểm tra", tone: "warn" },
  no_example: { text: "Chưa có câu ví dụ", tone: "warn" },
  example_missing_term: { text: "Ví dụ chưa chứa từ khóa (bài đục lỗ sẽ không dùng được)", tone: "warn" },
  no_example_translation: { text: "Chưa có bản dịch câu ví dụ", tone: "warn" },
  not_verified: { text: "AI chưa kiểm tra lại thẻ này", tone: "warn" },
  fixed_by_reviewer: { text: "AI kiểm duyệt đã chỉnh sửa", tone: "info" }
};

const LOADING_STEPS = [
  "AI đang chọn các từ phù hợp...",
  "AI đang viết nghĩa, phiên âm và câu ví dụ...",
  "AI đang kiểm tra lại chất lượng từng thẻ..."
];

/** Chủ đề ngắn -> sinh theo chủ đề; đoạn dài -> trích từ quan trọng trong đoạn văn. */
export function detectInputMode(input: string): "topic" | "text" {
  const trimmed = input.trim();
  const words = trimmed.split(/\s+/).filter(Boolean).length;
  return trimmed.length <= 100 && words <= 8 ? "topic" : "text";
}

const newRequestId = (): string =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `req-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

export const GenerateVocabModal: React.FC<GenerateVocabModalProps> = ({
  isOpen,
  onClose,
  targetDeck,
  lang,
  onStartLearning
}) => {
  const queryClient = useQueryClient();

  // Ngôn ngữ do SỔ ĐÍCH quyết định (sổ là đơn vị ngôn ngữ); tạo sổ mới thì theo `lang`; không rõ thì tiếng Anh.
  const langCode = useMemo(() => {
    const code = normalizeLangCode(targetDeck?.lang_code || targetDeck?.langCode || lang);
    return code && isLearnableLang(code) ? code : "en";
  }, [targetDeck, lang]);
  const langMeta = LANG_CONFIG[langCode];
  const viLang = `tiếng ${langMeta.viName.split(" ").slice(1).join(" ")}`;
  const phoneticHint = PHONETIC_HINTS[langCode] ?? DEFAULT_PHONETIC_HINT;
  const purposes = PURPOSES.filter((p) => langCode === "en" || !ENGLISH_ONLY_PURPOSES.includes(p.value));

  const [step, setStep] = useState<Step>("input");
  const [tab, setTab] = useState<InputTab>("topic");
  const [input, setInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [level, setLevel] = useState<CefrLevel>("B1");
  const [count, setCount] = useState(20);
  const [purpose, setPurpose] = useState<VocabPurpose | "">("");
  const [instruction, setInstruction] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [quota, setQuota] = useState<VocabQuota | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [items, setItems] = useState<EditableItem[]>([]);
  const [meta, setMeta] = useState<{ mode: GenerateVocabResult["mode"]; topic?: string | null; dropped: number; lang: string } | null>(null);
  const [deckTitle, setDeckTitle] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState<CommitGeneratedResult | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef<string>(newRequestId());
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const detectedMode = useMemo(() => detectInputMode(input), [input]);
  const keptItems = useMemo(() => items.filter((i) => i.keep), [items]);

  const refreshQuota = useCallback(async () => {
    const res = await fetchVocabQuota();
    if (res.ok && res.data) setQuota(res.data);
  }, []);

  // Mở modal: đặt lại trạng thái và lấy hạn mức.
  useEffect(() => {
    if (!isOpen) return;
    setStep("input");
    setError(null);
    setItems([]);
    setSaved(null);
    setMeta(null);
    setPurpose((p) => (p && langCode !== "en" && ENGLISH_ONLY_PURPOSES.includes(p) ? "" : p));
    requestIdRef.current = newRequestId();
    void refreshQuota();
    return () => abortRef.current?.abort();
  }, [isOpen, refreshQuota, langCode]);

  // Ảnh xem trước: giải phóng object URL khi đổi/đóng.
  useEffect(() => {
    if (!imageFile) {
      setImagePreview(null);
      return;
    }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  // Thông báo tiến trình theo thời gian chờ (pipeline 3 bước: chọn từ -> sinh chi tiết -> kiểm tra).
  useEffect(() => {
    if (step !== "loading" && !isLoadingMore) return;
    setLoadingStep(0);
    const timer = window.setInterval(() => setLoadingStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1)), 7000);
    return () => window.clearInterval(timer);
  }, [step, isLoadingMore]);

  const acceptImage = useCallback((file: File | null | undefined) => {
    if (!file) return;
    if (!IMAGE_TYPES.includes(file.type)) {
      setError("Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP.");
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setError("Ảnh vượt quá 5MB.");
      return;
    }
    setError(null);
    setImageFile(file);
  }, []);

  // Ctrl+V để dán ảnh.
  useEffect(() => {
    if (!isOpen || tab !== "image" || step !== "input") return;
    const onPaste = (e: ClipboardEvent) => {
      const file = Array.from(e.clipboardData?.files || []).find((f) => f.type.startsWith("image/"));
      if (file) {
        e.preventDefault();
        acceptImage(file);
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [isOpen, tab, step, acceptImage]);

  const handleClose = () => {
    abortRef.current?.abort();
    onClose();
  };

  const requestGeneration = async (extraExclude: string[] = [], n: number = count) => {
    const controller = new AbortController();
    abortRef.current = controller;
    const common = { level, count: n, purpose: purpose || undefined, instruction: instruction.trim(), deckId: targetDeck?.id, langCode };
    const timeout = window.setTimeout(() => controller.abort(), 90_000);
    try {
      if (tab === "image" && imageFile) {
        return await generateVocabularyFromImage(imageFile, common, controller.signal);
      }
      const mode = detectedMode;
      return await generateVocabulary(
        { ...common, mode, topic: mode === "topic" ? input.trim() : undefined, text: mode === "text" ? input.trim() : undefined, excludeTerms: extraExclude },
        controller.signal
      );
    } finally {
      window.clearTimeout(timeout);
    }
  };

  const validateInput = (): string | null => {
    if (tab === "image") return imageFile ? null : "Vui lòng chọn hoặc dán một hình ảnh.";
    const trimmed = input.trim();
    if (trimmed.length < 2) return `Vui lòng nhập chủ đề hoặc đoạn văn ${viLang}.`;
    if (detectedMode === "text" && trimmed.length < 20) return "Đoạn văn quá ngắn (ít nhất 20 ký tự).";
    return null;
  };

  const handleGenerate = async () => {
    const problem = validateInput();
    if (problem) {
      setError(problem);
      return;
    }
    if (quota && quota.remaining <= 0) {
      setError("Bạn đã hết lượt tạo từ vựng bằng AI hôm nay.");
      return;
    }
    setError(null);
    setStep("loading");
    const res = await requestGeneration();
    if (!res.ok) {
      setError(res.error?.message || "Không thể tạo từ vựng. Vui lòng thử lại.");
      setStep("input");
      void refreshQuota();
      return;
    }
    const data = res.data;
    setItems(data.items.map((i) => ({ ...i, keep: true })));
    setMeta({ mode: data.mode, topic: data.topic, dropped: data.dropped.length, lang: data.lang_code || langCode });
    if (data.quota) setQuota(data.quota);
    const baseTitle =
      data.mode === "topic" && data.topic
        ? `${data.topic} (${data.level})`
        : data.mode === "image"
        ? "Từ vựng từ hình ảnh"
        : "Từ vựng từ đoạn văn";
    setDeckTitle(targetDeck ? targetDeck.title : baseTitle.slice(0, 100));
    requestIdRef.current = newRequestId();
    setStep("review");
  };

  const handleGenerateMore = async () => {
    if (isLoadingMore) return;
    if (quota && quota.remaining <= 0) {
      setError("Bạn đã hết lượt tạo từ vựng bằng AI hôm nay.");
      return;
    }
    setError(null);
    setIsLoadingMore(true);
    const res = await requestGeneration(items.map((i) => i.term), Math.min(10, 50));
    setIsLoadingMore(false);
    if (!res.ok) {
      setError(res.error?.message || "Không thể tạo thêm từ vựng.");
      void refreshQuota();
      return;
    }
    const known = new Set(items.map((i) => i.term.trim().toLowerCase()));
    const batchTag = Date.now().toString(36);
    const fresh = res.data.items
      .filter((i) => !known.has(i.term.trim().toLowerCase()))
      .map((i) => ({ ...i, temp_id: `${batchTag}-${i.temp_id}`, keep: true }));
    setItems((prev) => [...prev, ...fresh]);
    if (res.data.quota) setQuota(res.data.quota);
    requestIdRef.current = newRequestId(); // danh sách đã thay đổi -> yêu cầu lưu mới
  };

  const updateItem = (tempId: string, patch: Partial<EditableItem>) =>
    setItems((prev) => prev.map((i) => (i.temp_id === tempId ? { ...i, ...patch } : i)));

  const handleSave = async () => {
    const cards = keptItems
      .map((i) => ({
        term: i.term.trim(),
        definition: i.definition.trim(),
        partOfSpeech: i.part_of_speech,
        phonetic: i.ipa.trim(),
        example: i.example.trim(),
        exampleTranslation: i.example_translation.trim(),
        level: i.level
      }))
      .filter((c) => c.term && c.definition);
    if (cards.length === 0) {
      setError("Cần giữ lại ít nhất một từ có đủ từ vựng và nghĩa.");
      return;
    }
    if (!targetDeck && !deckTitle.trim()) {
      setError("Vui lòng đặt tên cho sổ thẻ.");
      return;
    }
    setError(null);
    setIsSaving(true);
    const res = await commitGeneratedVocabulary({
      clientRequestId: requestIdRef.current,
      deckId: targetDeck?.id,
      deck: targetDeck
        ? undefined
        : {
            title: deckTitle.trim(),
            description: `Tạo bằng AI${meta?.topic ? ` · Chủ đề: ${meta.topic}` : ""} · ${level}`,
            langCode: meta?.lang || langCode
          },
      cards,
      // Dùng ngôn ngữ của lượt sinh (không phải ngôn ngữ hiện tại của hộp) để không lưu nhầm từ vào sổ khác ngôn ngữ.
      source: { mode: meta?.mode || "topic", topic: meta?.topic || undefined, level, langCode: meta?.lang || langCode }
    });
    setIsSaving(false);
    if (!res.ok) {
      setError(res.error?.message || "Không thể lưu bộ từ vựng. Vui lòng thử lại.");
      return;
    }
    setSaved(res.data);
    setStep("saved");
    queryClient.invalidateQueries({ queryKey: ["flashcard_decks"] });
    queryClient.invalidateQueries({ queryKey: ["flashcard_cards"] });
    queryClient.invalidateQueries({ queryKey: ["flashcard_study"] });
  };

  if (!isOpen) return null;

  const noQuota = !!quota && quota.remaining <= 0;
  const inputLength = input.length;

  const footerNode = (
    <div className="flex w-full items-center justify-between gap-3">
          {step === "input" && (
            <>
              <button type="button" onClick={handleClose} className="text-sm font-bold text-sky-700 hover:text-sky-800 dark:text-sky-400">
                Hủy
              </button>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={noQuota}
                className="flex flex-1 items-center justify-center gap-2 rounded-full bg-blue-600 py-3 text-sm font-bold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none sm:px-10"
              >
                <Zap size={16} />
                <span>{noQuota ? "Đã hết lượt hôm nay" : "Tạo từ vựng với AI"}</span>
              </button>
            </>
          )}
          {step === "loading" && (
            <button
              type="button"
              onClick={() => {
                abortRef.current?.abort();
                setStep("input");
              }}
              className="text-sm font-bold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Hủy yêu cầu
            </button>
          )}
          {step === "review" && (
            <>
              <button type="button" onClick={() => setStep("input")} className="text-sm font-bold text-sky-700 hover:text-sky-800 dark:text-sky-400">
                ← Quay lại
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving || keptItems.length === 0}
                className="flex items-center justify-center gap-2 rounded-full bg-blue-600 px-8 py-3 text-sm font-bold text-white shadow-sm transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? <RefreshCw size={15} className="animate-spin" /> : <CheckCircle2 size={16} />}
                <span>{isSaving ? "Đang lưu..." : `Lưu ${keptItems.length} từ`}</span>
              </button>
            </>
          )}
          {step === "saved" && saved && (
            <>
              <button type="button" onClick={handleClose} className="text-sm font-bold text-sky-700 hover:text-sky-800 dark:text-sky-400">
                Đóng
              </button>
              <button
                type="button"
                onClick={() => {
                  onStartLearning(saved);
                  onClose();
                }}
                className="rounded-full bg-blue-600 px-8 py-3 text-sm font-bold text-white shadow-sm transition-colors hover:bg-blue-700"
              >
                Bắt đầu học ngay
              </button>
            </>
          )}
    </div>
  );

  return (
    <FcModal
      title={
        <span className="flex items-center gap-2 text-lg">
          <Zap size={20} className="text-blue-600 dark:text-blue-400" aria-hidden="true" />
          <span>Tạo từ vựng với AI</span>
        </span>
      }
      headerExtra={
          <div className="mt-2.5 flex flex-wrap items-center gap-2 text-[11px] font-extrabold uppercase tracking-wide">
            <span
              data-testid="generate-language"
              className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-3 py-1 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200"
            >
              <LangFlag lang={langCode} size="xs" /> {langMeta.viName}
            </span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700 dark:bg-slate-700 dark:text-slate-200">{quota?.tier_label || "THƯỜNG"}</span>
            <span
              className={`rounded-full px-3 py-1 ${noQuota ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300" : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"}`}
            >
              {quota ? `Còn ${quota.remaining}/${quota.limit} lượt hôm nay` : "Đang tải hạn mức..."}
            </span>
            <span className="rounded-full bg-sky-100 px-3 py-1 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">Đã dùng {quota?.used ?? 0}</span>
            {targetDeck && (
              <span className="rounded-full bg-blue-50 px-3 py-1 normal-case tracking-normal text-blue-700 dark:bg-blue-950/40 dark:text-blue-300">
                Thêm vào sổ: {targetDeck.title}
              </span>
            )}
          </div>
      }
      size="xl"
      onClose={handleClose}
      dismissible={step !== "loading"}
      footer={footerNode}
    >
          {error && (
            <div role="alert" className="mb-4 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: INPUT */}
          {step === "input" && (
            <div className="flex flex-col gap-4">
              <div className="flex gap-2" role="tablist">
                {(
                  [
                    ["topic", "Nhập chủ đề"],
                    ["image", "Hình ảnh"]
                  ] as [InputTab, string][]
                ).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={tab === key}
                    onClick={() => {
                      setTab(key);
                      setError(null);
                    }}
                    className={`rounded-full px-5 py-2 text-sm font-bold transition-colors ${
                      tab === key ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {tab === "topic" ? (
                <div>
                  <div className="relative">
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value.slice(0, MAX_TEXT_CHARS))}
                      rows={5}
                      placeholder={`Nhập chủ đề (VD: ${TOPIC_EXAMPLES[langCode] ?? DEFAULT_TOPIC_EXAMPLE}) hoặc dán một đoạn văn ${viLang} để trích xuất từ vựng...`}
                      className="w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none dark:border-slate-600 dark:bg-slate-900/40 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:bg-slate-900"
                    />
                    <span className="pointer-events-none absolute bottom-2 right-3 text-[11px] text-slate-500 dark:text-slate-400">
                      {inputLength}/{MAX_TEXT_CHARS}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    💡 Nhập tên chủ đề để AI tạo từ vựng về chủ đề đó, hoặc dán một đoạn văn {viLang} để AI trích xuất các từ quan trọng.
                    {input.trim().length >= 2 && (
                      <strong className="ml-1 text-blue-600 dark:text-blue-400">
                        Đang nhận diện: {detectedMode === "topic" ? "chủ đề" : "đoạn văn"}.
                      </strong>
                    )}
                  </p>
                </div>
              ) : (
                <div>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      acceptImage(e.dataTransfer.files?.[0]);
                    }}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInputRef.current?.click()}
                    className="flex min-h-[190px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-blue-300 bg-blue-50/40 p-5 text-center transition-colors hover:bg-blue-50 dark:border-blue-700 dark:bg-blue-950/30 dark:hover:bg-blue-950/50"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={(e) => acceptImage(e.target.files?.[0])}
                    />
                    {imagePreview ? (
                      <div className="flex flex-col items-center gap-2">
                        <img src={imagePreview} alt="Ảnh đã chọn" className="max-h-40 rounded-xl border border-slate-200 object-contain dark:border-slate-600" />
                        <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">{imageFile?.name} · bấm để chọn ảnh khác</span>
                      </div>
                    ) : (
                      <>
                        <ImagePlus size={34} className="mb-2 text-slate-500 dark:text-slate-400" />
                        <p className="text-sm font-bold text-slate-600 dark:text-slate-300">Kéo thả hoặc click để chọn ảnh</p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          hoặc nhấn <strong>Ctrl+V</strong> để dán ảnh
                        </p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">JPG, PNG, WEBP - tối đa 5MB</p>
                      </>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    🖼️ AI sẽ nhận diện và trích xuất từ vựng {viLang} từ hình ảnh (sách, biển quảng cáo, tài liệu...). Ảnh chỉ dùng để
                    xử lý, không được lưu lại.
                  </p>
                </div>
              )}

              {/* Tùy chọn */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
                  Trình độ (CEFR)
                  <select
                    value={level}
                    onChange={(e) => setLevel(e.target.value as CefrLevel)}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-normal focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800"
                  >
                    {LEVELS.map((l) => (
                      <option key={l} value={l}>
                        {l}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
                  Số từ: <span className="text-blue-600 dark:text-blue-400">{count}</span>
                  <input
                    type="range"
                    min={5}
                    max={50}
                    step={5}
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    className="accent-blue-600"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => setShowAdvanced((v) => !v)}
                  className="col-span-2 flex items-center justify-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 sm:col-span-1 sm:mt-5 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  Tùy chọn thêm <ChevronDown size={14} className={showAdvanced ? "rotate-180" : ""} />
                </button>
              </div>
              {showAdvanced && (
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
                    Mục đích học
                    <select
                      value={purpose}
                      onChange={(e) => setPurpose(e.target.value as VocabPurpose | "")}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-normal focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800"
                    >
                      {purposes.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
                    Yêu cầu thêm (tùy chọn)
                    <input
                      value={instruction}
                      onChange={(e) => setInstruction(e.target.value.slice(0, 300))}
                      placeholder={langCode === "en" ? "VD: Tập trung từ dùng cho IELTS Writing" : "VD: Tập trung từ dùng khi đi du lịch"}
                      className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal focus:border-blue-500 focus:outline-none dark:border-slate-600"
                    />
                  </label>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: LOADING */}
          {step === "loading" && (
            <div className="flex min-h-[260px] flex-col items-center justify-center gap-3 text-center" aria-live="polite">
              <RefreshCw size={38} className="animate-spin text-blue-600 dark:text-blue-400" />
              <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{LOADING_STEPS[loadingStep]}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Thường mất 15-40 giây. Vui lòng không đóng cửa sổ này.</p>
            </div>
          )}

          {/* STEP 3: REVIEW */}
          {step === "review" && (
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-bold text-slate-700 dark:text-slate-200">
                  AI đề xuất {items.length} từ · đang giữ {keptItems.length}
                  {meta && meta.dropped > 0 && (
                    <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-400">({meta.dropped} từ bị loại do trùng hoặc không đạt)</span>
                  )}
                </p>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">Phiên âm và nghĩa do AI tạo - hãy kiểm tra trước khi lưu</span>
              </div>

              <ul className="flex flex-col gap-3">
                {items.map((item) => (
                  <li
                    key={item.temp_id}
                    className={`rounded-2xl border p-3 transition-opacity ${
                      item.keep ? "border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-800" : "border-dashed border-slate-200 bg-slate-50 opacity-50 dark:border-slate-600 dark:bg-slate-900/50"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        type="checkbox"
                        checked={item.keep}
                        onChange={(e) => updateItem(item.temp_id, { keep: e.target.checked })}
                        aria-label={`Giữ từ ${item.term}`}
                        className="h-4 w-4 accent-blue-600"
                      />
                      <input
                        value={item.term}
                        onChange={(e) => updateItem(item.temp_id, { term: e.target.value })}
                        aria-label="Từ vựng"
                        lang={langCode}
                        className="min-w-[120px] flex-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm font-bold text-slate-800 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:text-slate-100"
                      />
                      <select
                        value={item.part_of_speech}
                        onChange={(e) => updateItem(item.temp_id, { part_of_speech: e.target.value })}
                        aria-label="Từ loại"
                        className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800"
                      >
                        {POS_OPTIONS.includes(item.part_of_speech) ? null : <option value={item.part_of_speech}>{item.part_of_speech}</option>}
                        {POS_OPTIONS.map((p) => (
                          <option key={p} value={p}>
                            {p}
                          </option>
                        ))}
                      </select>
                      <input
                        value={item.ipa}
                        onChange={(e) => updateItem(item.temp_id, { ipa: e.target.value })}
                        placeholder={phoneticHint.placeholder}
                        aria-label={phoneticHint.label}
                        className="w-32 rounded-lg border border-slate-200 px-2.5 py-1.5 font-mono text-xs text-blue-700 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:text-blue-300"
                      />
                      {item.verified && (
                        <span title="Đã được AI kiểm duyệt" className="text-emerald-600 dark:text-emerald-400">
                          <ShieldCheck size={16} />
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => setItems((prev) => prev.filter((i) => i.temp_id !== item.temp_id))}
                        aria-label={`Xóa từ ${item.term}`}
                        className="ml-auto rounded-full p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/50 dark:text-slate-400"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                    <input
                      value={item.definition}
                      onChange={(e) => updateItem(item.temp_id, { definition: e.target.value })}
                      aria-label="Nghĩa tiếng Việt"
                      placeholder="Nghĩa tiếng Việt"
                      className="mt-2 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none dark:border-slate-600"
                    />
                    <input
                      value={item.example}
                      onChange={(e) => updateItem(item.temp_id, { example: e.target.value })}
                      aria-label="Câu ví dụ"
                      lang={langCode}
                      placeholder="Câu ví dụ"
                      className="mt-2 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm italic text-slate-700 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:text-slate-200"
                    />
                    <input
                      value={item.example_translation}
                      onChange={(e) => updateItem(item.temp_id, { example_translation: e.target.value })}
                      aria-label="Dịch câu ví dụ"
                      placeholder="Dịch câu ví dụ"
                      className="mt-2 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs text-slate-500 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:text-slate-400"
                    />
                    {item.warnings.filter((w) => WARNING_LABELS[w]).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {item.warnings
                          .filter((w) => WARNING_LABELS[w])
                          .map((w) => (
                            <span
                              key={w}
                              className={`rounded-full px-2 py-0.5 text-[10.5px] font-semibold ${
                                WARNING_LABELS[w].tone === "warn" ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" : "bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300"
                              }`}
                            >
                              {WARNING_LABELS[w].text}
                            </span>
                          ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>

              {meta?.mode !== "image" && (
              <button
                type="button"
                onClick={handleGenerateMore}
                disabled={isLoadingMore || noQuota || items.length >= 100}
                className="flex items-center justify-center gap-2 rounded-2xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-xs font-bold text-blue-700 transition-colors hover:bg-blue-100 disabled:opacity-50 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50"
              >
                {isLoadingMore ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={14} />}
                <span>{isLoadingMore ? LOADING_STEPS[loadingStep] : "Thêm 10 từ nữa (tốn 1 lượt)"}</span>
              </button>
              )}

              {!targetDeck && (
                <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
                  Tên sổ thẻ mới
                  <input
                    value={deckTitle}
                    onChange={(e) => setDeckTitle(e.target.value.slice(0, 100))}
                    className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal focus:border-blue-500 focus:outline-none dark:border-slate-600"
                  />
                </label>
              )}
            </div>
          )}

          {/* STEP 4: SAVED */}
          {step === "saved" && saved && (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400">
                <CheckCircle2 size={32} />
              </div>
              <h4 className="text-lg font-bold text-slate-800 dark:text-slate-100">Đã lưu bộ từ vựng!</h4>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Thêm mới <strong className="text-emerald-600 dark:text-emerald-400">{saved.inserted}</strong> thẻ
                {saved.skipped_duplicates > 0 && <> · bỏ qua {saved.skipped_duplicates} thẻ trùng</>}
                {saved.deck?.title && (
                  <>
                    {" "}
                    vào sổ <strong>"{saved.deck.title}"</strong>
                  </>
                )}
                .
              </p>
              {saved.extended_saved === false && (
                <p className="max-w-md rounded-xl bg-amber-50 p-2.5 text-xs text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
                  Máy chủ chưa cập nhật cơ sở dữ liệu nên bản dịch câu ví dụ chưa được lưu (quản trị viên cần chạy migration 003).
                </p>
              )}
              <p className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                <Volume2 size={13} /> Giọng đọc chuẩn đang được tạo trước ở chế độ nền.
              </p>
            </div>
          )}
    </FcModal>
  );
};

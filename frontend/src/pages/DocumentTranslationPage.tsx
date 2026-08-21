import { useState, useEffect, useRef } from "react";
import {
  FileText,
  UploadCloud,
  Download,
  Sparkles,
  CheckCircle2,
  Languages,
  ArrowRightLeft,
  BookOpen,
  BookmarkPlus,
  Loader2,
  AlignLeft,
  Copy,
  Check,
  BookMarked,
  FileCheck,
  Eye,
  AlertCircle,
  ExternalLink,
  FileType,
  Volume2,
  RotateCcw,
  ShieldCheck
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  LANG_CONFIG,
  getDecks,
  createCustomDeck,
  addCardToDeck,
  type FlashcardDeck
} from "../services/deckStorage";
import {
  fetchBackendDecks,
  createBackendDeck,
  createBackendCard,
  type BackendDeck
} from "../services/flashcardService";
import { getToken } from "../services/authService";
import { useAuth } from "../hooks/useAuth";

interface DocumentFile {
  id?: string;
  name: string;
  type: "pdf";
  size: string;
  pagesOrSlides: string;
  title: string;
}

interface GlossaryItem {
  term: string;
  translation?: string;
  vi?: string; // Fallback
  context?: string;
  phonetic?: string;
  audio_url?: string;
}

export default function DocumentTranslationPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const storageKey = user?.id ? `iuh_doc_translation_session_${user.id}` : "iuh_doc_translation_session_guest";

  // Ref để phân biệt giữa F5/Reload trang và Chuyển trang/Logout (SPA navigation)
  const isReloadingRef = useRef(false);

  // Language & Selection state (Default: English -> Vietnamese)
  const [sourceLang, setSourceLang] = useState("en");
  const [targetLang, setTargetLang] = useState("vi");
  const [selectedFile, setSelectedFile] = useState<DocumentFile | null>(null);
  const [actualFile, setActualFile] = useState<File | null>(null);

  // Processing state
  const [docId, setDocId] = useState<string>("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [isExtractingGlossary, setIsExtractingGlossary] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Vui lòng chọn tài liệu PDF để bắt đầu");
  const [modelUsed, setModelUsed] = useState<string>("");
  const [isCompleted, setIsCompleted] = useState(false);
  const [savedKeywordsSuccess, setSavedKeywordsSuccess] = useState(false);

  // Translated Result Frame State
  const [translatedText, setTranslatedText] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"pdf" | "markdown" | "summary">("pdf");

  // Extracted Glossary from real document processing
  const [glossary, setGlossary] = useState<GlossaryItem[]>([]);
  const [selectedGlossaryIndices, setSelectedGlossaryIndices] = useState<Set<number>>(new Set());

  // Deck Modal & Saving State
  const [isDeckModalOpen, setIsDeckModalOpen] = useState(false);
  const [isLoadingDecks, setIsLoadingDecks] = useState(false);
  const [isSavingCards, setIsSavingCards] = useState(false);
  const [deckOption, setDeckOption] = useState<"existing" | "new">("existing");
  const [selectedDeckId, setSelectedDeckId] = useState<string>("");
  const [newDeckTitle, setNewDeckTitle] = useState("");
  const [availableDecks, setAvailableDecks] = useState<BackendDeck[]>([]);
  const [saveSuccessDetail, setSaveSuccessDetail] = useState<{ count: number; deckTitle: string } | null>(null);

  // Ref to track latest state for async event listeners
  const selectedFileRef = useRef(selectedFile);
  selectedFileRef.current = selectedFile;

  const persistSession = (dataToSave: Record<string, any>) => {
    try {
      const existing = JSON.parse(sessionStorage.getItem(storageKey) || "{}");
      const merged = { ...existing, ...dataToSave, timestamp: Date.now() };
      sessionStorage.setItem(storageKey, JSON.stringify(merged));
    } catch (e) {
      console.error("Error saving translation session:", e);
    }
  };

  const handleResetTranslation = () => {
    sessionStorage.removeItem(storageKey);
    // Dọn dẹp cả localStorage cũ nếu có
    localStorage.removeItem(storageKey);
    localStorage.removeItem("iuh_doc_translation_session");

    setDocId("");
    setSelectedFile(null);
    setActualFile(null);
    setIsTranslating(false);
    setIsExtractingGlossary(false);
    setIsCompleted(false);
    setProgressPercent(0);
    setStatusMessage("Vui lòng chọn tài liệu để bắt đầu");
    setTranslatedText("");
    setGlossary([]);
    setSelectedGlossaryIndices(new Set());
    setModelUsed("");
    setActiveTab("pdf");
  };

  // Quản lý vòng đời session: Giữ khi F5/Reload, Tự động XÓA khi chuyển trang / quay lại / logout
  useEffect(() => {
    const handleBeforeUnload = () => {
      isReloadingRef.current = true;
    };
    window.addEventListener("beforeunload", handleBeforeUnload);

    // 1. Khôi phục trạng thái từ sessionStorage (khi người dùng F5 / Reload trang)
    try {
      // Dọn dẹp localStorage cũ
      localStorage.removeItem("iuh_doc_translation_session");
      localStorage.removeItem(storageKey);

      const saved = sessionStorage.getItem(storageKey);
      if (saved) {
        const data = JSON.parse(saved);
        if (data && data.docId) {
          setDocId(data.docId);
          if (data.sourceLang) setSourceLang(data.sourceLang);
          if (data.targetLang) setTargetLang(data.targetLang);
          if (data.selectedFile) setSelectedFile(data.selectedFile);
          if (data.translatedText) setTranslatedText(data.translatedText);
          if (data.glossary) setGlossary(data.glossary);
          if (data.modelUsed) setModelUsed(data.modelUsed);
          if (data.statusMessage) setStatusMessage(data.statusMessage);
          if (data.progressPercent !== undefined) setProgressPercent(data.progressPercent);
          if (data.isCompleted !== undefined) setIsCompleted(data.isCompleted);
          if (data.activeTab) setActiveTab(data.activeTab);

          // Fetch fresh state from backend
          const baseUrl = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
          const token = getToken();
          const headers: Record<string, string> = {};
          if (token) headers["Authorization"] = `Bearer ${token}`;

          fetch(`${baseUrl}/api/v1/documents/${data.docId}/status`, { headers })
            .then((res) => (res.ok ? res.json() : null))
            .then((resData) => {
              if (resData?.data) {
                const item = resData.data;
                if (item.status === "completed") {
                  setIsCompleted(true);
                  setIsTranslating(false);
                  setIsExtractingGlossary(false);
                  setProgressPercent(100);
                  if (item.glossary_json && item.glossary_json.length > 0) setGlossary(item.glossary_json);
                  else if (item.glossary && item.glossary.length > 0) setGlossary(item.glossary);
                  if (item.translated_text) setTranslatedText(item.translated_text);
                  if (item.model_used) setModelUsed(item.model_used);
                  if (item.message) setStatusMessage(item.message);
                }
              }
            })
            .catch((e) => console.log("Status restore check:", e));
        }
      }
    } catch (e) {
      console.error("Lỗi khôi phục session dịch thuật:", e);
    }

    // 2. Cleanup khi unmount: Nếu KHÔNG PHẢI F5 (tức là chuyển trang khác / back / logout) -> Xóa sạch session để bảo mật
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      if (!isReloadingRef.current) {
        sessionStorage.removeItem(storageKey);
      }
    };
  }, [storageKey]);

  const swapLanguages = () => {
    const newSrc = targetLang;
    const newTgt = sourceLang;
    setSourceLang(newSrc);
    setTargetLang(newTgt);
    persistSession({ sourceLang: newSrc, targetLang: newTgt });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Hệ thống chuyên biệt dịch tài liệu học thuật định dạng PDF. Vui lòng chỉ tải lên file có đuôi .pdf.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Kích thước file vượt quá giới hạn 10MB. Vui lòng chọn file PDF nhỏ hơn.");
      return;
    }

    const newDocId = `doc_${Date.now()}`;
    const fileObj: DocumentFile = {
      id: newDocId,
      name: file.name,
      type: "pdf",
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      pagesOrSlides: "Tài liệu PDF",
      title: file.name.replace(/\.[^/.]+$/, ""),
    };

    setDocId(newDocId);
    setActualFile(file);
    setSelectedFile(fileObj);
    setIsCompleted(false);
    setIsExtractingGlossary(false);
    setProgressPercent(0);
    setStatusMessage("Tài liệu PDF đã sẵn sàng để dịch");
    setTranslatedText("");
    setGlossary([]);
    setSelectedGlossaryIndices(new Set());

    persistSession({
      docId: newDocId,
      selectedFile: fileObj,
      isCompleted: false,
      progressPercent: 0,
      statusMessage: "Tài liệu PDF đã sẵn sàng để dịch",
      translatedText: "",
      glossary: []
    });
  };

  const handleStartTranslate = async () => {
    if (!actualFile) {
      alert("Vui lòng tải lên một tài liệu PDF từ máy tính của bạn.");
      return;
    }

    setIsTranslating(true);
    setIsExtractingGlossary(false);
    setIsCompleted(false);
    setProgressPercent(5);
    setStatusMessage("Đang tải tài liệu PDF lên hệ thống AI...");

    try {
      const formData = new FormData();
      formData.append("file", actualFile);
      formData.append("source_lang", sourceLang);
      formData.append("target_lang", targetLang);

      const baseUrl = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
      const token = getToken();
      
      const headers = new Headers();
      if (token) {
        headers.append("Authorization", `Bearer ${token}`);
      }

      const uploadRes = await fetch(`${baseUrl}/api/v1/documents/upload`, {
        method: "POST",
        headers: headers,
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error("Lỗi tải lên tài liệu: " + uploadRes.statusText);
      }

      const uploadData = await uploadRes.json();
      const currentDocId = uploadData.data.doc_id;
      setDocId(currentDocId);

      persistSession({
        docId: currentDocId,
        sourceLang,
        targetLang,
        selectedFile: selectedFileRef.current,
        isCompleted: false,
        progressPercent: 10,
        statusMessage: "Đang xử lý dịch thuật PDF ngầm..."
      });

      // FIX-AGENT: Thêm cơ chế tự động kết nối lại (Auto-reconnect) cho EventSource
      let retryCount = 0;
      const MAX_RETRIES = 5;
      let eventSource: EventSource | null = null;
      let currentProgress = 10;
      let currentIsCompleted = false;

      const connectSSE = () => {
        const eventSourceUrl = new URL(`${baseUrl}/api/v1/documents/${currentDocId}/stream`);
        if (token) {
          eventSourceUrl.searchParams.append("token", token);
        }
        eventSource = new EventSource(eventSourceUrl.toString());

        eventSource.addEventListener("update", (event) => {
          retryCount = 0; // Reset số lần thử khi nhận tin nhắn thành công
          try {
            const data = JSON.parse(event.data);
            
            if (data.progress !== undefined) {
              setProgressPercent(data.progress);
              currentProgress = data.progress;
            }
            if (data.message) setStatusMessage(data.message);
            if (data.model_used) setModelUsed(data.model_used);
            
            // Khi đã có nội dung dịch hoặc PDF link, hiển thị ngay PDF view cho người dùng
            if (data.translated_text || data.translated_file_url) {
              if (data.translated_text) setTranslatedText(data.translated_text);
              setIsCompleted(true);
              currentIsCompleted = true;
              setIsTranslating(false);
              setActiveTab("pdf");
            }

            if (data.glossary && data.glossary.length > 0) {
              setGlossary(data.glossary);
              setIsExtractingGlossary(false);
            } else if (data.progress >= 80 || (data.message && data.message.toLowerCase().includes("glossary"))) {
              setIsExtractingGlossary(true);
            }

            const statusLower = data.status ? String(data.status).toLowerCase() : "";
            if (statusLower === "completed") {
              eventSource?.close();
              setIsTranslating(false);
              setIsCompleted(true);
              currentIsCompleted = true;
              setIsExtractingGlossary(false);
              setActiveTab("pdf");

              persistSession({
                docId: currentDocId,
                sourceLang,
                targetLang,
                selectedFile: selectedFileRef.current,
                translatedText: data.translated_text || "",
                glossary: data.glossary || [],
                modelUsed: data.model_used || "",
                statusMessage: data.message || "Đã hoàn thành dịch thuật PDF",
                progressPercent: 100,
                isCompleted: true,
                activeTab: "pdf"
              });
            } else if (statusLower === "failed") {
              eventSource?.close();
              setIsTranslating(false);
              setIsExtractingGlossary(false);
              setStatusMessage("Lỗi xử lý: " + (data.message || data.error || ""));
              persistSession({
                docId: currentDocId,
                isCompleted: false,
                statusMessage: "Lỗi xử lý: " + (data.message || data.error || "")
              });
            }
          } catch (err) {
            console.error("Lỗi khi parse dữ liệu SSE:", err);
          }
        });

        eventSource.onerror = (err) => {
          console.error("Lỗi kết nối SSE:", err);
          eventSource?.close();
          
          if (currentProgress < 100 && !currentIsCompleted) {
            if (retryCount < MAX_RETRIES) {
              retryCount++;
              setStatusMessage(`Mất kết nối. Đang thử kết nối lại... (${retryCount}/${MAX_RETRIES})`);
              setTimeout(connectSSE, 3000);
            } else {
              setIsTranslating(false);
              setStatusMessage("Mất kết nối với máy chủ (SSE). Vui lòng thử lại.");
            }
          }
        };
      };

      connectSSE();

    } catch (err: any) {
      console.error(err);
      setIsTranslating(false);
      setStatusMessage("Lỗi kết nối API: " + err.message);
    }
  };

  const baseUrl = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
  const token = getToken();
  const pdfUrl = docId ? `${baseUrl}/api/v1/documents/${docId}/download${token ? `?token=${token}` : ""}` : "";

  const handleOpenPdfNewTab = () => {
    if (!pdfUrl) return;
    window.open(pdfUrl, "_blank");
  };

  const handleDownloadFile = () => {
    if (!pdfUrl) return;
    const link = document.createElement("a");
    link.href = pdfUrl;
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyText = () => {
    if (!translatedText) return;
    navigator.clipboard.writeText(translatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenDeckModal = async () => {
    if (selectedGlossaryIndices.size === 0) {
      alert("Vui lòng chọn ít nhất một thuật ngữ để lưu.");
      return;
    }
    setIsDeckModalOpen(true);
    setIsLoadingDecks(true);

    let allDecks: BackendDeck[] = [];
    try {
      const res = await fetchBackendDecks();
      if (res.ok && res.data && res.data.length > 0) {
        allDecks = [...res.data];
      }
    } catch (e) {
      console.warn("fetchBackendDecks failed in DocumentTranslationPage:", e);
    }

    // Merge with local storage
    const local = getDecks();
    for (const ld of local) {
      if (!allDecks.some((d) => d.id === ld.id)) {
        allDecks.push({
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

    setAvailableDecks(allDecks);

    if (allDecks.length > 0) {
      const match = allDecks.find((d) => (d.lang_code || d.langCode) === sourceLang);
      setSelectedDeckId(match ? match.id : allDecks[0].id);
      setDeckOption("existing");
    } else {
      setDeckOption("new");
      const meta = LANG_CONFIG[sourceLang] || { defaultTitle: `Sổ từ vựng ${sourceLang.toUpperCase()}` };
      setNewDeckTitle(meta.defaultTitle);
    }

    setIsLoadingDecks(false);
  };

  const handleSaveKeywordsToDeck = async () => {
    if (selectedGlossaryIndices.size === 0) return;
    setIsSavingCards(true);

    try {
      let targetDeckId = selectedDeckId;
      let targetDeckTitle = "";

      if (deckOption === "new") {
        const meta = LANG_CONFIG[sourceLang] || { defaultTitle: `Sổ từ vựng ${sourceLang.toUpperCase()}` };
        const title = newDeckTitle.trim() || meta.defaultTitle;
        const desc = `Trích xuất từ tài liệu: ${selectedFile?.name || "Bản dịch PDF"}`;

        try {
          const deckRes = await createBackendDeck(title, desc, sourceLang);
          if (deckRes.ok && deckRes.data) {
            targetDeckId = deckRes.data.id;
            targetDeckTitle = deckRes.data.title;
            // Đồng bộ LocalStorage
            createCustomDeck(sourceLang, targetDeckTitle, desc, targetDeckId);
          } else {
            const localDeck = createCustomDeck(sourceLang, title, desc);
            targetDeckId = localDeck.id;
            targetDeckTitle = localDeck.title;
          }
        } catch {
          const localDeck = createCustomDeck(sourceLang, title, desc);
          targetDeckId = localDeck.id;
          targetDeckTitle = localDeck.title;
        }
      } else {
        const currentDeck = availableDecks.find((d) => d.id === selectedDeckId);
        targetDeckId = selectedDeckId;
        targetDeckTitle = currentDeck?.title || "Sổ thẻ";
      }

      const selectedItems = Array.from(selectedGlossaryIndices).map((i) => glossary[i]);
      let savedCount = 0;

      for (const item of selectedItems) {
        const termClean = (item.term || "").trim();
        const termTranslation = (item.translation || item.vi || "").trim();
        if (!termClean || !termTranslation) continue;

        // 1. Gửi request lưu thẻ lên Backend Flashcard Service
        try {
          await createBackendCard({
            deckId: targetDeckId,
            term: termClean,
            definition: termTranslation,
            phonetic: item.phonetic || undefined,
            exampleSentence: item.context || `Trích xuất từ tài liệu: ${selectedFile?.name || "Bản dịch"}`,
            partOfSpeech: "phrase",
            langCode: sourceLang
          });
        } catch (err) {
          console.warn("createBackendCard fallback to local:", err);
        }

        // 2. Luôn đồng bộ vào LocalStorage để sẵn sàng hiển thị ngay cả khi offline
        addCardToDeck(
          sourceLang,
          termClean,
          termTranslation,
          item.context || `Trích xuất từ tài liệu: ${selectedFile?.name || "Bản dịch"}`,
          "phrase",
          targetDeckId
        );
        savedCount++;
      }

      setSaveSuccessDetail({ count: savedCount, deckTitle: targetDeckTitle });
      setSavedKeywordsSuccess(true);
      setIsDeckModalOpen(false);
      setSelectedGlossaryIndices(new Set()); // Reset selections
      setTimeout(() => setSavedKeywordsSuccess(false), 7000);
    } catch (e: any) {
      console.error("Error saving cards", e);
      alert(e?.message || "Đã xảy ra lỗi khi lưu thẻ.");
    } finally {
      setIsSavingCards(false);
    }
  };

  const playAudio = (text: string, langCode: string) => {
    if (!text || !text.trim()) return;
    const voiceLang = langCode === "en" ? "en-US" : (langCode === "vi" ? "vi-VN" : langCode);
    const resolvedUrl = `${baseUrl}/api/v1/translate/tts?text=${encodeURIComponent(text.trim())}&lang=${voiceLang}`;

    const audio = new Audio(resolvedUrl);
    audio.play().catch((e) => {
      console.warn("Audio playback error, trying Web Speech API fallback...", e);
      try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = langCode === "en" ? "en-US" : langCode;
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error("SpeechSynthesis fallback failed:", err);
      }
    });
  };

  const toggleGlossaryItem = (index: number) => {
    const newSet = new Set(selectedGlossaryIndices);
    if (newSet.has(index)) newSet.delete(index);
    else newSet.add(index);
    setSelectedGlossaryIndices(newSet);
  };

  const toggleAllGlossary = () => {
    if (selectedGlossaryIndices.size === glossary.length) {
      setSelectedGlossaryIndices(new Set());
    } else {
      setSelectedGlossaryIndices(new Set(glossary.map((_, i) => i)));
    }
  };

  return (
    <div className="mx-auto flex h-full max-w-7xl flex-col p-4 sm:p-6">
      {/* Header Bar */}
      <div className="mb-4 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Languages className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-800">
              Dịch Thuật Tài Liệu PDF & Trích Xuất Từ Điển Học Thuật IUH
            </h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Dịch bài báo khoa học PDF giữ nguyên cấu trúc trang, hiển thị PDF bản dịch trực tiếp và trích xuất từ điển học vụ vào Flashcard
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/translation")}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <AlignLeft size={16} />
            <span>Dịch Văn Bản</span>
          </button>
          <button
            type="button"
            onClick={() => navigate("/flashcards")}
            className="flex items-center gap-1.5 rounded-xl border border-blue-200 bg-blue-50 px-3.5 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
          >
            <BookOpen size={16} />
            <span>Sổ Thẻ Flashcard</span>
          </button>
        </div>
      </div>

      {/* Language Selector Bar (Default: EN -> VI) */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Ngôn ngữ gốc:</span>
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-blue-500 focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={swapLanguages}
            title="Đổi chiều ngôn ngữ"
            className="rounded-full border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-600 transition-colors"
          >
            <ArrowRightLeft size={16} />
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Dịch sang:</span>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-blue-500 focus:outline-none"
            >
              {Object.entries(LANG_CONFIG).map(([code, meta]) => (
                <option key={code} value={code}>
                  {meta.flag} {meta.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={handleStartTranslate}
          disabled={isTranslating || !selectedFile}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          {isTranslating ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              <span>Đang dịch tài liệu PDF...</span>
            </>
          ) : (
            <>
              <Sparkles size={15} />
              <span>Bắt đầu dịch tài liệu</span>
            </>
          )}
        </button>
      </div>

      {/* Main Workspace: 2-Column Side-by-Side Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 flex-1">
        
        {/* LEFT COLUMN: Upload, Progress & Glossary */}
        <div className="space-y-4 lg:col-span-5 flex flex-col">
          {/* Upload Dropzone */}
          <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 p-5 text-center hover:bg-slate-100/50 transition-colors cursor-pointer">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="absolute inset-0 z-10 cursor-pointer opacity-0"
            />
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-red-100 text-red-600 shadow-sm">
              <FileText size={22} />
            </div>
            <div className="text-xs font-bold text-slate-800">
              Nhấp hoặc kéo thả tài liệu PDF học thuật
            </div>
            <div className="mt-1 text-[11px] text-slate-400">
              Hỗ trợ file PDF tối đa 10MB, giữ nguyên cấu trúc trang & bảng biểu
            </div>
          </div>

          {/* Selected File Card & Processing Progress */}
          {selectedFile && (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-red-50 border border-red-100 shadow-sm">
                    <FileText className="h-7 w-7 text-red-500" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800 break-all">
                      {selectedFile.name}
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-500">
                      <span>{selectedFile.size}</span>
                      <span>•</span>
                      <span>{selectedFile.pagesOrSlides}</span>
                    </div>
                  </div>
                </div>

                <span className="rounded-full bg-red-600 px-2.5 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                  PDF
                </span>
              </div>

              {/* Progress Bar & Status text */}
              {(isTranslating || progressPercent > 0 || isCompleted) && (
                <div className="mt-4 border-t border-slate-100 pt-3">
                  <div className="mb-1.5 flex items-center justify-between text-xs font-semibold">
                    <span className="text-slate-600">{statusMessage}</span>
                    <span className="text-blue-600 font-bold">{progressPercent}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-blue-600 transition-all duration-500"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Academic Glossary Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm flex-1 flex flex-col">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookMarked size={18} className="text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">
                  Từ Điển Thuật Ngữ IUH ({glossary.length})
                </span>
                {isExtractingGlossary && (
                  <span className="flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold text-indigo-700 animate-pulse">
                    <Loader2 size={11} className="animate-spin" />
                    <span>Đang trích xuất...</span>
                  </span>
                )}
              </div>

              {glossary.length > 0 && (
                <div className="flex items-center gap-3">
                  <button onClick={toggleAllGlossary} className="text-[11px] text-slate-500 hover:text-blue-600 font-medium transition-colors">
                    {selectedGlossaryIndices.size === glossary.length ? "Bỏ chọn tất cả" : "Chọn tất cả"}
                  </button>
                  <button
                    type="button"
                    onClick={handleOpenDeckModal}
                    disabled={selectedGlossaryIndices.size === 0}
                    className="flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1.5 text-[11px] font-bold text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-all active:scale-95"
                  >
                    <BookmarkPlus size={14} />
                    <span>Lưu thẻ ({selectedGlossaryIndices.size})</span>
                  </button>
                </div>
              )}
            </div>

            {savedKeywordsSuccess && (
              <div className="mb-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 p-3 text-xs font-medium text-emerald-900 shadow-sm animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600 text-white shrink-0 shadow-sm">
                    <CheckCircle2 size={16} />
                  </div>
                  <div>
                    <span className="font-bold text-emerald-800">Lưu Flashcard thành công!</span>
                    <p className="text-[11px] text-emerald-700 mt-0.5">
                      Đã lưu <strong>{saveSuccessDetail?.count || selectedGlossaryIndices.size} thuật ngữ</strong> vào sổ thẻ <strong>"{saveSuccessDetail?.deckTitle || "Sổ thẻ"}"</strong>.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => navigate("/flashcards")}
                  className="flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100/80 hover:bg-emerald-200/80 px-2.5 py-1.5 rounded-lg transition-all shrink-0 hover:shadow-xs active:scale-95 cursor-pointer"
                >
                  <span>Mở Flashcard</span>
                  <ExternalLink size={12} />
                </button>
              </div>
            )}

            {isExtractingGlossary && glossary.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center py-8 text-center bg-indigo-50/50 rounded-xl border border-dashed border-indigo-200 p-4 animate-pulse">
                <Loader2 size={24} className="mb-2 animate-spin text-indigo-600" />
                <span className="text-xs font-bold text-indigo-900">Đang phân tích & trích xuất thuật ngữ AI...</span>
                <span className="text-[11px] text-indigo-500 mt-1">Đang tạo phiên âm IPA và giọng phát âm chuẩn</span>
              </div>
            ) : glossary.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center py-8 text-center text-slate-400">
                <AlertCircle size={24} className="mb-1 text-slate-300" />
                <span className="text-xs">Chưa có thuật ngữ trích xuất</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Thuật ngữ sẽ tự động xuất hiện khi dịch tài liệu</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 overflow-y-auto max-h-[220px] pr-1">
                {glossary.map((g, i) => (
                  <div key={i} className={`relative rounded-xl border ${selectedGlossaryIndices.has(i) ? 'border-blue-400 bg-blue-50/50' : 'border-slate-200 bg-slate-50/70'} p-2.5 text-xs transition-all cursor-pointer group hover:border-blue-300 shadow-sm`} onClick={() => toggleGlossaryItem(i)}>
                    <div className="flex items-start justify-between mb-1.5">
                      <div className="flex items-start gap-2 max-w-[80%]">
                        <input type="checkbox" checked={selectedGlossaryIndices.has(i)} readOnly className="mt-0.5 rounded text-blue-600 border-slate-300 focus:ring-0 shrink-0" />
                        <div>
                           <div className="font-bold text-slate-800 break-words">{g.term}</div>
                           {g.phonetic && <div className="text-[10.5px] text-slate-500 font-mono mt-0.5">{g.phonetic}</div>}
                        </div>
                      </div>
                      
                      <button onClick={(e) => { e.stopPropagation(); playAudio(g.term, sourceLang); }} className="text-blue-600 hover:text-blue-800 hover:bg-blue-100/80 p-1.5 rounded-full transition-colors shrink-0 flex items-center justify-center bg-blue-50/50 cursor-pointer" title="Phát âm">
                        <Volume2 size={15} />
                      </button>
                    </div>
                    
                    <div className="text-blue-700 font-medium ml-[22px]">{g.translation || g.vi}</div>
                    {g.context && <div className="text-[10px] text-slate-400 ml-[22px] mt-1">{g.context}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Dedicated Translated Document Result Frame (PDF Embedded Viewer) */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="flex-1 rounded-2xl border border-slate-200 bg-white shadow-sm flex flex-col overflow-hidden min-h-[560px]">
            
            {/* Header of Result Frame */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-4 py-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                  <FileCheck size={18} />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-800">
                    Khung Hiển Thị Bản Dịch PDF
                  </h3>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500">
                    <span className="font-medium">{selectedFile?.title || "Chưa chọn tài liệu"}</span>
                    {selectedFile && (
                      <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[9px] font-bold text-blue-600 uppercase">
                        {sourceLang} ➔ {targetLang}
                      </span>
                    )}
                    {modelUsed && (
                      <span className="rounded bg-purple-50 px-1.5 py-0.5 text-[9px] font-bold text-purple-700">
                        🤖 {modelUsed}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Top Action Buttons */}
              <div className="flex items-center gap-2">
                {isCompleted && (
                  <button
                    type="button"
                    onClick={handleResetTranslation}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
                    title="Dịch tài liệu PDF khác"
                  >
                    <RotateCcw size={14} />
                    <span>Dịch file mới</span>
                  </button>
                )}

                {isCompleted && pdfUrl && (
                  <button
                    type="button"
                    onClick={handleOpenPdfNewTab}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
                    title="Mở PDF tab mới"
                  >
                    <ExternalLink size={14} />
                    <span>Mở Tab mới</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleCopyText}
                  disabled={!translatedText}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors shadow-sm"
                  title="Sao chép văn bản Markdown"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-green-600" />
                      <span className="text-green-600">Đã chép</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleDownloadFile}
                  disabled={!isCompleted}
                  className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-green-700 disabled:opacity-40 transition-all"
                >
                  <Download size={14} />
                  <span>Tải file PDF</span>
                </button>
              </div>
            </div>

            {/* Sub-Header Tabs */}
            <div className="flex border-b border-slate-100 bg-white px-4 pt-2">
              <button
                type="button"
                onClick={() => setActiveTab("pdf")}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-bold transition-colors ${
                  activeTab === "pdf"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                <FileType size={14} />
                <span>📄 File PDF Bản Dịch</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("markdown")}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-bold transition-colors ${
                  activeTab === "markdown"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                <Eye size={14} />
                <span>📝 Văn Bản Markdown</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("summary")}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-bold transition-colors ${
                  activeTab === "summary"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                <Sparkles size={14} />
                <span>📊 Tóm Tắt Nhanh</span>
              </button>
            </div>

            {/* Body Content Area */}
            <div className="flex-1 p-3 overflow-hidden bg-slate-100/60 flex flex-col">
              
              {/* LOADING STATE */}
              {isTranslating && !isCompleted && (
                <div className="flex h-full flex-col items-center justify-center py-20 text-center">
                  <Loader2 size={38} className="animate-spin text-blue-600 mb-3" />
                  <div className="text-sm font-bold text-slate-800">
                    Đang dịch & render file PDF bản dịch...
                  </div>
                  <div className="mt-1 text-xs text-slate-500 max-w-sm">
                    {statusMessage} ({progressPercent}%)
                  </div>
                </div>
              )}

              {/* EMPTY STATE */}
              {!isTranslating && !isCompleted && (
                <div className="flex h-full flex-col items-center justify-center py-20 text-center">
                  <FileText size={42} className="text-slate-300 mb-3" />
                  <div className="text-sm font-bold text-slate-700">Chưa có bản dịch PDF</div>
                  <div className="mt-1 text-xs text-slate-400 max-w-xs leading-relaxed">
                    Vui lòng chọn tài liệu PDF tiếng Anh và nhấn <strong>"Bắt đầu dịch tài liệu"</strong> để xem file PDF bản dịch trực tiếp tại đây.
                  </div>
                </div>
              )}

              {/* COMPLETED TAB CONTENT */}
              {isCompleted && (
                <div className="flex-1 flex flex-col overflow-hidden h-full">
                  {/* TAB 1: PDF EMBEDDED VIEWER */}
                  {activeTab === "pdf" && (
                    <div className="flex-1 w-full h-full min-h-[500px] rounded-xl overflow-hidden border border-slate-200 bg-slate-900 shadow-inner flex flex-col">
                      <object
                        data={`${pdfUrl}#toolbar=1&navpanes=0&view=FitH`}
                        type="application/pdf"
                        className="w-full h-full min-h-[500px] flex-1"
                      >
                        <iframe
                          src={`${pdfUrl}#toolbar=1&navpanes=0&view=FitH`}
                          className="w-full h-full min-h-[500px] flex-1 border-0"
                          title="PDF Viewer"
                        >
                          <div className="flex h-full flex-col items-center justify-center p-6 text-center text-white">
                            <p className="text-xs mb-2">Trình duyệt không hỗ trợ nhúng trực tiếp PDF.</p>
                            <button
                              type="button"
                              onClick={handleOpenPdfNewTab}
                              className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-bold text-white shadow hover:bg-blue-700 transition-all"
                            >
                              Xem PDF ở Tab Mới
                            </button>
                          </div>
                        </iframe>
                      </object>
                    </div>
                  )}

                  {/* TAB 2: MARKDOWN TEXT PREVIEW */}
                  {activeTab === "markdown" && (
                    <div className="flex-1 p-2 overflow-y-auto max-h-[520px]">
                      <div className="rounded-xl border border-slate-200 bg-white p-5 text-xs text-slate-800 shadow-sm leading-relaxed whitespace-pre-wrap font-sans">
                        {translatedText || "Không có văn bản Markdown."}
                      </div>
                    </div>
                  )}

                  {/* TAB 3: SUMMARY */}
                  {activeTab === "summary" && (
                    <div className="flex-1 p-2 space-y-4 overflow-y-auto max-h-[520px]">
                      <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
                        <div className="flex items-center gap-2 font-bold text-blue-900 text-xs mb-1">
                          <Sparkles size={16} className="text-blue-600" />
                          <span>Tóm Tắt Tổng Quan Tài Liệu</span>
                        </div>
                        <p className="text-xs text-blue-800 leading-relaxed">
                          Nội dung tài liệu đã được dịch thành công và render thành định dạng file PDF chuẩn giữ nguyên cấu trúc trình bày.
                        </p>
                      </div>

                      {glossary.length > 0 && (
                        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-2">
                          <div className="font-bold text-slate-800 text-xs mb-2">Từ vựng & Thuật ngữ trích xuất ({glossary.length}):</div>
                          {glossary.slice(0, 8).map((g, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-slate-700">
                              <CheckCircle2 size={15} className="text-green-600 flex-shrink-0 mt-0.5" />
                              <span><strong>{g.term}</strong>: {g.translation || g.vi}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer Bar of Result Frame */}
            <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/80 px-4 py-2.5 text-[11px] text-slate-500">
              <div className="flex items-center gap-3">
                <span>Trình xem PDF Trực Tiếp</span>
                <span>•</span>
                <span>File ID: {docId ? docId.slice(0, 12) : "N/A"}</span>
              </div>

              {isCompleted && (
                <div className="flex items-center gap-2 text-green-700 font-semibold">
                  <CheckCircle2 size={13} className="text-green-600" />
                  <span>PDF Rendered & Ready</span>
                </div>
              )}
            </div>

          </div>
        </div>

      </div>
      {/* Deck Selection Modal */}
      {isDeckModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl border border-slate-100">
            <h3 className="mb-1 text-lg font-bold text-slate-800 flex items-center gap-2">
              <BookmarkPlus size={20} className="text-blue-600"/>
              Lưu Thẻ Flashcard
            </h3>
            <p className="mb-4 text-xs text-slate-500 leading-relaxed">
              Bạn đang lưu <strong className="text-slate-700">{selectedGlossaryIndices.size} thuật ngữ</strong>. Vui lòng chọn sổ thẻ đích:
            </p>

            {isLoadingDecks ? (
              <div className="flex items-center justify-center py-6 gap-2 text-xs text-slate-500">
                <Loader2 size={18} className="animate-spin text-blue-600" />
                <span>Đang tải danh sách sổ thẻ...</span>
              </div>
            ) : (
              <div className="space-y-4">
                <label className="flex flex-col gap-2 cursor-pointer group">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 group-hover:text-blue-600 transition-colors">
                    <input type="radio" name="deckOption" value="existing" checked={deckOption === "existing"} onChange={() => setDeckOption("existing")} className="text-blue-600 focus:ring-0 border-slate-300 w-4 h-4" />
                    Lưu vào sổ thẻ hiện có
                  </div>
                  {deckOption === "existing" && (
                    <select
                      value={selectedDeckId}
                      onChange={(e) => setSelectedDeckId(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs font-medium text-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none ml-6 max-w-[90%] shadow-sm transition-all"
                    >
                      {availableDecks.map(d => (
                        <option key={d.id} value={d.id}>{d.icon_flag || d.iconFlag || "🌐"} {d.title} ({d.cards_count || 0} thẻ)</option>
                      ))}
                      {availableDecks.length === 0 && <option value="" disabled>Chưa có sổ thẻ nào</option>}
                    </select>
                  )}
                </label>

                <label className="flex flex-col gap-2 cursor-pointer group mt-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 group-hover:text-blue-600 transition-colors">
                    <input type="radio" name="deckOption" value="new" checked={deckOption === "new"} onChange={() => setDeckOption("new")} className="text-blue-600 focus:ring-0 border-slate-300 w-4 h-4" />
                    Tạo sổ thẻ mới
                  </div>
                  {deckOption === "new" && (
                    <input
                      type="text"
                      placeholder={`Nhập tên sổ thẻ mới... (VD: Sổ từ ${sourceLang.toUpperCase()})`}
                      value={newDeckTitle}
                      onChange={(e) => setNewDeckTitle(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs font-medium text-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none ml-6 max-w-[90%] shadow-sm transition-all placeholder:text-slate-400"
                    />
                  )}
                </label>
              </div>
            )}

            <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsDeckModalOpen(false)}
                disabled={isSavingCards}
                className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors disabled:opacity-50 cursor-pointer"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={handleSaveKeywordsToDeck}
                disabled={isSavingCards || isLoadingDecks || (deckOption === "existing" && !selectedDeckId) || (deckOption === "new" && !newDeckTitle.trim())}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow-sm cursor-pointer"
              >
                {isSavingCards ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Đang lưu...</span>
                  </>
                ) : (
                  <>
                    <BookmarkPlus size={14} />
                    <span>Lưu Thẻ ({selectedGlossaryIndices.size})</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Privacy Policy Note */}
      <div className="mt-4 flex items-center gap-2.5 rounded-xl bg-slate-50 border border-slate-200 px-4 py-2.5 text-[11px] text-slate-500 shadow-sm">
        <ShieldCheck size={16} className="text-blue-600 shrink-0" />
        <span>
          <strong>Lưu ý bảo mật:</strong> Nội dung tài liệu và kết quả dịch chỉ được lưu tạm thời trong phiên làm việc hiện tại. Nếu bạn tải lại trang (F5 / Reload), dữ liệu vẫn được giữ nguyên. Tuy nhiên, khi bạn chuyển sang trang khác, quay lại trang trước hoặc đăng xuất, toàn bộ dữ liệu sẽ tự động được xóa để bảo mật.
        </span>
      </div>
    </div>
  );
}

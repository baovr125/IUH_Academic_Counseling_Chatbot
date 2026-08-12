import { useState } from "react";
import {
  FileText,
  UploadCloud,
  Download,
  Sparkles,
  CheckCircle2,
  Languages,
  File,
  ArrowRightLeft,
  BookOpen,
  BookmarkPlus,
  Loader2,
  Presentation,
  AlignLeft,
  Copy,
  Check,
  BookMarked,
  FileCheck,
  Search,
  MessageSquare,
  Eye,
  AlertCircle,
  ExternalLink,
  FileType
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { LANG_CONFIG, addCardToDeck } from "../services/deckStorage";

interface DocumentFile {
  id?: string;
  name: string;
  type: "pdf" | "docx" | "pptx";
  size: string;
  pagesOrSlides: string;
  title: string;
}

interface GlossaryItem {
  term: string;
  vi: string;
  context?: string;
}

export default function DocumentTranslationPage() {
  const navigate = useNavigate();

  // Language & Selection state (Default: English -> Vietnamese)
  const [sourceLang, setSourceLang] = useState("en");
  const [targetLang, setTargetLang] = useState("vi");
  const [selectedFile, setSelectedFile] = useState<DocumentFile | null>(null);
  const [actualFile, setActualFile] = useState<File | null>(null);

  // Processing state
  const [docId, setDocId] = useState<string>("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Vui lòng chọn tài liệu để bắt đầu");
  const [modelUsed, setModelUsed] = useState<string>("");
  const [isCompleted, setIsCompleted] = useState(false);
  const [savedKeywordsSuccess, setSavedKeywordsSuccess] = useState(false);

  // Translated Result Frame State
  const [translatedText, setTranslatedText] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"pdf" | "markdown" | "summary" | "rag">("pdf");

  // RAG Query state within Result Frame
  const [ragQuery, setRagQuery] = useState("");
  const [ragAnswer, setRagAnswer] = useState<string | null>(null);
  const [isRagQuerying, setIsRagQuerying] = useState(false);

  // Extracted Glossary from real document processing
  const [glossary, setGlossary] = useState<GlossaryItem[]>([]);

  const swapLanguages = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      alert("Kích thước file vượt quá giới hạn 10MB. Vui lòng chọn file nhỏ hơn.");
      return;
    }

    let type: "pdf" | "docx" | "pptx" = "pdf";
    if (file.name.endsWith(".pptx") || file.name.endsWith(".ppt")) type = "pptx";
    else if (file.name.endsWith(".docx") || file.name.endsWith(".doc")) type = "docx";

    const newDocId = `doc_${Date.now()}`;
    setDocId(newDocId);
    setActualFile(file);
    setSelectedFile({
      id: newDocId,
      name: file.name,
      type,
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      pagesOrSlides: type === "pptx" ? "PowerPoint" : "Document",
      title: file.name.replace(/\.[^/.]+$/, ""),
    });
    setIsCompleted(false);
    setProgressPercent(0);
    setStatusMessage("Tài liệu đã sẵn sàng để dịch");
    setTranslatedText("");
    setGlossary([]);
    setRagAnswer(null);
  };

  const handleStartTranslate = async () => {
    if (!actualFile) {
      alert("Vui lòng tải lên một tài liệu (PDF, Word, PowerPoint) từ máy tính của bạn.");
      return;
    }

    setIsTranslating(true);
    setIsCompleted(false);
    setProgressPercent(5);
    setStatusMessage("Đang tải tài liệu lên hệ thống AI...");

    try {
      const formData = new FormData();
      formData.append("file", actualFile);
      formData.append("source_lang", sourceLang);
      formData.append("target_lang", targetLang);

      const baseUrl = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
      
      const uploadRes = await fetch(`${baseUrl}/api/v1/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error("Lỗi tải lên tài liệu: " + uploadRes.statusText);
      }

      const uploadData = await uploadRes.json();
      const currentDocId = uploadData.data.doc_id;
      setDocId(currentDocId);

      // Nhận luồng SSE real progress từ backend
      const eventSource = new EventSource(`${baseUrl}/api/v1/documents/${currentDocId}/stream`);

      eventSource.addEventListener("update", (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.progress !== undefined) setProgressPercent(data.progress);
          if (data.message) setStatusMessage(data.message);
          if (data.model_used) setModelUsed(data.model_used);
          if (data.glossary && data.glossary.length > 0) setGlossary(data.glossary);
          if (data.translated_text) setTranslatedText(data.translated_text);

          const statusLower = data.status ? String(data.status).toLowerCase() : "";
          if (statusLower === "completed") {
            eventSource.close();
            setIsTranslating(false);
            setIsCompleted(true);
            setActiveTab("pdf"); // Switch directly to PDF view on completion
          } else if (statusLower === "failed") {
            eventSource.close();
            setIsTranslating(false);
            setStatusMessage("Lỗi xử lý: " + (data.message || data.error || ""));
          }
        } catch (err) {
          console.error("Lỗi khi parse dữ liệu SSE:", err);
        }
      });

      eventSource.onerror = (err) => {
        console.error("Lỗi kết nối SSE:", err);
        eventSource.close();
        // Không set lỗi ngay lập tức nếu tiến trình chưa hoàn thành,
        // nhưng nếu ngắt kết nối thì báo lỗi.
        if (progressPercent < 100 && !isCompleted) {
          setIsTranslating(false);
          setStatusMessage("Mất kết nối với máy chủ (SSE). Vui lòng thử lại.");
        }
      };

    } catch (err: any) {
      console.error(err);
      setIsTranslating(false);
      setStatusMessage("Lỗi kết nối API: " + err.message);
    }
  };

  const baseUrl = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
  const pdfUrl = docId ? `${baseUrl}/api/v1/documents/${docId}/download` : "";

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

  const handleSaveKeywordsToDeck = () => {
    if (!selectedFile || glossary.length === 0) return;

    glossary.forEach((item) => {
      addCardToDeck(
        targetLang,
        item.term,
        item.vi,
        `Trích xuất từ tài liệu: ${selectedFile.name}`,
        "noun"
      );
    });

    setSavedKeywordsSuccess(true);
    setTimeout(() => setSavedKeywordsSuccess(false), 4000);
  };

  const handleRagQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragQuery.trim() || !docId) return;

    setIsRagQuerying(true);
    try {
      const res = await fetch(`${baseUrl}/api/v1/documents/${docId}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: ragQuery }),
      });

      if (res.ok) {
        const data = await res.json();
        setRagAnswer(data.data.answer);
      } else {
        setRagAnswer("Không thể truy vấn thông tin từ tài liệu này. Vui lòng kiểm tra lại bản dịch.");
      }
    } catch {
      setRagAnswer("Không thể kết nối với dịch vụ RAG.");
    } finally {
      setIsRagQuerying(false);
    }
  };

  const getFileIcon = (type: "pdf" | "docx" | "pptx") => {
    if (type === "pdf") return <FileText className="h-7 w-7 text-red-500" />;
    if (type === "pptx") return <Presentation className="h-7 w-7 text-orange-500" />;
    return <File className="h-7 w-7 text-blue-500" />;
  };

  return (
    <div className="mx-auto flex h-full max-w-7xl flex-col p-4 sm:p-6">
      {/* Header Bar */}
      <div className="mb-4 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Languages className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-800">
              Dịch Thuật & Document RAG Workspace (PDF / PPT / Word)
            </h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Dịch tài liệu giữ nguyên cấu trúc, hiển thị bản dịch PDF trực tiếp và trích xuất từ điển học vụ IUH
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
              <span>Đang dịch tài liệu...</span>
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
              accept=".pdf,.docx,.doc,.pptx,.ppt"
              onChange={handleFileUpload}
              className="absolute inset-0 z-10 cursor-pointer opacity-0"
            />
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 shadow-sm">
              <UploadCloud size={22} />
            </div>
            <div className="text-xs font-bold text-slate-800">
              Nhấp hoặc kéo thả tài liệu (PDF, Word, PowerPoint)
            </div>
            <div className="mt-1 text-[11px] text-slate-400">
              Hỗ trợ file tối đa 10MB, giữ nguyên định dạng trang
            </div>
          </div>

          {/* Selected File Card & Processing Progress */}
          {selectedFile && (
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-slate-50 border border-slate-100 shadow-sm">
                    {getFileIcon(selectedFile.type)}
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

                <span className="rounded-full bg-blue-600 px-2.5 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                  {selectedFile.type}
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
              </div>

              {glossary.length > 0 && (
                <button
                  type="button"
                  onClick={handleSaveKeywordsToDeck}
                  className="flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
                >
                  <BookmarkPlus size={13} />
                  <span>Lưu Thẻ Flashcard</span>
                </button>
              )}
            </div>

            {savedKeywordsSuccess && (
              <div className="mb-3 flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 p-2.5 text-xs font-medium text-green-800">
                <CheckCircle2 size={15} className="text-green-600" />
                <span>Đã lưu thành công thuật ngữ vào Flashcard!</span>
              </div>
            )}

            {glossary.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center py-8 text-center text-slate-400">
                <AlertCircle size={24} className="mb-1 text-slate-300" />
                <span className="text-xs">Chưa có thuật ngữ trích xuất</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Thuật ngữ sẽ tự động xuất hiện khi dịch tài liệu</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 overflow-y-auto max-h-[220px] pr-1">
                {glossary.map((g, i) => (
                  <div key={i} className="rounded-xl border border-slate-100 bg-slate-50/70 p-2.5 text-xs">
                    <div className="font-bold text-slate-800">{g.term}</div>
                    <div className="text-blue-600 font-medium mt-0.5">{g.vi}</div>
                    {g.context && <div className="text-[10px] text-slate-400 mt-0.5">{g.context}</div>}
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
                    Khung Hiển Thị Kết Quả Dịch (PDF Viewer)
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

              <button
                type="button"
                onClick={() => setActiveTab("rag")}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-bold transition-colors ${
                  activeTab === "rag"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                <MessageSquare size={14} />
                <span>🔍 Tra Cứu RAG</span>
              </button>
            </div>

            {/* Body Content Area */}
            <div className="flex-1 p-3 overflow-hidden bg-slate-100/60 flex flex-col">
              
              {/* LOADING STATE */}
              {isTranslating && (
                <div className="flex h-full flex-col items-center justify-center py-20 text-center">
                  <Loader2 size={38} className="animate-spin text-blue-600 mb-3" />
                  <div className="text-sm font-bold text-slate-800">Đang dịch & render file PDF...</div>
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
                    Vui lòng chọn tài liệu tiếng Anh (PDF/Word/PPT) và nhấn <strong>"Bắt đầu dịch tài liệu"</strong> để hiển thị file PDF bản dịch tại đây.
                  </div>
                </div>
              )}

              {/* COMPLETED TAB CONTENT */}
              {!isTranslating && isCompleted && (
                <div className="flex-1 flex flex-col overflow-hidden h-full">
                  {/* TAB 1: EMBEDDED PDF VIEWER */}
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
                          <div className="font-bold text-slate-800 text-xs mb-2">Từ vựng & Thuật ngữ trích xuất:</div>
                          {glossary.slice(0, 8).map((g, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-slate-700">
                              <CheckCircle2 size={15} className="text-green-600 flex-shrink-0 mt-0.5" />
                              <span><strong>{g.term}</strong>: {g.vi}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 4: RAG QUERY */}
                  {activeTab === "rag" && (
                    <div className="flex-1 p-2 space-y-4 overflow-y-auto max-h-[520px]">
                      <form onSubmit={handleRagQuery} className="flex gap-2">
                        <input
                          type="text"
                          value={ragQuery}
                          onChange={(e) => setRagQuery(e.target.value)}
                          placeholder="Hỏi bất kỳ điều gì về nội dung tài liệu này..."
                          className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none shadow-sm"
                        />
                        <button
                          type="submit"
                          disabled={isRagQuerying || !ragQuery.trim()}
                          className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm"
                        >
                          {isRagQuerying ? (
                            <Loader2 size={15} className="animate-spin" />
                          ) : (
                            <Search size={15} />
                          )}
                          <span>Truy vấn</span>
                        </button>
                      </form>

                      {ragAnswer && (
                        <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-indigo-950">
                          <div className="flex items-center gap-2 font-bold text-indigo-900 mb-1">
                            <MessageSquare size={15} className="text-indigo-600" />
                            <span>Kết Quả Hỏi Đáp RAG:</span>
                          </div>
                          <p className="leading-relaxed">{ragAnswer}</p>
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
                  <span>PDF Rendered & Indexed</span>
                </div>
              )}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

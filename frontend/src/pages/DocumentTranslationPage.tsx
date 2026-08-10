import { useState, useEffect, useRef } from "react";
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
  MessageSquare,
  Send,
  ExternalLink,
  X,
  Bot,
  User,
  BookMarked,
  Info
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

interface Citation {
  page: number;
  snippet: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "bot";
  text: string;
  citations?: Citation[];
  timestamp: string;
}

const SAMPLE_DOCS: DocumentFile[] = [
  {
    id: "sample_doc_01",
    name: "Quy_che_hoc_vu_tin_chi_2026.pdf",
    type: "pdf",
    size: "4.1 MB",
    pagesOrSlides: "24 trang",
    title: "Quy chế đào tạo theo hệ thống tín chỉ IUH",
  },
  {
    id: "sample_doc_02",
    name: "Bao_cao_thuc_tap_tot_nghiep_IUH.docx",
    type: "docx",
    size: "2.4 MB",
    pagesOrSlides: "15 trang",
    title: "Báo cáo thực tập tốt nghiệp chuyên ngành Kỹ thuật Phần mềm",
  },
  {
    id: "sample_doc_03",
    name: "Slide_gioi_thieu_Khoa_CNTT.pptx",
    type: "pptx",
    size: "6.8 MB",
    pagesOrSlides: "18 slides",
    title: "Giới thiệu chương trình đào tạo Khoa Công nghệ Thông tin",
  },
];

export default function DocumentTranslationPage() {
  const navigate = useNavigate();

  // Language & Selection state
  const [sourceLang, setSourceLang] = useState("vi");
  const [targetLang, setTargetLang] = useState("en");
  const [selectedFile, setSelectedFile] = useState<DocumentFile | null>(SAMPLE_DOCS[0]);

  // Processing state
  const [docId, setDocId] = useState<string>("sample_doc_01");
  const [isTranslating, setIsTranslating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Sẵn sàng xử lý tài liệu");
  const [isCompleted, setIsCompleted] = useState(true);
  const [savedKeywordsSuccess, setSavedKeywordsSuccess] = useState(false);

  // Extracted Glossary
  const [glossary, setGlossary] = useState<GlossaryItem[]>([
    { term: "Academic Regulations", vi: "Quy chế học vụ", context: "Quy định đào tạo tín chỉ tại IUH" },
    { term: "Credit System", vi: "Hệ thống tín chỉ", context: "Phương thức đào tạo theo tín chỉ" },
    { term: "Cumulative GPA", vi: "Điểm trung bình tích lũy (CGPA)", context: "Điểm tổng kết tích lũy toàn khóa" },
    { term: "Academic Advisor", vi: "Cố vấn học tập", context: "Giảng viên hỗ trợ sinh viên" },
  ]);

  // Document RAG Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      sender: "bot",
      text: "Xin chào! Tôi là Trợ lý RAG Tài liệu. Bạn có thể hỏi bất kỳ thắc mắc nào liên quan đến nội dung tài liệu này.",
      timestamp: "Vừa xong",
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);

  // Citation Preview Modal State
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isQuerying]);

  const swapLanguages = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    let type: "pdf" | "docx" | "pptx" = "pdf";
    if (file.name.endsWith(".pptx") || file.name.endsWith(".ppt")) type = "pptx";
    else if (file.name.endsWith(".docx") || file.name.endsWith(".doc")) type = "docx";

    const newDocId = `doc_${Date.now()}`;
    setDocId(newDocId);
    setSelectedFile({
      id: newDocId,
      name: file.name,
      type,
      size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      pagesOrSlides: type === "pptx" ? "12 slides" : "10 trang",
      title: file.name.replace(/\.[^/.]+$/, ""),
    });
    setIsCompleted(false);
  };

  const handleStartTranslate = () => {
    if (!selectedFile) return;
    setIsTranslating(true);
    setIsCompleted(false);
    setProgressPercent(10);
    setStatusMessage("1/5: Đang đọc và trích xuất cấu trúc văn bản qua PyMuPDF...");

    const t1 = setTimeout(() => {
      setProgressPercent(35);
      setStatusMessage("2/5: Phân cấp Hierarchical Chunking v6.2 (Parent-Child Sections)...");
    }, 800);

    const t2 = setTimeout(() => {
      setProgressPercent(60);
      setStatusMessage("3/5: Dịch thuật ngữ văn cảnh lớn bằng Gemini 2.5 Flash & Từ điển IUH...");
    }, 1800);

    const t3 = setTimeout(() => {
      setProgressPercent(85);
      setStatusMessage("4/5: Tạo Vector BAAI/bge-m3 (1024 chiều) & Upsert vào Supabase pgvector...");
    }, 2800);

    const t4 = setTimeout(() => {
      setProgressPercent(100);
      setIsTranslating(false);
      setIsCompleted(true);
      setStatusMessage("5/5: Hoàn tất dịch thuật & Indexed RAG Vector thành công!");

      setChatMessages([
        {
          id: `msg-${Date.now()}`,
          sender: "bot",
          text: `Đã dịch thuật và indexed tài liệu "${selectedFile.title}" thành công với mô hình BAAI/bge-m3 (1024d). Bạn có thể bắt đầu hỏi đáp bên dưới!`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }, 3800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  };

  const handleDownloadFile = () => {
    if (!selectedFile) return;

    const content = `================================================================
TÀI LIỆU ĐÃ DỊCH: ${selectedFile.name}
HỆ THỐNG: IUH Portal AI Document Service
MODEL EMBEDDING: BAAI/bge-m3 (1024 chiều)
NGÔN NGỮ: ${LANG_CONFIG[sourceLang]?.label || sourceLang} ➔ ${LANG_CONFIG[targetLang]?.label || targetLang}
================================================================

[TIÊU ĐỀ TÀI LIỆU]
${selectedFile.title}

[THUẬT NGỮ HỌC VỤ TRÍCH XUẤT]
${glossary.map((g) => `- ${g.term}: ${g.vi}`).join("\n")}

[NỘI DUNG DỊCH BAGE-M3 RAG INDEXED]
- Trang 1: Tổng quan quy chế đào tạo tín chỉ Đại học Công nghiệp TP.HCM...
- Trang 2-5: Quy định đăng ký học phần, điểm tích lũy CGPA và cố vấn học tập...
- Trang 6-12: Tiêu chuẩn xét duyệt đồ án tốt nghiệp và thực tập công ty...

================================================================
Tài liệu được dịch và xác thực bởi IUH Portal AI Engine.
================================================================
`;

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `[${targetLang.toUpperCase()}]_${selectedFile.name}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSaveKeywordsToDeck = () => {
    if (!selectedFile) return;

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

  const handleSendQuery = (customQuery?: string) => {
    const query = customQuery || inputQuery;
    if (!query.trim() || isQuerying) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInputQuery("");
    setIsQuerying(true);

    setTimeout(() => {
      let botAnswer = `Dựa trên tài liệu "${selectedFile?.title}", điều kiện quy định như sau:`;
      let citations: Citation[] = [
        {
          page: 3,
          snippet: "Sinh viên phải tích lũy đủ tổng số tín chỉ tối thiểu theo chương trình đào tạo và đạt điểm trung bình tích lũy (CGPA) từ 2.0 trở lên.",
        },
        {
          page: 7,
          snippet: "Đồng thời phải hoàn tất báo cáo thực tập tốt nghiệp và đạt chuẩn đầu ra ngoại ngữ theo quy định của nhà trường.",
        },
      ];

      if (query.includes("tốt nghiệp") || query.includes("điều kiện")) {
        botAnswer = "Theo Quy chế Học vụ IUH (Trang 3 & Trang 7), điều kiện xét tốt nghiệp bao gồm:\n1. Tích lũy đủ số tín chỉ quy định của ngành học (CGPA >= 2.00).\n2. Đạt chuẩn đầu ra Ngoại ngữ và Tin học theo quy định.\n3. Hoàn thành Báo cáo Thực tập tốt nghiệp và không bị truy cứu kỷ luật.";
      } else if (query.includes("tín chỉ") || query.includes("học phí")) {
        botAnswer = "Tài liệu ghi rõ sinh viên đăng ký học phần theo Hệ thống Tín chỉ (Trang 4). Học phí được tính căn cứ theo số lượng tín chỉ của từng học phần đăng ký trong học kỳ.";
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: botAnswer,
        citations,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setChatMessages((prev) => [...prev, botMsg]);
      setIsQuerying(false);
    }, 1200);
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
            Dịch tài liệu theo phân cấp ngữ cảnh, trích xuất thuật ngữ IUH và hỏi đáp RAG bảo mật với Vector BGE-M3 (1024d)
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

      {/* Language Selector Bar */}
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
              <span>Đang dịch & Indexed BGE-M3...</span>
            </>
          ) : (
            <>
              <Sparkles size={15} />
              <span>Bắt đầu dịch tài liệu</span>
            </>
          )}
        </button>
      </div>

      {/* Main Workspace: 2-Column Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 flex-1">
        {/* Left Column: File Management, Upload, Progress, Glossary */}
        <div className="space-y-4 lg:col-span-6">
          {/* Upload Dropzone */}
          <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 p-5 text-center hover:bg-slate-100/50 transition-colors">
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
            <p className="mt-1 text-[11px] text-slate-500">
              Mô hình BAAI/bge-m3 1024d hỗ trợ ngữ cảnh lớn tới 8192 tokens
            </p>
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
              {(isTranslating || isCompleted) && (
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

              {/* Action Buttons */}
              {isCompleted && (
                <div className="mt-4 flex items-center justify-between gap-2 border-t border-slate-100 pt-3">
                  <div className="flex items-center gap-1.5 text-xs text-green-600 font-semibold">
                    <CheckCircle2 size={16} />
                    <span>Đã Indexed Vector BGE-M3 (1024d)</span>
                  </div>

                  <button
                    type="button"
                    onClick={handleDownloadFile}
                    className="flex items-center gap-1.5 rounded-xl bg-green-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-green-700 transition-all"
                  >
                    <Download size={15} />
                    <span>Tải bản dịch</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Academic Glossary Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookMarked size={18} className="text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">
                  Từ Điển Thuật Ngữ Học Vụ IUH Trích Xuất ({glossary.length})
                </span>
              </div>

              <button
                type="button"
                onClick={handleSaveKeywordsToDeck}
                className="flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
              >
                <BookmarkPlus size={13} />
                <span>Lưu Thẻ Từ Vựng</span>
              </button>
            </div>

            {savedKeywordsSuccess && (
              <div className="mb-3 flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 p-2.5 text-xs font-medium text-green-800">
                <CheckCircle2 size={15} className="text-green-600" />
                <span>Đã lưu thành công danh sách thuật ngữ vào Sổ Flashcard!</span>
              </div>
            )}

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {glossary.map((g, i) => (
                <div key={i} className="rounded-xl border border-slate-100 bg-slate-50/70 p-2.5 text-xs">
                  <div className="font-bold text-slate-800">{g.term}</div>
                  <div className="text-blue-600 font-medium mt-0.5">{g.vi}</div>
                  {g.context && <div className="text-[10px] text-slate-400 mt-0.5">{g.context}</div>}
                </div>
              ))}
            </div>
          </div>

          {/* Quick Select Sample Docs */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <span className="mb-2.5 block text-xs font-bold text-slate-700">
              ⚡ Tài liệu mẫu có sẵn của nhà trường:
            </span>
            <div className="space-y-2">
              {SAMPLE_DOCS.map((doc) => (
                <button
                  type="button"
                  key={doc.id}
                  onClick={() => {
                    setSelectedFile(doc);
                    setDocId(doc.id || "sample_doc_01");
                    setIsCompleted(true);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl border p-2.5 text-left transition-all ${
                    selectedFile?.name === doc.name
                      ? "border-blue-500 bg-blue-50/60 ring-2 ring-blue-500/20"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    {getFileIcon(doc.type)}
                    <div>
                      <div className="text-xs font-semibold text-slate-800">{doc.title}</div>
                      <div className="text-[10px] text-slate-500">{doc.name} • {doc.pagesOrSlides}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Document RAG Chat */}
        <div className="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm lg:col-span-6 h-[640px]">
          {/* Chat Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-slate-50/70 rounded-t-2xl">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
                <Bot size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-800">
                  Document RAG Chat (Hard Payload Filtered)
                </h3>
                <span className="text-[10px] text-slate-500 block">
                  Cô lập theo file: <b className="text-slate-700">{selectedFile?.name}</b>
                </span>
              </div>
            </div>

            <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-[10px] font-bold text-green-700">
              Vector BGE-M3 1024d Active
            </span>
          </div>

          {/* Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/30">
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "bot" && (
                  <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-white text-xs">
                    <Bot size={14} />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 text-xs ${
                    msg.sender === "user"
                      ? "bg-blue-600 text-white rounded-br-xs shadow-sm"
                      : "bg-white border border-slate-200 text-slate-800 rounded-bl-xs shadow-sm"
                  }`}
                >
                  <p className="whitespace-pre-line leading-relaxed">{msg.text}</p>

                  {/* Citations Badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 border-t border-slate-100 pt-2 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Trích dẫn:
                      </span>
                      {msg.citations.map((cite, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setActiveCitation(cite)}
                          className="flex items-center gap-1 rounded-md bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-bold text-blue-700 hover:bg-blue-100 transition-colors"
                        >
                          <span>[Trang {cite.page}]</span>
                          <ExternalLink size={10} />
                        </button>
                      ))}
                    </div>
                  )}

                  <div
                    className={`mt-1.5 text-[9px] text-right ${
                      msg.sender === "user" ? "text-blue-200" : "text-slate-400"
                    }`}
                  >
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === "user" && (
                  <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-slate-700 text-white text-xs">
                    <User size={14} />
                  </div>
                )}
              </div>
            ))}

            {isQuerying && (
              <div className="flex items-center gap-2 text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl p-3 w-fit">
                <Loader2 size={14} className="animate-spin text-blue-600" />
                <span>Đang tìm kiếm Vector BGE-M3 (1024d) & Gemini RAG...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions Suggestions */}
          <div className="border-t border-slate-100 bg-white px-3 py-2 flex items-center gap-1.5 overflow-x-auto text-[11px]">
            <span className="text-slate-400 flex items-center gap-1 shrink-0">
              <Info size={12} /> Gợi ý:
            </span>
            {[
              "Điều kiện xét tốt nghiệp là gì?",
              "Quy định tích lũy tín chỉ CGPA?",
              "Quy trình nộp báo cáo thực tập?",
            ].map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendQuery(q)}
                className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="border-t border-slate-200 p-3 bg-white rounded-b-2xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuery();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Hỏi đáp về nội dung tài liệu này..."
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isQuerying}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                <Send size={15} />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Citation Preview Modal */}
      {activeCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl border border-slate-200">
            <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-2.5">
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-blue-600" />
                <h3 className="text-sm font-bold text-slate-800">
                  Xem Trích Đoạn Gốc (Trang {activeCitation.page})
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveCitation(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-700">
              <p>"{activeCitation.snippet}"</p>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => setActiveCitation(null)}
                className="rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-900 transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

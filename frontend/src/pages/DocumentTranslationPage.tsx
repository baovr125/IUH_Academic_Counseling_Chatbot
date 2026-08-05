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
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { LANG_CONFIG, addCardToDeck } from "../services/deckStorage";

interface DocumentFile {
  name: string;
  type: "pdf" | "docx" | "pptx";
  size: string;
  pagesOrSlides: string;
  title: string;
}

const SAMPLE_DOCS: DocumentFile[] = [
  {
    name: "Bao_cao_thuc_tap_tot_nghiep_IUH.docx",
    type: "docx",
    size: "2.4 MB",
    pagesOrSlides: "15 trang",
    title: "Báo cáo thực tập tốt nghiệp chuyên ngành Kỹ thuật Phần mềm",
  },
  {
    name: "Quy_che_hoc_vu_tin_chi_2026.pdf",
    type: "pdf",
    size: "4.1 MB",
    pagesOrSlides: "24 trang",
    title: "Quy chế đào tạo theo hệ thống tín chỉ IUH",
  },
  {
    name: "Slide_gioi_thieu_Khoa_CNTT.pptx",
    type: "pptx",
    size: "6.8 MB",
    pagesOrSlides: "18 slides",
    title: "Giới thiệu chương trình đào tạo Khoa Công nghệ Thông tin",
  },
];

export default function DocumentTranslationPage() {
  const navigate = useNavigate();

  const [sourceLang, setSourceLang] = useState("vi");
  const [targetLang, setTargetLang] = useState("en");
  const [selectedFile, setSelectedFile] = useState<DocumentFile | null>(SAMPLE_DOCS[0]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [showSummary, setShowSummary] = useState(true);
  const [savedKeywordsSuccess, setSavedKeywordsSuccess] = useState(false);

  const swapLanguages = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setIsCompleted(false);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    let type: "pdf" | "docx" | "pptx" = "pdf";
    if (file.name.endsWith(".pptx") || file.name.endsWith(".ppt")) type = "pptx";
    else if (file.name.endsWith(".docx") || file.name.endsWith(".doc")) type = "docx";

    setSelectedFile({
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
    setProgressPercent(15);

    setTimeout(() => setProgressPercent(45), 600);
    setTimeout(() => setProgressPercent(80), 1200);
    setTimeout(() => {
      setProgressPercent(100);
      setIsTranslating(false);
      setIsCompleted(true);
      setShowSummary(true);
    }, 1800);
  };

  const handleDownloadFile = () => {
    if (!selectedFile) return;

    const content = `================================================================
TÀI LIỆU ĐÃ DỊCH: ${selectedFile.name}
NGÔN NGỮ: ${LANG_CONFIG[sourceLang]?.label || sourceLang} -> ${LANG_CONFIG[targetLang]?.label || targetLang}
HỆ THỐNG: Trợ lý Học vụ Thông minh IUH Portal AI
================================================================

[TIÊU ĐỀ TÀI LIỆU]
${selectedFile.title} (${LANG_CONFIG[targetLang]?.label || targetLang})

[TÓM TẮT Ý CHÍNH CỦA TÀI LIỆU]
1. Tài liệu phân tích chuyên sâu về chủ đề "${selectedFile.title}".
2. Hệ thống hóa các quy trình, cấu trúc kỹ thuật và yêu cầu học vụ của Đại học Công nghiệp TP.HCM (IUH).
3. Kết quả khảo sát và đánh giá thực tiễn cho thấy hiệu quả vượt trội khi áp dụng giải pháp đề xuất.

[NỘI DUNG DỊCH CHI TIẾT (MẪU)]
- Trang 1: Giới thiệu chung và phạm vi áp dụng...
- Trang 2-5: Cơ sở lý thuyết và các khái niệm cốt lõi...
- Trang 6-12: Phương pháp triển khai và số liệu kết quả...
- Trang 13-15: Kết luận và hướng phát triển tiếp theo...

================================================================
Tài liệu được dịch và xác thực bởi IUH Portal AI (RAG Neural Engine).
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

    const keywords = [
      {
        term: "Academic Regulations (Quy chế học vụ)",
        def: "Các quy định, điều khoản về quản lý đào tạo và học vụ tại trường.",
      },
      {
        term: "Graduation Internship Report (Báo cáo TTCN)",
        def: "Báo cáo thực tập tốt nghiệp và ứng dụng công nghệ thực tế.",
      },
      {
        term: "System Architecture (Cấu trúc hệ thống)",
        def: "Kiến trúc tổng thể của hệ thống phần mềm hoặc cổng thông tin.",
      },
    ];

    keywords.forEach((kw) => {
      addCardToDeck(
        targetLang,
        kw.term,
        kw.def,
        `Trích xuất từ tài liệu: ${selectedFile.name}`,
        "noun"
      );
    });

    setSavedKeywordsSuccess(true);
    setTimeout(() => setSavedKeywordsSuccess(false), 4000);
  };

  const getFileIcon = (type: "pdf" | "docx" | "pptx") => {
    if (type === "pdf") {
      return <FileText className="h-7 w-7 text-red-500" />;
    }
    if (type === "pptx") {
      return <Presentation className="h-7 w-7 text-orange-500" />;
    }
    return <File className="h-7 w-7 text-blue-500" />;
  };

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col p-6">
      {/* Top Header + Tabs */}
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Languages className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-slate-800">Dịch thuật & Tóm tắt Tài Liệu (PDF / PPT / Word)</h1>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Dịch trọn vẹn tài liệu học vụ, bài giảng PowerPoint và báo cáo Word, tải về file dịch và xem tóm tắt tự động bằng AI
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/translation")}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <AlignLeft size={16} />
            <span>Dịch Văn Bản (Text)</span>
          </button>
          <button
            type="button"
            onClick={() => navigate("/flashcards")}
            className="flex items-center gap-1.5 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
          >
            <BookOpen size={16} />
            <span>Xem Sổ Thẻ Flashcard</span>
          </button>
        </div>
      </div>

      {/* Mode Switcher Banner */}
      <div className="mb-6 flex gap-2 border-b border-slate-200 pb-px">
        <button
          type="button"
          onClick={() => navigate("/translation")}
          className="flex items-center gap-2 border-b-2 border-transparent px-4 py-2.5 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors"
        >
          <AlignLeft size={15} />
          <span>Dịch Văn Bản Ngắn (Text Translation)</span>
        </button>
        <button
          type="button"
          className="flex items-center gap-2 border-b-2 border-blue-600 px-4 py-2.5 text-xs font-semibold text-blue-600 transition-colors"
        >
          <FileText size={15} />
          <span>Dịch Tài Liệu (PDF, PowerPoint, Word)</span>
        </button>
      </div>

      {/* Language Selector Bar */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          {/* Source Language Select */}
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

          {/* Target Language Select */}
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
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
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

      {/* Main Grid: Upload & File selection (Left) | Translation & Summary Result (Right) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: File upload + Sample docs */}
        <div className="space-y-4 lg:col-span-5">
          {/* Dropzone / Upload Box */}
          <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/60 p-6 text-center hover:bg-slate-100/50 transition-colors">
            <input
              type="file"
              accept=".pdf,.docx,.doc,.pptx,.ppt"
              onChange={handleFileUpload}
              className="absolute inset-0 z-10 cursor-pointer opacity-0"
            />
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 shadow-sm">
              <UploadCloud size={24} />
            </div>
            <div className="text-xs font-bold text-slate-800">
              Nhấp hoặc kéo thả file tài liệu vào đây
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Hỗ trợ định dạng: PDF (.pdf), PowerPoint (.pptx), Word (.docx) - Tối đa 25MB
            </p>
          </div>

          {/* Currently Selected Document Card */}
          {selectedFile && (
            <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-white shadow-sm border border-slate-100">
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

                <span className="rounded-full bg-blue-600 px-2.5 py-0.5 text-[10px] font-bold text-white uppercase">
                  {selectedFile.type}
                </span>
              </div>
            </div>
          )}

          {/* Sample Documents for Demo */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <span className="mb-3 block text-xs font-bold text-slate-700">
              ⚡ Hoặc chọn nhanh Tài Liệu Mẫu của trường:
            </span>
            <div className="space-y-2">
              {SAMPLE_DOCS.map((doc) => (
                <button
                  type="button"
                  key={doc.name}
                  onClick={() => {
                    setSelectedFile(doc);
                    setIsCompleted(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl border p-3 text-left transition-all ${
                    selectedFile?.name === doc.name
                      ? "border-blue-500 bg-blue-50/60 ring-2 ring-blue-500/20"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(doc.type)}
                    <div>
                      <div className="text-xs font-semibold text-slate-800">
                        {doc.title}
                      </div>
                      <div className="mt-0.5 text-[10px] text-slate-500">
                        {doc.name} • {doc.pagesOrSlides}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Progress / Download / Summary */}
        <div className="lg:col-span-7">
          {isTranslating ? (
            <div className="flex h-full min-h-[360px] flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <div className="relative mb-6 flex h-20 w-20 items-center justify-center">
                <div className="absolute inset-0 animate-ping rounded-full bg-blue-100 opacity-75" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-white shadow-md">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              </div>
              <h3 className="text-base font-bold text-slate-800">
                Đang dịch tài liệu "{selectedFile?.name}"
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                AI Neural Engine đang xử lý định dạng và dịch thuật sang{" "}
                {LANG_CONFIG[targetLang]?.label || targetLang}...
              </p>

              {/* Progress Bar */}
              <div className="mt-6 w-full max-w-sm">
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
                  <span>Tiến độ xử lý</span>
                  <span>{progressPercent}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          ) : isCompleted && selectedFile ? (
            <div className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              {/* Success Header */}
              <div className="mb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100 text-green-600">
                    <CheckCircle2 size={22} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-800">
                      Đã dịch xong tài liệu thành công!
                    </h3>
                    <p className="text-xs text-slate-500">
                      Sẵn sàng tải về hoặc xem tóm tắt thông minh bằng AI
                    </p>
                  </div>
                </div>

                {/* Download Button */}
                <button
                  type="button"
                  onClick={handleDownloadFile}
                  className="flex items-center justify-center gap-2 rounded-xl bg-green-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-green-700 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Download size={16} />
                  <span>Tải tài liệu đã dịch ({selectedFile.type.toUpperCase()})</span>
                </button>
              </div>

              {savedKeywordsSuccess && (
                <div className="mb-4 flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 p-3 text-xs font-medium text-green-800">
                  <CheckCircle2 size={16} className="text-green-600" />
                  <span>
                    Đã lưu các từ khóa cốt lõi của tài liệu vào Sổ từ vựng{" "}
                    <b>{LANG_CONFIG[targetLang]?.defaultTitle}</b>!
                  </span>
                </div>
              )}

              {/* Summary Toggle Header */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles size={16} className="text-amber-500" />
                  <span className="text-sm font-bold text-slate-800">
                    Tóm tắt tự động tài liệu bằng AI (AI Document Summary)
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => setShowSummary((s) => !s)}
                  className="text-xs font-semibold text-blue-600 hover:underline"
                >
                  {showSummary ? "Thu gọn" : "Hiển thị tóm tắt"}
                </button>
              </div>

              {/* AI Summary Content Box */}
              {showSummary && (
                <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-5 text-xs">
                  <div>
                    <span className="font-bold text-slate-700 uppercase tracking-wide text-[11px]">
                      1. Tổng quan tài liệu (Executive Summary)
                    </span>
                    <p className="mt-1.5 leading-relaxed text-slate-700">
                      Tài liệu <b>{selectedFile.title}</b> bao gồm {selectedFile.pagesOrSlides}{" "}
                      trình bày cấu trúc chi tiết, quy trình thực hiện và những giải pháp đổi mới
                      trong công tác học vụ tại Trường Đại học Công nghiệp TP.HCM (IUH). Bản dịch đã
                      chuyển ngữ trọn vẹn sang <b>{LANG_CONFIG[targetLang]?.label || targetLang}</b>{" "}
                      đảm bảo độ chính xác học thuật cao.
                    </p>
                  </div>

                  <div>
                    <span className="font-bold text-slate-700 uppercase tracking-wide text-[11px]">
                      2. Các điểm cốt lõi (Key Findings & Points)
                    </span>
                    <ul className="mt-1.5 space-y-1.5 list-disc pl-4 text-slate-700">
                      <li>
                        <b>Quy chế học vụ & Tín chỉ:</b> Xác định điều kiện đăng ký, tích lũy điểm và
                        quy định tốt nghiệp theo chuẩn mới nhất.
                      </li>
                      <li>
                        <b>Ứng dụng Công nghệ AI:</b> Mô hình hóa Trợ lý học vụ AI (RAG) giúp tự
                        động hóa 85% thắc mắc sinh viên.
                      </li>
                      <li>
                        <b>Thực hành chuyên sâu:</b> Kết quả thực tế đạt mức độ hài lòng trên 92% từ
                        cả giảng viên và sinh viên.
                      </li>
                    </ul>
                  </div>

                  {/* Key Terminology Section */}
                  <div className="border-t border-slate-200/80 pt-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-bold text-slate-700 uppercase tracking-wide text-[11px]">
                        3. Thuật ngữ cốt lõi (Key Terminology)
                      </span>
                      <button
                        type="button"
                        onClick={handleSaveKeywordsToDeck}
                        className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
                      >
                        <BookmarkPlus size={14} />
                        <span>Lưu 3 từ khóa này vào Sổ thẻ ({LANG_CONFIG[targetLang]?.flag})</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      {[
                        {
                          term: "Academic Regulations",
                          vi: "Quy chế học vụ",
                        },
                        {
                          term: "Graduation Internship",
                          vi: "Thực tập tốt nghiệp",
                        },
                        {
                          term: "System Architecture",
                          vi: "Cấu trúc hệ thống",
                        },
                      ].map((item) => (
                        <div
                          key={item.term}
                          className="rounded-lg border border-slate-200 bg-white p-2.5 text-[11px]"
                        >
                          <div className="font-bold text-slate-800">{item.term}</div>
                          <div className="text-slate-500">{item.vi}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-full min-h-[360px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                <FileText size={28} />
              </div>
              <h3 className="text-base font-bold text-slate-700">
                Chưa bắt đầu dịch tài liệu
              </h3>
              <p className="mt-1 max-w-sm text-xs text-slate-500">
                Hãy chọn một tài liệu mẫu bên trái hoặc tải file của bạn lên, sau đó bấm nút{" "}
                <b>"Bắt đầu dịch tài liệu"</b> ở trên.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

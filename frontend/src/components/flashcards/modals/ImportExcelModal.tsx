import React, { useState, useRef } from "react";
import {
  X,
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FileText
} from "lucide-react";
import { getExcelTemplateDownloadUrl, type BulkImportResult } from "../../../services/flashcardService";
import type { BackendDeck } from "../../../services/flashcardService";

interface ImportExcelModalProps {
  isOpen: boolean;
  deck: BackendDeck;
  onClose: () => void;
  onImport: (file: File) => Promise<BulkImportResult>;
  isLoading?: boolean;
}

export const ImportExcelModal: React.FC<ImportExcelModalProps> = ({
  isOpen,
  deck,
  onClose,
  onImport,
  isLoading = false
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<BulkImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (file: File | null) => {
    setErrorMsg(null);
    setImportResult(null);
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const fname = file.name.toLowerCase();
    if (!fname.endsWith(".xlsx") && !fname.endsWith(".xls") && !fname.endsWith(".csv")) {
      setErrorMsg("Chỉ hỗ trợ file định dạng Excel (.xlsx, .xls) hoặc CSV (.csv).");
      setSelectedFile(null);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg("Dung lượng file không được vượt quá 5MB.");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setErrorMsg(null);
    try {
      const res = await onImport(selectedFile);
      setImportResult(res);
    } catch (err: any) {
      setErrorMsg(err?.message || "Có lỗi xảy ra trong quá trình nhập file.");
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setErrorMsg(null);
    setImportResult(null);
    onClose();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-3xl bg-white p-6 sm:p-7 shadow-2xl animate-in zoom-in-95 duration-200 flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <FileSpreadsheet size={22} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Nhập từ vựng từ Excel / CSV</h3>
              <p className="text-[11px] text-slate-400">
                Thêm hàng loạt từ mới vào sổ <strong className="text-slate-600">"{deck.title}"</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Template Download Banner */}
        <div className="flex items-center justify-between rounded-2xl bg-blue-50/70 p-3.5 border border-blue-100 text-xs">
          <div className="flex items-center gap-2.5 text-blue-900">
            <FileText size={18} className="text-blue-600 flex-shrink-0" />
            <span>Chưa có mẫu file chuẩn? Tải file mẫu mẫu để điền từ:</span>
          </div>
          <a
            href={getExcelTemplateDownloadUrl()}
            download="flashcard_template.xlsx"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-blue-700 transition-all flex-shrink-0"
          >
            <Download size={13} />
            <span>Tải file mẫu (.xlsx)</span>
          </a>
        </div>

        {/* Dropzone */}
        {!importResult ? (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center rounded-3xl border-2 border-dashed p-7 text-center transition-all cursor-pointer ${
                isDragOver
                  ? "border-emerald-500 bg-emerald-50/40"
                  : selectedFile
                  ? "border-blue-400 bg-blue-50/20"
                  : "border-slate-200 bg-slate-50/60 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                className="hidden"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
              />

              {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                    <FileSpreadsheet size={26} />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-slate-800 break-all">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <span className="text-[11px] font-semibold text-blue-600 mt-1 hover:underline">
                    Bấm để chọn file khác
                  </span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                    <UploadCloud size={26} />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-700">
                      Kéo thả file Excel / CSV vào đây, hoặc <span className="text-blue-600">chọn từ máy tính</span>
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Hỗ trợ định dạng .xlsx, .xls, .csv (Tối đa 2,000 từ / 5MB)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="flex items-center gap-2 rounded-2xl bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200 animate-in fade-in duration-150">
                <AlertCircle size={16} className="flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Format Instructions */}
            <div className="rounded-2xl bg-slate-50 p-3.5 text-[11px] text-slate-500 border border-slate-100">
              <p className="font-semibold text-slate-700 mb-1">💡 Hỗ trợ Đa Ngôn Ngữ & Tiêu đề linh hoạt:</p>
              <ul className="list-disc pl-4 space-y-1">
                <li>
                  <strong>Cột 1 (Bắt buộc) - Từ vựng</strong>: Từ gốc bằng bất kỳ ngôn ngữ nào (Anh, Đức, Pháp, Nhật, Trung, Hàn, Nga, v.v.). <em>Tiêu đề cột: Term, Từ vựng, Word, Wort, Mot, 单次, 単語...</em>
                </li>
                <li>
                  <strong>Cột 2 (Bắt buộc) - Định nghĩa</strong>: Nghĩa tiếng Việt hoặc giải nghĩa. <em>Tiêu đề cột: Definition, Nghĩa, Meaning, Bedeutung, Sens, 意思, 意味...</em>
                </li>
                <li>
                  <strong>Cột 3 (Tùy chọn) - Phiên âm</strong>: Ký hiệu IPA, Pinyin (tiếng Trung), Furigana/Romaji (tiếng Nhật), Romaja (tiếng Hàn).
                </li>
                <li>
                  <strong>Cột 4 (Tùy chọn) - Từ loại</strong>: noun/danh từ, verb/động từ, adj/tính từ, phrase/cụm từ (hoặc Nomen, Verb, Adjektiv...).
                </li>
                <li>
                  <strong>Cột 5 (Tùy chọn) - Ví dụ</strong>: Câu ví dụ ngữ cảnh tương ứng với từ vựng.
                </li>
              </ul>
              <p className="mt-2 text-[10.5px] text-slate-400 italic">
                * Mẹo: Tiêu đề cột có thể viết bằng tiếng Việt hoặc tiếng Anh. Nếu file không có dòng tiêu đề, hệ thống sẽ tự động gán dữ liệu theo thứ tự 5 cột trên.
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleClose}
                className="rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={!selectedFile || isLoading}
                className="flex items-center gap-2 rounded-2xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50 transition-all"
              >
                {isLoading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Đang xử lý & nhập từ...</span>
                  </>
                ) : (
                  <>
                    <FileSpreadsheet size={15} />
                    <span>Xác nhận Import</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          /* Result Summary */
          <div className="flex flex-col gap-4 py-2 animate-in zoom-in-95 duration-200">
            <div className="rounded-2xl bg-emerald-50 p-5 text-center border border-emerald-200 flex flex-col items-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-2">
                <CheckCircle2 size={28} />
              </div>
              <h4 className="text-base font-bold text-emerald-900">Nhập dữ liệu thành công!</h4>
              <p className="text-xs text-emerald-700 mt-1">
                Toàn bộ từ vựng đã được nạp vào sổ thẻ và tự động khởi tạo thuật toán FSRS.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="rounded-2xl bg-slate-50 p-3.5 border border-slate-200">
                <span className="text-[11px] text-slate-500 font-medium">Thêm mới thành công</span>
                <p className="text-xl font-extrabold text-emerald-600 mt-0.5">
                  +{importResult.inserted} <span className="text-xs font-medium">thẻ</span>
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-3.5 border border-slate-200">
                <span className="text-[11px] text-slate-500 font-medium">Bỏ qua (Trùng lặp)</span>
                <p className="text-xl font-extrabold text-slate-600 mt-0.5">
                  {importResult.skipped_duplicates} <span className="text-xs font-medium">thẻ</span>
                </p>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic text-center">
              🔊 Hệ thống âm thanh Edge Neural TTS đang sinh trước giọng phát âm chuẩn cho các từ mới ở chế độ nền.
            </p>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleClose}
                className="w-full rounded-2xl bg-blue-600 py-3 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition-colors text-center"
              >
                Hoàn tất & Bắt đầu học ngay
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

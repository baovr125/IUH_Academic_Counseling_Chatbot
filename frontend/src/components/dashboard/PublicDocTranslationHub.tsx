import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  UploadCloud,
  ArrowRight,
  Sparkles,
  Search,
  School,
  DollarSign,
  Award,
  Globe2,
  BookOpen,
} from "lucide-react";
import type { DashboardStats } from "../../types";

interface PublicDocTranslationHubProps {
  stats: DashboardStats;
}

const ADMISSION_PROMPT_CHIPS = [
  {
    label: "Phương thức Tuyển sinh 2026",
    query: "Các phương thức xét tuyển đại học chính quy của IUH năm học 2026 là gì?",
    icon: School,
    color: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  },
  {
    label: "Điểm chuẩn CNTT & Kỹ thuật",
    query: "Điểm chuẩn trúng tuyển ngành Công nghệ Thông tin và Kỹ thuật Phần mềm IUH các năm gần đây?",
    icon: Award,
    color: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
  {
    label: "Mức Học phí & Học bổng",
    query: "Mức học phí theo tín chỉ và chính sách học bổng dành cho tân sinh viên IUH như thế nào?",
    icon: DollarSign,
    color: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  },
  {
    label: "Liên kết Quốc tế 2+2",
    query: "Thông tin về các chương trình đào tạo liên kết quốc tế và chuyển tiếp đại học tại IUH?",
    icon: Globe2,
    color: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
  },
];

export const PublicDocTranslationHub: React.FC<PublicDocTranslationHubProps> = ({ stats }) => {
  const navigate = useNavigate();
  const [queryInput, setQueryInput] = useState("");

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    navigate("/chat", { state: { initialPrompt: queryInput.trim() } });
  };

  const handleChipClick = (query: string) => {
    navigate("/chat", { state: { initialPrompt: query } });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {/* 1. Document Translation & PDF RAG Card */}
      <div className="flex flex-col justify-between rounded-3xl border border-blue-200/80 bg-gradient-to-br from-blue-50/60 via-white to-indigo-50/40 p-6 shadow-sm dark:border-blue-900/60 dark:bg-gradient-to-br dark:from-slate-800 dark:via-slate-800 dark:to-blue-950/30 transition-all hover:shadow-md">
        <div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-600/30">
                <FileText size={20} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  Dịch thuật PDF & Document RAG
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">Nghiên cứu tài liệu học thuật AI</p>
              </div>
            </div>
            <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              Chuyên ngành
            </span>
          </div>

          <div
            onClick={() => navigate("/translation-doc")}
            className="mt-4 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-blue-300 bg-white/80 p-5 text-center transition-all hover:border-blue-500 hover:bg-blue-50/50 dark:border-blue-800 dark:bg-slate-900/50 dark:hover:bg-slate-900/80 cursor-pointer group"
          >
            <UploadCloud size={32} className="text-blue-500 transition-transform group-hover:-translate-y-1" />
            <p className="mt-2 text-xs font-bold text-slate-700 dark:text-slate-200">
              Nhấn để tải lên file PDF / DOCX
            </p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              AI tự động dịch toàn văn, trích xuất thuật ngữ & hỏi đáp theo file
            </p>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-blue-100 dark:border-slate-700/60">
          <button
            type="button"
            onClick={() => navigate("/translation-doc")}
            className="group flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-600/25 hover:bg-blue-700 transition-all cursor-pointer hover:scale-[1.01]"
          >
            <span>Mở Trình Dịch Tài Liệu Nghiên Cứu</span>
            <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </div>

      {/* 2. AI Admission & General Exploration Card */}
      <div className="flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                Tư vấn Tuyển sinh & Khám phá IUH
              </h3>
              <p className="text-xs text-slate-400">Giải đáp mọi thông tin về trường</p>
            </div>
          </div>

          {/* Quick Search Form */}
          <form onSubmit={handleQuickSearch} className="relative mt-4">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Hỏi về điểm chuẩn, ngành học, học phí..."
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 py-2.5 pl-3.5 pr-10 text-xs text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:placeholder-slate-500 transition-all"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
              title="Tìm kiếm"
            >
              <Search size={13} />
            </button>
          </form>

          {/* Smart Admission Chips */}
          <div className="mt-3.5 space-y-1.5">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Câu hỏi phổ biến:</p>
            <div className="flex flex-wrap gap-1.5">
              {ADMISSION_PROMPT_CHIPS.map((chip, idx) => {
                const Icon = chip.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleChipClick(chip.query)}
                    className={`flex items-center gap-1 rounded-xl border px-2.5 py-1 text-[11px] font-medium transition-all hover:scale-105 cursor-pointer ${chip.color}`}
                  >
                    <Icon size={12} />
                    <span>{chip.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between text-xs">
          <span className="text-slate-400">RAG Chatbot AI thông minh</span>
          <button
            type="button"
            onClick={() => navigate("/chat")}
            className="flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <span>Trò chuyện ngay</span>
            <ArrowRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

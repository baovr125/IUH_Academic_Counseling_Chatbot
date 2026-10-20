import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  ArrowRight,
  Search,
  MessageSquare,
  HelpCircle,
  Award,
  CalendarCheck,
  FileCheck2,
} from "lucide-react";
import { FlashcardDueCard } from "./FlashcardDueCard";

const SMART_PROMPT_CHIPS = [
  {
    label: "Đăng ký học phần bổ sung",
    query: "Quy trình và thời hạn đăng ký học phần bổ sung học kỳ này như thế nào?",
    icon: CalendarCheck,
    color: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
  },
  {
    label: "Điều kiện Học bổng KKHT",
    query: "Điều kiện điểm GPA và điểm rèn luyện để được xét học bổng khuyến khích học tập IUH?",
    icon: Award,
    color: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  },
  {
    label: "Thủ tục Phúc khảo / Hoãn thi",
    query: "Hướng dẫn thủ tục và thời hạn nộp đơn xin phúc khảo bài thi kết thúc học phần?",
    icon: FileCheck2,
    color: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
  {
    label: "Chuẩn đầu ra Ngoại ngữ",
    query: "Quy định về chứng chỉ chuẩn đầu ra ngoại ngữ TOEIC và VSTEP đối với sinh viên IUH?",
    icon: HelpCircle,
    color: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
  },
];

export const StudentDailyActionHub: React.FC = () => {
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
      {/* 1. Flashcard Due Today Card (số liệu thật từ service Flashcard) */}
      <FlashcardDueCard />

      {/* 2. AI Quick Counseling Query Card */}
      <div className="flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                Hỏi đáp Quy chế Học vụ IUH
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">RAG AI trích dẫn sổ tay chính xác</p>
            </div>
          </div>

          {/* Quick Search Form */}
          <form onSubmit={handleQuickSearch} className="relative mt-4">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Tra cứu quy chế, học bổng, đăng ký môn..."
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 py-2.5 pl-3.5 pr-10 text-xs text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:placeholder-slate-500 transition-all"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
              title="Tìm kiếm với Chatbot AI"
            >
              <Search size={13} />
            </button>
          </form>

          {/* Smart Prompt Chips */}
          <div className="mt-3.5 space-y-1.5">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider dark:text-slate-400">Chủ đề thường gặp:</p>
            <div className="flex flex-wrap gap-1.5">
              {SMART_PROMPT_CHIPS.map((chip, idx) => {
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
          <span className="text-slate-500 dark:text-slate-400">Trợ lý AI sẵn sàng 24/7</span>
          <button
            type="button"
            onClick={() => navigate("/chat")}
            className="flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <span>Mở Khung Chat Đầy Đủ</span>
            <ArrowRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

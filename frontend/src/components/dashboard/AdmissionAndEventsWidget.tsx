import React from "react";
import { useNavigate } from "react-router-dom";
import { School, ArrowRight, ExternalLink, Sparkles, Award } from "lucide-react";
import type { DashboardStats, AdmissionNews } from "../../types";

interface AdmissionAndEventsWidgetProps {
  stats: DashboardStats;
}

export const AdmissionAndEventsWidget: React.FC<AdmissionAndEventsWidgetProps> = ({ stats }) => {
  const navigate = useNavigate();
  const newsList: AdmissionNews[] = stats.admissionNews || [];

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700/60">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
            <School size={16} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100">
              Tuyển Sinh & Điểm Chuẩn IUH
            </h3>
            <p className="text-[10px] text-slate-400">Thông tin chính thức từ Hội đồng Tuyển sinh</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => navigate("/chat", { state: { initialPrompt: "Tư vấn đề án tuyển sinh và học phí IUH" } })}
          className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400"
        >
          <span>Hỏi AI</span>
          <Sparkles size={11} />
        </button>
      </div>

      {/* News Items */}
      <div className="mt-4 space-y-3">
        {newsList.map((item) => (
          <div
            key={item.id}
            onClick={() => navigate("/chat", { state: { initialPrompt: `Cho tôi biết thêm về: ${item.title}` } })}
            className="group rounded-2xl border border-slate-100 bg-slate-50/60 p-3.5 dark:border-slate-700/50 dark:bg-slate-900/40 hover:border-blue-200 hover:bg-blue-50/30 dark:hover:border-blue-800 dark:hover:bg-slate-900/70 transition-all cursor-pointer"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                {item.badge}
              </span>
              <span className="text-[10px] font-semibold text-slate-400">{item.date}</span>
            </div>
            <h4 className="mt-1.5 text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 leading-snug">
              {item.title}
            </h4>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
              {item.description}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60 text-center">
        <a
          href="https://tuyensinh.iuh.edu.vn"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:underline"
        >
          <span>Xem Cổng Tuyển sinh IUH Chính thức</span>
          <ExternalLink size={12} />
        </a>
      </div>
    </div>
  );
};

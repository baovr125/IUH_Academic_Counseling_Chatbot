import { Award, BookOpen, Bot, FileCheck2, GraduationCap, Sparkles, ArrowRight } from "lucide-react";
import logoMark from "../../assets/brand/iuh-mark-256.png";
import { useSettings } from "../../context/SettingsContext";

interface ChatWelcomeScreenProps {
  onSelectPrompt: (prompt: string) => void;
}

const SUGGESTIONS = [
  {
    icon: Award,
    categoryVi: "Học bổng & Khen thưởng",
    categoryEn: "Scholarships & Awards",
    descVi: "Điều kiện và tiêu chuẩn xét học bổng khuyến khích học tập tại trường?",
    descEn: "What are the requirements for academic incentive scholarships?",
    prompt: "Điều kiện để nhận học bổng khuyến khích học tập tại IUH là gì?",
  },
  {
    icon: GraduationCap,
    categoryVi: "Cảnh báo học vụ & Điểm số",
    categoryEn: "Academic Warning & GPA",
    descVi: "Quy định về các mức cảnh báo học vụ và điều kiện buộc thôi học?",
    descEn: "Regulations on academic warning levels and forced dropouts?",
    prompt: "Quy định về các mức cảnh báo học vụ và buộc thôi học mới nhất của IUH như thế nào?",
  },
  {
    icon: FileCheck2,
    categoryVi: "Biểu mẫu & Thủ tục",
    categoryEn: "Forms & Procedures",
    descVi: "Hướng dẫn thủ tục xin cấp giấy chứng nhận sinh viên hoặc hoãn thi?",
    descEn: "How to request student certificates or apply for exam postponement?",
    prompt: "Hướng dẫn thủ tục xin cấp giấy chứng nhận sinh viên và đơn xin hoãn thi tại IUH?",
  },
  {
    icon: BookOpen,
    categoryVi: "Đăng ký học phần",
    categoryEn: "Course Registration",
    descVi: "Quy trình đăng ký học phần bổ sung và xử lý khi bị trùng lịch học?",
    descEn: "Course registration procedure and handling schedule conflicts?",
    prompt: "Quy trình đăng ký học phần bổ sung và cách xử lý khi môn học bị trùng lịch tại IUH?",
  },
];

export function ChatWelcomeScreen({ onSelectPrompt }: ChatWelcomeScreenProps) {
  const { language } = useSettings();
  const isVi = language === "vi";

  return (
    <div className="relative flex flex-col items-center justify-center min-h-full px-4 py-8 max-w-4xl mx-auto select-none overflow-hidden">
      {/* Background Animated Ambient Glows */}
      <div className="pointer-events-none absolute -top-16 left-1/2 -translate-x-1/2 w-80 h-80 rounded-full bg-blue-500/15 dark:bg-blue-600/10 blur-3xl animate-pulse-glow" />
      <div className="pointer-events-none absolute top-32 left-1/4 w-72 h-72 rounded-full bg-indigo-500/10 dark:bg-indigo-600/10 blur-3xl animate-pulse-glow" />
      <div className="pointer-events-none absolute top-28 right-1/4 w-72 h-72 rounded-full bg-amber-500/10 dark:bg-amber-600/10 blur-3xl animate-pulse-glow" />

      {/* Central Catchy Animation: Layered floating badge with IUH Logo */}
      <div className="relative mb-6 animate-float-slow">
        {/* Glow halo */}
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-amber-500 blur-md opacity-40 animate-pulse" />
        
        {/* Main Logo Card */}
        <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-white p-3 shadow-xl ring-1 ring-slate-100 dark:bg-slate-800 dark:ring-slate-700">
          <img
            src={logoMark}
            alt="IUH Logo"
            className="h-full w-full object-contain filter drop-shadow-sm transition-transform hover:scale-105"
          />

          {/* Orbiting Bot badge */}
          <div className="absolute -bottom-2 -right-2 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg ring-3 ring-white dark:ring-slate-800">
            <Bot size={16} />
          </div>

          {/* Orbiting Sparkles badge */}
          <div className="absolute -top-2 -left-2 flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-amber-400 to-orange-400 text-white shadow-md ring-3 ring-white dark:ring-slate-800">
            <Sparkles size={14} />
          </div>
        </div>
      </div>

      {/* Modern Status Badge */}
      <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-orange-200/80 bg-orange-50/80 px-3.5 py-1 text-xs font-semibold text-orange-800 backdrop-blur-sm dark:border-orange-900/50 dark:bg-orange-950/40 dark:text-orange-300">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
        </span>
        <span>{isVi ? "IUH Portal AI • Trợ lý Học vụ Trực tuyến" : "IUH Portal AI • Online Academic Assistant"}</span>
      </div>

      {/* Main Title & Subtitle */}
      <h1 className="text-center text-2xl sm:text-3xl font-extrabold text-slate-800 dark:text-slate-100 tracking-tight">
        {isVi ? (
          <>
            Chào bạn! Tôi có thể giúp gì cho{" "}
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-orange-500 bg-clip-text text-transparent">
              kỳ học của bạn?
            </span>
          </>
        ) : (
          <>
            Hello! How can I assist with your{" "}
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-orange-500 bg-clip-text text-transparent">
              academic journey?
            </span>
          </>
        )}
      </h1>

      <p className="mt-2 text-center text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-lg leading-relaxed">
        {isVi
          ? "Hỏi đáp mọi thông tin về quy chế đào tạo, tín chỉ, học bổng, biểu mẫu đơn từ và thủ tục tại Đại học Công nghiệp TP.HCM."
          : "Ask anything about academic regulations, credits, scholarships, student forms, and procedures at IUH."}
      </p>

      {/* Key Feature Highlights */}
      <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-[11.5px] text-slate-600 dark:text-slate-300">
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/70 px-2.5 py-1 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/70">
          <GraduationCap size={14} className="text-blue-500" />
          <span>{isVi ? "Quy chế đào tạo tín chỉ" : "Credit Regulations"}</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/70 px-2.5 py-1 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/70">
          <FileCheck2 size={14} className="text-emerald-500" />
          <span>{isVi ? "Sổ tay & Biểu mẫu sinh viên" : "Forms & Handbook"}</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/70 px-2.5 py-1 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/70">
          <Award size={14} className="text-amber-500" />
          <span>{isVi ? "Học bổng & Điểm rèn luyện" : "Scholarships & Scores"}</span>
        </div>
      </div>

      {/* Suggested Questions Grid (Requirement 1: Chỉ hiển thị khi là đoạn hội thoại mới) */}
      <div className="mt-8 w-full">
        <div className="mb-3 flex items-center justify-between px-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {isVi ? "Gợi ý câu hỏi phổ biến" : "Suggested questions"}
          </span>
          <span className="text-[11px] text-orange-600 font-semibold dark:text-orange-400">
            {isVi ? "Nhấp vào câu hỏi để gửi ngay" : "Click to ask directly"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {SUGGESTIONS.map((item, idx) => {
            const IconComponent = item.icon;
            return (
              <button
                key={idx}
                onClick={() => onSelectPrompt(item.prompt)}
                className="group flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-3.5 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-400 hover:shadow-md hover:shadow-orange-500/10 active:scale-[0.99] dark:border-slate-700 dark:bg-slate-800/90 dark:hover:border-orange-500/60 cursor-pointer"
              >
                <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-orange-100 text-orange-700 group-hover:bg-gradient-to-tr group-hover:from-orange-500 group-hover:to-amber-500 group-hover:text-white group-hover:shadow-sm group-hover:shadow-orange-500/30 transition-all dark:bg-orange-950/60 dark:text-orange-300">
                  <IconComponent size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
                      {isVi ? item.categoryVi : item.categoryEn}
                    </span>
                    <ArrowRight size={14} className="text-orange-400 group-hover:text-orange-600 group-hover:translate-x-1 transition-all flex-shrink-0" />
                  </div>
                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    {isVi ? item.descVi : item.descEn}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

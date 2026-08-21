import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  MessageSquare,
  BookOpen,
  ArrowRight,
  Clock,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  FileCheck,
} from "lucide-react";
import type { DashboardStats, RecentDocument, RecentChatPreview } from "../../types";

interface RecentWorkspaceTabsProps {
  stats: DashboardStats;
  isStudent: boolean;
}

export const RecentWorkspaceTabs: React.FC<RecentWorkspaceTabsProps> = ({
  stats,
  isStudent,
}) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"docs" | "chats">("docs");

  const recentDocs = stats.recentDocuments || [];
  const recentChats = stats.recentChatSessions || [];

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-all hover:shadow-md">
      {/* Header with Switcher Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-700/60">
        <div className="flex items-center gap-2">
          <div className="flex rounded-2xl bg-slate-100 p-1 dark:bg-slate-900">
            <button
              type="button"
              onClick={() => setActiveTab("docs")}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "docs"
                  ? "bg-white text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                  : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <FileText size={14} />
              <span>Tài liệu Dịch gần đây ({recentDocs.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("chats")}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "chats"
                  ? "bg-white text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                  : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <MessageSquare size={14} />
              <span>Phiên Tư vấn Chat ({recentChats.length})</span>
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={() => navigate(activeTab === "docs" ? "/translation-doc" : "/chat")}
          className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <span>{activeTab === "docs" ? "Xem tất cả tài liệu" : "Lịch sử cuộc trò chuyện"}</span>
          <ArrowRight size={13} />
        </button>
      </div>

      {/* Tab 1: Documents Content */}
      {activeTab === "docs" && (
        <div className="mt-4 space-y-2.5">
          {recentDocs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              <FileText size={28} className="mx-auto mb-2 opacity-40" />
              <p>Chưa có tài liệu nào được dịch gần đây.</p>
              <button
                type="button"
                onClick={() => navigate("/translation-doc")}
                className="mt-2 text-xs font-semibold text-blue-600 hover:underline"
              >
                + Tải lên tài liệu đầu tiên
              </button>
            </div>
          ) : (
            recentDocs.map((doc) => (
              <div
                key={doc.id}
                className="group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50/50 p-3.5 transition-all hover:border-blue-200 hover:bg-blue-50/30 dark:border-slate-700/60 dark:bg-slate-900/40 dark:hover:border-blue-800 dark:hover:bg-slate-900/80"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400">
                    <FileCheck size={20} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="truncate text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                        {doc.name}
                      </h4>
                      <span className="flex-shrink-0 rounded-md bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
                        Hoàn tất
                      </span>
                    </div>
                    {doc.translatedTitle && (
                      <p className="truncate text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        {doc.translatedTitle}
                      </p>
                    )}
                    <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-400">
                      {doc.pageCount && <span>{doc.pageCount} trang</span>}
                      {doc.fileSize && <span>• {doc.fileSize}</span>}
                      <span className="flex items-center gap-1">
                        <Clock size={11} /> {doc.modifiedAt}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-shrink-0 items-center gap-2 self-end sm:self-center">
                  <button
                    type="button"
                    onClick={() => navigate("/translation-doc")}
                    className="flex items-center gap-1 rounded-xl bg-white border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
                  >
                    <span>Mở đọc song ngữ</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate("/translation-doc")}
                    className="flex items-center gap-1 rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
                  >
                    <Sparkles size={12} />
                    <span>Hỏi đáp RAG</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Chat Sessions Content */}
      {activeTab === "chats" && (
        <div className="mt-4 space-y-2.5">
          {recentChats.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              <MessageSquare size={28} className="mx-auto mb-2 opacity-40" />
              <p>Chưa có phiên trò chuyện nào.</p>
              <button
                type="button"
                onClick={() => navigate("/chat")}
                className="mt-2 text-xs font-semibold text-blue-600 hover:underline"
              >
                + Bắt đầu hỏi đáp với Trợ lý AI
              </button>
            </div>
          ) : (
            recentChats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => navigate("/chat")}
                className="group flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50/50 p-3.5 transition-all hover:border-blue-200 hover:bg-blue-50/30 dark:border-slate-700/60 dark:bg-slate-900/40 dark:hover:border-blue-800 dark:hover:bg-slate-900/80 cursor-pointer"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400">
                    <MessageSquare size={18} />
                  </div>
                  <div className="min-w-0">
                    <h4 className="truncate text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {chat.title}
                    </h4>
                    <p className="truncate text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 max-w-xl">
                      {chat.lastMessage}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                      <span>{chat.messageCount} tin nhắn</span>
                      <span>• Cập nhật {chat.updatedAt}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-shrink-0 items-center">
                  <span className="text-xs font-semibold text-blue-600 group-hover:underline flex items-center gap-1">
                    Tiếp tục <ArrowRight size={12} />
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

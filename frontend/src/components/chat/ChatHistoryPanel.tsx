import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { MessageSquare, SquarePen, Pencil, Trash2, AlertTriangle, Clock, PanelLeftClose } from "lucide-react";
import type { ChatSession } from "../../types";
import { useSettings } from "../../context/SettingsContext";

interface ChatHistoryPanelProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onRenameSession: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
  hasMoreSessions: boolean;
  isLoadingMoreSessions: boolean;
  onLoadMoreSessions: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

const MIN_SIDEBAR_WIDTH = 200;
const MAX_SIDEBAR_WIDTH = 520;
const DEFAULT_SIDEBAR_WIDTH = 260;
const SIDEBAR_WIDTH_KEY = "chat_history_sidebar_width";

function formatSessionDateTime(dateString?: string): string {
  if (!dateString) return "";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "";

    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();

    return `${hours}:${minutes} - ${day}/${month}/${year}`;
  } catch {
    return "";
  }
}

function groupByRecency(sessions: ChatSession[]) {
  const today: ChatSession[] = [];
  const yesterday: ChatSession[] = [];
  const older: ChatSession[] = [];

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 86400000;

  for (const s of sessions) {
    const time = s.updatedAt ? new Date(s.updatedAt).getTime() : 0;
    if (time >= startOfToday) {
      today.push(s);
    } else if (time >= startOfYesterday) {
      yesterday.push(s);
    } else {
      older.push(s);
    }
  }
  return { today, yesterday, older };
}

export function ChatHistoryPanel({
  sessions,
  activeSessionId,
  isLoading,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  hasMoreSessions,
  isLoadingMoreSessions,
  onLoadMoreSessions,
  isOpen = true,
  onClose,
}: ChatHistoryPanelProps) {
  const { language } = useSettings();
  const isVi = language === "vi";

  // Persistent Resizable Width
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    const saved = localStorage.getItem(SIDEBAR_WIDTH_KEY);
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= MIN_SIDEBAR_WIDTH && parsed <= MAX_SIDEBAR_WIDTH) {
        return parsed;
      }
    }
    return DEFAULT_SIDEBAR_WIDTH;
  });

  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Sort sessions descending by latest updatedAt timestamp
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => {
      const timeA = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
      const timeB = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
      return timeB - timeA;
    });
  }, [sessions]);

  const { today, yesterday, older } = useMemo(
    () => groupByRecency(sortedSessions),
    [sortedSessions]
  );

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deletingTarget, setDeletingTarget] = useState<ChatSession | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  // Mouse drag handlers for resizing
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!sidebarRef.current) return;
      const sidebarLeft = sidebarRef.current.getBoundingClientRect().left;
      const newWidth = Math.min(
        Math.max(e.clientX - sidebarLeft, MIN_SIDEBAR_WIDTH),
        MAX_SIDEBAR_WIDTH
      );
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    const prevUserSelect = document.body.style.userSelect;
    const prevCursor = document.body.style.cursor;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.body.style.userSelect = prevUserSelect;
      document.body.style.cursor = prevCursor;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  // Persist width when updated
  useEffect(() => {
    localStorage.setItem(SIDEBAR_WIDTH_KEY, sidebarWidth.toString());
  }, [sidebarWidth]);

  const handleResetWidth = () => {
    setSidebarWidth(DEFAULT_SIDEBAR_WIDTH);
  };

  const handleStartEdit = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleCommitEdit = (sessionId: string) => {
    if (editingId === sessionId) {
      if (editTitle.trim()) {
        onRenameSession(sessionId, editTitle.trim());
      }
      setEditingId(null);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setDeletingTarget(session);
  };

  const handleConfirmDelete = () => {
    if (deletingTarget) {
      onDeleteSession(deletingTarget.id);
      setDeletingTarget(null);
    }
  };

  if (!isOpen) return null;

  const renderGroup = (label: string, items: ChatSession[]) =>
    items.length > 0 && (
      <div className="mb-3">
        <p className="mb-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          {label}
        </p>
        <div className="space-y-1">
          {items.map((session) => {
            const isEditing = editingId === session.id;
            const isActive = activeSessionId === session.id;
            const formattedTime = formatSessionDateTime(session.updatedAt);

            if (isEditing) {
              return (
                <div key={session.id} className="px-1 py-1">
                  <input
                    ref={inputRef}
                    type="text"
                    autoFocus
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => handleCommitEdit(session.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleCommitEdit(session.id);
                      } else if (e.key === "Escape") {
                        setEditingId(null);
                      }
                    }}
                    className="w-full rounded-md border border-blue-500 bg-white px-2 py-1 text-xs text-slate-800 focus:outline-none shadow-sm dark:bg-slate-800 dark:text-slate-100"
                  />
                </div>
              );
            }

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group relative flex w-full cursor-pointer flex-col gap-1 rounded-lg px-2.5 py-2 text-left transition-colors ${
                  isActive
                    ? "bg-orange-50 text-orange-900 font-medium dark:bg-orange-950/40 dark:text-orange-200"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700/60"
                }`}
              >
                <div className="flex items-center justify-between gap-1.5">
                  <div className="flex min-w-0 flex-1 items-center gap-1.5">
                    <MessageSquare
                      size={14}
                      className={`flex-shrink-0 ${
                        isActive
                          ? "text-orange-500 dark:text-orange-400"
                          : "text-slate-400 dark:text-slate-500"
                      }`}
                    />
                    <span className="truncate text-xs font-medium" title={session.title}>
                      {session.title}
                    </span>
                  </div>

                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleStartEdit(e, session)}
                      title={isVi ? "Đổi tên cuộc trò chuyện" : "Rename conversation"}
                      className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-600 dark:hover:text-slate-200"
                    >
                      <Pencil size={12} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteClick(e, session)}
                      title={isVi ? "Xóa cuộc trò chuyện" : "Delete conversation"}
                      className="rounded p-1 text-slate-400 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/50 dark:hover:text-red-400"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>

                {formattedTime && (
                  <div className="flex items-center gap-1 pl-5 text-[10.5px] text-slate-400 dark:text-slate-500">
                    <Clock size={11} className="flex-shrink-0 opacity-75" />
                    <span>{formattedTime}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );

  return (
    <>
      <div
        ref={sidebarRef}
        style={{ width: `${sidebarWidth}px` }}
        className="relative flex h-full flex-shrink-0 flex-col border-r border-slate-200 bg-white px-2 py-3 dark:border-slate-700 dark:bg-slate-800"
      >
        <div className="mb-2 flex items-center justify-between px-2">
          <div className="flex items-center gap-1.5 min-w-0">
            {onClose && (
              <button
                onClick={onClose}
                title={isVi ? "Ẩn lịch sử trò chuyện" : "Hide chat history"}
                className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200 transition-colors"
              >
                <PanelLeftClose size={16} />
              </button>
            )}
            <span className="truncate text-sm font-semibold text-slate-700 dark:text-slate-200">
              {isVi ? "Lịch sử trò chuyện" : "Chat History"}
            </span>
          </div>
          <button
            onClick={onNewChat}
            title={isVi ? "Tạo cuộc trò chuyện mới" : "Start new chat"}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-2.5 py-1.5 text-xs font-bold text-white shadow-sm shadow-orange-500/25 hover:from-orange-600 hover:to-amber-600 active:scale-95 transition-all"
          >
            <SquarePen size={14} />
            <span>{isVi ? "Chat mới" : "New"}</span>
          </button>
        </div>

        {isLoading ? (
          <div className="space-y-2 px-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded bg-slate-100 dark:bg-slate-700" />
            ))}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto pr-1">
            {renderGroup(isVi ? "Hôm nay" : "Today", today)}
            {renderGroup(isVi ? "Hôm qua" : "Yesterday", yesterday)}
            {renderGroup(isVi ? "Cũ hơn" : "Older", older)}

            {sortedSessions.length === 0 && (
              <div className="py-8 text-center text-xs text-slate-400 dark:text-slate-500">
                {isVi ? "Chưa có cuộc trò chuyện nào" : "No conversation yet"}
              </div>
            )}

            {hasMoreSessions && (
              <div className="py-2 text-center mt-2 border-t border-slate-100 pt-3 dark:border-slate-700">
                <button
                  onClick={onLoadMoreSessions}
                  disabled={isLoadingMoreSessions}
                  className="rounded-xl border border-orange-200 bg-orange-50 px-3.5 py-1.5 text-xs font-bold text-orange-700 shadow-sm hover:bg-orange-100 hover:border-orange-300 disabled:opacity-50 flex items-center justify-center gap-1.5 mx-auto dark:border-orange-900/50 dark:bg-orange-950/40 dark:text-orange-300 dark:hover:bg-orange-900/60 transition-colors"
                >
                  {isLoadingMoreSessions ? (
                    <>
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-orange-300 border-t-orange-600 dark:border-orange-600"></div>
                      {isVi ? "Đang tải..." : "Loading..."}
                    </>
                  ) : (
                    isVi ? "Tải thêm" : "Load more"
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Resizer Handle */}
        <div
          onMouseDown={handleMouseDown}
          onDoubleClick={handleResetWidth}
          title={isVi ? "Kéo để đổi độ rộng (Nhấp đúp để đặt lại)" : "Drag to resize (Double click to reset)"}
          className={`group absolute -right-1 top-0 z-20 h-full w-2 cursor-col-resize select-none ${
            isResizing ? "bg-blue-500/30" : "hover:bg-blue-500/20"
          }`}
        >
          <div
            className={`mx-auto h-full w-[2px] transition-colors ${
              isResizing
                ? "bg-blue-500"
                : "bg-transparent group-hover:bg-blue-400 dark:group-hover:bg-blue-500"
            }`}
          />
        </div>
      </div>

      {/* --- Delete Confirmation Popup Modal --- */}
      {deletingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl border border-slate-100 animate-in zoom-in-95 dark:bg-slate-800 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400">
                <AlertTriangle size={20} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                  {isVi ? "Xác nhận xóa cuộc trò chuyện" : "Confirm delete conversation"}
                </h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {isVi ? (
                    <>
                      Bạn có chắc chắn muốn xóa cuộc trò chuyện{" "}
                      <strong className="text-slate-700 dark:text-slate-200">
                        "{deletingTarget.title}"
                      </strong>{" "}
                      không?
                    </>
                  ) : (
                    <>
                      Are you sure you want to delete{" "}
                      <strong className="text-slate-700 dark:text-slate-200">
                        "{deletingTarget.title}"
                      </strong>
                      ?
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                onClick={() => setDeletingTarget(null)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                {isVi ? "Hủy" : "Cancel"}
              </button>
              <button
                onClick={handleConfirmDelete}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-700 shadow-sm transition-colors"
              >
                {isVi ? "Xóa ngay" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
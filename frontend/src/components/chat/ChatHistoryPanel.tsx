import { useState, useRef, useEffect, useMemo } from "react";
import {
  AlertTriangle,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  Search,
  SquarePen,
  Trash2,
} from "lucide-react";
import type { ChatSession } from "../../types";
import { useSettings } from "../../context/SettingsContext";

interface ChatHistoryPanelProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  streamingSessionIds?: Set<string>;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onRenameSession: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
  hasMoreSessions: boolean;
  isLoadingMoreSessions: boolean;
  onLoadMoreSessions: () => void;
  /** Đang mở rộng (hiện danh sách). Khi đóng: `inline` thu về thanh icon hẹp (nếu có `onOpen`), `drawer` không render gì. */
  isOpen?: boolean;
  onClose?: () => void;
  /** Mở rộng lại từ thanh icon hẹp (chỉ dùng ở chế độ `inline`). */
  onOpen?: () => void;
  /** `drawer`: ngăn kéo phủ lên nội dung (màn hình nhỏ); `inline`: cột bên cạnh nội dung kiểu ChatGPT. */
  variant?: "inline" | "drawer";
}

const PANEL_WIDTH = 260;
const RAIL_WIDTH = 56;

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

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
  const last7: ChatSession[] = [];
  const older: ChatSession[] = [];

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - ONE_DAY_MS;
  const startOf7Days = startOfToday - 7 * ONE_DAY_MS;

  for (const s of sessions) {
    const time = s.updatedAt ? new Date(s.updatedAt).getTime() : 0;
    if (time >= startOfToday) {
      today.push(s);
    } else if (time >= startOfYesterday) {
      yesterday.push(s);
    } else if (time >= startOf7Days) {
      last7.push(s);
    } else {
      older.push(s);
    }
  }
  return { today, yesterday, last7, older };
}

/** Bỏ dấu tiếng Việt và hạ chữ thường để tìm kiếm không phân biệt dấu. */
const normalizeForSearch = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();

interface RowMenu {
  session: ChatSession;
  top: number;
  left: number;
}

/** Nút icon trần của thanh thu gọn: không nền/viền; rê chuột mới hiện nền trắng + bóng nhẹ. */
const railBtn =
  "relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-slate-500 transition-all hover:bg-white hover:text-brand-700 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 [@media(pointer:coarse)]:h-11 [@media(pointer:coarse)]:w-11";

const iconBtn =
  "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-100 [@media(pointer:coarse)]:h-11 [@media(pointer:coarse)]:w-11";

export function ChatHistoryPanel({
  sessions,
  activeSessionId,
  isLoading,
  streamingSessionIds,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  hasMoreSessions,
  isLoadingMoreSessions,
  onLoadMoreSessions,
  isOpen = true,
  onClose,
  onOpen,
  variant = "inline",
}: ChatHistoryPanelProps) {
  const { language } = useSettings();
  const isVi = language === "vi";
  const isDrawer = variant === "drawer";

  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deletingTarget, setDeletingTarget] = useState<ChatSession | null>(null);
  const [menu, setMenu] = useState<RowMenu | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  // Bấm icon tìm kiếm ở thanh icon: mở rộng rồi đặt con trỏ vào ô tìm kiếm.
  const focusSearchOnOpen = useRef(false);

  // Deduplicate and sort sessions descending by latest updatedAt timestamp
  const sortedSessions = useMemo(() => {
    const map = new Map<string, ChatSession>();
    for (const s of sessions) {
      if (!s || !s.id) continue;
      if (!map.has(s.id)) {
        map.set(s.id, s);
      } else {
        const existing = map.get(s.id)!;
        const timeExisting = existing.updatedAt ? new Date(existing.updatedAt).getTime() : 0;
        const timeCurrent = s.updatedAt ? new Date(s.updatedAt).getTime() : 0;
        if (timeCurrent > timeExisting) {
          map.set(s.id, s);
        }
      }
    }
    return Array.from(map.values()).sort((a, b) => {
      const timeA = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
      const timeB = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
      return timeB - timeA;
    });
  }, [sessions]);

  const filteredSessions = useMemo(() => {
    const q = normalizeForSearch(query.trim());
    if (!q) return sortedSessions;
    return sortedSessions.filter((s) => normalizeForSearch(s.title || "").includes(q));
  }, [sortedSessions, query]);

  const { today, yesterday, last7, older } = useMemo(() => groupByRecency(filteredSessions), [filteredSessions]);

  useEffect(() => {
    if (isOpen && focusSearchOnOpen.current) {
      focusSearchOnOpen.current = false;
      searchRef.current?.focus();
    }
  }, [isOpen]);

  // Menu ⋯: đóng khi bấm ra ngoài hoặc nhấn Esc.
  useEffect(() => {
    if (!menu) return;
    const onPointerDown = (e: PointerEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(null);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setMenu(null);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown, true);
    };
  }, [menu]);

  // Ngăn kéo: Esc để đóng (khi đang sửa tên/mở menu/hỏi xóa thì Esc chỉ đóng phần đó).
  useEffect(() => {
    if (!isDrawer || !isOpen || !onClose) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && editingId === null && deletingTarget === null && menu === null) onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isDrawer, isOpen, onClose, editingId, deletingTarget, menu]);

  const openMenu = (e: React.MouseEvent<HTMLButtonElement>, session: ChatSession) => {
    e.stopPropagation();
    if (menu?.session.id === session.id) {
      setMenu(null);
      return;
    }
    const rect = e.currentTarget.getBoundingClientRect();
    const MENU_W = 176;
    const MENU_H = 92;
    const top = rect.bottom + MENU_H > window.innerHeight ? Math.max(8, rect.top - MENU_H) : rect.bottom + 4;
    const left = Math.max(8, Math.min(rect.right - MENU_W, window.innerWidth - MENU_W - 8));
    setMenu({ session, top, left });
  };

  const handleStartEdit = (session: ChatSession) => {
    setMenu(null);
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

  const handleDeleteClick = (session: ChatSession) => {
    setMenu(null);
    setDeletingTarget(session);
  };

  const handleConfirmDelete = () => {
    if (deletingTarget) {
      onDeleteSession(deletingTarget.id);
      setDeletingTarget(null);
    }
  };

  const newChatLabel = isVi ? "Cuộc trò chuyện mới" : "New chat";
  const historyTitle = isVi ? "Lịch sử trò chuyện" : "Chat history";

  // ---- Thanh icon hẹp (máy tính, khi đã thu gọn) ----
  if (!isOpen && (isDrawer || !onOpen)) return null;

  const isAnyStreaming = (streamingSessionIds?.size ?? 0) > 0;
  const rail = (
    <div className="flex h-full w-14 flex-col items-center gap-1 py-1">
      <button
        type="button"
        onClick={onOpen}
        title={`${isVi ? "Mở lịch sử trò chuyện" : "Open chat history"} (Ctrl+\\)`}
        aria-label={isVi ? "Mở lịch sử trò chuyện" : "Open chat history"}
        className={railBtn}
      >
        <PanelLeftOpen size={19} aria-hidden="true" />
        {isAnyStreaming && (
          <span
            className="absolute right-1.5 top-1.5 h-2 w-2 animate-pulse rounded-full bg-brand-500 ring-2 ring-brand-50 dark:ring-slate-950"
            title={isVi ? "Đang xử lý phản hồi..." : "Generating response..."}
          />
        )}
      </button>
      <button
        type="button"
        onClick={onNewChat}
        title={`${newChatLabel} (Ctrl+Shift+O)`}
        aria-label={newChatLabel}
        className={railBtn}
      >
        <SquarePen size={19} aria-hidden="true" />
      </button>
      <button
        type="button"
        onClick={() => {
          focusSearchOnOpen.current = true;
          onOpen?.();
        }}
        title={isVi ? "Tìm kiếm cuộc trò chuyện" : "Search chats"}
        aria-label={isVi ? "Tìm kiếm cuộc trò chuyện" : "Search chats"}
        className={railBtn}
      >
        <Search size={19} aria-hidden="true" />
      </button>
    </div>
  );

  const renderGroup = (label: string, items: ChatSession[]) =>
    items.length > 0 && (
      <div className="mb-3">
        <p className="mb-1 px-2.5 text-xs sm:text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          {label}
        </p>
        <div className="space-y-0.5">
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
                    aria-label={isVi ? "Tên cuộc trò chuyện" : "Conversation name"}
                    className="w-full rounded-lg border border-brand-500 bg-white px-2 py-1.5 text-sm text-slate-800 shadow-sm focus:outline-none dark:bg-slate-800 dark:text-slate-100"
                  />
                </div>
              );
            }

            const menuOpen = menu?.session.id === session.id;
            return (
              <div key={session.id} className="group relative">
                <button
                  type="button"
                  onClick={() => onSelectSession(session.id)}
                  title={formattedTime ? `${session.title} — ${formattedTime}` : session.title}
                  aria-current={isActive ? "true" : undefined}
                  className={`flex w-full items-center gap-2 rounded-lg py-2 pl-2.5 pr-9 text-left text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 [@media(pointer:coarse)]:min-h-[44px] ${
                    isActive || menuOpen
                      ? "bg-brand-50 font-medium text-brand-800 dark:bg-brand-950/50 dark:text-brand-200"
                      : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700/60"
                  }`}
                >
                  <span className="min-w-0 flex-1 truncate">{session.title}</span>
                  {streamingSessionIds?.has(session.id) && (
                    <span
                      className="inline-block h-2 w-2 flex-shrink-0 animate-pulse rounded-full bg-brand-500"
                      title={isVi ? "Đang xử lý phản hồi..." : "Generating response..."}
                    />
                  )}
                </button>

                <button
                  type="button"
                  onClick={(e) => openMenu(e, session)}
                  aria-label={isVi ? "Tùy chọn cuộc trò chuyện" : "Conversation options"}
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  className={`absolute right-1 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 transition-opacity hover:bg-slate-200 hover:text-slate-800 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-slate-100 [@media(pointer:coarse)]:h-10 [@media(pointer:coarse)]:w-10 ${
                    menuOpen ? "opacity-100" : "opacity-0 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
                  }`}
                >
                  <MoreHorizontal size={16} aria-hidden="true" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );

  const content = (
    <div
      className={`flex h-full flex-col bg-white py-3 dark:bg-slate-800 ${isDrawer ? "w-80 max-w-[85vw] shadow-2xl" : ""}`}
      style={isDrawer ? undefined : { width: `${PANEL_WIDTH}px` }}
      {...(isDrawer ? { role: "dialog", "aria-modal": true, "aria-label": historyTitle } : {})}
    >
      <div className="mb-2 flex items-center gap-1 px-2">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            title={isDrawer ? (isVi ? "Đóng" : "Close") : `${isVi ? "Thu gọn lịch sử" : "Collapse history"} (Ctrl+\\)`}
            aria-label={isDrawer ? (isVi ? "Đóng lịch sử trò chuyện" : "Close chat history") : isVi ? "Thu gọn lịch sử trò chuyện" : "Collapse chat history"}
            className={iconBtn}
          >
            <PanelLeftClose size={18} aria-hidden="true" />
          </button>
        )}
        <span className="min-w-0 flex-1 truncate px-1 text-sm font-semibold text-slate-700 dark:text-slate-200">{historyTitle}</span>
      </div>

      <div className="space-y-2 px-3 pb-2">
        <button
          type="button"
          onClick={onNewChat}
          title={`${newChatLabel} (Ctrl+Shift+O)`}
          className="flex w-full items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-3 py-2.5 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-900/50 [@media(pointer:coarse)]:min-h-[44px]"
        >
          <SquarePen size={16} aria-hidden="true" className="flex-shrink-0" />
          <span className="truncate">{newChatLabel}</span>
        </button>

        <label className="relative block">
          <span className="sr-only">{isVi ? "Tìm kiếm cuộc trò chuyện" : "Search chats"}</span>
          <Search size={15} aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            ref={searchRef}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={isVi ? "Tìm kiếm cuộc trò chuyện..." : "Search chats..."}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 [@media(pointer:coarse)]:py-2.5"
          />
        </label>
      </div>

      {isLoading ? (
        <div className="space-y-2 px-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-8 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-700" />
          ))}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-2">
          {renderGroup(isVi ? "Hôm nay" : "Today", today)}
          {renderGroup(isVi ? "Hôm qua" : "Yesterday", yesterday)}
          {renderGroup(isVi ? "7 ngày trước" : "Previous 7 days", last7)}
          {renderGroup(isVi ? "Cũ hơn" : "Older", older)}

          {filteredSessions.length === 0 && (
            <div className="py-8 text-center text-xs text-slate-400 dark:text-slate-500">
              {query.trim()
                ? isVi
                  ? "Không tìm thấy cuộc trò chuyện nào"
                  : "No matching conversation"
                : isVi
                  ? "Chưa có cuộc trò chuyện nào"
                  : "No conversation yet"}
            </div>
          )}

          {hasMoreSessions && (
            <div className="mt-2 border-t border-slate-100 py-2 pt-3 text-center dark:border-slate-700">
              <button
                type="button"
                onClick={onLoadMoreSessions}
                disabled={isLoadingMoreSessions}
                className="mx-auto flex items-center justify-center gap-1.5 rounded-xl border border-brand-200 bg-brand-50 px-3.5 py-1.5 text-xs font-bold text-brand-700 shadow-sm hover:border-brand-300 hover:bg-brand-100 disabled:opacity-50 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-900/50 [@media(pointer:coarse)]:min-h-[44px]"
              >
                {isLoadingMoreSessions ? (
                  <>
                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-brand-300 border-t-brand-600 dark:border-brand-600"></div>
                    {isVi ? "Đang tải..." : "Loading..."}
                  </>
                ) : isVi ? (
                  "Tải thêm"
                ) : (
                  "Load more"
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      {isDrawer ? (
        <div className="fixed inset-0 z-40">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
          <div className="absolute inset-y-0 left-0 flex">{content}</div>
        </div>
      ) : (
        <div
          className={`relative my-3 ml-1 h-[calc(100%-1.5rem)] flex-shrink-0 overflow-hidden rounded-2xl border transition-[width,background-color,box-shadow,border-color] duration-200 motion-reduce:transition-none ${
            isOpen
              ? "border-brand-100 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
              : "border-transparent bg-transparent"
          }`}
          style={{ width: `${isOpen ? PANEL_WIDTH : RAIL_WIDTH}px` }}
        >
          {isOpen ? content : rail}
        </div>
      )}

      {/* --- Menu ⋯ của một cuộc trò chuyện (vị trí cố định theo nút để không bị khung cuộn cắt) --- */}
      {menu && (
        <div
          ref={menuRef}
          role="menu"
          style={{ top: menu.top, left: menu.left }}
          className="fixed z-50 w-44 rounded-xl border border-slate-200 bg-white p-1 shadow-xl dark:border-slate-700 dark:bg-slate-800"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => handleStartEdit(menu.session)}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700 [@media(pointer:coarse)]:min-h-[44px]"
          >
            <Pencil size={15} aria-hidden="true" />
            {isVi ? "Đổi tên" : "Rename"}
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => handleDeleteClick(menu.session)}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40 [@media(pointer:coarse)]:min-h-[44px]"
          >
            <Trash2 size={15} aria-hidden="true" />
            {isVi ? "Xóa" : "Delete"}
          </button>
        </div>
      )}

      {/* --- Delete Confirmation Popup Modal --- */}
      {deletingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-sm rounded-2xl border border-slate-100 bg-white p-5 shadow-2xl animate-in zoom-in-95 dark:border-slate-700 dark:bg-slate-800">
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
                      <strong className="text-slate-700 dark:text-slate-200">"{deletingTarget.title}"</strong> không?
                    </>
                  ) : (
                    <>
                      Are you sure you want to delete{" "}
                      <strong className="text-slate-700 dark:text-slate-200">"{deletingTarget.title}"</strong>?
                    </>
                  )}
                </p>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeletingTarget(null)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 [@media(pointer:coarse)]:min-h-[44px]"
              >
                {isVi ? "Hủy" : "Cancel"}
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-red-700 [@media(pointer:coarse)]:min-h-[44px]"
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

import { useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { ChatHistoryPanel } from "../components/chat/ChatHistoryPanel";
import { ChatMessageBubble } from "../components/chat/ChatMessageBubble";
import { ChatComposer } from "../components/chat/ChatComposer";
import { ChatWelcomeScreen } from "../components/chat/ChatWelcomeScreen";
import { PanelLeftOpen } from "lucide-react";
import { useSettings } from "../context/SettingsContext";
import { useMediaQuery } from "../hooks/useMediaQuery";

export default function ChatPage() {
  const { language } = useSettings();
  const isVi = language === "vi";

  const {
    sessions,
    activeSessionId,
    messages,
    isSending,
    isLoadingSessions,
    error,
    streamingSessionIds,
    selectSession,
    startNewSession,
    sendMessage,
    renameSession,
    deleteSession,
    abortStream,
    hasMoreSessions,
    isLoadingMoreSessions,
    loadMoreSessions,
    hasMoreMessages,
    isLoadingMoreMessages,
    loadMoreMessages,
  } = useChat();

  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(() => {
    const saved = localStorage.getItem("chat_history_panel_open");
    return saved !== null ? saved === "true" : true;
  });

  // Từ lg (1024px) lịch sử là cột bên cạnh (trạng thái đóng/mở được nhớ); dưới lg là ngăn kéo, luôn mở lại ở trạng thái đóng.
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const closeDrawer = () => setIsDrawerOpen(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem("chat_history_panel_open", next.toString());
      return next;
    });
  };

  // Phím tắt kiểu ChatGPT: Ctrl+Shift+O = cuộc trò chuyện mới, Ctrl+\ = mở/thu gọn lịch sử.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      if (e.shiftKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        startNewSession();
        if (!isDesktop) closeDrawer();
      } else if (!e.shiftKey && e.key === "\\") {
        e.preventDefault();
        if (isDesktop) toggleSidebar();
        else setIsDrawerOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const scrollRef = useRef<HTMLDivElement>(null);
  const prevScrollHeightRef = useRef<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (!isLoadingMoreMessages) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, isLoadingMoreMessages]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop } = scrollRef.current;
    
    if (scrollTop === 0 && hasMoreMessages && !isLoadingMoreMessages) {
      prevScrollHeightRef.current = scrollRef.current.scrollHeight;
      loadMoreMessages();
    }
  };

  return (
    <div className="relative flex h-full overflow-hidden">
      <ChatHistoryPanel
        sessions={sessions}
        activeSessionId={activeSessionId}
        isLoading={isLoadingSessions}
        streamingSessionIds={streamingSessionIds}
        onSelectSession={(id) => {
          selectSession(id);
          if (!isDesktop) closeDrawer();
        }}
        onNewChat={() => {
          startNewSession();
          if (!isDesktop) closeDrawer();
        }}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        hasMoreSessions={hasMoreSessions}
        isLoadingMoreSessions={isLoadingMoreSessions}
        onLoadMoreSessions={loadMoreSessions}
        isOpen={isDesktop ? isSidebarOpen : isDrawerOpen}
        onClose={isDesktop ? toggleSidebar : closeDrawer}
        onOpen={toggleSidebar}
        variant={isDesktop ? "inline" : "drawer"}
      />

      <div className="relative flex min-w-0 flex-1 flex-col">
        {/* Điện thoại/máy tính bảng: chỉ một icon nhỏ nổi ở góc trái để mở lịch sử (không chiếm hàng riêng). */}
        {!isDesktop && (
          <button
            type="button"
            onClick={() => setIsDrawerOpen(true)}
            aria-label={isVi ? "Mở lịch sử trò chuyện" : "Open chat history"}
            title={isVi ? "Lịch sử trò chuyện" : "Chat history"}
            className="absolute left-2 top-2 z-20 flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-600 shadow-sm backdrop-blur hover:bg-white hover:text-brand-700 active:scale-95 dark:border-slate-700 dark:bg-slate-800/90 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-brand-300"
          >
            <PanelLeftOpen size={20} aria-hidden="true" />
          </button>
        )}

        {/* Message / Welcome Area */}
        <div ref={scrollRef} onScroll={handleScroll} className={`flex-1 space-y-4 overflow-y-auto px-4 pb-5 sm:px-6 ${isDesktop ? "pt-5" : "pt-14"}`}>
          {isLoadingMoreMessages && (
            <div className="py-2 text-center text-xs text-slate-500 flex justify-center items-center gap-2 dark:text-slate-400">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600 dark:border-slate-600"></div>
              {isVi ? "Đang tải tin nhắn cũ..." : "Loading older messages..."}
            </div>
          )}

          {messages.length === 0 ? (
            <ChatWelcomeScreen onSelectPrompt={(prompt) => sendMessage(prompt)} />
          ) : (
            messages.map((message, index) => (
              <ChatMessageBubble
                key={message.id}
                message={message}
                isLatest={index === messages.length - 1}
                onSendMessage={sendMessage}
                previousUserMessage={index > 0 ? messages[index - 1] : undefined}
              />
            ))
          )}

          <div ref={messagesEndRef} />

          {error && (
            <div className="mx-auto max-w-md rounded-xl bg-red-50 p-3 text-center text-xs text-red-600 border border-red-200/60 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/40">
              {error}
            </div>
          )}
        </div>

        {/* Composer Input Bar */}
        <ChatComposer onSend={sendMessage} isSending={isSending} onAbort={abortStream} />
      </div>
    </div>
  );
}

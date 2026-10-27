import { useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { ChatHistoryPanel } from "../components/chat/ChatHistoryPanel";
import { ChatMessageBubble } from "../components/chat/ChatMessageBubble";
import { ChatComposer } from "../components/chat/ChatComposer";
import { ChatWelcomeScreen } from "../components/chat/ChatWelcomeScreen";
import { PanelLeftOpen } from "lucide-react";
import { useSettings } from "../context/SettingsContext";

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

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem("chat_history_panel_open", next.toString());
      return next;
    });
  };

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
        onSelectSession={selectSession}
        onNewChat={startNewSession}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        hasMoreSessions={hasMoreSessions}
        isLoadingMoreSessions={isLoadingMoreSessions}
        onLoadMoreSessions={loadMoreSessions}
        isOpen={isSidebarOpen}
        onClose={toggleSidebar}
      />

      <div className="relative flex min-w-0 flex-1 flex-col bg-slate-50 dark:bg-slate-900/50">
        {/* Floating toggle button when history panel is hidden */}
        {!isSidebarOpen && (
          <div className="absolute top-3.5 left-3.5 z-20">
            <button
              onClick={toggleSidebar}
              title={isVi ? "Hiện lịch sử trò chuyện" : "Show chat history"}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-3 py-1.5 text-xs font-bold text-white shadow-md shadow-orange-500/25 hover:from-orange-600 hover:to-amber-600 active:scale-95 transition-all"
            >
              <PanelLeftOpen size={15} />
              <span>{isVi ? "Lịch sử" : "History"}</span>
            </button>
          </div>
        )}

        {/* Message / Welcome Area */}
        <div ref={scrollRef} onScroll={handleScroll} className="flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6">
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

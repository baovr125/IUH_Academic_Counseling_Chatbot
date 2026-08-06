import { useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import { ChatHistoryPanel } from "../components/chat/ChatHistoryPanel";
import { ChatMessageBubble } from "../components/chat/ChatMessageBubble";
import { ChatComposer } from "../components/chat/ChatComposer";
import { MessageSquareText } from "lucide-react";

export default function ChatPage() {
  const {
    sessions,
    activeSessionId,
    messages,
    isSending,
    isLoadingSessions,
    error,
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

  const scrollRef = useRef<HTMLDivElement>(null);
  const prevScrollHeightRef = useRef<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages if we are at the bottom, or if this is the first load
  // Actually, we should scroll to bottom when a new message is added by the user, but preserve scroll when loading older messages.
  useEffect(() => {
    if (!scrollRef.current) return;
    
    // If we loaded more older messages, we want to maintain our relative scroll position
    const currentScrollHeight = scrollRef.current.scrollHeight;
    if (prevScrollHeightRef.current > 0 && currentScrollHeight > prevScrollHeightRef.current && isLoadingMoreMessages) {
       // Scroll position adjustment after prepending items could go here if needed, 
       // but typically browsers handle this okay or we adjust manually.
    }
  }, [messages, isLoadingMoreMessages]);

  useEffect(() => {
    // Only auto-scroll to bottom when a new user message is sent (messages length increases and it's at the end)
    // For simplicity, let's just scroll to bottom if we are not loading more messages
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
    <div className="flex h-full">
      <ChatHistoryPanel
        sessions={sessions}
        activeSessionId={activeSessionId}
        isLoading={isLoadingSessions}
        onSelectSession={selectSession}
        onNewChat={startNewSession}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        hasMoreSessions={hasMoreSessions}
        isLoadingMoreSessions={isLoadingMoreSessions}
        onLoadMoreSessions={loadMoreSessions}
      />

      <div className="flex min-w-0 flex-1 flex-col bg-slate-50">
        <div ref={scrollRef} onScroll={handleScroll} className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
          {isLoadingMoreMessages && (
             <div className="py-2 text-center text-xs text-slate-500 flex justify-center items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"></div>
                Đang tải tin nhắn cũ...
             </div>
          )}

          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
              <MessageSquareText size={32} className="mb-2" />
              <p className="text-sm">Ask anything about IUH's academic rules, forms, or policies.</p>
            </div>
          ) : (
            messages.map((message, index) => <ChatMessageBubble key={message.id} message={message} isLatest={index === messages.length - 1} onSendMessage={sendMessage} />)
          )}
          
          <div ref={messagesEndRef} />

          {error && (
            <div className="mx-auto max-w-md rounded-lg bg-red-50 px-3 py-2 text-center text-xs text-red-600">
              {error}
            </div>
          )}
        </div>

        <ChatComposer onSend={sendMessage} isSending={isSending} onAbort={abortStream} />
      </div>
    </div>
  );
}

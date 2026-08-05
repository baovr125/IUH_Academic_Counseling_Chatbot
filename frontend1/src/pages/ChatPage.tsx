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
  } = useChat();

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

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
      />

      <div className="flex min-w-0 flex-1 flex-col bg-slate-50">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
              <MessageSquareText size={32} className="mb-2" />
              <p className="text-sm">Ask anything about IUH's academic rules, forms, or policies.</p>
            </div>
          ) : (
            messages.map((message) => <ChatMessageBubble key={message.id} message={message} onSendMessage={sendMessage} />)
          )}

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

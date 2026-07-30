import { useCallback, useEffect, useState } from "react";
import * as chatService from "../services/chatService";
import type { ChatMessage, ChatSession } from "../types";

interface UseChatReturn {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  isSending: boolean;
  isLoadingSessions: boolean;
  error: string | null;
  selectSession: (sessionId: string) => void;
  startNewSession: () => void;
  sendMessage: (content: string) => Promise<void>;
}

/**
 * Owns all chat/RAG state for the Knowledge Hub screen. Components only
 * ever read `messages` / `isSending` and call `sendMessage` — they never
 * touch chatService directly, so swapping the mock service for real fetch
 * calls to FastAPI later is a one-file change.
 */
export function useChat(): UseChatReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load of chat history sidebar.
  useEffect(() => {
    (async () => {
      setIsLoadingSessions(true);
      const result = await chatService.fetchSessions();
      setIsLoadingSessions(false);

      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      setSessions(result.data);
      const first = result.data[0];
      if (first) {
        setActiveSessionId(first.id);
        setMessages(first.messages);
      }
    })();
  }, []);

  const selectSession = useCallback(
    (sessionId: string) => {
      const session = sessions.find((s) => s.id === sessionId);
      setActiveSessionId(sessionId);
      setMessages(session?.messages ?? []);
    },
    [sessions]
  );

  const startNewSession = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isSending) return;
      setError(null);

      // Optimistic user bubble, then a pending assistant bubble while we
      // "wait" on the RAG pipeline — this is the loading state the chat
      // screen renders as a typing indicator.
      const optimisticUserMessage: ChatMessage = {
        id: `temp_${Date.now()}`,
        role: "user",
        content,
        createdAt: new Date().toISOString(),
        status: "complete",
      };
      const pendingAssistantMessage: ChatMessage = {
        id: `temp_pending_${Date.now()}`,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        status: "pending",
      };

      setMessages((prev) => [...prev, optimisticUserMessage, pendingAssistantMessage]);
      setIsSending(true);

      const result = await chatService.sendMessage({
        sessionId: activeSessionId,
        content,
      });

      setIsSending(false);

      if (!result.ok) {
        setError(result.error.message);
        setMessages((prev) => prev.filter((m) => m.id !== pendingAssistantMessage.id));
        return;
      }

      setActiveSessionId(result.data.sessionId);
      setMessages((prev) =>
        prev.map((m) => (m.id === pendingAssistantMessage.id ? result.data.message : m))
      );

      // Refresh the session list so titles / ordering stay in sync.
      const refreshed = await chatService.fetchSessions();
      if (refreshed.ok) setSessions(refreshed.data);
    },
    [activeSessionId, isSending]
  );

  return {
    sessions,
    activeSessionId,
    messages,
    isSending,
    isLoadingSessions,
    error,
    selectSession,
    startNewSession,
    sendMessage,
  };
}

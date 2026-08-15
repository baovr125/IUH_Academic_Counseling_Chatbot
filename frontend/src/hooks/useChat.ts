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
  renameSession: (sessionId: string, newTitle: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  abortStream: () => void;
  hasMoreSessions: boolean;
  isLoadingMoreSessions: boolean;
  loadMoreSessions: () => Promise<void>;
  hasMoreMessages: boolean;
  isLoadingMoreMessages: boolean;
  loadMoreMessages: () => Promise<void>;
}

/**
 * Owns all chat/RAG state for the Knowledge Hub screen. Components only
 * ever read `messages` / `isSending` and call `sendMessage` — they never
 * touch chatService directly, so swapping the mock service for real fetch
 * calls to FastAPI later is a one-file change.
 */
export function useChat(): UseChatReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    return localStorage.getItem("activeChatSessionId");
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const [isLoadingMoreSessions, setIsLoadingMoreSessions] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [isLoadingMoreMessages, setIsLoadingMoreMessages] = useState(false);

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
      setSessions(result.data || []);
      setHasMoreSessions(result.data ? result.data.length === 20 : false);
      
      const storedId = localStorage.getItem("activeChatSessionId");
      const matched = (result.data || []).find(s => s.id === storedId);
      
      if (matched) {
        setActiveSessionId(matched.id);
        const msgsRes = await chatService.fetchSessionMessages(matched.id);
        setMessages(msgsRes.ok && msgsRes.data ? msgsRes.data : []);
        setHasMoreMessages(msgsRes.ok && msgsRes.data ? msgsRes.data.length === 50 : false);
      } else {
        const first = result.data ? result.data[0] : undefined;
        if (first) {
          setActiveSessionId(first.id);
          localStorage.setItem("activeChatSessionId", first.id);
          const msgsRes = await chatService.fetchSessionMessages(first.id);
          setMessages(msgsRes.ok && msgsRes.data ? msgsRes.data : []);
          setHasMoreMessages(msgsRes.ok && msgsRes.data ? msgsRes.data.length === 50 : false);
        }
      }
    })();
  }, []);

  const selectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      localStorage.setItem("activeChatSessionId", sessionId);
      const msgsRes = await chatService.fetchSessionMessages(sessionId);
      setMessages(msgsRes.ok && msgsRes.data ? msgsRes.data : []);
      setHasMoreMessages(msgsRes.ok && msgsRes.data ? msgsRes.data.length === 50 : false);
    },
    []
  );

  const loadMoreSessions = useCallback(async () => {
    if (isLoadingMoreSessions || !hasMoreSessions) return;
    setIsLoadingMoreSessions(true);
    const result = await chatService.fetchSessions(20, sessions.length);
    setIsLoadingMoreSessions(false);
    if (result.ok && result.data) {
      setSessions((prev) => [...prev, ...result.data]);
      setHasMoreSessions(result.data.length === 20);
    }
  }, [isLoadingMoreSessions, hasMoreSessions, sessions.length]);

  const loadMoreMessages = useCallback(async () => {
    if (isLoadingMoreMessages || !hasMoreMessages || !activeSessionId) return;
    setIsLoadingMoreMessages(true);
    const msgsRes = await chatService.fetchSessionMessages(activeSessionId, 50, messages.length);
    setIsLoadingMoreMessages(false);
    if (msgsRes.ok && msgsRes.data) {
      // New messages are older, so they should be prepended
      setMessages((prev) => [...msgsRes.data, ...prev]);
      setHasMoreMessages(msgsRes.data.length === 50);
    }
  }, [isLoadingMoreMessages, hasMoreMessages, activeSessionId, messages.length]);


  const startNewSession = useCallback(() => {
    setActiveSessionId(null);
    localStorage.removeItem("activeChatSessionId");
    setMessages([]);
  }, []);

  const renameSession = useCallback(
    async (sessionId: string, newTitle: string) => {
      if (!newTitle.trim()) return;
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle.trim() } : s))
      );
      await chatService.renameSession(sessionId, newTitle.trim());
    },
    []
  );

  const deleteSession = useCallback(
    async (sessionId: string) => {
      let nextIdToLoad: string | null = null;
      setSessions((prev) => {
        const updated = prev.filter((s) => s.id !== sessionId);
        if (activeSessionId === sessionId) {
          const next = updated[0];
          setActiveSessionId(next?.id ?? null);
          if (next?.id) {
            localStorage.setItem("activeChatSessionId", next.id);
            nextIdToLoad = next.id;
          } else {
            localStorage.removeItem("activeChatSessionId");
            setMessages([]);
          }
        }
        return updated;
      });
      
      if (nextIdToLoad) {
        const msgsRes = await chatService.fetchSessionMessages(nextIdToLoad);
        setMessages(msgsRes.ok && msgsRes.data ? msgsRes.data : []);
        setHasMoreMessages(msgsRes.ok && msgsRes.data ? msgsRes.data.length === 50 : false);
      }
      
      await chatService.deleteSession(sessionId);
    },
    [activeSessionId]
  );

  const abortStream = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsSending(false);
    }
  }, [abortController]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isSending) return;
      setError(null);

      let currentSessionId = activeSessionId;
      
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
      
      if (!currentSessionId) {
        currentSessionId = `s_${Date.now()}`;
        setActiveSessionId(currentSessionId);
        localStorage.setItem("activeChatSessionId", currentSessionId);
        
        // Optimistically add the new session to the sidebar
        const newSession: ChatSession = {
          id: currentSessionId,
          title: content.slice(0, 40) + (content.length > 40 ? "..." : ""),
          updatedAt: new Date().toISOString(),
          messages: [optimisticUserMessage],
        };
        setSessions(prev => [newSession, ...prev]);
      } else {
        // Optimistically update the existing session's message list in the sidebar
        setSessions(prev => 
          prev.map(s => 
            s.id === currentSessionId 
              ? { ...s, updatedAt: new Date().toISOString(), messages: [...s.messages, optimisticUserMessage] } 
              : s
          )
        );
      }

      const pendingAssistantMessage: ChatMessage = {
        id: `temp_pending_${Date.now()}`,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        status: "pending",
      };

      setMessages((prev) => [...prev, optimisticUserMessage, pendingAssistantMessage]);
      setIsSending(true);
      const newAbortController = new AbortController();
      setAbortController(newAbortController);

      await chatService.sendMessageStream(
        {
          sessionId: currentSessionId,
          content,
        },
        {
          onMetadata: async ({ sessionId, citations }) => {
            if (sessionId) {
              setActiveSessionId(sessionId);
              localStorage.setItem("activeChatSessionId", sessionId);
              
              setSessions((prev) =>
                prev.map((s) =>
                  s.id === currentSessionId
                    ? { ...s, id: sessionId, updatedAt: new Date().toISOString() }
                    : s
                )
              );
              currentSessionId = sessionId;
            }
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, citations }
                  : m
              )
            );
          },
          onDelta: (chunkText) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, content: m.content + chunkText }
                  : m
              )
            );
          },
          onDone: async () => {
            setIsSending(false);
            setAbortController(null);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, status: "complete" }
                  : m
              )
            );
            
            setSessions((prev) => {
              const target = prev.find((s) => s.id === currentSessionId);
              if (!target) return prev;
              const filtered = prev.filter((s) => s.id !== currentSessionId);
              return [{ ...target, updatedAt: new Date().toISOString() }, ...filtered];
            });
          },
          onError: (errMsg) => {
            setIsSending(false);
            setAbortController(null);
            setError(errMsg);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, content: m.content || `⚠️ Lỗi: ${errMsg}`, status: "complete" }
                  : m
              )
            );
          },
        },
        newAbortController.signal
      );
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
    renameSession,
    deleteSession,
    abortStream,
    hasMoreSessions,
    isLoadingMoreSessions,
    loadMoreSessions,
    hasMoreMessages,
    isLoadingMoreMessages,
    loadMoreMessages,
  };
}

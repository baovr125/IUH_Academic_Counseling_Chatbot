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
  sendMessage: (
    content: string, 
    bypassCache?: boolean, 
    replaceMessageIds?: { userMsgId?: string; assistantMsgId?: string }
  ) => Promise<void>;
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
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const [isLoadingMoreSessions, setIsLoadingMoreSessions] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [isLoadingMoreMessages, setIsLoadingMoreMessages] = useState(false);

  // Initial load of chat history sidebar. Always default to a fresh new chat session.
  useEffect(() => {
    (async () => {
      setIsLoadingSessions(true);
      const result = await chatService.fetchSessions();
      setIsLoadingSessions(false);

      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      const rawSessions = result.data || [];
      const sorted = [...rawSessions].sort(
        (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
      );
      setSessions(sorted);
      setHasMoreSessions(rawSessions.length === 20);

      // Default to fresh new chat as requested
      setActiveSessionId(null);
      setMessages([]);
      localStorage.removeItem("activeChatSessionId");
    })();
  }, []);

  // Listen for global reset-chat-view event to switch to new chat when clicking nav
  useEffect(() => {
    const handleReset = () => {
      setActiveSessionId(null);
      localStorage.removeItem("activeChatSessionId");
      setMessages([]);
    };
    window.addEventListener("reset-chat-view", handleReset);
    return () => window.removeEventListener("reset-chat-view", handleReset);
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
      setSessions((prev) => {
        const combined = [...prev, ...result.data];
        const map = new Map<string, ChatSession>();
        for (const s of combined) {
          map.set(s.id, s);
        }
        return Array.from(map.values()).sort(
          (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
        );
      });
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
    async (
      content: string, 
      bypassCache: boolean = false, 
      replaceMessageIds?: { userMsgId?: string; assistantMsgId?: string }
    ) => {
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
        
        // Optimistically add the new session to the top of the sidebar
        const newSession: ChatSession = {
          id: currentSessionId,
          title: content.slice(0, 40) + (content.length > 40 ? "..." : ""),
          updatedAt: new Date().toISOString(),
          messages: [optimisticUserMessage],
        };
        setSessions(prev => [newSession, ...prev]);
      } else {
        // Optimistically update the existing session's message list in the sidebar and move to top
        setSessions(prev => {
          const target = prev.find(s => s.id === currentSessionId);
          if (!target) return prev;
          let targetMessages = target.messages || [];
          if (replaceMessageIds?.userMsgId || replaceMessageIds?.assistantMsgId) {
            targetMessages = targetMessages.filter(
              (m) =>
                m.id !== replaceMessageIds.userMsgId &&
                m.id !== replaceMessageIds.assistantMsgId
            );
          } else if (bypassCache) {
            targetMessages = targetMessages.length >= 2 ? targetMessages.slice(0, targetMessages.length - 2) : [];
          }
          const updated: ChatSession = {
            ...target,
            updatedAt: new Date().toISOString(),
            messages: [...targetMessages, optimisticUserMessage],
          };
          return [updated, ...prev.filter(s => s.id !== currentSessionId)];
        });
      }

      const pendingAssistantMessage: ChatMessage = {
        id: `temp_pending_${Date.now()}`,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        status: "pending",
      };

      setMessages((prev) => {
        let base = prev;
        if (replaceMessageIds?.userMsgId || replaceMessageIds?.assistantMsgId) {
          base = base.filter(
            (m) =>
              m.id !== replaceMessageIds.userMsgId &&
              m.id !== replaceMessageIds.assistantMsgId
          );
        } else if (bypassCache) {
          base = base.length >= 2 ? base.slice(0, base.length - 2) : [];
        }
        return [...base, optimisticUserMessage, pendingAssistantMessage];
      });

      setIsSending(true);
      const newAbortController = new AbortController();
      setAbortController(newAbortController);

      const idsToDelete = [replaceMessageIds?.userMsgId, replaceMessageIds?.assistantMsgId].filter(
        (id): id is string => Boolean(id)
      );

      await chatService.sendMessageStream(
        {
          sessionId: currentSessionId,
          content,
          bypassCache,
          replaceMessageIds: idsToDelete.length > 0 ? idsToDelete : undefined,
        },
        {
          onMetadata: async ({ sessionId, citations, cacheStatus }) => {
            if (sessionId) {
              setActiveSessionId(sessionId);
              localStorage.setItem("activeChatSessionId", sessionId);
              
              setSessions((prev) => {
                const target = prev.find((s) => s.id === currentSessionId);
                const updated: ChatSession = target
                  ? { ...target, id: sessionId, updatedAt: new Date().toISOString() }
                  : {
                      id: sessionId,
                      title: content.slice(0, 40) + (content.length > 40 ? "..." : ""),
                      updatedAt: new Date().toISOString(),
                      messages: [],
                    };
                return [updated, ...prev.filter((s) => s.id !== currentSessionId && s.id !== sessionId)];
              });
              currentSessionId = sessionId;
            }
            setMessages((prev) =>
              prev.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, citations, cacheStatus }
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

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import * as chatService from "../services/chatService";
import { generateUUID } from "../services/utils";
import type { ChatMessage, ChatSession } from "../types";

export interface UseChatReturn {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  isSending: boolean;
  isLoadingSessions: boolean;
  error: string | null;
  streamingSessionIds: Set<string>;
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

export const ACTIVE_SESSION_STORAGE_KEY = "activeChatSessionId";
export const RESET_CHAT_EVENT_NAME = "reset-chat-view";
export const SESSIONS_PAGE_SIZE = 20;
export const MESSAGES_PAGE_SIZE = 50;
export const MAX_SESSION_TITLE_LENGTH = 40;

/**
 * Formats a user message content into a concise conversation title.
 */
export function formatSessionTitle(content: string, maxLength = MAX_SESSION_TITLE_LENGTH): string {
  const trimmed = content.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength)}...`;
}

/**
 * Deduplicates sessions by session ID, keeping the latest updatedAt entry.
 */
export function deduplicateSessions(sessions: ChatSession[]): ChatSession[] {
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
  return Array.from(map.values());
}

export function useChatState(): UseChatReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const activeSessionIdRef = useRef<string | null>(null);

  // In-memory cache of messages keyed by sessionId to decouple background streams from active screen
  const sessionMessagesRef = useRef<Record<string, ChatMessage[]>>({});
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Track active abort controllers per sessionId
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());

  // Track which session IDs are actively streaming in the background
  const [streamingSessionIds, setStreamingSessionIds] = useState<Set<string>>(new Set());
  const streamingSessionIdsRef = useRef<Set<string>>(new Set());

  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const [isLoadingMoreSessions, setIsLoadingMoreSessions] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [isLoadingMoreMessages, setIsLoadingMoreMessages] = useState(false);

  // isSending is true only if the currently active session is actively streaming!
  const isSending = Boolean(activeSessionId && streamingSessionIds.has(activeSessionId));

  // Initial load of chat history sidebar. Always default to fresh new chat.
  useEffect(() => {
    (async () => {
      setIsLoadingSessions(true);
      const result = await chatService.fetchSessions(SESSIONS_PAGE_SIZE, 0);
      setIsLoadingSessions(false);

      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      const rawSessions = result.data || [];
      const deduplicated = deduplicateSessions(rawSessions);
      const sorted = deduplicated.sort(
        (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
      );
      setSessions(sorted);
      setHasMoreSessions(rawSessions.length === SESSIONS_PAGE_SIZE);

      setActiveSessionId(null);
      activeSessionIdRef.current = null;
      setMessages([]);
      localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
    })();
  }, []);

  // Listen for global reset-chat-view event to switch to new chat when clicking nav icon
  useEffect(() => {
    const handleReset = () => {
      // Switch view to fresh new chat WITHOUT aborting any background streaming sessions!
      setActiveSessionId(null);
      activeSessionIdRef.current = null;
      localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
      setMessages([]);
    };
    window.addEventListener(RESET_CHAT_EVENT_NAME, handleReset);
    return () => window.removeEventListener(RESET_CHAT_EVENT_NAME, handleReset);
  }, []);

  const selectSession = useCallback(async (sessionId: string) => {
    setActiveSessionId(sessionId);
    activeSessionIdRef.current = sessionId;
    localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);

    // If we have cached messages in memory (e.g. from background stream or recent load), display immediately
    const cached = sessionMessagesRef.current[sessionId];
    if (cached) {
      setMessages(cached);
    } else {
      setMessages([]);
    }

    // If this session is NOT currently streaming, fetch messages from the server to guarantee sync
    if (!streamingSessionIdsRef.current.has(sessionId)) {
      const msgsRes = await chatService.fetchSessionMessages(sessionId, MESSAGES_PAGE_SIZE, 0);
      if (msgsRes.ok && msgsRes.data && msgsRes.data.length > 0) {
        if (!streamingSessionIdsRef.current.has(sessionId)) {
          const currentInMemory = sessionMessagesRef.current[sessionId] || [];
          if (currentInMemory.length <= msgsRes.data.length) {
            sessionMessagesRef.current[sessionId] = msgsRes.data;
            if (activeSessionIdRef.current === sessionId) {
              setMessages(msgsRes.data);
              setHasMoreMessages(msgsRes.data.length === MESSAGES_PAGE_SIZE);
            }
          }
        }
      }
    }
  }, []);

  const loadMoreSessions = useCallback(async () => {
    if (isLoadingMoreSessions || !hasMoreSessions) return;
    setIsLoadingMoreSessions(true);
    const result = await chatService.fetchSessions(SESSIONS_PAGE_SIZE, sessions.length);
    setIsLoadingMoreSessions(false);
    if (result.ok && result.data) {
      setSessions((prev) => {
        const combined = [...prev, ...result.data];
        const deduplicated = deduplicateSessions(combined);
        return deduplicated.sort(
          (a, b) => new Date(b.updatedAt || 0).getTime() - new Date(a.updatedAt || 0).getTime()
        );
      });
      setHasMoreSessions(result.data.length === SESSIONS_PAGE_SIZE);
    }
  }, [isLoadingMoreSessions, hasMoreSessions, sessions.length]);

  const loadMoreMessages = useCallback(async () => {
    if (isLoadingMoreMessages || !hasMoreMessages || !activeSessionId) return;
    setIsLoadingMoreMessages(true);
    const msgsRes = await chatService.fetchSessionMessages(activeSessionId, MESSAGES_PAGE_SIZE, messages.length);
    setIsLoadingMoreMessages(false);
    if (msgsRes.ok && msgsRes.data) {
      const combined = [...msgsRes.data, ...messages];
      sessionMessagesRef.current[activeSessionId] = combined;
      setMessages(combined);
      setHasMoreMessages(msgsRes.data.length === MESSAGES_PAGE_SIZE);
    }
  }, [isLoadingMoreMessages, hasMoreMessages, activeSessionId, messages]);

  const startNewSession = useCallback(() => {
    // Switch to new chat without aborting background streams!
    setActiveSessionId(null);
    activeSessionIdRef.current = null;
    localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
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
      // Abort stream if this session was generating
      const controller = abortControllersRef.current.get(sessionId);
      if (controller) {
        controller.abort();
        abortControllersRef.current.delete(sessionId);
      }
      streamingSessionIdsRef.current.delete(sessionId);
      setStreamingSessionIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
      delete sessionMessagesRef.current[sessionId];

      let nextIdToLoad: string | null = null;
      setSessions((prev) => {
        const updated = prev.filter((s) => s.id !== sessionId);
        if (activeSessionIdRef.current === sessionId) {
          const next = updated[0];
          setActiveSessionId(next?.id ?? null);
          activeSessionIdRef.current = next?.id ?? null;
          if (next?.id) {
            localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, next.id);
            nextIdToLoad = next.id;
          } else {
            localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
            setMessages([]);
          }
        }
        return updated;
      });
      
      if (nextIdToLoad) {
        selectSession(nextIdToLoad);
      }
      
      await chatService.deleteSession(sessionId);
    },
    [selectSession]
  );

  // Abort only the stream for the currently active session
  const abortStream = useCallback(() => {
    const currentId = activeSessionIdRef.current;
    if (!currentId) return;
    const controller = abortControllersRef.current.get(currentId);
    if (controller) {
      controller.abort();
      abortControllersRef.current.delete(currentId);
      streamingSessionIdsRef.current.delete(currentId);
      setStreamingSessionIds((prev) => {
        const next = new Set(prev);
        next.delete(currentId);
        return next;
      });
    }
  }, []);

  const sendMessage = useCallback(
    async (
      content: string, 
      bypassCache: boolean = false, 
      replaceMessageIds?: { userMsgId?: string; assistantMsgId?: string }
    ) => {
      if (!content.trim()) return;

      const isNewSession = !activeSessionIdRef.current;
      const targetSessionId = activeSessionIdRef.current || generateUUID();

      // Avoid double sending on the same session
      if (streamingSessionIdsRef.current.has(targetSessionId)) return;

      setError(null);

      // Register session as streaming in background
      streamingSessionIdsRef.current.add(targetSessionId);
      setStreamingSessionIds((prev) => new Set(prev).add(targetSessionId));

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

      // Retrieve existing messages for this session
      let existingMessages = sessionMessagesRef.current[targetSessionId] || (activeSessionIdRef.current === targetSessionId ? messages : []);
      if (replaceMessageIds?.userMsgId || replaceMessageIds?.assistantMsgId) {
        existingMessages = existingMessages.filter(
          (m) => m.id !== replaceMessageIds.userMsgId && m.id !== replaceMessageIds.assistantMsgId
        );
      } else if (bypassCache) {
        existingMessages = existingMessages.length >= 2 ? existingMessages.slice(0, existingMessages.length - 2) : [];
      }

      const newMessagesList = [...existingMessages, optimisticUserMessage, pendingAssistantMessage];
      sessionMessagesRef.current[targetSessionId] = newMessagesList;

      if (isNewSession) {
        setActiveSessionId(targetSessionId);
        activeSessionIdRef.current = targetSessionId;
        localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, targetSessionId);

        const newSession: ChatSession = {
          id: targetSessionId,
          title: formatSessionTitle(content),
          updatedAt: new Date().toISOString(),
          messages: [optimisticUserMessage],
        };
        setSessions((prev) => deduplicateSessions([newSession, ...prev]));
      } else {
        setSessions((prev) => {
          const target = prev.find((s) => s.id === targetSessionId);
          if (!target) return prev;
          const updated: ChatSession = {
            ...target,
            updatedAt: new Date().toISOString(),
            messages: [...existingMessages, optimisticUserMessage],
          };
          return deduplicateSessions([updated, ...prev.filter((s) => s.id !== targetSessionId)]);
        });
      }

      // If user is currently viewing targetSessionId, update UI messages
      if (activeSessionIdRef.current === targetSessionId) {
        setMessages(newMessagesList);
      }

      const newAbortController = new AbortController();
      abortControllersRef.current.set(targetSessionId, newAbortController);

      const idsToDelete = [replaceMessageIds?.userMsgId, replaceMessageIds?.assistantMsgId].filter(
        (id): id is string => Boolean(id)
      );

      try {
        await chatService.sendMessageStream(
          {
            sessionId: targetSessionId,
            content,
            bypassCache,
            replaceMessageIds: idsToDelete.length > 0 ? idsToDelete : undefined,
          },
          {
            onMetadata: async ({ sessionId, citations, cacheStatus }) => {
              const currentList = sessionMessagesRef.current[targetSessionId] || [];
              const updatedList = currentList.map((m) =>
                m.id === pendingAssistantMessage.id ? { ...m, citations, cacheStatus } : m
              );
              sessionMessagesRef.current[targetSessionId] = updatedList;

              // Only update UI if user is actively viewing this session
              if (activeSessionIdRef.current === targetSessionId) {
                setMessages(updatedList);
              }
            },
            onDelta: (chunkText) => {
              const currentList = sessionMessagesRef.current[targetSessionId] || [];
              const updatedList = currentList.map((m) =>
                m.id === pendingAssistantMessage.id ? { ...m, content: m.content + chunkText } : m
              );
              sessionMessagesRef.current[targetSessionId] = updatedList;

              // Stream delta directly to UI if user is viewing this session
              if (activeSessionIdRef.current === targetSessionId) {
                setMessages(updatedList);
              }
            },
            onDone: async () => {
              abortControllersRef.current.delete(targetSessionId);
              streamingSessionIdsRef.current.delete(targetSessionId);
              setStreamingSessionIds((prev) => {
                const next = new Set(prev);
                next.delete(targetSessionId);
                return next;
              });

              const currentList = sessionMessagesRef.current[targetSessionId] || [];
              const updatedList = currentList.map((m) =>
                m.id === pendingAssistantMessage.id ? { ...m, status: "complete" as const } : m
              );
              sessionMessagesRef.current[targetSessionId] = updatedList;

              if (activeSessionIdRef.current === targetSessionId) {
                setMessages(updatedList);
              }

              // Update sidebar updatedAt timestamp
              setSessions((prev) => {
                const target = prev.find((s) => s.id === targetSessionId);
                if (!target) return prev;
                const filtered = prev.filter((s) => s.id !== targetSessionId);
                return deduplicateSessions([{ ...target, updatedAt: new Date().toISOString() }, ...filtered]);
              });
            },
            onError: (errMsg) => {
              abortControllersRef.current.delete(targetSessionId);
              streamingSessionIdsRef.current.delete(targetSessionId);
              setStreamingSessionIds((prev) => {
                const next = new Set(prev);
                next.delete(targetSessionId);
                return next;
              });

              const currentList = sessionMessagesRef.current[targetSessionId] || [];
              const updatedList = currentList.map((m) =>
                m.id === pendingAssistantMessage.id
                  ? { ...m, content: m.content || `⚠️ ${errMsg}`, status: "complete" as const }
                  : m
              );
              sessionMessagesRef.current[targetSessionId] = updatedList;

              if (activeSessionIdRef.current === targetSessionId) {
                setError(errMsg);
                setMessages(updatedList);
              }
            },
          },
          newAbortController.signal
        );
      } catch (err: any) {
        // Errors handled in onError callback
      }
    },
    [messages]
  );

  return {
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
  };
}

export const ChatContext = createContext<UseChatReturn | null>(null);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const chat = useChatState();
  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
};

export function useChatContext(): UseChatReturn | null {
  return useContext(ChatContext);
}

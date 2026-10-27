import { useContext } from "react";
import {
  ChatContext,
  useChatState,
  UseChatReturn,
  ACTIVE_SESSION_STORAGE_KEY,
  RESET_CHAT_EVENT_NAME,
  SESSIONS_PAGE_SIZE,
  MESSAGES_PAGE_SIZE,
  MAX_SESSION_TITLE_LENGTH,
  formatSessionTitle,
  deduplicateSessions,
  ChatProvider,
  useChatContext,
} from "../context/ChatContext";

export type { UseChatReturn };
export {
  ChatProvider,
  useChatContext,
  useChatState,
  ACTIVE_SESSION_STORAGE_KEY,
  RESET_CHAT_EVENT_NAME,
  SESSIONS_PAGE_SIZE,
  MESSAGES_PAGE_SIZE,
  MAX_SESSION_TITLE_LENGTH,
  formatSessionTitle,
  deduplicateSessions,
};

/**
 * Hook to access the chat state.
 * If inside a ChatProvider, uses the shared persistent state across the entire app.
 * If used outside a ChatProvider (e.g. in tests), falls back to a local useChatState instance.
 */
export function useChat(): UseChatReturn {
  const context = useContext(ChatContext);
  if (context) {
    return context;
  }
  // Fallback for isolated unit tests or components rendered outside provider
  // eslint-disable-next-line react-hooks/rules-of-hooks
  return useChatState();
}

import type {
  ApiResult,
  ChatMessage,
  ChatSession,
  SendMessagePayload,
  SendMessageResponse,
} from "../types";
import { MOCK_CHAT_SESSIONS } from "../mock/mockData";
import { getToken } from "./authService";
import { delay, generateId } from "./utils";

const getApiUrl = (endpoint: string): string => {
  const env = (import.meta as any).env || {};
  const base = (env.VITE_API_BASE_URL !== undefined ? env.VITE_API_BASE_URL : "").replace(/\/+$/, "");
  if (!base) return endpoint;
  if (base.endsWith("/api") && endpoint.startsWith("/api/")) {
    return `${base}${endpoint.slice(4)}`;
  }
  return `${base}${endpoint}`;
};

// In-memory store standing in for a DB table during frontend-only development.
let sessionsStore: ChatSession[] = JSON.parse(JSON.stringify(MOCK_CHAT_SESSIONS));

function getAuthHeaders(): Record<string, string> {
  const token = getToken() || localStorage.getItem("token") || localStorage.getItem("auth_token") || "mock_dev_test_token_2026";
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

export async function fetchSessions(): Promise<ApiResult<ChatSession[]>> {
  try {
    const res = await fetch(getApiUrl("/api/chat/sessions"), {
      headers: getAuthHeaders()
    });
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const result: ApiResult<ChatSession[]> = await res.json();
      if (result.ok && Array.isArray(result.data)) {
        sessionsStore = result.data;
        return result;
      }
    }
  } catch (err) {
    // Fallback to local store if DB is unreachable
  }
  return { ok: true, data: sessionsStore };
}

export async function fetchSession(sessionId: string): Promise<ApiResult<ChatSession>> {
  const session = sessionsStore.find((s) => s.id === sessionId);
  if (!session) return { ok: false, error: { message: "Không tìm thấy hội thoại." } };
  return { ok: true, data: session };
}

export async function renameSession(sessionId: string, title: string): Promise<ApiResult<{ sessionId: string; title: string }>> {
  try {
    const res = await fetch(getApiUrl(`/api/chat/sessions/${sessionId}`), {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });
    const result = await res.json();
    return result;
  } catch (err: any) {
    return { ok: false, error: { message: err?.message || "Không thể đổi tên cuộc trò chuyện." } };
  }
}

export async function deleteSession(sessionId: string): Promise<ApiResult<{ sessionId: string; deleted: boolean }>> {
  try {
    const res = await fetch(getApiUrl(`/api/chat/sessions/${sessionId}`), {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    const result = await res.json();
    return result;
  } catch (err: any) {
    return { ok: false, error: { message: err?.message || "Không thể xóa cuộc trò chuyện." } };
  }
}

/**
 * CONTRACT NOTE FOR BACKEND INTEGRATION
 * ---------------------------------------------------------------------------
 * The real FastAPI endpoint (e.g. POST /api/chat/messages) is expected to
 * return a RAG pipeline result shaped exactly like SendMessageResponse:
 *   {
 *     sessionId: string,
 *     message: {
 *       id, role: "assistant",
 *       original_answer: string,   // raw LLM output before citation formatting
 *       content: string,           // final rendered answer (markdown)
 *       citations: [{ id, sourceTitle, pageOrSection, snippet?, url? }],
 *       createdAt, status: "complete"
 *     }
 *   }
 * UI components only ever read this shape, so swapping this function's body
 * for a real `fetch` call requires no changes elsewhere.
 * ---------------------------------------------------------------------------
 */

export async function sendMessage(
  payload: SendMessagePayload
): Promise<ApiResult<SendMessageResponse>> {
  let session = sessionsStore.find((s) => s.id === payload.sessionId);
  const sessionId = payload.sessionId ?? generateId("s");

  if (!session) {
    session = {
      id: sessionId,
      title: payload.content.slice(0, 40),
      updatedAt: new Date().toISOString(),
      messages: [],
    };
    sessionsStore = [session, ...sessionsStore];
  }

  const userMessage: ChatMessage = {
    id: generateId("m"),
    role: "user",
    content: payload.content,
    createdAt: new Date().toISOString(),
    status: "complete",
  };
  session.messages.push(userMessage);

  try {
    const res = await fetch(getApiUrl("/api/chat/messages"), {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        sessionId: payload.sessionId,
        content: payload.content,
      }),
    });

    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return {
        ok: false,
        error: { message: `Lỗi máy chủ (${res.status}): Không thể kết nối Backend API.` },
      };
    }

    const result: ApiResult<SendMessageResponse> = await res.json();
    if (result.ok && result.data) {
      session.messages.push(result.data.message);
      session.updatedAt = new Date().toISOString();
      return {
        ok: true,
        data: {
          sessionId: result.data.sessionId || sessionId,
          message: result.data.message,
        },
      };
    } else {
      return result;
    }
  } catch (err: any) {
    return {
      ok: false,
      error: { message: err.message || "Lỗi kết nối tới Server Backend." },
    };
  }
}

export interface StreamCallbacks {
  onMetadata?: (data: { sessionId: string; citations: any[] }) => void;
  onDelta?: (text: string) => void;
  onDone?: () => void;
  onError?: (error: string) => void;
}

export async function sendMessageStream(
  payload: SendMessagePayload,
  callbacks: StreamCallbacks
): Promise<void> {
  const url = getApiUrl("/api/chat/messages/stream");
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
      callbacks.onError?.(`Lỗi máy chủ (${response.status}): Không thể kết nối Real-time Stream.`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          const jsonStr = trimmed.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === "metadata") {
              callbacks.onMetadata?.({
                sessionId: data.sessionId,
                citations: data.citations || [],
              });
            } else if (data.type === "delta" && data.text) {
              callbacks.onDelta?.(data.text);
            } else if (data.type === "done") {
              callbacks.onDone?.();
            } else if (data.type === "error") {
              callbacks.onError?.(data.message || "Lỗi khi stream dữ liệu.");
            }
          } catch (e) {
            // Ignore parse errors for chunk boundaries
          }
        }
      }
    }
  } catch (err: any) {
    callbacks.onError?.(err?.message || "Không thể kết nối đến máy chủ.");
  }
}

export async function submitFeedback(messageId: string, payload: { feedback: 'like' | 'dislike' | null; comment?: string }): Promise<ApiResult<any>> {
  try {
    const res = await fetch(getApiUrl(`/api/chat/messages/${messageId}/feedback`), {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    return result;
  } catch (err: any) {
    return { ok: false, error: { message: err?.message || "Không thể gửi phản hồi." } };
  }
}


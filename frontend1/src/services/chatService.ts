import type {
  ApiResult,
  ChatMessage,
  ChatSession,
  SendMessagePayload,
  SendMessageResponse,
} from "../types";
import { MOCK_CHAT_SESSIONS } from "../mock/mockData";
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

export async function fetchSessions(): Promise<ApiResult<ChatSession[]>> {
  try {
    const res = await fetch(getApiUrl("/api/chat/sessions"));
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const result: ApiResult<ChatSession[]> = await res.json();
      if (result.ok && result.data && result.data.length > 0) {
        sessionsStore = result.data;
        return result;
      }
    }
  } catch (err) {
    // Fallback to local store if DB is empty or unreachable
  }
  return { ok: true, data: sessionsStore };
}

export async function fetchSession(sessionId: string): Promise<ApiResult<ChatSession>> {
  const session = sessionsStore.find((s) => s.id === sessionId);
  if (!session) return { ok: false, error: { message: "Không tìm thấy hội thoại." } };
  return { ok: true, data: session };
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
      headers: { "Content-Type": "application/json" },
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


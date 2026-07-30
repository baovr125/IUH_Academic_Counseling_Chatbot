import type {
  ApiResult,
  ChatMessage,
  ChatSession,
  SendMessagePayload,
  SendMessageResponse,
} from "../types";
import { MOCK_CHAT_SESSIONS } from "../mock/mockData";
import { delay, generateId } from "./utils";

// In-memory store standing in for a DB table during frontend-only development.
let sessionsStore: ChatSession[] = JSON.parse(JSON.stringify(MOCK_CHAT_SESSIONS));

export async function fetchSessions(): Promise<ApiResult<ChatSession[]>> {
  await delay(600);
  return { ok: true, data: sessionsStore };
}

export async function fetchSession(sessionId: string): Promise<ApiResult<ChatSession>> {
  await delay(400);
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
  await delay(1800); // simulate RAG retrieval + generation latency

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

  const rawAnswer =
    "Based on the retrieved documents, here is a summary that addresses the question directly, drawing only on verified university sources.";

  const assistantMessage: ChatMessage = {
    id: generateId("m"),
    role: "assistant",
    original_answer: rawAnswer,
    content: `Here's what I found:\n\n${rawAnswer}\n\nLet me know if you'd like more detail on any part.`,
    citations: [
      { id: generateId("c"), sourceTitle: "Sổ tay sinh viên", pageOrSection: "trang 15" },
      { id: generateId("c"), sourceTitle: "Quy chế đào tạo IUH 2024", pageOrSection: "Điều 12" },
    ],
    createdAt: new Date().toISOString(),
    status: "complete",
  };

  session.messages.push(userMessage, assistantMessage);
  session.updatedAt = new Date().toISOString();

  return { ok: true, data: { sessionId: session.id, message: assistantMessage } };
}

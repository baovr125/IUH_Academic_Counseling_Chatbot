import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChat } from '../src/hooks/useChat';
import * as chatService from '../src/services/chatService';

vi.mock('../src/services/chatService', () => ({
  fetchSessions: vi.fn(),
  fetchSessionMessages: vi.fn(),
  sendMessageStream: vi.fn(),
  renameSession: vi.fn(),
  deleteSession: vi.fn(),
}));

describe('useChat hook - Session management, Deduplication & Background Streaming', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    (chatService.fetchSessions as any).mockResolvedValue({
      ok: true,
      data: [
        {
          id: '11111111-1111-4111-8111-111111111111',
          title: 'Hội thoại ban đầu',
          updatedAt: '2026-10-27T10:00:00.000Z',
          messages: [],
        },
      ],
    });
    (chatService.fetchSessionMessages as any).mockImplementation((sessionId: string) => {
      if (sessionId === '11111111-1111-4111-8111-111111111111') {
        return Promise.resolve({
          ok: true,
          data: [
            {
              id: 'msg-existing-1',
              role: 'user',
              content: 'Tin nhắn cũ',
              createdAt: '2026-10-27T10:00:00.000Z',
              status: 'complete',
            },
          ],
        });
      }
      return Promise.resolve({ ok: true, data: [] });
    });
  });

  it('generates a valid UUID and does not create duplicate entries during sendMessage', async () => {
    let capturedCallbacks: any;
    (chatService.sendMessageStream as any).mockImplementation((_payload: any, callbacks: any) => {
      capturedCallbacks = callbacks;
      return Promise.resolve();
    });

    const { result } = renderHook(() => useChat());

    // Wait for initial sessions load
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.sessions.length).toBe(1);

    // Send a message in a new session
    await act(async () => {
      await result.current.sendMessage('Câu hỏi test');
    });

    // Should have added the new session optimistically (total 2 sessions)
    expect(result.current.sessions.length).toBe(2);
    const newSession = result.current.sessions[0];
    expect(newSession.title).toContain('Câu hỏi test');
    // Ensure the ID is a valid RFC4122 UUIDv4
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(uuidRegex.test(newSession.id)).toBe(true);

    // Simulate backend sending metadata with the same UUID
    await act(async () => {
      capturedCallbacks?.onMetadata({
        sessionId: newSession.id,
        citations: [],
      });
    });

    // Still exactly 2 sessions, no duplicate created!
    expect(result.current.sessions.length).toBe(2);

    // Simulate backend done
    await act(async () => {
      capturedCallbacks?.onDone();
    });

    // Still exactly 2 sessions!
    expect(result.current.sessions.length).toBe(2);
  });

  it('keeps LLM call streaming in background when switching sessions and recovers answer upon return', async () => {
    let capturedCallbacks: any;
    let streamSignal: AbortSignal | undefined;

    (chatService.sendMessageStream as any).mockImplementation((_payload: any, callbacks: any, signal: AbortSignal) => {
      capturedCallbacks = callbacks;
      streamSignal = signal;
      return new Promise(() => {}); // Keep stream open in background
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await Promise.resolve();
    });

    // Start streaming message in Session A (new session)
    await act(async () => {
      result.current.sendMessage('Câu hỏi session A');
    });

    const sessionAId = result.current.activeSessionId!;
    expect(result.current.isSending).toBe(true);
    expect(streamSignal?.aborted).toBe(false);

    // Stream receives initial chunk
    act(() => {
      capturedCallbacks?.onDelta('Đây là câu trả lời ');
    });

    expect(result.current.messages[1].content).toBe('Đây là câu trả lời ');

    // User switches to Session B while Session A is STILL streaming
    await act(async () => {
      await result.current.selectSession('11111111-1111-4111-8111-111111111111');
    });

    // IMPORTANT: Stream MUST NOT be aborted! It must continue running in the background!
    expect(streamSignal?.aborted).toBe(false);

    // The active view is now Session B, not Session A
    expect(result.current.activeSessionId).toBe('11111111-1111-4111-8111-111111111111');
    expect(result.current.isSending).toBe(false); // Session B is not sending

    // Session A continues receiving chunks in the background!
    act(() => {
      capturedCallbacks?.onDelta('được tạo trong nền.');
      capturedCallbacks?.onDone();
    });

    // While on Session B, Session B's messages are NOT polluted
    expect(result.current.messages[0].content).toBe('Tin nhắn cũ');

    // User switches back to Session A
    await act(async () => {
      await result.current.selectSession(sessionAId);
    });

    // The answer in Session A has the full background generated text!
    expect(result.current.activeSessionId).toBe(sessionAId);
    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[1].content).toBe('Đây là câu trả lời được tạo trong nền.');
    expect(result.current.messages[1].status).toBe('complete');
  });

  it('aborts only when user explicitly calls abortStream', async () => {
    let streamSignal: AbortSignal | undefined;
    (chatService.sendMessageStream as any).mockImplementation((_payload: any, _callbacks: any, signal: AbortSignal) => {
      streamSignal = signal;
      return new Promise(() => {}); // Keep stream hanging
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await Promise.resolve();
    });

    act(() => {
      result.current.sendMessage('Câu hỏi cần dừng');
    });

    expect(result.current.isSending).toBe(true);
    expect(streamSignal?.aborted).toBe(false);

    // Explicit user abort
    act(() => {
      result.current.abortStream();
    });

    expect(streamSignal?.aborted).toBe(true);
    expect(result.current.isSending).toBe(false);
  });
});

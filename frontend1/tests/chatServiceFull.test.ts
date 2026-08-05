import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  sendMessage,
  sendMessageStream,
  fetchSessions,
  renameSession,
  deleteSession,
  submitFeedback,
} from '../src/services/chatService';
import * as authService from '../src/services/authService';

// Mock global fetch
global.fetch = vi.fn();

// Mock authService
vi.mock('../src/services/authService', () => ({
  getToken: vi.fn(),
}));

// Mock utils (generateId used internally)
vi.mock('../src/services/utils', () => ({
  delay: vi.fn(),
  generateId: vi.fn((prefix: string) => `${prefix}_mock123`),
}));

describe('chatService — API integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (authService.getToken as any).mockReturnValue('jwt-token-test');
  });

  // ─── Auth Headers ──────────────────────────────────────────

  describe('Auth Headers', () => {
    it('sendMessage includes Bearer token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({
          ok: true,
          data: {
            sessionId: 's1',
            message: {
              id: 'm1', role: 'assistant', content: 'Hi',
              createdAt: new Date().toISOString(), status: 'complete',
            }
          }
        }),
      });

      await sendMessage({ content: 'Hello', sessionId: 'test-session' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });

    it('fetchSessions includes Bearer token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ ok: true, data: [] }),
      });

      await fetchSessions();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/sessions'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });

    it('renameSession includes Bearer token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true }),
      });

      await renameSession('s1', 'New Title');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/sessions/s1'),
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });

    it('deleteSession includes Bearer token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true }),
      });

      await deleteSession('s1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/sessions/s1'),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });

    it('submitFeedback includes Bearer token', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true }),
      });

      await submitFeedback('msg1', { feedback: 'like' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/messages/msg1/feedback'),
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });
  });

  // ─── sendMessage ───────────────────────────────────────────

  describe('sendMessage', () => {
    it('returns success with session and message data', async () => {
      const mockMessage = {
        id: 'm_resp', role: 'assistant', content: 'Xin chào!',
        createdAt: '2026-08-05T10:00:00Z', status: 'complete',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({
          ok: true,
          data: { sessionId: 'sess-1', message: mockMessage },
        }),
      });

      const result = await sendMessage({ content: 'Xin chào', sessionId: 'sess-1' });
      expect(result.ok).toBe(true);
      expect(result.data?.sessionId).toBe('sess-1');
      expect(result.data?.message.content).toBe('Xin chào!');
    });

    it('handles non-JSON response gracefully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        headers: { get: () => 'text/html' },
      });

      const result = await sendMessage({ content: 'Test' });
      expect(result.ok).toBe(false);
      expect(result.error?.message).toContain('500');
    });

    it('handles network error gracefully', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await sendMessage({ content: 'Test' });
      expect(result.ok).toBe(false);
      expect(result.error?.message).toContain('Network error');
    });
  });

  // ─── sendMessageStream ────────────────────────────────────

  describe('sendMessageStream', () => {
    it('includes Bearer token in stream request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: vi.fn() },
      });

      try {
        await sendMessageStream({ content: 'Stream test', sessionId: 's1' }, { onError: vi.fn() });
      } catch (e) { /* reader mock throws */ }

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat/messages/stream'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer jwt-token-test',
          }),
        })
      );
    });

    it('calls onError for non-ok response', async () => {
      const onError = vi.fn();
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 503,
        body: null,
      });

      await sendMessageStream({ content: 'Test' }, { onError });
      expect(onError).toHaveBeenCalledWith(expect.stringContaining('503'));
    });

    it('calls onError for AbortError', async () => {
      const onError = vi.fn();
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      (global.fetch as any).mockRejectedValueOnce(abortError);

      await sendMessageStream({ content: 'Test' }, { onError });
      expect(onError).toHaveBeenCalledWith(expect.stringContaining('hủy'));
    });

    it('parses SSE metadata event', async () => {
      const onMetadata = vi.fn();
      const onDelta = vi.fn();
      const onDone = vi.fn();

      const ssePayload =
        'data: {"type":"metadata","sessionId":"s1","citations":[{"id":"c1","sourceTitle":"Test"}]}\n\n' +
        'data: {"type":"delta","text":"Xin "}\n\n' +
        'data: {"type":"delta","text":"chào!"}\n\n' +
        'data: {"type":"done"}\n\n';

      const encoder = new TextEncoder();
      const chunks = [encoder.encode(ssePayload)];
      let readIndex = 0;

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => {
              if (readIndex < chunks.length) {
                return { done: false, value: chunks[readIndex++] };
              }
              return { done: true, value: undefined };
            },
          }),
        },
      });

      await sendMessageStream({ content: 'Hello', sessionId: 's1' }, {
        onMetadata,
        onDelta,
        onDone,
      });

      expect(onMetadata).toHaveBeenCalledWith(
        expect.objectContaining({ sessionId: 's1' })
      );
      expect(onDelta).toHaveBeenCalledWith('Xin ');
      expect(onDelta).toHaveBeenCalledWith('chào!');
      expect(onDone).toHaveBeenCalledTimes(1);
    });
  });
});

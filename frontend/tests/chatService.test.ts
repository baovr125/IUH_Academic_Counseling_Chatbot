import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sendMessage, sendMessageStream } from '../src/services/chatService';
import * as authService from '../src/services/authService';

// Mock globalThis.fetch
globalThis.fetch = vi.fn();

// Mock authService to control the token returned
vi.mock('../src/services/authService', () => ({
  getToken: vi.fn()
}));

describe('chatService (Test Case 0.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Set a mock token for all tests
    (authService.getToken as any).mockReturnValue('mock-jwt-token-123');
  });

  it('T0.2: sendMessage includes Authorization header', async () => {
    (globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ answer: 'Mock response' })
    });

    await sendMessage({ content: 'Hello API', sessionId: 'session-123' });

    // Verify fetch was called with the correct Authorization header
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer mock-jwt-token-123',
        })
      })
    );
  });

  it('T0.2: sendMessageStream includes Authorization header', async () => {
    (globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      body: { getReader: vi.fn() }
    });

    try {
      await sendMessageStream({ content: 'Hello Stream API', sessionId: 'session-123' }, { onError: vi.fn() });
    } catch (e) {
      // Ignore reader setup errors since we mocked it simply
    }

    // Verify fetch was called with the correct Authorization header
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer mock-jwt-token-123',
        })
      })
    );
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatHistoryPanel } from '../src/components/chat/ChatHistoryPanel';
import type { ChatSession } from '../src/types';

vi.mock('../src/context/SettingsContext', () => ({
  useSettings: () => ({ language: 'vi', t: (k: string) => k }),
}));

describe('ChatHistoryPanel - Deduplication & Sorting', () => {
  const dummyHandlers = {
    onSelectSession: vi.fn(),
    onNewChat: vi.fn(),
    onRenameSession: vi.fn(),
    onDeleteSession: vi.fn(),
    onLoadMoreSessions: vi.fn(),
  };

  it('deduplicates sessions with the exact same ID and renders only one entry', () => {
    const duplicateSessions: ChatSession[] = [
      {
        id: 'session-uuid-1',
        title: 'Học bổng khuyến khích',
        updatedAt: '2026-10-27T10:00:00.000Z',
        messages: [],
      },
      {
        id: 'session-uuid-1',
        title: 'Học bổng khuyến khích (updated)',
        updatedAt: '2026-10-27T10:05:00.000Z',
        messages: [],
      },
    ];

    render(
      <ChatHistoryPanel
        sessions={duplicateSessions}
        activeSessionId="session-uuid-1"
        isLoading={false}
        hasMoreSessions={false}
        isLoadingMoreSessions={false}
        {...dummyHandlers}
      />
    );

    // There should be only 1 session title rendered in the panel
    const items = screen.getAllByText(/Học bổng khuyến khích/);
    expect(items.length).toBe(1);
    expect(items[0]).toHaveTextContent('Học bổng khuyến khích (updated)');
  });

  it('sorts sessions descending by updatedAt', () => {
    const sessions: ChatSession[] = [
      {
        id: 'session-1',
        title: 'Session 1 Older',
        updatedAt: '2026-10-26T08:00:00.000Z',
        messages: [],
      },
      {
        id: 'session-2',
        title: 'Session 2 Newer',
        updatedAt: '2026-10-27T12:00:00.000Z',
        messages: [],
      },
    ];

    render(
      <ChatHistoryPanel
        sessions={sessions}
        activeSessionId="session-2"
        isLoading={false}
        hasMoreSessions={false}
        isLoadingMoreSessions={false}
        {...dummyHandlers}
      />
    );

    const titles = screen.getAllByText(/Session/);
    expect(titles.length).toBe(2);
    expect(titles[0]).toHaveTextContent('Session 2 Newer');
    expect(titles[1]).toHaveTextContent('Session 1 Older');
  });
});

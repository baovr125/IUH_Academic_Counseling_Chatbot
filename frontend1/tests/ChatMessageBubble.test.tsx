import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatMessageBubble } from '../src/components/chat/ChatMessageBubble';
import '@testing-library/jest-dom/vitest';

// Mock FormattedMarkdown since it's a separate component
vi.mock('../src/components/chat/FormattedMarkdown', () => {
  return {
    FormattedMarkdown: function DummyFormattedMarkdown({ content }: { content: string }) {
      return <div data-testid="markdown">{content}</div>;
    }
  };
});

// Mock lucide-react to avoid issues with SVGs
vi.mock('lucide-react', () => ({
  Bot: () => <div data-testid="bot-icon" />,
  ThumbsUp: () => <div data-testid="thumbs-up-icon" />,
  ThumbsDown: () => <div data-testid="thumbs-down-icon" />,
  MessageSquare: () => <div data-testid="message-square-icon" />,
  BookMarked: () => <div data-testid="bookmarked-icon" />
}));

describe('ChatMessageBubble (Test Case 0.1)', () => {
  it('T0.1: renders typing indicator when status is pending and no content exists', () => {
    const message = { id: '1', role: 'assistant' as const, content: '', status: 'pending' as const };
    const { container, queryByTestId } = render(<ChatMessageBubble message={message} />);
    
    // Typing indicator should be visible (3 bouncing dots)
    const dots = container.querySelectorAll('.animate-bounce');
    expect(dots.length).toBe(3);
    
    // Content should NOT be rendered
    expect(queryByTestId('markdown')).not.toBeInTheDocument();
  });

  it('T0.1: renders content progressively and shows pulsing cursor when status is pending but content exists', () => {
    const message = { id: '2', role: 'assistant' as const, content: 'Đang giải thích', status: 'pending' as const };
    const { getByTestId, container } = render(<ChatMessageBubble message={message} />);
    
    // Typing indicator should disappear
    const dots = container.querySelectorAll('.animate-bounce');
    expect(dots.length).toBe(0);
    
    // Content should be rendered
    expect(getByTestId('markdown')).toHaveTextContent('Đang giải thích');
    
    // Check for blinking cursor (the span with animate-pulse class)
    const cursor = container.querySelector('.animate-pulse');
    expect(cursor).toBeInTheDocument();
  });

  it('T0.1: removes pulsing cursor when status is complete', () => {
    const message = { id: '3', role: 'assistant' as const, content: 'Đã giải thích xong', status: 'complete' as const };
    const { getByTestId, container } = render(<ChatMessageBubble message={message} />);
    
    // Content should be rendered
    expect(getByTestId('markdown')).toHaveTextContent('Đã giải thích xong');
    
    // Blinking cursor should be removed
    const cursor = container.querySelector('.animate-pulse');
    expect(cursor).not.toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatComposer } from '../src/components/chat/ChatComposer';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Send: () => <div data-testid="send-icon" />,
  Square: () => <div data-testid="square-icon" />,
}));

describe('ChatComposer', () => {
  const mockOnSend = vi.fn();
  const PLACEHOLDER = 'Hỏi Chatbot bất cứ thứ gì liên quan đến học tập...';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders textarea input field with correct placeholder', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    expect(input).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const sendButton = screen.getByTestId('send-icon').closest('button');
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when content is typed', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    fireEvent.change(input, { target: { value: 'Xin chào' } });

    const sendButton = screen.getByTestId('send-icon').closest('button');
    expect(sendButton).not.toBeDisabled();
  });

  it('calls onSend with trimmed content and clears input on Enter', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    fireEvent.change(input, { target: { value: '  Học phí bao nhiêu?  ' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

    expect(mockOnSend).toHaveBeenCalledWith('Học phí bao nhiêu?');
    expect(input).toHaveValue('');
  });

  it('does NOT send when only whitespace is entered', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('shows character counter', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    expect(screen.getByText('0/2000')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    fireEvent.change(input, { target: { value: 'Hello' } });

    expect(screen.getByText('5/2000')).toBeInTheDocument();
  });

  it('shows stop button when isSending is true', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={true} onAbort={vi.fn()} />);

    expect(screen.getByTestId('square-icon')).toBeInTheDocument();
    expect(screen.getByTitle('Dừng phản hồi')).toBeInTheDocument();
  });

  it('calls onAbort when stop button is clicked', () => {
    const mockAbort = vi.fn();
    render(<ChatComposer onSend={mockOnSend} isSending={true} onAbort={mockAbort} />);

    fireEvent.click(screen.getByTitle('Dừng phản hồi'));
    expect(mockAbort).toHaveBeenCalledTimes(1);
  });

  it('enforces maxLength=2000 on input', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText(PLACEHOLDER);
    expect(input).toHaveAttribute('maxLength', '2000');
  });
});

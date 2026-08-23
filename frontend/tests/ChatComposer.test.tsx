import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatComposer } from '../src/components/chat/ChatComposer';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Paperclip: () => <div data-testid="paperclip-icon" />,
  Send: () => <div data-testid="send-icon" />,
  Square: () => <div data-testid="square-icon" />,
}));

describe('ChatComposer', () => {
  const mockOnSend = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders input field and quick action buttons', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    expect(input).toBeInTheDocument();

    expect(screen.getByText(/Giới thiệu về trường/i)).toBeInTheDocument();
    expect(screen.getByText(/Tìm kiếm biểu mẫu/i)).toBeInTheDocument();
    expect(screen.getByText(/Viết email xin phép/i)).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const sendButton = screen.getByTestId('send-icon').closest('button');
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when content is typed', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    fireEvent.change(input, { target: { value: 'Xin chào' } });

    const sendButton = screen.getByTestId('send-icon').closest('button');
    expect(sendButton).not.toBeDisabled();
  });

  it('calls onSend with trimmed content and clears input', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    fireEvent.change(input, { target: { value: '  Học phí bao nhiêu?  ' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockOnSend).toHaveBeenCalledWith('Học phí bao nhiêu?');
    expect(input).toHaveValue('');
  });

  it('does NOT send when only whitespace is entered', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('shows character counter', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    expect(screen.getByText('0/2000')).toBeInTheDocument();

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    fireEvent.change(input, { target: { value: 'Hello' } });

    expect(screen.getByText('5/2000')).toBeInTheDocument();
  });

  it('shows stop button when isSending is true', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={true} onAbort={vi.fn()} />);

    expect(screen.getByTestId('square-icon')).toBeInTheDocument();
    expect(screen.getByTitle('Stop generating')).toBeInTheDocument();
  });

  it('calls onAbort when stop button is clicked', () => {
    const mockAbort = vi.fn();
    render(<ChatComposer onSend={mockOnSend} isSending={true} onAbort={mockAbort} />);

    fireEvent.click(screen.getByTitle('Stop generating'));
    expect(mockAbort).toHaveBeenCalledTimes(1);
  });

  it('sets input value when quick action is clicked', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    fireEvent.click(screen.getByText(/Giới thiệu về trường/i));
    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...') as HTMLInputElement;
    expect(input.value).toContain('Giới thiệu về trường');
  });

  it('enforces maxLength=2000 on input', () => {
    render(<ChatComposer onSend={mockOnSend} isSending={false} />);

    const input = screen.getByPlaceholderText('Ask the Knowledge Hub...');
    expect(input).toHaveAttribute('maxLength', '2000');
  });
});

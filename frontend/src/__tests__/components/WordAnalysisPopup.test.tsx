import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WordAnalysisPopup } from '../../components/translation/WordAnalysisPopup';

describe('WordAnalysisPopup Component', () => {
  const defaultProps = {
    position: { x: 100, y: 100 },
    isLoading: false,
    data: null,
    error: null,
    onClose: vi.fn(),
    onRetry: vi.fn(),
  };

  it('renders loading state', () => {
    render(<WordAnalysisPopup {...defaultProps} isLoading={true} />);
    expect(screen.getByText('Analyzing context...')).toBeInTheDocument();
  });

  it('renders error state and handles retry', () => {
    render(<WordAnalysisPopup {...defaultProps} error="Network Error" />);
    expect(screen.getByText('Network Error')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);
    expect(defaultProps.onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders data correctly', () => {
    const mockData = {
      word: 'book',
      lemma: 'book',
      part_of_speech: 'VERB',
      context: 'book a flight',
      cached: false,
      latency_ms: 100,
      contextual_meaning: {
        pos: 'v',
        english_definition: 'reserve',
        target_language_meaning: 'đặt chỗ',
        examples: ['book a flight'],
        target_language_examples: ['đặt chuyến bay']
      },
      other_meanings: [
        { 
          pos: 'n',
          english_definition: 'a written work',
          target_language_meaning: 'cuốn sách',
          examples: ['read a book'],
          target_language_examples: ['đọc sách']
        }
      ]
    };

    render(<WordAnalysisPopup {...defaultProps} data={mockData} />);
    
    // Check main headers
    expect(screen.getByText('book')).toBeInTheDocument();
    expect(screen.getByText('Verb')).toBeInTheDocument();
    
    // Check context match
    expect(screen.getByText('đặt chỗ')).toBeInTheDocument();
    expect(screen.getByText('"book a flight"')).toBeInTheDocument();
    
    // Check other meanings
    expect(screen.getByText('cuốn sách')).toBeInTheDocument();
    expect(screen.getByText('"read a book"')).toBeInTheDocument();
  });

  it('handles close button click', () => {
    const mockData = {
      word: 'test', lemma: 'test', part_of_speech: 'NOUN', context: 'test',
      cached: false, latency_ms: 100,
      contextual_meaning: { pos: 'n', english_definition: 'test', target_language_meaning: 'test', examples: [], target_language_examples: [] },
      other_meanings: []
    };
    render(<WordAnalysisPopup {...defaultProps} data={mockData} />);
    
    // Find the close button (first button in the DOM usually, or by accessible name if provided)
    // In our component, it's a generic button with a lucide-react X icon, let's find it by role or just generic button click
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]); // The close button
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });
});

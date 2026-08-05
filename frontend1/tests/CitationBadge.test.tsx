import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CitationBadge } from '../src/components/chat/CitationBadge';
import '@testing-library/jest-dom/vitest';

// Mock lucide-react
vi.mock('lucide-react', () => ({
  BookMarked: () => <div data-testid="bookmarked-icon" />,
}));

describe('CitationBadge', () => {
  it('renders source title', () => {
    const citation = {
      id: 'c_test1',
      sourceTitle: 'Cẩm nang Sinh viên IUH',
      pageOrSection: 'Trang 15',
      snippet: 'Đăng ký học phần tại IUH...',
      url: 'https://camnang.iuh.edu.vn',
    };

    render(<CitationBadge citation={citation} />);
    expect(screen.getByText(/Cẩm nang Sinh viên IUH/)).toBeInTheDocument();
  });

  it('renders page/section after source title', () => {
    const citation = {
      id: 'c_test2',
      sourceTitle: 'Quy chế Đào tạo',
      pageOrSection: 'Chương 3',
    };

    render(<CitationBadge citation={citation} />);
    expect(screen.getByText(/Quy chế Đào tạo/)).toBeInTheDocument();
    expect(screen.getByText(/, Chương 3/)).toBeInTheDocument();
  });

  it('omits page/section when empty', () => {
    const citation = {
      id: 'c_test3',
      sourceTitle: 'Biểu mẫu',
      pageOrSection: '',
    };

    const { container } = render(<CitationBadge citation={citation} />);
    expect(container.textContent).not.toContain(',');
  });

  it('shows snippet in title attribute when present', () => {
    const citation = {
      id: 'c_test4',
      sourceTitle: 'Test Source',
      pageOrSection: 'Section A',
      snippet: 'This is a preview snippet...',
    };

    render(<CitationBadge citation={citation} />);
    const badge = screen.getByTitle('This is a preview snippet...');
    expect(badge).toBeInTheDocument();
  });

  it('falls back to sourceTitle in title attribute when no snippet', () => {
    const citation = {
      id: 'c_test5',
      sourceTitle: 'Fallback Title',
      pageOrSection: 'Page 1',
    };

    render(<CitationBadge citation={citation} />);
    const badge = screen.getByTitle('Fallback Title');
    expect(badge).toBeInTheDocument();
  });

  it('renders BookMarked icon', () => {
    const citation = {
      id: 'c_icon',
      sourceTitle: 'Test',
      pageOrSection: 'P1',
    };

    render(<CitationBadge citation={citation} />);
    expect(screen.getByTestId('bookmarked-icon')).toBeInTheDocument();
  });
});

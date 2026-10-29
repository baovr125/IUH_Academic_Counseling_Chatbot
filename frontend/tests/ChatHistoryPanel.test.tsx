import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
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

const NOW = new Date();
const daysAgo = (d: number) => new Date(NOW.getTime() - d * 24 * 60 * 60 * 1000).toISOString();

const mkSessions = (): ChatSession[] => [
  { id: 's1', title: 'Quy chế đào tạo', updatedAt: NOW.toISOString(), messages: [] },
  { id: 's2', title: 'Học phí học kỳ', updatedAt: daysAgo(3), messages: [] },
  { id: 's3', title: 'Điều kiện tốt nghiệp', updatedAt: daysAgo(40), messages: [] },
];

const baseProps = () => ({
  sessions: mkSessions(),
  activeSessionId: 's1',
  isLoading: false,
  hasMoreSessions: false,
  isLoadingMoreSessions: false,
  onSelectSession: vi.fn(),
  onNewChat: vi.fn(),
  onRenameSession: vi.fn(),
  onDeleteSession: vi.fn(),
  onLoadMoreSessions: vi.fn(),
});

describe('ChatHistoryPanel - giao diện kiểu ChatGPT', () => {
  it('có hàng "Cuộc trò chuyện mới" gọi onNewChat', () => {
    const props = baseProps();
    render(<ChatHistoryPanel {...props} isOpen onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Cuộc trò chuyện mới/ }));
    expect(props.onNewChat).toHaveBeenCalledTimes(1);
  });

  it('mỗi cuộc trò chuyện một dòng, không hiện giờ trong danh sách (giờ nằm ở tooltip)', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={vi.fn()} />);
    expect(screen.queryByText(/\d{2}:\d{2} - \d{2}\/\d{2}\/\d{4}/)).toBeNull();
    const row = screen.getByText('Quy chế đào tạo').closest('button') as HTMLElement;
    expect(row.getAttribute('title')).toMatch(/Quy chế đào tạo — \d{2}:\d{2}/);
  });

  it('chia nhóm Hôm nay / 7 ngày trước / Cũ hơn', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={vi.fn()} />);
    expect(screen.getByText('Hôm nay')).toBeInTheDocument();
    expect(screen.getByText('7 ngày trước')).toBeInTheDocument();
    expect(screen.getByText('Cũ hơn')).toBeInTheDocument();
  });

  it('tìm kiếm không phân biệt dấu và báo khi không có kết quả', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={vi.fn()} />);
    const search = screen.getByRole('searchbox');
    fireEvent.change(search, { target: { value: 'hoc phi' } });
    expect(screen.getByText('Học phí học kỳ')).toBeInTheDocument();
    expect(screen.queryByText('Quy chế đào tạo')).toBeNull();
    fireEvent.change(search, { target: { value: 'zzz' } });
    expect(screen.getByText('Không tìm thấy cuộc trò chuyện nào')).toBeInTheDocument();
  });

  it('menu ⋯: Đổi tên gọi onRenameSession, Xóa hỏi xác nhận rồi gọi onDeleteSession', () => {
    const props = baseProps();
    render(<ChatHistoryPanel {...props} isOpen onClose={vi.fn()} />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Tùy chọn cuộc trò chuyện' })[0]);
    fireEvent.click(screen.getByRole('menuitem', { name: /Đổi tên/ }));
    const input = screen.getByRole('textbox', { name: 'Tên cuộc trò chuyện' });
    fireEvent.change(input, { target: { value: 'Tên mới' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(props.onRenameSession).toHaveBeenCalledWith('s1', 'Tên mới');

    fireEvent.click(screen.getAllByRole('button', { name: 'Tùy chọn cuộc trò chuyện' })[1]);
    fireEvent.click(screen.getByRole('menuitem', { name: /Xóa/ }));
    expect(props.onDeleteSession).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Xóa ngay' }));
    expect(props.onDeleteSession).toHaveBeenCalledWith('s2');
  });

  it('nút ⋯ luôn hiện trên thiết bị cảm ứng (không chỉ khi hover)', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={vi.fn()} />);
    const kebab = screen.getAllByRole('button', { name: 'Tùy chọn cuộc trò chuyện' })[0];
    expect(kebab.className).toContain('[@media(hover:none)]:opacity-100');
  });

  it('không còn tay kéo đổi độ rộng', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={vi.fn()} />);
    expect(screen.queryByTitle(/Kéo để đổi độ rộng/)).toBeNull();
  });
});

describe('ChatHistoryPanel - thu gọn thành thanh icon (máy tính)', () => {
  it('khi đóng hiện thanh icon: mở lại, cuộc trò chuyện mới, tìm kiếm', () => {
    const props = baseProps();
    const onOpen = vi.fn();
    render(<ChatHistoryPanel {...props} isOpen={false} onOpen={onOpen} onClose={vi.fn()} />);
    expect(screen.queryByText('Hôm nay')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Mở lịch sử trò chuyện' }));
    fireEvent.click(screen.getByRole('button', { name: 'Tìm kiếm cuộc trò chuyện' }));
    expect(onOpen).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' }));
    expect(props.onNewChat).toHaveBeenCalledTimes(1);
  });

  it('có nút thu gọn khi đang mở', () => {
    const onClose = vi.fn();
    render(<ChatHistoryPanel {...baseProps()} isOpen onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn lịch sử trò chuyện' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('đóng mà không có onOpen thì không render gì', () => {
    const { container } = render(<ChatHistoryPanel {...baseProps()} isOpen={false} onClose={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe('ChatHistoryPanel - thanh icon trần khi thu gọn', () => {
  it('thu gọn: không có thẻ/viền/bóng bao quanh; mở rộng thì có thẻ', () => {
    const { container, rerender } = render(<ChatHistoryPanel {...baseProps()} isOpen={false} onOpen={vi.fn()} onClose={vi.fn()} />);
    const frame = container.firstElementChild as HTMLElement;
    expect(frame.className).toContain('border-transparent');
    expect(frame.className).toContain('bg-transparent');
    expect(frame.className).not.toContain('shadow-sm');

    rerender(<ChatHistoryPanel {...baseProps()} isOpen onOpen={vi.fn()} onClose={vi.fn()} />);
    const open = container.firstElementChild as HTMLElement;
    expect(open.className).toContain('bg-white');
    expect(open.className).toContain('shadow-sm');
  });

  it('nút icon không có nền cố định, chỉ hiện nền khi rê chuột', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen={false} onOpen={vi.fn()} onClose={vi.fn()} />);
    const btn = screen.getByRole('button', { name: 'Mở lịch sử trò chuyện' });
    expect(btn.className).toContain('hover:bg-white');
    expect(btn.className).not.toMatch(/(^|\s)bg-/);
  });

  it('tooltip ghi đúng phím tắt Ctrl+\\ và Ctrl+Shift+O', () => {
    render(<ChatHistoryPanel {...baseProps()} isOpen={false} onOpen={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Mở lịch sử trò chuyện' }).getAttribute('title')).toContain('Ctrl+\\');
    expect(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' }).getAttribute('title')).toContain('Ctrl+Shift+O');
  });

  it('bấm icon tìm kiếm: mở lịch sử và đặt con trỏ vào ô tìm kiếm', () => {
    function Harness() {
      const [open, setOpen] = React.useState(false);
      return <ChatHistoryPanel {...baseProps()} isOpen={open} onOpen={() => setOpen(true)} onClose={() => setOpen(false)} />;
    }
    render(<Harness />);
    expect(screen.queryByRole('searchbox')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Tìm kiếm cuộc trò chuyện' }));
    expect(document.activeElement).toBe(screen.getByRole('searchbox'));
  });

  it('bấm icon mở lịch sử thì không tự focus ô tìm kiếm', () => {
    function Harness() {
      const [open, setOpen] = React.useState(false);
      return <ChatHistoryPanel {...baseProps()} isOpen={open} onOpen={() => setOpen(true)} onClose={() => setOpen(false)} />;
    }
    render(<Harness />);
    fireEvent.click(screen.getByRole('button', { name: 'Mở lịch sử trò chuyện' }));
    expect(document.activeElement).not.toBe(screen.getByRole('searchbox'));
  });

  it('chấm báo đang trả lời trên icon lịch sử khi có cuộc trò chuyện đang stream', () => {
    const { rerender } = render(<ChatHistoryPanel {...baseProps()} isOpen={false} onOpen={vi.fn()} onClose={vi.fn()} />);
    expect(screen.queryByTitle('Đang xử lý phản hồi...')).toBeNull();
    rerender(<ChatHistoryPanel {...baseProps()} streamingSessionIds={new Set(['s1'])} isOpen={false} onOpen={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByTitle('Đang xử lý phản hồi...')).toBeInTheDocument();
  });
});

describe('ChatHistoryPanel - chế độ ngăn kéo (màn hình nhỏ)', () => {
  it('render dạng dialog có hàng "Cuộc trò chuyện mới" khi mở', () => {
    const props = baseProps();
    render(<ChatHistoryPanel {...props} variant="drawer" isOpen onClose={vi.fn()} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole('button', { name: /Cuộc trò chuyện mới/ }));
    expect(props.onNewChat).toHaveBeenCalledTimes(1);
  });

  it('đóng bằng Esc và khi bấm nền mờ', () => {
    const onClose = vi.fn();
    const { container } = render(<ChatHistoryPanel {...baseProps()} variant="drawer" isOpen onClose={onClose} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.click(container.querySelector('[aria-hidden="true"]') as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('Esc khi đang mở menu ⋯ chỉ đóng menu, không đóng ngăn kéo', () => {
    const onClose = vi.fn();
    render(<ChatHistoryPanel {...baseProps()} variant="drawer" isOpen onClose={onClose} />);
    fireEvent.click(screen.getAllByRole('button', { name: 'Tùy chọn cuộc trò chuyện' })[0]);
    expect(screen.getByRole('menu')).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('menu')).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('không render gì khi đóng', () => {
    const { container } = render(<ChatHistoryPanel {...baseProps()} variant="drawer" isOpen={false} onClose={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });
});

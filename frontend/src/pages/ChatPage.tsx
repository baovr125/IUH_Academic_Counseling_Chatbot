import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, X, Plus, LogOut, LogIn, MessageSquare, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message, Conversation } from '../types/chat';

const ChatPage: React.FC = () => {
  const { logout, currentUser } = useAuth();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string>('new-chat');
  
  // Dummy history for UI mapping
  const [history] = useState<Conversation[]>([
    { id: '1', title: 'Quy chế học vụ năm tư', updatedAt: new Date() },
    { id: '2', title: 'Tín chỉ tự chọn Khoa học máy tính', updatedAt: new Date() },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const newUserMsg: Message = {
      id: Date.now().toString(),
      text: userText,
      isBot: false,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      // Logic xác thực linh hoạt: Có tài khoản thì lấy token, không thì gửi dạng Guest
      let token = '';
      if (currentUser) {
        token = await currentUser.getIdToken();
      }
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ 
          message: userText, 
          conversationId: currentConversationId 
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const newBotMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: data.reply,
        isBot: true,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, newBotMsg]);

    } catch (error: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: `**Lỗi hệ thống:** Không thể kết nối đến server Backend. Chi tiết: ${error.message}`,
        isBot: true,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`; // Max-h-32 = 128px
  };

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-white">
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 md:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-gray-900 transition-transform duration-300 ease-in-out md:static md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-full flex-col p-3">
          <button 
            onClick={() => { setMessages([]); setCurrentConversationId('new-chat'); }}
            className="flex w-full items-center gap-3 rounded-lg border border-gray-700 p-3 text-sm text-white transition-colors hover:bg-gray-800"
          >
            <Plus className="h-4 w-4" />
            Chat mới
          </button>

          <div className="mt-4 flex-1 overflow-y-auto">
            <div className="text-xs font-semibold text-gray-500 mb-2 px-2">Lịch sử hôm nay</div>
            <div className="space-y-1">
              {history.map((conv) => (
                <button 
                  key={conv.id}
                  className="flex w-full items-center gap-3 rounded-lg p-3 text-sm text-gray-300 transition-colors hover:bg-gray-800"
                >
                  <MessageSquare className="h-4 w-4" />
                  <span className="truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-auto border-t border-gray-800 pt-3">
            {currentUser ? (
              <button 
                onClick={logout}
                className="flex w-full items-center gap-3 rounded-lg p-3 text-sm text-gray-300 transition-colors hover:bg-gray-800"
              >
                <LogOut className="h-4 w-4" />
                Đăng xuất
              </button>
            ) : (
              <button 
                onClick={() => navigate('/login')}
                className="flex w-full items-center gap-3 rounded-lg p-3 text-sm font-medium text-[#be1e2d] transition-colors hover:bg-gray-800"
              >
                <LogIn className="h-4 w-4" />
                Đăng nhập hệ thống
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden relative">
        {/* Header */}
        <header className="flex h-14 items-center justify-between border-b bg-white px-4 md:justify-center">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700 md:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-semibold text-gray-800">IUH Chatbot Tư vấn học vụ</h1>
          <div className="w-6 md:hidden"></div> {/* Spacer for mobile balance */}
        </header>

        {/* Message List */}
        <div className="flex-1 overflow-y-auto p-4 md:px-20 lg:px-40">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-gray-400">
              <MessageSquare className="mb-4 h-12 w-12 opacity-50" />
              <p className="text-lg font-medium">Bạn cần tư vấn gì hôm nay?</p>
            </div>
          ) : (
            <div className="space-y-6 pb-6">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex w-full ${msg.isBot ? 'justify-start' : 'justify-end'}`}>
                  {msg.isBot && (
                    <div className="mr-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white shadow-sm">
                      AD
                    </div>
                  )}
                  <div className={`max-w-[85%] px-5 py-3.5 shadow-sm md:max-w-[75%] ${
                    msg.isBot 
                      ? 'rounded-2xl rounded-tl-none border border-gray-100 bg-white text-slate-700' 
                      : 'rounded-2xl rounded-tr-none bg-[#be1e2d] text-white'
                  }`}>
                    {msg.isBot ? (
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        className="prose prose-sm max-w-none dark:prose-invert"
                        components={{
                          a: ({node, ...props}) => (
                            <a {...props} target="_blank" rel="noopener noreferrer" className="font-bold text-blue-600 underline" />
                          )
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    ) : (
                      <div className="whitespace-pre-wrap">{msg.text}</div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex w-full justify-start">
                  <div className="mr-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white shadow-sm">
                    AD
                  </div>
                  <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-none border border-gray-100 bg-white px-5 py-4 shadow-sm">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '0ms' }}></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '150ms' }}></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Footer */}
        <div className="border-t bg-white p-4 pb-6 md:px-20 lg:px-40">
          <div className="relative flex w-full items-end gap-2 rounded-2xl border border-gray-300 bg-white shadow-sm focus-within:border-[#be1e2d] focus-within:ring-1 focus-within:ring-[#be1e2d]">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              rows={1}
              className="max-h-32 w-full resize-none rounded-2xl bg-transparent py-3 pl-4 pr-12 outline-none"
              placeholder="Nhập câu hỏi về chương trình Khoa học máy tính hoặc quy chế học vụ... (Shift + Enter để xuống dòng)"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-lg bg-[#be1e2d] text-white transition-colors disabled:bg-gray-300 disabled:text-gray-500 hover:bg-[#a01925]"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-2 text-center text-xs text-gray-400">
            Hệ thống có thể mắc lỗi. Vui lòng kiểm tra lại thông tin quan trọng.
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
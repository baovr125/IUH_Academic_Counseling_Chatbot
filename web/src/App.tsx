import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  text: string;
  isBot: boolean;
  id: number;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: "Chào bạn! Mình là Ad - Tư vấn viên học vụ ảo của IUH. Mình có thể giúp gì cho bạn hôm nay?", isBot: true }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    const userMessageId = Date.now();
    
    setMessages(prev => [...prev, { id: userMessageId, text: userMsg, isBot: false }]);
    setInput('');
    setIsLoading(true);

    try {
      // Đã sửa lỗi khoảng trắng thừa ở đầu URL http://localhost:8000/chat    https://bondless-immerse-paternal.ngrok-free.dev/chat
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!res.ok) throw new Error("Không thể kết nối với server AI");
      const data = await res.json();
      
      setMessages(prev => [...prev, { id: Date.now() + 1, text: data.reply, isBot: true }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now() + 2, 
        text: "Huhu, có lỗi kết nối với bộ não AI rồi! Bạn hãy thử lại sau nhé.", 
        isBot: true 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-slate-50 font-sans">
      {/* Header - Tối ưu cho cả Mobile & Desktop */}
      <header className="bg-[#be1e2d] text-white p-3 md:p-4 shadow-lg flex items-center justify-between px-4 md:px-8 sticky top-0 z-10">
        <div className="flex items-center gap-2 md:gap-4">
          <div className="w-9 h-9 md:w-11 md:h-11 bg-white rounded-full flex items-center justify-center text-[#be1e2d] font-black shadow-inner text-sm md:text-base">
            IUH
          </div>
          <div>
            <h1 className="text-sm md:text-xl font-bold leading-tight uppercase tracking-tight">Tư vấn Học vụ ảo</h1>
            <p className="text-[10px] md:text-xs opacity-90 font-medium">Đại học Công nghiệp TP.HCM</p>
          </div>
        </div>
        <div className="hidden sm:block text-[10px] md:text-xs bg-white/20 px-3 py-1 rounded-full backdrop-blur-sm border border-white/30">
          AI Smart Assistant
        </div>
      </header>

      {/* Chat Container - Tự động giãn cách theo màn hình */}
      <main className="flex-1 overflow-y-auto p-3 md:p-6 space-y-4 md:space-y-6 w-full max-w-5xl mx-auto custom-scrollbar">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.isBot ? 'justify-start' : 'justify-end'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
            <div className={`flex gap-2 md:gap-3 max-w-[92%] md:max-w-[80%] ${m.isBot ? 'flex-row' : 'flex-row-reverse'}`}>
              {m.isBot && (
                <div className="w-7 h-7 md:w-9 md:h-9 rounded-full bg-gradient-to-tr from-blue-600 to-blue-400 flex-shrink-0 flex items-center justify-center text-white text-[10px] md:text-xs font-bold shadow-md mt-1">
                  AD
                </div>
              )}
              
              <div className={`px-4 py-3 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed border ${
                m.isBot 
                  ? 'bg-white text-slate-700 border-slate-200 rounded-tl-none' 
                  : 'bg-[#be1e2d] text-white border-[#be1e2d] rounded-tr-none shadow-[#be1e2d]/20'
              }`}>
                
                {/* Đã bọc ReactMarkdown trong thẻ div để xử lý triệt để lỗi "Unexpected className prop" */}
                <div className="prose prose-sm md:prose-base max-w-none break-words">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Cấu hình để mọi thẻ <a> đều mở tab mới
                      a: ({ node, ...props }) => (
                        <a 
                          {...props} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className={`underline font-bold transition-colors ${m.isBot ? 'text-blue-600 hover:text-blue-800' : 'text-white hover:text-red-100'}`}
                        />
                      ),
                      p: ({children}) => <p className="mb-1 last:mb-0">{children}</p>
                    }}
                  >
                    {m.text}
                  </ReactMarkdown>
                </div>

              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-[#be1e2d] rounded-full animate-bounce [animation-duration:0.8s]"></div>
              <div className="w-1.5 h-1.5 bg-[#be1e2d] rounded-full animate-bounce [animation-duration:0.8s] [animation-delay:0.2s]"></div>
              <div className="w-1.5 h-1.5 bg-[#be1e2d] rounded-full animate-bounce [animation-duration:0.8s] [animation-delay:0.4s]"></div>
            </div>
          </div>
        )}
        <div ref={scrollRef} className="h-2" />
      </main>

      {/* Input Area - Cố định phía dưới, bo góc mượt mà */}
      <footer className="p-3 md:p-6 bg-white border-t border-slate-200 shadow-[0_-4px_10px_rgba(0,0,0,0.03)]">
        <div className="max-w-4xl mx-auto flex items-center gap-2 bg-slate-50 p-1.5 rounded-2xl border border-slate-200 focus-within:border-[#be1e2d] focus-within:ring-1 focus-within:ring-[#be1e2d] transition-all">
          <input
            type="text"
            className="flex-1 bg-transparent px-4 py-2 md:py-3 text-sm md:text-base focus:outline-none"
            placeholder="Hỏi về học phí, học bổng..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button 
            onClick={handleSend}
            disabled={input.trim() === '' || isLoading}
            className={`flex items-center justify-center p-2.5 md:p-3 rounded-xl transition-all shadow-sm ${
              isLoading || input.trim() === '' 
                ? 'bg-slate-300 cursor-not-allowed' 
                : 'bg-[#be1e2d] hover:bg-red-700 text-white active:scale-95'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          </button>
        </div>
        <p className="text-[9px] md:text-[10px] text-center text-slate-400 mt-2 font-medium">
          Dữ liệu được cập nhật từ Phòng Đào tạo IUH
        </p>
      </footer>
    </div>
  );
}

export default App;
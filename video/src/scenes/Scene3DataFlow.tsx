import React from 'react';
import { Audio, staticFile, useCurrentFrame } from 'remotion';
import { ArchitectureDiagram } from '../components/ArchitectureDiagram';
import { DataFlowOverlay } from '../components/DataFlowOverlay';
import { SubtitlesBar } from '../components/SubtitlesBar';

export const Scene3DataFlow: React.FC = () => {
  const frame = useCurrentFrame();

  // Dynamic Subtitle text synced with speech progression
  let subText = 'Ví dụ thực tế: Sinh viên khóa 21 hỏi: "Em bị điểm C môn Triết, GPA tính thế nào và có được học vượt không?"';
  let highlightNodeId: string | undefined = 'client-web';

  if (frame >= 315 && frame < 495) {
    subText = 'Bước 1: Câu hỏi kèm mã định danh được gửi từ trình duyệt qua cổng bảo mật Kong.';
    highlightNodeId = 'gateway-kong';
  } else if (frame >= 495 && frame < 675) {
    subText = 'Bước 2: Cổng Kong xác thực hợp lệ và chuyển tiếp câu hỏi đến dịch vụ Chatbot.';
    highlightNodeId = 'svc-chatbot';
  } else if (frame >= 675 && frame < 1035) {
    subText = 'Bước 3: Hệ thống kiểm tra cuốn sổ nhớ Redis bằng bộ đệm ngữ nghĩa 2 giai đoạn (Cross-Encoder chống nhầm lẫn câu đảo nghĩa).';
    highlightNodeId = 'cache-redis';
  } else if (frame >= 1035 && frame < 1305) {
    subText = 'Bước 4: Thực hiện tìm kiếm lai phân cấp trong PostgreSQL, kết hợp từ khóa và vector ngữ nghĩa qua RRF.';
    highlightNodeId = 'db-postgres';
  } else if (frame >= 1305 && frame < 1545) {
    subText = 'Bước 5: Sắp xếp điều luật theo thuật toán chiếc bánh kẹp Sandwich và bọc kín trong vùng an toàn chống tấn công mã độc.';
    highlightNodeId = 'svc-chatbot';
  } else if (frame >= 1545) {
    subText = 'Bước 6: Trí tuệ nhân tạo tự suy ngẫm trong thẻ nội bộ, tính điểm từng bước và truyền câu trả lời từng chữ qua SSE.';
    highlightNodeId = 'client-web';
  }

  return (
    <div className="relative w-full h-full bg-slate-950 flex flex-col font-sans">
      {/* Audio Voiceover: VieNeu-TTS Studio Quality */}
      <Audio src={staticFile('audio/scene3.mp3')} volume={1} />

      {/* Top Banner */}
      <div className="h-16 px-10 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-cyan-400 ring-4 ring-cyan-900/50" />
          <h2 className="text-base font-bold text-slate-100 tracking-wide">
            Mô Phỏng Luồng Dữ Liệu Thực Tế: Câu Hỏi Sinh Viên K21 (Triết học, GPA &amp; Học vượt)
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 bg-cyan-950/60 px-3 py-1 rounded-full border border-cyan-800">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          Active Pipeline Simulator
        </div>
      </div>

      {/* Main Diagram with Live Data Flow & Active Node Highlight */}
      <div className="flex-1 relative">
        <ArchitectureDiagram highlightNodeId={highlightNodeId} showDetails={false} />
        <DataFlowOverlay />
      </div>

      {/* Synchronized Subtitles Bar */}
      <SubtitlesBar text={subText} />
    </div>
  );
};

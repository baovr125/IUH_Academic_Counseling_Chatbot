import React from 'react';
import { Audio, staticFile, useCurrentFrame } from 'remotion';
import { ArchitectureDiagram } from '../components/ArchitectureDiagram';
import { SubtitlesBar } from '../components/SubtitlesBar';

export const Scene2Architecture: React.FC = () => {
  const frame = useCurrentFrame();

  // Precise Voiceover Synchronization (Total: 1660 frames = 55.35s)
  let activeCategory: string | undefined = undefined;
  let highlightNodeId: string | undefined = undefined;
  let sectionTitle = 'Tổng Quan Kiến Trúc Hệ Thống: 5 Phân Tầng Clean Architecture';
  let subText = 'Kiến trúc hệ thống được thiết kế theo chuẩn Clean Architecture gồm 5 phân tầng rõ rệt.';

  if (frame >= 165 && frame < 435) {
    // 5.5s -> 14.5s: Web Frontend
    activeCategory = 'client';
    highlightNodeId = 'client-web';
    sectionTitle = 'Tier 1: Web Client (React 18 + TypeScript + Vite + TailwindCSS)';
    subText = 'Sinh viên tương tác qua giao diện web React 18, hiển thị mượt mà công thức toán học và trích dẫn điều khoản.';
  } else if (frame >= 435 && frame < 825) {
    // 14.5s -> 27.5s: Kong API Gateway
    activeCategory = 'gateway';
    highlightNodeId = 'gateway-kong';
    sectionTitle = 'Tier 2: Kong API Gateway 3.9.3 (Bác bảo vệ thông minh kiểm tra JWT HS256 & Rate Limit)';
    subText = 'Mọi yêu cầu đều qua Kong API Gateway như bác bảo vệ thông minh: kiểm tra thẻ sinh viên, chặn tấn công rồi mới điều hướng.';
  } else if (frame >= 825 && frame < 1155) {
    // 27.5s -> 38.5s: Academic Chatbot Service
    activeCategory = 'service';
    highlightNodeId = 'svc-chatbot';
    sectionTitle = 'Tier 3: Academic Chatbot Service (Bộ não điều phối RAG & SpatioRoute Router)';
    subText = 'Ở trung tâm là Academic Chatbot Service, bộ não điều khiển toàn bộ quy trình AI, định tuyến ý định và điều phối LLM.';
  } else if (frame >= 1155 && frame < 1290) {
    // 38.5s -> 43s: Redis 7 Semantic Cache
    activeCategory = 'storage';
    highlightNodeId = 'cache-redis';
    sectionTitle = 'Tier 5: Redis 7 (Cuốn sổ ghi nhớ ngữ nghĩa 2 giai đoạn siêu tốc < 20ms)';
    subText = 'Phía sau là cụm cơ sở dữ liệu: Redis đóng vai trò cuốn sổ ghi nhớ tốc độ cao, phản hồi cache dưới 20ms.';
  } else if (frame >= 1290 && frame < 1425) {
    // 43s -> 47.5s: PostgreSQL + pgvector
    activeCategory = 'storage';
    highlightNodeId = 'db-postgres';
    sectionTitle = 'Tier 5: PostgreSQL / Supabase + pgvector (Lưu trữ 1024d Dense Vectors & Full-Text Search)';
    subText = 'PostgreSQL lưu trữ các vector nhúng 1024 chiều và chỉ mục tìm kiếm toàn văn Full-Text Search kết hợp RRF.';
  } else if (frame >= 1425) {
    // 47.5s -> 55.35s: Worker, RabbitMQ, MinIO
    activeCategory = 'worker';
    highlightNodeId = 'worker-doc';
    sectionTitle = 'Tier 4: Cụm Worker Bất Đồng Bộ Celery, RabbitMQ & MinIO S3';
    subText = 'Hệ thống mở rộng với Celery Worker, hàng đợi RabbitMQ và bộ lưu trữ MinIO, xử lý tài liệu đa định dạng chạy ngầm.';
  }

  return (
    <div className="relative w-full h-full bg-slate-950 flex flex-col font-sans">
      {/* Audio Voiceover: VieNeu-TTS Studio Quality */}
      <Audio src={staticFile('audio/scene2.mp3')} volume={1} />

      {/* Top Banner */}
      <div className="h-16 px-10 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-indigo-500 ring-4 ring-indigo-900/50" />
          <h2 className="text-base font-bold text-slate-100 tracking-wide">
            {sectionTitle}
          </h2>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1 rounded-full border border-slate-800">
          Docker Compose: 5 Services + Kong + RabbitMQ + Redis + MinIO
        </div>
      </div>

      {/* Main Diagram Area */}
      <div className="flex-1 relative">
        <ArchitectureDiagram
          highlightNodeId={highlightNodeId}
          activeCategory={activeCategory}
        />
      </div>

      {/* Synchronized Subtitles Bar */}
      <SubtitlesBar text={subText} />
    </div>
  );
};

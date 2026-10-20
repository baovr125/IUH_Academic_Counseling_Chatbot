import React from 'react';
import { Audio, staticFile, useCurrentFrame } from 'remotion';
import { IMPORTANT_FILES } from '../data/architectureData';
import { FolderTree } from '../components/FolderTree';
import { FileHighlightCard } from '../components/FileHighlightCard';
import { SubtitlesBar } from '../components/SubtitlesBar';
import { Code2 } from 'lucide-react';

export const Scene4FileHighlights: React.FC = () => {
  const frame = useCurrentFrame();

  // Precise Speech-to-File Synchronization (1653 frames total)
  let fileIndex = 0;
  let subText = 'Điểm sáng nổi bật của dự án nằm ở 4 file mã nguồn cốt lõi trong chuỗi commit mới nhất.';

  if (frame >= 150 && frame < 540) {
    // 5s -> 18s: hybrid_chunker.py (Parent-Child)
    fileIndex = 0;
    subText = 'File hybrid_chunker: Phân đoạn cha con: đoạn cha giữ trọn ngữ cảnh điều luật, đoạn con nhúng vector tìm kiếm chính xác.';
  } else if (frame >= 540 && frame < 930) {
    // 18s -> 31s: rag_service.py (Sandwich Reordering)
    fileIndex = 1;
    subText = 'File rag_service: Thuật toán chiếc bánh kẹp Sandwich đưa 2 tài liệu đắt giá nhất lên đầu và xuống cuối, khắc phục Lost in the Middle.';
  } else if (frame >= 930 && frame < 1305) {
    // 31s -> 43.5s: prompt_templates.py (SpatioRoute -64%)
    fileIndex = 2;
    subText = 'File prompt_templates: Tối ưu mật độ token giảm 64% chi phí, ép buộc giải toán từng bước và khẳng định dứt khoát.';
  } else if (frame >= 1305) {
    // 43.5s -> 55.11s: query_filter.py (Guardrails & Sandboxing)
    fileIndex = 3;
    subText = 'File query_filter: Lớp giáp an ninh bọc Context Sandboxing và chặn đứng mọi mã độc tiêm lệnh Prompt Injection.';
  }

  const activeFile = IMPORTANT_FILES[fileIndex];

  return (
    <div className="relative w-full h-full bg-slate-950 flex flex-col font-sans select-none overflow-hidden">
      {/* Audio Voiceover: VieNeu-TTS Studio Quality */}
      <Audio src={staticFile('audio/scene4.mp3')} volume={1} />

      {/* Top Banner */}
      <div className="h-16 px-10 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Code2 size={20} className="text-amber-400" />
          <h2 className="text-base font-bold text-slate-100 tracking-wide">
            Cấu Trúc Thư Mục &amp; Điểm Sáng Codebase (Commit a50bcffd ➔ HEAD)
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Đang giải thích:</span>
          <span className="text-xs font-mono font-bold text-amber-300 bg-amber-950/70 border border-amber-800/80 px-2.5 py-0.5 rounded-full">
            {activeFile.fileName} ({fileIndex + 1}/4)
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 grid grid-cols-12 gap-8 p-8 items-center">
        {/* Left Col: Folder Tree (5 cols) */}
        <div className="col-span-5 h-[580px]">
          <FolderTree activeFileIndex={fileIndex} />
        </div>

        {/* Right Col: Code Snippet Card (7 cols) */}
        <div className="col-span-7 flex justify-center">
          <FileHighlightCard key={activeFile.path} file={activeFile} />
        </div>
      </div>

      {/* Synchronized Subtitles Bar */}
      <SubtitlesBar text={subText} />
    </div>
  );
};

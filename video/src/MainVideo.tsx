import React from 'react';
import { Series } from 'remotion';
import { Scene1Intro } from './scenes/Scene1Intro';
import { Scene2ArchitectureComparison } from './scenes/Scene2ArchitectureComparison';
import { Scene3LiteratureMapping } from './scenes/Scene3LiteratureMapping';
import { Scene4HybridChunking } from './scenes/Scene4HybridChunking';
import { Scene5SemanticCache } from './scenes/Scene5SemanticCache';
import { Scene6HybridRRF } from './scenes/Scene6HybridRRF';
import { Scene7ContextSandboxing } from './scenes/Scene7ContextSandboxing';
import { Scene8UnitTests } from './scenes/Scene8UnitTests';
import { Scene9Outro } from './scenes/Scene9Outro';

// Audio-calibrated exact frame durations at 30 fps (High-Density Technical Script)
export const SCENE_DURATIONS_30FPS = {
  scene1: 1305, // 43.51s
  scene2: 2360, // 78.67s
  scene3: 1713, // 57.12s
  scene4: 1790, // 59.67s
  scene5: 1724, // 57.47s
  scene6: 1690, // 56.34s
  scene7: 1610, // 53.69s
  scene8: 1515, // 50.50s
  scene9: 1213, // 40.46s
};

export const TOTAL_FRAMES_30FPS = Object.values(SCENE_DURATIONS_30FPS).reduce((a, b) => a + b, 0); // 14,423 frames (~8m 0s)

export const MainVideo: React.FC = () => {
  return (
    <Series>
      {/* Scene 1: Mở Đầu & Tử Huyệt của Naive RAG trong Tư Vấn Học Vụ (2274 frames = ~75.8s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene1}>
        <Scene1Intro />
      </Series.Sequence>

      {/* Scene 2: Cơ Sở Khoa Học & Lựa Chọn: Advanced RAG hay Modular RAG? (2950 frames = ~98.3s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene2}>
        <Scene2ArchitectureComparison />
      </Series.Sequence>

      {/* Scene 3: Bản Đồ Nghiên Cứu: Áp Dụng Điểm Nào, Loại Bỏ Điểm Nào? (4010 frames = ~133.7s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene3}>
        <Scene3LiteratureMapping />
      </Series.Sequence>

      {/* Scene 4: Kỹ Nghệ Dữ Liệu Đầu Vào: Hybrid Parent-Child & Table-Aware (2676 frames = ~89.2s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene4}>
        <Scene4HybridChunking />
      </Series.Sequence>

      {/* Scene 5: Tốc Độ & An Toàn: Bộ Đệm Ngữ Nghĩa 2 Giai Đoạn (2689 frames = ~89.6s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene5}>
        <Scene5SemanticCache />
      </Series.Sequence>

      {/* Scene 6: Truy Xuất Lai Hợp Hybrid RRF, Quota Deduplication & BGE-Reranker (3211 frames = ~107.0s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene6}>
        <Scene6HybridRRF />
      </Series.Sequence>

      {/* Scene 7: Tối Ưu Chú Ý Transformer, Context Sandboxing & SpatioRoute (2461 frames = ~82.0s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene7}>
        <Scene7ContextSandboxing />
      </Series.Sequence>

      {/* Scene 8: Bảo Chứng Chất Lượng Qua 126 Automated Unit Tests (2667 frames = ~88.9s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene8}>
        <Scene8UnitTests />
      </Series.Sequence>

      {/* Scene 9: Tổng Kết & Tầm Nhìn Hệ Thống (1516 frames = ~50.5s) */}
      <Series.Sequence durationInFrames={SCENE_DURATIONS_30FPS.scene9}>
        <Scene9Outro />
      </Series.Sequence>
    </Series>
  );
};

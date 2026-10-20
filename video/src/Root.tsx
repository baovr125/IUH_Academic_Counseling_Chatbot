import React from 'react';
import { Composition } from 'remotion';
import './index.css';
import { MainVideo, SCENE_DURATIONS_30FPS, TOTAL_FRAMES_30FPS } from './MainVideo';
import { Scene1Intro } from './scenes/Scene1Intro';
import { Scene2ArchitectureComparison } from './scenes/Scene2ArchitectureComparison';
import { Scene3LiteratureMapping } from './scenes/Scene3LiteratureMapping';
import { Scene4HybridChunking } from './scenes/Scene4HybridChunking';
import { Scene5SemanticCache } from './scenes/Scene5SemanticCache';
import { Scene6HybridRRF } from './scenes/Scene6HybridRRF';
import { Scene7ContextSandboxing } from './scenes/Scene7ContextSandboxing';
import { Scene8UnitTests } from './scenes/Scene8UnitTests';
import { Scene9Outro } from './scenes/Scene9Outro';
import { SceneRAGOperationFlow } from './scenes/SceneRAGOperationFlow';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 0. DEDICATED MASTER VIDEO: Quy Trình Hoạt Động End-to-End Của Hệ Thống RAG Chatbot (6419 frames = ~214.0s / ~3m 34s) */}
      <Composition
        id="RAG-EndToEnd-Operation"
        component={SceneRAGOperationFlow}
        durationInFrames={6419}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 1. Full Master Explainer Video (24,454 frames @ 30fps = ~815.1s / ~13m 35s) */}
      <Composition
        id="MainExplainerVideo"
        component={MainVideo}
        durationInFrames={TOTAL_FRAMES_30FPS}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 2. Standalone Scene 1: Mở Đầu & Tử Huyệt của Naive RAG (2274 frames = ~75.8s) */}
      <Composition
        id="Scene1-Intro"
        component={Scene1Intro}
        durationInFrames={SCENE_DURATIONS_30FPS.scene1}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 3. Standalone Scene 2: Cơ Sở Khoa Học & Lựa Chọn Kiến Trúc (2950 frames = ~98.3s) */}
      <Composition
        id="Scene2-ArchitectureComparison"
        component={Scene2ArchitectureComparison}
        durationInFrames={SCENE_DURATIONS_30FPS.scene2}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 4. Standalone Scene 3: Bản Đồ Nghiên Cứu 5 Paper (4010 frames = ~133.7s) */}
      <Composition
        id="Scene3-LiteratureMapping"
        component={Scene3LiteratureMapping}
        durationInFrames={SCENE_DURATIONS_30FPS.scene3}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 5. Standalone Scene 4: Kỹ Nghệ Dữ Liệu Hybrid Parent-Child & Table-Aware (2676 frames = ~89.2s) */}
      <Composition
        id="Scene4-HybridChunking"
        component={Scene4HybridChunking}
        durationInFrames={SCENE_DURATIONS_30FPS.scene4}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 6. Standalone Scene 5: Tốc Độ & An Toàn: Bộ Đệm Ngữ Nghĩa 2 Giai Đoạn (2689 frames = ~89.6s) */}
      <Composition
        id="Scene5-SemanticCache"
        component={Scene5SemanticCache}
        durationInFrames={SCENE_DURATIONS_30FPS.scene5}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 7. Standalone Scene 6: Truy Xuất Lai Hợp Hybrid RRF & Quota Deduplication (3211 frames = ~107.0s) */}
      <Composition
        id="Scene6-HybridRRF"
        component={Scene6HybridRRF}
        durationInFrames={SCENE_DURATIONS_30FPS.scene6}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 8. Standalone Scene 7: Tối Ưu Chú Ý Transformer & Context Sandboxing (2461 frames = ~82.0s) */}
      <Composition
        id="Scene7-ContextSandboxing"
        component={Scene7ContextSandboxing}
        durationInFrames={SCENE_DURATIONS_30FPS.scene7}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 9. Standalone Scene 8: Bảo Chứng Chất Lượng Qua 126 Unit Tests (2667 frames = ~88.9s) */}
      <Composition
        id="Scene8-UnitTests"
        component={Scene8UnitTests}
        durationInFrames={SCENE_DURATIONS_30FPS.scene8}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* 10. Standalone Scene 9: Tổng Kết & Tầm Nhìn Hệ Thống (1516 frames = ~50.5s) */}
      <Composition
        id="Scene9-Outro"
        component={Scene9Outro}
        durationInFrames={SCENE_DURATIONS_30FPS.scene9}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};

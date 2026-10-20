#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import subprocess
import numpy as np
import soundfile as sf
from vieneu import Vieneu

out_dir = "video/public/audio"
os.makedirs(out_dir, exist_ok=True)
sample_rate = 24000
pause_samples = int(0.32 * sample_rate) # 320ms pause between steps
pause_audio = np.zeros(pause_samples, dtype=np.float32)

steps_data = [
    {
        "step_id": 0,
        "title": "Tổng Quan Luồng Xử Lý End-to-End",
        "file": "services/academic_chatbot_service/app/main.py",
        "text": "Chào mừng bạn đến với quy trình vận hành toàn trình của hệ thống Chatbot Tư vấn Học vụ I U Hát. Hệ thống được xây dựng trên kiến trúc Advanced RAG hướng dịch vụ, kết nối chặt chẽ giữa cổng bảo mật, dịch vụ xử lý học vụ, cơ sở dữ liệu Pốt gờ rét và mô hình ngôn ngữ lớn dùng chung."
    },
    {
        "step_id": 1,
        "title": "Cổng Bảo Mật & Định Tuyến Kong Gateway",
        "file": "gateway/kong.template.yml",
        "text": "Khởi đầu quy trình, sinh viên gửi câu hỏi từ cổng thông tin trực tuyến đến cổng Kong Gateway tại cổng 8000. Kong thực thi kiểm soát tần suất tối đa 1.000 yêu cầu một phút, gán mã định danh X Request I D để truy vết toàn trình, và tước bỏ mọi tiêu đề giả mạo trước khi chuyển tiếp yêu cầu tới cổng 8002 của dịch vụ Chatbot."
    },
    {
        "step_id": 2,
        "title": "Lớp Giáp An Toàn Guardrail Chặn Tiêm Mã",
        "file": "services/academic_chatbot_service/app/guardrails/query_filter.py",
        "text": "Tại lối vào của dịch vụ, bộ lọc Guardrail lập tức kiểm tra chuỗi câu hỏi bằng hệ thống biểu thức chính quy biên dịch sẵn. Mọi hành vi tiêm mã prompt injection, đóng thẻ X M L giả mạo, hoặc phá vỡ cấu trúc hệ thống đều bị chặn đứng và từ chối ngay lập tức, hoàn toàn không tiêu tốn token L L M."
    },
    {
        "step_id": 3,
        "title": "Phân Loại Ý Định & Phân Rã Truy Vấn",
        "file": "services/academic_chatbot_service/app/services/rag_service.py",
        "text": "Tiếp theo, module Rewriter sử dụng mô hình ngôn ngữ lớn Cua wen 35B để phân tích ngữ cảnh hội thoại. Mô hình phân loại câu hỏi vào một trong bảy nhóm ý định học vụ gồm Thủ tục, Quy chế, Khủng hoảng, Đề xuất, Khiếu nại, Kỹ thuật và Chung, đồng thời phân rã câu hỏi kép thành tối đa 4 truy vấn con độc lập."
    },
    {
        "step_id": 4,
        "title": "Mã Hóa Vector & Ký Ức Hội Thoại",
        "file": "services/academic_chatbot_service/app/services/rag_service.py",
        "text": "Truy vấn chính được mô hình Bi Encoder tiếng Việt tối ưu O N N X trên C U D A chuyển hóa thành vector 768 chiều. Vector này được lưu vào bộ đệm bộ nhớ và kích hoạt tác vụ bất đồng bộ để cập nhật ký ức ngữ nghĩa cho phiên trao đổi của sinh viên."
    },
    {
        "step_id": 5,
        "title": "Bộ Nhớ Đệm Ngữ Nghĩa Hai Giai Đoạn",
        "file": "services/academic_chatbot_service/app/services/rag_service.py",
        "text": "Trước khi tìm kiếm dữ liệu, hệ thống đối soát bộ nhớ đệm ngữ nghĩa hai giai đoạn. Lớp không kiểm tra bộ đệm Rê đít theo khóa chuẩn hóa với phản hồi chỉ trong 12 mili giây. Nếu chưa khớp, lớp một quét vector trên P G véc tơ với ngưỡng 0,60, và lớp hai kiểm định bằng Cross Encoder với ngưỡng khắt khe 0,80 kết hợp lớp giáp số thực thể Entity Numbers Guard."
    },
    {
        "step_id": 6,
        "title": "Truy Xuất Lai Hợp Song Song Hybrid RRF",
        "file": "services/academic_chatbot_service/app/services/rag_service.py",
        "text": "Khi đệm không khớp, hệ thống kích hoạt tìm kiếm song song cho từng truy vấn con qua hàm R R F trên cơ sở dữ liệu Pốt gờ rét. Kênh vector H N S W và kênh từ khóa B M hai mươi lăm được dung hợp theo công thức nghịch đảo thứ hạng với hằng số k bằng 60, mang lại 50 ứng viên tiềm năng cho mỗi truy vấn."
    },
    {
        "step_id": 7,
        "title": "Tái Xếp Hạng Cross-Encoder & Hạn Ngạch Khối Cha",
        "file": "services/academic_chatbot_service/app/services/rag_service.py",
        "text": "Mô hình Cross Encoder B G E Reranker chấm điểm tương đồng chéo giữa từng khối dữ liệu với câu hỏi con tương ứng. Hệ thống loại bỏ điểm dưới 0,20 và áp dụng hạn ngạch phân bổ khối cha độc lập từ 2 đến tối đa 8 văn bản, ưu tiên các khối đạt điểm chất lượng cao từ 0,65 trở lên."
    },
    {
        "step_id": 8,
        "title": "Bung Nở Small-to-Big & Hoán Vị Bánh Kẹp",
        "file": "services/academic_chatbot_service/app/guardrails/query_filter.py",
        "text": "Các khối con đạt chuẩn được tự động bung nở thành khối cha hoàn chỉnh 1.200 token qua cơ chế Small-to-Big. Sau đó, thuật toán hoán vị bánh kẹp Sandwich Reordering đưa tài liệu tốt nhất lên đầu và tài liệu tốt thứ hai xuống sát đáy theo trật tự một, ba, năm, bốn, hai, giải quyết triệt để hiện tượng mất chú ý ở vùng giữa của Transformer."
    },
    {
        "step_id": 9,
        "title": "Đóng Hộp XML & Chỉ Thị Hệ Thống Động",
        "file": "services/academic_chatbot_service/app/prompts/prompt_templates.py",
        "text": "Toàn bộ tài liệu được bọc kín trong vùng an toàn X M L Sandboxing kèm thẻ nhắc nhở câu hỏi ở sát đáy. Hệ thống ghép nối chỉ thị theo ý định chuyên biệt, kích hoạt suy luận số học từng bước Arithmetic C o T cho quy chế tín chỉ, giúp tiết kiệm hơn 60% token prompt không cần thiết."
    },
    {
        "step_id": 10,
        "title": "Sinh Trả Lời Thời Gian Thực & Lọc Luồng SSE",
        "file": "services/academic_chatbot_service/app/services/llm_generation_service.py",
        "text": "Mô hình ngôn ngữ lớn Cua wen 35B dùng chung tiến hành sinh văn bản theo thời gian thực. Hệ thống gửi trước dữ liệu trích dẫn nguồn học vụ, đồng thời bộ lọc trên máy chủ tự động bóc tách các thẻ suy nghĩ nháp trước khi chuyển tiếp từng token mượt mà qua luồng Server-Sent Events về lại giao diện người dùng."
    },
    {
        "step_id": 11,
        "title": "Chốt Chặn Self-RAG & Ghi Đệm Bất Đồng Bộ",
        "file": "services/academic_chatbot_service/app/services/llm_generation_service.py",
        "text": "Ở bước cuối cùng, chốt chặn sép RAG phân tích các thẻ phản chiếu chất lượng: chỉ khi độ liên quan tài liệu được xác nhận và độ tin cậy đạt mức cao, phản hồi mới được phép ghi đệm vào Rê đít và Pốt gờ rét trong 7 ngày, khép lại chu trình xử lý chuẩn mực và an toàn tuyệt đối."
    }
]

print("Initializing Vieneu TTS v3nano...")
tts = Vieneu(mode="v3nano")
voice_name = "Minh Quân"

audio_chunks = []
timings = []
current_time_sec = 0.0

for idx, item in enumerate(steps_data):
    clean_text = item["text"].strip()
    print(f"[{idx+1}/{len(steps_data)}] Synthesizing: {item['title']} ({clean_text[:45]}...)...")
    audio = tts.infer(clean_text, voice=voice_name)
    if not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)
    else:
        audio = audio.astype(np.float32)
    
    dur_sec = len(audio) / sample_rate
    start_frame = int(round(current_time_sec * 30))
    end_frame = int(round((current_time_sec + dur_sec) * 30))

    timings.append({
        "step_id": item["step_id"],
        "title": item["title"],
        "file": item["file"],
        "text": clean_text,
        "start_sec": round(current_time_sec, 2),
        "end_sec": round(current_time_sec + dur_sec, 2),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "duration_frames": end_frame - start_frame
    })

    audio_chunks.append(audio)
    audio_chunks.append(pause_audio)
    current_time_sec += dur_sec + 0.32

full_audio = np.concatenate(audio_chunks)
wav_path = os.path.join(out_dir, "rag_operation_flow.wav")
mp3_path = os.path.join(out_dir, "rag_operation_flow.mp3")
sf.write(wav_path, full_audio, sample_rate)

print("Converting to MP3 via ffmpeg...")
subprocess.run([
    "ffmpeg", "-y", "-i", wav_path,
    "-b:a", "192k", mp3_path
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

res = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
], stdout=subprocess.PIPE, text=True, check=True)
total_dur = float(res.stdout.strip())
total_frames = int(round(total_dur * 30))

print(f"==> Successfully generated rag_operation_flow.mp3: {total_dur:.2f}s (~{total_frames} frames @ 30fps)")

# Save timing data
data_file = "video/src/data/ragOperationTimings.json"
with open(data_file, "w", encoding="utf-8") as f:
    json.dump({
        "duration_sec": round(total_dur, 2),
        "total_frames": total_frames,
        "steps": timings
    }, f, ensure_ascii=False, indent=2)

print(f"Timing metadata saved to {data_file}")

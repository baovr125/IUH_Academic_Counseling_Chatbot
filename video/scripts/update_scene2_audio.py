#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import subprocess
import numpy as np
import soundfile as sf
from vieneu import Vieneu

out_dir = "video/public/audio"
sample_rate = 24000
pause_samples = int(0.28 * sample_rate) # 280ms pause
pause_audio = np.zeros(pause_samples, dtype=np.float32)

sentences = [
    "Dựa trên công trình tổng quan của Gao và các cộng sự năm 2023, chúng tôi lựa chọn kiến trúc Át van xơ RAG tích hợp các module chuyên sâu thay vì Mô đu la RAG thuần túy.",
    "Bởi lẽ, kiến trúc Mô đu la RAG dạng đa tác tử agentic phải qua nhiều vòng lập luận lặp lại, khiến độ trễ phản hồi kéo dài từ 5 đến 10 giây và làm đội chi phí token lên gấp 4 lần, hoàn toàn không khả thi khi phục vụ hàng nghìn sinh viên cùng lúc.",
    "Trên sơ đồ xử lý yêu cầu thực tế, câu hỏi từ giao diện người dùng I U Hát đi qua cổng bảo mật Kong Gateway, được xác thực J W T và kiểm soát tần suất, trước khi chuyển tiếp tới dịch vụ Academic Chatbot Service tại cổng 8002.",
    "Tại đây, lớp giáp Guardrail lập tức kiểm tra và ngăn chặn các hành vi tiêm mã prompt injection. Kế tiếp, module Rewriter và Router phân tích 7 loại ý định và phân rã truy vấn.",
    "Đặc biệt, trong thực tế mã nguồn, chúng tôi sử dụng chung cùng một mô hình ngôn ngữ lớn cho cả bước viết lại truy vấn và bước sinh câu trả lời cuối cùng, với cấu trúc phản hồi JSON không cần học tăng cường để tối ưu tốc độ.",
    "Truy vấn sau đó được đối soát qua bộ nhớ đệm ngữ nghĩa hai giai đoạn, tìm kiếm lai hợp R R F trên Pốt gờ rét, tái xếp hạng và cô lập ngữ cảnh, trước khi mô hình trả về phản hồi theo thời gian thực qua luồng Server-Sent Events về lại giao diện sinh viên."
]

print("Loading Vieneu TTS v3nano...")
tts = Vieneu(mode="v3nano")
voice_name = "Minh Quân"

scene_audio_chunks = []
timings = []
current_time_sec = 0.0

for idx, sent in enumerate(sentences):
    clean_sent = sent.strip()
    print(f"[{idx+1}/{len(sentences)}] Synthesizing: {clean_sent[:60]}...")
    audio = tts.infer(clean_sent, voice=voice_name)
    if not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)
    else:
        audio = audio.astype(np.float32)
    
    dur_sec = len(audio) / sample_rate
    start_frame = int(current_time_sec * 30)
    end_frame = int((current_time_sec + dur_sec) * 30)

    timings.append({
        "sentence_idx": idx,
        "text": clean_sent,
        "start_sec": round(current_time_sec, 2),
        "end_sec": round(current_time_sec + dur_sec, 2),
        "start_frame": start_frame,
        "end_frame": end_frame
    })

    scene_audio_chunks.append(audio)
    scene_audio_chunks.append(pause_audio)
    current_time_sec += dur_sec + 0.28

full_audio = np.concatenate(scene_audio_chunks)
wav_path = os.path.join(out_dir, "scene2.wav")
mp3_path = os.path.join(out_dir, "scene2.mp3")
sf.write(wav_path, full_audio, sample_rate)

subprocess.run([
    "ffmpeg", "-y", "-i", wav_path,
    "-b:a", "192k", mp3_path
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

res = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
], stdout=subprocess.PIPE, text=True, check=True)
dur = float(res.stdout.strip())
frames = int(dur * 30)

print(f"==> Scene 2 regenerated: {dur:.2f}s (~{frames} frames @ 30fps)")

# Update sentenceTimings.json
timings_file = "video/src/data/sentenceTimings.json"
with open(timings_file, "r", encoding="utf-8") as f:
    all_timings = json.load(f)

all_timings["scene2"] = {
    "duration_sec": round(dur, 2),
    "total_frames": frames,
    "sentences": timings
}

with open(timings_file, "w", encoding="utf-8") as f:
    json.dump(all_timings, f, ensure_ascii=False, indent=2)

# Update audioDurations.json
dur_file = "video/src/data/audioDurations.json"
with open(dur_file, "r", encoding="utf-8") as f:
    all_durs = json.load(f)

all_durs["scene2"] = frames

with open(dur_file, "w", encoding="utf-8") as f:
    json.dump(all_durs, f, ensure_ascii=False, indent=2)

print("Updated sentenceTimings.json and audioDurations.json!")

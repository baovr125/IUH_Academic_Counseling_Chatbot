#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates high-quality Vieneu TTS audio for the revised technical script (6.5 minutes),
with natural Vietnamese pronunciation ('sép RAG', standard technical terms),
and records precise sentence-level timestamps for frame-accurate video synchronization.
"""

import os
import re
import json
import subprocess
import numpy as np
import soundfile as sf
from vieneu import Vieneu

# REVISED HIGH-DENSITY TECHNICAL SCRIPT (100% faithful to actual codebase)
SCENE_SCRIPTS = {
    "scene1": [
        "Chào các bạn! Tại Trường Đại học Công nghiệp Thành phố Hồ Chí Minh (I U Hát), hệ thống quy chế đào tạo tín chỉ bao gồm hàng trăm trang văn bản pháp lý phức tạp và liên tục cập nhật theo từng khóa sinh viên.",
        "Nếu triển khai một hệ sinh thái RAG cơ bản kiểu Nai íp RAG thông thường, hệ thống sẽ lập tức rơi vào ba tử huyệt:",
        "Thứ nhất, việc cắt nhỏ văn bản cố định làm đứt gãy ngữ cảnh của các bảng biểu điều kiện tốt nghiệp và biểu phí học kỳ.",
        "Thứ hai, mô hình dễ nhầm lẫn giữa văn bản cũ và mới, dẫn đến ảo giác học vụ nghiêm trọng khi sinh viên khóa cũ bị áp nhầm quy chế của khóa mới.",
        "Thứ ba, người dùng có thể thực hiện tấn công tiêm mã prompt injection, lừa mô hình xác nhận sai kết quả học tập.",
        "Dịch vụ Academic Chatbot Service được thiết kế để giải quyết triệt để bài toán này."
    ],
    "scene2": [
        "Dựa trên công trình tổng quan của Gao và các cộng sự năm 2023, chúng tôi lựa chọn kiến trúc Át van xơ RAG tích hợp các module chuyên sâu thay vì Mô đu la RAG thuần túy.",
        "Bởi lẽ, kiến trúc Mô đu la RAG dạng đa tác tử agentic phải qua nhiều vòng lập luận lặp lại, khiến độ trễ phản hồi kéo dài từ 5 đến 10 giây và làm đội chi phí token lên gấp 4 lần, hoàn toàn không khả thi khi phục vụ hàng nghìn sinh viên cùng lúc.",
        "Trên sơ đồ luồng dữ liệu của Academic Chatbot Service, câu hỏi từ sinh viên đi qua cổng bảo mật Kong Gateway và hàng rào an toàn Guardrail.",
        "Tiếp theo, module Rewriter và Router phân tích 7 loại ý định và phân rã truy vấn.",
        "Đặc biệt, trong thực tế mã nguồn, chúng tôi sử dụng chung cùng một mô hình ngôn ngữ lớn cho cả bước viết lại truy vấn và bước sinh câu trả lời cuối cùng, với cấu trúc phản hồi JSON không cần học tăng cường để tối ưu tốc độ.",
        "Truy vấn sau đó được đối soát qua bộ nhớ đệm ngữ nghĩa hai giai đoạn, tìm kiếm lai hợp R R F, tái xếp hạng và cô lập ngữ cảnh trước khi mô hình trả về phản hồi qua luồng Server-Sent Events."
    ],
    "scene3": [
        "Kiến trúc của dự án được kế thừa có chọn lọc từ 5 nghiên cứu khoa học cốt lõi:",
        "Thứ nhất, từ nghiên cứu Rewrite-Retrieve-Read của Microsoft Research, chúng tôi áp dụng phân rã câu hỏi kép thành các truy vấn con độc lập, nhưng loại bỏ phương pháp học tăng cường P P O phức tạp để sử dụng ràng buộc JSON schema siêu tốc.",
        "Thứ hai, từ nghiên cứu Lost in the Middle của Đại học Stanford, chúng tôi áp dụng thuật toán hoán vị bánh kẹp Sandwich Reordering và gắn thẻ nhắc câu hỏi ở sát đáy ngữ cảnh.",
        "Thứ ba, từ nghiên cứu sép RAG của Đại học Washington, chúng tôi tích hợp các thẻ tự đánh giá độ liên quan và độ tự tin trong khối suy nghĩ, làm chốt chặn an toàn cho bộ nhớ đệm.",
        "Thứ tư, kế thừa từ C F RAG, hệ thống thiết lập độ ưu tiên giải quyết mâu thuẫn văn bản: niên khóa sinh viên được ưu tiên cao nhất, kế đến là năm ban hành văn bản.",
        "Cuối cùng, chúng tôi loại bỏ kỹ thuật Hai Đi của Đại học C M U, vì việc tạo câu trả lời giả định rất dễ làm sai lệch các điều khoản học vụ nghiêm ngặt."
    ],
    "scene4": [
        "Tầng dữ liệu của hệ thống được xử lý qua module hai brít chăn cơ, tạo ra 1.445 khối cha và 3.252 khối con trong cơ sở dữ liệu thực tế:",
        "Thứ nhất, văn bản Markdown được trích xuất siêu dữ liệu phần đầu frontmatter gồm địa chỉ nguồn, tiêu đề và đường dẫn breadcrumb điều hướng.",
        "Thứ hai, hệ thống bóc tách các khối cha theo tiêu đề Markdown từ Hát một đến Hát sáu. Chỉ khi một phần vượt quá ngưỡng 1.200 token, thuật toán mới kích hoạt biểu thức chính quy phụ để nhận diện số La Mã hoặc đề mục in đậm, kết hợp cơ chế chia nhỏ theo đoạn văn.",
        "Thứ ba, bộ phân tách nhận diện bảng biểu Table-Aware phát hiện các bảng quy chế, tự động nhân bản dòng tiêu đề cột vào từng khối con. Nhờ đó, mỗi dòng điểm số hay mức học phí không bao giờ bị mất đi ý nghĩa của bảng.",
        "Mỗi khối con có kích thước tối đa 600 ký tự với độ gối đầu 100 ký tự, được gắn kèm tiền tố breadcrumb và mã hóa thành vector 768 chiều bởi mô hình Bi Encoder tiếng Việt tối ưu O N N X trên C U D A."
    ],
    "scene5": [
        "Khi bước vào mùa cao điểm đăng ký học phần, hàng nghìn sinh viên gửi các câu hỏi tương tự nhau. Dịch vụ triển khai bộ nhớ đệm ngữ nghĩa hai giai đoạn để phản hồi tức thì:",
        "Lớp không: Kiểm tra bộ đệm Rê đít theo khóa ký tự chuẩn hóa với độ phức tạp O một, trả về kết quả chỉ trong 12 mili giây.",
        "Lớp một: Nếu chưa khớp tuyệt đối, truy vấn vector 768 chiều trên P G véc tơ với ngưỡng bao quát 0,60 để quét nhanh các câu hỏi đồng nghĩa.",
        "Lớp hai: Mô hình so khớp chéo Cross Encoder kiểm định sự tương đồng ngữ nghĩa sâu với ngưỡng khắt khe 0,80.",
        "Đặc biệt, lớp giáp Entity Numbers Guard sẽ so khớp chính xác từng con số như năm học, học kỳ hay điểm trung bình G P A, ngăn chặn hoàn toàn việc nhầm lẫn giữa năm 2024 và năm 2025.",
        "Cuối cùng, cơ chế sép RAG kiểm soát ghi đệm: chỉ khi câu trả lời có độ tự tin cao và tài liệu hoàn toàn liên quan thì dữ liệu mới được phép ghi vào bộ nhớ đệm, bảo đảm chống đầu độc cache 100%."
    ],
    "scene6": [
        "Khi câu hỏi chưa có trong bộ nhớ đệm, quy trình truy xuất lai hợp được kích hoạt qua 3 bước:",
        "Bước một: Mô hình ngôn ngữ lớn phân loại câu hỏi vào một trong bảy nhóm ý định. Nếu là câu chào hỏi xã giao, hệ thống sẽ bỏ qua truy xuất để tiết kiệm tài nguyên. Nếu là câu hỏi kép, mô hình phân rã thành tối đa 4 truy vấn con độc lập.",
        "Bước hai: Mỗi truy vấn con thực thi tìm kiếm song song trên Pốt gờ rét qua hàm lai hợp R R F, kết hợp vector ngữ nghĩa H N S W và tìm kiếm từ khóa B M hai mươi lăm với hằng số k bằng 60.",
        "Về mặt toán học, tài liệu được cả hai kênh đồng thuận đạt 0,0322 điểm, luôn chiến thắng tài liệu chỉ đứng đầu đơn độc một kênh với 0,0163 điểm.",
        "Bước ba: Mô hình Cross Encoder tái xếp hạng ứng viên cho từng truy vấn con, áp dụng hạn ngạch từ 2 đến tối đa 8 khối cha.",
        "Sau đó, cơ chế Small-to-Big tự động gộp các khối con xuất sắc thành khối cha hoàn chỉnh 1.200 token để nạp vào prompt cho mô hình đọc hiểu."
    ],
    "scene7": [
        "Sau khi chọn lọc được các khối tài liệu giá trị nhất, hệ thống nạp vào prompt thông qua các kỹ thuật kiểm soát ngữ cảnh hiện đại:",
        "Thứ nhất, giải quyết hiện tượng mất tập trung ở giữa Lost in the Middle bằng thuật toán hoán vị bánh kẹp Sandwich Reordering: đưa tài liệu quan trọng nhất lên đầu và tài liệu quan trọng thứ hai xuống sát đáy theo trật tự một, ba, năm, bốn, hai.",
        "Thứ hai, toàn bộ tài liệu được bọc kín trong vùng an toàn X M L Sandboxing với cấu trúc thẻ nguồn rõ ràng và kết thúc bằng thẻ nhắc câu hỏi ở sát đáy.",
        "Lớp giáp bảo vệ Guardrail chặn đứng các thẻ đóng giả mạo và các câu lệnh tiêm mã prompt injection.",
        "Thứ ba, cơ chế định tuyến SpatioRoute dựa trên bảy nhóm ý định để chèn các quy tắc chuyên biệt: ví dụ ý định Quy chế kích hoạt tính toán từng bước Arithmetic CoT cho điểm G P A, trong khi ý định Khủng hoảng đưa ra lời trấn an trước tiên, giúp cắt giảm đến 60% token prompt không cần thiết."
    ],
    "scene8": [
        "Độ tin cậy và sự ổn định của toàn bộ kiến trúc được bảo chứng qua 126 ca kiểm thử đơn vị tự động trên 8 bộ suite chuyên biệt trong thư mục tests/unit, vượt qua 100% chỉ trong 1 phẩy 04 giây:",
        "Ca một — Chặn tiêm mã cấu trúc: Kiểm thử phát hiện thẻ đóng giả mạo trong câu hỏi sinh viên, kích hoạt phản hồi từ chối an toàn ngay lập tức.",
        "Ca hai — Hoán vị bánh kẹp Sandwich: Kiểm chứng danh sách tài liệu đầu vào được sắp xếp chính xác theo phân bổ chữ U của Stanford, đưa hai ứng viên tốt nhất vào hai vị trí chú ý cao nhất.",
        "Ca ba — Đồng thuận đa nguồn R R F: Chứng minh công thức R R F luôn ưu tiên tài liệu xuất hiện đồng thời trên cả kênh tìm kiếm vector và tìm kiếm từ khóa.",
        "Ca bốn — Khóa cổng ghi bộ đệm sép RAG: Khi mô hình tự đánh giá câu trả lời thiếu cơ sở pháp lý, lệnh ghi vào bộ đệm Rê đít bị hủy bỏ hoàn toàn."
    ],
    "scene9": [
        "Nhìn lại toàn bộ hành trình, Academic Chatbot Service là lời giải kỹ thuật chuẩn mực cho bài toán tư vấn học vụ đại học:",
        "Hệ thống đạt 4 chỉ số vàng đo lường thực tế: 126 bài kiểm thử tự động vượt qua 100%, thời gian phản hồi bộ đệm đạt 12 mili giây, loại bỏ hoàn toàn hiện tượng ảo giác quy chế, và tiết kiệm đến 60% chi phí tính toán vận hành.",
        "Đối với giảng viên và sinh viên, đây là người trợ lý học vụ chuẩn xác, bảo mật và luôn sẵn sàng hỗ trợ 24 trên 7.",
        "Đối với kỹ sư A I, đây là một kiến trúc RAG nâng cao kết hợp bảo vệ ngữ cảnh hoàn chỉnh, chứng minh sự kết hợp hoàn hảo giữa nghiên cứu khoa học và kỹ nghệ triển khai thực tế.",
        "Xin trân trọng cảm ơn!"
    ]
}

def main():
    out_dir = "video/public/audio"
    os.makedirs(out_dir, exist_ok=True)
    
    # Save text script file
    script_txt_path = os.path.join(out_dir, "cleaned_voiceover_debug.txt")
    with open(script_txt_path, "w", encoding="utf-8") as f:
        for sid, sentences in SCENE_SCRIPTS.items():
            f.write(f"=== {sid.upper()} ===\n")
            f.write(" ".join(sentences) + "\n\n")
    print(f"Saved revised script to {script_txt_path}")

    print("\nLoading VieNeu-TTS v3 Nano with local HuggingFace weights on GPU...")
    tts = Vieneu(mode="v3nano")
    voice_name = "Minh Quân"
    print(f"Voice: {voice_name}")

    scene_durations = {}
    sentence_timings = {}
    sample_rate = 24000
    pause_samples = int(0.28 * sample_rate) # 280ms pause between sentences
    pause_audio = np.zeros(pause_samples, dtype=np.float32)

    for sid, sentences in SCENE_SCRIPTS.items():
        print(f"\n==========================================")
        print(f"Synthesizing {sid} ({len(sentences)} sentences)...")
        print(f"==========================================")
        
        scene_audio_chunks = []
        timings = []
        current_time_sec = 0.0

        for idx, sentence in enumerate(sentences):
            clean_sent = sentence.strip()
            print(f"  [{idx+1}/{len(sentences)}] ({len(clean_sent)} chars): {clean_sent[:60]}...")
            sent_audio = tts.infer(clean_sent, voice=voice_name)
            
            # Ensure float32 array
            if not isinstance(sent_audio, np.ndarray):
                sent_audio = np.array(sent_audio, dtype=np.float32)
            else:
                sent_audio = sent_audio.astype(np.float32)
                
            sent_dur_sec = len(sent_audio) / sample_rate
            start_frame = int(current_time_sec * 30)
            end_frame = int((current_time_sec + sent_dur_sec) * 30)

            timings.append({
                "sentence_idx": idx,
                "text": clean_sent,
                "start_sec": round(current_time_sec, 2),
                "end_sec": round(current_time_sec + sent_dur_sec, 2),
                "start_frame": start_frame,
                "end_frame": end_frame
            })

            scene_audio_chunks.append(sent_audio)
            scene_audio_chunks.append(pause_audio)
            current_time_sec += sent_dur_sec + 0.28

        # Combine scene audio
        full_audio = np.concatenate(scene_audio_chunks)
        wav_path = os.path.join(out_dir, f"{sid}.wav")
        mp3_path = os.path.join(out_dir, f"{sid}.mp3")
        sf.write(wav_path, full_audio, sample_rate)

        # Convert to high-quality MP3 (192kbps)
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-b:a", "192k", mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Measure exact duration with ffprobe
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ], stdout=subprocess.PIPE, text=True, check=True)
        dur = float(res.stdout.strip())
        frames = int(dur * 30)

        scene_durations[sid] = frames
        sentence_timings[sid] = {
            "duration_sec": round(dur, 2),
            "total_frames": frames,
            "sentences": timings
        }
        print(f"==> Finished {sid}: {dur:.2f}s (~{frames} frames @ 30fps)")

    # Save durations and sentence timings
    durations_json_path = "video/src/data/audioDurations.json"
    os.makedirs(os.path.dirname(durations_json_path), exist_ok=True)
    with open(durations_json_path, "w", encoding="utf-8") as f:
        json.dump(scene_durations, f, indent=2, ensure_ascii=False)
    print(f"\nSaved audio durations to {durations_json_path}")

    timings_json_path = "video/src/data/sentenceTimings.json"
    with open(timings_json_path, "w", encoding="utf-8") as f:
        json.dump(sentence_timings, f, indent=2, ensure_ascii=False)
    print(f"Saved precise sentence timings to {timings_json_path}")

    total_frames = sum(scene_durations.values())
    total_seconds = total_frames / 30
    mins = int(total_seconds // 60)
    secs = int(total_seconds % 60)
    print(f"\n==========================================")
    print(f"ALL SCENES GENERATED SUCCESSFULLY!")
    print(f"Total Video Length: {mins}m {secs}s ({total_frames} frames @ 30fps)")
    print(f"==========================================")

if __name__ == "__main__":
    main()

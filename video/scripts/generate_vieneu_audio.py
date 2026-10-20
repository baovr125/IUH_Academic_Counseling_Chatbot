import os
import subprocess
import soundfile as sf
from vieneu import Vieneu

SCENE_SCRIPTS = {
    "scene1": (
        "Chào mừng quý thầy cô và các bạn. Tại Trường Đại học Công nghiệp Thành phố Hồ Chí Minh, "
        "với quy mô hàng chục ngàn sinh viên, việc tra cứu quy chế học vụ luôn là một trở ngại lớn. "
        "Các quy định thường xuyên được cập nhật theo từng năm, khiến sinh viên khóa cũ và khóa mới có những quy chế áp dụng hoàn toàn khác nhau. "
        "Nếu chỉ sử dụng một chatbot trí tuệ nhân tạo thông thường, hệ thống rất dễ bị ảo giác thông tin, nhầm lẫn giữa quy chế cũ và mới, "
        "hoặc tiêu tốn chi phí máy chủ khổng lồ. "
        "Chính vì vậy, chúng tôi đã phát triển hệ sinh thái AI Microservices hoàn chỉnh, "
        "mang đến sáu giải pháp kỹ thuật đột phá giúp sinh viên tra cứu chính xác, tức thì và hoàn toàn bảo mật."
    ),
    "scene2": (
        "Kiến trúc hệ thống được thiết kế theo chuẩn Clean Architecture gồm năm phân tầng rõ rệt. "
        "Đầu tiên, sinh viên tương tác qua giao diện web xây dựng bằng React mười tám, hiển thị mượt mà công thức toán học và trích dẫn điều khoản. "
        "Mọi yêu cầu gửi lên đều phải đi qua Kong API Gateway. Bạn có thể hình dung cổng này như một bác bảo vệ trường học thông minh, "
        "chịu trách nhiệm kiểm tra thẻ sinh viên, chặn đứng các cuộc tấn công phá hoại, rồi mới điều hướng vào bên trong. "
        "Ở trung tâm là Academic Chatbot Service, bộ não điều khiển toàn bộ quy trình trí tuệ nhân tạo, "
        "tự động định tuyến ý định câu hỏi và điều phối các mô hình ngôn ngữ lớn. "
        "Phía sau là cụm cơ sở dữ liệu phân tán: Redis đóng vai trò cuốn sổ ghi nhớ tốc độ cao, "
        "và PostgreSQL lưu trữ các vector ngữ nghĩa một nghìn không trăm hai mươi bốn chiều. "
        "Hệ thống còn mở rộng với cụm Celery Worker chạy ngầm, hàng đợi RabbitMQ và bộ lưu trữ MinIO, "
        "giúp xử lý các tệp tài liệu phức tạp mà không làm nghẽn máy chủ."
    ),
    "scene3": (
        "Hãy cùng theo dõi luồng di chuyển của dữ liệu qua một ví dụ thực tế: "
        "Sinh viên khóa hai mươi mốt hỏi: Em bị điểm C môn Triết, điểm trung bình tính thế nào và có được học vượt không? "
        "Bước một: Câu hỏi kèm mã định danh được gửi từ trình duyệt qua cổng bảo mật Kong. "
        "Bước hai: Cổng Kong xác thực hợp lệ và chuyển tiếp câu hỏi đến dịch vụ Chatbot. "
        "Bước ba: Hệ thống kiểm tra cuốn sổ nhớ Redis bằng bộ đệm ngữ nghĩa hai giai đoạn. "
        "Nhờ mô hình Cross-Encoder kiểm chứng chặt chẽ, các câu hỏi đảo nghĩa như được phép hay bị cấm sẽ không bao giờ bị trả lời nhầm lẫn. "
        "Bước bốn: Nếu chưa có trong bộ đệm, hệ thống thực hiện tìm kiếm lai phân cấp trong PostgreSQL, "
        "kết hợp tìm kiếm từ khóa và vector ngữ nghĩa để chọn ra các điều luật chính xác nhất. "
        "Bước năm: Các điều luật được sắp xếp lại theo thuật toán chiếc bánh kẹp Sandwich và bọc kín trong vùng an toàn để chống tấn công can thiệp mã độc. "
        "Bước sáu: Trí tuệ nhân tạo tự suy ngẫm trong thẻ nội bộ, tính toán từng bước công thức điểm số "
        "và truyền trực tiếp câu trả lời từng chữ về màn hình sinh viên qua Server-Sent Events."
    ),
    "scene4": (
        "Điểm sáng nổi bật của dự án nằm ở bốn file mã nguồn cốt lõi trong chuỗi commit mới nhất. "
        "Đầu tiên là file hybrid chunker. Thay vì cắt vụn văn bản làm mất tiêu đề điều luật, "
        "chúng tôi xây dựng cơ chế phân đoạn cha con: đoạn cha giữ trọn vẹn ngữ cảnh của điều luật, "
        "còn các đoạn con giúp tìm kiếm chính xác từng câu từ. "
        "Kế tiếp là file rag service với thuật toán Sandwich Reordering. "
        "Giống như trí nhớ con người thường nhớ rõ đầu câu và cuối câu nhưng hay quên đoạn giữa, "
        "thuật toán sẽ đưa hai tài liệu quan trọng nhất lên đầu và xuống cuối ngữ cảnh, triệt tiêu hiện tượng lơ là thông tin của mô hình. "
        "Tại file prompt templates, chúng tôi tối ưu mật độ câu từ, giúp cắt giảm đến sáu mươi tư phần trăm lượng token tiêu thụ, "
        "đồng thời bắt buộc mô hình phải giải thích từng bước tính điểm và khẳng định dứt khoát Được phép hay Không được phép. "
        "Cuối cùng là file query filter, lớp giáp an ninh bảo vệ hệ thống, "
        "ngăn chặn người dùng gửi các mã độc tiêm lệnh hoặc giả mạo các thẻ hệ thống của chatbot."
    ),
    "scene5": (
        "Nhờ những cải tiến kỹ thuật đồng bộ, hệ thống đã vượt qua toàn bộ một trăm hai mươi sáu bài kiểm thử tự động "
        "với tỷ lệ chính xác tuyệt đối một trăm phần trăm. "
        "Thời gian phản hồi khi trúng bộ đệm chỉ dưới hai mươi mili-giây, độ chính xác truy xuất tăng hơn hai mươi lăm phần trăm, "
        "và tiết kiệm gần năm trăm token trên mỗi câu hỏi quy chế. "
        "Hệ sinh thái AI Microservices không chỉ là một đồ án công nghệ, "
        "mà là một giải pháp hoàn chỉnh, an toàn và sẵn sàng phục vụ thực tế cho sinh viên Trường Đại học Công nghiệp Thành phố Hồ Chí Minh. "
        "Xin trân trọng cảm ơn quý thầy cô và các bạn đã theo dõi!"
    ),
}

def main():
    out_dir = "video/public/audio"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Loading VieNeu-TTS v3 Nano with local HuggingFace weights...")
    tts = Vieneu(mode="v3nano")
    voice_name = "Minh Quân"
    print(f"Using voice: {voice_name}")

    results = {}
    for scene_id, text in SCENE_SCRIPTS.items():
        print(f"\n--- Generating {scene_id} ---")
        wav_path = os.path.join(out_dir, f"{scene_id}.wav")
        mp3_path = os.path.join(out_dir, f"{scene_id}.mp3")
        
        # 1. Synthesize audio with VieNeu
        audio = tts.infer(text, voice=voice_name)
        tts.save(audio, wav_path)
        print(f"Generated WAV: {wav_path} ({os.path.getsize(wav_path)} bytes)")

        # 2. Convert to high-quality MP3 (192kbps) with ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-b:a", "192k", mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Converted to MP3: {mp3_path} ({os.path.getsize(mp3_path)} bytes)")

        # 3. Measure duration with ffprobe
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ], stdout=subprocess.PIPE, text=True, check=True)
        dur = float(res.stdout.strip())
        frames = int(dur * 30)
        results[scene_id] = {"duration": dur, "frames": frames}
        print(f"{scene_id}: {dur:.2f}s (~{frames} frames @ 30fps)")

    print("\n=== GENERATION SUMMARY ===")
    total_frames = 0
    for sid, info in results.items():
        print(f"{sid}: {info['duration']:.2f}s -> {info['frames']} frames")
        total_frames += info["frames"]
    print(f"Total video length: {total_frames / 30:.2f}s ({total_frames} frames)")

if __name__ == "__main__":
    main()

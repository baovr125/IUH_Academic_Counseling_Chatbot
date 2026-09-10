import os
import tempfile
import asyncio
from app.utils.logger import logger
from app.services.minio_client import upload_audio
from app.services.supabase_client import get_supabase

async def generate_audio_for_entries(entries: list):
    """
    Tiến trình chạy ngầm: Nhận danh sách các từ vựng mới import.
    Với mỗi từ, tạo audio bằng edge-tts, upload lên MinIO và update Supabase.
    """
    if not entries:
        return
        
    logger.info(f"Background Task: Đang xử lý sinh audio cho {len(entries)} từ vựng...")
    supabase = get_supabase()
    
    # Do edge-tts CLI tool runs asynchronously, we can use asyncio.create_subprocess_exec
    for entry in entries:
        word_id = entry.get("id")
        word_text = entry.get("word")
        audio_url = entry.get("audio_url")
        
        # Bỏ qua nếu đã có audio
        if audio_url or not word_id or not word_text:
            continue
            
        try:
            # Tạo file tạm để lưu mp3
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                
            # Sử dụng edge-tts CLI command
            # Giọng đọc chuẩn Anh-Mỹ: en-US-AriaNeural hoặc en-US-GuyNeural
            voice = "en-US-AriaNeural"
            
            process = await asyncio.create_subprocess_exec(
                "edge-tts",
                "--voice", voice,
                "--text", word_text,
                "--write-media", temp_audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Đọc file mp3
                with open(temp_audio_path, "rb") as f:
                    audio_bytes = f.read()
                
                # Upload lên MinIO
                # Tên file: word_id.mp3 để đảm bảo unique
                file_name = f"{word_id}.mp3"
                minio_url = upload_audio(file_name, audio_bytes)
                
                if minio_url and supabase:
                    # Update Supabase
                    supabase.table("domain_dictionaries").update({"audio_url": minio_url}).eq("id", word_id).execute()
                    logger.info(f"Đã tạo audio thành công cho từ: {word_text}")
                else:
                    logger.error(f"Tạo audio thất bại hoặc upload MinIO thất bại cho từ: {word_text}")
            else:
                logger.error(f"Lỗi edge-tts cho từ {word_text}: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Lỗi không xác định khi tạo audio cho từ {word_text}: {e}")
        finally:
            # Xóa file tạm
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                
        # Nghỉ 0.5s giữa các từ để tránh block resource / spam API
        await asyncio.sleep(0.5)

    logger.info("Background Task: Hoàn tất sinh audio.")

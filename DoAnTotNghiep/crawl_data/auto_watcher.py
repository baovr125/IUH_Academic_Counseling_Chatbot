import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import các biến và hàm từ file chatbot_core.py
from retrival import index, update_document

# Thư mục chứa các file JSON nhỏ
WATCH_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\data_json\json_documents"
os.makedirs(WATCH_DIR, exist_ok=True)

class RagDataHandler(FileSystemEventHandler):
    def process_file(self, file_path):
        print(f"\n[WATCHER] Phát hiện thay đổi ở file: {os.path.basename(file_path)}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_chunks_data = json.load(f)
            
            if new_chunks_data:
                source_url = new_chunks_data[0].get("metadata", {}).get("source_url")
                if source_url:
                    print(f"[WATCHER] Đang cập nhật Database cho URL: {source_url}...")
                    update_document(index, new_chunks_data, source_url)
                else:
                    print(f"[WATCHER] ⚠️ Lỗi: Không tìm thấy 'source_url' trong {file_path}")
        except Exception as e:
            print(f"[WATCHER] ❌ Lỗi xử lý: {e}")

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"\n[WATCHER] 🟢 FILE MỚI: {os.path.basename(event.src_path)}")
            time.sleep(1) # Chờ ghi xong file
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            print(f"\n[WATCHER] 🟡 FILE CẬP NHẬT: {os.path.basename(event.src_path)}")
            time.sleep(1)
            self.process_file(event.src_path)

def start_watching():
    print("="*60)
    print("👀 RAG WATCHER ĐÃ KHỞI ĐỘNG (Chạy ngầm 24/7)")
    print(f"Đang giám sát: {WATCH_DIR}")
    print("="*60)
    
    event_handler = RagDataHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[WATCHER] Đã dừng giám sát.")
    observer.join()

if __name__ == "__main__":
    start_watching()
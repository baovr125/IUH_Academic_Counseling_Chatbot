import os
import json
import chromadb
import uvicorn
import threading
import glob
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# LlamaIndex core
from llama_index.core import Settings, VectorStoreIndex, StorageContext, PromptTemplate
from llama_index.core.schema import TextNode
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# =====================================================================
# 1. CẤU HÌNH LLM & EMBEDDING
# =====================================================================
print("-> Đang khởi tạo mô hình AI (Qwen3)...")
Settings.llm = Ollama(
    model="qwen3:8b", 
    request_timeout=180.0,
    additional_kwargs={"num_gpu": 99} # Tối ưu hóa cho GPU Tesla T4 trên Kaggle
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device="cuda" # Sử dụng CUDA để tăng tốc độ nhúng vector
)

# =====================================================================
# 2. KẾT NỐI CHROMADB & NẠP DỮ LIỆU BAN ĐẦU
# =====================================================================
print("-> Đang kết nối tới ChromaDB...")
DB_DIR = "/kaggle/working/chatbox_IUH/chroma_db"
JSON_DIR = "/kaggle/working/chatbox_IUH/data_json/json_documents"

db = chromadb.PersistentClient(path=DB_DIR)
chroma_collection = db.get_or_create_collection("camnang_iuh")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

if chroma_collection.count() == 0:
    print(f"-> Database trống. Đang quét thư mục: {JSON_DIR}")
    json_files = glob.glob(os.path.join(JSON_DIR, "*.json"))
    
    if not json_files:
        print("⚠️ CẢNH BÁO: Không tìm thấy file JSON nào! Server sẽ khởi chạy với Index trống.")
        index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)
    else:
        all_nodes = []
        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as f:
                children_data = json.load(f)
                for item in children_data:
                    raw_meta = item.get("metadata", {})
                    clean_meta = {}
                    for key, value in raw_meta.items():
                        if isinstance(value, list):
                            clean_meta[key] = " > ".join(str(x) for x in value)
                        else:
                            clean_meta[key] = str(value) if value is not None else "None"

                    node = TextNode(
                        id_=item.get("id"),
                        text=item.get("text", ""),
                        metadata=clean_meta
                    )
                    all_nodes.append(node)
        
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(all_nodes, storage_context=storage_context, embed_model=Settings.embed_model)
        print(f"✅ Đã nạp thành công {len(all_nodes)} chunks vào Database!")
else:
    print(f"-> Đã load {chroma_collection.count()} chunks từ Database (Bản ghi cũ).")
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)

# =====================================================================
# 3. KHỞI TẠO QUERY ENGINE
# =====================================================================
qa_prompt_tmpl_str = (
    "Bạn là chuyên viên tư vấn học vụ ảo nhiệt tình, thân thiện của Trường Đại học Công nghiệp TP.HCM (IUH).\n"
    "Nhiệm vụ: Giải đáp thắc mắc của sinh viên dựa HOÀN TOÀN vào ngữ cảnh được cung cấp.\n"
    "Yêu cầu:\n"
    "- Trả lời chi tiết, rõ ràng, dễ hiểu.\n"
    "- Sử dụng gạch đầu dòng cho các điều kiện hoặc các bước thực hiện.\n"
    "- Nếu không có thông tin, hãy hướng dẫn sinh viên liên hệ Phòng Đào tạo (Nhà A).\n"
    "- Tuyệt đối không tự bịa thông tin không có trong tài liệu.\n\n"
    "Ngữ cảnh từ cẩm nang:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Câu hỏi của sinh viên: {query_str}\n"
    "Trả lời chi tiết:"
)
qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

query_engine = index.as_query_engine(similarity_top_k=3)
query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})

# =====================================================================
# 4. HÀM CẬP NHẬT DỮ LIỆU ĐỘNG (HOT-SWAP VÀ REFRESH AI)
# =====================================================================
def update_document(target_index, new_chunks_data, source_url):
    global query_engine # Quan trọng: Gọi biến toàn cục để Refresh lại miệng AI
    
    print(f"\n[RETRIVAL] Đang tiến hành tích hợp tri thức nóng cho URL: {source_url}")
    try:
        # Lấy Chroma collection gốc
        v_store = target_index.storage_context.vector_store
        c_collection = v_store.chroma_collection if hasattr(v_store, "chroma_collection") else v_store._collection
            
        # Tìm và xóa dữ liệu cũ của URL này để tránh AI bị rối
        existing_data = c_collection.get(where={"source_url": source_url})
        existing_ids = existing_data.get("ids", [])
        
        if existing_ids:
            print(f"[RETRIVAL] 🟡 Phát hiện {len(existing_ids)} phân mảnh cũ của trang này. Đang tiến hành dọn dẹp...")
            target_index.delete_nodes(existing_ids)
            print("[RETRIVAL] ✅ Đã dọn dẹp xong dữ liệu cũ.")
        else:
            print("[RETRIVAL] 🟢 Không có dữ liệu cũ cần dọn dẹp (Đây là bài viết mới).")
            
        # Đóng gói dữ liệu mới thành Node
        new_nodes = []
        for item in new_chunks_data:
            raw_meta = item.get("metadata", {})
            clean_meta = {}
            for key, value in raw_meta.items():
                if isinstance(value, list):
                    clean_meta[key] = " > ".join(str(x) for x in value)
                else:
                    clean_meta[key] = str(value) if value is not None else "None"
                    
            node = TextNode(
                id_=item.get("id"),
                text=item.get("text", ""),
                metadata=clean_meta
            )
            new_nodes.append(node)
            
        # Bơm thẳng vào Index đang chạy trên RAM
        if new_nodes:
            print(f"[RETRIVAL] Đang mã hóa và nhét {len(new_nodes)} phân mảnh mới vào bộ nhớ...")
            target_index.insert_nodes(new_nodes)
            
            # --- BƯỚC QUYẾT ĐỊNH ---
            # Làm mới lại (Refresh) Query Engine để AI lập tức xài kiến thức mới
            query_engine = target_index.as_query_engine(similarity_top_k=4)
            query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
            
            print(f"[RETRIVAL] 🎉 THÀNH CÔNG: Hệ thống AI đã học xong và được Refresh bộ nhớ!")
    except Exception as e:
        print(f"[RETRIVAL] ❌ Lỗi xử lý cập nhật tri thức: {e}")

# =====================================================================
# 5. THIẾT LẬP FASTAPI SERVER
# =====================================================================
app = FastAPI(title="IUH Chatbot API - Final Version")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        response = query_engine.query(req.message)
        urls_seen = set()
        if response.source_nodes:
            for node in response.source_nodes:
                url = node.metadata.get("source_url")
                if url and url != "unknown_url":
                    urls_seen.add(url)
        
        reply_text = response.response
        if urls_seen:
            reply_text += "\n\n🔗 **Nguồn tham khảo chi tiết:**\n"
            for url in urls_seen:
                reply_text += f"👉 [{url}]({url})\n"
        
        return {
            "reply": reply_text,
            "sources": list(urls_seen)
        }
    except Exception as e:
        print(f"Lỗi Chat API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/judge")
async def judge_endpoint(req: ChatRequest):
    try:
        response = Settings.llm.complete(req.message)
        return {"reply": str(response.text)}
    except Exception as e:
        print(f"Lỗi Judge API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 6. CƠ CHẾ WATCHER TỰ ĐỘNG (Bắt CẢ LỖI SỬA LẪN FILE MỚI)
# =====================================================================
class APIRagHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_processed = {} # Chống việc hệ điều hành gọi 2 lần liên tục

    def process_event(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
            
        # Kỹ thuật Debounce: Chống việc nháy file (File vừa Create xong lại Modified ngay lập tức)
        current_time = time.time()
        if event.src_path in self.last_processed:
            if current_time - self.last_processed[event.src_path] < 5: # Chặn 5 giây
                return
        self.last_processed[event.src_path] = current_time

        print(f"\n[HOT RELOAD] 🟡 Đã bắt được file tài liệu: {os.path.basename(event.src_path)}")
        time.sleep(2) # Chờ 2 giây để file JSON được lưu xong xuống đĩa hoàn toàn
        try:
            with open(event.src_path, 'r', encoding='utf-8') as f:
                new_chunks_data = json.load(f)
            
            if new_chunks_data:
                source_url = new_chunks_data[0].get("metadata", {}).get("source_url")
                if source_url:
                    update_document(index, new_chunks_data, source_url)
        except Exception as e:
            print(f"[HOT RELOAD] ❌ Lỗi bóc tách file JSON bối cảnh: {e}")

    # Bắt cả sự kiện sửa file (File cũ ghi đè)
    def on_modified(self, event):
        self.process_event(event)

    # Bắt cả sự kiện tạo file (File mới toanh)
    def on_created(self, event):
        self.process_event(event)

# Khởi chạy hệ thống chính
if __name__ == "__main__":
    print("👀 Kích hoạt cơ chế Dynamic RAG Watcher chia sẻ bộ nhớ...")
    watcher_handler = APIRagHandler()
    observer = Observer()
    observer.schedule(watcher_handler, JSON_DIR, recursive=False)
    observer.start()

    try:
        print("🚀 Server FastAPI đang khởi chạy tại port 8000...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        observer.stop()
        observer.join()

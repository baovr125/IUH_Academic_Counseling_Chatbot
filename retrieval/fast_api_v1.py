import os
import uvicorn
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# LlamaIndex core
from llama_index.core import Settings, VectorStoreIndex, PromptTemplate
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
    additional_kwargs={"num_gpu": 99}
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device="cpu"
)

# # =====================================================================
# # 2. KẾT NỐI CHROMADB (CHỈ ĐỌC DỮ LIỆU)
# # =====================================================================
# print("-> Đang kết nối tới ChromaDB...")
# DB_DIR = "G:\Khoa_Luan\Source_code\data\chroma_db"

# db = chromadb.PersistentClient(path=DB_DIR)
# chroma_collection = db.get_collection("camnang_iuh") # Chỉ lấy collection ra, không cần create
# vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# # Load thẳng Index từ Vector Store
# index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)
# print(f"✅ Đã kết nối thành công! Đang có {chroma_collection.count()} chunks trong Database.")
# =====================================================================
# 2. KẾT NỐI CHROMADB (CHỈ ĐỌC DỮ LIỆU)
# =====================================================================
print("-> Đang kết nối tới ChromaDB...")

# 1. Đổi lại đúng đường dẫn ổ G của bạn
DB_DIR = r"G:\Khoa_Luan\Source_code\data\chroma_db" 

db = chromadb.PersistentClient(path=DB_DIR)

# 2. Đổi lại đúng tên Collection đã tạo ở Step 2
chroma_collection = db.get_collection("camnang_iuh_collection") 

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# Load thẳng Index từ Vector Store
index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)
print(f"✅ Đã kết nối thành công! Đang có {chroma_collection.count()} chunks trong Database.")

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
# 4. THIẾT LẬP FASTAPI SERVER
# =====================================================================
app = FastAPI(title="IUH Chatbot API - Siêu nhẹ")

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
                if url and url != "unknown_url" and url != "None":
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Server FastAPI đang khởi chạy tại port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
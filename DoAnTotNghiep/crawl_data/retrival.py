import os
import json
import chromadb
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.vector_stores.chroma import ChromaVectorStore

# =====================================================================
# 1. CẤU HÌNH TỐI ƯU CHO LEGION 5 (GPU 8GB)
# =====================================================================
print("-> Đang khởi tạo LLM và Embedding Model (Ép chạy trên GPU)...")

# Cấu hình LLM
Settings.llm = Ollama(
    model="qwen3:8b", # Bạn có thể đổi sang qwen2.5:3b nếu muốn
    request_timeout=180.0,
    additional_kwargs={"num_gpu": 99} # Ép nạp tối đa vào GPU
)

# Cấu hình Embedding (Thêm device="cuda" để tăng tốc cực độ)
# Lưu ý: Cần cài đặt PyTorch bản có CUDA (như đã trao đổi) để dòng này hoạt động mượt mà
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device="cpu" 
)

# =====================================================================
# 2. HÀM HỖ TRỢ: LÀM PHẲNG METADATA (CHROMA DB FIX)
# =====================================================================
def sanitize_metadata(meta):
    """
    ChromaDB chỉ chấp nhận metadata là str, int, float, hoặc None.
    Hàm này sẽ ép kiểu các list hoặc dict thành chuỗi (string) để tránh lỗi ValueError.
    """
    sanitized = {}
    if not meta:
        return sanitized
        
    for k, v in meta.items():
        if isinstance(v, (str, int, float)) or v is None:
            sanitized[k] = v
        elif isinstance(v, list):
            sanitized[k] = ", ".join([str(x) for x in v])
        elif isinstance(v, dict):
            sanitized[k] = json.dumps(v, ensure_ascii=False)
        else:
            sanitized[k] = str(v)
    return sanitized

# =====================================================================
# 3. KHỞI TẠO CHROMADB (LƯU TRỮ VĨNH VIỄN)
# =====================================================================
# ĐƯỜNG DẪN THƯ MỤC DATABASE
DB_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\chroma_db"
os.makedirs(DB_DIR, exist_ok=True)

db = chromadb.PersistentClient(path=DB_DIR)
chroma_collection = db.get_or_create_collection("camnang_iuh")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# =====================================================================
# 4. CÁC HÀM XỬ LÝ DỮ LIỆU ĐỘNG (DYNAMIC RAG CRUD)
# =====================================================================
def build_initial_index(json_path):
    print("-> Đang build Index lần đầu tiên vào ChromaDB...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = []
    for item in data:
        raw_metadata = item.get("metadata", {})
        source_url = raw_metadata.get("source_url", "unknown_url")
        
        # Làm phẳng metadata trước khi đưa vào Node
        clean_metadata = sanitize_metadata(raw_metadata)
        
        node = TextNode(text=item.get("text", ""), metadata=clean_metadata)
        
        # Gắn ID tài liệu gốc thông qua NodeRelationship (Cách mới của LlamaIndex)
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=source_url)
        
        # Loại trừ một số trường không cần thiết cho LLM
        node.excluded_embed_metadata_keys = ["source_url", "page", "llm_summary"]
        node.excluded_llm_metadata_keys = ["page", "llm_summary", "llm_qa", "llm_custom"] 
        
        nodes.append(node)
        
    index = VectorStoreIndex(nodes, storage_context=storage_context)
    print(f"-> Đã insert {len(nodes)} chunks vào DB.")
    return index

def delete_document(index, source_url):
    """Xóa toàn bộ các chunks liên quan đến một URL"""
    try:
        index.delete_ref_doc(source_url, delete_from_docstore=True)
        print(f"Đã xóa tài liệu cũ: {source_url}")
    except Exception as e:
        print(f"Lỗi khi xóa (có thể tài liệu chưa tồn tại): {e}")

def update_document(index, new_chunks_data, source_url):
    """Cập nhật một tài liệu: Xóa cái cũ -> Insert cái mới"""
    delete_document(index, source_url)
    
    new_nodes = []
    for item in new_chunks_data:
        raw_metadata = item.get("metadata", {})
        clean_metadata = sanitize_metadata(raw_metadata)
        
        node = TextNode(text=item.get("text", ""), metadata=clean_metadata)
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=source_url)
        new_nodes.append(node)
        
    index.insert_nodes(new_nodes)
    print(f"Đã cập nhật thành công nội dung mới cho: {source_url}")

# =====================================================================
# 5. TẢI HOẶC LOAD INDEX TỪ CHROMA DB
# =====================================================================
if chroma_collection.count() == 0:
    DATA_PATH = r"G:\ChatBot\Code\Version1\chatbox_IUH\data_json2\camnang_enriched_chunks_data.json"
    index = build_initial_index(DATA_PATH)
else:
    print(f"-> Đã load {chroma_collection.count()} chunks từ Database (Không cần nhúng lại!)")
    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=Settings.embed_model
    )

# =====================================================================
# 6. KHỞI TẠO CHAT ENGINE TỐI ƯU TỐC ĐỘ (STREAMING & ĐỘ CHÍNH XÁC)
# =====================================================================
memory = ChatMemoryBuffer.from_defaults(token_limit=2000)

# Prompt mới: Bắt buộc LLM dựa vào Context và cấm tự bịa link
SYSTEM_PROMPT = (
    "Bạn là Ad - tư vấn viên học vụ thân thiện của IUH. "
    "Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên DỰA HOÀN TOÀN VÀO NGỮ CẢNH ĐƯỢC CUNG CẤP. "
    "Nếu thông tin trong ngữ cảnh không đủ để trả lời, hãy trung thực nói: 'Ad không tìm thấy thông tin này trong hệ thống'. "
    "Trình bày câu trả lời rõ ràng, dễ hiểu, dùng gạch đầu dòng nếu cần thiết. "
    "TUYỆT ĐỐI KHÔNG tự bịa ra thông tin và KHÔNG tự tạo đường link."
)

# Dùng chat_mode="context" siêu nhanh, bỏ qua bước Condense tốn thời gian
chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=SYSTEM_PROMPT,
    similarity_top_k=4 # Tăng top_k lên 4 để Ad IUH có nhiều ngữ cảnh hơn
)

# =====================================================================
# 7. GIAO DIỆN TERMINAL (CÓ TRÍCH XUẤT NGUỒN CHUẨN XÁC) 
# =====================================================================
def start_app():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*70)
    print("🤖 CHATBOT IUH - DYNAMIC RAG LOCAL (TRÍCH DẪN NGUỒN CHUẨN XÁC)")
    print("="*70)

    while True:
        user_input = input("\nSinh viên: ").strip()
        if user_input.lower() in ['exit', 'thoát', 'quit', 'q']: 
            print("Tạm biệt!")
            break
        if not user_input: continue

        print("-" * 70)
        print("🤖 Ad trả lời: ", end="")
        
        try:
            # Dùng Stream Chat để gõ từng chữ ngay lập tức, chống Timeout
            streaming_response = chat_engine.stream_chat(user_input)
            
            # 1. In ra câu trả lời của LLM
            for token in streaming_response.response_gen:
                print(token, end="", flush=True)
            
            # 2. Dùng Python bóc tách Nguồn (URL) chuẩn 100% từ Retriever
            print("\n\n🔗 Nguồn tham khảo chi tiết:")
            source_nodes = streaming_response.source_nodes
            urls_seen = set() # Tránh in trùng lặp URL
            
            if source_nodes:
                for node in source_nodes:
                    url = node.metadata.get("source_url")
                    if url and url != "unknown_url" and url not in urls_seen:
                        print(f"  👉 {url}")
                        urls_seen.add(url)
                
                if not urls_seen:
                    print("  (Không có link cụ thể cho phần này)")
            else:
                print("  (Không sử dụng tài liệu từ hệ thống)")
            
            print("-" * 70)
            
        except Exception as e:
            print(f"\n[LỖI QUÁ TRÌNH TRẢ LỜI]: {str(e)}")

if __name__ == "__main__":
    start_app()
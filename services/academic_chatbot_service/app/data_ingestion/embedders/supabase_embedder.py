import os
import json
import uuid
import hashlib
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from app.data_ingestion.utils.logger import setup_logger
from app.services.supabase_client import get_supabase_client

logger = setup_logger("embedder", "embedder.log")

def inject_meta(text, meta):
    breadcrumbs = meta.get("breadcrumbs", "")
    title = meta.get("title", "")
    headers = meta.get("headers", [])
    
    prefix_parts = []
    if breadcrumbs:
        prefix_parts.append(f"Đường dẫn: {breadcrumbs}")
    if headers:
        headers_str = " > ".join([h.replace("#", "").strip() for h in headers])
        prefix_parts.append(f"Mục: {headers_str}")
    elif title:
        prefix_parts.append(f"Mục: {title}")
        
    if prefix_parts:
        prefix = "[" + " | ".join(prefix_parts) + "] "
    else:
        prefix = ""
        
    return prefix + text

class SupabaseEmbedder:
    def __init__(self, model_name="bkai-foundation-models/vietnamese-bi-encoder", embedder_instance=None):
        if embedder_instance:
            logger.info(f"Sử dụng mô hình nhúng đã tải sẵn từ bộ nhớ...")
            self.embedder = embedder_instance
        else:
            logger.info(f"Đang tải mô hình nhúng {model_name}...")
            self.embedder = SentenceTransformer(model_name)
            
        self.supabase = get_supabase_client()
        if not self.supabase:
            raise ValueError("Không thể kết nối Supabase REST API (kiểm tra SUPABASE_URL và SUPABASE_KEY).")
        
    def run_embedding(self, children_file_path):
        logger.info(f"Đọc dữ liệu từ {children_file_path}...")
        with open(children_file_path, 'r', encoding='utf-8') as f:
            children = json.load(f)
            
        if not children:
            logger.warning("Không có dữ liệu child chunks để embed.")
            return

        docs_map = {}
        for child in children:
            meta = child.get("metadata", {})
            source_url = meta.get("source_url", "unknown")
            if source_url not in docs_map:
                docs_map[source_url] = {
                    "title": meta.get("title", ""),
                    "breadcrumbs": meta.get("breadcrumbs", ""),
                    "chunks": []
                }
            docs_map[source_url]["chunks"].append(child)

        stats = {"added_or_updated_docs": 0, "embedded_chunks": 0}
        
        try:
            for source_url, doc_info in tqdm(docs_map.items(), desc="Nhúng và Lưu DB"):
                title = doc_info["title"]
                breadcrumbs = doc_info["breadcrumbs"]
                all_text = "".join(c["text"] for c in doc_info["chunks"])
                content_hash = hashlib.md5(all_text.encode('utf-8')).hexdigest()
                
                # 1. Upsert Document via REST API
                doc_payload = {
                    "title": title,
                    "source_url": source_url,
                    "breadcrumbs": breadcrumbs,
                    "content_hash": content_hash,
                    "chunk_count": len(doc_info["chunks"])
                }
                
                doc_res = self.supabase.table("documents").upsert(
                    doc_payload, on_conflict="source_url"
                ).execute()
                
                if not doc_res.data or len(doc_res.data) == 0:
                    logger.error(f"Không thể upsert document cho '{source_url}'")
                    continue
                    
                document_id = doc_res.data[0]["id"]
                stats["added_or_updated_docs"] += 1
                
                # 2. Xóa chunk cũ
                self.supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
                
                # 3. Chuẩn bị bulk insert chunks
                chunk_records = []
                chunks_batch = doc_info["chunks"]
                
                texts_to_embed = [inject_meta(c["text"], c.get("metadata", {})) for c in chunks_batch]
                vectors = self.embedder.encode(texts_to_embed, convert_to_numpy=True).tolist()
                
                for idx, (child, vector) in enumerate(zip(chunks_batch, vectors)):
                    injected_text = texts_to_embed[idx]
                    meta_cleaned = {k: (v if v is not None else "") for k, v in child.get("metadata", {}).items()}
                    tokens_count = len(child["text"].split())
                    
                    chunk_records.append({
                        "document_id": document_id,
                        "chunk_index": idx,
                        "content": child["text"],
                        "injected_content": injected_text,
                        "metadata": meta_cleaned,
                        "embedding": vector,
                        "tokens_count": tokens_count
                    })
                    
                # 4. Bulk Insert Chunks
                # We can insert in batches of 100 to avoid request size limits
                batch_size = 100
                for i in range(0, len(chunk_records), batch_size):
                    batch = chunk_records[i:i+batch_size]
                    self.supabase.table("document_chunks").insert(batch).execute()
                    
                stats["embedded_chunks"] += len(chunk_records)
                
            logger.info("✅ HOÀN TẤT NẠP VECTOR VÀO SUPABASE!")
            logger.info(f"📊 Kết quả: {stats['added_or_updated_docs']} Documents, {stats['embedded_chunks']} Chunks")
            return stats
            
        except Exception as e:
            logger.exception(f"Lỗi trong quá trình embed và nạp Supabase: {e}")
            raise

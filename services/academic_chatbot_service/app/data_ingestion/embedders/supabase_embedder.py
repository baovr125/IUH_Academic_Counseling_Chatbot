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
        
    def run_embedding(self, children_file_path, parents_file_path=None):
        logger.info(f"Đọc dữ liệu từ {children_file_path}...")
        with open(children_file_path, 'r', encoding='utf-8') as f:
            children = json.load(f)
            
        if not children:
            logger.warning("Không có dữ liệu child chunks để embed.")
            return

        # Auto-detect parents.json if not explicitly provided
        if not parents_file_path:
            candidate_parents = os.path.join(os.path.dirname(children_file_path), "parents.json")
            if os.path.exists(candidate_parents):
                parents_file_path = candidate_parents

        parents_map = {}
        if parents_file_path and os.path.exists(parents_file_path):
            logger.info(f"Đọc dữ liệu parent chunks từ {parents_file_path}...")
            with open(parents_file_path, 'r', encoding='utf-8') as f:
                parents_data = json.load(f)
            for p in parents_data:
                url = p.get("metadata", {}).get("source_url")
                if url:
                    parents_map.setdefault(url, []).append(p)
            logger.info(f"Đã tải {len(parents_data)} parent chunks cho {len(parents_map)} tài liệu.")

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

        stats = {"added_or_updated_docs": 0, "embedded_chunks": 0, "parent_sections": 0}
        
        try:
            for source_url, doc_info in tqdm(docs_map.items(), desc="Nhúng và Lưu DB (Parent-Child)"):
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
                
                # 2. Xóa các bản ghi cũ của document_id (document_parents & document_chunks)
                try:
                    self.supabase.table("document_parents").delete().eq("document_id", document_id).execute()
                except Exception:
                    pass
                self.supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
                
                # 3. Nạp document_parents và lập bản đồ parent_id (Local MD5 -> Database UUID)
                parent_id_map = {}
                doc_parents = parents_map.get(source_url, [])
                if doc_parents:
                    parent_records = []
                    for p_idx, p in enumerate(doc_parents):
                        headers = p.get("metadata", {}).get("headers", [])
                        header_path = " > ".join(headers) if headers else ""
                        meta_cleaned = {k: (v if v is not None else "") for k, v in p.get("metadata", {}).items()}
                        parent_records.append({
                            "document_id": document_id,
                            "parent_index": p_idx,
                            "header_path": header_path,
                            "content": p.get("text", ""),
                            "metadata": meta_cleaned
                        })
                    
                    # Insert parents in batches of 50
                    for pb in range(0, len(parent_records), 50):
                        pb_records = parent_records[pb:pb+50]
                        pb_orig = doc_parents[pb:pb+50]
                        p_res = self.supabase.table("document_parents").insert(pb_records).execute()
                        if p_res.data:
                            for p_db, p_item in zip(p_res.data, pb_orig):
                                parent_id_map[p_item.get("parent_id")] = p_db["id"]
                                stats["parent_sections"] += 1
                
                # 4. Chuẩn bị bulk insert child chunks (có gắn parent_id)
                chunk_records = []
                chunks_batch = doc_info["chunks"]
                
                texts_to_embed = [inject_meta(c["text"], c.get("metadata", {})) for c in chunks_batch]
                vectors = self.embedder.encode(texts_to_embed, convert_to_numpy=True).tolist()
                
                for idx, (child, vector) in enumerate(zip(chunks_batch, vectors)):
                    injected_text = texts_to_embed[idx]
                    meta_cleaned = {k: (v if v is not None else "") for k, v in child.get("metadata", {}).items()}
                    tokens_count = len(child["text"].split())
                    real_parent_id = parent_id_map.get(child.get("parent_id"))
                    
                    chunk_records.append({
                        "document_id": document_id,
                        "parent_id": real_parent_id,
                        "chunk_index": idx,
                        "content": child["text"],
                        "injected_content": injected_text,
                        "metadata": meta_cleaned,
                        "embedding": vector,
                        "tokens_count": tokens_count
                    })
                    
                # 5. Bulk Insert Chunks in batches of 100
                batch_size = 100
                for i in range(0, len(chunk_records), batch_size):
                    batch = chunk_records[i:i+batch_size]
                    self.supabase.table("document_chunks").insert(batch).execute()
                    
                stats["embedded_chunks"] += len(chunk_records)
                
            logger.info("✅ HOÀN TẤT NẠP VECTOR VÀ PARENT-CHILD VÀO SUPABASE!")
            logger.info(f"📊 Kết quả: {stats['added_or_updated_docs']} Documents, {stats['parent_sections']} Parents, {stats['embedded_chunks']} Chunks")
            return stats
            
        except Exception as e:
            logger.exception(f"Lỗi trong quá trình embed và nạp Supabase: {e}")
            raise

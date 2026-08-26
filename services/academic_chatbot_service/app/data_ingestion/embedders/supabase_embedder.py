import os
import json
import uuid
import hashlib
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv
from app.data_ingestion.utils.logger import setup_logger

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
    def __init__(self, model_name="bkai-foundation-models/vietnamese-bi-encoder"):
        load_dotenv()
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("Không tìm thấy DATABASE_URL trong .env")
            
        logger.info(f"Đang tải mô hình nhúng {model_name}...")
        self.embedder = SentenceTransformer(model_name)
        
    def get_connection(self):
        return psycopg2.connect(self.db_url)
        
    def run_embedding(self, children_file_path):
        logger.info(f"Đọc dữ liệu từ {children_file_path}...")
        with open(children_file_path, 'r', encoding='utf-8') as f:
            children = json.load(f)
            
        if not children:
            logger.warning("Không có dữ liệu child chunks để embed.")
            return

        # Nhóm chunks theo source_url
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
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for source_url, doc_info in tqdm(docs_map.items(), desc="Nhúng và Lưu DB"):
                        title = doc_info["title"]
                        breadcrumbs = doc_info["breadcrumbs"]
                        
                        # Tạo hash đại diện cho doc này (để sau này có incremental caching nếu muốn)
                        # Tạm thời sinh random UUID hoặc hash nội dung
                        all_text = "".join(c["text"] for c in doc_info["chunks"])
                        content_hash = hashlib.md5(all_text.encode('utf-8')).hexdigest()
                        
                        # 1. Upsert Document
                        upsert_doc_query = """
                            INSERT INTO documents (title, source_url, breadcrumbs, content_hash, updated_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (source_url) 
                            DO UPDATE SET 
                                title = EXCLUDED.title,
                                breadcrumbs = EXCLUDED.breadcrumbs,
                                content_hash = EXCLUDED.content_hash,
                                updated_at = NOW()
                            RETURNING id;
                        """
                        cur.execute(upsert_doc_query, (title, source_url, breadcrumbs, content_hash))
                        doc_row = cur.fetchone()
                        if not doc_row:
                            logger.error(f"Không thể upsert document cho '{source_url}'")
                            continue
                        document_id = doc_row[0]
                        stats["added_or_updated_docs"] += 1
                        
                        # 2. Xóa chunk cũ của document_id này (tránh orphan khi update)
                        cur.execute("DELETE FROM document_chunks WHERE document_id = %s;", (document_id,))
                        
                        # 3. Chuẩn bị bulk insert chunks
                        chunk_records = []
                        chunks_batch = doc_info["chunks"]
                        
                        # Embed từng chunk một (có thể batch encode để nhanh hơn)
                        texts_to_embed = [inject_meta(c["text"], c.get("metadata", {})) for c in chunks_batch]
                        vectors = self.embedder.encode(texts_to_embed, convert_to_numpy=True).tolist()
                        
                        for idx, (child, vector) in enumerate(zip(chunks_batch, vectors)):
                            injected_text = texts_to_embed[idx]
                            meta_cleaned = {k: (v if v is not None else "") for k, v in child.get("metadata", {}).items()}
                            vector_str = "[" + ",".join(str(x) for x in vector) + "]"
                            
                            # Tính tokens roughly
                            tokens_count = len(child["text"].split())
                            
                            chunk_records.append((
                                document_id,
                                idx,
                                child["text"],
                                injected_text,
                                Json(meta_cleaned),
                                vector_str,
                                tokens_count
                            ))
                            
                        # 4. Insert chunks
                        insert_chunks_query = """
                            INSERT INTO document_chunks (
                                document_id,
                                chunk_index,
                                content,
                                injected_content,
                                metadata,
                                embedding,
                                tokens_count
                            ) VALUES %s;
                        """
                        execute_values(
                            cur,
                            insert_chunks_query,
                            chunk_records,
                            template="(%s, %s, %s, %s, %s, %s::vector, %s)"
                        )
                        stats["embedded_chunks"] += len(chunk_records)
                        
                conn.commit()
                
            logger.info("✅ HOÀN TẤT NẠP VECTOR VÀO SUPABASE!")
            logger.info(f"📊 Kết quả: {stats['added_or_updated_docs']} Documents, {stats['embedded_chunks']} Chunks")
            return stats
            
        except Exception as e:
            logger.exception(f"Lỗi trong quá trình embed và nạp Supabase: {e}")
            raise

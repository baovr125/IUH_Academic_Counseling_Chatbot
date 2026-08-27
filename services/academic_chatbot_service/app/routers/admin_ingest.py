import os
import asyncio
import hashlib
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from app.utils.security import get_current_admin_user
from app.utils.logger import logger
from pydantic import BaseModel

from app.data_ingestion.crawlers.content_crawler import ContentCrawler
from app.data_ingestion.extractors.url_extractor import URLExtractor
from app.data_ingestion.crawlers.pdf_extractor import PDFExtractor
from app.data_ingestion.chunkers.hybrid_chunker import HybridChunker
from app.data_ingestion.embedders.supabase_embedder import SupabaseEmbedder
from app.services.rag_service import get_embedder
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/admin/ingest", tags=["Admin Ingestion"])

DATA_DIR = "/app/app/data_ingestion/data"

STAGING_DIR = os.path.join(DATA_DIR, "staging_markdown")
CHILDREN_FILE = os.path.join(DATA_DIR, "children.json")

class UrlsPayload(BaseModel):
    urls: List[str]

# Simple in-memory status tracker for SSE
ingestion_status = {"status": "idle", "message": "Đang chờ lệnh", "progress": 0}

def set_status(status_str: str, message: str, progress: int = 0):
    ingestion_status["status"] = status_str
    ingestion_status["message"] = message
    ingestion_status["progress"] = progress
    logger.info(f"[INGESTION] {message}")

def run_unified_pipeline(new_markdown_files: List[str] = None):
    """
    Runs the chunking and embedding steps on the specified markdown files.
    If none specified, runs on the whole STAGING_DIR.
    """
    try:
        os.makedirs(STAGING_DIR, exist_ok=True)
        
        set_status("chunking", "Đang cắt nhỏ (chunking) dữ liệu Markdown...")
        
        chunker = HybridChunker(max_child_size=600, overlap=100)
        # Instead of processing the whole directory, the HybridChunker currently processes the whole directory anyway.
        # We will just let it process everything in MARKDOWN_DIR for now to ensure index is rebuilt,
        # or we could optimize it later. The prompt said "reuse existing functions".
        parents, children = chunker.process_directory(STAGING_DIR)
        
        # Deduplication
        seen_hashes = set()
        unique_children = []
        for c in children:
            raw_text = c.get('text', '').strip()
            normalized_text = " ".join(raw_text.lower().split())
            text_hash = hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_children.append(c)
        
        children = unique_children
        import json
        with open(CHILDREN_FILE, 'w', encoding='utf-8') as f:
            json.dump(children, f, indent=4, ensure_ascii=False)
            
        parents_file = os.path.join(DATA_DIR, "parents.json")
        with open(parents_file, 'w', encoding='utf-8') as f:
            json.dump(parents, f, indent=4, ensure_ascii=False)
            
        set_status("embedding", f"Đang nhúng (embedding) {len(children)} chunks lên Supabase...")
        # Tận dụng mô hình đã load sẵn trên RAM/VRAM của Chatbot
        embed_model = get_embedder()
        embedder = SupabaseEmbedder(embedder_instance=embed_model)
        embedder.run_embedding(CHILDREN_FILE)
        

        
        set_status("completed", "Hoàn tất xử lý và nhúng dữ liệu vào cơ sở dữ liệu!", 100)
    except Exception as e:
        set_status("error", f"Lỗi trong quá trình xử lý: {e}", 0)
        logger.error(f"Unified pipeline error: {e}")

def clear_markdown_cache():
    if os.path.exists(STAGING_DIR):
        import shutil
        for filename in os.listdir(STAGING_DIR):
            file_path = os.path.join(STAGING_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")
    os.makedirs(STAGING_DIR, exist_ok=True)
    

async def process_uploaded_files(files_data: List[dict]):
    set_status("parsing", f"Đang phân tích {len(files_data)} file được tải lên...")
    clear_markdown_cache()
    pdf_extractor = PDFExtractor(output_dir=STAGING_DIR)
    
    for idx, fdata in enumerate(files_data):
        filename = fdata["filename"]
        content = fdata["bytes"]
        
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            set_status("parsing", f"Đang trích xuất PDF ({idx+1}/{len(files_data)}): {filename}")
            extracted_text = await asyncio.to_thread(pdf_extractor.extract_from_bytes, content, filename)
        elif filename.lower().endswith(".md") or filename.lower().endswith(".txt"):
            extracted_text = content.decode("utf-8", errors="ignore")
        else:
            logger.warning(f"Bỏ qua định dạng không được hỗ trợ: {filename}")
            continue
            
        if extracted_text:
            safe_name = hashlib.md5(content).hexdigest()[:8] + "_" + filename.replace(".pdf", "") + ".md"
            with open(os.path.join(STAGING_DIR, safe_name), "w", encoding="utf-8") as f:
                frontmatter = f"---\nsource_url: {filename}\ntitle: {filename}\nbreadcrumbs: Tải lên hệ thống\n---\n\n"
                f.write(frontmatter + f"# TÀI LIỆU: {filename}\n\n{extracted_text}")
                
    # Run the chunk & embed pipeline
    await asyncio.to_thread(run_unified_pipeline)

async def process_crawled_urls(urls: List[str]):
    set_status("crawling", f"Đang cào dữ liệu từ {len(urls)} URLs...")
    clear_markdown_cache()
    crawler = ContentCrawler(output_dir=STAGING_DIR, max_workers=5)
    await asyncio.to_thread(crawler.run_crawl, urls, False)
    
    # Run the chunk & embed pipeline
    await asyncio.to_thread(run_unified_pipeline)


@router.post("/files")
async def ingest_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    admin_id: str = Depends(get_current_admin_user)
):
    if ingestion_status["status"] not in ["idle", "completed", "error"]:
        raise HTTPException(status_code=400, detail="Hệ thống đang xử lý một tiến trình khác. Vui lòng đợi.")
        
    logger.info(f"Admin {admin_id} uploaded {len(files)} files for ingestion.")
    set_status("starting", "Khởi tạo tiến trình xử lý file...")
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append({"filename": f.filename, "bytes": content, "content_type": f.content_type})
        
    background_tasks.add_task(process_uploaded_files, file_data)
    return {"message": f"Successfully queued {len(files)} files for unified ingestion pipeline."}

@router.post("/urls")
async def ingest_urls(
    payload: UrlsPayload,
    background_tasks: BackgroundTasks,
    admin_id: str = Depends(get_current_admin_user)
):
    if ingestion_status["status"] not in ["idle", "completed", "error"]:
        raise HTTPException(status_code=400, detail="Hệ thống đang xử lý một tiến trình khác. Vui lòng đợi.")
        
    logger.info(f"Admin {admin_id} requested ingestion for {len(payload.urls)} URLs.")
    set_status("starting", "Khởi tạo tiến trình cào dữ liệu...")
    background_tasks.add_task(process_crawled_urls, payload.urls)
    return {"message": f"Successfully queued {len(payload.urls)} URLs for unified ingestion pipeline."}

@router.get("/status")
async def get_ingestion_status(admin_id: str = Depends(get_current_admin_user)):
    import json
    async def event_generator():
        last_status = None
        while True:
            current_status = json.dumps(ingestion_status, ensure_ascii=False)
            if current_status != last_status:
                yield f"data: {current_status}\n\n"
                last_status = current_status
            
            if ingestion_status["status"] in ["completed", "error"]:
                break
                
            await asyncio.sleep(1)
                
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

from fastapi import Query

@router.get("/documents")
async def get_ingested_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    sort_by: str = Query("updated_at", pattern="^(updated_at|chunk_count)$"),
    search: str = Query(None),
    admin_id: str = Depends(get_current_admin_user)
):
    try:
        supabase = get_supabase_client()
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit - 1
        
        query = supabase.table("documents").select("id, title, source_url, updated_at, chunk_count")
        count_query = supabase.table("documents").select("id", count="exact")
        
        if search and search.strip():
            # Escape double quotes to prevent breaking the PostgREST or_ syntax
            search_clean = search.strip().replace('"', '\\"')
            # Wrap in double quotes so commas, hyphens, and parentheses inside the search term don't break the logic tree
            or_cond = f'source_url.ilike."%{search_clean}%",title.ilike."%{search_clean}%"' 
            query = query.or_(or_cond)
            count_query = count_query.or_(or_cond)
        
        # Get total count
        count_res = count_query.execute()
        total_count = count_res.count if hasattr(count_res, 'count') and count_res.count else 0
        
        # Fetch paginated documents
        is_desc = True if sort == "desc" else False
        response = query.order(sort_by, desc=is_desc).range(start_idx, end_idx).execute()
        
        docs = response.data if response.data else []
        # chunk_count is now natively retrieved from the documents table!
        for d in docs:
            if "chunk_count" not in d or d["chunk_count"] is None:
                d["chunk_count"] = 0
                    
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return {
            "ok": True, 
            "data": docs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_items": total_count,
                "total_pages": total_pages
            }
        }
    except Exception as e:
        logger.exception("Error fetching documents:")
        raise HTTPException(status_code=500, detail=str(e))

class UpdateDocumentPayload(BaseModel):
    title: str

@router.patch("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    payload: UpdateDocumentPayload,
    admin_id: str = Depends(get_current_admin_user)
):
    try:
        supabase = get_supabase_client()
        res = supabase.table("documents").update({"title": payload.title}).eq("id", doc_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"ok": True, "message": "Cập nhật thành công"}
    except Exception as e:
        logger.exception(f"Error updating document {doc_id}:")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    admin_id: str = Depends(get_current_admin_user)
):
    try:
        supabase = get_supabase_client()
        # Explicitly delete chunks first to avoid foreign key constraint errors if ON DELETE CASCADE is missing
        supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
        # Delete the document itself
        res = supabase.table("documents").delete().eq("id", doc_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"ok": True, "message": "Xóa thành công"}
    except Exception as e:
        logger.exception(f"Error deleting document {doc_id}:")
        raise HTTPException(status_code=500, detail=str(e))

class ExtractPayload(BaseModel):
    extra_urls: List[str]

async def process_full_extract_and_crawl(extra_urls: List[str]):
    set_status("extracting", "Đang tự động trích xuất các URL từ cấu trúc Sitemap và BFS mặc định của trường...")
    clear_markdown_cache()
    
    try:
        # Run URLExtractor blocking code in thread
        def _extract():
            extractor = URLExtractor()
            all_urls = set(extra_urls)
            
            camnang_urls = extractor.extract_from_sitemap("https://camnang.iuh.edu.vn/sitemap.xml")
            all_urls.update(camnang_urls)
            
            iuh_thong_bao = extractor.extract_from_category("https://iuh.edu.vn/vi/thong-bao.html", max_pages=10)
            all_urls.update(iuh_thong_bao)
            
            iuh_static = extractor.extract_from_bfs("https://iuh.edu.vn/", max_depth=0)
            all_urls.update(iuh_static)
            
            camnang_bfs = extractor.extract_from_bfs("https://camnang.iuh.edu.vn/", max_depth=10)
            all_urls.update(camnang_bfs)
            
            tuyensinh_urls = [
                "https://tuyensinh.iuh.edu.vn/quyChe",
                "https://tuyensinh.iuh.edu.vn/nganhDaoTao",
                "https://tuyensinh.iuh.edu.vn/diemChuan",
                "https://tuyensinh.iuh.edu.vn/deAnTS",
            ]
            all_urls.update(tuyensinh_urls)
            return list(all_urls)
            
        final_urls = await asyncio.to_thread(_extract)
        
        set_status("crawling", f"Đã trích xuất {len(final_urls)} URLs. Đang tiến hành cào dữ liệu...")
        crawler = ContentCrawler(output_dir=STAGING_DIR, max_workers=5)
        # For this massive pipeline, we disable recursive BFS on the crawler because URLExtractor already did it
        await asyncio.to_thread(crawler.run_crawl, final_urls, False)
        
        # Run chunking & embedding
        await asyncio.to_thread(run_unified_pipeline)
        
    except Exception as e:
        set_status("error", f"Lỗi trong quá trình trích xuất: {e}", 0)
        logger.error(f"Full extract pipeline error: {e}")

@router.post("/extract-and-crawl")
async def ingest_extract_and_crawl(
    payload: ExtractPayload,
    background_tasks: BackgroundTasks,
    admin_id: str = Depends(get_current_admin_user)
):
    if ingestion_status["status"] not in ["idle", "completed", "error"]:
        raise HTTPException(status_code=400, detail="Hệ thống đang xử lý một tiến trình khác. Vui lòng đợi.")
        
    logger.info(f"Admin {admin_id} requested full extraction with {len(payload.extra_urls)} extra URLs.")
    set_status("starting", "Khởi tạo tiến trình quét toàn bộ website...")
    background_tasks.add_task(process_full_extract_and_crawl, payload.extra_urls)
    return {"message": "Successfully queued full extraction pipeline."}

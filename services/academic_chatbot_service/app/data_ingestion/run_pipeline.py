import os
import json
import argparse
from urllib.parse import urlparse
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv()

from app.data_ingestion.utils.logger import setup_logger
from app.data_ingestion.extractors.url_extractor import URLExtractor
from app.data_ingestion.sources import collect_iuh_urls
from app.data_ingestion.crawlers.content_crawler import ContentCrawler
from app.services.supabase_client import get_supabase_client
REPO_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "ingestion")
DATA_DIR = os.getenv("DATA_INGESTION_DIR", REPO_DATA_DIR if os.path.exists(REPO_DATA_DIR) else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
URL_LIST_FILE = os.path.join(DATA_DIR, "urls.json")
GRAPH_FILE = os.path.join(DATA_DIR, "web_structure_graph.json")
MARKDOWN_DIR = os.path.join(DATA_DIR, "staging_markdown")
CHILDREN_FILE = os.path.join(DATA_DIR, "children.json")

logger = setup_logger("orchestrator", "pipeline.log")

def run_extraction():
    logger.info("========== BƯỚC 0: TRÍCH XUẤT TOÀN BỘ URL (HYBRID APPROACH) ==========")
    extractor = URLExtractor()
    all_urls = collect_iuh_urls(extractor)
    
    target_urls = list(all_urls)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    graph_data = {}
    for url in target_urls:
        domain_key = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
        if domain_key not in graph_data:
            graph_data[domain_key] = []
        graph_data[domain_key].append(url)
        
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=4, ensure_ascii=False)
        
    with open(URL_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(target_urls, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Đã lưu {len(target_urls)} URLs vào {URL_LIST_FILE}")
    return target_urls

def run_crawling(urls=None):
    logger.info("========== BƯỚC 1: CÀO NỘI DUNG VÀ PARSE MARKDOWN ==========")
    if not urls:
        if not os.path.exists(URL_LIST_FILE):
            logger.error(f"Không tìm thấy file {URL_LIST_FILE}. Vui lòng chạy bước trích xuất URL trước!")
            return
        with open(URL_LIST_FILE, 'r', encoding='utf-8') as f:
            urls = json.load(f)
            
    crawler = ContentCrawler(output_dir=MARKDOWN_DIR, max_workers=5)
    crawler.run_crawl(urls, recursive=False, max_pages=None)

from app.data_ingestion.chunkers.hybrid_chunker import HybridChunker

def reset_database(clear_cache: bool = True) -> bool:
    """Xóa sạch dữ liệu cũ trong Supabase (documents, document_parents, document_chunks, semantic_cache)"""
    logger.info("========== ĐANG XÓA TOÀN BỘ CƠ SỞ DỮ LIỆU CŨ TRÊN SUPABASE ==========")
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Không thể kết nối Supabase! Vui lòng kiểm tra SUPABASE_URL và SUPABASE_KEY trong .env")
        return False
        
    try:
        logger.info("1/4. Đang xóa dữ liệu bảng document_chunks...")
        supabase.table("document_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        logger.info("2/4. Đang xóa dữ liệu bảng document_parents...")
        supabase.table("document_parents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        logger.info("3/4. Đang xóa dữ liệu bảng documents...")
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        if clear_cache:
            try:
                logger.info("4/4. Đang xóa dữ liệu bảng semantic_cache...")
                supabase.table("semantic_cache").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            except Exception as ce:
                logger.warning(f"Bỏ qua xóa semantic_cache: {ce}")
                
        logger.info("✅ ĐÃ XÓA SẠCH DỮ LIỆU CSDL CŨ TRÊN SUPABASE THÀNH CÔNG!")
        return True
    except Exception as e:
        logger.exception(f"Lỗi khi xóa dữ liệu trên Supabase: {e}")
        return False

def clean_local_cache():
    """Dọn dẹp thư mục staging markdown và các file cache json cục bộ để cào mới từ đầu"""
    logger.info("========== ĐANG DỌN DẸP CACHE VÀ STAGING LOCAL ==========")
    import shutil
    if os.path.exists(MARKDOWN_DIR):
        try:
            shutil.rmtree(MARKDOWN_DIR)
            os.makedirs(MARKDOWN_DIR, exist_ok=True)
        except PermissionError as pe:
            logger.error(
                f"❌ Lỗi phân quyền khi xóa {MARKDOWN_DIR}: {pe}\n"
                f"👉 Một số file PDF/MD do Docker hoặc tiến trình root tạo ra. Vui lòng chạy lệnh sau trên terminal:\n"
                f"   sudo chown -R $USER:$USER /home/anhhao/workSpace/IUH_Academic_Counseling_Chatbot/data/ingestion"
            )
            raise
    
    files_to_remove = [
        CHILDREN_FILE,
        os.path.join(DATA_DIR, "parents.json"),
        os.path.join(DATA_DIR, "mock_supabase_state.json")
    ]
    for fp in files_to_remove:
        if os.path.exists(fp):
            try:
                os.remove(fp)
                logger.info(f"Đã xóa file tạm: {fp}")
            except PermissionError:
                logger.warning(f"Không thể xóa {fp} do thiếu quyền sở hữu.")
    logger.info("✅ ĐÃ DỌN DẸP SẠCH LOCAL STAGING DIR!")

def run_chunking():
    logger.info("========== BƯỚC 2: CẮT NHỎ MARKDOWN (CHUNKING) ==========")
    if not os.path.exists(MARKDOWN_DIR) or not os.listdir(MARKDOWN_DIR):
        logger.error(f"Thư mục {MARKDOWN_DIR} trống. Vui lòng chạy bước cào (crawl) trước!")
        return []
        
    chunker = HybridChunker(max_child_size=600, overlap=100, max_parent_tokens=1200)
    parents, children = chunker.process_directory(MARKDOWN_DIR)

    # --- DEDUPLICATION AT INDEX TIME ---
    import hashlib
    seen_hashes = set()
    unique_children = []
    
    for c in children:
        raw_text = c.get('text', '').strip()
        normalized_text = " ".join(raw_text.lower().split())
        text_hash = hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
        
        if text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            unique_children.append(c)
            
    logger.info(f"Deduplication removed {len(children) - len(unique_children)} duplicate chunks.")
    children = unique_children
    # -----------------------------------
    
    parents_file = os.path.join(DATA_DIR, "parents.json")
    with open(parents_file, 'w', encoding='utf-8') as f:
        json.dump(parents, f, indent=4, ensure_ascii=False)
        
    children_file = os.path.join(DATA_DIR, "children.json")
    with open(children_file, 'w', encoding='utf-8') as f:
        json.dump(children, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Đã cắt thành {len(parents)} Parent Chunks và {len(children)} Child Chunks (Unique).")
    logger.info(f"Lưu tại {parents_file} và {children_file}")
    return children

from app.data_ingestion.embedders.supabase_embedder import SupabaseEmbedder

def run_embedding():
    logger.info("========== BƯỚC 3: NHÚNG VÀ LƯU VÀO SUPABASE (EMBEDDING) ==========")
    if not os.path.exists(CHILDREN_FILE):
        logger.error(f"Không tìm thấy {CHILDREN_FILE}. Vui lòng chạy bước cắt (chunk) trước!")
        return
        
    embedder = SupabaseEmbedder(model_name="bkai-foundation-models/vietnamese-bi-encoder")
    embedder.run_embedding(CHILDREN_FILE, os.path.join(DATA_DIR, "parents.json"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IUH Academic Counseling Data Pipeline")
    parser.add_argument('--step', type=str, choices=['all', 'extract', 'crawl', 'chunk', 'embed', 'reset'], default='all',
                        help='Chọn bước để chạy (all, extract, crawl, chunk, embed, reset)')
    parser.add_argument('--reset-db', action='store_true',
                        help='Xóa sạch dữ liệu cũ trong Supabase (documents, document_parents, document_chunks, semantic_cache) trước khi chạy')
    parser.add_argument('--clean-local', action='store_true',
                        help='Xóa sạch staging_markdown và mock_supabase_state.json để cào mới hoàn toàn từ web')
    args = parser.parse_args()

    logger.info(f"BẮT ĐẦU CHẠY PIPELINE (Chế độ: {args.step.upper()})...")
    
    # 1. Reset CSDL nếu được yêu cầu hoặc nếu step == 'reset'
    if args.reset_db or args.step == 'reset':
        reset_database()
        if args.step == 'reset':
            logger.info("✅ Hoàn tất thao tác xóa CSDL!")
            exit(0)
            
    # 2. Xóa local staging nếu được yêu cầu
    if args.clean_local:
        clean_local_cache()
    
    urls = []
    if args.step in ['all', 'extract']:
        urls = run_extraction()
        
    if args.step in ['all', 'crawl']:
        if args.step == 'crawl':
            run_crawling()
        else:
            run_crawling(urls)
            
    if args.step in ['all', 'chunk']:
        run_chunking()
        
    if args.step in ['all', 'embed']:
        run_embedding()
            
    logger.info("✅ HOÀN TẤT PIPELINE!")

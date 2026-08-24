import os
import json
import argparse
from urllib.parse import urlparse
from data_pipeline.utils.logger import setup_logger
from data_pipeline.extractors.url_extractor import URLExtractor
from data_pipeline.crawlers.content_crawler import ContentCrawler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
URL_LIST_FILE = os.path.join(DATA_DIR, "urls.json")
GRAPH_FILE = os.path.join(DATA_DIR, "web_structure_graph.json")
MARKDOWN_DIR = os.path.join(DATA_DIR, "crawled_markdown")
CHILDREN_FILE = os.path.join(DATA_DIR, "children.json")

logger = setup_logger("orchestrator", "pipeline.log")

def run_extraction():
    logger.info("========== BƯỚC 0: TRÍCH XUẤT TOÀN BỘ URL (HYBRID APPROACH) ==========")
    extractor = URLExtractor()
    all_urls = set()
    
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
        # "https://tuyensinh.iuh.edu.vn/Files_thongBao/thongbaotuyensinhlienthongdot12026.pdf"   # skip
    ]
    all_urls.update(tuyensinh_urls)
    
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
    crawler.run_crawl(urls)

from data_pipeline.chunkers.hybrid_chunker import HybridChunker

def run_chunking():
    logger.info("========== BƯỚC 2: CẮT NHỎ MARKDOWN (CHUNKING) ==========")
    if not os.path.exists(MARKDOWN_DIR) or not os.listdir(MARKDOWN_DIR):
        logger.error(f"Thư mục {MARKDOWN_DIR} trống. Vui lòng chạy bước cào (crawl) trước!")
        return []
        
    chunker = HybridChunker(max_child_size=600, overlap=100)
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

from data_pipeline.embedders.supabase_embedder import SupabaseEmbedder

def run_embedding():
    logger.info("========== BƯỚC 3: NHÚNG VÀ LƯU VÀO SUPABASE (EMBEDDING) ==========")
    if not os.path.exists(CHILDREN_FILE):
        logger.error(f"Không tìm thấy {CHILDREN_FILE}. Vui lòng chạy bước cắt (chunk) trước!")
        return
        
    embedder = SupabaseEmbedder(model_name="bkai-foundation-models/vietnamese-bi-encoder")
    embedder.run_embedding(CHILDREN_FILE)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IUH Academic Counseling Data Pipeline")
    parser.add_argument('--step', type=str, choices=['all', 'extract', 'crawl', 'chunk', 'embed'], default='all',
                        help='Chọn bước để chạy (all, extract, crawl, chunk, embed)')
    args = parser.parse_args()

    logger.info(f"BẮT ĐẦU CHẠY PIPELINE (Chế độ: {args.step.upper()})...")
    
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

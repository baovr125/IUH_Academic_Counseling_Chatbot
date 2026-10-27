"""Danh sách nguồn website IUH dùng cho bước trích xuất URL (CLI run_pipeline và API admin_ingest)."""
from typing import Iterable, Set

SITEMAP_SOURCES = ["https://camnang.iuh.edu.vn/sitemap.xml"]

# (URL danh mục, số trang tối đa)
CATEGORY_SOURCES = [("https://iuh.edu.vn/vi/thong-bao.html", 10)]

# (URL gốc, độ sâu BFS tối đa)
BFS_SOURCES = [
    ("https://iuh.edu.vn/", 2),
    ("https://camnang.iuh.edu.vn/", 5),
    ("https://ctsv.iuh.edu.vn/", 4),
    ("https://csm.iuh.edu.vn/", 3),
]

# Trang tuyển sinh được thêm thẳng, không duyệt BFS.
FIXED_URLS = [
    "https://tuyensinh.iuh.edu.vn/quyChe",
    "https://tuyensinh.iuh.edu.vn/nganhDaoTao",
    "https://tuyensinh.iuh.edu.vn/diemChuan",
    "https://tuyensinh.iuh.edu.vn/deAnTS",
]


def collect_iuh_urls(extractor, extra_urls: Iterable[str] = ()) -> Set[str]:
    """Gom URL từ sitemap, danh mục, BFS và danh sách cố định (cộng thêm extra_urls)."""
    all_urls: Set[str] = set(extra_urls)
    for sitemap in SITEMAP_SOURCES:
        all_urls.update(extractor.extract_from_sitemap(sitemap))
    for url, max_pages in CATEGORY_SOURCES:
        all_urls.update(extractor.extract_from_category(url, max_pages=max_pages))
    for url, max_depth in BFS_SOURCES:
        all_urls.update(extractor.extract_from_bfs(url, max_depth=max_depth))
    all_urls.update(FIXED_URLS)
    return all_urls

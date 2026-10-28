"""Danh sách nguồn crawl dùng chung giữa run_pipeline (CLI) và admin_ingest (API)."""
from app.data_ingestion.sources import BFS_SOURCES, CATEGORY_SOURCES, FIXED_URLS, SITEMAP_SOURCES, collect_iuh_urls


class _FakeExtractor:
    def __init__(self):
        self.calls = []

    def extract_from_sitemap(self, url):
        self.calls.append(("sitemap", url))
        return {f"{url}#a"}

    def extract_from_category(self, url, max_pages):
        self.calls.append(("category", url, max_pages))
        return {f"{url}#c"}

    def extract_from_bfs(self, url, max_depth):
        self.calls.append(("bfs", url, max_depth))
        return {f"{url}#b"}


def test_collect_uses_every_configured_source_with_its_limits():
    extractor = _FakeExtractor()
    collect_iuh_urls(extractor)

    assert [c for c in extractor.calls if c[0] == "sitemap"] == [("sitemap", u) for u in SITEMAP_SOURCES]
    assert [c for c in extractor.calls if c[0] == "category"] == [("category", u, n) for u, n in CATEGORY_SOURCES]
    assert [c for c in extractor.calls if c[0] == "bfs"] == [("bfs", u, d) for u, d in BFS_SOURCES]


def test_collect_includes_fixed_and_extra_urls():
    urls = collect_iuh_urls(_FakeExtractor(), ["https://example.test/extra"])

    assert "https://example.test/extra" in urls
    assert set(FIXED_URLS) <= urls


def test_known_iuh_hosts_are_covered():
    hosts = {u.split("/")[2] for u, _ in BFS_SOURCES}
    assert {"iuh.edu.vn", "camnang.iuh.edu.vn", "ctsv.iuh.edu.vn", "csm.iuh.edu.vn"} <= hosts
    assert len(FIXED_URLS) == 4

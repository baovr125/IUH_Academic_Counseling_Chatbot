import pytest
from unittest.mock import MagicMock, patch
from app.data_ingestion.utils.url_helpers import clean_and_verify_url
from app.data_ingestion.extractors.url_extractor import URLExtractor
from app.data_ingestion.crawlers.content_crawler import ContentCrawler

class TestURLHelpersCTSV:
    def test_ctsv_feedback_url_allowed(self):
        url = "https://ctsv.iuh.edu.vn/feedback.html@detail@216@2799@Giay-vay-sinh-viên"
        clean = clean_and_verify_url(url)
        assert clean is not None
        assert "feedback.html" in clean
        assert "2799" in clean

    def test_ctsv_redundant_at_symbols_collapsed(self):
        url = "https://ctsv.iuh.edu.vn/feedback.html@@@p=1"
        clean = clean_and_verify_url(url)
        assert clean is not None
        assert "@@" not in clean
        assert clean == "https://ctsv.iuh.edu.vn/feedback.html@p=1"

    def test_ctsv_non_academic_blacklist_still_filtered(self):
        assert clean_and_verify_url("https://ctsv.iuh.edu.vn/news.html@211@hoat-dong-phong-trao") is None
        assert clean_and_verify_url("https://ctsv.iuh.edu.vn/upload/images/banner.jpg") is None


class TestURLExtractorDeduplication:
    def test_ctsv_feedback_and_news_deduplication_by_id(self):
        extractor = URLExtractor()
        
        # Mock HTML returned by session.get
        mock_html = """
        <html><body>
            <a href="feedback.html@detail@216@2799@Giay-vay-sinh-viên">Q1</a>
            <a href="feedback.html@detail@2799@Thoi-gian-hoc-tap">Q1 Duplicate with different slug</a>
            <a href="feedback.html@detail@@2799@Hoi-thac-mac">Q1 Duplicate with double at</a>
            <a href="feedback.html@detail@216@2798@Thoi-gian-hoc-tap">Q2</a>
            <a href="news.html@detail@150@613@Thong-bao-BHYT">News 1</a>
            <a href="news.html@detail@613@Thong-bao-BHYT-2">News 1 Duplicate</a>
        </body></html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        
        with patch.object(extractor.session, 'get', return_value=mock_response):
            results = extractor.extract_from_bfs("https://ctsv.iuh.edu.vn/", max_depth=1)
            
        feedback_results = [u for u in results if "feedback.html" in u]
        news_results = [u for u in results if "news.html" in u]
        
        # Exactly 2 distinct questions (2799 and 2798), not 4!
        assert len(feedback_results) == 2
        assert any("2799" in u for u in feedback_results)
        assert any("2798" in u for u in feedback_results)
        
        # Exactly 1 distinct news item (613), not 2!
        assert len(news_results) == 1
        assert "613" in news_results[0]


class TestContentCrawlerUncapped:
    def test_run_crawl_default_parameters(self):
        crawler = ContentCrawler(output_dir="/tmp/test_uncapped_output")
        with patch.object(crawler, '_process_url_worker', return_value=(True, [])):
            urls = [f"https://camnang.iuh.edu.vn/item{i}" for i in range(10)]
            # max_pages is None by default and recursive is False
            crawler.run_crawl(urls, recursive=False, max_pages=None)
            assert len(urls) == 10

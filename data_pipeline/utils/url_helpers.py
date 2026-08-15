import re
from urllib.parse import urlparse

ALLOWED_DOMAINS = ["iuh.edu.vn", "camnang.iuh.edu.vn", "tuyensinh.iuh.edu.vn"]

SOCIAL_MEDIA_PATTERN = re.compile(
    r'(facebook\.com|twitter\.com|instagram\.com|youtube\.com|tiktok\.com|zalo\.me|linkedin\.com)', 
    re.IGNORECASE
)

def clean_and_verify_url(url):
    """
    Làm sạch URL (bỏ query params rác, anchors) và kiểm tra xem có thuộc domain cho phép không.
    Trả về URL sạch nếu hợp lệ, ngược lại trả về None.
    """
    if not url or not url.startswith("http"):
        return None
        
    # Sửa lỗi sitemap của camnang tự động nối dính 2 URL vào nhau (vd: https://camnang.../https://iuh...)
    if url.count("http") > 1:
        last_http_index = url.rfind("http")
        url = url[last_http_index:]
        
    url = url.split('#')[0]
    
    if "?" in url:
        base, query = url.split('?', 1)
        if "p=" in query:
            url = f"{base}?{query}"
        else:
            url = base
            
    if ".html/" in url:
        url = url.split(".html/")[0] + ".html"
        
    parsed = urlparse(url)
    path_segments = parsed.path.lower().split('/')
    if path_segments.count('vi') + path_segments.count('en') > 1:
        return None
        
    if "://www." in url:
        url = url.replace("://www.", "://")
    
    if url.startswith("http://"):
        url = url.replace("http://", "https://")
        
    if url.endswith("/"):
        url = url[:-1]
        
    parsed = urlparse(url)
    netloc = parsed.netloc
    
    if netloc not in ALLOWED_DOMAINS:
        return None
        
    if netloc == "iuh.edu.vn":
        iuh_blacklist = [
            "/hop-tac", "/tin-tuc-dao-tao", "/tin-tuc", "/tags", 
            "/guong-dien-hinh", "/nghien-cuu", "/su-kien", 
            "/thanh-tich-hoc-tap", "/ky-nang-mem", "/kham-pha-iuh", 
            "/hoat-dong-phong-trao", "/en/", "sinh-vien-tinh-nguyen"
        ]
        if any(b in parsed.path.lower() for b in iuh_blacklist):
            return None
            
    if netloc == "tuyensinh.iuh.edu.vn":
        tuyensinh_whitelist = [
            "/quyche", "/nganhdaotao", "/diemchuan", "/deants", 
            "/files_thongbao/thongbaotuyensinhlienthongdot12026.pdf"
        ]
        if not any(parsed.path.lower() == w for w in tuyensinh_whitelist):
            return None
            
    if SOCIAL_MEDIA_PATTERN.search(url):
        return None
        
    return url

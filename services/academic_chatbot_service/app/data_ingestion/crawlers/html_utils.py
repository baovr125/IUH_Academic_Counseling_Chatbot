import re
from datetime import datetime
try:
    import trafilatura
except ImportError:
    trafilatura = None
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_published_date(soup):
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime']
    
    date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})')
    for tag in soup.find_all(['span', 'div', 'p', 'li', 'td', 'time']): 
        text = tag.get_text(strip=True)
        if "đăng" in text.lower() or "ngày" in text.lower() or re.search(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}', text):
            match = date_pattern.search(text)
            if match:
                date_str = match.group(1)
                try:
                    parsed_date = datetime.strptime(date_str.replace('-', '/'), "%d/%m/%Y")
                    return parsed_date.isoformat()
                except:
                    return date_str
    
    return datetime.now().isoformat()

def clean_html_boilerplate(soup):
    for span in soup.find_all('span'):
        if span.string and "Chia sẻ:" in span.string:
            parent_div = span.find_parent('div', class_=re.compile(r'border-t|justify-between|flex'))
            if parent_div:
                parent_div.decompose()
                
    for div in soup.find_all('div', class_=re.compile(r'pdf-download|viewpdf', re.I)):
        div.decompose()
        
    bad_classes = ['pbmit-rpw-content', 'post-navigation', 'nav-links', 'widget-title', 'widget']
    for bad_class in bad_classes:
        for tag in soup.find_all(class_=re.compile(bad_class, re.I)):
            tag.decompose()

    for pattern in [r'\d+\s*lượt xem', r'Tải file thiết kế', r'Download file', r'Vui lòng xem file pdf']:
        for node in soup.find_all(string=re.compile(pattern, re.I)):
            parent = node.parent
            if parent: parent.decompose()
                
    for box in soup.find_all(class_=re.compile(r'pbmit-author-box|author-box', re.I)):
        container = soup.new_tag('div')
        text_parts = box.get_text(separator='\n').split('\n')
        for part in text_parts:
            if part.strip():
                p = soup.new_tag('p')
                p.string = part.strip()
                container.append(p)
        box.replace_with(container)
        
    # Giữ lại các link video Youtube hoặc Google Drive quan trọng (Trafilatura mặc định sẽ xóa iframe)
    for iframe in soup.find_all('iframe', src=True):
        src = iframe['src']
        if 'youtube.com' in src.lower() or 'youtu.be' in src.lower():
            link = soup.new_tag('a', href=src)
            link.string = f"[Video YouTube: {src}]"
            iframe.replace_with(link)
        elif 'drive.google.com' in src.lower():
            link = soup.new_tag('a', href=src)
            link.string = f"[Tài liệu Google Drive: {src}]"
            iframe.replace_with(link)


def extract_markdown(soup):
    article_node = soup.find(class_=re.compile(r'iuhArticleContent|page-content', re.I)) or soup.find('main')
    if not article_node:
        article_node = soup.find('article')
        
    clean_md = None
    if article_node:
        html_to_parse = f"<html><body>{str(article_node)}</body></html>"
        if trafilatura:
            clean_md = trafilatura.extract(html_to_parse, include_links=True, output_format="markdown")
    else:
        for tag in soup.find_all(['header', 'footer', 'nav', 'aside']):
            tag.decompose()
        exact_bad_classes = {'footer', 'header', 'menu', 'sidebar', 'widget-area', 'site-footer', 'site-header'}
        for tag in soup.find_all('div'):
            if exact_bad_classes.intersection(set(tag.get('class', []))):
                tag.decompose()
        if trafilatura:
            clean_md = trafilatura.extract(str(soup), include_links=True, output_format="markdown")
        
    if not clean_md and article_node:
        fallback_node = BeautifulSoup(str(article_node), "html.parser")
        for tag in fallback_node.find_all(['header', 'footer', 'nav', 'aside']):
            tag.decompose()
        for a in fallback_node.find_all('a', href=True):
            if text := a.get_text(strip=True):
                a.replace_with(f"[{text}]({a['href']})")
        lines = [line.strip() for line in fallback_node.get_text(separator='\n', strip=True).split('\n') if line.strip()]
        clean_md = '\n'.join(lines)
        
    return clean_md or ""

def get_pdf_links(soup, base_url):
    urls = set()
    for a in soup.find_all('a', href=True):
        if a['href'].lower().endswith('.pdf'):
            urls.add(urljoin(base_url, a['href']))
    for obj in soup.find_all('object', data=True):
        if obj['data'].lower().endswith('.pdf'):
            urls.add(urljoin(base_url, obj['data']))
    return list(urls)

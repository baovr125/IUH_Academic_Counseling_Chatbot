import re
import unicodedata

def clean_noise(text: str) -> str:
    if not text:
        return text
        
    # Preserve Frontmatter (extract it out temporarily so we don't mess up its formatting)
    frontmatter = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = "---" + parts[1] + "---\n"
            text = parts[2]
            
    # 1. Normalize Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # 2. Remove invisible characters
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # 3. Cap excessive indentation (HTML artifact) to max 4 spaces (preserves markdown lists)
    text = re.sub(r'^ {5,}', '    ', text, flags=re.MULTILINE)
    text = re.sub(r'^\t{2,}', '\t', text, flags=re.MULTILINE)
    
    # 4. Remove useless AI OCR watermarks
    text = text.replace("[DỮ LIỆU ĐƯỢC TRÍCH XUẤT BẰNG CÔNG NGHỆ AI OCR]", "")
    
    # 5. Fix hard-wrapped sentences (a newline followed by a lowercase letter should probably be a space)
    # This fixes PDFs that hard-wrap sentences in the middle of a paragraph.
    text = re.sub(r'([^\n])\n([a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ])', r'\1 \2', text)
    
    # 6. Replace multiple newlines with exactly two newlines to preserve paragraphs
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 7. Remove weird PDF CID artifacts
    text = re.sub(r'\(cid:\d+\)', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 8. Normalize multiple spaces into a single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 9. Clean up trailing spaces on lines
    text = re.sub(r' \n', '\n', text)
    
    return frontmatter + text.strip()

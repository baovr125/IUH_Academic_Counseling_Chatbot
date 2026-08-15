import json
import os
import glob
import re

def main():
    print("="*50)
    print("PHẦN 1: PHÂN TÍCH DỮ LIỆU CRAWL THÔ (RAW MARKDOWN)")
    print("="*50)
    
    md_files = glob.glob('data/crawled_markdown/*.md')
    print(f"Số lượng file Markdown: {len(md_files)}")
    
    all_paragraphs = []
    for file in md_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Xóa YAML frontmatter
            content = re.sub(r'^---\n.*?\n---\n+', '', content, flags=re.DOTALL)
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                p = p.strip()
                if p:
                    all_paragraphs.append(p)
                    
    lengths = sorted([len(p) for p in all_paragraphs])
    total_p = len(lengths)
    print(f"Tổng số đoạn văn tự nhiên (Paragraphs): {total_p:,}")
    print(f"Độ dài trung bình 1 đoạn: {sum(lengths)/total_p:.0f} ký tự")
    print(f"Đoạn văn dài nhất: {max(lengths):,} ký tự")
    
    # Tính percentile tự làm để không cần numpy
    def percentile(data, percent):
        k = (len(data) - 1) * percent
        f = int(k)
        c = int(k) + 1 if int(k) < len(data) - 1 else int(k)
        if f == c:
            return data[int(k)]
        d0 = data[f] * (c - k)
        d1 = data[c] * (k - f)
        return round(d0 + d1)

    print("\n[Tỷ lệ bao phủ độ dài tự nhiên]")
    for p in [50, 75, 90, 95, 99]:
        val = percentile(lengths, p / 100.0)
        print(f" - {p}% đoạn văn có độ dài DƯỚI: {val} ký tự")

    print("\n" + "="*50)
    print("PHẦN 2: THỐNG KÊ KẾT QUẢ CHUNKING (PARENTS & CHILDREN)")
    print("="*50)
    
    try:
        with open('data/parents.json', 'r', encoding='utf-8') as f:
            parents = json.load(f)
        with open('data/children.json', 'r', encoding='utf-8') as f:
            children = json.load(f)
            
        parent_lens = sorted([len(p['text']) for p in parents])
        child_lens = sorted([len(c['text']) for c in children])
        
        print(f"Tổng số Parent Chunks: {len(parents):,}")
        print(f"Độ dài Parent - Trung bình: {sum(parent_lens)/len(parents):.0f} | Lớn nhất: {max(parent_lens):,}")
        
        print(f"\nTổng số Child Chunks: {len(children):,}")
        print(f"Tỷ lệ đẻ nhánh (Child/Parent): {len(children)/len(parents):.2f}")
        print(f"Độ dài Child - Trung bình: {sum(child_lens)/len(children):.0f} | Lớn nhất: {max(child_lens):,}")
        
        print("\n[Phân bổ độ dài Child Chunks]")
        for p in [50, 75, 90, 95, 99]:
            val = percentile(child_lens, p / 100.0)
            print(f" - {p}% Child chunk có độ dài DƯỚI: {val} ký tự")
            
    except Exception as e:
        print(f"Lỗi đọc file chunks: {e}")

if __name__ == '__main__':
    main()

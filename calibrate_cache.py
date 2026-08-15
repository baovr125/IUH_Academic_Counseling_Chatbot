import os
import sys
import numpy as np
import re
from sentence_transformers import SentenceTransformer

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def extract_numbers(text):
    """Extracts all numbers from text as a sorted list of strings."""
    return sorted(re.findall(r'\d+', text))

def check_cache_hit(query, cached_query, embedder, threshold=0.93):
    """Simulates cache check with both semantic threshold and number matching."""
    v1 = embedder.encode(query)
    v2 = embedder.encode(cached_query)
    sim = cosine_similarity(v1, v2)
    
    if sim < threshold:
        return False, sim, "Bị loại do điểm cosine thấp"
        
    num_q = extract_numbers(query)
    num_c = extract_numbers(cached_query)
    
    if num_q != num_c:
        return False, sim, f"Bị loại do khác biệt con số (Khác entities: {num_q} vs {num_c})"
        
    return True, sim, "CACHE HIT HỢP LỆ!"

def main():
    print("🚀 Đang tải mô hình nhúng (Embedding Model)...")
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedder = SentenceTransformer(model_name)
    print(f"✅ Đã tải thành công {model_name}\n")
    
    # 1. Các cặp câu đồng nghĩa (Paraphrases) - Kì vọng: Độ tương đồng cao (Cache HIT)
    positive_pairs = [
        ("Quy định chuẩn đầu ra ngoại ngữ", "Cho mình hỏi về chuẩn đầu ra tiếng Anh ạ"),
        ("Học phí ngành CNTT là bao nhiêu?", "Sinh viên ngành Công nghệ thông tin phải đóng bao nhiêu tiền học phí?"),
        ("Khi nào đăng ký môn học học kỳ 1?", "Thời gian mở form đăng ký tín chỉ kỳ 1 là bao giờ vậy?"),
        ("Điều kiện cấp học bổng khuyến khích học tập", "Làm sao để nhận được học bổng giỏi?"),
        ("Hồ sơ xin xét tốt nghiệp cần những gì?", "Các giấy tờ thủ tục cần nộp để ra trường")
    ]
    
    # 2. Các cặp câu tương đối giống nhau nhưng mang ý nghĩa/thông tin khác nhau - Kì vọng: Độ tương đồng không quá cao (Cache MISS)
    negative_pairs = [
        ("Học phí Khóa 18", "Học phí Khóa 19"),
        ("Quy định chuẩn đầu ra ngoại ngữ Khóa 18", "Quy định chuẩn đầu ra ngoại ngữ Khóa 19"),
        ("Đăng ký môn học học kỳ 1", "Đăng ký môn học học kỳ 2"),
        ("Học phí ngành CNTT", "Học phí ngành Kế toán"),
        ("Cấp lại thẻ sinh viên do bị mất", "Gia hạn thẻ sinh viên do hết hạn")
    ]
    
    threshold = 0.50 # Lower threshold to allow paraphrases to hit
    print(f"--- 🟢 KIỂM TRA CÁC CẶP CÂU ĐỒNG NGHĨA (THRESHOLD = {threshold}) ---")
    for q1, q2 in positive_pairs:
        hit, sim, reason = check_cache_hit(q1, q2, embedder, threshold)
        status = "✅ HIT" if hit else "❌ MISS"
        print(f"Q1: {q1}\nQ2: {q2}\n=> Cosine: {sim:.4f} | Kết quả: {status} ({reason})\n")
        
    print(f"--- 🔴 KIỂM TRA CÁC CẶP CÂU KHÁC NHAU (THRESHOLD = {threshold}) ---")
    for q1, q2 in negative_pairs:
        hit, sim, reason = check_cache_hit(q1, q2, embedder, threshold)
        status = "✅ HIT (LỖI)" if hit else "❌ MISS (ĐÚNG)"
        print(f"Q1: {q1}\nQ2: {q2}\n=> Cosine: {sim:.4f} | Kết quả: {status} ({reason})\n")

if __name__ == "__main__":
    main()

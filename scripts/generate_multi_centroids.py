import sys
import os
import numpy as np

# Adjust path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/academic_chatbot_service')))

from app.services.rag_service import get_embedder

def normalize_vector(v):
    norm = np.linalg.norm(v)
    if norm > 0:
        return v / norm
    return v

def generate_centroids():
    print("Loading ONNX Embedder...")
    embedder = get_embedder()
    
    categories = {
        "tuition_finance": [
            "Học phí kỳ này bao nhiêu?",
            "Làm sao để đóng học phí?",
            "Khi nào hết hạn nộp học phí?",
            "Đóng tiền bảo hiểm y tế ở đâu?",
            "Bảo hiểm thân thể sinh viên",
            "Miễn giảm học phí cho sinh viên khó khăn",
            "Chưa đóng học phí có bị cấm thi không?",
            "Hướng dẫn nộp tiền qua Viettel Money",
            "Học phí chậm tiến độ",
            "bao giờ đóng tiền mạng",
            "chừng nào đóng tiền học"
        ],
        "course_registration": [
            "Đăng ký học phần ở đâu?",
            "Khi nào mở cổng đăng ký môn học?",
            "Hủy học phần đã đăng ký như thế nào?",
            "Rút bớt học phần có được hoàn tiền không?",
            "Lịch học lý thuyết và thực hành",
            "Thời khóa biểu cá nhân",
            "Không đăng ký được môn học",
            "Lớp học phần bị hủy do ít sinh viên",
            "Đăng ký học vượt",
            "Đăng ký học lại cải thiện điểm",
            "chừng nào đkhp"
        ],
        "academic_grades_exams": [
            "Khi nào có lịch thi cuối kỳ?",
            "Xem điểm thi ở đâu?",
            "Cách tính điểm rèn luyện",
            "Quy chế xét học vụ",
            "Bị cảnh báo học tập phải làm sao?",
            "Điều kiện xét tốt nghiệp",
            "Làm tiểu luận, đồ án tốt nghiệp",
            "Thi rớt môn có phải học lại không?",
            "Cách tính điểm hệ 4 và hệ 10",
            "chuẩn đầu ra ngoại ngữ tin học"
        ],
        "it_portal": [
            "Quên mật khẩu cổng thông tin sinh viên",
            "Lấy lại mật khẩu email sv",
            "Không đăng nhập được vào trang web",
            "Lỗi hệ thống không xem được lịch học",
            "Đổi mật khẩu email sinh viên",
            "Mất thẻ sinh viên làm lại thế nào?",
            "app sinh viên iuh bị lỗi"
        ],
        "general_greetings_chit_chat": [
            "Xin chào",
            "Chào bạn",
            "Bạn ơi",
            "Cho mình hỏi một chút được không?",
            "Tư vấn giúp mình nhé",
            "Tôi có câu hỏi",
            "Trường Đại học Công nghiệp TPHCM",
            "Địa chỉ trường ở đâu?",
            "Số điện thoại phòng đào tạo",
            "Liên hệ giáo viên chủ nhiệm"
        ]
    }
    
    centroids = {}
    
    print("Generating embeddings...")
    for category, phrases in categories.items():
        embeddings = []
        for phrase in phrases:
            # embedder.encode returns a numpy array for standard models, or list.
            vec = embedder.encode(phrase)
            if isinstance(vec, list):
                vec = np.array(vec)
            embeddings.append(vec)
            
        # Average the embeddings
        mean_vec = np.mean(embeddings, axis=0)
        
        # Normalize the centroid
        centroid = normalize_vector(mean_vec)
        centroids[category] = centroid
        print(f"Generated centroid for {category} (shape: {centroid.shape})")
        
    # Save all centroids to an .npz file
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/academic_chatbot_service/app/guardrails/multi_domain_centroids.npz'))
    np.savez(output_path, **centroids)
    print(f"Saved multiple centroids to {output_path}")

if __name__ == '__main__':
    generate_centroids()

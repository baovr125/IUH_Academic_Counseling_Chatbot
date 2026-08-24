import os
import json
import numpy as np
import asyncio
from sentence_transformers import SentenceTransformer

# 100 Diverse IUH Academic Questions
IUH_QUESTIONS = [
    # Học phí & Tài chính
    "Học phí 1 tín chỉ của trường Đại học Công nghiệp TP.HCM là bao nhiêu?",
    "Đóng học phí qua ngân hàng nào?",
    "Hạn chót đóng học phí học kỳ này là khi nào?",
    "Tại sao em chưa được gạch nợ học phí?",
    "Cách tính học phí hệ chất lượng cao có khác đại trà không?",
    "Bao giờ có danh sách cảnh báo học vụ do nợ học phí?",
    "Sinh viên thuộc diện hộ nghèo có được miễn giảm học phí không?",
    "Xin gia hạn đóng học phí cần những giấy tờ gì?",
    "Học phí học kỳ 1 năm 2026 là bao nhiêu?",
    "Đóng dư học phí thì trường có hoàn trả không?",
    
    # Đăng ký học phần
    "Khi nào bắt đầu đăng ký học phần kỳ 2?",
    "Làm sao để đăng ký học vượt?",
    "Môn học bị hủy thì có được đăng ký lại môn khác không?",
    "Lớp học phần bị đầy thì phải làm sao?",
    "Đăng ký học cải thiện thì điểm được tính như thế nào?",
    "Có được rút bớt môn học sau khi đã đóng học phí không?",
    "Rút môn học có được hoàn lại tiền không?",
    "Sinh viên năm cuối có được ưu tiên đăng ký môn không?",
    "Trùng thời khóa biểu thì xử lý ra sao?",
    "Web dkhp bị sập thì khi nào mở lại?",
    "Cách xem thời khóa biểu trên trang sinh viên?",
    "Đăng ký nhóm thực hành như thế nào?",
    "Điều kiện để đăng ký học lại là gì?",
    "Em lỡ quên đăng ký tín chỉ thì có bị cấm thi không?",
    
    # Xét tốt nghiệp & Chuẩn đầu ra
    "Bao nhiêu tín chỉ thì đủ điều kiện xét tốt nghiệp?",
    "Chuẩn đầu ra ngoại ngữ của trường là Toeic bao nhiêu?",
    "Chứng chỉ tin học IC3 có được xét chuẩn đầu ra không?",
    "Bao giờ có đợt xét tốt nghiệp tiếp theo?",
    "Làm sao để đăng ký xét tốt nghiệp trực tuyến?",
    "Em còn nợ 1 môn thì có được đi thực tập tốt nghiệp không?",
    "Bằng tốt nghiệp hệ đại trà và CLC có khác nhau không?",
    "Mất bằng tốt nghiệp có được cấp lại không?",
    "Lễ trao bằng tốt nghiệp thường tổ chức vào tháng mấy?",
    "Điều kiện để làm khóa luận tốt nghiệp là gì?",
    "GPA 3.2 thì tốt nghiệp loại gì?",
    "Bằng IELTS 6.0 có được quy đổi điểm tiếng Anh không?",
    
    # Ký túc xá & Ngoại trú
    "Cách đăng ký ký túc xá cho tân sinh viên?",
    "Chi phí ở ký túc xá 1 tháng là bao nhiêu?",
    "Ký túc xá có cho nấu ăn không?",
    "Nội quy giờ giấc của ký túc xá IUH như thế nào?",
    "Hồ sơ xin ở ký túc xá gồm những gì?",
    "Sinh viên năm 2 có được đăng ký ở KTX không?",
    "Giấy tạm vắng tạm trú làm ở đâu?",
    
    # Học bổng & Khen thưởng
    "Điều kiện xét học bổng khuyến khích học tập là gì?",
    "Điểm rèn luyện bao nhiêu thì được xét học bổng?",
    "Học bổng tân sinh viên được cấp khi nào?",
    "Trường có những loại học bổng tài trợ nào?",
    "Em bị rớt 1 môn thì có được xét học bổng không?",
    "Học cải thiện có được tính điểm để xét học bổng không?",
    "Bao giờ trường công bố danh sách nhận học bổng?",
    
    # Điểm số, Thi cử & Phúc khảo
    "Làm sao để xin hoãn thi cuối kỳ?",
    "Điều kiện để được thi lại là gì?",
    "Thời gian nộp đơn phúc khảo bài thi là bao lâu?",
    "Lệ phí phúc khảo là bao nhiêu?",
    "Xem điểm thi cuối kỳ ở đâu?",
    "Điểm quá trình chiếm bao nhiêu phần trăm tổng điểm?",
    "Tại sao điểm trên web chưa được cập nhật?",
    "Gian lận thi cử bị xử lý như thế nào?",
    "Cách tính điểm hệ 4 và hệ 10?",
    "Em vắng thi giữa kỳ có được thi cuối kỳ không?",
    "Nộp giấy khám bệnh để xin hoãn thi ở phòng nào?",
    "Thi rớt môn thực hành có được thi lại không?",
    
    # Giấy tờ hành chính & Thẻ sinh viên
    "Xin giấy xác nhận sinh viên để vay vốn ở đâu?",
    "Thủ tục cấp lại thẻ sinh viên bị mất?",
    "Mất biên lai đóng học phí có sao không?",
    "Mật khẩu wifi của trường là gì?",
    "Làm sao để đổi mật khẩu tài khoản sinh viên?",
    "Thẻ sinh viên có dùng làm thẻ ATM được không?",
    "Làm thẻ bảo hiểm y tế tại trường như thế nào?",
    "Sổ đoàn nộp cho ai?",
    "Quy trình xin chuyển ngành học?",
    "Muốn bảo lưu kết quả học tập thì cần điều kiện gì?",
    "Bảo lưu tối đa được mấy học kỳ?",
    "Xin bảng điểm tiếng Anh có dấu mộc ở đâu?",
    "Thời gian làm việc của Phòng Đào tạo?",
    
    # Quy chế đào tạo
    "Cảnh báo học vụ lần 1 có bị đuổi học không?",
    "GPA dưới bao nhiêu thì bị buộc thôi học?",
    "Quy định về trang phục khi đến trường?",
    "Sinh viên có được hút thuốc trong khuôn viên trường không?",
    "Chương trình học của ngành CNTT có bao nhiêu tín chỉ?",
    "Thang điểm đánh giá rèn luyện gồm những tiêu chí nào?",
    "Làm sao để tham gia các câu lạc bộ của trường?",
    "Số ngày nghỉ tối đa của một môn học là bao nhiêu?",
    "Vi phạm nội quy thi bị đình chỉ học mấy kỳ?",
    "Có bắt buộc mặc áo đoàn vào thứ 2 không?",
    
    # Đồ án & Thực tập
    "Bao giờ khoa IT tổ chức bảo vệ đồ án tốt nghiệp?",
    "Mẫu báo cáo thực tập tải ở đâu?",
    "Có được tự liên hệ công ty thực tập không?",
    "Trường có hỗ trợ giới thiệu chỗ thực tập không?",
    "Giấy giới thiệu thực tập xin ở đâu?",
    "Nộp báo cáo thực tập trễ có bị trừ điểm không?",
    "Hướng dẫn cách trình bày khóa luận tốt nghiệp?",
    "Đồ án chuyên ngành 1 có cần bảo vệ trước hội đồng không?",
    
    # Cấu trúc câu hỏi chung / Biến thể (Casual)
    "Cho em hỏi quy chế đào tạo tín chỉ tải ở đâu vậy ạ?",
    "Ad ơi cho hỏi học phí ngành ngôn ngữ anh là nhiêu?",
    "Trường mình có wifi miễn phí cho sv ko?",
    "dkhp đợt này web lag quá có được gia hạn ko?",
    "sv năm nhất có bắt buộc ở ktx ko?",
    "hướng dẫn nộp bảo hiểm y tế online",
    "cho xin link down biểu mẫu xin chuyển ngành",
    "khi nào thì có tkb kỳ mới v ad?",
    "điểm rèn luyện loại khá có bị ảnh hưởng gì ko?",
    "hôm nay phòng công tác sinh viên có làm việc không?",
    "muốn đăng ký học lại thì vào mục nào trên web?"
]

def main():
    print(f"Loading Model... Preparing to embed {len(IUH_QUESTIONS)} questions.")
    model_name = "bkai-foundation-models/vietnamese-bi-encoder"
    
    # This matches the model used in the RAG service
    model = SentenceTransformer(model_name)
    
    print("Generating embeddings...")
    embeddings = model.encode(IUH_QUESTIONS, show_progress_bar=True, convert_to_numpy=True)
    
    print("Calculating domain centroid (mean vector)...")
    centroid = np.mean(embeddings, axis=0)
    
    # Normalize the centroid vector for cosine similarity
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
        
    output_dir = "services/academic_chatbot_service/app/guardrails"
    os.makedirs(output_dir, exist_ok=True)
    
    centroid_path = os.path.join(output_dir, "academic_domain_centroid.npy")
    np.save(centroid_path, centroid)
    
    print(f"\n✅ Success! Centroid vector created and saved to: {centroid_path}")
    print(f"Centroid shape: {centroid.shape}")
    print(f"Norm of centroid: {np.linalg.norm(centroid):.4f}")

if __name__ == "__main__":
    main()

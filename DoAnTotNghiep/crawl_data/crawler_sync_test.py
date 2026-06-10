import os
import shutil

# 🟢 IMPORT hàm chunking từ file step2 của bạn
from step2_chunk_embed import process_single_markdown

# Thư mục đích chứa JSON (Watcher đang canh chừng thư mục này)
JSON_DOCS_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\data_json\json_documents"
os.makedirs(JSON_DOCS_DIR, exist_ok=True)

# Thư mục giả lập chứa Markdown mới cào về
NEW_MARKDOWN_DIR = r"G:\ChatBot\Code\Version1\chatbox_IUH\markdown_updates"
os.makedirs(NEW_MARKDOWN_DIR, exist_ok=True)

def simulate_real_web_update():
    print("="*60)
    print("🌐 ĐANG CHẠY KỊCH BẢN: CÀO VÀ XỬ LÝ DỮ LIỆU ĐỘNG...")
    print("="*60)
    
    # 1. TẠO FILE MARKDOWN GIẢ LẬP (Mô phỏng Crawler cào bài mới về)
    # Trong thực tế, Tool Crawler của bạn sẽ tải file .md này vào thư mục.
    sample_md_filename = "thong-bao-nghi-le-2026.md"
    sample_md_path = os.path.join(NEW_MARKDOWN_DIR, sample_md_filename)
    
    # Nội dung Markdown chuẩn có Front Matter (giống format Cẩm nang IUH)
    markdown_content = """---
source_url: "https://camnang.iuh.edu.vn/thong-bao-nghi-le-2026"
title: "Thông báo nghỉ Lễ Quốc Khánh năm 2026"
---
# THÔNG BÁO NGHỈ LỄ QUỐC KHÁNH
Sinh viên toàn trường được nghỉ Lễ Quốc khánh từ ngày 01/09/2026 đến hết ngày 04/09/2026.
Ngày 05/09/2026 (Thứ 7) toàn trường đi học lại bình thường theo thời khóa biểu. 
Để đảm bảo an toàn trong dịp lễ, Phòng Công tác Sinh viên yêu cầu toàn thể các bạn sinh viên chấp hành nghiêm chỉnh luật lệ giao thông khi di chuyển về quê hoặc đi du lịch. 
Tuyệt đối không tham gia các hoạt động nguy hiểm, không sử dụng rượu bia khi tham gia giao thông. Nhà trường chúc các bạn sinh viên và gia đình có một kỳ nghỉ lễ thật vui vẻ, đầm ấm và an toàn!
"""
    
    with open(sample_md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"1. Đã giả lập tải file Markdown mới về: {sample_md_filename}")
    
    # 2. GỌI HÀM CHUNKING TỪ STEP 2
    print("2. Bắt đầu gọi tiến trình Chunking...")
    success = process_single_markdown(sample_md_path, JSON_DOCS_DIR)
    
    # 3. KẾT LUẬN
    if success:
        print("\n🎉 HOÀN TẤT!")
        print("👉 File JSON đã được đẩy vào thư mục json_documents.")
        print("👉 Kẻ giám sát (Watcher) sẽ tự động bắt lấy file này và đưa vào ChromaDB!")
        
        # (Tùy chọn) Xóa file md sau khi xử lý xong cho sạch
        # os.remove(sample_md_path)
    else:
        print("\n❌ Thất bại trong việc xử lý file Markdown.")

if __name__ == "__main__":
    simulate_real_web_update()
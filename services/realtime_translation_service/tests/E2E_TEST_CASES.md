# Bảng Kiểm Thử Giao Diện (Selenium E2E Test Cases)
**Chức năng:** Premium Terminology & Warning Logic (Realtime Translation)
**Mục tiêu:** Xác minh luồng giao diện người dùng từ lúc nhập văn bản, chọn domain, đến lúc hiển thị cảnh báo (Warning Alert) một cách chính xác theo logic Backend.

---

| Test Item | Pre-Condition | Test Data | Test Steps | Expected Results | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-TC01:** Dịch thành công thuật ngữ <=3 từ, không kích hoạt cảnh báo. | - Frontend & Backend chạy.<br>- Data JSON chuyên ngành IT. | - **Domain:** "Công nghệ Thông tin (IT)"<br>- **Input:** `Memory leak` | 1. Mở trang dịch thuật.<br>2. Chọn Domain IT.<br>3. Nhập `Memory leak`.<br>4. Chờ dịch vụ hoàn tất.<br>5. Chụp ảnh màn hình. | - Kết quả chứa cụm từ `"rò rỉ bộ nhớ"`.<br>- **KHÔNG** hiển thị Banner màu cam. | High |
| **E2E-TC02:** Kích hoạt cảnh báo thiếu từ khóa (Fallback NLLB). | - Frontend & Backend chạy. | - **Domain:** "Công nghệ Thông tin (IT)"<br>- **Input:** `Random unknown word` | Nhập văn bản không có trong Dictionary. | - Dịch từ NLLB.<br>- **HIỂN THỊ** Banner: *"⚠️ Cảnh báo: Từ/cụm từ này không được tìm thấy..."* | High |
| **E2E-TC03:** Dịch thành công câu dài chứa thuật ngữ chuyên khoa (LLM Flow). | - Data JSON chuyên khoa Y. | - **Domain:** "Y khoa / Sức khỏe"<br>- **Input:** `Checking drug interaction is extremely important.` | Nhập câu dài >= 4 từ, có chứa "drug interaction". | - Kết quả chứa `"tương tác thuốc"`.<br>- **KHÔNG** hiển thị Banner cảnh báo. | High |
| **E2E-TC04:** Kích hoạt cảnh báo khi LLM chuyên ngành bị lỗi. | - Backend được cấu hình chạy Mock/Invalid API Keys để ép lỗi LLM. | - **Domain:** "Công nghệ Thông tin (IT)"<br>- **Input:** `A memory leak causes crashes` | Nhập câu dài >= 4 từ, có chứa từ vựng. Đợi hệ thống xử lý qua LLM nhưng bị lỗi. | - Dịch từ NLLB fallback.<br>- **HIỂN THỊ** Banner: *"⚠️ Cảnh báo: Hệ thống không thể dịch bằng AI model chuyên ngành..."* | Medium |
| **E2E-TC05:** Dịch câu dài KHÔNG chứa thuật ngữ chuyên ngành. | - Frontend & Backend chạy ổn định. | - **Domain:** "Y khoa / Sức khỏe"<br>- **Input:** `This is just a normal sentence to translate.` | Nhập câu dài >= 4 từ, nhưng là một câu tiếng Anh hoàn toàn bình thường. | - Dịch thẳng qua NLLB một cách trơn tru.<br>- **KHÔNG** hiển thị Banner cảnh báo (tránh cảnh báo sai). | Medium |
| **E2E-TC06:** Xử lý case-insensitivity và ký tự đặc biệt trên UI. | - Data JSON chuyên ngành IT. | - **Domain:** "Công nghệ Thông tin (IT)"<br>- **Input:** `MEMORY LEAK` | Nhập thuật ngữ với chữ IN HOA toàn bộ, thay vì chữ thường như trong từ điển. | - Kết quả chứa `"rò rỉ bộ nhớ"`.<br>- Hệ thống tự map đúng, **KHÔNG** hiển thị Banner cảnh báo sai. | Low |
| **E2E-TC07:** Dịch Luồng 1 (Không chọn Domain) - Câu ngắn. | - Frontend & Backend chạy bình thường. | - **Domain:** "Dịch thông thường (Mặc định)" hoặc KHÔNG chọn.<br>- **Input:** `Memory leak` | 1. Mở trang dịch thuật.<br>2. Chọn Domain Mặc định.<br>3. Nhập từ khóa.<br>4. Chụp màn hình. | - Kết quả dịch thô bằng NLLB (có thể không sát nghĩa chuyên ngành).<br>- **KHÔNG** kích hoạt bộ lọc thuật ngữ, **KHÔNG** hiển thị cảnh báo. | High |
| **E2E-TC08:** Dịch Luồng 1 (Không chọn Domain) - Câu dài. | - Frontend & Backend chạy bình thường. | - **Domain:** "Dịch thông thường (Mặc định)"<br>- **Input:** `A memory leak causes crashes` | 1. Mở trang dịch thuật.<br>2. Chọn Domain Mặc định.<br>3. Nhập câu dài.<br>4. Chụp màn hình. | - Dịch NLLB một cách trơn tru.<br>- Tuyệt đối **KHÔNG** gọi LLM Groq/Gemini, **KHÔNG** hiển thị cảnh báo. | High |

---

## Ghi chú cho quá trình Automation (Pytest-Selenium):
- **Cấu trúc lưu Screenshot:** Ảnh chụp sẽ được lưu tại `tests/e2e/screenshots/terminology/`. Tên ảnh được định dạng là `{Test_Item_ID}_{Trạng_Thái}.png`.
- **Kỹ thuật Wait:** Dùng `WebDriverWait` để dò sự kiện DOM, chờ Banner hiển thị hoặc Timeout (nếu test case kỳ vọng không có Banner).
- Đối với **E2E-TC04**, cần thiết lập fixture trong Pytest để tạm thời mock/tắt API LLM ở tầng Backend khi chạy test E2E.

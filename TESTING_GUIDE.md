# Cẩm Nang Kiểm Thử Tự Động Toàn Diện (Automated Testing & Quality Gates Guide)

Hệ thống **IUH Microservices AI** áp dụng nguyên tắc cốt lõi:
> **"Mọi thay đổi hoặc hành động chạy/commit code đều phải đi kèm với kiểm thử và vượt qua 100% test suites."**

Tài liệu này hướng dẫn toàn bộ quy trình thiết lập môi trường, thực thi kiểm thử với 1 lệnh, quy chuẩn Mocking và phương pháp viết test case mới cho cả Backend và Frontend.

---

## 1. Cấu Trúc Kiểm Thử (Microservices Isolated Test Structure)

Hệ thống tuân thủ kiến trúc **Database-per-service** và phân tách các tầng kiểm thử độc lập:

```
IUH_Academic_Counseling_Chatbot/
├── services/
│   ├── <service_name>/
│   │   ├── pytest.ini            # Cấu hình Pytest riêng cho service
│   │   └── tests/
│   │       ├── conftest.py       # Thiết lập test client, biến môi trường test
│   │       ├── fixtures/         # Mock Supabase, Redis, RabbitMQ, MinIO, Gemini
│   │       ├── unit/             # Kiểm thử logic nghiệp vụ nội bộ (Domain/Service/Schema)
│   │       └── integration/      # Kiểm thử API Router qua TestClient với mocked dependencies
├── frontend/
│   ├── vite.config.ts            # Cấu hình jsdom, globals, setupFiles
│   └── tests/
│       ├── setupTests.ts         # @testing-library/jest-dom matchers
│       ├── FlashcardCard.test.tsx
│       ├── ChatMessageBubble.test.tsx
│       └── chatService.test.ts
├── scripts/
│   └── eval/
│       └── test_rag_benchmark.py # Đánh giá Hit Rate@K, MRR@K, Latency
├── run_tests.bat                 # Script chạy test 1-click (Windows CMD / PowerShell)
├── run_tests.sh                  # Script chạy test 1-click (Linux / macOS / CI)
├── .pre-commit-config.yaml       # Pre-commit hook framework
└── .github/workflows/ci.yml      # GitHub Actions CI Matrix Pipeline
```

---

## 2. Hướng Dẫn Chạy Kiểm Thử Bằng 1 Câu Lệnh

### 2.1. Trên Windows (PowerShell hoặc Command Prompt)
Chạy script `run_tests.bat` từ thư mục gốc dự án:

```bat
:: Chạy toàn bộ test suites (5 Backend Services + Frontend + RAG Eval)
run_tests.bat

:: Chạy riêng từng Microservice mong muốn
run_tests.bat auth         :: Chỉ test Auth Service & đo Coverage
run_tests.bat academic     :: Chỉ test Academic Chatbot Service
run_tests.bat realtime     :: Chỉ test Real-time Translation Service
run_tests.bat doc          :: Chỉ test Document Translation & RAG Service
run_tests.bat flashcard    :: Chỉ test Flashcard Spaced Repetition Service
run_tests.bat frontend     :: Chỉ test Frontend (Vitest)
run_tests.bat eval         :: Chỉ test RAG Benchmark Evaluation
```

### 2.2. Trên Linux / macOS / Docker / CI
Cấp quyền thực thi và chạy script `run_tests.sh`:

```bash
chmod +x run_tests.sh

# Chạy toàn bộ test suites
./run_tests.sh

# Hoặc chạy riêng từng service
./run_tests.sh auth
./run_tests.sh academic
./run_tests.sh realtime
./run_tests.sh doc
./run_tests.sh flashcard
./run_tests.sh frontend
./run_tests.sh eval
```

---

## 3. Quy Chuẩn Mock Dữ Liệu Ngoại Vi (Zero External Dependency)

Mọi Unit và Integration Test **tuyệt đối không phụ thuộc vào mạng internet hay API Key thật**. Mọi thành phần ngoại vi đều được giả lập (Mock) thông qua `unittest.mock`:

### 3.1. Mock Supabase Database & RPC
```python
from unittest.mock import MagicMock, patch

def test_example_with_mock_supabase(client):
    with patch("app.services.auth_service.get_supabase") as mock_sb:
        mock_client = MagicMock()
        # Giả lập trả về danh sách người dùng
        mock_client.table().select().eq().execute.return_value.data = [
            {"id": "user-123", "email": "student@student.iuh.edu.vn"}
        ]
        mock_sb.return_value = mock_client

        # Gọi API hoặc Service cần test
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer valid_token"})
        assert res.status_code == 200
```

### 3.2. Mock Redis Semantic Cache
```python
from unittest.mock import patch, MagicMock

def test_example_with_mock_redis():
    with patch("app.services.cache_service.get_redis") as mock_get_redis:
        mock_redis = MagicMock()
        mock_redis.get.return_value = "dữ liệu đã dịch trong cache"
        mock_get_redis.return_value = mock_redis

        # Kiểm tra logic đọc cache
        val = get_cached_translation("hello_en_vi")
        assert val == "dữ liệu đã dịch trong cache"
```

### 3.3. Mock Google Gemini LLM API
```python
from unittest.mock import patch, MagicMock

def test_example_with_mock_gemini():
    with patch("app.services.rag_service.get_gemini") as mock_gemini:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Câu trả lời tư vấn từ Gemini LLM."
        mock_client.models.generate_content.return_value = mock_response
        mock_gemini.return_value = mock_client
```

### 3.4. Mock MinIO S3 Object Storage & Edge-TTS
```python
from unittest.mock import patch, MagicMock

def test_example_with_mock_minio():
    with patch("app.utils.minio_client.audio_exists", return_value=True), \
         patch("app.utils.minio_client.get_audio_bytes", return_value=b"\xff\xfb\x90\x44"):
        # Test trả về file MP3 có sẵn trong S3
        pass
```

---

## 4. Hướng Dẫn Từng Bước Viết Thêm Test Case Mới

### 4.1. Thêm Unit Test mới cho Backend (FastAPI / Python)
1. Tạo file kiểm thử trong thư mục `services/<service_name>/tests/unit/test_<feature>.py`.
2. Khai báo class kiểm thử và các hàm `test_*`:
```python
import pytest
from app.services.my_service import calculate_score

class TestMyFeature:
    def test_calculate_score_with_valid_input(self):
        # 1. Arrange (Chuẩn bị dữ liệu)
        input_data = [10, 20, 30]
        
        # 2. Act (Thực thi)
        result = calculate_score(input_data)
        
        # 3. Assert (Xác minh kết quả)
        assert result == 60

    def test_calculate_score_with_empty_input_raises_error(self):
        with pytest.raises(ValueError):
            calculate_score([])
```

### 4.2. Thêm Integration Test mới cho Backend API
1. Đặt trong thư mục `services/<service_name>/tests/integration/test_<api>.py`.
2. Sử dụng fixture `client` được cung cấp bởi `conftest.py`:
```python
def test_create_resource_api(client):
    res = client.post("/api/v1/resource", json={"name": "Test Item"})
    assert res.status_code == 201
    data = res.json()
    assert data["ok"] is True
    assert data["data"]["name"] == "Test Item"
```

### 4.3. Thêm Component Test mới cho Frontend (React / Vitest / RTL)
1. Tạo file `frontend/tests/<ComponentName>.test.tsx`.
2. Sử dụng `@testing-library/react` để render component và mô phỏng tương tác:
```tsx
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MyButton } from "../src/components/MyButton";

describe("MyButton Component", () => {
  it("renders label and handles click event", () => {
    const handleClick = vi.fn();
    render(<MyButton label="Gửi tin nhắn" onClick={handleClick} />);

    const btn = screen.getByRole("button", { name: /Gửi tin nhắn/i });
    expect(btn).toBeInTheDocument();

    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

---

## 5. Tự Động Hóa Với Git Pre-Commit Hook

Hệ thống đã cấu hình sẵn Git Pre-commit Hook tại `.git/hooks/pre-commit` và `.pre-commit-config.yaml`.
- Mỗi khi lập trình viên thực hiện lệnh `git commit`, script sẽ tự động quét các file trong Staging Area (`git diff --cached --name-only`).
- Chỉ kích hoạt test suites của Microservice có code bị chỉnh sửa (giúp tốc độ commit nhanh, không gây gián đoạn).
- Nếu có bất kỳ test case nào **FAIL**, lệnh commit sẽ **lập tức bị hủy** và thông báo lỗi kèm vị trí dòng code gây lỗi.

---

## 6. Tiêu Chuẩn Đo Lường Code Coverage ($\ge 80\%$)

Mọi Microservice phải duy trì độ bao phủ mã nguồn tối thiểu **80%**. Khi chạy PyTest, bảng báo cáo độ bao phủ chi tiết theo từng file sẽ được in ra:

```bash
pytest services/auth_service/tests -v --cov=services/auth_service/app --cov-fail-under=80
```
Nếu Code Coverage dưới 80%, quá trình build sẽ tự động dừng với mã lỗi `exit 1`.

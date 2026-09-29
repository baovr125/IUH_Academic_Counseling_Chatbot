from locust import HttpUser, task, between

class TranslationUser(HttpUser):
    wait_time = between(1, 3) # Chờ 1-3 giây giữa các request
    
    def on_start(self):
        # Thiết lập header bypass JWT Auth
        self.client.headers = {
            "Content-Type": "application/json",
            "X-User-ID": "admin-evaluation"
        }

    @task(3) # Tỉ lệ gọi API thường (không thuật ngữ)
    def test_general_translation(self):
        payload = {
            "text": "The Industrial University of Ho Chi Minh City is a large university in Vietnam.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "general"
        }
        self.client.post("/api/v1/translate/text", json=payload, name="/text (General)")

    @task(1) # Tỉ lệ gọi API chứa thuật ngữ (Ép hệ thống dùng Glossary Bypass)
    def test_academic_translation(self):
        payload = {
            "text": "Students must complete all prerequisite courses before registering for the thesis.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "academic"
        }
        self.client.post("/api/v1/translate/text", json=payload, name="/text (Academic)")
        
    @task(1) # Tỉ lệ gọi API Stream (Mô phỏng UI Typing)
    def test_stream_translation(self):
        payload = {
            "text": "The Realtime Translation Service aims to solve the latency problem.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "general"
        }
        # Lưu ý: stream=True để đọc SSE chunk
        with self.client.post("/api/v1/translate/stream", json=payload, stream=True, name="/stream (SSE)") as response:
            for line in response.iter_lines():
                if line:
                    pass

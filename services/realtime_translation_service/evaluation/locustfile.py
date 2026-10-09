from locust import HttpUser, task, between

class TranslationUser(HttpUser):
    wait_time = between(1, 3) # Chờ 1-3 giây giữa các request
    
    def on_start(self):
        # Thiết lập header bypass JWT Auth
        self.client.headers = {
            "Content-Type": "application/json",
            "X-User-ID": "admin-evaluation"
        }

    @staticmethod
    def _validate_translation_response(response):
        if response.status_code != 200:
            response.failure(f"Failed with status {response.status_code}")
            return
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            response.failure(f"Invalid JSON response: {exc}")
            return
        translation = (payload.get("data") or {}).get("translated_text")
        if payload.get("ok") is not True or not isinstance(translation, str) or not translation.strip():
            response.failure("Response did not contain a successful non-empty translation")

    @task(3) # Tỉ lệ gọi API thường (không thuật ngữ)
    def test_general_translation(self):
        payload = {
            "text": "The Industrial University of Ho Chi Minh City is a large university in Vietnam.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "Dịch thông thường (Mặc định)"
        }
        with self.client.post("/api/v1/translate/text", json=payload, name="/text (General)", catch_response=True) as response:
            self._validate_translation_response(response)

    @task(1) # Tỉ lệ gọi API chứa thuật ngữ (Ép hệ thống dùng Glossary Bypass)
    def test_academic_translation(self):
        payload = {
            "text": "Students must complete all prerequisite courses before registering for the thesis.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "Công nghệ Thông tin (IT)"
        }
        with self.client.post("/api/v1/translate/text", json=payload, name="/text (Academic)", catch_response=True) as response:
            self._validate_translation_response(response)
        
    @task(1) # Tỉ lệ gọi API Stream (Mô phỏng UI Typing)
    def test_stream_translation(self):
        payload = {
            "text": "The Realtime Translation Service aims to solve the latency problem.",
            "source_lang": "en",
            "target_lang": "vi",
            "domain": "Dịch thông thường (Mặc định)"
        }
        # Lưu ý: stream=True để đọc SSE chunk
        with self.client.post("/api/v1/translate/stream", json=payload, stream=True, name="/stream (SSE)", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed with status {response.status_code}")
                return
            try:
                import json
                translated_text_seen = False
                stream_error = None
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
                        if decoded_line.startswith("data:"):
                            try:
                                data = json.loads(decoded_line[5:].strip())
                                if not isinstance(data, dict):
                                    stream_error = "SSE data payload was not a JSON object"
                                    break
                                if "error" in data:
                                    stream_error = f"SSE error: {data['error']}"
                                    break
                                if isinstance(data.get("text"), str) and data["text"].strip():
                                    translated_text_seen = True
                            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                                stream_error = f"Invalid SSE data payload: {exc}"
                                break
                if stream_error:
                    response.failure(stream_error)
                elif not translated_text_seen:
                    response.failure("SSE completed without translated text")
            except Exception as e:
                response.failure(f"Stream interrupted: {str(e)}")

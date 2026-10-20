FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# Cập nhật pip/setuptools của image gốc (pip-audit báo các CVE đã có bản vá ở pip>=26.2, setuptools>=83).
RUN pip install --no-cache-dir --upgrade pip setuptools && pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]

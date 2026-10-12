FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đúng các phiên bản đã khóa để build tái lập được.
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.lock

COPY app ./app

# Không chạy bằng root.
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3).status == 200 else 1)"

# Một worker: bộ đếm chống dò mật khẩu nằm trong bộ nhớ tiến trình (xem app/utils/throttle.py).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 \
    torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8002

# Suppress TensorRT provider warnings: only use CUDA and CPU providers
ENV ORT_TENSORRT_DUMMY_LOAD=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

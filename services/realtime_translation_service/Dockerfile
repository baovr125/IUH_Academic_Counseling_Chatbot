FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 torch==2.5.1
RUN pip install --no-cache-dir nvidia-cublas-cu12 nvidia-cudnn-cu12

ENV LD_LIBRARY_PATH="/usr/local/lib/python3.10/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.10/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH}"
ENV CUDA_MODULE_LOADING="LAZY"

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

# Download the NLLB model during image build and clean HuggingFace cache
RUN python download_model.py && rm -rf /root/.cache/huggingface

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

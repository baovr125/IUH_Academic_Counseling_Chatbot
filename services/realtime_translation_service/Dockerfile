FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 torch --extra-index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

# Download the NLLB model during image build and clean HuggingFace cache
RUN python download_model.py && rm -rf /root/.cache/huggingface

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

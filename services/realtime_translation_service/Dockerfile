FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

# Download the NLLB model during image build
RUN python download_model.py

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

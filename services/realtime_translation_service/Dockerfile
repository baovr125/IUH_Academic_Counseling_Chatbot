FROM python:3.11-slim

WORKDIR /app

ENV NLLB_MODEL_DIR=/app/models/nllb-200-distilled-600M-ct2-int8 \
    FASTTEXT_LID_MODEL=/app/models/lid.176.ftz \
    NLLB_DEVICE=auto

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

# NLTK corpora required by Word Analysis (WordNet + multilingual mappings).
RUN python -m nltk.downloader -d /usr/local/share/nltk_data wordnet omw-1.4

# CUDA 12 runtime libraries for CTranslate2 GPU inference.
RUN pip install --no-cache-dir \
    nvidia-cuda-runtime-cu12==12.1.105 \
    nvidia-cublas-cu12==12.1.3.1 \
    nvidia-cudnn-cu12==9.1.0.70

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib
ENV NLTK_DATA=/usr/local/share/nltk_data

# Download SpaCy and NLTK models for Word Analysis
RUN pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz

COPY . .

# Download the NLLB model during image build and clean HuggingFace cache
RUN python download_model.py \
    && python verify_models.py \
    && rm -rf /root/.cache/huggingface

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 torch==2.5.1

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

import logging
import contextvars
from pythonjsonlogger import jsonlogger

request_id_var = contextvars.ContextVar("request_id", default="N/A")

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['service'] = 'academic_chatbot_service'
        log_record['request_id'] = request_id_var.get()

logger = logging.getLogger("academic_chatbot_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(service)s %(request_id)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
import os

LOG_DIR = "/app/logs/academic_chatbot"
os.makedirs(LOG_DIR, exist_ok=True)
TRACE_FILE = os.path.join(LOG_DIR, "query_traces.jsonl")

def log_query_trace(session_id: str, original_query: str, retrieval_query: str, retrieved_chunks: list, ai_response: str):
    import json
    import datetime
    try:
        trace = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "session_id": session_id,
            "original_query": original_query,
            "retrieval_query": retrieval_query,
            "retrieved_chunks": retrieved_chunks,
            "ai_response": ai_response,
        }
        with open(TRACE_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write query trace: {e}")

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
    formatter = CustomJsonFormatter(
        '%(asctime)s %(levelname)s %(service)s %(request_id)s %(message)s',
        rename_fields={'asctime': 'timestamp', 'levelname': 'level'},  # khóa JSON: timestamp/level
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

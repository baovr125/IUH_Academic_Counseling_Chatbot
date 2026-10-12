import contextvars
import logging

try:  # python-json-logger >= 3.1
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # phiên bản cũ hơn
    from pythonjsonlogger.jsonlogger import JsonFormatter

request_id_var = contextvars.ContextVar("request_id", default="N/A")


class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "auth_service"
        log_record["request_id"] = request_id_var.get()


logger = logging.getLogger("auth_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    # asctime/levelname là thuộc tính thật của LogRecord; rename để khóa JSON là timestamp/level.
    handler.setFormatter(CustomJsonFormatter(
        "%(asctime)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    ))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

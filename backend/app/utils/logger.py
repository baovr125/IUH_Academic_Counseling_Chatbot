import logging
import sys
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar
import uuid

# Context variable to hold the current request_id
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

def get_logger(name: str = "iuh_portal_ai"):
    logger = logging.getLogger(name)
    
    # Only configure if no handlers are present to prevent duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        log_handler = logging.StreamHandler(sys.stdout)
        
        # Define fields to output in JSON
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
        
        log_handler.setFormatter(formatter)
        log_handler.addFilter(RequestIdFilter())
        
        logger.addHandler(log_handler)
        
    return logger

# Default global logger instance
logger = get_logger()

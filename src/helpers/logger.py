# helpers/logger.py
import logging
import sys
import contextvars

# store user_id for current request
current_user_id = contextvars.ContextVar("current_user_id", default="anonymous")

class RequestFilter(logging.Filter):
    def filter(self, record):
        record.user_id = current_user_id.get()
        return True

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [user=%(user_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addFilter(RequestFilter())
    return logger

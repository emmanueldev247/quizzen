import json
import logging
import os
import re
from colorlog import ColoredFormatter
from flask import has_request_context, request
from logging.handlers import RotatingFileHandler


# Ensure the logs directory exists
log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

def redact_email(message):
    """Redact emails in log messages by keeping first 3 letters and domain."""
    return re.sub(
        r'\b([A-Za-z0-9._%+-]{3})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b',
        r'\1***@\2',
        message
    )

def get_client_ip():
    if has_request_context():
        try:
            x_forwarded_for = request.headers.get("X-Forwarded-For", "")
            if x_forwarded_for:
                return x_forwarded_for.split(",")[0].strip()
            elif request.headers.get("X-Real-Ip", ""):
                x_real_ip = request.headers.get("X-Real-Ip", "")
                return x_real_ip.split(",")[0].strip()
            elif hasattr(request, 'remote_addr'):
                return request.remote_addr
            else:
                return 'N/A'
        except Exception as e:
            logger.error(f"Error retrieving client IP: {e}")
            return 'N/A'
    else:
        return 'N/A'

class RedactingFormatter(logging.Formatter):
    """Formatter to redact sensitive user information."""
    def format(self, record):
        # Redact email in the message
        getattr(record, 'user_id', 'N/A')
        record.msg = redact_email(record.msg)
        return super().format(record)
        

class RequestFormatter(logging.Formatter):
    """Custom log formatter to include client IP."""
    def format(self, record):
        record.client_ip = get_client_ip()
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for detailed logs."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "client_ip": getattr(record, "client_ip", "N/A"),
            "message": record.getMessage(),
            "file": record.pathname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        return json.dumps(log_record)


def setup_logger():
    """Set up logging for the application."""
    logger = logging.getLogger('quizzen_app')

    if len(logger.handlers) > 0:
        return logger

    # if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

        # ---- 1. Rotating File Logger for JSON ---- #
    json_file = os.path.join(log_dir, 'structured_logs.json')
    json_file_handler = RotatingFileHandler(json_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    json_file_handler.setLevel(logging.INFO)
    json_file_handler.setFormatter(JSONFormatter(
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # ---- 2. File Logger for Redacted User Details ---- #
    user_log_file = os.path.join(log_dir, 'user_logs.log')
    user_file_handler = RotatingFileHandler(user_log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    user_file_handler.setLevel(logging.INFO)
    user_file_handler.setFormatter(RedactingFormatter(
        '%(asctime)s - %(levelname)s - [USER ID: %(user_id)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # ---- 3. Color-Coded Console Logger ---- #
    console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d --> [%(client_ip)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    ))

    # ---- 4. File Logger for General app ---- #
    log_file = os.path.join(log_dir, 'app.log')   
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    # file_handler.setLevel(logging.DEBUG)   
    formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d --> [%(client_ip)s] %(message)s'
    )
    
    logger.addHandler(json_file_handler)
    logger.addHandler(user_file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
        
    return logger
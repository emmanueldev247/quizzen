import logging
import os
from flask import request
from logging.handlers import RotatingFileHandler


# Ensure the logs directory exists
log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class RequestFormatter(logging.Formatter):
    """Custom log formatter to include client IP."""
    def format(self, record):
        try:
            x_forwarded_for = request.headers.get("X-Forwarded-For", "")
            if x_forwarded_for:
                record.client_ip = x_forwarded_for.split(",")[0].strip()
            elif request.headers.get("X-Real-Ip", ""):
                x_real_ip = request.headers.get("X-Real-Ip", "")
                record.client_ip = x_real_ip.split(",")[0].strip()
            elif hasattr(request, 'remote_addr'):
                record.client_ip = request.remote_addr
            else:
                record.client_ip = 'N/A'
        except Exception as e:
            record.client_ip = f'Error: {str(e)}'
    return super().format(record)

def setup_logger():
    """Set up logging for the application."""
    logger = logging.getLogger('quizzen_app')
    logger.setLevel(logging.DEBUG)

    log_file = os.path.join(log_dir, 'app.log')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG)
    
    # Create a console handler for logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(client_ip)s] %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
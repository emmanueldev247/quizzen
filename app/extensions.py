"""Extensions to prevent circular import error"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_migrate import Migrate
from flask_mail import Mail
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_ip_from_proxy():
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.remote_addr

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
session = Session()
migrate = Migrate()
mail = Mail()
limiter = Limiter(
    key_func=get_ip_from_proxy,
    storage_uri="redis://localhost:6379/0",
    default_limits=["200 per day", "50 per hour"]
)
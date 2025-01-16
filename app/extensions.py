"""Extensions to prevent circular import error"""

import humanize
import os
import redis
from datetime import datetime, timezone
from flask import Blueprint, Flask, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# from authlib.integrations.flask_client import OAuth

def get_ip_from_proxy():
    """gets ip from clients for logger"""
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-Ip", "")
    if x_real_ip:
        return x_real_ip.split(",")[0].strip()
    return request.remote_addr


def timeago_filter(value):
    """Convert a datetime object to 'time ago' format."""
    if isinstance(value, datetime):
        current_time = datetime.now(timezone.utc)

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return humanize.naturaltime(current_time - value)
    return value


# Initialize extensions
# oauth = OAuth()
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
jwt = JWTManager()
blacklist_redis = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB1', 1)),
    decode_responses=True
)


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """checks for jwt revoke status"""
    jti = jwt_payload["jti"]
    return blacklist_redis.get(jti) is not None

# Blueprints
full_bp = Blueprint('full_bp', __name__, url_prefix='/quizzen')
api_v1 = Blueprint('api_v1', __name__, url_prefix='/quizzen/api/v1')
oauth_bp = Blueprint('oauth', __name__, url_prefix='quizzen/auth/google')
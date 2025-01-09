"""Extensions to prevent circular import error"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_migrate import Migrate
from flask_mail import Mail
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
import redis

def get_ip_from_proxy():
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-Ip", "")
    if x_real_ip:
        return x_real_ip.split(",")[0].strip()
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
jwt = JWTManager()
blacklist_redis = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.get('REDIS_DB1', 1)),
    decode_responses=True
)

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return blacklist_redis.get(jti) is not None
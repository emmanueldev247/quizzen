import unicodedata
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from app.models import User
from app.extensions import blacklist_redis, limiter
from . import api_v1

@api_v1.route('/connect', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json

    email = unicodedata.normalize(
                'NFKC', data.get('email', '').strip().lower()
            )
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({"success": True, "access_token":access_token}), 200
    return jsonify({"success": False, "error": "Invalid credentials"}), 401


@api_v1.route('/disconnect', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def logout():
    jti = get_jwt()["jti"]
    blacklist_redis.set(jti, "blacklisted", ex=60*60)
    return jsonify({"success": True, "msg": "Token successfully disconnected"})

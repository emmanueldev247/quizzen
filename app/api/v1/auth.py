import unicodedata
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, exceptions as jwt_exceptions
from jwt.exceptions import (
    NoAuthorizationError,
    RevokedTokenError,
    ExpiredSignatureError,
    InvalidTokenError,
)
from app.models import User
from app.extensions import blacklist_redis, limiter, jwt
from app.routes import logger
from . import api_v1
from werkzeug.exceptions import Unauthorized


@jwt.unauthorized_loader
def unauthorized_response(error):
    """Handle unauthorized errors when token is missing or invalid."""
    return jsonify({
        "success": False,
        "error": "Unauthorized access",
        "message": "Request must include an Authorization header with a valid token"
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_data):
    """Handle token revoked errors"""
    return jsonify({
        "success": False,
        "error": "Revoked Token",
        "message": "Token has been revoked. Please re-authenticate."
    }), 401
    
# Blueprint error handlers
@api_v1.errorhandler(ExpiredSignatureError)
def handle_expired_token_error(e):
    response = {
        "success": False,
        "error": "Expired Token",
        "message": "Your session has expired. Please log in again."
    }
    return jsonify(response), 401

@api_v1.errorhandler(InvalidTokenError)
def handle_invalid_token_error(e):
    response = {
        "success": False,
        "error": "Invalid Token",
        "message": "Invalid token. Please provide a valid token."
    }
    return jsonify(response), 400

@api_v1.errorhandler(405)
def handle_not_allowed_error(e):
    logger.error(f"Method not allowed error: {str(e)}")
    response = {
        "success": False,
        "error": 405,
        "message": "Method Not Allowed"
    }
    return jsonify(response), 405

@api_v1.errorhandler(404)
def handle_not_found_error(e):
    response = {
        "success": False,
        "error": 404,
        "message": "Endpoint not found"
    }
    return jsonify(response), 404

@api_v1.errorhandler(429)
def handle_rate_limit_error(e):
    response = {
        "success": False,
        "error": 429,
        "message": "Too many requests. Please try again later"
    }
    return jsonify(response), 429

@api_v1.errorhandler(Exception)
def handle_generic_error(e):
    if isinstance(e, (NoAuthorizationError, RevokedTokenError, ExpiredSignatureError, InvalidTokenError)):
        raise e 

    response = {
        "success": False,
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later."
    }
    logger.error(f"Unhandled exception: {e}")
    return jsonify(response), 500


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
    return jsonify({"success": True, "message": "Token successfully disconnected"})

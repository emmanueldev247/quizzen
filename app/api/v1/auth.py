import unicodedata
from flask import request, jsonify, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from flask_jwt_extended.exceptions import (
    NoAuthorizationError,
    RevokedTokenError
)
from jwt.exceptions import (
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
        "message": "Authorization header with valid token is required"
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
        "message": "Your session has expired. Please re-authenticate."
    }
    return jsonify(response), 401

@api_v1.errorhandler(InvalidTokenError)
def handle_invalid_token_error(e):
    response = {
        "success": False,
        "error": "Invalid Token",
        "message": "Provided token is invalid. Please re-authenticate."
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
    logger.error(f"Method not allowed: {str(e)}")
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
        "message": f"Too many requests. Try again in later."
    }
    return jsonify(response), 429

@api_v1.errorhandler(Exception)
def handle_generic_error(e):
    if isinstance(e, NoAuthorizationError):
        return unauthorized_response(str(e))
    elif isinstance(e, RevokedTokenError):
        return revoked_token_callback(None, None)
    elif isinstance(e, ExpiredSignatureError):
        return handle_expired_token_error(e)
    elif isinstance(e, InvalidTokenError):
        return handle_invalid_token_error(e)
        
    response = {
        "success": False,
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later."
    }
    logger.error(f"Unhandled exception in {request.path}: {e}, Data: {request.json}")
    return jsonify(response), 500


@api_v1.route('/connect', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Invalid JSON",
                "details": "Request content must be 'application/json'"
            }), 400

        try:
            data = request.get_json()
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": "Failed to parse JSON",
                "details": str(parse_error)
            }), 400

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"success": False, "error": "Invalid input", "message": "Email and password are required"}), 400

        email = unicodedata.normalize(
                    'NFKC', data.get('email', '').strip().lower()
                )
        password = data.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return jsonify({"success": True, "access_token":access_token}), 200
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"success": False, "error": "Login failed", "details": str(e)}), 500


@api_v1.route('/disconnect', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def logout():
    try:
        jti = get_jwt()["jti"]
        blacklist_redis.set(jti, "blacklisted", ex=60*60)
        return jsonify({"success": True, "message": "Token successfully disconnected"})
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({"success": False, "error": "Logout failed", "details": str(e)}), 500

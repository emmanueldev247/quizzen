"""
    Defined routes:
      - '/' -> home
      - '/signup' -> signup
      - '/login' -> login
      - '/reset_password' -> reset_password
      - '/reset_password/<token>' -> reset_password_with_token
      - '/logout' -> logout
"""
import google.auth.transport.requests
import os
import pathlib
import requests
import unicodedata
from flask import (
    current_app, flash, jsonify,
    redirect, render_template, request,
    session, url_for
)
from flask_limiter.errors import RateLimitExceeded
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from functools import wraps
from oauthlib.oauth2.rfc6749.errors import (
    MismatchingStateError,
    InvalidGrantError,
    InvalidClientError,
    InvalidScopeError,
    UnauthorizedClientError,
    AccessDeniedError,
    TokenExpiredError,
)
from google.auth.exceptions import RefreshError, TransportError
from requests.exceptions import ConnectionError, Timeout

from app.extensions import db, full_bp, oauth_bp, limiter
from app.models import User
from app.routes import logger, rate_limit_exceeded

def oauth_is_required(f):
    """OAuth required function"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        """OAuth required decorator"""
        logger.info(f"OAuth Attempt")
        if "oauth_user" not in session:
            logger.error(f"Oauth token missing")
            flash("You need to log in first", "error")
            return redirect(url_for('full_bp.login'))
        else:
            return f(*args, **kwargs)
    return wrapper


@oauth_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return rate_limit_exceeded(e)


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

# Flow setup
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "utils/client_secret.json")

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
)


@oauth_bp.route("/")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@oauth_bp.route("/callback")
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)
    except MismatchingStateError as e:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("An error occured. Please log in again", "error")
        return redirect(url_for('full_bp.login'))
        
    except AccessDeniedError as e:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("An error occured. Please log in again", "error")
        return redirect(url_for('full_bp.login'))

    except InvalidGrantError as e:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("An error occured. Please log in again", "error")
        return redirect(url_for('full_bp.login'))

    except TokenExpiredError:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("Session expired. Please log in again", "error")
        return redirect(url_for('full_bp.login'))

    except Timeout:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("The request timed out. Try again later", "error")
        return redirect(url_for('full_bp.login'))

    except ConnectionError:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("Network connection error", "error")
        return redirect(url_for('full_bp.login'))
        
    except Exception as e:
        logger.error(f"Error occured in callback: {str(e)}")
        flash("An error occured. Please log in again", "error")
        return redirect(url_for('full_bp.login'))

    try:
        if not session or session['state'] != request.args['state']:
            logger.error(f"State does not match")
            flash("Session expired. Please log in again", "error")
            return redirect(url_for('full_bp.login'))

        credentials = flow.credentials
        request_session = requests.session()
        token_request = google.auth.transport.requests.Request(session=request_session)

        user_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        email = unicodedata.normalize(
            'NFKC', user_info.get('email', '').strip().lower()
        )
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        profile_picture = user_info.get('picture', '')

        user = User.query.filter_by(email=email).first()
        if not user:
            session["oauth_user"] = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "profile_picture": profile_picture if profile_picture else None
            }
            return redirect(url_for("full_bp.oauth_registration"))

        session.clear()
        session['user_id'] = user.id
        session['user_role'] = user.role
        logger.info(f"Session (after clear): {session}")
        logger.info(f"Oauth User {user.id} logged in successfully")

        return redirect(url_for("full_bp.user_dashboard"))
    except Exception as e:
        logger.error(f"Error during callback: {e}")
        return redirect(url_for("full_bp.user_dashboard"))



@full_bp.route("/oauth/signin", methods=["GET", "POST"])
@oauth_is_required
def oauth_registration():
    if request.method == "GET":
        limiter.limit("20 per minute")(lambda: None)()
        return render_template("signup_oauth.html")

    if request.method == "POST":
        limiter.limit("5 per minute")(lambda: None)()

        oauth_user = session.get("oauth_user")
        if not oauth_user:
            flash("Session expired. Please log in again", "error")
            return redirect(url_for("full_bp.login"))

        try:
            data = request.get_json() if request.is_json else request.form
            role = data.get('role', '').strip()
            if not role:
                flash("You must select a role", "error")
                return redirect(url_for("full_bp.oauth_registration"))

            user = User(
                email=oauth_user["email"],
                first_name=oauth_user["first_name"],
                last_name=oauth_user["last_name"],
                profile_picture=oauth_user["profile_picture"],
                role=role,
            )

            db.session.add(user)
            db.session.commit()

            session.clear()
            logger.info(f"Session: {session}")
            session["user_id"] = user.id
            session['user_role'] = user.role
            logger.info(f"Oauth User {user.id} logged in successfully")
            return jsonify({
                "success": True,
                "message": "OAuth User registered successfully"
            }), 201
        except Exception as e:
            logger.error(f"Error during Oauth signup: {e}")
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": "Error saving user",
                "error": str(e)
            }), 500

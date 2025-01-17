from app.extensions import full_bp, oauth_bp
from app.models import User, UsedToken

from functools import wraps

import os
import pathlib
import requests
from flask import session, abort, redirect, request, abort, current_app
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from app.routes import (
    logger, rate_limit_exceeded
)


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
from requests.exceptions import Timeout, ConnectionError

def oauth_is_required(f):
    """OAuth required function"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        """OAuth required decorator"""
        logger.info(f"OAuth Attempt")
        if "oauth_user" not in session:
            logger.error(f"Oauth token missing")
            flash("log in", "error")
            return redirect(url_for('full_bp.login'))
        else:
            return f(*args, **kwargs)
    return wrapper


@oauth_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return rate_limit_exceeded(e)

@full_bp.before_request
def debug_session():
    print(f"fbp: SESSION_COOKIE_SAMESITE before request: {current_app.config['SESSION_COOKIE_SAMESITE']}")
    print(f"Session before request: {dict(session)}")

@full_bp.after_request
def debug_session_after(response):
    print(f"Session after request: {dict(session)}")
    print(f"fbp: SESSION_COOKIE_SAMESITE after request: {current_app.config['SESSION_COOKIE_SAMESITE']}")
    return response

@oauth_bp.before_app_request
def before_oauth_request():
    if request.endpoint == 'oauth.login' or request.endpoint == 'oauth.callback':
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    else:
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

@oauth_bp.after_app_request
def after_oauth_request(response):
    if 'state' not in session:
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    #print(f"obp: SESSION_COOKIE_SAMESITE after request: {current_app.config['SESSION_COOKIE_SAMESITE']}")
    return response

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

# Flow setup
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "utils/client_secret.json")
print(client_secrets_file)

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
)

    
@full_bp.route("/quizzen/index")
def index_oauth():
    return "Hello World <a href='/quizzen/auth/google'><button>Login</button></a>"


@oauth_bp.route("/")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    print(f'Session after set: {session}')
    print(f'Session after set: {dict(session)}')

    return redirect(authorization_url)


@oauth_bp.route("/callback")
def callback():
    print(f'Session: {session}')
    try:
        flow.fetch_token(authorization_response=request.url)
    except MismatchingStateError:
        # Handle CSRF state mismatch error
        print("Error: CSRF protection triggered. State does not match.")
        # Take appropriate action, like logging or showing an error to the user

    except AccessDeniedError:
        # User denied access to the app
        print("Error: The user denied the authorization request.")

    except InvalidGrantError:
        # Authorization code invalid, expired, or already used
        print("Error: Invalid or expired authorization code.")

    except InvalidClientError:
        # Client credentials are incorrect or not recognized
        print("Error: Invalid client credentials. Check your client_id and client_secret.")

    except UnauthorizedClientError:
        # Client not authorized to request tokens for this flow
        print("Error: Unauthorized client. Ensure your app is authorized for this flow.")

    except InvalidScopeError:
        # The requested scope is invalid or malformed
        print("Error: Invalid or unknown scope. Check your requested scopes.")

    except TokenExpiredError:
        # Token expired before it could be used
        print("Error: The token has expired. Reauthenticate to get a new token.")

    except RefreshError:
        # Failure while refreshing or exchanging the token
        print("Error: Failed to refresh or fetch the token. Verify network and credentials.")

    except TransportError:
        # Network transport error occurred
        print("Error: Network transport error occurred. Check your connection.")

    except Timeout:
        # Network request timed out
        print("Error: The request timed out. Try again later.")

    except ConnectionError:
        # Network connection issue
        print("Error: Network connection error. Ensure your internet is stable.")

    except Exception as e:
        pass

    try:
        if not session or session['state'] != request.args['state']:
            abort(500, 'State does not match')

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        user_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        email = user_info.get('email')
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

        # Log in the user
        session['user_id'] = user.id
        session['user_role'] = user.role
        logger.info(f"Oauth User {user.id} logged in successfully")
        
        return redirect(url_for("full_bp.user_dashboard"))
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("index"))

@full_bp.route("/oauth/signin", methods=["GET", "POST"])
@oauth_is_required
def oauth_registration():
    if request.method == "GET":
        return render_template("signup_oauth.html")

    if request.method == "POST":
        # Retrieve user info from session
        oauth_user = session.get("oauth_user")
        if not oauth_user:
            flash("Session expired. Please log in again.", "danger")
            return redirect(url_for("full_bp.user_dashboard"))

        # Get form data
        role = data.get('role', '').strip()

        # Validate input
        if not role:
            flash("All fields are required.", "danger")
            return redirect(url_for("full_bp.user_dashboard"))

        # Create and save user
        user = User(
            email=oauth_user["email"],
            first_name=oauth_user["first_name"],
            last_name=oauth_user["last_name"],
            profile_picture=oauth_user["profile_picture"],
            role=role,
        )

        db.session.add(user)
        db.session.commit()

        # Log in user
        session["user_id"] = user.id
        session['user_role'] = user.role
        flash("Registration complete!", "success")
        return redirect(url_for("full_bp.user_dashboard"))
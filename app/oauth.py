from app.extensions import full_bp, oauth_bp
from app.models import User, UsedToken

import os
import pathlib
import requests
from flask import session, abort, redirect, request, abort, current_app
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
print(f'Google ID: {GOOGLE_CLIENT_ID}')

# Flow setup
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "utils/client_secret.json")
print(client_secrets_file)

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
)

# come back
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
    print(f"abp: SESSION_COOKIE_SAMESITE before request: {current_app.config['SESSION_COOKIE_SAMESITE']}")
    print(f'Endpoint: {request.endpoint}')

    if request.endpoint == 'oauth.login' or request.endpoint == 'oauth.callback':
    #     and 'state' in request.args:
    # if request.endpoint == 'oauth.callback' and 'state' in request.args:
        print("setting............")
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    else:
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'


@oauth_bp.after_app_request
def after_oauth_request(response):
    if 'state' not in session:
        current_app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    print(f"obp: SESSION_COOKIE_SAMESITE after request: {current_app.config['SESSION_COOKIE_SAMESITE']}")
    return response


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

    
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
    flow.fetch_token(authorization_response=request.url)

    try:
        if session['state'] != request.args['state']:
            abort(500, 'State does not match')
    except Exception as e:
        print(f'Error: {str(e)}')

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    print(f'ID_INFO: {id_info}')

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/quizzen/protected_area")


@full_bp.route("/logout2")
def logout2():
    session.clear()
    return redirect("/quizzen/index")


@full_bp.route("/protected_area")
@login_is_required
def protected_area():
    return f"Hello {session['name']}! <br/> <a href='/quizzen/logout2'><button>Logout</button></a>"
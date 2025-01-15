from app.extensions import full_bp, mail, limiter, oauth
from app.models import User, UsedToken
from app.utils.logger import setup_logger

import os
import pathlib

import requests
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

@full_bp.before_request
def debug_session():
    print(f"Session before request: {session}")

@full_bp.after_request
def debug_session_after(response):
    print(f"Session after request: {session}")
    return response


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

print(f'Google ID: {GOOGLE_CLIENT_ID}')
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

    
@full_bp.route("/quizzen/index")
def index_oauth():
    return "Hello World <a href='/quizzen/auth/login'><button>Login</button></a>"


@full_bp.route("/auth/login")
def testing():
    """print(session)
    session.clear()
    print("session cleared")"""
    
    print(f'Session: {session}')

    authorization_url, state = flow.authorization_url()
    session["state"] = state
    print(f'Session after set: {session}')
    print(f'URL: {authorization_url}')

    return redirect(authorization_url)


@full_bp.route("/auth/google/callback")
def callback():
    print(session)
    flow.fetch_token(authorization_response=request.url)

    try:
        if not session["state"] == request.args["state"]:
            abort(500)  # State does not match!
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


@full_bp.route("/quizzen/protected_area")
@login_is_required
def protected_area():
    return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"
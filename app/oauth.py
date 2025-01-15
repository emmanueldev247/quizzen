
# import unicodedata
# from datetime import datetime
# from flask import (
#     current_app, flash, jsonify,
#     redirect, render_template, request,
#     session, url_for
# )
# from flask_limiter.errors import RateLimitExceeded
# from flask_mail import Message
# from itsdangerous import (
#     BadSignature, SignatureExpired,
#     URLSafeTimedSerializer as Serializer
# )

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


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

print(f'Google ID: {GOOGLE_CLIENT_ID}')
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
     client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
)

@full_bp.route("/quizzen/index")
def index_oauth():
    return "Hello World <a href='/quizzen/auth/login'><button>Login</button></a>"


@full_bp.route("/auth/login")
def testing():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    print(session)
    print(authorization_url)

    return redirect(authorization_url)


@full_bp.route("/auth/google/callback")
def callback():
    print(session)
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    print(id_info)

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


# def login_is_required(function):
#     def wrapper(*args, **kwargs):
#         if "google_id" not in session:
#             return abort(401)  # Authorization required
#         else:
#             return function()

#     return wrapper


# @app.route("/login")
# def login():
#     authorization_url, state = flow.authorization_url()
#     session["state"] = state
#     return redirect(authorization_url)


# @app.route("/callback")
# def callback():
#     flow.fetch_token(authorization_response=request.url)

#     if not session["state"] == request.args["state"]:
#         abort(500)  # State does not match!

#     credentials = flow.credentials
#     request_session = requests.session()
#     cached_session = cachecontrol.CacheControl(request_session)
#     token_request = google.auth.transport.requests.Request(session=cached_session)

#     id_info = id_token.verify_oauth2_token(
#         id_token=credentials._id_token,
#         request=token_request,
#         audience=GOOGLE_CLIENT_ID
#     )

#     session["google_id"] = id_info.get("sub")
#     session["name"] = id_info.get("name")
#     return redirect("/protected_area")


# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect("/")


# @app.route("/")
# def index():
#     return "Hello World <a href='/login'><button>Login</button></a>"


# @app.route("/protected_area")
# @login_is_required
# def protected_area():
#     return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"


# if __name__ == "__main__":
#     app.run(debug=True)
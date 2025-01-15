"""
    Defined routes:
      - '/' -> home
      - '/signup' -> signup
      - '/login' -> login
      - '/reset_password' -> reset_password
      - '/reset_password/<token>' -> reset_password_with_token
      - '/logout' -> logout
"""

import unicodedata
from datetime import datetime
from flask import (
    current_app, flash, jsonify,
    redirect, render_template, request,
    session, url_for
)
from flask_limiter.errors import RateLimitExceeded
from flask_mail import Message
from itsdangerous import (
    BadSignature, SignatureExpired,
    URLSafeTimedSerializer as Serializer
)

from app.extensions import db, full_bp, mail, limiter, oauth
from app.models import User, UsedToken
from app.utils.logger import setup_logger


logger = setup_logger()


@full_bp.errorhandler(RateLimitExceeded)
def rate_limit_exceeded(e):
    """Rate limit handler"""
    logger.warning(
        f"Rate limit exceeded on route {request.path}. "
        f"Details: {e.description}"
    )
    return jsonify({
        "success": False,
        "error": "Too many requests, please try again later."
    }), 429


@full_bp.after_request
def log_response_info(response):
    """Middle ware for after request"""
    logger.info(f'"{request.method} {request.path}" {response.status_code}')
    return response


@full_bp.route('/')
def home():
    """Home route"""
    return render_template('index.html', title='Home')


@full_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup  route"""
    logger.debug(f"{request.method} - Signup attempt")
    if request.method == 'POST':
        try:
            limiter.limit("5 per minute")(lambda: None)()
            data = request.get_json() if request.is_json else request.form

            email = unicodedata.normalize(
                'NFKC', data.get('email', '').strip().lower()
            )

            password = data.get('password', '')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            date_of_birth = data.get('date_of_birth', '').strip()
            role = data.get('role', '').strip()
            gender = data.get('gender', '').strip()
        except Exception as e:
            logger.error(f"Error during signup: {e}")
            return jsonify({
                "success": False,
                "message": "Form data not valid",
                "error": str(e)
            }), 401

        if not all([email, password, first_name,
                    last_name, date_of_birth, role, gender]):
            logger.error(f"Form data not valid")
            return jsonify({
                "success": False,
                "message": "Form data not valid"
            }), 401

        try:
            if User.query.filter_by(email=email).first():
                logger.error(f"Email '{email}' already exists")
                return jsonify({
                    "success": False,
                    "message": "Email already exists"
                }), 400
        except Exception as e:
            logger.error(f"Error during signup: {e}")
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": "Server error",
                "error": str(e)
            }), 500

        try:
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d'),
                gender=gender,
                role=role
            )
            if password:
                new_user.set_password(password)
                new_user.has_password = True
            else:
                new_user.has_password = False

            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User '{new_user.id}' registered successfully")
            return jsonify({
                "success": True,
                "message": "User registered successfully"
            }), 201
        except Exception as e:
            logger.error(f"Error during signup: {e}")
            db.session.rollback()
            return jsonify({
                "success": False,
                "message": "Error saving user",
                "error": str(e)
            }), 500

    return render_template('signup.html', title='Sign up')


@full_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    logger.debug(f"{request.method} - Login attempt")
    if request.method == 'POST':
        try:
            limiter.limit("5 per minute")(lambda: None)()
            data = request.get_json() if request.is_json else request.form

            email = unicodedata.normalize(
                'NFKC', data.get('email', '').strip().lower()
            )
            password = data.get('password', '')
        except Exception as e:
            logger.error(f"Error during signup: {e}")
            return jsonify({
                "success": False,
                "message": "Form data not valid",
                "error": str(e)
            }), 400

        try:
            user = User.query.filter_by(email=email).first()
            if user:
                if user.has_password:
                    if user.check_password(password):
                        session['user_id'] = user.id
                        session['user_role'] = user.role
                        logger.info(f"User {user.id} logged in successfully")
                        return jsonify({
                            "success": True,
                            "message": "Login successful"
                        }), 200
                    logger.warning(f"Failed login attempt for email: {email}")
                    return jsonify({
                        "success": False,
                        "message": "Invalid Credentials"
                    }), 401
                else:
                    logger.warning(f"User with email {email} is an OAuth user")
                    return jsonify({
                        "success": False,
                        "message": "Please use OAuth to log in."
                    }), 400
            else:
                logger.warning(f"User not found for email: {email}")
                return jsonify({
                    "success": False,
                    "message": "Invalid Credentials"
                }), 401

        except Exception as e:
            logger.error(f"Error during login: {e}")
            return jsonify({
                "success": False,
                "message": "Server error",
                "error": str(e)
            }), 500

    return render_template('login.html', title='Login')


@full_bp.route('/reset_password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """reset password route"""
    try:
        logger.debug(f"Password reset attempt")
        data = request.get_json() if request.is_json else request.form

        email = unicodedata.normalize(
                'NFKC', data.get('email', '').strip().lower()
        )

    except Exception as e:
        logger.error(f"Error during password reset: {e}")
        return jsonify({
            "success": False,
            "message": "Form data not valid",
            "error": str(e)
        }), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.error(f"Email '{email}' not found")
            return jsonify({
                "success": False,
                "message": "Email not found"
            }), 404
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': user.id})

        reset_link = url_for('full_bp.reset_with_token',
                             token=token, _external=True, _scheme='https')
        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f"""
         Hello,

         We received a request to reset your password for your Quizzen account.
         If you made this request, click the link below to reset your password:

         {reset_link}

         If you did not request a password reset, please ignore this email or
         contact support if you have any concerns.

         Thank you,
         The Quizzen Team
        """

        # READ TEMPLATE
        with open("app/templates/password_reset_email.html", "r") as file:
            template = file.read()
        msg.html = template.format(reset_link=reset_link)
        mail.send(msg)
        logger.info(f"Link sent to mail '{mail}'")
        return jsonify({
            "success": True,
            "message": "Password reset link sent to your email!"
        }), 200
    except Exception as e:
        logger.error(f"Error during password reset: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to send email. Please try again later.",
            "error": str(e)
        }), 500


@full_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    """reset password with token route"""
    logger.debug(f"{request.method} - Password reset with token attempt")
    try:
        s = Serializer(current_app.config['SECRET_KEY'])
        data = s.loads(token, max_age=1800)
    except SignatureExpired:
        logger.error(f"Token Expired")
        if (
            request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html']
        ):
            return jsonify({
                "success": False,
                "message": "Expired token."
            }), 400
        else:
            return render_template(
                'reset_password_error.html',
                title="Error",
                message_h1="Link Expired",
                message_p="Your password reset link has expired. To reset "
                          "your password, please return to the login page and"
                          " select \"<b>Forgot Password?</b>\""
                          " to request a new reset link."
            ), 400
    except BadSignature:
        logger.error(f"Invalid Token")
        if (
            request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html']
        ):
            return jsonify({
                "success": False,
                "message": "Invalid token."
            }), 400
        else:
            return render_template(
                'reset_password_error.html',
                title="Error",
                message_h1="Invalid Link",
                message_p="We're sorry, but the link you clicked is invalid "
                          "or has already been used. Please return to the "
                          "login page and select \"<b>Forgot Password?</b>\" "
                          "to request a new reset link."
            ), 400

    try:
        if UsedToken.query.filter_by(token=token).first():
            logger.error(f"Token has been used")
            if (
                request.accept_mimetypes['application/json'] >=
                request.accept_mimetypes['text/html']
            ):
                return jsonify({
                    "success": False,
                    "message": "Token has already been used."
                }), 400
            else:
                return render_template(
                    'reset_password_error.html',
                    title="Error",
                    message_h1="Invalid Link",
                    message_p="We're sorry, but the link you clicked is "
                              "invalid or has already been used. "
                              "Please return to the login page and select "
                              "\"<b>Forgot Password?</b>\" to request "
                              "a new reset link."
                ), 400
    except Exception as e:
        logger.error(f"Error during reset password with token: {e}")
        if (
            request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html']
        ):
            return jsonify({
                "success": False,
                "message": "Failed to check Token. Please try again later.",
                "error": str(e)
            }), 500
        else:
            return render_template(
                'reset_password_error.html',
                title="Error",
                message_h1="Invalid Link",
                message_p="We're sorry, but the link you clicked is invalid "
                          "or has already been used. Please return to the "
                          "login page and select \"<b>Forgot Password?</b>\""
                          " to request a new reset link."
            ), 500

    user = User.query.get(data['user_id'])
    if not user:
        logger.error(f"User '{user.id}' not found")
        if (
            request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html']
        ):
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404
        else:
            return render_template(
                'reset_password_error.html',
                title="Error",
                message_h1="Invalid Link",
                message_p="We're sorry, but the link you clicked is invalid "
                          "or has already been used. Please return to the "
                          "login page and select \"<b>Forgot Password?</b>\""
                          " to request a new reset link."
            ), 404

    if request.method == 'POST':
        limiter.limit("5 per minute")(lambda: None)()
        new_password = request.json.get('password')
        if not new_password:
            logger.error(f"Password cannot be empty")
            return jsonify({
                "success": False,
                "message": "Password cannot be empty."
            }), 422

        user.set_password(new_password)
        db.session.add(user)

        used_token = UsedToken(token=token)
        db.session.add(used_token)

        db.session.commit()
        logger.info(f"Password for user '{user.id}' reset successfully")
        return jsonify({
            "success": True,
            "message": "Password successfully reset."
        }), 200

    return render_template('reset_password.html', title="Reset Password")


@full_bp.route('/logout')
def logout():
    """Logout route"""
    user_id = session.get('user_id')
    if user_id:
        logger.info(f"User '{user_id}' has logged out")
    session.clear()
    response = redirect(url_for('full_bp.home'))
    response.set_cookie('session', '', expires=0)
    return response


# @full_bp.route('/auth/google/callback', methods=['GET', 'POST'])
# def login():
#     """Login route"""

# import os
# import pathlib
# import time

# import requests
# from flask import Flask, session, abort, redirect, request
# from google.oauth2 import id_token
# from google_auth_oauthlib.flow import Flow
# from pip._vendor import cachecontrol
# import google.auth.transport.requests

# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# GOOGLE_CLIENT_ID = "33674737284-srfbp7srvi8ie2m0sr426fved0hjq2tp.apps.googleusercontent.com"
# client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

# flow = Flow.from_client_secrets_file(
#     client_secrets_file=client_secrets_file,
#     scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
#     redirect_uri="https://emmanueldev247.tech/quizzen/auth/google/callback"
# )


# @full_bp.route("/oauth-test")
# def index_oauth():
#     return "Hello World <a href=\"{{ url_for('full_bp.testing') }}\"><button>Login</button></a>"


# @full_bp.route('/auth/login')
# def testing():
#     """Login route"""
#     authorization_url, state = flow.authorization_url()
#     print(f'Flow is: {flow.authorization_url()}')
#     session["state"] = state
#     return redirect(authorization_url)


# @full_bp.route('/auth/google/callback')
# def callback():
#     """Login route"""
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

#     print(f'id info : {id_info}')
    
#     session["google_id"] = id_info.get("sub")
#     session["name"] = id_info.get("name")
#     return redirect("/protected_area")


# @full_bp.route("/logout_auth")
# def logout_auth():
#     session.clear()

#     time.sleep(5)
#     return redirect("/quizzen/oauth-test")


# @full_bp.route("/protected_area")
# def protected_area():
#     return f"Hello {session['name']}! <br/> <a href='/quizzen/logout_auth'><button>Logout</button></a>"


# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile'
    }
)



@full_bp.route("/oauth-test")
def index_oauth():
    return "Hello World <a href='/quizzen/auth/login'><button>Login</button></a>"


@full_bp.route('/auth/login')
def testing():
    """Login route"""
    redirect_uri = url_for('full_bp.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

    authorization_url, state = flow.authorization_url()
    print(f'Flow is: {flow.authorization_url()}')
    session["state"] = state
    return redirect(authorization_url)


import time
@full_bp.route('/authorize')
def authorize():
    token = google.authorize_access_token()  
    user_info = google.get('userinfo').json()
    
    print(f'user: {user_info}')
    
    email = user_info.get('email')
    name = user_info.get('name')

    time.sleep(10)

    return redirect(url_for('full_bp.login'))

    # user = find_user_by_email(email)  # Implement this function to query your database
    # if user:
    #     # Existing user: log them in
    #     session['user'] = user  # Store user info in the session
    #     return redirect(url_for('dashboard'))
    # else:
    #     # New user: sign them up
    #     create_new_user(email, name)  # Implement this function to save to your database
    #     session['user'] = {'email': email, 'name': name}
    #     return redirect(url_for('dashboard'))

# @full_bp.route('/auth/google/callback')
# def callback():
#     """Login route"""
#     flow.fetch_token(authorization_response=request.url)

#     if not session["state"] == request.args["state"]:
#         abort(500)  # State does not match!

#     credentials = flow.credentials
#     request_session = requests.session()
#     cached_session = cachecontrol.CacheControl(request_session)
#     token_request = google.auth.transport.requests.Request(session=cached_session)


from app.extensions import db, bcrypt, mail, limiter
from app.models import User, UsedToken, QuizHistory, Leaderboard, Notification
from app.utils.logger import setup_logger
from datetime import datetime
from flask import (
    Blueprint, current_app, jsonify,
    redirect, render_template, request,
    session, url_for
    )
from flask_mail import Message
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from functools import wraps
from itsdangerous import (
    URLSafeTimedSerializer as Serializer,
    BadSignature, SignatureExpired
)


full_bp = Blueprint('full_bp', __name__, url_prefix='/quizzen')
logger = setup_logger()


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info(f"Auth Attempt")
        if 'user_id' not in session:
            logger.error(f"Session token missing")
            return jsonify({
                "success": False,
                "message": "Authentication token is missing.",
            }), 401
                
        try:
            user_id = session['user_id']
            current_user = User.query.get(user_id)

            if not current_user:
                logger.error("Invalid Token")
                return jsonify({
                    "success": False,
                    "message": "Invalid session"
                }), 401
        except Exceptionas e:
            logger.error(f"Invalid Token, Error: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Invalid session",
                "error": str(e)
            }), 401
        return f(current_user, *args, **kwargs)
    return decorated


@full_bp.errorhandler(RateLimitExceeded)
def ratelimit_exceeded(e):
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
    logger.info(f'"{request.method} {request.path}" {response.status_code}')
    return response


@full_bp.route('/')
def home():
    return render_template('index.html', title='Home')


@full_bp.route('/test')
def test():
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        return jsonify({
            "success": True,
            "x_forwarded_for": x_forwarded_for
        }), 200
    else:
        x_real_ip = request.headers.get("X-Real-Ip", "")
        return jsonify({
            "success": True,
            "x_real_ip": x_real_ip
        }), 200


@full_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    logger.debug(f"{request.method} - Signup attempt")
    if request.method == 'POST':
        limiter.limit("5 per minute")(lambda: None)()
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            email = data.get('email', '').strip()
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
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d'),
                gender=gender,
                role=role
            )
            new_user.set_password(password)

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
    logger.debug(f"{request.method} - Login attempt")
    if request.method == 'POST':
        limiter.limit("5 per minute")(lambda: None)()
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            email = data.get('email', '').strip()
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
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
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
    logger.debug(f"Password reset attempt")
    try:
        email = request.form.get('email').strip()
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
        with open("password_reset_email.html", "r") as file:
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
    logger.debug(f"{request.method} - Password reset with token attempt")
    try:
        s = Serializer(current_app.config['SECRET_KEY'])
        data = s.loads(token, max_age=1800)
    except SignatureExpired:
        logger.error(f"Token Expired")
        if request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']:
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
        if request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']:
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
            if request.accept_mimetypes['application/json'] >= \
            request.accept_mimetypes['text/html']:
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
        if request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']:
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
        if request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']:
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
    user_id = session.get('user_id')
    if user_id:
        logger.info(f"User '{user_id}' has logged out")
    session.clear()
    response = redirect(url_for('full_bp.home'))
    response.set_cookie('session', '', expires=0)
    return response


@full_bp.route('/dashboard')
@auth_required
def dashboard():
    user = User.query.get(current_user.id)
    if not user:
        return redirect(url_for('full_bp.login'))

    quizzes = QuizHistory.query.filter_by(user_id=user.id).all()
    leaderboard = Leaderboard.query.order_by(
        Leaderboard.score.desc()
    ).limit(10).all()
    notifications = Notification.query.filter_by(
        user_id=user.id
    ).order_by(
        Notification.date_posted.desc()
    ).all()

    return render_template(
        'dashboard.html',
        title='Dashboard',
        user=user,
        quizzes=quizzes,
        leaderboard=leaderboard,
        notifications=notifications
    )

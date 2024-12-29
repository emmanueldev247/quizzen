from flask import (
    Blueprint, current_app, jsonify,
    redirect, render_template, request,
    session, url_for
    )
from flask_mail import Message
from app.extensions import db, bcrypt, mail
from app.models import User, UsedToken
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired
from functools import wraps


full_bp = Blueprint('full_bp', __name__, url_prefix='/quizzen')

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Authentication token is missing.", "success": False}), 401
        try:
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(token)
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({"message": "Invalid token.", "success": False}), 401
        except BadSignature:
            return jsonify({"message": "Invalid or expired token.", "success": False}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@full_bp.route('/')
def home():
    return render_template('index.html', title='Home')

@full_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            email = request.form.get('email').strip()
            password = request.form.get('password')
            first_name = request.form.get('first_name').strip()
            last_name = request.form.get('last_name').strip()
            date_of_birth = request.form.get('date_of_birth').strip()
            role = request.form.get('role').strip()
            gender = request.form.get('gender').strip()
        except Exception as e:
            return jsonify(
                {'success': False, 'message': 'Form data not valid', 'error': str(e)}
            ), 401

        try:
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'message': 'Email already exists'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Server error', 'error': str(e)}), 500

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
            return jsonify({'success': True, 'message': 'User registered successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error saving user', 'error': str(e)}), 500

    return render_template('signup.html', title='Sign up')


@full_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email').strip()
            password = request.form.get('password')
        except Exception as e:
            return jsonify(
                {'success': False, 'message': 'Form data not valid', 'error': str(e)}
            ), 400

        try:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                return jsonify({"success": True, "message": "Login successful"}), 200
            return jsonify({"success": False, "message": "Invalid Credentials"}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': 'Server error', 'error': str(e)}), 500

    return render_template('login.html', title='Login')

@full_bp.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        email = request.form.get('email').strip()
    except Exception as e:
        return jsonify(
            {'success': False, 'message': 'Form data not valid', 'error': str(e)}
        ), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, "message": "Email not found"}), 404
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': user.id})

        reset_link = url_for('full_bp.reset_with_token', token=token, _external=True, _scheme='https')
        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f"""
            Hello,

            We received a request to reset your password for your Quizzen account. If you made this request, click the link below to reset your password:

            {reset_link}

            If you did not request a password reset, please ignore this email or contact support if you have any concerns.

            Thank you,
            The Quizzen Team
        """
        msg.html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; font-size: 14px">
                    <h2 style="text-align: center; color: #444;">Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>We received a request to reset your password for your Quizzen account. If you made this request, click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 20px;">
                        <a href="{reset_link}" 
                        style="background-color: #6a0dad; 
                                color: white; 
                                padding: 10px 20px; 
                                text-decoration: none; 
                                border-radius: 5px; 
                                font-size: 16px;">
                            Reset Your Password
                        </a>
                    </div>
                    <p>If you did not request a password reset, please ignore this email or contact support if you have any concerns.</p>
                    <p>Thank you,<br>The Quizzen Team</p>
                </body>
            </html>
        """
        mail.send(msg)
        return jsonify({"success": True, "message": "Password reset link sent to your email!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to send email. Please try again later.", "error": str(e)}), 500

@full_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        s = Serializer(current_app.config['SECRET_KEY'])
        data = s.loads(token, max_age=1800)
    except SignatureExpired:
        if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({"success": False, "message": "Expired token."}), 400
        else:
            return render_template('reset_password_error', 
                                    message_h1="Link Expired",
                                    message_p='Your password reset link has expired. To reset your password,\
                                        please return to the login page and select "Forgot Password" to request a new reset link.'
                                  ), 404
    except BadSignature:
        if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({"success": False, "message": "Invalid token."}), 400
        else:
            return render_template('reset_password_error', 
                                    message_h1="Invalid Link",
                                    message_p="We're sorry, but the link you clicked is invalid or has already been used.\
                                        Please return to the login page and select \"Forgot Password\" to request a new reset link."
                                  ), 404
            # return render_template('reset_password_error', title="Error" ), 404

    try:
        if UsedToken.query.filter_by(token=token).first():
            if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
                return jsonify({"success": False, "message": "Token has already been used."}), 400
            else:
                return render_template('reset_password_error', 
                                        message_h1="Invalid Link",
                                        message_p="We're sorry, but the link you clicked is invalid or has already been used.\
                                            Please return to the login page and select \"Forgot Password\" to request a new reset link."
                                    ), 404
                # return render_template('reset_password_error', title="Error" ), 404
    except Exception as e:
        if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({"success": False, "message": "Failed to check Token. Please try again later.", "error": str(e)}), 500
        else:
            return render_template('reset_password_error', 
                                    message_h1="Invalid Link",
                                    message_p="We're sorry, but the link you clicked is invalid or has already been used.\
                                        Please return to the login page and select \"Forgot Password\" to request a new reset link."
                                ), 404
            # return render_template('reset_password_error', title="Error" ), 404

    user = User.query.get(data['user_id'])
    if not user:
        if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
            return jsonify({"success": False, "message": "User not found."}), 404
        else:
            return render_template('reset_password_error', 
                                    message_h1="Invalid Link",
                                    message_p="We're sorry, but the link you clicked is invalid or has already been used.\
                                        Please return to the login page and select \"Forgot Password\" to request a new reset link."
                                ), 404
            # return render_template('reset_password_error', title="Error" ), 404

    if request.method == 'POST':
        new_password = request.json.get('password')
        if not new_password:
            return jsonify({"success": False, "message": "Password cannot be empty."}), 400

        user.set_password(new_password)
        db.session.add(user)

        used_token = UsedToken(token=token)
        db.session.add(used_token)

        db.session.commit()
        return jsonify({"success": True, "message": "Password successfully reset."}), 200

    return render_template('reset_password.html', title="Reset Password")

@full_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('full_bp.home'))

@full_bp.route('/dashboard')
@auth_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

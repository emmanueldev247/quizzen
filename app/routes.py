from flask import (
    Blueprint, flash, jsonify,
    redirect, render_template, request,
    session, url_for
    )
from flask_mail import Message
from app.extensions import db, bcrypt, mail
from app.models import User
from datetime import datetime
from itsdangerous import TimedSerializer as Serializer, BadSignature


full_bp = Blueprint('full_bp', __name__, url_prefix='/quizzen')

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
                flash('Email already registered', 'danger')
                print(f'user exist')
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
        s = Serializer(app.config['SECRET_KEY'], expires_in=1800)
        token = s.dumps({'user_id': user.id}).decode('utf-8')

        reset_link = url_for('full_bp.reset_with_token', token=token, _external=True)

        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f'Click the link to reset your password: {reset_link}'
        mail.send(msg)
        return jsonify({"message": "Password reset link sent to your email!"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to send email. Please try again later."}), 500

@full_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        s = Serializer(app.config['SECRET_KEY'])
        data = s.loads(token)
    except BadSignature:
        return jsonify({"message": "Invalid or expired token."}), 400

    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({"message": "User not found."}), 404

    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password:
            return jsonify({"message": "Password cannot be empty."}), 400

        user.set_password(new_password)
        db.session.commit()
        return jsonify({"message": "Password successfully reset."}), 200

    return jsonify({"message": "Use the POST method to reset your password."}), 405


@full_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('full_bp.home'))

@full_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

from flask import ( 
    Blueprint, flash, jsonify, 
    redirect, render_template, request, 
    session)
from app.extensions import db, bcrypt
from app.models import User
from datetime import datetime


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
                flash('Login successful!', 'success')
                return redirect(url_for('full_bp.dashboard'))
            flash('Invalid credentials', 'danger')
        except Exception as e:
            return jsonify({'success': False, 'message': 'Server error', 'error': str(e)}), 500
  
    return render_template('login.html', title='Login')

@full_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('full_bp.home'))
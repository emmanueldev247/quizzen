from flask import render_template, redirect, url_for, request, session, flash, Blueprint
from app.extensions import db, bcrypt
from app.models import User


full_bp = Blueprint('full_bp', __name__, url_prefix='/quizzen')

@full_bp.route('/')
def home():
    return render_template('index.html', title='Home')

@full_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        print("request.form: ",request.form)
        email = request.form.get('email').strip()
        password = request.form.get('password')
        first_name = request.form.get('first_name').strip()
        last_name = request.form.get('last_name').strip()
        date_of_birth = request.form.get('date_of_birth').strip()
        role = request.form.get('role').strip()
        gender = request.form.get('gender').strip()

        # if User.query.filter_by(email=email).first():
        #     flash('Email already registered', 'danger')
        #     return redirect(url_for('full_bp.signup'))

        #new_user = User(username=email, email=email, first_name=first_name,
                        # last_name=last_name, date_of_birth=date_of_birth, 
                        # gender=gender, role=role)
        #new_user.set_password(password)

#        db.session.add(new_user)
 #       db.session.commit()
        print(f'''
            email is: {email}
            first name is: {first_name}
            last name is: {last_name}
            gender is: {gender}
            role is: {role}
            password is: {password}
            date of birth: {date_of_birth}
        '''
        )
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('full_bp.login'))
    return render_template('signup.html', title='Sign up')


@full_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('full_bp.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', title='Login')

@full_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('full_bp.home'))

# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, SubmitField
# from wtforms.validators import DataRequired, Email

# class SignupForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     gender = StringField('Gender', validators=[DataRequired()])  # New gender field
#     submit = SubmitField('Sign Up')

# @full_bp.route('/signup2', methods=['GET', 'POST'])
# def signup2():
#     form = SignupForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data,
#                     email=form.email.data,
#                     password=form.password.data,
#                     gender=form.gender.data)  # Capture the gender data
#         # db.session.add(user)
#         # db.session.commit()
#         return redirect(url_for('login'))  # Redirect after signup
#     return render_template('signup2.html', form=form)
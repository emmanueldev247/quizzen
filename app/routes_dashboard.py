"""
    Defined routes:
      -
"""
from app.extensions import db
from app.models import (
    Category, Leaderboard, Notification,
    QuizHistory, User
)
from app.routes import (
    auth_required, full_bp
)
from flask import (
    current_app, flash, jsonify,
    redirect, render_template, request,
    session, url_for
)


@full_bp.route('/dashboard')
@auth_required
def dashboard(current_user):
    logger.debug(f"{request.method} - Dashboard")
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
        Notification.date_sent.desc()
    ).all()

    return render_template(
        'dashboard.html',
        title='Dashboard',
        user=user,
        quizzes=quizzes,
        leaderboard=leaderboard,
        notifications=notifications
    )


@full_bp.route('/create_quiz', methods=['GET', 'POST'])
@auth_required
def create_quiz(current_user):
    logger.debug(f"{request.method} - Create quiz attempt")
    user = User.query.get(current_user.id)
    if not user:
        return redirect(url_for('full_bp.login'))
    if request.method == 'POST':
        limiter.limit("5 per minute")(lambda: None)()
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            title = data.get('title', '').strip()
            description = data.get('description', '')
            category_id = data.get('category_id', '')
            duration = data.get('duration', '')

        except Exception as e:
            logger.error(f"Error during quiz creation: {e}")
            return jsonify({
                "success": False,
                "message": "Form data not valid",
                "error": str(e)
            }), 400

        if not all([title, description, duration]):
            flash("All fields are required!", 'danger')
            return redirect(url_for('create_quiz'))

        new_quiz = Quiz(
            title=title,
            description=description,
            category_id=category_id,
            created_by=current_user.id,
            duration=duration
        )

        # Save to the database
        # db.session.add(new_quiz)
        # db.session.commit()

        flash("Quiz created successfully!", 'success')
        return redirect(url_for('dashboard'))

    # GET request: Display the quiz creation form
    categories = Category.query.all()  # Fetch all quiz categories
    return render_template('create_quiz.html', categories=categories)
